"""Freeze and evaluate outcome prediction independently of permission policy.

Inference occurs only through the explicit run command. This tool never trains
or dispatches a downstream task worker; it calls the configured research endpoint.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
import urllib.request

from swag_routing_contract import ROOT, canonical_bytes, digest, strict_json
from swag_routing_dataset import read_jsonl
from swag_routing_eval import NoRedirect, endpoint_url
from swag_model_qualification import serving_identity_present
from swag_task_outcomes import messages, verify_dataset

ARMS = ('base_bf16', 'custom_bf16', 'custom_quantized', 'small_baseline')


def validate_artifact(manifest: dict) -> None:
    files = manifest.get('files') if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not files:
        raise ValueError('Declared artifact inventory required')
    for name, entry in files.items():
        if (not isinstance(name, str) or not name or not isinstance(entry, dict)
                or type(entry.get('bytes')) is not int or entry['bytes'] < 0
                or not isinstance(entry.get('sha256'), str)
                or re.fullmatch(r'[0-9a-f]{64}', entry['sha256']) is None):
            raise ValueError('Invalid declared artifact inventory')


def implementation_hashes() -> dict:
    names = ('tools/swag_outcome_eval.py', 'tools/swag_task_outcomes.py',
             'tools/swag_routing_dataset.py', 'tools/swag_routing_contract.py',
             'tools/swag_routing_eval.py', 'tools/swag_model_qualification.py',
             'config/training/task_outcome.schema.json',
             'config/training/task_outcome_review.schema.json')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def validate_limits(limits: dict) -> None:
    integers = {'minimumCases', 'maximumInvalidOutputs', 'maximumOrderSensitiveCases', 'maximumQuantizedServingBytes'}
    rates = {'decisionThreshold', 'minimumDecisionAccuracy', 'minimumCoverage',
             'maximumSelectiveRisk', 'maximumBrierScore', 'maximumCustomAccuracyDrop',
             'maximumQuantizedAccuracyDrop'}
    if set(limits) != integers | rates | {'maximumP95Seconds'}:
        raise ValueError('All outcome thresholds and relative margins must be explicit')
    for key in integers:
        if type(limits[key]) is not int or limits[key] < (1 if key in ('minimumCases', 'maximumQuantizedServingBytes') else 0):
            raise ValueError('Invalid integer threshold')
    for key in rates | {'maximumP95Seconds'}:
        if type(limits[key]) not in (int, float) or not math.isfinite(limits[key]):
            raise ValueError('Invalid finite threshold')
    if any(not 0 <= limits[key] <= 1 for key in rates) or limits['maximumP95Seconds'] <= 0:
        raise ValueError('Threshold out of range')


def freeze(dataset: Path, split: str, limits: dict, output: Path) -> dict:
    manifest = verify_dataset(dataset)
    validate_limits(limits)
    if split not in ('development', 'acceptance'):
        raise ValueError('Evaluation requires development or acceptance')
    cases, cases_sha = read_jsonl(dataset / f'{split}.cases.jsonl')
    if len(cases) < limits['minimumCases']:
        raise ValueError('Insufficient reviewed cases')
    if len({case['observation']['taskId'] for case in cases}) != len(cases):
        raise ValueError('Repeated tasks need a grouped evaluation protocol, not inflated case counts')
    protocol = {
        'schemaVersion': 1, 'kind': 'swag.outcome_protocol', 'scope': split,
        'objective': manifest['objective'], 'createdAt': datetime.now(timezone.utc).isoformat(),
        'datasetManifestSha256': hashlib.sha256((dataset / 'manifest.json').read_bytes()).hexdigest(),
        'casesSha256': cases_sha, 'implementation': implementation_hashes(), 'limits': limits,
        'generation': {'temperature': 0, 'max_tokens': 512}, 'variants': ['original', 'reversed'],
        'cases': cases, 'deploymentQualified': False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(canonical_bytes(protocol) + b'\n')
    return protocol


def probability_output(raw: str, case: dict) -> dict | None:
    try:
        value = strict_json(raw)
        expected = set(case['outcomes'])
        if not isinstance(value, dict) or set(value) != {'probabilities'}:
            return None
        probabilities = value['probabilities']
        if not isinstance(probabilities, dict) or set(probabilities) != expected:
            return None
        if any(type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
               for p in probabilities.values()):
            return None
        return probabilities
    except (ValueError, TypeError):
        return None


def score(raw: str, case: dict, threshold: float) -> dict:
    probabilities = probability_output(raw, case)
    result = {'validOutput': probabilities is not None, 'selectedOption': None,
              'decisionCorrect': False, 'selectedSuccess': None, 'brierScore': None}
    if probabilities is None:
        return result
    highest = max(probabilities.values())
    winners = [key for key, value in probabilities.items() if value == highest]
    # A tie is uncertainty; never turn lexical provider names into strengths.
    selected = winners[0] if len(winners) == 1 and highest >= threshold else None
    result.update({
        'selectedOption': selected,
        'selectedSuccess': case['outcomes'][selected] if selected is not None else None,
        'decisionCorrect': case['outcomes'][selected] if selected is not None else not any(case['outcomes'].values()),
        'brierScore': sum((probabilities[key] - int(value)) ** 2 for key, value in case['outcomes'].items()) / len(probabilities),
    })
    return result


def summarize(protocol: dict, rows: list[dict]) -> dict:
    expected = {(case['caseId'], variant) for case in protocol['cases'] for variant in protocol['variants']}
    indexed = {(row['caseId'], row['variant']): row for row in rows}
    if len(indexed) != len(rows) or set(indexed) != expected:
        raise ValueError('Every case and order variant must retain one result, including failures')
    scores = {}
    for case in protocol['cases']:
        for variant in protocol['variants']:
            row = indexed[case['caseId'], variant]
            request = case['request']
            if variant == 'reversed':
                request = {**request, 'candidates': list(reversed(request['candidates']))}
            if row['requestSha256'] != digest(messages(request, protocol['objective'])):
                raise ValueError('Result belongs to a different prompt or candidate order')
            elapsed = row['elapsedSeconds']
            if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError('Invalid elapsed time')
            scores[case['caseId'], variant] = score(
                '' if row.get('errorClass') else row['rawOutput'], case, protocol['limits']['decisionThreshold'])
    primary = [scores[case['caseId'], 'original'] for case in protocol['cases']]
    count = len(primary)
    correct = sum(row['decisionCorrect'] for row in primary)
    selected = [row for row in primary if row['selectedOption'] is not None]
    risk = sum(not row['selectedSuccess'] for row in selected) / len(selected) if selected else None
    valid = [row for row in primary if row['validOutput']]
    brier = sum(row['brierScore'] for row in valid) / len(valid) if valid else None
    invalid = sum(not row['validOutput'] for row in scores.values())
    durations = sorted(row['elapsedSeconds'] for row in rows)
    p95 = durations[math.ceil(len(durations) * .95) - 1]
    sensitivity = sum(scores[case['caseId'], 'original']['selectedOption'] !=
                      scores[case['caseId'], 'reversed']['selectedOption'] for case in protocol['cases'])
    limits = protocol['limits']
    accuracy, coverage = correct / count, len(selected) / count
    # Wilson interval: descriptive task-level uncertainty, not a causal or clustered CI.
    z = 1.959963984540054
    center = (accuracy + z * z / (2 * count)) / (1 + z * z / count)
    margin = z * math.sqrt(accuracy * (1 - accuracy) / count + z * z / (4 * count * count)) / (1 + z * z / count)
    passed = (count >= limits['minimumCases'] and accuracy >= limits['minimumDecisionAccuracy']
              and coverage >= limits['minimumCoverage'] and invalid <= limits['maximumInvalidOutputs']
              and sensitivity <= limits['maximumOrderSensitiveCases']
              and brier is not None and brier <= limits['maximumBrierScore']
              and (risk is not None and risk <= limits['maximumSelectiveRisk'])
              and p95 <= limits['maximumP95Seconds'])
    return {'cases': count, 'decisionAccuracy': accuracy, 'accuracyWilson95': [center - margin, center + margin],
            'coverage': coverage, 'selectiveRisk': risk, 'brierScore': brier,
            'brierValidCases': len(valid), 'invalidOutputs': invalid, 'p95Seconds': p95,
            'orderSensitiveCases': sensitivity, 'protocolPassed': passed,
            'enginePermissionEvaluated': False, 'deploymentQualified': False,
            'probabilitiesCalibrated': False}


def load_protocol(path: Path, expected_sha: str) -> tuple[dict, bytes]:
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != expected_sha:
        raise ValueError('Protocol bytes differ from caller-pinned digest')
    protocol = strict_json(contents)
    if protocol.get('kind') != 'swag.outcome_protocol' or protocol['implementation'] != implementation_hashes():
        raise ValueError('Outcome protocol implementation changed; freeze again')
    validate_limits(protocol['limits'])
    return protocol, contents


def run(protocol_path: Path, expected_sha: str, artifact_path: Path, arm: str,
        base_url: str, model: str, key_file: Path, output: Path) -> dict:
    protocol, protocol_bytes = load_protocol(protocol_path, expected_sha)
    if arm not in ARMS:
        raise ValueError('Unknown comparison arm')
    artifact_bytes = artifact_path.read_bytes()
    artifact = strict_json(artifact_bytes)
    validate_artifact(artifact)
    url = endpoint_url(base_url)
    keys = [line.split('=', 1)[1].strip() for line in key_file.read_text(encoding='utf-8').splitlines()
            if line.startswith('VLLM_API_KEY=')]
    if len(keys) != 1 or not keys[0]:
        raise ValueError('Require one VLLM_API_KEY in a private environment file')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'protocol.json').write_bytes(protocol_bytes)
    (output / 'artifact-manifest.json').write_bytes(artifact_bytes)
    results = []
    with (output / 'results.jsonl').open('xb') as stream:
        for case in protocol['cases']:
            for variant in protocol['variants']:
                request_data = case['request']
                if variant == 'reversed':
                    request_data = {**request_data, 'candidates': list(reversed(request_data['candidates']))}
                chat = messages(request_data, protocol['objective'])
                payload = {'model': model, **protocol['generation'], 'messages': chat}
                request = urllib.request.Request(url, data=canonical_bytes(payload), method='POST',
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + keys[0]})
                row = {'caseId': case['caseId'], 'variant': variant, 'requestSha256': digest(chat), 'rawOutput': ''}
                started = time.monotonic()
                try:
                    with opener.open(request, timeout=60) as response:
                        raw = response.read(1_000_001)
                    if len(raw) > 1_000_000:
                        raise ValueError('Response too large')
                    body = strict_json(raw)
                    row['rawOutput'] = body['choices'][0]['message']['content']
                    row['servedModel'], row['usage'] = body.get('model'), body.get('usage')
                    if body.get('model') != model or not isinstance(row['rawOutput'], str):
                        row['errorClass'] = 'ServedModelOrOutputMismatch'
                except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
                    row['errorClass'] = type(exc).__name__
                row['elapsedSeconds'] = time.monotonic() - started
                results.append(row)
                stream.write(canonical_bytes(row) + b'\n')
                stream.flush()
    summary = {**summarize(protocol, results), 'arm': arm, 'objective': protocol['objective'],
               'scope': protocol['scope'], 'protocolSha256': expected_sha,
               'artifactManifestSha256': hashlib.sha256(artifact_bytes).hexdigest(),
               'resultsSha256': hashlib.sha256((output / 'results.jsonl').read_bytes()).hexdigest(),
               'serverIdentityAttested': False}
    (output / 'summary.json').write_bytes(canonical_bytes(summary) + b'\n')
    return summary


def compare(runs: dict[str, Path], protocol_path: Path, expected_sha: str,
            maximum_serving_bytes: int) -> dict:
    """Recompute all four arms. Missing data never becomes a successful comparison."""
    if type(maximum_serving_bytes) is not int or maximum_serving_bytes <= 0:
        raise ValueError('Explicit positive total serving-memory target required')
    protocol, _ = load_protocol(protocol_path, expected_sha)
    if maximum_serving_bytes != protocol['limits']['maximumQuantizedServingBytes']:
        raise ValueError('Serving-memory target must match the frozen protocol')
    reasons, arms, manifests, hashes = [], {}, {}, {}
    if protocol['scope'] != 'acceptance':
        reasons.append('Qualification requires frozen unseen acceptance tasks')
    for arm in ARMS:
        directory = runs.get(arm)
        if directory is None:
            reasons.append('Missing arm: ' + arm)
            continue
        retained = strict_json((directory / 'summary.json').read_bytes())
        raw_manifest = (directory / 'artifact-manifest.json').read_bytes()
        manifests[arm] = strict_json(raw_manifest)
        validate_artifact(manifests[arm])
        hashes[arm] = hashlib.sha256(raw_manifest).hexdigest()
        rows, results_sha = read_jsonl(directory / 'results.jsonl')
        if (retained.get('arm') != arm or retained.get('protocolSha256') != expected_sha
                or hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest() != expected_sha
                or retained.get('resultsSha256') != results_sha
                or retained.get('artifactManifestSha256') != hashes[arm]):
            raise ValueError('Run identity or retained bytes mismatch')
        arms[arm] = summarize(protocol, rows)
        if not arms[arm]['protocolPassed']:
            reasons.append(arm + ': outcome protocol failed')
        if not serving_identity_present(directory, retained, manifests[arm]):
            reasons.append(arm + ': missing observed serving-process identity')
        memory_path = directory / 'serving-memory.json'
        if not memory_path.is_file():
            reasons.append(arm + ': missing total serving-memory measurement')
            continue
        memory = strict_json(memory_path.read_bytes())
        raw_path = directory / 'serving-memory.raw'
        if (memory.get('scope') != 'total_serving' or memory.get('artifactManifestSha256') != hashes[arm]
                or memory.get('protocolSha256') != expected_sha
                or type(memory.get('bytes')) is not int or memory['bytes'] <= 0
                or not memory.get('method') or not memory.get('processIdentity')
                or not raw_path.is_file()
                or hashlib.sha256(raw_path.read_bytes()).hexdigest() != memory.get('rawEvidenceSha256')):
            reasons.append(arm + ': incomplete or mismatched serving-memory evidence')
            continue
        identity = strict_json((directory / 'serving-identity.json').read_bytes()) if (directory / 'serving-identity.json').is_file() else {}
        if memory['processIdentity'] != identity.get('processIdentity'):
            reasons.append(arm + ': memory and serving identity refer to different processes')
        arms[arm]['totalServingBytes'] = memory['bytes']
        if arm == 'custom_quantized' and memory['bytes'] > maximum_serving_bytes:
            reasons.append('Quantized total serving memory exceeds the frozen target')
    if all(arm in arms for arm in ARMS):
        base, custom, quantized = (manifests[arm] for arm in ARMS[:3])
        if (base.get('custom_checkpoint') is not False or base.get('precision') not in ('bf16', 'bfloat16')
                or custom.get('custom_checkpoint') is not True or custom.get('precision') not in ('bf16', 'bfloat16')
                or custom.get('baseManifestSha256') != hashes['base_bf16']):
            reasons.append('Original/custom BF16 lineage is missing or mismatched')
        if (quantized.get('parentManifestSha256') != hashes['custom_bf16']
                or quantized.get('custom_checkpoint') is not True or not quantized.get('quantizationMethod')
                or quantized.get('precision') in (None, 'bf16', 'bfloat16')):
            reasons.append('Quantized arm must derive from exactly the custom BF16 artifact')
        base_accuracy, custom_accuracy, quant_accuracy = (arms[arm]['decisionAccuracy'] for arm in ARMS[:3])
        if (base_accuracy - custom_accuracy > protocol['limits']['maximumCustomAccuracyDrop']
                or custom_accuracy - quant_accuracy > protocol['limits']['maximumQuantizedAccuracyDrop']):
            reasons.append('Quality regression exceeds frozen margin')
    return {'schemaVersion': 1, 'kind': 'swag.outcome_comparison', 'objective': protocol['objective'],
            'protocolSha256': expected_sha, 'comparisonEvidencePassed': not reasons,
            'deploymentQualified': False, 'promotionAuthorized': False, 'reasons': reasons, 'arms': arms,
            'maximumQuantizedServingBytes': maximum_serving_bytes,
            'limitations': ['Local review and process attestations require independent verification.',
                            'One observed outcome per option is not its long-run success probability.',
                            'Wilson intervals assume independent tasks; related-project clustering needs separate analysis.',
                            'This offline comparison does not verify engine execution, UI integration or rollback.']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    freezing = sub.add_parser('freeze')
    for name in ('dataset-dir', 'limits', 'output'):
        freezing.add_argument('--' + name, type=Path, required=True)
    freezing.add_argument('--split', choices=['development', 'acceptance'], required=True)
    running = sub.add_parser('run')
    for name in ('protocol', 'artifact-manifest', 'api-key-env-file', 'output-dir'):
        running.add_argument('--' + name, type=Path, required=True)
    for name in ('protocol-sha256', 'base-url', 'model'):
        running.add_argument('--' + name, required=True)
    running.add_argument('--arm', choices=ARMS, required=True)
    comparison = sub.add_parser('compare')
    comparison.add_argument('--protocol', type=Path, required=True)
    comparison.add_argument('--protocol-sha256', required=True)
    comparison.add_argument('--maximum-serving-bytes', type=int, required=True)
    comparison.add_argument('--output', type=Path, required=True)
    for arm in ARMS:
        comparison.add_argument('--' + arm.replace('_', '-'), type=Path)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze(args.dataset_dir, args.split, strict_json(args.limits.read_bytes()), args.output)
        print(json.dumps({'protocolSha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))
        return 0
    if args.command == 'compare':
        result = compare({arm: getattr(args, arm) for arm in ARMS if getattr(args, arm)},
                         args.protocol, args.protocol_sha256, args.maximum_serving_bytes)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as stream:
            stream.write(canonical_bytes(result) + b'\n')
        print(json.dumps(result))
        return 0 if result['comparisonEvidencePassed'] else 1
    result = run(args.protocol, args.protocol_sha256, args.artifact_manifest, args.arm,
                 args.base_url, args.model, args.api_key_env_file, args.output_dir)
    print(json.dumps(result))
    return 0 if result['protocolPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
