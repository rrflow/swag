"""Explicit local LFG assessment client. No provider dispatch or engine authority."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import time
from urllib import error, parse, request
from uuid import uuid4

from swag_observability import Span


class LfgBridgeError(RuntimeError):
    """Only static, content-free messages may cross the MCP boundary."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _configuration() -> dict:
    location = os.environ.get('SWAG_LFG_CONNECTION_FILE')
    if not location:
        raise LfgBridgeError('Configure SWAG_LFG_CONNECTION_FILE for a local LFG instance.')
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
        for key in ('timeoutMs', 'maxRequestBytes', 'maxResponseBytes'):
            if type(config.get(key)) is not int or config[key] <= 0 or config[key] > 2**31 - 1:
                raise ValueError('invalid resource limit')
        return config
    except (OSError, KeyError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        raise LfgBridgeError('LFG connection configuration is invalid; check its origin and limits.') from None


def _exchange(config: dict, path: str, deadline: float, payload: dict | None = None) -> dict:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise LfgBridgeError('LFG timed out; check the configured deadline and service.')
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if body is not None and len(body) > config['maxRequestBytes']:
        raise LfgBridgeError('LFG request exceeds the configured request limit.')
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    headers = {'Accept': 'application/json'}
    if body is not None:
        headers['Content-Type'] = 'application/json; charset=utf-8'
    req = request.Request(config['baseUrl'].rstrip('/') + path, data=body, headers=headers,
                          method='GET' if body is None else 'POST')
    try:
        with Span('lfg.exchange') as span:
            span.set(operation='lfg.capabilities' if body is None else 'lfg.observe')
            if body is not None:
                span.set(inputBytes=len(body))
            with opener.open(req, timeout=remaining) as response:
                span.set(httpStatus=response.status)
                raw = response.read(config['maxResponseBytes'] + 1)
            span.set(outputBytes=len(raw))
        if len(raw) > config['maxResponseBytes'] or time.monotonic() >= deadline:
            raise LfgBridgeError('LFG response exceeded the configured size or deadline.')
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('response is not an object')
        return value
    except LfgBridgeError:
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError, UnicodeError):
        raise LfgBridgeError('LFG is unavailable or returned an invalid response; check its local service.') from None


def _finite_number(value: object) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def assess(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise LfgBridgeError('Supply a nonempty request to assess.')
    config = _configuration()
    deadline = time.monotonic() + config['timeoutMs'] / 1000
    caps = _exchange(config, '/api/lfg/observations/capabilities', deadline)
    digest = lambda value: isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None
    if (caps.get('requestSchemaVersion') != 'lfg.observation-request.v1'
            or caps.get('responseSchemaVersion') != 'lfg.observation.v1'
            or not digest(caps.get('assessmentSha256')) or not digest(caps.get('rulesSha256'))
            or type(caps.get('maxInputBytes')) is not int or caps['maxInputBytes'] <= 0):
        raise LfgBridgeError('LFG reports an incompatible observation contract.')
    try:
        encoded = text.encode('utf-8')
    except UnicodeEncodeError:
        raise LfgBridgeError('LFG input must be valid UTF-8 text.') from None
    if len(encoded) > min(config['maxRequestBytes'], caps['maxInputBytes']):
        raise LfgBridgeError('LFG input exceeds the configured or advertised input limit.')
    identity = 'swag-' + uuid4().hex
    source_digest = hashlib.sha256(encoded).hexdigest()
    payload = {'schemaVersion': caps['requestSchemaVersion'], 'requestId': identity, 'revision': 1,
               'text': text, 'inputSha256': source_digest,
               'expectedAssessmentSha256': caps['assessmentSha256'],
               'expectedRulesSha256': caps['rulesSha256'],
               'deadlineUnixMs': int(time.time() * 1000 + max(0, deadline - time.monotonic()) * 1000)}
    result = _exchange(config, '/api/lfg/observations', deadline, payload)
    if (result.get('schemaVersion') != caps['responseSchemaVersion'] or result.get('requestId') != identity
            or result.get('revision') != 1 or result.get('inputSha256') != source_digest
            or result.get('assessmentSha256') != caps['assessmentSha256']
            or result.get('rulesSha256') != caps['rulesSha256'] or result.get('advisory') is not True
            or result.get('confidence') is not None or result.get('status') not in ('available', 'partial')
            or not isinstance(result.get('intent'), dict) or not isinstance(result.get('complexity'), dict)
            or not isinstance(result.get('agents'), dict)):
        raise LfgBridgeError('LFG returned an incompatible or mismatched observation.')
    intent, complexity, agents = result['intent'], result['complexity'], result['agents']
    if (intent.get('status') not in ('available', 'inconclusive') or not isinstance(intent.get('category'), str)
            or not isinstance(complexity.get('bracket'), str)
            or not _finite_number(complexity.get('score'))
            or complexity.get('scoreUnit') != 'configured-rule-points'
            or any(type(agents.get(key)) is not int or agents[key] < 1 for key in ('suggested', 'min', 'max'))
            or not agents['min'] <= agents['suggested'] <= agents['max']
            or not all(isinstance(result.get(key), str) and result[key]
                       for key in ('analyzer', 'assessmentRevision', 'rulesRevision', 'suggestedRole', 'suggestedEffort'))
            or not isinstance(result.get('reasonIds'), list)
            or not all(isinstance(item, str) for item in result['reasonIds'])
            or type(result.get('ignoredExtensionCount')) is not int or result['ignoredExtensionCount'] < 0):
        raise LfgBridgeError('LFG returned an invalid observation; check the local service.')
    # Accept future fields but only expose the currently understood projection.
    fields = ('schemaVersion', 'requestId', 'revision', 'inputSha256', 'analyzer',
              'assessmentRevision', 'assessmentSha256', 'rulesRevision', 'rulesSha256',
              'status', 'intent', 'complexity', 'agents', 'suggestedRole', 'suggestedEffort',
              'reasonIds', 'ignoredExtensionCount', 'advisory', 'confidence')
    projected = {name: result[name] for name in fields if name in result}
    projected['intent'] = {name: intent[name] for name in ('status', 'category')}
    projected['complexity'] = {name: complexity[name] for name in ('bracket', 'score', 'scoreUnit')}
    projected['agents'] = {name: agents[name] for name in ('suggested', 'min', 'max')}
    return {'status': result['status'], 'observation': projected,
            'scope': 'Local LFG advisory observation; RRFlow admission and dispatch are not performed.'}
