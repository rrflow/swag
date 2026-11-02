"""Explicit, read-only SWAG integration with an installed public RRFlow API."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, parse, request
from uuid import uuid4

from swag_observability import Span, observed


class RRFlowError(RuntimeError):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def connection() -> dict:
    path = os.environ.get('SWAG_RRFLOW_CONNECTION_FILE')
    if not path:
        raise RRFlowError('RRFlow connection is not configured')
    config_path = Path(path)
    if config_path.stat().st_size > 16384:
        raise RRFlowError('RRFlow connection file exceeds its bound')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if (not isinstance(config, dict) or set(config) != {'schemaVersion', 'baseUrl', 'instanceId', 'credentialFile'}
            or config['schemaVersion'] != 1 or not all(isinstance(config[k], str) and config[k]
                                                     for k in ('baseUrl', 'instanceId', 'credentialFile'))):
        raise RRFlowError('Invalid RRFlow connection configuration')
    url = parse.urlsplit(config['baseUrl'])
    if (not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('', '/')
            or not (url.scheme == 'https' or (url.scheme == 'http' and url.hostname in {'localhost', '127.0.0.1', '::1'}))):
        raise RRFlowError('RRFlow requires an HTTPS origin or explicit loopback HTTP')
    credential_path = Path(config['credentialFile'])
    if not credential_path.is_absolute():
        credential_path = config_path.parent / credential_path
    if credential_path.stat().st_size > 16384:
        raise RRFlowError('RRFlow credential exceeds its bound')
    credential = json.loads(credential_path.read_text(encoding='utf-8'))
    if not isinstance(credential, dict) or not all(isinstance(credential.get(k), str) and credential[k] for k in ('credential', 'principal_id')):
        raise RRFlowError('Invalid installed RRFlow credential')
    return {'base': config['baseUrl'].rstrip('/'), 'instance': config['instanceId'], 'credential': credential}


class Client:
    def __init__(self, config: dict):
        self.config = config
        self.opener = request.build_opener(NoRedirect())
        self.headers: dict[str, str] = {}
        catalogue = self.exchange('/v1/schema/endpoints', 'GET')
        self.endpoints = {entry['operation']: entry for entry in catalogue['endpoints']}

    def exchange(self, path: str, method: str, body=None, headers=None, operation='endpoint-catalogue'):
        # Discovery may supply templates, never another origin or credential target.
        if not isinstance(path, str) or not path.startswith('/v1/') or any(c in path for c in ('?', '#', '\\', '\r', '\n')):
            raise RRFlowError('Invalid engine operation path')
        with Span('rrflow.exchange') as span:
            span.set(operation=operation)
            extra = {'traceparent': span.traceparent, **(headers or {})}
            if body is not None:
                request_id, operation_id = 'swag-' + uuid4().hex, 'swag-' + uuid4().hex
                body['context']['request_id'], body['context']['operation_id'] = request_id, operation_id
                span.set(engineRequestId=request_id, engineOperationId=operation_id)
                encoded = json.dumps(body, separators=(',', ':')).encode()
                span.set(inputBytes=len(encoded))
            else:
                encoded = None
            req = request.Request(self.config['base'] + path, data=encoded, method=method,
                                  headers={'Content-Type': 'application/json', **extra})
            try:
                with self.opener.open(req, timeout=15) as response:
                    span.set(httpStatus=response.status)
                    raw = response.read(2_000_001)
            except error.HTTPError as exc:
                span.set(httpStatus=exc.code)
                raise RRFlowError('Engine rejected the request') from None
            except (error.URLError, TimeoutError, OSError):
                raise RRFlowError('Engine is unavailable') from None
            if len(raw) > 2_000_000:
                raise RRFlowError('Engine response exceeds its bound')
            span.set(outputBytes=len(raw))
            result = json.loads(raw)
            if not isinstance(result, dict) or result.get('protocol') != 'rrd' or result.get('protocol_version') != 1:
                raise RRFlowError('Engine protocol mismatch')
            outcome = result.get('outcome', {})
            if not isinstance(outcome, dict) or 'payload' not in outcome:
                raise RRFlowError('Engine did not return a successful payload')
            return outcome['payload']

    def call(self, operation: str, payload: dict, headers=None):
        endpoint = self.endpoints[operation]
        selected = self.headers if headers is None else headers
        path = endpoint['path'].replace('{session}', selected.get('X-RRD-Session', ''))
        body = {'protocol': 'rrd', 'protocol_version': 1,
                'context': {'request_id': '', 'operation_id': '',
                            'idempotency_key': 'swag-' + uuid4().hex if endpoint['mutation'] else None,
                            'deadline_unix_ms': None},
                'resource': {'segments': [{'kind': 'instance', 'id': self.config['instance']}]}, 'payload': payload}
        return self.exchange(path, endpoint['method'].upper(), body, selected, operation)


@observed('rrflow.status')
def status() -> dict:
    config = connection()
    client = Client(config)
    credential = config['credential']
    session = client.call('session-create', {'limits': {'idle_timeout_ms': 60000,
        'absolute_timeout_ms': 120000, 'max_open_transactions': 1}},
        {'Authorization': 'ApiKey ' + credential['credential'], 'X-RRD-Principal': credential['principal_id']})
    client.headers = {'Authorization': 'Bearer ' + session['token'], 'X-RRD-Session': session['session_id']}
    try:
        storage = client.call('diagnostics-storage-read', {'scope': 'instance:' + config['instance']})
        return {'schema': 'swag.rrflow-status/v1', 'authenticated': True, 'instanceId': config['instance'],
                'availableOperations': sorted(client.endpoints), 'storage': storage,
                'scope': 'Authenticated engine readback; no model dispatch or project execution.'}
    finally:
        client.call('session-close', {})
