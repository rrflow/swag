import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_capture_watch as watch
from jsonschema import ValidationError


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.context = self.root / 'task.json'
        self.context.write_text(json.dumps({'schemaVersion': 1, 'issueTitle': 'Fixture task'}))
        self.output = self.root / 'observations.jsonl'
        self.git('init', '-q')
        self.git('config', 'user.name', 'Capture fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        (self.repo / 'code.py').write_text('original\n')
        self.git('add', 'code.py')
        self.git('commit', '-qm', 'Create fixture')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, check=True)

    def capture(self):
        return watch.capture_once(self.repo, self.context, self.output)

    def rows(self):
        return [json.loads(row) for row in self.output.read_text().splitlines()]

    def test_same_path_edits_staging_and_returning_to_old_content(self):
        self.assertTrue(self.capture())
        original = self.output.read_bytes()
        self.assertFalse(self.capture())
        (self.repo / 'code.py').write_text('first edit\n')
        self.assertTrue(self.capture())
        (self.repo / 'code.py').write_text('second edit\n')
        self.assertTrue(self.capture())
        self.git('add', 'code.py')
        self.assertTrue(self.capture())
        self.git('reset', '-q', 'HEAD', '--', 'code.py')
        (self.repo / 'code.py').write_text('original\n')
        self.assertTrue(self.capture())
        rows = self.rows()
        self.assertEqual(len(rows), 5)
        self.assertTrue(self.output.read_bytes().startswith(original))
        self.assertEqual(rows[0]['source_snapshot']['snapshot_sha256'], rows[-1]['source_snapshot']['snapshot_sha256'])
        self.assertNotEqual(rows[0]['record_id'], rows[-1]['record_id'])
        self.assertEqual(rows[2]['source_snapshot']['previous_record_id'], rows[1]['record_id'])
        self.assertEqual(rows[1]['repo_context']['changed_files'], rows[2]['repo_context']['changed_files'])

    def test_restart_deduplicates_and_override_is_not_a_label(self):
        self.capture()
        command = [sys.executable, str(ROOT / 'tools/swag_capture_watch.py'), '--repo', str(self.repo),
                   '--context', str(self.context), '--output', str(self.output), '--once']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['state'], 'unchanged')
        self.context.write_text(json.dumps({'schemaVersion': 1, 'issueTitle': 'New fixture title',
            'userOverride': True, 'route': {'provider': 'fixture', 'modelId': 'fixture-model',
            'effort': 'low', 'accessMode': 'local', 'bindingId': 'fixture-binding'}}))
        self.assertTrue(self.capture())
        last = self.rows()[-1]
        self.assertTrue(last['user_override'])
        self.assertFalse(last['training_consent'])
        self.assertEqual(last['label_status'], 'unreviewed')
        self.assertIsNone(last['outcome']['tests_passed'])

    def test_invalid_or_changing_context_can_recover(self):
        self.capture()
        retained = self.output.read_bytes()
        self.context.write_text('{"schemaVersion":1,')
        with self.assertRaises(ValueError):
            self.capture()
        self.assertEqual(self.output.read_bytes(), retained)
        self.context.write_text(json.dumps({'schemaVersion': 1, 'issueTitle': 'Recovered edit'}))
        first = watch.observe(self.repo, self.context)
        changed = (first[0], {**first[1], 'context_sha256': '0' * 64}, first[2])
        with patch.object(watch, 'observe', side_effect=[first, changed]):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                self.capture()
        self.assertTrue(self.capture())
        self.assertEqual(len(self.rows()), 2)

    def test_metadata_only_redaction_and_explicit_untracked_exclusion(self):
        secret = 'sk-' + 'a' * 30
        self.context.write_text(json.dumps({'schemaVersion': 1, 'issueTitle': 'Remove ' + secret}))
        (self.repo / 'code.py').write_text(secret)
        self.capture()
        self.assertNotIn(secret, self.output.read_text())
        (self.repo / 'untracked.txt').write_text('outside declared scope')
        self.assertFalse(self.capture())
        self.assertEqual(self.rows()[0]['source_snapshot']['scope'], 'tracked_files_only')

    def test_bounds_and_partial_output_preserve_existing_data(self):
        with self.assertRaises(ValueError):
            watch.git_bytes(self.repo, 'show', 'HEAD:code.py', limit=2)
        self.context.write_bytes(b'x' * (watch.MAX_CONTEXT_BYTES + 1))
        with self.assertRaises(ValueError):
            self.capture()
        self.context.write_text(json.dumps({'schemaVersion': 1, 'issueTitle': 'Fixture task'}))
        self.output.write_bytes(b'{"partial":')
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.capture()
        self.assertEqual(self.output.read_bytes(), b'{"partial":')
        self.assertFalse(self.output.with_suffix('.jsonl.lock').exists())
        with self.assertRaises(ValueError):
            watch.capture_once(self.repo, self.context, self.repo / 'feedback.jsonl')

    def test_forged_training_permission_and_duplicate_context_rejected(self):
        self.context.write_text('{"schemaVersion":1,"issueTitle":"x","training_consent":true}')
        with self.assertRaises(ValidationError):
            self.capture()
        self.context.write_text('{"schemaVersion":1,"issueTitle":"a","issueTitle":"b"}')
        with self.assertRaises(ValueError):
            self.capture()

    def test_running_poll_process_captures_later_edit_and_stops_at_record_limit(self):
        command = [sys.executable, str(ROOT / 'tools/swag_capture_watch.py'), '--repo', str(self.repo),
                   '--context', str(self.context), '--output', str(self.output),
                   '--interval-seconds', '0.25', '--duration-seconds', '15', '--max-records', '2']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not self.output.exists() or not self.output.read_bytes().endswith(b'\n'):
                self.assertIsNone(process.poll())
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.05)
            (self.repo / 'code.py').write_text('edit while collector is running\n')
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(len(self.rows()), 2)
            self.assertEqual(json.loads(stdout.splitlines()[-1]),
                             {'state': 'stopped', 'recordsWritten': 2, 'trainingAuthorized': False})
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
