"""Offline proposal adapter; local consistency checks do not authorize execution."""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import math

from baseline_route_selector import select_route
from swag_routing_contract import digest, validate_request


class SemanticRouterAdapter:
    """Wrap a model/proposer behind a strict bounded route interface."""

    def __init__(self, proposer: Callable[[dict], dict] | dict | None = None, validator=None):
        self.proposer = select_route if proposer is None else proposer
        self.validator = validator

    @staticmethod
    def _finite_float(value: object) -> float:
        if type(value) not in (int, float):
            raise ValueError('Confidence must be numeric, not a boolean or string.')
        try:
            candidate = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('Confidence must be a numeric value.') from None
        if not math.isfinite(candidate):
            raise ValueError('Confidence must be finite.')
        return candidate

    def _normalize(self, proposal: dict) -> dict:
        if not isinstance(proposal, dict):
            raise TypeError('Semantic-router proposals must be dictionaries.')
        decision = proposal.get('decision') if isinstance(proposal.get('decision'), dict) else proposal
        if not isinstance(decision, dict):
            raise TypeError('Semantic-router proposals require a decision object.')
        if not {'bindingId', 'effort'} <= set(decision):
            raise ValueError('Semantic-router proposals require explicit bindingId and effort.')
        binding_id = decision.get('bindingId')
        effort = decision.get('effort')
        if binding_id is not None and not isinstance(binding_id, str):
            raise TypeError('bindingId must be a string or null.')
        if effort is not None and not isinstance(effort, str):
            raise TypeError('effort must be a string or null.')
        confidence = proposal.get('confidence')
        if confidence is not None:
            confidence = self._finite_float(confidence)
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError('Confidence must be within [0, 1].')
        abstain = proposal.get('abstain', binding_id is None)
        if type(abstain) is not bool:
            raise ValueError('Abstention must be a boolean.')
        if abstain and binding_id is not None:
            raise ValueError('An abstention cannot include a bindingId.')
        if (not abstain) and binding_id is None:
            raise ValueError('A route proposal without a bindingId must abstain.')
        normalized = {
            'bindingId': binding_id,
            'effort': effort,
            'confidence': confidence,
            'confidenceCalibrated': False,
            'inputSha256': proposal.get('inputSha256'),
            'abstain': abstain,
            'reason': str(proposal.get('reason', 'semantic-router proposal')),
            'source': str(proposal.get('source', 'semantic_router')),
            'decision': {'bindingId': binding_id, 'effort': effort},
        }
        return normalized

    def propose(self, request: dict) -> dict:
        validate_request(request)
        identity = digest(request)
        if callable(self.proposer):
            raw = self.proposer(deepcopy(request))
        else:
            raw = self.proposer
        if raw is None:
            raise ValueError('Semantic-router proposer returned no proposal.')
        if isinstance(raw, dict):
            normalized = self._normalize(raw)
            if normalized['inputSha256'] is None:
                if not callable(self.proposer):
                    raise ValueError('A retained proposal must supply its inputSha256.')
                normalized['inputSha256'] = identity
            return normalized
        raise TypeError('Semantic-router proposer must return a dictionary.')

    def route(self, request: dict) -> dict:
        proposal = self.propose(request)
        if self.validator is not None:
            proposal['localValidation'] = self.validator.evaluate(request, proposal)
        proposal['executionAuthorized'] = False
        return proposal

    __call__ = route
