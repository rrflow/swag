"""Bounded trainer observations, not an engine job ledger or training permission."""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import islice
import json
import math
from pathlib import Path
import re
import signal
import time
from uuid import uuid4

from swag_training_artifacts import read_object

METRICS = {'loss', 'eval_loss', 'learning_rate', 'grad_norm', 'train_runtime', 'train_loss'}
EVENTS = {'started', 'progress', 'checkpoint_saved', 'stop_observed', 'loop_returned', 'artifacts_saved', 'failed'}
ERROR_NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]{0,95}\Z')


def numeric_metrics(values: dict) -> dict:
    return {key: value for key, value in values.items() if key in METRICS
            and type(value) in (int, float) and math.isfinite(value) and value >= 0}


def progress(directory: Path) -> dict:
    """Read a saved TrainerState. Its age does not attest process liveness."""
    path = directory / 'trainer_state.json'
    observations = list(islice(directory.glob('training-observations-*.jsonl'), 9))
    if observations:
        return observed_progress(observations)
    if not path.exists():
        return {'state': 'not_recorded', 'globalStep': None, 'maxSteps': None, 'points': []}
    try:
        data, _ = read_object(path)
        step, maximum = data.get('global_step'), data.get('max_steps')
        history = data.get('log_history')
        if (type(step) is not int or type(maximum) is not int or step < 0 or maximum < 1 or step > maximum
                or not isinstance(history, list) or len(history) > 100_000):
            raise ValueError('Invalid trainer state')
        points = []
        for item in history:
            if not isinstance(item, dict) or type(item.get('step')) is not int or not 0 <= item['step'] <= step:
                raise ValueError('Invalid training metric step')
            values = numeric_metrics(item)
            if values:
                points.append({'step': item['step'], **values})
        return {'state': 'saved_state', 'globalStep': step, 'maxSteps': maximum,
                'points': points[-200:], 'pointsOmitted': max(0, len(points) - 200),
                'processLiveness': 'unknown', 'completionVerified': False}
    except (OSError, ValueError, TypeError, AttributeError):
        return {'state': 'invalid_state', 'globalStep': None, 'maxSteps': None, 'points': []}


def observed_progress(paths: list[Path]) -> dict:
    try:
        if len(paths) != 1:
            raise ValueError('A fresh training directory must have exactly one observed attempt')
        with paths[0].open('rb') as source:
            content = source.read(4_000_001)
        if len(content) > 4_000_000:
            raise ValueError('Observation projection exceeds read bound')
        lines = content.splitlines()
        partial = bool(content and not content.endswith(b'\n'))
        if partial:
            lines = lines[:-1]
        rows, points, attempt = [], [], None
        for index, line in enumerate(lines):
            row = json.loads(line)
            if (row.get('schema') != 'swag.training-observation/v1' or type(row.get('sequence')) is not int or row['sequence'] != index
                    or row.get('kind') not in EVENTS
                    or not isinstance(row.get('attemptId'), str) or not re.fullmatch('[0-9a-f]{32}', row['attemptId'])
                    or (attempt is not None and row['attemptId'] != attempt)):
                raise ValueError('Invalid training observation sequence')
            attempt = row['attemptId']
            datetime.fromisoformat(row['observedAt'])
            if 'globalStep' in row:
                if (type(row['globalStep']) is not int or type(row.get('maxSteps')) is not int
                        or not 0 <= row['globalStep'] <= row['maxSteps'] or row['maxSteps'] < 1):
                    raise ValueError('Invalid observed progress')
                metrics = numeric_metrics(row.get('metrics', {}))
                if metrics:
                    points.append({'step': row['globalStep'], **metrics})
            rows.append(row)
        latest = next((row for row in reversed(rows) if 'globalStep' in row), {})
        return {'state': 'observed_progress', 'globalStep': latest.get('globalStep'),
                'maxSteps': latest.get('maxSteps'), 'points': points[-200:],
                'pointsOmitted': max(0, len(points) - 200), 'attemptId': attempt,
                'lastObservedAt': rows[-1]['observedAt'] if rows else None,
                'lastObservation': rows[-1]['kind'] if rows else None,
                'incompleteTail': partial, 'processLiveness': 'unknown', 'completionVerified': False}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'state': 'invalid_state', 'globalStep': None, 'maxSteps': None, 'points': []}


class TrainingObserver:
    """One attempt's content-free observations; SIGINT/SIGTERM request a cooperative stop."""
    def __init__(self, directory: Path, *, limit_bytes: int = 4_000_000):
        if type(limit_bytes) is not int or not 1024 <= limit_bytes <= 4_000_000:
            raise ValueError('Invalid observation byte limit')
        self.attempt_id = uuid4().hex
        self.path = directory / ('training-observations-' + self.attempt_id + '.jsonl')
        self.writer = self.path.open('x', encoding='utf-8')
        self.limit = limit_bytes
        self.size = self.sequence = 0
        self.started = time.monotonic()
        self.stop_requested = False
        self.previous_handlers = {}

    def emit(self, kind: str, state=None, metrics: dict | None = None, error_type: str | None = None):
        if kind not in EVENTS:
            raise ValueError('Invalid observation kind')
        record = {'schema': 'swag.training-observation/v1', 'attemptId': self.attempt_id,
                  'sequence': self.sequence, 'observedAt': datetime.now(timezone.utc).isoformat(),
                  'elapsedSeconds': time.monotonic() - self.started, 'kind': kind,
                  'metrics': numeric_metrics(metrics or {}), 'stopRequested': self.stop_requested}
        if state is not None:
            for source, target in (('global_step', 'globalStep'), ('max_steps', 'maxSteps')):
                value = getattr(state, source, None)
                if type(value) is not int or value < 0:
                    raise ValueError('Invalid observed training step')
                record[target] = value
            if record['maxSteps'] == 0 and record['globalStep'] == 0:
                del record['globalStep'], record['maxSteps']
            elif record['globalStep'] > record['maxSteps']:
                raise ValueError('Observed step exceeds training bound')
        if error_type is not None:
            record['errorType'] = error_type if ERROR_NAME.fullmatch(error_type) else 'Error'
        encoded = json.dumps(record, separators=(',', ':'), allow_nan=False) + '\n'
        size = len(encoded.encode('utf-8'))
        if self.size + size > self.limit:
            raise ValueError('Training observations exceed byte budget')
        self.writer.write(encoded)
        self.writer.flush()
        self.sequence += 1
        self.size += size

    def request_stop(self, signum=None, frame=None):
        self.stop_requested = True

    def install_signals(self):
        for name in ('SIGINT', 'SIGTERM'):
            sig = getattr(signal, name)
            self.previous_handlers[sig] = signal.signal(sig, self.request_stop)

    def close(self):
        for sig, handler in self.previous_handlers.items():
            signal.signal(sig, handler)
        self.writer.close()

    def callback(self):
        # Import only inside an explicitly admitted training process.
        from transformers import TrainerCallback
        observer = self

        class Callback(TrainerCallback):
            def on_train_begin(self, args, state, control, **kwargs):
                observer.emit('started', state)

            def on_log(self, args, state, control, logs=None, **kwargs):
                observer.emit('progress', state, logs)

            def on_step_end(self, args, state, control, **kwargs):
                if observer.stop_requested:
                    control.should_training_stop = True
                    control.should_save = True
                    observer.emit('stop_observed', state)
                return control

            def on_save(self, args, state, control, **kwargs):
                observer.emit('checkpoint_saved', state)

            def on_train_end(self, args, state, control, **kwargs):
                observer.emit('loop_returned', state)

        return Callback()
