#!/usr/bin/env python3
"""Run fixed synthetic routing cases against a real local model endpoint."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def policy_oracle(task: dict, candidates: list[dict]) -> dict:
    """Independent deterministic fixture baseline; never a runtime authority."""
    eligible = [candidate for candidate in candidates
                if candidate['authorized'] and candidate['healthy'] and candidate['quotaAvailable']
                and candidate['quality'] >= task['minimumQuality']
                and candidate['cost'] <= task['maxCost']
                and task['requestedEffort'] in candidate['efforts']
                and (not task['localOnly'] or candidate['location'] == 'local')]
    if not eligible:
        return {'bindingId':None, 'effort':None}
    choice = min(eligible, key=lambda item: (item['cost'], item['bindingId']))
    return {'bindingId':choice['bindingId'], 'effort':task['requestedEffort']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--api-key-env-file', type=Path, required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:8083')
    parser.add_argument('--model', default='swag-qwen3-coder-bf16-baseline')
    args = parser.parse_args()
    content = args.cases.read_bytes()
    protocol = json.loads(content)
    if not protocol['cases'] or len({case['id'] for case in protocol['cases']}) != len(protocol['cases']):
        raise ValueError('Require nonempty cases with unique identities')
    key = next(line.split('=', 1)[1] for line in args.api_key_env_file.read_text().splitlines()
               if line.startswith('VLLM_API_KEY='))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    # Reserve a fresh evidence file before any inference, never overwrite a run.
    with args.output.open('x', encoding='utf-8') as stream:
        for case in protocol['cases']:
            candidates = copy.deepcopy(protocol['candidates'])
            if case.get('exhaustQuota'):
                for candidate in candidates:
                    candidate['quotaAvailable'] = False
            if policy_oracle(case['input'], candidates) != case['expected']:
                raise ValueError('Fixture gold disagrees with the deterministic policy oracle')
            payload = {'model':args.model, 'temperature':0, 'max_tokens':96,
                       'messages':[{'role':'system', 'content':protocol['systemPrompt']},
                                   {'role':'user', 'content':json.dumps({**case['input'], 'candidates':candidates})}]}
            request = urllib.request.Request(args.base_url.rstrip('/')+'/v1/chat/completions',
                data=json.dumps(payload).encode(), headers={'Content-Type':'application/json',
                    'Authorization':'Bearer '+key}, method='POST')
            started = time.monotonic()
            result = {'caseId':case['id'], 'expected':case['expected'], 'matched':False,
                      'timestamp':datetime.now(timezone.utc).isoformat(),
                      'protocolSha256':hashlib.sha256(content).hexdigest()}
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    body = json.load(response)
                raw = body['choices'][0]['message']['content']
                result.update({'rawOutput':raw, 'usage':body.get('usage'),
                               'servedModel':body.get('model')})
                actual = json.loads(raw)
                result.update({'actual':actual, 'matched':actual == case['expected']})
            except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
                result['errorClass'] = type(error).__name__
            result['elapsedSeconds'] = time.monotonic() - started
            results.append(result)
            stream.write(json.dumps(result)+'\n')
            stream.flush()
            print(json.dumps({'caseId':case['id'],'matched':result['matched'],
                              'elapsedSeconds':result['elapsedSeconds']}), flush=True)
    summary = {'cases':len(results), 'matched':sum(row['matched'] for row in results),
               'scope':'synthetic smoke only', 'deploymentQualified':False}
    print(json.dumps(summary), flush=True)
    return 0 if all(row['matched'] for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
