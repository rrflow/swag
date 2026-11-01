"""Check retained A/B/C evidence. This report cannot activate an engine model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from swag_evidence_projection import project_run
from swag_routing_contract import canonical_bytes, strict_json
from swag_routing_eval import verify_dataset

ARMS = ('base_bf16', 'custom_bf16', 'custom_quantized')


def serving_identity_present(directory: Path, summary: dict, manifest: dict) -> bool:
    if summary.get('serverIdentityAttested') is not True:
        return False
    path = directory / 'serving-identity.json'
    raw = directory / 'serving-identity.raw'
    if not path.exists() or not raw.exists():
        return False
    identity = strict_json(path.read_bytes())
    expected_files = {name: row.get('sha256') for name, row in manifest.get('files', {}).items()}
    return bool(expected_files and identity.get('scope') == 'observed_serving_process'
                and identity.get('artifactManifestSha256') == summary['artifactManifestSha256']
                and identity.get('protocolSha256') == summary['protocolSha256']
                and identity.get('verifiedArtifactFiles') == expected_files
                and identity.get('processIdentity') and identity.get('runtimeIdentity')
                and identity.get('rawEvidenceSha256') == hashlib.sha256(raw.read_bytes()).hexdigest())


def assess(runs: dict[str, Path], dataset: Path | None, maximum_quantized_bytes: int = 29_000_000_000) -> dict:
    if type(maximum_quantized_bytes) is not int or maximum_quantized_bytes < 1:
        raise ValueError('Positive total serving memory limit required')
    reasons, retained, manifests, summaries, protocols = [], {}, {}, {}, {}
    admitted = None
    if dataset is None:
        reasons.append('Missing independently reviewed acceptance dataset')
    else:
        admitted = verify_dataset(dataset)
    for arm in ARMS:
        directory = runs.get(arm)
        if directory is None:
            reasons.append('Missing arm: ' + arm)
            continue
        view = project_run(directory)  # Recompute scores from original outputs, including every failure.
        summary = strict_json((directory / 'summary.json').read_bytes())
        protocol = strict_json((directory / 'protocol.json').read_bytes())
        manifest = strict_json((directory / 'artifact-manifest.json').read_bytes())
        retained[arm] = {'provenance': view['provenance'], 'metrics': view['metrics']}
        manifests[arm], summaries[arm], protocols[arm] = manifest, summary, protocol
        if summary.get('arm') != arm:
            reasons.append(arm + ': reported arm mismatch')
        if view['scope'] != 'acceptance':
            reasons.append(arm + ': development evidence cannot qualify a model')
        if not view['metrics']['protocolPassed'] or view['metrics']['policyViolations']:
            reasons.append(arm + ': frozen protocol failed or contains policy violations')
        if not serving_identity_present(directory, summary, manifest):
            reasons.append(arm + ': serving identity has no runtime attestation')
        if not isinstance(manifest.get('files'), dict) or not manifest['files']:
            reasons.append(arm + ': missing bound artifact inventory')
        if dataset is not None and admitted is not None:
            admission_sha = hashlib.sha256((dataset / 'manifest.json').read_bytes()).hexdigest()
            if protocol.get('source', {}).get('admissionManifestSha256') != admission_sha:
                reasons.append(arm + ': protocol is not bound to this admitted dataset')
            expected = [strict_json(line) for line in (dataset / 'acceptance.cases.jsonl').read_bytes().splitlines() if line.strip()]
            if protocol.get('cases') != expected:
                reasons.append(arm + ': acceptance cases differ from admitted split')
            if any(case.get('sourceKind') != 'real_observation' for case in expected):
                reasons.append(arm + ': acceptance requires real observations')
        if arm == 'custom_quantized':
            memory_path = directory / 'serving-memory.json'
            if not memory_path.exists():
                reasons.append(arm + ': missing total serving memory measurement')
            else:
                measurement = strict_json(memory_path.read_bytes())
                if (measurement.get('scope') != 'total_serving_peak'
                        or measurement.get('protocolSha256') != summary['protocolSha256']
                        or measurement.get('artifactManifestSha256') != summary['artifactManifestSha256']
                        or type(measurement.get('bytes')) is not int
                        or not 0 < measurement['bytes'] <= maximum_quantized_bytes
                        or not measurement.get('method') or not measurement.get('rawEvidenceSha256')):
                    reasons.append(arm + ': memory evidence is incomplete, mismatched or exceeds the target')
                else:
                    evidence = directory / 'serving-memory.raw'
                    if not evidence.exists() or hashlib.sha256(evidence.read_bytes()).hexdigest() != measurement['rawEvidenceSha256']:
                        reasons.append(arm + ': memory raw evidence missing or changed')
    if len(retained) == 3:
        if len({row['provenance']['protocolSha256'] for row in retained.values()}) != 1:
            reasons.append('All three arms must use the exact same frozen protocol')
        base, custom, quantized = (manifests[arm] for arm in ARMS)
        base_sha = summaries['base_bf16']['artifactManifestSha256']
        custom_sha = summaries['custom_bf16']['artifactManifestSha256']
        if (base.get('custom_checkpoint') is not False or base.get('precision') not in ('bf16', 'bfloat16')
                or custom.get('custom_checkpoint') is not True or custom.get('precision') not in ('bf16', 'bfloat16')
                or custom.get('baseManifestSha256') != base_sha):
            reasons.append('Custom BF16 lineage does not bind the original BF16 base')
        if (quantized.get('custom_checkpoint') is not True
                or quantized.get('parentManifestSha256') != custom_sha
                or quantized.get('precision') in (None, 'bf16', 'bfloat16')
                or not quantized.get('quantizationMethod')):
            reasons.append('Quantized artifact is not bound to exactly the custom BF16 checkpoint')
        # Relative regressions need declared, frozen allowances; no post-result defaults.
        comparison = protocols['base_bf16'].get('comparisonLimits')
        if not isinstance(comparison, dict) or set(comparison) != {'maximumCustomAccuracyDrop', 'maximumQuantizedAccuracyDrop'}:
            reasons.append('Missing frozen relative-quality limits')
        else:
            for key in comparison:
                if type(comparison[key]) not in (int, float) or not 0 <= comparison[key] <= 1:
                    raise ValueError('Invalid relative-quality threshold')
            a, b, c = (retained[arm]['metrics']['accuracy'] for arm in ARMS)
            if a - b > comparison['maximumCustomAccuracyDrop'] or b - c > comparison['maximumQuantizedAccuracyDrop']:
                reasons.append('Relative-quality regression exceeds the frozen allowance')
    return {'schemaVersion': 1, 'kind': 'swag.offline_qualification_report',
            'comparisonEvidencePassed': not reasons, 'deploymentQualified': False,
            'promotionAuthorized': False, 'reasons': reasons, 'arms': retained,
            'maximumQuantizedServingBytes': maximum_quantized_bytes,
            'limitations': ['Local evidence attestations still require independent verification.',
                           'Installed engine admission, downstream outcomes, rollback and candidate PR/CI remain required.']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arm in ARMS:
        parser.add_argument('--' + arm.replace('_', '-'), type=Path)
    parser.add_argument('--dataset-dir', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = assess({arm: getattr(args, arm) for arm in ARMS if getattr(args, arm)}, args.dataset_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical_bytes(result) + b'\n')
    print(json.dumps(result))
    return 0 if result['comparisonEvidencePassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
