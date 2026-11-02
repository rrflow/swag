"""Local bridge contract and privacy tests; no model-quality evidence."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_lfg
import swag_mcp_server as mcp


class LfgBridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root / 'connection.json'
        self.settings = {'schemaVersion': 1, 'baseUrl': 'http://127.0.0.1:4317',
                         'timeoutMs': 5000, 'maxRequestBytes': 65536, 'maxResponseBytes': 65536}
        self.config.write_text(json.dumps(self.settings), encoding='utf-8')
        environment = patch.dict(os.environ, {'SWAG_LFG_CONNECTION_FILE': str(self.config),
                                              'SWAG_TRACE_DIR': str(self.root / 'traces')})
        environment.start()
        self.addCleanup(environment.stop)

    def test_configuration_allows_extra_fields_but_only_literal_loopback(self):
        self.settings['futureOption'] = {'unused': True}
        self.config.write_text(json.dumps(self.settings), encoding='utf-8')
        self.assertEqual(swag_lfg._configuration()['timeoutMs'], 5000)
        for origin in ('http://example.com:4317', 'http://localhost:4317',
                       'http://127.0.0.1:4317/path', 'http://user@127.0.0.1:4317',
                       'https://127.0.0.1:4317'):
            self.settings['baseUrl'] = origin
            self.config.write_text(json.dumps(self.settings), encoding='utf-8')
            with self.assertRaises(swag_lfg.LfgBridgeError):
                swag_lfg._configuration()

    def test_real_contract_flow_binds_input_and_does_not_expose_extensions(self):
        secret = 'request-canary-private-content'
        caps = {'requestSchemaVersion': 'lfg.observation-request.v1',
                'responseSchemaVersion': 'lfg.observation.v1', 'assessmentSha256': 'a' * 64,
                'rulesSha256': 'b' * 64, 'maxInputBytes': 1024}

        def exchange(_config, path, _deadline, payload=None):
            if payload is None:
                return caps
            self.assertEqual(path, '/api/lfg/observations')
            self.assertEqual(payload['text'], secret)
            return {'schemaVersion': caps['responseSchemaVersion'], 'requestId': payload['requestId'],
                    'revision': 1, 'inputSha256': payload['inputSha256'],
                    'assessmentSha256': caps['assessmentSha256'], 'rulesSha256': caps['rulesSha256'],
                    'advisory': True, 'confidence': None, 'status': 'available',
                    'intent': {'status': 'available', 'category': 'build.software'},
                    'complexity': {'bracket': 'moderate', 'score': 1, 'scoreUnit': 'configured-rule-points'},
                    'agents': {'suggested': 1, 'min': 1, 'max': 2},
                    'analyzer': 'deterministic-rules', 'assessmentRevision': 'fixture', 'rulesRevision': 'fixture',
                    'suggestedRole': 'fixture', 'suggestedEffort': 'fixture', 'reasonIds': [], 'ignoredExtensionCount': 0,
                    'unknownResponse': secret}

        with patch('swag_lfg._exchange', side_effect=exchange):
            result = mcp._handle_message({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                'params': {'name': 'lfg_assess', 'arguments': {'text': secret, 'future': 'ignored'}}})
        self.assertFalse(result['result'].get('isError', False))
        self.assertNotIn(secret, json.dumps(result))
        traces = ''.join(path.read_text(encoding='utf-8') for path in (self.root / 'traces').glob('*.jsonl'))
        self.assertNotIn(secret, traces)
        self.assertEqual(json.loads(result['result']['content'][0]['text'])['status'], 'available')

    def test_mismatched_identity_fails_and_config_errors_are_actionable(self):
        caps = {'requestSchemaVersion': 'lfg.observation-request.v1',
                'responseSchemaVersion': 'lfg.observation.v1', 'assessmentSha256': 'a' * 64,
                'rulesSha256': 'b' * 64, 'maxInputBytes': 1024}
        with patch('swag_lfg._exchange', side_effect=[caps, {'schemaVersion': 'lfg.observation.v1'}]):
            with self.assertRaisesRegex(swag_lfg.LfgBridgeError, 'mismatched'):
                swag_lfg.assess('A request')
        with patch.dict(os.environ, {'SWAG_LFG_CONNECTION_FILE': ''}):
            result = mcp._handle_message({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                'params': {'name': 'lfg_assess', 'arguments': {'text': 'A request'}}})
        self.assertTrue(result['result']['isError'])
        self.assertIn('SWAG_LFG_CONNECTION_FILE', result['result']['content'][0]['text'])

    def test_redirect_and_oversized_response_are_rejected(self):
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                if self.path == '/redirect':
                    self.send_response(302)
                    self.send_header('Location', '/target')
                    self.end_headers()
                elif self.path == '/slow':
                    self.send_response(200)
                    self.send_header('Content-Length', '10')
                    self.end_headers()
                    try:
                        for _ in range(10):
                            self.wfile.write(b' ')
                            self.wfile.flush()
                            time.sleep(0.05)
                    except OSError:
                        pass
                else:
                    data = b'{' + b' ' * 100 + b'}'
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)

            def log_message(self, *_args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.settings['baseUrl'] = f'http://127.0.0.1:{server.server_port}'
        self.settings['maxResponseBytes'] = 16
        with self.assertRaises(swag_lfg.LfgBridgeError):
            swag_lfg._exchange(self.settings, '/redirect', time.monotonic() + 3)
        self.assertEqual(calls, ['/redirect'])
        with self.assertRaisesRegex(swag_lfg.LfgBridgeError, 'size or deadline'):
            swag_lfg._exchange(self.settings, '/large', time.monotonic() + 3)
        start = time.monotonic()
        with self.assertRaises(swag_lfg.LfgBridgeError):
            swag_lfg._exchange(self.settings, '/slow', start + 0.12)
        self.assertLess(time.monotonic() - start, 2)


if __name__ == '__main__':
    unittest.main()
