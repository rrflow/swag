"""Measure task-intent generalization on a project-held-out provisional corpus."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import time
from urllib.request import Request, build_opener

from swag_routing_contract import canonical_bytes, strict_json
from swag_routing_eval import NoRedirect, endpoint_url
from swag_task_corpus import LABELS, SYSTEM, lines, verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('corpus-dir', 'artifact-manifest', 'api-key-env-file', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    manifest = verify(args.corpus_dir)
    url = endpoint_url(args.base_url)
    keys = [line.split('=', 1)[1].strip() for line in args.api_key_env_file.read_text().splitlines()
            if line.startswith('VLLM_API_KEY=')]
    if len(keys) != 1 or not keys[0]:
        raise ValueError('Exactly one API key required')
    cases = lines(args.corpus_dir / 'development.cases.jsonl')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    artifact_bytes = args.artifact_manifest.read_bytes()
    (args.output_dir / 'artifact-manifest.json').write_bytes(artifact_bytes)
    (args.output_dir / 'corpus-manifest.json').write_bytes((args.corpus_dir / 'manifest.json').read_bytes())
    protocol = {'schemaVersion': 1, 'purpose': manifest['purpose'], 'scope': 'development',
                'systemPrompt': SYSTEM, 'temperature': 0, 'max_tokens': 32,
                'casesSha256': manifest['files']['development.cases.jsonl'],
                'runnerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output_dir / 'protocol.json').write_bytes(canonical_bytes(protocol) + b'\n')
    results = []
    opener = build_opener(NoRedirect())
    with (args.output_dir / 'results.jsonl').open('x', encoding='utf-8') as stream:
        for case in cases:
            payload = {'model': args.model, 'temperature': 0, 'max_tokens': 32,
                       'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': case['taskText']}]}
            row = {'taskId': case['taskId'], 'expected': case['taskFamily'], 'matched': False, 'valid': False}
            started = time.monotonic()
            try:
                req = Request(url, canonical_bytes(payload), {'Authorization': 'Bearer ' + keys[0], 'Content-Type': 'application/json'})
                with opener.open(req, timeout=120) as response:
                    body = strict_json(response.read(2_000_000))
                raw = body['choices'][0]['message']['content']
                row['rawOutput'] = raw
                row['usage'] = body.get('usage')
                parsed = strict_json(raw)
                row['valid'] = (isinstance(parsed, dict) and set(parsed) == {'taskFamily'}
                                and parsed['taskFamily'] in LABELS and body['model'] == args.model)
                row['matched'] = row['valid'] and parsed['taskFamily'] == case['taskFamily']
            except (ValueError, OSError, KeyError, IndexError, TypeError) as exc:
                row['errorClass'] = type(exc).__name__
            row['elapsedSeconds'] = time.monotonic() - started
            stream.write(canonical_bytes(row).decode() + '\n')
            stream.flush()
            results.append(row)
            print(json.dumps({'taskId': row['taskId'], 'matched': row['matched']}), flush=True)
    summary = {'schemaVersion': 1, 'model': args.model, 'cases': len(results),
               'matched': sum(row['matched'] for row in results), 'invalid': sum(not row['valid'] for row in results),
               'warmMedianSeconds': statistics.median(row['elapsedSeconds'] for row in results[1:]),
               'completedAt': datetime.now(timezone.utc).isoformat(),
               'corpusManifestSha256': hashlib.sha256((args.corpus_dir / 'manifest.json').read_bytes()).hexdigest(),
               'artifactManifestSha256': hashlib.sha256(artifact_bytes).hexdigest(),
               'resultsSha256': hashlib.sha256((args.output_dir / 'results.jsonl').read_bytes()).hexdigest(),
               'protocolSha256': hashlib.sha256((args.output_dir / 'protocol.json').read_bytes()).hexdigest(),
               'humanReviewed': False, 'providerRoutingEvaluated': False, 'deploymentQualified': False}
    (args.output_dir / 'summary.json').write_bytes(canonical_bytes(summary) + b'\n')
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
