"""Publish a verified, content-free evaluation report and confirm stored readback."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib import parse, request

from swag_evidence_projection import project_run, report_record
from swag_routing_contract import canonical_bytes, strict_json
from swag_routing_eval import NoRedirect, endpoint_url


def exchange(url: str, key: str, payload: dict | None = None) -> dict:
    req = request.Request(url, data=canonical_bytes(payload) if payload is not None else None,
                          headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
                          method='POST' if payload is not None else 'GET')
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=15) as response:
            body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('Response exceeds limit')
        result = strict_json(body)
        if not isinstance(result, dict):
            raise ValueError('Expected an object response')
        return result
    except Exception as exc:
        raise RuntimeError('Signal sink exchange failed: ' + type(exc).__name__) from None


def publish_and_verify(run_dir: Path, base_url: str, key: str, project: str,
                       expected_devspace: str, output: Path, verify_only: bool = False) -> dict:
    endpoint_url(base_url)  # Same HTTPS/loopback and no embedded credential restrictions.
    base = base_url.rstrip('/')
    if base.endswith('/v1'):
        base = base[:-3]
    if not key.strip() or not expected_devspace:
        raise ValueError('A credential and expected devspace are required')
    record = report_record(project_run(run_dir), project)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'request.json').write_bytes(canonical_bytes({'turns': [record]}) + b'\n')
    own = exchange(base + '/v1/whoami', key)
    if own.get('devspace') != expected_devspace:
        raise ValueError('Credential resolves to an unexpected devspace; nothing published')
    acknowledgements = []
    for attempt in range(0 if verify_only else 2):
        ack = exchange(base + '/v1/turns', key, {'turns': [record]})
        if type(ack.get('accepted')) is not int or ack['accepted'] != 1 or ack.get('devspace') != expected_devspace:
            raise ValueError('Signal sink did not acknowledge one event in the expected devspace')
        clean = {name: ack.get(name) for name in ('devspace', 'accepted', 'new', 'replaced')}
        (output / f'ack-{attempt}.json').write_bytes(canonical_bytes(clean) + b'\n')
        acknowledgements.append(clean)
    if not verify_only and (acknowledgements[1]['new'] != 0 or acknowledgements[1]['replaced'] != 1):
        raise ValueError('Retry did not replace the same event')
    fetched = exchange(base + '/v1/turns?agent=swag-evidence&limit=1000', key)
    if fetched.get('devspace') != expected_devspace or not isinstance(fetched.get('turns'), list):
        raise ValueError('Readback devspace or shape mismatch')
    matching = [row for row in fetched['turns'] if row.get('event_id') == record['event_id']]
    if matching != [record]:
        raise ValueError('Stored event differs from sent projection or is not unique')
    receipt = {'schemaVersion': 1, 'scope': 'signal_sink_readback' if verify_only else 'signal_sink_ingest_retry_readback',
               'completedAt': datetime.now(timezone.utc).isoformat(), 'eventId': record['event_id'],
               'reportSha256': hashlib.sha256(canonical_bytes(record)).hexdigest(),
               'devspace': expected_devspace, 'acknowledgements': acknowledgements,
               'storedMatches': True, 'contentIncluded': False,
               'engineIntegrated': False, 'modelQualified': False,
               'endpointScope': 'loopback' if parse.urlsplit(base).hostname in {'localhost', '127.0.0.1', '::1'} else 'remote'}
    (output / 'receipt.json').write_bytes(canonical_bytes(receipt) + b'\n')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run-dir', 'credential-file', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--devspace', required=True)
    parser.add_argument('--project', default='swag')
    parser.add_argument('--verify-only', action='store_true', help='Only retrieve and compare an already stored report.')
    args = parser.parse_args()
    receipt = publish_and_verify(args.run_dir, args.base_url, args.credential_file.read_text().strip(),
                                 args.project, args.devspace, args.output_dir, args.verify_only)
    print(json.dumps(receipt))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
