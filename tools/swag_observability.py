"""Content-free local spans and observed timing summaries; no automatic upload."""
from __future__ import annotations

import argparse
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import json
import math
import os
from pathlib import Path
import re
import statistics
import threading
import time
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
CURRENT: ContextVar[Span | None] = ContextVar('swag_span', default=None)
SAFE_NAME = re.compile(r'[a-zA-Z0-9_.:-]{1,96}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
TRACEPARENT = re.compile(r'00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})\Z')
ATTRIBUTES = {'configurationSha256', 'sourceSha256', 'eventId', 'engineRequestId',
              'engineOperationId', 'engineConfigurationSha256', 'operation', 'httpStatus',
              'inputBytes', 'outputBytes', 'modelExecuted', 'engineIntegrated'}


def trace_directory() -> Path:
    return Path(os.environ.get('SWAG_TRACE_DIR', str(ROOT / '.swag' / 'traces'))).resolve()


class Span:
    def __init__(self, operation: str, *, traceparent: str | None = None):
        if not SAFE_NAME.fullmatch(operation):
            raise ValueError('Invalid trace operation')
        self.operation = operation
        self.parent = CURRENT.get()
        supplied = TRACEPARENT.fullmatch(traceparent) if isinstance(traceparent, str) else None
        if traceparent is not None and (not supplied or int(supplied[1], 16) == 0 or int(supplied[2], 16) == 0):
            raise ValueError('Invalid traceparent')
        self.trace_id = self.parent.trace_id if self.parent else supplied[1] if supplied else uuid4().hex
        self.span_id = uuid4().hex[:16]
        self.parent_id = self.parent.span_id if self.parent else supplied[2] if supplied else None
        self.attributes: dict[str, Any] = {}
        self.writer = self.parent.writer if self.parent else None
        self.lock = self.parent.lock if self.parent else threading.Lock()
        self.count = self.parent.count if self.parent else [0]
        self.failure: str | None = None

    def fail(self, error_type: str) -> None:
        if not SAFE_NAME.fullmatch(error_type):
            raise ValueError('Invalid error class')
        self.failure = error_type

    @property
    def traceparent(self) -> str:
        return f'00-{self.trace_id}-{self.span_id}-01'

    def set(self, **attributes: Any) -> None:
        for name, value in attributes.items():
            if name not in ATTRIBUTES:
                raise ValueError('Unsupported trace attribute')
            if name.endswith('Sha256'):
                valid = isinstance(value, str) and bool(HASH.fullmatch(value))
            elif name in {'inputBytes', 'outputBytes', 'httpStatus'}:
                valid = type(value) is int and 0 <= value <= 2**63 - 1
            elif name in {'modelExecuted', 'engineIntegrated'}:
                valid = type(value) is bool
            else:
                valid = isinstance(value, str) and bool(SAFE_NAME.fullmatch(value))
            if not valid:
                raise ValueError('Invalid trace attribute')
            self.attributes[name] = value

    def emit(self, event: str, **fields: Any) -> None:
        record = {'schema': 'swag.trace/v1', 'timestamp': datetime.now(timezone.utc).isoformat(),
                  'traceId': self.trace_id, 'spanId': self.span_id, 'parentSpanId': self.parent_id,
                  'operation': self.operation, 'event': event, 'attributes': dict(self.attributes), **fields}
        with self.lock:
            if self.count[0] >= 1024:
                raise RuntimeError('Trace event limit exceeded')
            self.writer.write(json.dumps(record, separators=(',', ':')) + '\n')
            self.writer.flush()
            self.count[0] += 1

    def __enter__(self):
        if self.writer is None:
            directory = trace_directory()
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f'{self.trace_id}-{self.span_id}.jsonl'
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            self.writer = os.fdopen(descriptor, 'w', encoding='utf-8')
        self.started = time.perf_counter_ns()
        try:
            self.emit('start')
        except BaseException:
            if self.parent is None:
                self.writer.close()
            raise
        self.token = CURRENT.set(self)
        return self

    def __exit__(self, kind, error, traceback):
        try:
            # Exception messages, source lines, arguments and local variables can
            # contain prompts or secrets. Keep only our code locations and class.
            frames = []
            cursor = traceback
            while cursor is not None:
                filename = Path(cursor.tb_frame.f_code.co_filename).resolve()
                if filename.parent == ROOT / 'tools':
                    frames.append({'file': filename.name, 'line': cursor.tb_lineno})
                cursor = cursor.tb_next
            error_type = kind.__name__ if kind and SAFE_NAME.fullmatch(kind.__name__) else 'Error' if kind else None
            self.emit('end', status='error' if kind or self.failure else 'ok',
                      durationMs=(time.perf_counter_ns() - self.started) / 1_000_000,
                      errorType=error_type or self.failure, frames=frames[-8:])
        finally:
            CURRENT.reset(self.token)
            if self.parent is None:
                self.writer.close()
        return False


def observed(operation: str):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with Span(operation):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def summarize(directory: Path) -> dict[str, Any]:
    groups: dict[tuple[str, str | None], list[dict]] = {}
    failures = []
    interrupted = invalid_files = 0
    files = sorted(directory.glob('*.jsonl'))
    active = CURRENT.get()
    # A status request must not classify its own open ancestors as interrupted.
    active_ids = set()
    while active is not None:
        active_ids.add((active.trace_id, active.span_id))
        active = active.parent
    for path in files:
        try:
            if path.stat().st_size > 2_000_000:
                raise ValueError('Oversized trace')
            starts, ends = {}, {}
            for line in path.read_text(encoding='utf-8').splitlines():
                row = json.loads(line)
                if row.get('schema') != 'swag.trace/v1' or not SAFE_NAME.fullmatch(row.get('operation', '')):
                    raise ValueError('Invalid trace')
                if (not isinstance(row.get('traceId'), str) or not re.fullmatch('[0-9a-f]{32}', row['traceId'])
                        or not isinstance(row.get('spanId'), str) or not re.fullmatch('[0-9a-f]{16}', row['spanId'])
                        or not isinstance(row.get('timestamp'), str) or not isinstance(row.get('attributes'), dict)):
                    raise ValueError('Invalid span identity')
                datetime.fromisoformat(row['timestamp'])
                configuration = row['attributes'].get('configurationSha256')
                if configuration is not None and (not isinstance(configuration, str) or not HASH.fullmatch(configuration)):
                    raise ValueError('Invalid configuration digest')
                identity = (row['traceId'], row['spanId'])
                if row['event'] == 'start':
                    if identity in starts:
                        raise ValueError('Duplicate start')
                    starts[identity] = row
                elif row['event'] == 'end':
                    duration = row.get('durationMs')
                    if (identity not in starts or identity in ends or row.get('status') not in {'ok', 'error'}
                            or type(duration) not in {int, float} or not math.isfinite(duration) or duration < 0
                            or row['operation'] != starts[identity]['operation']):
                        raise ValueError('Invalid terminal span')
                    ends[identity] = row
                else:
                    raise ValueError('Invalid event')
            interrupted += len(starts.keys() - ends.keys() - active_ids)
            for row in ends.values():
                key = (row['operation'], row.get('attributes', {}).get('configurationSha256'))
                groups.setdefault(key, []).append(row)
                if row['status'] == 'error':
                    # Preserve only the same narrow fields allowed by our writer.
                    error_type = row.get('errorType')
                    identity = row.get('traceId')
                    if (isinstance(error_type, str) and SAFE_NAME.fullmatch(error_type)
                            and isinstance(identity, str) and re.fullmatch('[0-9a-f]{32}', identity)):
                        failures.append({'traceId': identity, 'operation': row['operation'],
                                         'timestamp': row['timestamp'], 'errorType': error_type})
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            invalid_files += 1
    measurements = []
    for (operation, configuration), rows in sorted(groups.items(), key=lambda item: str(item[0])):
        durations = sorted(row['durationMs'] for row in rows)
        measurements.append({'operation': operation, 'configurationSha256': configuration,
                             'samples': len(rows), 'errors': sum(row['status'] == 'error' for row in rows),
                             'p50Ms': statistics.median(durations),
                             'p95Ms': durations[math.ceil(len(durations) * .95) - 1],
                             'maxMs': durations[-1]})
    return {'schema': 'swag.trace-summary/v1', 'files': len(files), 'invalidFiles': invalid_files,
            'incompleteSpans': interrupted, 'measurements': measurements,
            'recentFailures': sorted(failures, key=lambda row: row['timestamp'])[-25:],
            'usageObserved': False, 'modelQualityEvaluated': False,
            'scope': 'Observed client-operation timings; overlapping nested spans must not be added together.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['summarize'])
    parser.add_argument('--directory', type=Path, default=trace_directory())
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
