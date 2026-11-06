"""Bounded semantic-router adapter layer with RRFlow validation hook."""
from __future__ import annotations

from collections.abc import Callable
import math

from baseline_route_selector import select_route


class SemanticRouterAdapter:
    """Wrap a model/proposer behind a strict bounded route interface."""

    def __init__(self, proposer: Callable[[dict], dict] | dict | None = None, gate=None):
        self.proposer = proposer or select_route
        self.gate = gate

    @staticmethod
    def _finite_float(value: object) -> float:
        try:
            candidate = float(value)
        except (TypeError, ValueError):
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
        binding_id = decision.get('bindingId')
        effort = decision.get('effort')
        if binding_id is not None and not isinstance(binding_id, str):
            raise TypeError('bindingId must be a string or null.')
        if effort is not None and not isinstance(effort, str):
            raise TypeError('effort must be a string or null.')
        confidence = proposal.get('confidence', 0.5)
        confidence = self._finite_float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError('Confidence must be within [0, 1].')
        abstain = bool(proposal.get('abstain', binding_id is None))
        if abstain and binding_id is not None:
            raise ValueError('An abstention cannot include a bindingId.')
        if (not abstain) and binding_id is None:
            raise ValueError('A route proposal without a bindingId must abstain.')
        normalized = {
            'bindingId': binding_id,
            'effort': effort,
            'confidence': confidence,
            'abstain': abstain,
            'reason': str(proposal.get('reason', 'semantic-router proposal')),
            'source': str(proposal.get('source', 'semantic_router')),
            'decision': {'bindingId': binding_id, 'effort': effort},
        }
        return normalized

    def propose(self, request: dict) -> dict:
        if callable(self.proposer):
            raw = self.proposer(request)
        else:
            raw = self.proposer
        if raw is None:
            raise ValueError('Semantic-router proposer returned no proposal.')
        if isinstance(raw, dict):
            return self._normalize(raw)
        raise TypeError('Semantic-router proposer must return a dictionary.')

    def route(self, request: dict) -> dict:
        proposal = self.propose(request)
        if self.gate is not None:
            validation = self.gate.evaluate(request, proposal)
            proposal['rrflowValidation'] = validation
            proposal['accepted'] = validation['proposalAccepted']
        return proposal

    __call__ = route
