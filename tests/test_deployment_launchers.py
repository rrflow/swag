"""Launch scripts must not report an absent service as a deployment."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if os.name == "nt" and shutil.which("git"):
    candidate = Path(shutil.which("git")).resolve().parents[1] / "bin" / "bash.exe"
    if candidate.is_file():
        BASH = str(candidate)


@unittest.skipUnless(BASH, "Bash is required to exercise the shell launchers")
class DeploymentLauncherTests(unittest.TestCase):
    def run_script(self, script, *, env=None):
        return subprocess.run(
            [BASH, script.as_posix()], capture_output=True, text=True,
            timeout=15, env=env, cwd=ROOT,
        )

    def test_unimplemented_services_fail_explicitly(self):
        for name in ("rrflow", "connectome"):
            with self.subTest(service=name):
                result = self.run_script(ROOT / "deploy/scripts" / f"start-{name}.sh")
                self.assertEqual(result.returncode, 2)
                self.assertIn("was not started", result.stderr)

    def test_bootstrap_preserves_configuration_and_creates_no_engine_state(self):
        with tempfile.TemporaryDirectory() as directory:
            deployment = Path(directory) / "deploy"
            shutil.copytree(ROOT / "deploy", deployment,
                            ignore=shutil.ignore_patterns("*.env", "evidence", "connection.json"))
            script = deployment / "scripts/bootstrap-local-stack.sh"
            first = self.run_script(script)
            self.assertEqual(first.returncode, 0, first.stderr)
            config = deployment / "env/swag.env"
            self.assertIn("SWAG_HOST=127.0.0.1", config.read_text())
            config.write_text("# Existing user configuration\n", encoding="utf-8")
            second = self.run_script(script)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(config.read_text(), "# Existing user configuration\n")
            self.assertFalse((deployment / "rrflow/connection.json").exists())
            self.assertFalse((deployment / "evidence").exists())

    def test_swag_launcher_propagates_real_cli_failure(self):
        # Invalid CLI input must fail before opening a listener or calling a model.
        with tempfile.TemporaryDirectory() as directory:
            deployment = Path(directory) / "deploy"
            shutil.copytree(ROOT / "deploy", deployment,
                            ignore=shutil.ignore_patterns("*.env", "evidence"))
            # The actual launcher resolves its service relative to its deployment.
            (Path(directory) / "tools").mkdir()
            shutil.copy2(ROOT / "tools/swag_decision_service.py",
                         Path(directory) / "tools/swag_decision_service.py")
            env = {**os.environ, "SWAG_PYTHON": sys.executable,
                   "PYTHONPATH": str(ROOT / "tools"), "SWAG_PORT": "invalid"}
            result = self.run_script(deployment / "scripts/start-swag.sh", env=env)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("invalid int value", result.stderr)


if __name__ == "__main__":
    unittest.main()
