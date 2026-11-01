"""Evaluate pinned local Liquid d1 weights; separate comparator, not a Qwen export."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

from swag_routing_contract import SYSTEM_PROMPT, canonical_bytes, digest, score_output, strict_json
from swag_routing_eval import implementation_hashes, summarize, validate_limits


def make_question(request: dict) -> tuple[dict, dict]:
    choices = {'abstain': 'No eligible binding exists under all supplied policy constraints.'}
    mapping = {'abstain': None}
    for index, candidate in enumerate(request['candidates']):
        key = f'candidate_{index}'
        choices[key] = 'Select binding ' + candidate['bindingId'] + ': ' + canonical_bytes(candidate).decode()
        mapping[key] = candidate['bindingId']
    instruction = SYSTEM_PROMPT.split('Return exactly')[0] + ' Choose abstain only when none qualify.'
    return {'route': {'type': 'choice', 'instructions': instruction, 'criteria': choices}}, mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    content = args.protocol.read_bytes()
    if hashlib.sha256(content).hexdigest() != args.protocol_sha256:
        raise ValueError('Protocol digest mismatch')
    protocol = strict_json(content)
    if protocol['implementation'] != implementation_hashes() or protocol['systemPrompt'] != SYSTEM_PROMPT:
        raise ValueError('Protocol implementation changed')
    validate_limits(protocol['limits'])
    manifest = strict_json(args.manifest.read_bytes())
    snapshot = Path(manifest['snapshot']).resolve(strict=True)
    if manifest['model'] != 'LiquidAI/d1-3B' or manifest['revision'] != '051bcc464b01b9f92942b364d9586b0ef5912432':
        raise ValueError('Unexpected model or unreviewed code revision')
    for name, expected in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Invalid manifest path')
        hasher = hashlib.sha256()
        with (snapshot / name).open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                hasher.update(block)
        if hasher.hexdigest() != expected['sha256']:
            raise ValueError('Model artifact changed')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import torch
    from transformers import AutoModel

    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'protocol.json').write_bytes(content)
    (args.output_dir / 'artifact-manifest.json').write_bytes(args.manifest.read_bytes())
    runner_bytes = Path(__file__).read_bytes()
    (args.output_dir / 'swag_d1_eval.py').write_bytes(runner_bytes)
    print(json.dumps({'phase': 'load', 'gpu': torch.cuda.get_device_name(0)}), flush=True)
    model = AutoModel.from_pretrained(str(snapshot), trust_remote_code=True,
                                     local_files_only=True, dtype=torch.bfloat16).to('cuda').eval()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    results = []
    with (args.output_dir / 'results.jsonl').open('x', encoding='utf-8') as stream:
        for case in protocol['cases']:
            question, mapping = make_question(case['request'])
            torch.cuda.synchronize()
            start = time.monotonic()
            with torch.inference_mode():
                response = model.system_one(case['request'], question)
            torch.cuda.synchronize()
            elapsed = time.monotonic() - start
            answer = response['answers']['route']
            selected = mapping[answer['choice']]
            actual = {'bindingId': selected, 'effort': case['request']['requestedEffort'] if selected else None}
            raw = canonical_bytes(actual).decode()
            result = {'caseId': case['caseId'], 'requestSha256': digest(case['request']),
                      'expected': case['expected'], 'rawOutput': raw, 'decisionAnswer': answer,
                      'usage': response.get('usage'), 'elapsedSeconds': elapsed,
                      **score_output(raw, case['request'], case['expected'])}
            results.append(result)
            stream.write(canonical_bytes(result).decode() + '\n')
            stream.flush()
            print(json.dumps({'caseId': case['caseId'], 'matched': result['matched'],
                              'elapsedSeconds': elapsed}), flush=True)
    summary = {**summarize(results, protocol['limits']), 'scope': protocol['scope'],
               'arm': 'small_decision_comparator', 'model': manifest['model'],
               'completedAt': datetime.now(timezone.utc).isoformat(),
               'protocolSha256': args.protocol_sha256,
               'runnerSha256': hashlib.sha256(runner_bytes).hexdigest(),
               'artifactManifestSha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
               'resultsSha256': hashlib.sha256((args.output_dir / 'results.jsonl').read_bytes()).hexdigest(),
               'torch': torch.__version__, 'gpu': torch.cuda.get_device_name(0),
               'gpuPeakAllocatedBytes': torch.cuda.max_memory_allocated(),
               'gpuPeakReservedBytes': torch.cuda.max_memory_reserved(),
               'limitations': ['Different model/runtime and host from Qwen endpoint; not an isolated serving comparison.',
                              'Named choice API guarantees membership; effort is mapped from request, not generated.',
                              'Probabilities are uncalibrated on SWAG; synthetic development only.',
                              'GPU allocation counters are not total unified-memory footprint.']}
    (args.output_dir / 'summary.json').write_bytes(canonical_bytes(summary) + b'\n')
    print(json.dumps(summary), flush=True)
    return 0 if summary['protocolPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
