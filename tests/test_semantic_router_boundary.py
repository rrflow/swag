from copy import deepcopy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from baseline_route_selector import select_route
from local_route_validation import LocalRouteValidator
from swag_routing_contract import digest
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

    def test_local_validator_rejects_invalid_or_stale_proposals(self):
        gate = LocalRouteValidator()
        accepted = gate.evaluate(self.request, {'inputSha256': digest(self.request), 'decision': {'bindingId': 'qwen-coder-bf16', 'effort': 'medium'}})
        self.assertTrue(accepted['contractValid'])

        rejected = gate.evaluate(self.request, {'inputSha256': digest(self.request), 'decision': {'bindingId': 'claude-sonnet-4', 'effort': 'high'}})
        self.assertFalse(rejected['contractValid'])
        self.assertFalse(rejected['checks']['effort'])

    def test_adapter_wraps_output_without_claiming_engine_admission(self):
        adapter = SemanticRouterAdapter(
            proposer=lambda request: {
                'bindingId': 'qwen-coder-bf16',
                'effort': 'medium',
                'confidence': 0.81,
                'abstain': False,
                'source': 'semantic-router-test',
                'reason': 'cost-aware local candidate',
            },
            validator=LocalRouteValidator(),
        )
        result = adapter.route(self.request)
        self.assertEqual(result['bindingId'], 'qwen-coder-bf16')
        self.assertTrue(result['localValidation']['contractValid'])
        self.assertFalse(result['executionAuthorized'])
        self.assertFalse(result['localValidation']['engineValidated'])
        self.assertFalse(result['confidenceCalibrated'])
        self.assertNotIn('accepted', result)

    def test_unknown_and_ineligible_choices_are_rejected_without_lookup_error(self):
        for binding in ('unknown', 'claude-sonnet-4'):
            request = deepcopy(self.request)
            request['localOnly'] = True
            result = LocalRouteValidator().evaluate(request, {
                'inputSha256': digest(request),
                'decision': {'bindingId': binding, 'effort': 'medium'}})
            self.assertFalse(result['contractValid'])
            self.assertFalse(result['executionAuthorized'])

    def test_ordinary_edit_stales_only_old_snapshot_and_refresh_is_usable(self):
        proposal = select_route(self.request)
        changed = deepcopy(self.request)
        changed['taskText'] += ' Add an accessibility review.'
        validator = LocalRouteValidator()
        self.assertFalse(validator.evaluate(changed, proposal)['checks']['inputIdentity'])
        self.assertTrue(validator.evaluate(changed, select_route(changed))['contractValid'])

    def test_missing_confidence_stays_unknown_and_invalid_numbers_are_rejected(self):
        self.assertIsNone(select_route(self.request)['confidence'])
        for confidence in (True, '0.8', float('nan'), float('inf')):
            with self.subTest(confidence=confidence), self.assertRaises(ValueError):
                SemanticRouterAdapter(proposer={
                    'bindingId': 'qwen-coder-bf16', 'effort': 'medium',
                    'inputSha256': digest(self.request),
                    'confidence': confidence}).propose(self.request)

    def test_retained_proposal_cannot_be_rebound_without_its_input_identity(self):
        with self.assertRaisesRegex(ValueError, 'inputSha256'):
            SemanticRouterAdapter({'bindingId': None, 'effort': None}).propose(self.request)
        with self.assertRaisesRegex(ValueError, 'explicit bindingId'):
            SemanticRouterAdapter({}).propose(self.request)

    def test_proposer_cannot_mutate_callers_snapshot(self):
        original = deepcopy(self.request)
        def proposer(request):
            request['candidates'].clear()
            return select_route(request)
        result = SemanticRouterAdapter(proposer, LocalRouteValidator()).route(self.request)
        self.assertEqual(self.request, original)
        self.assertFalse(result['localValidation']['checks']['inputIdentity'])


if __name__ == '__main__':
    unittest.main()
