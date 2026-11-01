import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_collect_routing_tasks as collector


class CollectionTests(unittest.TestCase):
    def test_real_source_shape_does_not_invent_review_or_provider_outcome(self):
        pull = {'number': 1, 'title': 'Fixture task', 'url': 'https://example.test/1',
                'mergedAt': '2026-10-01T00:00:00Z', 'headRefOid': 'a' * 40, 'mergeCommit': {'oid': 'b' * 40}}
        details = {'files': [{'path': 'docs/guide.md'}], 'statusCheckRollup': [], 'reviewDecision': 'APPROVED'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'output'
            with patch.object(collector, 'gh_json', side_effect=[[pull], details, [], []]):
                manifest = collector.collect(root, 30)
            row = json.loads((root / 'review-candidates.jsonl').read_text())
            self.assertEqual(row['reviewStatus'], 'pending')  # PR approval is not routing-label review.
            self.assertIsNone(row['optimalProviderRoute'])
            self.assertFalse(row['trainingAdmitted'])
            self.assertEqual(hashlib.sha256((root / 'review-candidates.jsonl').read_bytes()).hexdigest(), manifest['candidateSha256'])
            source = root / 'sources' / (row['sourceSha256'] + '.json')
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row['sourceSha256'])


if __name__ == '__main__':
    unittest.main()
