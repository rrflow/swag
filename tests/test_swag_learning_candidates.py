import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_learning_candidates as learning


class LearningCandidateTests(unittest.TestCase):
    def fixture(self):
        return {'runId': 'one', 'provenance': {'resultsSha256': 'a' * 64},
                'signals': [{'signal': 'swag_route_policy_violation', 'score': 2}]}

    def test_duplicate_runs_do_not_inflate_candidates(self):
        with patch.object(learning, 'project_run', return_value=self.fixture()):
            result = learning.propose([Path('one'), Path('duplicate')])
        self.assertEqual(result['runs'], 1)
        self.assertEqual(result['candidates'][0]['observedCount'], 2)
        self.assertFalse(result['candidates'][0]['trainingAuthorized'])
        self.assertFalse(result['routineExecuted'])

    def test_changed_evidence_produces_successor_identity(self):
        original = self.fixture()
        changed = copy.deepcopy(original)
        changed['runId'] = 'two'
        changed['provenance']['resultsSha256'] = 'b' * 64
        with patch.object(learning, 'project_run', return_value=original):
            first = learning.propose([Path('one')])
        with patch.object(learning, 'project_run', return_value=changed):
            second = learning.propose([Path('two')])
        self.assertNotEqual(first['sourceIdentity'], second['sourceIdentity'])
        self.assertNotEqual(first['candidates'][0]['candidateId'], second['candidates'][0]['candidateId'])


if __name__ == '__main__':
    unittest.main()
