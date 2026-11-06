"""RRFlow-owned validation gate for a semantic-router proposal."""
from __future__ import annotations

from swag_routing_contract import eligible_candidates


class RRFlowRouteGate:
    """Reject stale or invalid route proposals before execution is allowed."""

    def __init__(self, policy_snapshot: dict | None = None):
        self.policy_snapshot = policy_snapshot or {}

    @staticmethod
    def _proposal_decision(proposal: dict) -> dict:
        if not isinstance(proposal, dict):
            raise TypeError('Route proposals must be dictionaries.')
        decision = proposal.get('decision') if isinstance(proposal.get('decision'), dict) else proposal
        if not isinstance(decision, dict):
            raise TypeError('Route proposals must contain a decision object.')
        if 'bindingId' not in decision or 'effort' not in decision:
            raise ValueError('Route proposal is missing bindingId or effort.')
        return {'bindingId': decision.get('bindingId'), 'effort': decision.get('effort')}

    def evaluate(self, request: dict, proposal: dict) -> dict:
        if not isinstance(request, dict):
            raise TypeError('Route evaluations require a request dictionary.')
        eligible = eligible_candidates(request)
        candidate_map = {candidate['bindingId']: candidate for candidate in eligible}
        decision = self._proposal_decision(proposal)
        binding_id = decision['bindingId']
        effort = decision['effort']
        checks = {
            'shape': isinstance(binding_id, (str, type(None))) and isinstance(effort, (str, type(None))),
            'abstain': bool(proposal.get('abstain', binding_id is None)) == (binding_id is None),
            'eligible': binding_id is None or binding_id in candidate_map,
            'effort_match': binding_id is None or effort == request['requestedEffort'],
            'allowed_by_policy': binding_id is None or binding_id in {item['bindingId'] for item in eligible},
        }
        if binding_id is not None:
            candidate = candidate_map[binding_id]
            checks['local_only'] = (not request['localOnly']) or candidate['location'] == 'local'
            checks['quota'] = candidate['quotaAvailable']
            checks['healthy'] = candidate['healthy']
            checks['authorized'] = candidate['authorized']
            checks['quality'] = candidate['quality'] >= request['minimumQuality']
            checks['cost'] = candidate['cost'] <= request['maxCost']
            checks['effort_allowed'] = request['requestedEffort'] in candidate['efforts']
        else:
            checks['local_only'] = True
            checks['quota'] = True
            checks['healthy'] = True
            checks['authorized'] = True
            checks['quality'] = True
            checks['cost'] = True
            checks['effort_allowed'] = True

        accepted = all(checks.values())
        reasons = [name for name, ok in checks.items() if not ok]
        return {
            'proposalAccepted': accepted,
            'eligibleBindingIds': sorted(item['bindingId'] for item in eligible),
            'policyChecks': checks,
            'reasons': reasons,
            'engineDecision': {'bindingId': binding_id, 'effort': effort},
        }
