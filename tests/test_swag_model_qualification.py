import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_model_qualification as qualification


class QualificationTests(unittest.TestCase):
    def test_bare_attestation_boolean_is_not_serving_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(qualification.serving_identity_present(Path(directory),
                {'serverIdentityAttested': True}, {'files': {'weights': {'sha256': 'a' * 64}}}))

    def test_missing_evidence_cannot_pass(self):
        result = qualification.assess({}, None)
        self.assertFalse(result['comparisonEvidencePassed'])
        self.assertFalse(result['deploymentQualified'])
        self.assertEqual(len(result['reasons']), 4)

    def test_development_scope_and_unbound_lineage_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = {}
            for arm in qualification.ARMS:
                run = root / arm
                run.mkdir()
                runs[arm] = run
                (run / 'summary.json').write_text(json.dumps({'arm': arm, 'artifactManifestSha256': arm,
                                                             'protocolSha256': 'same', 'serverIdentityAttested': False}))
                (run / 'protocol.json').write_text('{}')
                (run / 'artifact-manifest.json').write_text(json.dumps({'files': {'weights': {'sha256': 'a'*64}}}))
            view = {'scope': 'development', 'provenance': {'protocolSha256': 'same'},
                    'metrics': {'protocolPassed': True, 'policyViolations': 0, 'accuracy': 1}}
            with patch.object(qualification, 'project_run', return_value=view):
                result = qualification.assess(runs, None)
            reasons = '\n'.join(result['reasons'])
            self.assertIn('development evidence', reasons)
            self.assertIn('lineage', reasons)
            self.assertIn('exactly the custom', reasons)
            self.assertIn('total serving memory', reasons)
            self.assertFalse(result['comparisonEvidencePassed'])

    def test_weight_file_bytes_do_not_count_as_serving_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / 'summary.json').write_text(json.dumps({'arm': 'custom_quantized', 'protocolSha256': 'a',
                'artifactManifestSha256': 'b', 'serverIdentityAttested': False}))
            (run / 'protocol.json').write_text('{}')
            (run / 'artifact-manifest.json').write_text(json.dumps({'files': {'weights': {}}}))
            (run / 'serving-memory.json').write_text(json.dumps({'scope': 'weights_only', 'bytes': 28_000_000_000}))
            view = {'scope': 'acceptance', 'provenance': {}, 'metrics': {'protocolPassed': True, 'policyViolations': 0}}
            with patch.object(qualification, 'project_run', return_value=view):
                result = qualification.assess({'custom_quantized': run}, None)
            self.assertTrue(any('memory evidence' in reason for reason in result['reasons']))


if __name__ == '__main__':
    unittest.main()
