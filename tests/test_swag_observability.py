"""Trace safety and integration failures; these are software tests, not model evidence."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_mcp_server as mcp
from swag_observability import CURRENT, Span, summarize


class TraceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        context = patch.dict(os.environ, {'SWAG_TRACE_DIR': str(self.directory)})
        context.start()
        self.addCleanup(context.stop)

    def records(self):
        return [json.loads(line) for path in self.directory.glob('*.jsonl')
                for line in path.read_text().splitlines()]

    def test_parent_correlation_and_unknown_attributes(self):
        parent = '00-' + '1' * 32 + '-' + '2' * 16 + '-01'
        with Span('test.root', traceparent=parent) as root:
            with Span('test.child') as child:
                self.assertEqual(child.trace_id, '1' * 32)
                self.assertEqual(child.parent_id, root.span_id)
                with self.assertRaises(ValueError):
                    child.set(prompt='sensitive')
                self.assertEqual(summarize(self.directory)['incompleteSpans'], 0)
        self.assertIsNone(CURRENT.get())
        self.assertEqual(len(self.records()), 4)
        self.assertEqual(len(summarize(self.directory)['measurements']), 2)
        with self.assertRaises(ValueError):
            Span('test.root', traceparent='00-' + '0' * 32 + '-' + '2' * 16 + '-01')

    def test_exception_content_is_never_saved(self):
        sensitive = 'private prompt and credential contents'
        with self.assertRaisesRegex(ValueError, sensitive):
            with Span('test.failure'):
                raise ValueError(sensitive)
        records = self.records()
        self.assertNotIn(sensitive, json.dumps(records))
        self.assertEqual(records[-1]['status'], 'error')
        self.assertEqual(records[-1]['errorType'], 'ValueError')

    def test_concurrent_roots_do_not_mix(self):
        def run(_):
            with Span('test.concurrent') as span:
                return span.trace_id
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(run, range(12)))
        self.assertEqual(len(set(ids)), 12)
        summary = summarize(self.directory)
        self.assertEqual(summary['measurements'][0]['samples'], 12)
        self.assertEqual(summary['invalidFiles'], 0)

    def test_partial_and_invalid_files_are_not_successes(self):
        with Span('test.partial'):
            pass
        path = next(self.directory.glob('*.jsonl'))
        path.write_text(path.read_text().splitlines()[0] + '\n')
        (self.directory / 'invalid.jsonl').write_text('not json')
        summary = summarize(self.directory)
        self.assertEqual(summary['incompleteSpans'], 1)
        self.assertEqual(summary['invalidFiles'], 1)
        self.assertEqual(summary['measurements'], [])

    def test_mcp_denies_direct_dispatch_and_correlates_failure(self):
        with patch('swag_decision_service.DecisionService') as service:
            result = mcp._handle_message({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                'params': {'name': 'decision_route', 'arguments': {'execute_frontier': True}}})
        service.assert_not_called()
        self.assertTrue(result['result']['isError'])
        trace_id = result['result']['_meta']['swag/traceId']
        ends = [row for row in self.records() if row['event'] == 'end']
        self.assertTrue(all(row['traceId'] == trace_id and row['status'] == 'error' for row in ends))

    def test_protocol_error_is_not_a_successful_trace(self):
        result = mcp._handle_message({'jsonrpc': '2.0', 'id': 2, 'method': 'unknown secret text'})
        self.assertEqual(result['error']['code'], -32601)
        self.assertEqual(self.records()[-1]['status'], 'error')
        self.assertNotIn('unknown secret text', json.dumps(result) + json.dumps(self.records()))

    def test_stdio_lifecycle_is_clean_json(self):
        messages = [ {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'},
                     {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                     {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'health'}}]
        run = subprocess.run([sys.executable, str(ROOT / 'tools/swag_mcp_server.py')],
            input=''.join(json.dumps(item) + '\n' for item in messages), capture_output=True, text=True, check=True)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([row['id'] for row in rows], [1, 2])
        self.assertEqual(run.stderr, '')
        self.assertEqual(json.loads(rows[1]['result']['content'][0]['text'])['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
