import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_evidence_projection as projection
import swag_routing_contract as contract
import swag_routing_eval as evaluation
import swag_learning_candidates as learning


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        request = {'projectIntent': 'PRIVATE PROJECT TEXT', 'taskText': 'PRIVATE TASK TEXT',
                   'minimumQuality': 1, 'maxCost': 0, 'requestedEffort': 'high',
                   'localOnly': False, 'candidates': []}
        expected = {'bindingId': None, 'effort': None}
        protocol = {'scope': 'development', 'cases': [{'caseId': 'private-issue-title',
                    'request': request, 'expected': expected}],
                    'implementation': evaluation.implementation_hashes(),
                    'limits': {'minimumCases': 1, 'minimumAccuracy': 1,
                               'maximumPolicyViolations': 0, 'maximumInvalidOutputs': 0,
                               'maximumP95Seconds': 10}}
        raw = '{"bindingId":"forbidden","effort":"high"}'
        row = {'caseId': 'private-issue-title', 'expected': expected, 'requestSha256': contract.digest(request),
               'rawOutput': raw, 'elapsedSeconds': 1.0, **contract.score_output(raw, request, expected)}
        artifact = {'model': 'fixture-model', 'precision': 'bfloat16', 'custom_checkpoint': False,
                    'privateLocation': '/private/source', 'credential': 'SECRET'}
        contents = {'protocol.json': contract.canonical_bytes(protocol),
                    'results.jsonl': contract.canonical_bytes(row) + b'\n',
                    'artifact-manifest.json': contract.canonical_bytes(artifact)}
        for name, data in contents.items():
            (self.root / name).write_bytes(data)
        summary = {**evaluation.summarize([row], protocol['limits']), 'scope': 'development',
                   'completedAt': '2026-10-28T16:50:00+00:00',
                   **{key: hashlib.sha256(contents[name]).hexdigest() for key, name in (
                      ('protocolSha256', 'protocol.json'), ('resultsSha256', 'results.jsonl'),
                      ('artifactManifestSha256', 'artifact-manifest.json'))}}
        (self.root / 'summary.json').write_bytes(contract.canonical_bytes(summary))

    def test_projection_redacts_content_and_never_grants_authority(self):
        result = projection.project_run(self.root)
        serialized = json.dumps(result)
        for secret in ['PRIVATE', 'SECRET', '/private/source', 'private-issue-title', 'forbidden']:
            self.assertNotIn(secret, serialized)
        self.assertEqual(result['metrics']['policyViolations'], 1)
        self.assertFalse(result['authority']['trainingAuthorized'])
        self.assertFalse(result['metrics']['deploymentQualified'])
        self.assertEqual(result['learningSuggestions'][0]['state'], 'suggested')

    def test_exported_signal_event_is_content_free_and_idempotent(self):
        projected = projection.project_run(self.root)
        first = projection.report_record(projected, 'swag')
        self.assertEqual(first, projection.report_record(projected, 'swag'))
        self.assertNotEqual(first['event_id'], projection.report_record(projected, 'other')['event_id'])
        self.assertEqual(first['schema'], 'rroflow.turn/v1')
        self.assertIsNone(first['content'])
        self.assertEqual(first['usage']['input_tokens'], 0)  # Report projection invokes no model.
        self.assertEqual(first['tools'], [])
        self.assertIsNone(first['signals'][0]['evidence'][0]['excerpt'])

    def test_distinct_checkpoints_with_identical_outputs_remain_distinct(self):
        # Development-only protocol fixtures; these are not admitted model data.
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            for path in self.root.iterdir():
                (other / path.name).write_bytes(path.read_bytes())
            manifest_path = other / 'artifact-manifest.json'
            manifest = json.loads(manifest_path.read_bytes())
            manifest['custom_checkpoint'] = True
            manifest_path.write_bytes(contract.canonical_bytes(manifest))
            summary_path = other / 'summary.json'
            summary = json.loads(summary_path.read_bytes())
            summary['artifactManifestSha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            summary_path.write_bytes(contract.canonical_bytes(summary))

            first = projection.project_run(self.root)
            second = projection.project_run(other)
            self.assertEqual(first['provenance']['protocolSha256'], second['provenance']['protocolSha256'])
            self.assertEqual(first['provenance']['resultsSha256'], second['provenance']['resultsSha256'])
            self.assertNotEqual(first['runId'], second['runId'])
            self.assertNotEqual(projection.report_record(first, 'swag')['event_id'],
                                projection.report_record(second, 'swag')['event_id'])
            proposed = learning.propose([self.root, other, self.root])
            self.assertEqual(proposed['runs'], 2)
            self.assertTrue(proposed['candidates'])
            for candidate in proposed['candidates']:
                self.assertEqual(len(candidate['evidence']), 2)
                self.assertFalse(candidate['trainingAuthorized'])
                self.assertFalse(candidate['promotionAuthorized'])

    def test_changed_results_rejected(self):
        with (self.root / 'results.jsonl').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            projection.project_run(self.root)

    def test_untrusted_summary_cannot_fabricate_performance(self):
        path = self.root / 'summary.json'
        summary = json.loads(path.read_text())
        summary['matched'] = 1
        path.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, 'Summary metrics'):
            projection.project_run(self.root)

    def test_rehashed_output_cannot_keep_a_false_success_label(self):
        path = self.root / 'results.jsonl'
        row = json.loads(path.read_text())
        row['matched'] = True
        path.write_bytes(contract.canonical_bytes(row) + b'\n')
        summary_path = self.root / 'summary.json'
        summary = json.loads(summary_path.read_text())
        summary['resultsSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        summary_path.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError, 'scores disagree'):
            projection.project_run(self.root)


if __name__ == '__main__':
    unittest.main()
