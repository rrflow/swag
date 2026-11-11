"""Deterministic, policy-aware baseline for route selection."""
from __future__ import annotations

from swag_routing_contract import digest, expected_route, validate_request


def decision_for(request: dict) -> dict:
    """Return the exact bounded decision the contract would expect."""
    validate_request(request)
    return expected_route(request)


def select_route(request: dict) -> dict:
    """Return a strictly bounded proposal with metadata for monitoring."""
    if not isinstance(request, dict):
        raise TypeError('Route requests must be dictionaries.')
    decision = decision_for(request)
    if decision['bindingId'] is None:
        return {
            'bindingId': None,
            'effort': None,
            'abstain': True,
            'confidence': None,
            'inputSha256': digest(request),
            'reason': 'No eligible candidate satisfies the current policy and budget.',
            'source': 'deterministic_baseline',
            'decision': decision,
        }
    return {
        'bindingId': decision['bindingId'],
        'effort': decision['effort'],
        'abstain': False,
        'confidence': None,
        'inputSha256': digest(request),
        'reason': 'Lowest-cost eligible candidate after policy checks.',
        'source': 'deterministic_baseline',
        'decision': decision,
    }
