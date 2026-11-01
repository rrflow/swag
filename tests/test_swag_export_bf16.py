import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExportGuards(unittest.TestCase):
    def invoke(self, metadata):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapter = root / 'adapter'
            adapter.mkdir()
            (adapter / 'training_metadata.json').write_text(json.dumps(metadata))
            manifest = root / 'base.json'
            manifest.write_text(json.dumps({'revision': 'a' * 40}))
            result = subprocess.run([sys.executable, str(ROOT / 'tools/swag_export_bf16.py'),
                '--base-dir', str(root / 'missing-base'), '--base-manifest', str(manifest),
                '--adapter-dir', str(adapter), '--output-dir', str(root / 'output')], capture_output=True, text=True)
            self.assertFalse((root / 'output').exists())
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('ModuleNotFoundError', result.stderr)  # Reject before optional GPU dependencies.
            return result.stderr

    def test_no_training_steps_cannot_be_exported_as_trained(self):
        self.assertIn('completed, nonquantized BF16', self.invoke({'global_step': 0}))

    def test_quantized_training_not_claimed_as_bf16_baseline(self):
        self.assertIn('completed, nonquantized BF16', self.invoke({'global_step': 10, 'precision': 'bf16', 'base_quantized': True}))

    def test_revision_mismatch_rejected(self):
        self.assertIn('base revision mismatch', self.invoke({'global_step': 10, 'precision': 'bf16',
            'base_quantized': False, 'model_revision': 'b' * 40}))


if __name__ == '__main__':
    unittest.main()
