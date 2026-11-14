"""Local decision log for the developer tools: one JSON line per decision request.

Each record keeps what a developer needs to see why SWAG decided what it did: per question the
type, the decision and its status, confidence, the rules and preferences that applied, and the
time each step took. The caller's state is stored only as a digest and length unless
`SWAG_LOG_STATE=1`; it can hold private material. The log lives in `.swag/` and is never committed.

    python tools/swag_decision_log.py            # summary and the last 50 records as JSON
    python tools/swag_decision_log.py --limit 200
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import threading
from typing import Any
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'swag.decision-log/v1'
MAX_READ_BYTES = 20_000_000
_LOCK = threading.Lock()


def location() -> Path:
    return Path(os.environ.get('SWAG_DECISION_LOG') or ROOT / '.swag' / 'decision-log.jsonl')


def _clip(value: Any, limit: int = 240) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit - 1] + '…'


def record(request: dict, response: dict, source: str) -> dict:
    """Build the log record for one decision request and its response."""
    state_text = json.dumps(request['state'], ensure_ascii=False, sort_keys=True, default=str)
    swag = response['swag']
    questions = {}
    for question_id, question in request['questions'].items():
        decision = swag['decisions'][question_id]
        row = {key: decision.get(key) for key in (
            'mode', 'status', 'value', 'option', 'confidence', 'probability', 'abstainBelow', 'abstainBelowOrigin',
            'reason', 'abstainReason', 'rules', 'skippedRules', 'preferences', 'forbidden', 'defaultedBy', 'engineMs')
            if key in decision}
        row['instructions'] = _clip(question.get('instructions', ''))
        if question_id in response['answers']:
            row['answer'] = response['answers'][question_id]
        questions[question_id] = row
    entry = {
        'schema': SCHEMA,
        'id': uuid.uuid4().hex,
        'at': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'source': source,
        'template': request.get('swag', {}).get('template'),
        'stateSha256': hashlib.sha256(state_text.encode()).hexdigest(),
        'stateChars': len(state_text),
        'engine': swag['engine'],
        'timings': swag['timings'],
        'effectiveDigest': swag['effective']['digest'],
        'staleFacts': [fact['id'] for fact in swag['effective']['staleFacts']],
        'ruleConflicts': swag['effective']['ruleConflicts'],
        'suggestions': swag['suggestions'],
        'questions': questions,
    }
    if os.environ.get('SWAG_LOG_STATE') == '1':
        entry['state'] = request['state']
    return entry


def append(entry: dict) -> None:
    path = location()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'
    with _LOCK, path.open('a', encoding='utf-8') as stream:
        stream.write(line)


def read(limit: int = 50) -> dict:
    """The newest records and a summary of all records in the log."""
    path = location()
    rows: list[dict] = []
    if path.is_file():
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - MAX_READ_BYTES))
            for raw in stream.read().splitlines():
                try:
                    item = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(item, dict) and item.get('schema') == SCHEMA:
                    rows.append(item)
    statuses: dict[str, dict[str, int]] = {}
    hops: dict[str, list[float]] = {}
    confidence: dict[str, list[float]] = {}
    for row in rows:
        for key, value in row.get('timings', {}).items():
            hops.setdefault(key, []).append(value)
        for question in row.get('questions', {}).values():
            mode = question.get('mode', 'unknown')
            statuses.setdefault(mode, {})
            statuses[mode][question.get('status', 'unknown')] = statuses[mode].get(question.get('status', 'unknown'), 0) + 1
            if isinstance(question.get('confidence'), (int, float)):
                confidence.setdefault(mode, []).append(question['confidence'])

    def spread(values: list[float]) -> dict:
        ordered = sorted(values)
        return {'samples': len(ordered), 'median': round(statistics.median(ordered), 3),
                'p95': round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 3)}

    return {
        'schema': SCHEMA,
        'state': 'recorded' if rows else 'empty',
        'requests': len(rows),
        'byMode': statuses,
        'hopsMs': {key: spread(values) for key, values in hops.items()},
        'confidence': {key: spread(values) for key, values in confidence.items()},
        'records': list(reversed(rows[-max(1, min(limit, 500)):])),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=50)
    arguments = parser.parse_args()
    # ASCII output: the developer UI reads this through a pipe whose encoding varies by platform.
    print(json.dumps(read(arguments.limit), ensure_ascii=True, allow_nan=False))
