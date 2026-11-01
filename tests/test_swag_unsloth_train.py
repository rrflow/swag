"""CPU checks of input handling; these do not qualify GPU training."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("swag_unsloth_train", ROOT / "tools/swag_unsloth_train.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TrainingInputTests(unittest.TestCase):
    def rows(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return runner._training_rows(path)

    def test_preserves_chat_and_target_without_flattening(self):
        messages = [{"role": "user", "content": "Check this"},
                    {"role": "assistant", "content": '{"allow":false}'}]
        self.assertEqual(self.rows([{"messages": messages, "source": "fixture"}]),
                         [{"messages": messages}])

    def test_rejects_unlabelled_chat(self):
        with self.assertRaisesRegex(ValueError, "no assistant"):
            self.rows([{"messages": [{"role": "user", "content": "Check this"}]}])

    def test_checks_every_row(self):
        with self.assertRaisesRegex(ValueError, "Row 1"):
            self.rows([{"text": "valid"}, {"text": ""}])

    def test_rejects_mixed_formats(self):
        with self.assertRaisesRegex(ValueError, "mix"):
            self.rows([{"text": "valid"}, {"messages": [{"role": "assistant", "content": "yes"}]}])

    def test_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.jsonl"
            path.write_text('{"text":"one"}\n{"text":"two"}\n', encoding="utf-8")
            self.assertEqual(len(runner._training_rows(path)), 2)

    def test_eval_without_dataset_rejected_before_imports(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/swag_unsloth_train.py"),
                                 "--model", "unused", "--dataset-jsonl", "unused",
                                 "--output-dir", "unused", "--eval-steps", "1"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --eval-dataset-jsonl", result.stderr)


if __name__ == "__main__":
    unittest.main()
