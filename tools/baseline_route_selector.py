"""Deterministic, policy-aware baseline for route selection."""
from __future__ import annotations

from swag_routing_contract import eligible_candidates


def decision_for(request: dict) -> dict:
    """Return the exact bounded decision the contract would expect."""
    eligible = eligible_candidates(request)
    if not eligible:
        return {'bindingId': None, 'effort': None}
    choice = min(eligible, key=lambda item: (item['cost'], item['bindingId']))
    return {'bindingId': choice['bindingId'], 'effort': request['requestedEffort']}


def select_route(request: dict) -> dict:
    """Return a strictly bounded proposal with metadata for monitoring."""
    if not isinstance(request, dict):
        raise TypeError('Route requests must be dictionaries.')
    decision = decision_for(request)
    eligible = eligible_candidates(request)
    if not eligible:
        return {
            'bindingId': None,
            'effort': None,
            'abstain': True,
            'confidence': 0.0,
            'reason': 'No eligible candidate satisfies the current policy and budget.',
            'source': 'deterministic_baseline',
            'decision': decision,
        }
    return {
        'bindingId': decision['bindingId'],
        'effort': decision['effort'],
        'abstain': False,
        'confidence': 0.5,
        'reason': 'Lowest-cost eligible candidate after policy checks.',
        'source': 'deterministic_baseline',
        'decision': decision,
    }
