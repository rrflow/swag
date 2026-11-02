"""HTTP boundary tests; responses here are protocol fixtures, not model evidence."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_model_endpoint as endpoint


class ModelEndpointTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = {key: value for key, value in os.environ.items() if not key.startswith('SWAG_')}
        environment['SWAG_TRACE_DIR'] = str(self.root / 'traces')
        context = patch.dict(os.environ, environment, clear=True)
        context.start()
        self.addCleanup(context.stop)
        self.calls = []
        self.code = 200
        self.body = json.dumps({'data': [{'id': 'protocol-fixture'}]}).encode()
        self.headers = {}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                owner.calls.append((self.path, self.headers.get('Authorization')))
                self.send_response(owner.code)
                for key, value in owner.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                try:
                    self.wfile.write(owner.body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(self.server.shutdown)
        self.config = {'schemaVersion': 1, 'baseUrl': f'http://127.0.0.1:{self.server.server_port}',
                       'modelId': 'protocol-fixture', 'credentialFile': 'access.env',
                       'credentialVariable': 'MODEL_TOKEN', 'artifactManifest': 'manifest.json'}
        (self.root / 'access.env').write_text('MODEL_TOKEN=protocol-test-only\n')
        (self.root / 'manifest.json').write_text(json.dumps({'model': 'protocol-fixture'}))
        os.environ['SWAG_MODEL_CONNECTION_FILE'] = str(self.root / 'binding.json')
        self.write_config()

    def write_config(self):
        (self.root / 'binding.json').write_text(json.dumps(self.config))

    def test_discovery_never_attests_weights_inference_or_quality(self):
        result = endpoint.status()
        self.assertEqual(result['state'], 'model_listed')
        self.assertTrue(result['modelListed'])
        for key in ('loadedWeightsVerified', 'inferencePerformed', 'qualified'):
            self.assertFalse(result[key])
        self.assertEqual(self.calls, [('/v1/models', 'Bearer protocol-test-only')])
        serialized = json.dumps(result) + ''.join(path.read_text() for path in (self.root / 'traces').glob('*.jsonl'))
        self.assertNotIn('protocol-test-only', serialized)
        self.assertNotIn(self.config['baseUrl'], serialized)

    def test_no_configuration_does_not_contact_server(self):
        del os.environ['SWAG_MODEL_CONNECTION_FILE']
        self.assertEqual(endpoint.status()['state'], 'not_configured')
        self.assertEqual(self.calls, [])

    def test_missing_identity_and_authentication_failures_are_distinct(self):
        self.body = b'{"data":[]}'
        self.assertEqual(endpoint.status()['state'], 'model_not_listed')
        for code in (401, 403):
            self.code = code
            self.assertEqual(endpoint.status()['state'], 'authentication_failed')

    def test_redirect_is_not_followed_even_to_same_origin(self):
        self.code = 302
        self.headers = {'Location': self.config['baseUrl'] + '/credential-sink'}
        self.assertEqual(endpoint.status()['state'], 'discovery_rejected')
        self.assertEqual(len(self.calls), 1)

    def test_invalid_and_oversized_responses(self):
        for body in (b'not json', b'[]', b'{"data":[null]}', b'{"data":[{"id":1}]}', b' ' * 1_000_001):
            with self.subTest(size=len(body)):
                self.body = body
                self.assertEqual(endpoint.status()['state'], 'invalid_response')

    def test_invalid_configuration_fails_before_network(self):
        original = dict(self.config)
        for changes in ({'baseUrl': 'http://example.com'}, {'baseUrl': 'https://example.com\n'},
                        {'baseUrl': 'https://user:password@example.com'}, {'schemaVersion': True},
                        {'modelId': 'different-manifest'}, {'credentialVariable': 'INVALID NAME'}):
            with self.subTest(changes=changes):
                self.config = {**original, **changes}
                self.write_config()
                self.assertEqual(endpoint.status()['state'], 'invalid_configuration')
        self.assertEqual(self.calls, [])

    def test_changes_to_manifest_and_configuration_are_reobserved(self):
        first = endpoint.status()
        (self.root / 'manifest.json').write_text(json.dumps({'model': 'protocol-fixture', 'changed': True}))
        second = endpoint.status()
        self.assertNotEqual(first['manifestSha256'], second['manifestSha256'])
        self.config['baseUrl'] += '/v1/'
        self.write_config()
        self.assertEqual(endpoint.status()['state'], 'model_listed')
        self.assertEqual(self.calls[-1][0], '/v1/models')
        (self.root / 'manifest.json').write_text('{"model":"changed"}')
        self.assertEqual(endpoint.status()['state'], 'invalid_configuration')
        self.assertEqual(len(self.calls), 3)

    def test_ambiguous_credentials_are_rejected(self):
        (self.root / 'access.env').write_text('MODEL_TOKEN=first\nMODEL_TOKEN=second\n')
        self.assertEqual(endpoint.status()['state'], 'invalid_configuration')
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
