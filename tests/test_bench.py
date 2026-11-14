"""The competitor bench: runner and scorer against scripted SystemOne servers. Software tests, not results."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench'))
sys.path.insert(0, str(ROOT / 'tools'))

import run as bench_run
import score as bench_score

ROWS = [
    {'id': f'r{i}', 'benchmark': 'toy', 'state': {'n': i},
     'questions': {'q': {'type': 'choice', 'instructions': 'Pick.', 'criteria': {'A': 'a', 'B': 'b'}}},
     'expected': {'q': 'A' if i % 2 == 0 else 'B'}}
    for i in range(10)
] + [{'id': 'yes', 'benchmark': 'toy-binary', 'state': 'x', 'questions': {'b': {'type': 'noul'}}, 'expected': {'b': 'true'}}]


class AlwaysA(BaseHTTPRequestHandler):
    def log_message(self, *arguments):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.seen.append(self.headers.get('Authorization'))
        answers = {}
        for key, question in body['questions'].items():
            if question['type'] == 'noul':
                answers[key] = {'type': 'noul', 'noul': 0.8}
            else:
                answers[key] = {'type': 'choice', 'choice': 'A', 'confidence': 0.8, 'probabilities': {'A': 0.9, 'B': 0.1}}
        encoded = json.dumps({'answers': answers, 'usage': {'input_tokens': 1}}).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class BenchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), AlwaysA)
        self.server.seen = []
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}/v1/systemone'

    def write(self, name, value):
        path = self.directory / name
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')
        return path

    def test_every_arm_gets_the_same_rows_and_credentials_stay_out_of_results(self):
        arms = self.write('arms.json', [{'name': 'scripted', 'url': self.url, 'credentialEnv': 'BENCH_KEY'}])
        rows = self.write('rows.jsonl', '\n'.join(json.dumps(row) for row in ROWS))
        with patch.dict(os.environ, {'BENCH_KEY': 'secret-value'}):
            bench_run.main(['--arms', str(arms), '--rows', str(rows), '--out', str(self.directory / 'out')])
        results = (self.directory / 'out' / 'scripted.jsonl').read_text()
        self.assertEqual(len(results.splitlines()), len(ROWS))
        self.assertNotIn('secret-value', results)
        self.assertEqual(set(self.server.seen), {'Bearer secret-value'})
        report = bench_score.score(ROWS, {'scripted': [json.loads(line) for line in results.splitlines()]})
        toy = report['arms']['scripted']['toy']
        self.assertEqual((toy['accuracy'], toy['errors']), (0.5, 0))
        # Always 0.9 sure and right half the time: calibration error 0.4.
        self.assertAlmostEqual(toy['ece'], 0.4)
        self.assertEqual(report['arms']['scripted']['toy-binary']['accuracy'], 1.0)

    def test_unsafe_arm_urls_and_missing_credentials_are_refused(self):
        for arm in ({'name': 'x', 'url': 'http://example.com/v1/systemone'},
                    {'name': 'x', 'url': 'https://example.com/v1/other'},
                    {'name': 'x', 'url': self.url, 'credentialEnv': 'NOT_SET_ANYWHERE'},
                    {'name': 'x', 'url': self.url, 'surprise': True}):
            with self.subTest(arm=arm), self.assertRaises(SystemExit):
                bench_run.load_arms(self.write('arms.json', [arm]))

    def test_errors_and_missing_rows_count_as_wrong(self):
        results = [{'id': 'r0', 'status': 'ok', 'seconds': 0.1, 'answers': {'q': {'type': 'choice', 'probabilities': {'A': 1.0, 'B': 0.0}}}},
                   {'id': 'r2', 'status': 'error', 'seconds': 0.1}]
        toy = bench_score.score(ROWS[:4], {'arm': results})['arms']['arm']['toy']
        self.assertEqual((toy['rows'], toy['errors'], toy['accuracy']), (4, 3, 0.25))

    def test_paired_test_and_interval_math(self):
        self.assertEqual(bench_score.mcnemar(0, 0), 1.0)
        self.assertAlmostEqual(bench_score.mcnemar(10, 0), 2 / 2 ** 10)
        low, high = bench_score.wilson(50, 100)
        self.assertTrue(low < 0.5 < high and math.isclose(low + high, 1.0, abs_tol=1e-3))


if __name__ == '__main__':
    unittest.main()
