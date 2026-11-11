"""Read explicitly configured model discovery; never dispatch inference or training."""
from __future__ import annotations

import hashlib
from http.client import HTTPException
import json
import os
import re
import time
from pathlib import Path
from urllib import error, parse, request

from swag_observability import CURRENT, observed
from swag_rrflow import NoRedirect
from swag_training_artifacts import read_object


def read_credential(path: Path, variable: str) -> str:
    with path.open('rb') as stream:
        credential_bytes = stream.read(16385)
    if len(credential_bytes) > 16384:
        raise ValueError('Credential file exceeds bound')
    matches = []
    for line in credential_bytes.decode('utf-8').splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip() == variable:
            value = value.strip()
            if len(value) > 1 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            matches.append(value)
    if len(matches) != 1 or not matches[0] or any(ord(char) < 32 for char in matches[0]):
        raise ValueError('Credential reference is missing or ambiguous')
    return matches[0]


def binding(path: Path) -> tuple[dict, str, str]:
    config, raw = read_object(path, 16384)
    required = {'schemaVersion', 'baseUrl', 'modelId', 'credentialFile', 'credentialVariable', 'artifactManifest'}
    if (set(config) != required or type(config['schemaVersion']) is not int or config['schemaVersion'] != 1 or
            not all(isinstance(config[key], str) and 0 < len(config[key]) <= 4096 for key in required - {'schemaVersion'})):
        raise ValueError('Invalid model binding')
    if len(config['modelId']) > 256 or any(ord(character) < 32 for character in config['modelId']):
        raise ValueError('Invalid model identity')
    if (any(ord(character) <= 32 or ord(character) == 127 for character in config['baseUrl'])
            or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', config['credentialVariable'])):
        raise ValueError('Invalid endpoint or credential reference')
    url = parse.urlsplit(config['baseUrl'])
    if (not url.hostname or url.username or url.password or url.query or url.fragment
            or url.path.rstrip('/') not in ('', '/v1')
            or not (url.scheme == 'https' or url.scheme == 'http' and url.hostname in {'localhost', '127.0.0.1', '::1'})):
        raise ValueError('Model binding requires an HTTPS origin or loopback HTTP API')
    def local_file(name):
        selected = Path(config[name])
        return selected if selected.is_absolute() else path.resolve().parent / selected
    manifest, manifest_bytes = read_object(local_file('artifactManifest'))
    if manifest.get('model') != config['modelId']:
        raise ValueError('Configured model does not match the selected manifest identity')
    credential = read_credential(local_file('credentialFile'), config['credentialVariable'])
    config['manifestSha256'] = hashlib.sha256(manifest_bytes).hexdigest()
    config['configurationSha256'] = hashlib.sha256(raw).hexdigest()
    return config, credential, config['baseUrl'].rstrip('/') + ('/models' if url.path.rstrip('/') == '/v1' else '/v1/models')


@observed('swag.model_endpoint')
def status() -> dict:
    result = {'state': 'not_configured', 'modelListed': False,
              'loadedWeightsVerified': False, 'inferencePerformed': False, 'qualified': False}
    configured = os.environ.get('SWAG_MODEL_CONNECTION_FILE')
    if not configured:
        return result
    span = CURRENT.get()
    try:
        config, credential, url = binding(Path(configured))
        span.set(configurationSha256=config['configurationSha256'], sourceSha256=config['manifestSha256'])
    except (OSError, ValueError, TypeError, KeyError):
        span.fail('InvalidModelBinding')
        return {**result, 'state': 'invalid_configuration'}
    result.update(modelId=config['modelId'], manifestSha256=config['manifestSha256'])
    try:
        req = request.Request(url, headers={'Authorization': 'Bearer ' + credential, 'Accept': 'application/json'})
        deadline = time.monotonic() + 5
        with request.build_opener(request.ProxyHandler({}), NoRedirect()).open(req, timeout=5) as response:
            span.set(httpStatus=response.status)
            raw = bytearray()
            while len(raw) <= 1_000_000:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Model discovery deadline exceeded')
                chunk = response.read1(1_000_001 - len(raw))
                if not chunk:
                    break
                raw.extend(chunk)
            if time.monotonic() >= deadline:
                raise TimeoutError('Model discovery deadline exceeded')
        if len(raw) > 1_000_000:
            raise ValueError('Model discovery exceeds bound')
        span.set(outputBytes=len(raw))
        response = json.loads(raw)
        models = response.get('data') if isinstance(response, dict) else None
        if not isinstance(models, list) or len(models) > 4096:
            raise ValueError('Invalid model discovery')
        if any(not isinstance(row, dict) or not isinstance(row.get('id'), str) for row in models):
            raise ValueError('Invalid discovered model')
        result['modelListed'] = any(row['id'] == config['modelId'] for row in models)
        result['state'] = 'model_listed' if result['modelListed'] else 'model_not_listed'
        if not result['modelListed']:
            span.fail('ModelNotListed')
    except error.HTTPError as exc:
        exc.close()
        span.set(httpStatus=exc.code)
        span.fail('ModelDiscoveryRejected')
        result['state'] = 'authentication_failed' if exc.code in (401, 403) else 'discovery_rejected'
    except (error.URLError, TimeoutError, OSError, HTTPException):
        span.fail('ModelEndpointUnavailable')
        result['state'] = 'unavailable'
    except (ValueError, TypeError):
        span.fail('InvalidModelDiscovery')
        result['state'] = 'invalid_response'
    return result
