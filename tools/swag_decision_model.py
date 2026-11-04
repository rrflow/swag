"""Explicit local client for a decision model serving the SystemOne contract. No engine authority."""
from __future__ import annotations

import ipaddress
import json
import math
import os
from pathlib import Path
import time
from urllib import error, parse, request

from swag_observability import Span


class DecisionModelError(RuntimeError):
    """Only static, content-free messages may cross the MCP boundary."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configured() -> bool:
    return bool(os.environ.get('SWAG_DECISION_MODEL_CONNECTION_FILE'))


def _configuration() -> dict:
    location = os.environ.get('SWAG_DECISION_MODEL_CONNECTION_FILE')
    if not location:
        raise DecisionModelError('Configure SWAG_DECISION_MODEL_CONNECTION_FILE for a local decision model.')
    try:
        with Path(location).open('rb') as source:
            raw = source.read(16385)
        if len(raw) > 16384:
            raise ValueError('configuration exceeds limit')
        config = json.loads(raw)
        if not isinstance(config, dict) or config.get('schemaVersion') != 1:
            raise ValueError('invalid version')
        url = parse.urlsplit(config['baseUrl'])
        if (url.scheme != 'http' or not url.hostname or url.username or url.password
                or url.query or url.fragment or url.path not in ('', '/') or not url.port
                or not ipaddress.ip_address(url.hostname).is_loopback):
            raise ValueError('invalid origin')
        if not isinstance(config.get('model'), str) or not config['model']:
            raise ValueError('invalid model')
        for key in ('timeoutMs', 'maxRequestBytes', 'maxResponseBytes'):
            if type(config.get(key)) is not int or config[key] <= 0 or config[key] > 2**31 - 1:
                raise ValueError('invalid resource limit')
        return config
    except (OSError, KeyError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        raise DecisionModelError('Decision model configuration is invalid; check its origin and limits.') from None


def _exchange(config: dict, payload: dict, deadline: float) -> dict:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DecisionModelError('The decision model timed out; check the configured deadline and service.')
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(body) > config['maxRequestBytes']:
        raise DecisionModelError('The decision request exceeds the configured request limit.')
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    req = request.Request(config['baseUrl'].rstrip('/') + '/v1/systemone', data=body, method='POST',
                          headers={'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8'})
    try:
        with Span('decision_model.exchange') as span:
            span.set(operation='decision_model.systemone', inputBytes=len(body))
            with opener.open(req, timeout=remaining) as response:
                span.set(httpStatus=response.status)
                raw = response.read(config['maxResponseBytes'] + 1)
                span.set(outputBytes=len(raw))
        if len(raw) > config['maxResponseBytes'] or time.monotonic() >= deadline:
            raise DecisionModelError('The decision response exceeded the configured size or deadline.')
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('response is not an object')
        return value
    except DecisionModelError:
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError, UnicodeError):
        raise DecisionModelError('The decision model is unavailable or returned an invalid response; check its local service.') from None


def _probability(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def probabilities(state: object, questions: dict[str, dict], batch_size: int) -> dict:
    """Answer binary questions, returning each one's probability and the tokens the model read."""
    config = _configuration()
    deadline = time.monotonic() + config['timeoutMs'] / 1000
    items = list(questions.items())
    answers: dict[str, float] = {}
    input_tokens = 0
    for start in range(0, len(items), batch_size):
        batch = dict(items[start:start + batch_size])
        payload = {'model': config['model'], 'state': state, 'questions': batch}
        result = _exchange(config, payload, deadline)
        returned = result.get('answers')
        if not isinstance(returned, dict) or set(returned) != set(batch):
            raise DecisionModelError('The decision model did not answer exactly the questions it was asked.')
        for question_id in batch:
            answer = returned[question_id]
            if not isinstance(answer, dict) or answer.get('type') != 'noul' or not _probability(answer.get('noul')):
                raise DecisionModelError('The decision model returned an answer outside the requested type.')
            answers[question_id] = float(answer['noul'])
        usage = result.get('usage')
        if isinstance(usage, dict) and type(usage.get('input_tokens')) is int:
            input_tokens += usage['input_tokens']
    return {'answers': answers, 'inputTokens': input_tokens, 'model': config['model'], 'revision': config.get('revision')}
