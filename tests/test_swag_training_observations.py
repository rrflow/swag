"""Callback/control software probes; these are not training data or GPU evidence."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from swag_training_observations import TrainingObserver, progress


class ObservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def test_missing_state_is_unknown(self):
        self.assertEqual(progress(self.directory)['state'], 'not_recorded')

    def test_retained_real_training_history_projects_without_qualification(self):
        value = progress(ROOT / 'tests/fixtures/training-recorded')
        self.assertEqual(value['globalStep'], 33)
        self.assertEqual(value['maxSteps'], 33)
        self.assertEqual(len(value['points']), 37)
        self.assertEqual(value['processLiveness'], 'unknown')
        self.assertFalse(value['completionVerified'])

    def test_observations_exclude_prompt_and_unbounded_metrics(self):
        observer = TrainingObserver(self.directory)
        try:
            observer.emit('progress', SimpleNamespace(global_step=1, max_steps=2),
                          {'loss': .4, 'prompt': 'private input', 'learning_rate': float('nan')})
        finally:
            observer.close()
        self.assertNotIn('private input', observer.path.read_text())
        schema = json.loads((ROOT / 'config/training/training_observation.schema.json').read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(json.loads(observer.path.read_text()))
        value = progress(self.directory)
        self.assertEqual(value['points'], [{'step': 1, 'loss': .4}])
        self.assertEqual(value['processLiveness'], 'unknown')
        self.assertFalse(value['completionVerified'])

    def test_stop_requests_checkpoint_and_never_marks_completion(self):
        observer = TrainingObserver(self.directory)
        try:
            with patch.dict(sys.modules, {'transformers': SimpleNamespace(TrainerCallback=object)}):
                callback = observer.callback()
            state = SimpleNamespace(global_step=1, max_steps=2)
            control = SimpleNamespace(should_training_stop=False, should_save=False)
            observer.request_stop()
            callback.on_step_end(None, state, control)
            self.assertTrue(control.should_training_stop)
            self.assertTrue(control.should_save)
            self.assertEqual(progress(self.directory)['lastObservation'], 'stop_observed')
            self.assertFalse(progress(self.directory)['completionVerified'])
        finally:
            observer.close()

    def test_partial_tail_preserves_only_completed_observations(self):
        observer = TrainingObserver(self.directory)
        observer.emit('progress', SimpleNamespace(global_step=1, max_steps=2), {'loss': .4})
        observer.close()
        with observer.path.open('a') as output:
            output.write('{"incomplete":')
        value = progress(self.directory)
        self.assertTrue(value['incompleteTail'])
        self.assertEqual(value['globalStep'], 1)
        self.assertFalse(value['completionVerified'])

    def test_out_of_sequence_file_rejects(self):
        observer = TrainingObserver(self.directory)
        observer.emit('started', SimpleNamespace(global_step=0, max_steps=2))
        observer.close()
        row = json.loads(observer.path.read_text())
        row['sequence'] = 2
        observer.path.write_text(json.dumps(row) + '\n')
        self.assertEqual(progress(self.directory)['state'], 'invalid_state')

    def test_failure_before_first_step_remains_visible_without_invented_progress(self):
        observer = TrainingObserver(self.directory)
        observer.emit('failed', SimpleNamespace(global_step=0, max_steps=0), error_type='RuntimeError')
        observer.close()
        value = progress(self.directory)
        self.assertEqual(value['lastObservation'], 'failed')
        self.assertEqual(value['lastErrorType'], 'RuntimeError')
        self.assertIsNone(value['globalStep'])
        self.assertFalse(value['completionVerified'])

    def test_budget_is_bounded(self):
        observer = TrainingObserver(self.directory, limit_bytes=1024)
        try:
            with self.assertRaisesRegex(ValueError, 'byte budget'):
                for _ in range(20):
                    observer.emit('started')
            self.assertLessEqual(observer.path.stat().st_size, 1024)
        finally:
            observer.close()

    def test_invalid_saved_state_is_not_success(self):
        (self.directory / 'trainer_state.json').write_text('{"global_step":4,"max_steps":2,"log_history":[]}')
        self.assertEqual(progress(self.directory)['state'], 'invalid_state')


if __name__ == '__main__':
    unittest.main()
