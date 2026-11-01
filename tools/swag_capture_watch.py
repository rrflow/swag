"""Bounded local observation polling; never an engine routine or training grant."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from swag_passive_capture import DEFAULT_SCHEMA, append_record, build_capture_record
from swag_routing_contract import digest, strict_json
from swag_training_pipeline import _redact_text

MAX_DIFF_BYTES = 16 * 1024 * 1024
MAX_CONTEXT_BYTES = 64 * 1024
NULL_ROUTE = dict.fromkeys(('provider', 'modelId', 'effort', 'accessMode', 'bindingId'))


def git_bytes(repo: Path, *args: str, limit: int = MAX_DIFF_BYTES) -> bytes:
    """Bound output memory and wall time; never print project command output."""
    process = subprocess.Popen(
        ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=',
         '-C', str(repo), '--no-pager', *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    chunks: list[bytes] = []
    assert process.stdout is not None
    reader = threading.Thread(target=lambda: chunks.append(process.stdout.read(limit + 1)), daemon=True)
    try:
        reader.start()
        reader.join(20)
        if reader.is_alive():
            raise ValueError('Git observation timed out')
        data = chunks[0]
        if len(data) > limit:
            raise ValueError('Git observation exceeded byte limit')
        if process.wait(timeout=2):
            raise ValueError('Git observation failed; repository must have a commit')
        return data
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        reader.join(5)
        process.stdout.close()


def read_context(path: Path) -> tuple[dict, str]:
    with path.open('rb') as stream:
        raw = stream.read(MAX_CONTEXT_BYTES + 1)
    if len(raw) > MAX_CONTEXT_BYTES:
        raise ValueError('Task context exceeded byte limit')
    context = strict_json(raw)
    schema = strict_json(DEFAULT_SCHEMA.with_name('capture_watch_input.schema.json').read_bytes())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(context)
    return context, hashlib.sha256(raw).hexdigest()


def observe(repo: Path, context_path: Path) -> tuple[dict, dict, list[str]]:
    context, context_sha = read_context(context_path)
    head = git_bytes(repo, 'rev-parse', '--verify', 'HEAD', limit=256).decode().strip()
    branch = git_bytes(repo, 'rev-parse', '--abbrev-ref', 'HEAD', limit=4096).decode().strip()
    status = git_bytes(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=no', limit=1024 * 1024)
    staged = git_bytes(repo, 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', 'HEAD', '--')
    unstaged = git_bytes(repo, 'diff', '--binary', '--no-ext-diff', '--no-textconv', '--')
    paths = []
    entries = iter(status.decode('utf-8', errors='strict').split('\0'))
    for entry in entries:
        if entry:
            paths.append(entry[3:])
            if 'R' in entry[:2] or 'C' in entry[:2]:
                paths.append(next(entries))
    if len(paths) > 1000:
        raise ValueError('Changed path count exceeds 1000')
    source = {'scope': 'tracked_files_only', 'head': head, 'branch': redact(branch),
              'branch_sha256': hashlib.sha256(branch.encode()).hexdigest(),
              'status_sha256': hashlib.sha256(status).hexdigest(),
              'staged_diff_sha256': hashlib.sha256(staged).hexdigest(),
              'unstaged_diff_sha256': hashlib.sha256(unstaged).hexdigest(),
              'context_sha256': context_sha}
    return context, source, paths


def redact(text: str) -> str:
    return _redact_text(text, '<REDACTED>', False)[0]


def capture_once(repo: Path, context_path: Path, output: Path) -> bool:
    repo, context_path, output = repo.resolve(), context_path.resolve(), output.resolve()
    top_level = Path(git_bytes(repo, 'rev-parse', '--show-toplevel', limit=16384).decode().strip()).resolve()
    if top_level != repo:
        raise ValueError('Select the explicit Git repository root, not a subdirectory')
    if output.is_relative_to(repo):
        raise ValueError('Output must be outside the watched repository to prevent feedback')
    first = observe(repo, context_path)
    second = observe(repo, context_path)
    if first != second:
        raise ValueError('Inputs changed during observation; retry on the next poll')
    context, source, paths = second
    route = context.get('route', NULL_ROUTE)
    if any(isinstance(value, str) and redact(value) != value for value in route.values()):
        raise ValueError('Route identity contains sensitive-pattern text; do not alter it silently')
    record = build_capture_record(
        project_root=repo, task_type='routing observation',
        issue_title=redact(context['issueTitle']), issue_id=redact(context.get('issueId', '')),
        intent_text=redact(context.get('intentText', context['issueTitle'])),
        selected_question_ids=[], route_target_tier=None, stack=[], domain='',
        changed_files=[redact(path) for path in paths],
        user_override=context.get('userOverride'), user_acceptance=None, confidence=None,
        rationale='Observed local changes; technical outcome and preferred route remain unverified.',
        outcome=None, source_url=None, reviewer='unreviewed-local-observation', route=route)
    record['repo_context']['branch'] = redact(source['branch'])
    source['stream_id'] = digest([str(repo), str(context_path), 'tracked_files_only'])
    source['snapshot_sha256'] = digest(source)
    source['previous_record_id'] = None
    record['source_snapshot'] = source
    record['source_provenance']['source_type'] = 'bounded_local_git_and_task_watch'
    record['source_provenance']['notes'] = (
        'Two equal sequential observations, not an atomic Git snapshot or engine read stamp. '
        'No raw diff retained; untracked files and remote issue polling excluded. '
        'Pattern redaction is best effort; hashes are identities, not anonymization.')
    Draft202012Validator(strict_json(DEFAULT_SCHEMA.read_bytes()), format_checker=FormatChecker()).validate(record)
    return append_record(output, record, snapshot_dedup=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--context', type=Path, required=True, help='Explicit local issue/title/route JSON input')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval-seconds', type=float, default=5)
    parser.add_argument('--duration-seconds', type=float, default=300)
    parser.add_argument('--max-records', type=int, default=100)
    args = parser.parse_args()
    if (not math.isfinite(args.interval_seconds) or not .25 <= args.interval_seconds <= 3600
            or not math.isfinite(args.duration_seconds) or not 1 <= args.duration_seconds <= 86400
            or not 1 <= args.max_records <= 10000):
        parser.error('Require interval .25..3600 seconds, duration 1..86400 seconds and 1..10000 records')
    deadline, written, failed = time.monotonic() + args.duration_seconds, 0, False
    while time.monotonic() < deadline and written < args.max_records:
        try:
            changed = capture_once(args.repo, args.context, args.output)
            written += int(changed)
            failed = False
            if changed or args.once:
                print(json.dumps({'state': 'captured' if changed else 'unchanged', 'recordsWritten': written}), flush=True)
        except (OSError, ValueError, ValidationError, subprocess.TimeoutExpired) as error:
            # Errors may embed issue text or paths. Log only the class, never its payload.
            if not failed or args.once:
                print(json.dumps({'state': 'observation_deferred', 'errorClass': type(error).__name__}), flush=True)
            failed = True
        if args.once:
            return int(failed)
        time.sleep(max(0, min(args.interval_seconds, deadline - time.monotonic())))
    print(json.dumps({'state': 'stopped', 'recordsWritten': written, 'trainingAuthorized': False}), flush=True)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
