import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_passive_capture as capture


class CaptureTests(unittest.TestCase):
    def test_git_error_is_unknown_not_clean(self):
        with patch.object(capture.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'failed')):
            self.assertIsNone(capture._collect_changed_files(ROOT, None))

    def test_git_rename_preserves_both_names_and_quotes(self):
        result = subprocess.CompletedProcess([], 0, 'R  new name.py\0old name.py\0 M a\'b.py\0', '')
        with patch.object(capture.subprocess, 'run', return_value=result):
            self.assertEqual(capture._collect_changed_files(ROOT, None), ['new name.py', 'old name.py', "a'b.py"])

    def test_two_captures_preserve_first_record(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            capture.append_record(output, {'id': 'first'})
            capture.append_record(output, {'id': 'second'})
            self.assertEqual([json.loads(row)['id'] for row in output.read_text().splitlines()],
                             ['first', 'second'])

    def test_partial_tail_is_preserved_and_lock_released(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            output.write_bytes(b'{"partial":')
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                capture.append_record(output, {'id': 'second'})
            self.assertEqual(output.read_bytes(), b'{"partial":')
            self.assertFalse(output.with_name(output.name + '.lock').exists())

    def test_busy_writer_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            lock = output.with_name(output.name + '.lock')
            lock.write_text('owner')
            with self.assertRaises(FileExistsError):
                capture.append_record(output, {'id': 'second'})
            self.assertEqual(lock.read_text(), 'owner')

    def test_unknown_outcomes_are_not_training_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/swag_passive_capture.py'),
                '--intent-text', 'fixture only', '--selected-question-ids', 'fixture.check',
                '--changed-files', 'fixture.py', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(output.read_text())
            self.assertIsNone(record['confidence'])
            self.assertIsNone(record['user_acceptance'])
            self.assertTrue(all(value is None for value in record['outcome'].values()))
            self.assertFalse(record['training_consent'])
            self.assertEqual(record['label_status'], 'unreviewed')
            from jsonschema import Draft202012Validator
            validator = Draft202012Validator(json.loads(capture.DEFAULT_SCHEMA.read_text()))
            validator.validate(record)
            for change in ({'label_status':'verified'}, {'training_consent':True},
                           {'route':{**record['route'], 'accessMode':'invented'}}):
                self.assertTrue(list(validator.iter_errors({**record, **change})))


if __name__ == '__main__':
    unittest.main()
