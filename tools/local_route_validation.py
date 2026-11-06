"""Offline checks of caller-supplied routing data; never RRFlow admission."""
from __future__ import annotations

from swag_routing_contract import digest, eligible_candidates, validate, validate_request


class LocalRouteValidator:
    """Check a proposal against its supplied snapshot without attesting that data."""

    def evaluate(self, request: dict, proposal: dict) -> dict:
        validate_request(request)
        if not isinstance(proposal, dict):
            raise TypeError('Route proposals must be dictionaries.')
        decision = proposal.get('decision')
        validate(decision, 'routing_decision.schema.json')
        eligible = {item['bindingId'] for item in eligible_candidates(request)}
        binding_id, effort = decision['bindingId'], decision['effort']
        checks = {
            'inputIdentity': proposal.get('inputSha256') == digest(request),
            'eligible': binding_id is None or binding_id in eligible,
            'effort': effort is None if binding_id is None else effort == request['requestedEffort'],
        }
        return {
            'contractValid': all(checks.values()),
            'eligibleBindingIds': sorted(eligible),
            'checks': checks,
            'reasons': [name for name, ok in checks.items() if not ok],
            'engineValidated': False,
            'executionAuthorized': False,
            'scope': 'Offline consistency only; supplied authorization, health, quota and scores are not verified.',
        }
