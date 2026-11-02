"""Artifact integrity checks using repository bytes, never model-quality evidence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from swag_training_artifacts import describe, verify


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.content = (ROOT / 'AGENTS.md').read_bytes()
        (self.root / 'source.txt').write_bytes(self.content)
        self.manifest = self.root / 'manifest.json'
        self.data = {'files': {'source.txt': {'bytes': len(self.content), 'sha256': hashlib.sha256(self.content).hexdigest()}}}
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.data))

    def verify(self, **kwargs):
        return verify(self.root, self.manifest, max_bytes=kwargs.get('max_bytes', 100_000))

    def test_actual_repository_bytes_verify_without_model_claims(self):
        result = self.verify()
        self.assertEqual(result['bytes'], len(self.content))
        self.assertFalse(result['qualified'])
        self.assertFalse(result['tensorContentsValidated'])
        self.assertFalse(result['reloadVerified'])

    def test_changed_same_size_bytes_fail(self):
        (self.root / 'source.txt').write_bytes(b'!' + self.content[1:])
        with self.assertRaisesRegex(ValueError, 'content changed'):
            self.verify()

    def test_size_and_budget_fail(self):
        with self.assertRaisesRegex(ValueError, 'byte budget'):
            self.verify(max_bytes=1)
        (self.root / 'source.txt').write_bytes(self.content + b'!')
        with self.assertRaisesRegex(ValueError, 'size changed'):
            self.verify()

    def test_paths_cannot_escape_or_use_windows_streams(self):
        value = self.data['files']['source.txt']
        for name in ('../source.txt', '/source.txt', 'a\\source.txt', 'source.txt:stream', 'a/./source.txt'):
            with self.subTest(name=name):
                self.data['files'] = {name: value}
                self.write_manifest()
                with self.assertRaises(ValueError):
                    self.verify()

    def test_past_receipt_binds_manifest_not_current_weights(self):
        receipt = self.root / 'receipt.json'
        receipt.write_text(json.dumps(self.verify()))
        self.assertEqual(describe(self.manifest, receipt)['verification'], 'past_receipt_matches_manifest')
        (self.root / 'source.txt').write_bytes(b'!' + self.content[1:])
        # The read model explicitly reports a past receipt, never a fresh rehash.
        self.assertEqual(describe(self.manifest, receipt)['verification'], 'past_receipt_matches_manifest')
        with self.assertRaises(ValueError):
            self.verify()
        self.data['model'] = 'changed-identity'
        self.write_manifest()
        self.assertEqual(describe(self.manifest, receipt)['verification'], 'invalid_or_stale_receipt')

    def test_symlink_is_rejected(self):
        path = self.root / 'link.txt'
        try:
            path.symlink_to(self.root / 'source.txt')
        except OSError:
            self.skipTest('Symlink creation unavailable')
        self.data['files'] = {'link.txt': self.data['files']['source.txt']}
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
