import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from swag_d1_eval import make_question


class DecisionQuestionTests(unittest.TestCase):
    def test_preserves_denied_candidates_without_gold_labels(self):
        case = json.loads((ROOT / 'config/training/routing_development.jsonl').read_text().splitlines()[0])
        request = case['request']
        request['candidates'][0]['authorized'] = False
        question, mapping = make_question(request)
        self.assertIn('"authorized":false', question['route']['criteria']['candidate_0'])
        self.assertEqual(mapping['candidate_0'], request['candidates'][0]['bindingId'])
        self.assertIsNone(mapping['abstain'])
        self.assertNotIn('expected', str(question))
        self.assertEqual(len(mapping), len(request['candidates']) + 1)

    def test_empty_choice_set_has_explicit_abstention(self):
        question, mapping = make_question({'candidates': []})
        self.assertEqual(mapping, {'abstain': None})
        self.assertEqual(list(question['route']['criteria']), ['abstain'])


if __name__ == '__main__':
    unittest.main()
