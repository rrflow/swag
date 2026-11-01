"""Refusal checks only: no training data, provider calls or GPU jobs are created."""
from __future__ import annotations

import contextlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
pipeline = importlib.import_module("swag_training_pipeline")
runbook = importlib.import_module("run_training_job")


class LegacyTrainingRetirementTests(unittest.TestCase):
    def test_all_generator_entry_points_refuse_before_reading_or_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = (
                lambda: pipeline.run_pipeline(root / "pipeline.yaml"),
                lambda: pipeline.build_controller_sft_dataset(root, root / "rows.jsonl"),
                lambda: pipeline.build_runbooks(root / "models.yaml", root / "cluster.yaml",
                                                {}, root / "runs", root / "rows.jsonl"),
            )
            with patch.object(pipeline, "_load_yaml", side_effect=AssertionError("read config")), \
                    patch.object(pipeline, "_scenario_dirs", side_effect=AssertionError("read inputs")):
                for call in calls:
                    with self.subTest(call=call), self.assertRaisesRegex(RuntimeError, "retired"):
                        call()
            self.assertEqual(list(root.iterdir()), [])

    def test_execute_refuses_before_runbook_read_or_process_dispatch(self):
        # Deliberately no valid command or dataset: any attempted I/O is a failure.
        with patch.object(sys, "argv", ["run_training_job.py", "--runbook", "absent.json",
                                        "--step", "train", "--execute"]), \
                patch.object(runbook, "_load_json", side_effect=AssertionError("read runbook")), \
                patch.object(subprocess, "run", side_effect=AssertionError("launched process")):
            with self.assertRaisesRegex(SystemExit, "retired"):
                runbook.main()

    def test_execute_cannot_hide_behind_list_steps(self):
        with patch.object(sys, "argv", ["run_training_job.py", "--runbook", "absent.json",
                                        "--list-steps", "--execute"]):
            with self.assertRaisesRegex(SystemExit, "retired"):
                runbook.main()

    def test_historical_runbook_can_still_be_inspected_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runbook.json"
            # An inert CLI fixture, never submitted to a shell or a trainer.
            path.write_text(json.dumps({"commands": {"archived": "historical command text"}}),
                            encoding="utf-8")
            for arguments, expected in ((["--list-steps"], "archived"),
                                        (["--step", "archived"], "historical command text")):
                with patch.object(sys, "argv", ["run_training_job.py", "--runbook", str(path),
                                                *arguments]), \
                        patch.object(subprocess, "run", side_effect=AssertionError("launched")), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(runbook.main(), 0)
                    self.assertEqual(output.getvalue().strip(), expected)

    def test_raw_lora_entry_point_refuses_without_gpu_packages(self):
        result = subprocess.run([sys.executable, "-S", str(ROOT / "tools/swag_lora_train.py"),
                                 "--model", "absent", "--dataset-jsonl", "absent",
                                 "--output-dir", "absent"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_pipeline_cli_refuses_without_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-S",
                                     str(ROOT / "tools/swag_training_pipeline.py"),
                                     "--config", "absent.yaml"], cwd=directory,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retired", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_supported_trainer_requires_admission_before_gpu_imports(self):
        result = subprocess.run([sys.executable, "-S", str(ROOT / "tools/swag_unsloth_train.py"),
                                 "--model", "absent", "--dataset-jsonl", "absent",
                                 "--output-dir", "absent", "--seed", "1"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("training requires --admitted-dataset-dir", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_legacy_ui_callable_refuses_instead_of_generating_data(self):
        ui = importlib.import_module("swag_ops_ui")
        # Exercise the same callable used by the HTTP job, without starting a UI server.
        context = object.__new__(ui.OpsContext)
        context.pipeline_config = Path("absent.yaml")
        with self.assertRaisesRegex(RuntimeError, "retired"):
            context.run_training_pipeline()


if __name__ == "__main__":
    unittest.main()
