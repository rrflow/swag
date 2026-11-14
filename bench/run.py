"""Send the same SystemOne requests to every competitor and record what each answered.

Every arm is a `/v1/systemone` endpoint, so SWAG, TypeSafe's hosted Jev, a KnowLine server and a
Clef wrapper are called identically. Arms are listed in a JSON file (see `arms.example.json`):

    {"name": "jev", "url": "https://api.typesafe.ai/v1/systemone", "model": "jev-latest", "credentialEnv": "TYPESAFE_API_KEY"}

Credentials are read from the named environment variable and never written to results. Only
`https://` URLs and `http://` loopback URLs are accepted, redirects are refused, and a failed row is
recorded as an error and scored as wrong; nothing is retried or silently dropped.

    python bench/run.py --arms bench/arms.json --rows bench/data/public_rows.jsonl --out bench/results
    python bench/run.py ... --only swag --limit 200 --sample-seed 7
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import json
import os
from pathlib import Path
import random
import time
from typing import Any
from urllib import error, parse, request

ARM_FIELDS = {'name', 'url', 'model', 'credentialEnv', 'timeoutSeconds', 'workers', 'note'}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *arguments: Any) -> None:
        return None


def load_arms(path: Path) -> list[dict]:
    arms = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(arms, list) or not arms:
        raise SystemExit('The arms file is a non-empty JSON list.')
    names = set()
    for arm in arms:
        if not isinstance(arm, dict) or not {'name', 'url'} <= set(arm) or not set(arm) <= ARM_FIELDS:
            raise SystemExit('Each arm has name and url, and may have ' + ', '.join(sorted(ARM_FIELDS - {'name', 'url'})) + '.')
        if arm['name'] in names:
            raise SystemExit(f"Arm names must be unique: {arm['name']}")
        names.add(arm['name'])
        url = parse.urlsplit(arm['url'])
        loopback = url.hostname is not None and (url.hostname == 'localhost' or _is_loopback(url.hostname))
        if url.scheme != 'https' and not (url.scheme == 'http' and loopback):
            raise SystemExit(f"Arm {arm['name']}: use https, or http on this machine only.")
        if not url.path.endswith('/v1/systemone'):
            raise SystemExit(f"Arm {arm['name']}: the url must end in /v1/systemone.")
        if arm.get('credentialEnv') and not os.environ.get(arm['credentialEnv']):
            raise SystemExit(f"Arm {arm['name']}: set {arm['credentialEnv']} first.")
    return arms


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def ask(arm: dict, row: dict) -> dict:
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if arm.get('credentialEnv'):
        headers['Authorization'] = 'Bearer ' + os.environ[arm['credentialEnv']]
    body = {'model': arm.get('model', 'default'), 'state': row['state'], 'questions': row['questions']}
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    started = time.perf_counter()
    try:
        req = request.Request(arm['url'], data=json.dumps(body).encode('utf-8'), headers=headers, method='POST')
        with opener.open(req, timeout=arm.get('timeoutSeconds', 120)) as response:
            payload = json.loads(response.read(20_000_000))
        status = 'ok' if isinstance(payload.get('answers'), dict) and set(payload['answers']) == set(row['questions']) else 'error'
        result = {'answers': payload.get('answers'), 'usage': payload.get('usage')}
        if isinstance(payload.get('swag'), dict):
            result['swagDecisions'] = {key: {k: v for k, v in value.items() if k in ('status', 'value', 'reason')}
                                       for key, value in payload['swag'].get('decisions', {}).items()}
    except error.HTTPError as failure:
        status, result = 'error', {'httpStatus': failure.code}
    except (error.URLError, TimeoutError, OSError, ValueError) as failure:
        status, result = 'error', {'failure': type(failure).__name__}
    return {'id': row['id'], 'benchmark': row.get('benchmark'), 'status': status,
            'seconds': round(time.perf_counter() - started, 4), **result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--arms', type=Path, required=True)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--only', action='append', help='Run only these arm names')
    parser.add_argument('--limit', type=int, help='Run a seeded sample of this many rows')
    parser.add_argument('--sample-seed', type=int, default=0)
    arguments = parser.parse_args(argv)
    arms = [arm for arm in load_arms(arguments.arms) if not arguments.only or arm['name'] in arguments.only]
    rows = [json.loads(line) for line in arguments.rows.read_text(encoding='utf-8').splitlines() if line.strip()]
    if arguments.limit:
        rows = random.Random(arguments.sample_seed).sample(rows, min(arguments.limit, len(rows)))
    arguments.out.mkdir(parents=True, exist_ok=True)
    for arm in arms:
        with ThreadPoolExecutor(max(1, int(arm.get('workers', 4)))) as pool:
            results = list(pool.map(lambda row: ask(arm, row), rows))
        target = arguments.out / f"{arm['name']}.jsonl"
        with target.open('w', encoding='utf-8', newline='\n') as stream:
            for result in results:
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
        failed = sum(result['status'] != 'ok' for result in results)
        print(json.dumps({'arm': arm['name'], 'rows': len(results), 'errors': failed, 'file': str(target)}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
