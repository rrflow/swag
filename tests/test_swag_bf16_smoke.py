import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from swag_bf16_smoke import policy_oracle


class SmokeOracleTests(unittest.TestCase):
    def test_handwritten_gold_matches_policy_for_all_cases(self):
        protocol=json.loads((ROOT/'config/training/routing_smoke.json').read_text())
        self.assertEqual(len(protocol['cases']),8)
        for case in protocol['cases']:
            candidates=copy.deepcopy(protocol['candidates'])
            if case.get('exhaustQuota'):
                for candidate in candidates:
                    candidate['quotaAvailable']=False
            with self.subTest(case=case['id']):
                self.assertEqual(policy_oracle(case['input'],candidates),case['expected'])


if __name__=='__main__':
    unittest.main()
