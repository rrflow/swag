import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from baseline_route_selector import select_route
from rrflow_route_gate import RRFlowRouteGate
from semantic_router_adapter import SemanticRouterAdapter


class SemanticRouterBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            'projectIntent': 'Add billing',
            'taskText': 'Need a checkout and subscription flow',
            'minimumQuality': 0.75,
            'maxCost': 20,
            'requestedEffort': 'medium',
            'localOnly': False,
            'candidates': [
                {
                    'bindingId': 'claude-sonnet-4',
                    'provider': 'anthropic',
                    'modelId': 'claude-sonnet-4',
                    'accessMode': 'api',
                    'authorized': True,
                    'healthy': True,
                    'quotaAvailable': True,
                    'location': 'cloud',
                    'quality': 0.9,
                    'cost': 18,
                    'efforts': ['low', 'medium'],
                },
                {
                    'bindingId': 'qwen-coder-bf16',
                    'provider': 'local',
                    'modelId': 'qwen-coder-bf16',
                    'accessMode': 'local',
                    'authorized': True,
                    'healthy': True,
                    'quotaAvailable': True,
                    'location': 'local',
                    'quality': 0.8,
                    'cost': 9,
                    'efforts': ['medium'],
                },
            ],
        }

    def test_baseline_selects_lowest_cost_eligible_binding(self):
        route = select_route(self.request)
        self.assertFalse(route['abstain'])
        self.assertEqual(route['bindingId'], 'qwen-coder-bf16')
        self.assertEqual(route['effort'], 'medium')
        self.assertEqual(route['decision']['bindingId'], 'qwen-coder-bf16')

    def test_rrflow_gate_rejects_invalid_or_stale_proposals(self):
        gate = RRFlowRouteGate()
        accepted = gate.evaluate(self.request, {'decision': {'bindingId': 'qwen-coder-bf16', 'effort': 'medium'}})
        self.assertTrue(accepted['proposalAccepted'])

        rejected = gate.evaluate(self.request, {'decision': {'bindingId': 'claude-sonnet-4', 'effort': 'high'}})
        self.assertFalse(rejected['proposalAccepted'])
        self.assertIn('effort_match', rejected['policyChecks'])

    def test_adapter_wraps_model_output_and_rrflow_gate(self):
        adapter = SemanticRouterAdapter(
            proposer=lambda request: {
                'bindingId': 'qwen-coder-bf16',
                'effort': 'medium',
                'confidence': 0.81,
                'abstain': False,
                'source': 'semantic-router-test',
                'reason': 'cost-aware local candidate',
            },
            gate=RRFlowRouteGate(),
        )
        result = adapter.route(self.request)
        self.assertEqual(result['bindingId'], 'qwen-coder-bf16')
        self.assertTrue(result['accepted'])
        self.assertIn('rrflowValidation', result)


if __name__ == '__main__':
    unittest.main()
