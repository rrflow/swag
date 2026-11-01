"""Checks that the publishable tree excludes local-only material."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ONLY = (
    ".cursor/",
    ".swag/",
    ".test-tmp/",
    ".venv/",
    "Microsoft/",
    "chat-archive/",
    "chat-candidates/",
    "ui/dist/",
    "ui/node_modules/",
)
ALLOWED_GENERATED = {
    "files/controller_experiments/promotion_scorecard.json",
    "files/controller_experiments/tier_metrics.spark_latest.json",
}
PRIVATE_TEXT = re.compile(
    rb"/home/hades"
    rb"|D:/localdev"
    rb"|clyffy-0\d"
    rb"|\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"
)


@unittest.skipUnless(shutil.which("git") and (ROOT / ".git").exists(), "requires a git checkout")
class PublicBoundaryTests(unittest.TestCase):
    def setUp(self):
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        self.paths = [path.decode("utf-8") for path in listed.stdout.split(b"\0") if path]

    def test_local_only_paths_are_excluded(self):
        leaked = [path for path in self.paths if path.startswith(LOCAL_ONLY)]
        self.assertEqual(leaked, [])

    def test_generated_files_are_allowlisted(self):
        generated = {path for path in self.paths if path.startswith("files/")}
        self.assertEqual(generated - ALLOWED_GENERATED, set())

    def test_configuration_reference_is_included(self):
        self.assertIn(".env.example", self.paths)

    def test_text_has_no_private_infrastructure(self):
        own_path = Path(__file__).resolve()
        found = []
        for path in self.paths:
            candidate = ROOT / path
            if candidate.resolve() == own_path or not candidate.is_file():
                continue
            content = candidate.read_bytes()
            if b"\0" not in content and PRIVATE_TEXT.search(content):
                found.append(path)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
