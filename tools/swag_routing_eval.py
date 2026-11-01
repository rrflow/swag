"""Freeze and run an offline routing protocol against an authenticated endpoint."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import math
from pathlib import Path
import statistics
import time
import urllib.parse
import urllib.request

from swag_routing_contract import (ROOT, SYSTEM_PROMPT, canonical_bytes, digest,
                                   expected_route, messages, score_output, strict_json,
                                   validate, validate_request)
from swag_routing_dataset import read_jsonl


def implementation_hashes() -> dict:
    names = ('tools/swag_routing_contract.py', 'tools/swag_routing_eval.py',
             'config/training/routing_request.schema.json',
             'config/training/routing_decision.schema.json')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def verify_dataset(directory: Path) -> dict:
    manifest = strict_json((directory / 'manifest.json').read_bytes())
    required_files = {f'{split}.cases.jsonl' for split in ('train', 'development', 'acceptance')}
    required_files.update({'train.chat.jsonl', 'development.chat.jsonl'})
    if (manifest.get('schemaVersion') != 1 or manifest.get('scope') != 'offline_reviewed_bounded_routing'
            or set(manifest.get('files', {})) != required_files
            or set(manifest.get('counts', {})) != {'train', 'development', 'acceptance'}):
        raise ValueError('Incomplete admission manifest')
    for name, expected in manifest['files'].items():
        if Path(name).name != name or Path(name).is_absolute():
            raise ValueError('Invalid export artifact name')
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Export artifact changed after admission')
    for split in ('train', 'development', 'acceptance'):
        cases, _ = read_jsonl(directory / f'{split}.cases.jsonl')
        if type(manifest['counts'][split]) is not int or manifest['counts'][split] != len(cases):
            raise ValueError('Dataset count mismatch')
        if any(row.get('sourceKind') != 'real_observation' for row in cases):
            raise ValueError('Dataset use requires reviewed real observations in every split')
        if split != 'acceptance':
            chats, _ = read_jsonl(directory / f'{split}.chat.jsonl')
            expected = [{'messages': messages(row['request'], row['expected'])} for row in cases]
            if chats != expected:
                raise ValueError('Chat export does not match admitted cases and current prompt')
    return manifest


def validate_limits(limits: dict) -> None:
    if set(limits) != {'minimumCases', 'minimumAccuracy', 'maximumPolicyViolations',
                       'maximumInvalidOutputs', 'maximumP95Seconds'}:
        raise ValueError('All protocol thresholds must be explicit')
    for key in ('minimumCases', 'maximumPolicyViolations', 'maximumInvalidOutputs'):
        if type(limits[key]) is not int or limits[key] < (1 if key == 'minimumCases' else 0):
            raise ValueError('Invalid integer threshold')
    for key in ('minimumAccuracy', 'maximumP95Seconds'):
        if type(limits[key]) not in (int, float) or not math.isfinite(limits[key]):
            raise ValueError('Invalid numeric threshold')
    if not 0 <= limits['minimumAccuracy'] <= 1 or limits['maximumP95Seconds'] <= 0:
        raise ValueError('Invalid accuracy or latency threshold')


def freeze(cases: list[dict], scope: str, source: dict, limits: dict, output: Path,
           comparison_limits: dict | None = None) -> dict:
    validate_limits(limits)
    if scope not in {'development', 'acceptance'} or len(cases) < limits['minimumCases']:
        raise ValueError('Invalid scope or insufficient cases')
    ids, requests = set(), set()
    for case in cases:
        if not isinstance(case['caseId'], str) or not case['caseId'].strip():
            raise ValueError('Nonempty case identity required')
        validate_request(case['request'])
        validate(case['expected'], 'routing_decision.schema.json')
        if expected_route(case['request']) != case['expected']:
            raise ValueError('Case label contradicts bounded policy')
        if case['caseId'] in ids or digest(case['request']) in requests:
            raise ValueError('Duplicate case identity or request')
        ids.add(case['caseId'])
        requests.add(digest(case['request']))
        if scope == 'acceptance' and case.get('sourceKind') != 'real_observation':
            raise ValueError('Synthetic cases cannot enter acceptance')
    protocol = {
        'schemaVersion': 1, 'scope': scope, 'createdAt': datetime.now(timezone.utc).isoformat(),
        'task': 'bounded_candidate_selection_only', 'source': source,
        'systemPrompt': SYSTEM_PROMPT, 'implementation': implementation_hashes(),
        'limits': limits, 'generation': {'temperature': 0, 'max_tokens': 96},
        'cases': cases, 'deploymentQualified': False,
    }
    if comparison_limits is not None:
        if (set(comparison_limits) != {'maximumCustomAccuracyDrop', 'maximumQuantizedAccuracyDrop'}
                or any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1
                       for value in comparison_limits.values())):
            raise ValueError('Invalid relative-quality thresholds')
        protocol['comparisonLimits'] = comparison_limits
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(canonical_bytes(protocol) + b'\n')
    return protocol


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Endpoint redirects are not allowed')


def endpoint_url(base: str) -> str:
    parsed = urllib.parse.urlsplit(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Endpoint cannot contain credentials, query or fragment')
    try:
        loopback = ipaddress.ip_address(parsed.hostname or '').is_loopback
    except ValueError:
        loopback = parsed.hostname == 'localhost'
    if not parsed.hostname or not (parsed.scheme == 'https' or (parsed.scheme == 'http' and loopback)):
        raise ValueError('Require HTTPS or loopback HTTP')
    if parsed.path.rstrip('/') not in ('', '/v1'):
        raise ValueError('Use endpoint origin or /v1 base')
    return base.rstrip('/') + ('/chat/completions' if parsed.path.rstrip('/') == '/v1'
                               else '/v1/chat/completions')


def summarize(results: list[dict], limits: dict) -> dict:
    count = len(results)
    durations = sorted(row['elapsedSeconds'] for row in results)
    p95 = durations[math.ceil(count * .95) - 1] if count else None
    correct = sum(row['matched'] for row in results)
    violations = sum(row['policyViolation'] for row in results)
    invalid = sum(not row['validOutput'] for row in results)
    passed = (count >= limits['minimumCases'] and correct / count >= limits['minimumAccuracy']
              and violations <= limits['maximumPolicyViolations']
              and invalid <= limits['maximumInvalidOutputs']
              and p95 <= limits['maximumP95Seconds']) if count else False
    return {'cases': count, 'matched': correct, 'accuracy': correct / count if count else None,
            'policyViolations': violations, 'invalidOutputs': invalid,
            'falseAbstentions': sum(row['falseAbstention'] for row in results),
            'unnecessarySelections': sum(row['unnecessarySelection'] for row in results),
            'firstRequestSeconds': results[0]['elapsedSeconds'] if results else None,
            'warmMedianSeconds': statistics.median(row['elapsedSeconds'] for row in results[1:])
            if count > 1 else None, 'p95Seconds': p95, 'protocolPassed': passed,
            'deploymentQualified': False}


def run(protocol_path: Path, expected_sha: str, artifact_path: Path, arm: str,
        base_url: str, model: str, key_file: Path, output: Path) -> dict:
    protocol_bytes = protocol_path.read_bytes()
    if hashlib.sha256(protocol_bytes).hexdigest() != expected_sha:
        raise ValueError('Protocol bytes differ from caller-pinned digest')
    protocol = strict_json(protocol_bytes)
    if protocol['implementation'] != implementation_hashes() or protocol['systemPrompt'] != SYSTEM_PROMPT:
        raise ValueError('Protocol implementation changed; freeze a new protocol')
    validate_limits(protocol['limits'])
    artifact_bytes = artifact_path.read_bytes()
    artifact = strict_json(artifact_bytes)
    if not isinstance(artifact, dict) or not artifact:
        raise ValueError('Artifact manifest must be a nonempty object')
    # Manifest bytes are retained, not treated as server-side attestation.
    url = endpoint_url(base_url)
    lines = key_file.read_text(encoding='utf-8').splitlines()
    keys = [line.split('=', 1)[1].strip() for line in lines if line.startswith('VLLM_API_KEY=')]
    if len(keys) != 1 or not keys[0]:
        raise ValueError('Require one nonempty VLLM_API_KEY in private environment file')
    opener = urllib.request.build_opener(NoRedirect())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'protocol.json').write_bytes(protocol_bytes)
    (output / 'artifact-manifest.json').write_bytes(artifact_bytes)
    results = []
    with (output / 'results.jsonl').open('x', encoding='utf-8') as stream:
        for case in protocol['cases']:
            payload = {'model': model, **protocol['generation'], 'messages': messages(case['request'])}
            request = urllib.request.Request(url, data=canonical_bytes(payload), method='POST',
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + keys[0]})
            row = {'caseId': case['caseId'], 'expected': case['expected'],
                   'requestSha256': digest(case['request']), **score_output('', case['request'], case['expected'])}
            started = time.monotonic()
            try:
                with opener.open(request, timeout=180) as response:
                    body = strict_json(response.read())
                raw = body['choices'][0]['message']['content']
                if not isinstance(raw, str):
                    raise ValueError('Missing text output')
                row.update({'rawOutput': raw, 'usage': body.get('usage'), 'servedModel': body.get('model')})
                row.update(score_output(raw, case['request'], case['expected']))
                if body.get('model') != model:
                    row.update({'validOutput': False, 'matched': False, 'errorClass': 'ServedModelMismatch'})
            except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                row['errorClass'] = type(exc).__name__  # Never log exception text containing request credentials.
            row['elapsedSeconds'] = time.monotonic() - started
            results.append(row)
            stream.write(canonical_bytes(row).decode() + '\n')
            stream.flush()
            print(json.dumps({'caseId': row['caseId'], 'matched': row['matched']}), flush=True)
    summary = {**summarize(results, protocol['limits']), 'scope': protocol['scope'], 'arm': arm,
               'protocolSha256': expected_sha, 'artifactManifestSha256': hashlib.sha256(artifact_bytes).hexdigest(),
               'serverIdentityAttested': False, 'completedAt': datetime.now(timezone.utc).isoformat(),
               'resultsSha256': hashlib.sha256((output / 'results.jsonl').read_bytes()).hexdigest()}
    (output / 'summary.json').write_bytes(canonical_bytes(summary) + b'\n')
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    freeze_parser = sub.add_parser('freeze')
    sources = freeze_parser.add_mutually_exclusive_group(required=True)
    sources.add_argument('--dataset-dir', type=Path)
    sources.add_argument('--development-cases', type=Path)
    freeze_parser.add_argument('--split', choices=['development', 'acceptance'], default='development')
    freeze_parser.add_argument('--limits', type=Path, required=True)
    freeze_parser.add_argument('--comparison-limits', type=Path,
                               help='Freeze A/B/C relative-quality allowances before acceptance evaluation.')
    freeze_parser.add_argument('--output', type=Path, required=True)
    run_parser = sub.add_parser('run')
    for name in ('protocol', 'artifact-manifest', 'api-key-env-file', 'output-dir'):
        run_parser.add_argument('--' + name, type=Path, required=True)
    run_parser.add_argument('--protocol-sha256', required=True)
    run_parser.add_argument('--arm', choices=['base_bf16', 'custom_bf16', 'custom_quantized'], required=True)
    run_parser.add_argument('--base-url', default='http://127.0.0.1:8083')
    run_parser.add_argument('--model', required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        if args.development_cases:
            if args.split != 'development':
                parser.error('Direct cases may only be frozen for development')
            cases, sha = read_jsonl(args.development_cases)
            source = {'developmentCasesSha256': sha}
        else:
            manifest = verify_dataset(args.dataset_dir)
            cases, sha = read_jsonl(args.dataset_dir / f'{args.split}.cases.jsonl')
            if len(cases) != manifest['counts'][args.split]:
                raise ValueError('Dataset count mismatch')
            source = {'admissionManifestSha256': hashlib.sha256((args.dataset_dir / 'manifest.json').read_bytes()).hexdigest(),
                      'casesSha256': sha}
        freeze(cases, args.split, source, strict_json(args.limits.read_bytes()), args.output,
               strict_json(args.comparison_limits.read_bytes()) if args.comparison_limits else None)
        print(json.dumps({'protocolSha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                          'scope': args.split, 'cases': len(cases), 'deploymentQualified': False}))
        return 0
    summary = run(args.protocol, args.protocol_sha256, args.artifact_manifest, args.arm,
                  args.base_url, args.model, args.api_key_env_file, args.output_dir)
    print(json.dumps(summary))
    return 0 if summary['protocolPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
