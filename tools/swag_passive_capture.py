#!/usr/bin/env python3
"""Passive capture collector for SWAG controller training.

Emits explicit observations from caller-supplied decisions and Git status.
This is not an automatic watcher. Observations require review and training consent
before dataset admission; user acceptance is not proof of technical correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = ROOT / "config" / "training" / "passive_capture.schema.json"
DEFAULT_OUTPUT = ROOT / ".swag" / "capture" / "observations.jsonl"
NATIVE_ARTIFACT_LIMIT = 4 * 1024 * 1024
NATIVE_MANIFEST_LIMIT = 16 * 1024


def _reject_path_links(path: Path, *, allow_missing: bool = False) -> None:
    path = path.absolute()
    for component in (*reversed(path.parents), path):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Evidence links and reparse points are unsupported')


def _native_output_paths(path: Path, protected: tuple[Path, ...] = ()) -> None:
    """Preflight a dedicated destination; this is not filesystem-wide isolation."""
    for candidate in (path, path.with_name(path.name + '.lock')):
        _reject_path_links(candidate, allow_missing=True)
        if candidate.exists() and not candidate.is_file():
            raise ValueError('Native destination must be a regular file')
        for source in protected:
            if candidate.resolve() == source.resolve() or (
                    candidate.exists() and source.exists() and candidate.samefile(source)):
                raise ValueError('Native destination aliases protected evidence')


def _bounded_local_bytes(path: Path, limit: int) -> bytes:
    """Reject links and non-files before reading; never follow an evidence redirect."""
    _reject_path_links(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError('Evidence must be a bounded regular file')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened):
            raise ValueError('Evidence changed during open')
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (len(data) > limit or opened.st_size != len(data)
            or opened.st_size != after.st_size or opened.st_mtime_ns != after.st_mtime_ns):
        raise ValueError('Evidence changed or exceeded its bound')
    return data


def _native_json(data: bytes) -> dict[str, Any]:
    from swag_routing_contract import strict_json, canonical_bytes
    value = strict_json(data)
    canonical_bytes(value)  # Also reject numeric overflow, such as 1e999.
    if not isinstance(value, dict):
        raise ValueError('Expected evidence object')
    return value


def _native_equal(left: Any, right: Any) -> None:
    from swag_routing_contract import canonical_bytes
    if type(left) is not type(right) or canonical_bytes(left) != canonical_bytes(right):
        raise ValueError('Native evidence identity mismatch')


def _native_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError('Expected native text')
    return value


def _native_payload(data: bytes) -> dict[str, Any]:
    envelope = _native_json(data)
    _native_equal(envelope['protocol'], 'rrd')
    _native_equal(envelope['protocol_version'], 1)
    _native_equal(envelope['outcome']['status'], 'ok')
    payload = envelope['outcome']['payload']
    if not isinstance(payload, dict):
        raise ValueError('Expected successful native payload')
    return payload


def import_native_attempt(manifest_path: Path, evidence_root: Path,
                          *, output: Path | None = None) -> dict[str, Any]:
    """Import one retained v1 source-bound worker, without labels or live calls.

    Artifact/content hashes are verified here. Native task/outcome digests remain
    engine-reported identities: Python's serializer is not Rust's typed serializer.
    """
    from swag_routing_contract import digest, validate
    manifest = _native_json(_bounded_local_bytes(manifest_path, NATIVE_MANIFEST_LIMIT))
    if set(manifest) != {'schema_version', 'artifacts'}:
        raise ValueError('Unsupported manifest fields')
    _native_equal(manifest['schema_version'], 1)
    refs = manifest['artifacts']
    required = {'task', 'worker', 'selector', 'source', 'budget'}
    optional = {'prior_review', 'prepared_delivery', 'receiver_readback'}
    if not isinstance(refs, dict) or not required <= refs.keys() or refs.keys() - required - optional:
        raise ValueError('Unsupported artifact roles')
    if ('prepared_delivery' in refs) != ('receiver_readback' in refs):
        raise ValueError('Delivery and receiver evidence must be paired')
    root = evidence_root.absolute()
    artifacts: dict[str, bytes] = {}
    hashes: dict[str, str] = {}
    protected = [manifest_path]
    for role, ref in refs.items():
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            raise ValueError('Unsupported artifact reference')
        relative = ref['path']
        if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative
                or relative.startswith('/') or any(p in ('', '.', '..') for p in relative.split('/'))):
            raise ValueError('Evidence requires a bounded relative path')
        if not isinstance(ref['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256']):
            raise ValueError('Invalid artifact digest')
        path = root.joinpath(*relative.split('/'))
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Evidence path escapes root')
        raw = _bounded_local_bytes(path, NATIVE_ARTIFACT_LIMIT)
        actual = hashlib.sha256(raw).hexdigest()
        _native_equal(actual, ref['sha256'])
        artifacts[role], hashes[role] = raw, actual
        protected.append(path)
    if output is not None:
        _native_output_paths(output, tuple(protected))

    task = _native_payload(artifacts['task'])['task']
    budget = _native_payload(artifacts['budget'])['budget']
    worker_attempt = _native_payload(artifacts['worker'])['attempt']
    selector_attempt = _native_payload(artifacts['selector'])['attempt']
    worker = worker_attempt['worker_output']
    selector = selector_attempt['endpoint_proposal']
    for attempt, kind in ((worker_attempt, 'worker_output'), (selector_attempt, 'endpoint_proposal')):
        if set(attempt) != {'attempt_id', 'ordinal', 'status', 'outcome_sha256', 'result', kind}:
            raise ValueError('Unsupported attempt shape')
    for attempt, output in ((worker_attempt, worker), (selector_attempt, selector)):
        _native_equal(attempt['status'], 'accepted')
        _native_equal(attempt['result'], None)
        _native_equal(output['contract_version'], 1)
        _native_equal(output['attempt_id'], attempt['attempt_id'])
        _native_equal(output['scope'], task['scope'])
        _native_equal(output['task_id'], task['task_id'])
    _native_equal(task['format_version'], 1)
    _native_equal(budget['format_version'], 1)
    _native_equal(budget['task_id'], task['task_id'])
    _native_equal(budget['scope'], task['scope'])
    _native_equal(budget['scope'], 'instance:' + budget['instance_id'])
    _native_equal(selector['purpose'], 'experimental_proposal')
    _native_equal(selector['choice']['kind'], 'select')
    _native_equal(selector['choice']['binding_id'], worker['binding_id'])
    _native_equal(worker['selection_attempt_id'], selector_attempt['attempt_id'])
    _native_equal(worker['selection_sha256'], selector_attempt['outcome_sha256'])
    _native_equal(worker['task_sha256'], selector['task_sha256'])
    _native_equal(worker['configuration_sha256'], selector['configuration_sha256'])
    if (type(selector_attempt['ordinal']) is not int or type(worker_attempt['ordinal']) is not int
            or not 0 < selector_attempt['ordinal'] < worker_attempt['ordinal']):
        raise ValueError('Selection must precede its worker')
    # This first importer deliberately covers the source-only native contract.
    _native_equal(worker['context'], None)
    source = worker['source']
    _native_equal(source['contract_version'], 1)
    _native_equal(source['content_sha256'], hashes['source'])
    content_hash = hashlib.sha256(_native_text(worker['content']).encode('utf-8')).hexdigest()
    _native_equal(worker['content_sha256'], content_hash)
    goal_hash = hashlib.sha256(_native_text(task['goal']).encode('utf-8')).hexdigest()
    identity = {key: budget[key] for key in ('instance_id', 'scope', 'task_id')}
    identity['attempt_id'] = worker_attempt['attempt_id']

    def attempt_metadata(attempt: dict, output: dict, binding: str) -> dict:
        keys = ('attempt_id', 'task_sha256', 'configuration_sha256', 'packet_sha256',
                'request_sha256', 'response_sha256', 'content_sha256', 'service_id',
                'usage', 'elapsed_ms', 'http_status')
        return {**{key: output[key] for key in keys}, 'binding_id': output[binding],
                'ordinal': attempt['ordinal'], 'status': attempt['status'],
                'outcome_sha256': attempt['outcome_sha256']}

    native = {
        'contract_version': 1, 'identity': identity, 'identity_sha256': digest(identity),
        'digest_semantics': 'engine_reported_typed_digests_with_verified_artifact_and_content_bytes',
        'task_goal_sha256': goal_hash,
        'selector': attempt_metadata(selector_attempt, selector, 'controller_binding_id'),
        'worker': attempt_metadata(worker_attempt, worker, 'binding_id'),
        'selected_effort': selector['choice']['effort'],
        'model_revision': None, 'loaded_weights_attestation': None,
        'source': source, 'source_bytes': len(artifacts['source']), 'worker_read': worker['read'],
        'evidence_sha256': hashes, 'prior_review': None, 'delivery': None,
    }
    if 'prior_review' in artifacts:
        review = _native_json(artifacts['prior_review'])
        _native_equal(review['schema'], 'clyffy.private-draft-review.v1')
        expected = {'task_response_sha256': hashes['task'], 'task_goal_utf8_sha256': goal_hash,
                    'source_file_sha256': hashes['source'], 'source_file_bytes': len(artifacts['source']),
                    'worker_attempt_response_sha256': hashes['worker'],
                    'worker_content_utf8_sha256': content_hash, 'worker_reported_content_sha256': content_hash,
                    'worker_reported_source_sha256': hashes['source'], 'attempt_status': 'accepted'}
        _native_equal(review['identity'], expected)
        native['prior_review'] = {'artifact_sha256': hashes['prior_review'],
                                  'relationship': 'prior_observation_only_not_capture_review',
                                  'reviewed_at': review['reviewed_utc']}
    if 'prepared_delivery' in artifacts:
        prepared = _native_json(artifacts['prepared_delivery'])
        receiver = _native_json(artifacts['receiver_readback'])
        _native_equal(prepared['contract_version'], 1)
        _native_equal(prepared['scope'], identity['scope'])
        _native_equal(prepared['source'], {
            'kind': 'task_attempt',
            'request': {key: identity[key] for key in ('scope', 'task_id', 'attempt_id')},
            'expected_status': 'accepted', 'expected_outcome_sha256': worker_attempt['outcome_sha256']})
        events = receiver['events']
        if not isinstance(events, list):
            raise ValueError('Expected receiver event list')
        matching = [event for event in events if isinstance(event, dict)
                    and event.get('event_id') == prepared['event_id']]
        if len(matching) != 1:
            raise ValueError('Expected exactly one matching received event')
        event = matching[0]
        _native_equal(event['schema'], 'rroflow.capture/v1')
        _native_equal(event['agent'], 'rrflow')
        _native_equal(event['kind'], 'engine.observed')
        _native_equal(event['operation_id'], prepared['delivery_id'])
        engine = event['engine']
        for key, value in identity.items():
            _native_equal(engine[key], value)
        _native_equal(engine['version'], 1)
        _native_equal(engine['operation'], 'task-attempt-read')
        _native_equal(engine['configuration_sha256'], worker['configuration_sha256'])
        _native_equal(engine['response_sha256'], prepared['source_response_sha256'])
        # Receiver source identity is not reconstructed from protected local evidence.
        _native_equal(engine['source_sha256'], None)
        native['delivery'] = {
            'delivery_id': prepared['delivery_id'], 'event_id': prepared['event_id'],
            'source_response_sha256': prepared['source_response_sha256'],
            'payload_sha256': prepared['payload_sha256'],
            'configuration_sha256': prepared['configuration_sha256'],
            'receiver_source_sha256': None,
            'observation': 'matching_event_in_retained_receiver_readback',
        }
    record = {
        'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
        'label_status': 'unreviewed', 'training_consent': False,
        'record_id': 'passive-' + native['identity_sha256'][:12],
        'project_id': source['project_id'],
        'task_id': 'task-' + digest({key: identity[key] for key in ('instance_id', 'scope', 'task_id')})[:12],
        'source_type': 'passive_capture', 'task_type': '', 'stack': [], 'domain': '',
        'issue_title': '', 'issue_id': '', 'intent_text': '', 'selected_question_ids': [],
        'repo_context': {'branch': '', 'repo_root': '', 'changed_files': None},
        'route': {'provider': None, 'modelId': None, 'effort': selector['choice']['effort'],
                  'accessMode': None, 'bindingId': worker['binding_id']},
        'route_target_tier': None, 'user_override': None, 'user_acceptance': None,
        'confidence': None, 'rationale': '',
        'outcome': {'tests_passed': None, 'rollback': None, 'incident': None},
        'source_provenance': {'source_type': 'retained_native_attempt', 'source_url': '', 'reviewer': '',
            'notes': 'Offline metadata import; prior observations are not labels, consent or origin attestation.'},
        'native_attempt': native,
    }
    validate(record, 'passive_capture.schema.json')
    return record


def append_record(path: Path, record: dict[str, Any], *, snapshot_dedup: bool = False,
                  native_dedup: bool = False) -> bool:
    """Serialize local writers; never truncate observations or repair tails silently."""
    if native_dedup:
        _native_output_paths(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    handle = lock.open("xb")
    try:
        with handle:
            if native_dedup:
                _native_output_paths(path)
            if path.exists() and path.stat().st_size:
                with path.open("rb") as stream:
                    stream.seek(-1, os.SEEK_END)
                    if stream.read(1) != b"\n":
                        raise ValueError("Incomplete JSONL tail; preserve and reconcile it before appending")
            if native_dedup:
                from swag_routing_contract import canonical_bytes, digest, strict_json, validate
                validate(record, 'passive_capture.schema.json')
                _native_equal(record['native_attempt']['identity_sha256'],
                              digest(record['native_attempt']['identity']))
                if snapshot_dedup:
                    raise ValueError('Capture modes are mutually exclusive')
                if path.exists() and path.stat().st_size > 64 * 1024 * 1024:
                    raise ValueError('Capture log exceeds 64 MiB')
                replay = False
                seen_native: set[bytes] = set()
                if path.exists():
                    with path.open('rb') as existing:
                        for line in existing:
                            prior = strict_json(line)
                            validate(prior, 'passive_capture.schema.json')
                            native = prior.get('native_attempt')
                            if not native:
                                raise ValueError('Native import requires a dedicated capture destination')
                            _native_equal(native['identity_sha256'], digest(native['identity']))
                            native_key = canonical_bytes(native['identity'])
                            if native_key in seen_native:
                                raise ValueError('Duplicate native attempt in retained capture; preserve and reconcile')
                            seen_native.add(native_key)
                            if native and native['identity'] == record['native_attempt']['identity']:
                                if (canonical_bytes({key: value for key, value in prior.items() if key != 'captured_at'})
                                        != canonical_bytes({key: value for key, value in record.items() if key != 'captured_at'})):
                                    raise ValueError('Native attempt conflict or new supplement; preserve original capture')
                                replay = True
                if replay:
                    return False
            if snapshot_dedup:
                from swag_routing_contract import strict_json
                if path.exists() and path.stat().st_size > 64 * 1024 * 1024:
                    raise ValueError("Capture log exceeds 64 MiB; select a new retained output")
                previous = None
                if path.exists():
                    with path.open('rb') as existing:
                        for line in existing:
                            prior = strict_json(line)
                            if not isinstance(prior, dict) or not isinstance(prior.get('source_snapshot', {}), dict):
                                raise ValueError('Invalid retained observation; preserve before reconciliation')
                            source = prior.get('source_snapshot', {})
                            if source.get('stream_id') == record['source_snapshot']['stream_id']:
                                previous = prior
                source = record['source_snapshot']
                if previous and previous['source_snapshot']['snapshot_sha256'] == source['snapshot_sha256']:
                    return False
                source['previous_record_id'] = previous['record_id'] if previous else None
                record['record_id'] = 'passive-' + hashlib.sha256(
                    (source['stream_id'] + source['snapshot_sha256'] + (source['previous_record_id'] or '')).encode()
                ).hexdigest()[:12]
                Draft202012Validator(json.loads(DEFAULT_SCHEMA.read_text(encoding='utf-8')),
                                     format_checker=FormatChecker()).validate(record)
            encoded = (json.dumps(record, ensure_ascii=True, allow_nan=False) + "\n").encode()
            if (snapshot_dedup or native_dedup) and (path.stat().st_size if path.exists() else 0) + len(encoded) > 64 * 1024 * 1024:
                raise ValueError("Capture log would exceed 64 MiB")
            with path.open("ab") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
    finally:
        lock.unlink()
    return True


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _repo_name(project_root: Path) -> str:
    name = project_root.name.strip()
    if name:
        return name
    return "swag-project"


def _collect_changed_files(project_root: Path, changed_files_arg: str | None) -> list[str] | None:
    if changed_files_arg:
        return [p.strip() for p in changed_files_arg.split(",") if p.strip()]
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "status", "--porcelain=v1", "-z"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    out: list[str] = []
    entries = iter(completed.stdout.split('\0'))
    for entry in entries:
        if not entry:
            continue
        out.append(entry[3:])
        if 'R' in entry[:2] or 'C' in entry[:2]:
            previous = next(entries, '')
            if previous:
                out.append(previous)
    return out


def _task_id(project_id: str, issue_id: str | None, intent_text: str) -> str:
    seed = "|".join([project_id, issue_id or "", intent_text.strip()][:3])
    return "task-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def build_capture_record(
    *,
    project_root: Path,
    task_type: str,
    issue_title: str,
    issue_id: str | None,
    intent_text: str,
    selected_question_ids: list[str],
    route_target_tier: str | None,
    stack: list[str],
    domain: str,
    changed_files: list[str] | None,
    user_override: bool | None,
    user_acceptance: bool | None,
    confidence: float | None,
    rationale: str,
    outcome: dict[str, Any] | None,
    source_url: str | None,
    reviewer: str,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if confidence is not None and (not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise ValueError("confidence must be null or a finite value from 0 to 1")
    project_id = _repo_name(project_root)
    record_id = "passive-" + hashlib.sha256(
        (
            project_id
            + "|"
            + (issue_id or issue_title or intent_text)
            + "|"
            + datetime.now(timezone.utc).isoformat()
        ).encode("utf-8")
    ).hexdigest()[:12]
    task_id = _task_id(project_id, issue_id, intent_text)
    payload = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "label_status": "unreviewed",
        "training_consent": False,
        "route": route or {"provider":None, "modelId":None, "effort":None,
                           "accessMode":None, "bindingId":None},
        "record_id": record_id,
        "project_id": project_id,
        "task_id": task_id,
        "source_type": "passive_capture",
        "task_type": task_type,
        "stack": stack,
        "domain": domain,
        "issue_title": issue_title,
        "issue_id": issue_id or "",
        "repo_context": {
            "branch": os.environ.get("GIT_BRANCH", ""),
            "repo_root": str(project_root.resolve()),
            "changed_files": changed_files,
        },
        "intent_text": intent_text,
        "selected_question_ids": selected_question_ids,
        "route_target_tier": route_target_tier,
        "user_override": user_override,
        "user_acceptance": user_acceptance,
        "confidence": confidence,
        "rationale": rationale,
        "outcome": {
            "tests_passed": (outcome or {}).get("tests_passed"),
            "rollback": (outcome or {}).get("rollback"),
            "incident": (outcome or {}).get("incident"),
        },
        "source_provenance": {
            "source_type": "explicit_input_and_git_status",
            "source_url": source_url or "",
            "reviewer": reviewer,
            "notes": "Caller-supplied observations plus changed paths; no diff content, automatic watcher, or verified label implied.",
        },
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit passive capture JSONL records for SWAG training.")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root or repo to inspect.")
    parser.add_argument("--task-type", default="routing decisions", help="Task category for this record.")
    parser.add_argument("--issue-title", default="", help="Issue title or task summary.")
    parser.add_argument("--issue-id", default="", help="Issue or PR identifier if available.")
    parser.add_argument("--intent-text", default="", help="User prompt or task summary.")
    parser.add_argument("--selected-question-ids", default="", help="Comma-separated selected_question_ids.")
    parser.add_argument("--route-target-tier", default=None, help="Optional legacy tier; omitted means unknown.")
    parser.add_argument("--route-provider", default=None)
    parser.add_argument("--route-model", default=None)
    parser.add_argument("--route-effort", default=None)
    parser.add_argument("--access-mode", choices=["subscription", "api", "local"], default=None)
    parser.add_argument("--binding-id", default=None)
    parser.add_argument("--stack", default="", help="Comma-separated stack labels, e.g. python,react.")
    parser.add_argument("--domain", default="", help="Single domain label, e.g. auth_and_session_control.")
    parser.add_argument("--changed-files", default="", help="Comma-separated changed file paths.")
    parser.add_argument("--user-override", action=argparse.BooleanOptionalAction, default=None, help="Observed override; omitted means unknown.")
    parser.add_argument("--user-acceptance", action=argparse.BooleanOptionalAction, default=None, help="Observed acceptance; not a correctness label.")
    parser.add_argument("--confidence", type=float, default=None, help="Explicit reported confidence; omitted means unknown, not calibrated.")
    parser.add_argument("--rationale", default="", help="Short rationale for the route and question selection.")
    parser.add_argument("--tests-passed", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--rollback", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--incident", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--source-url", default="", help="Origin URL or issue/PR link if available.")
    parser.add_argument("--reviewer", default="user", help="Reviewer or source of the label.")
    parser.add_argument("--output", type=Path, help="Output JSONL path; required for native import.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="JSON Schema enforced before appending.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output summary.")
    parser.add_argument('--native-manifest', type=Path, help='Explicit offline native-attempt evidence manifest.')
    parser.add_argument('--evidence-root', type=Path, help='Private root containing the selected evidence files.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.native_manifest:
        if args.evidence_root is None or args.output is None or args.schema != DEFAULT_SCHEMA:
            raise SystemExit('Native import requires --evidence-root, --output and the shipped schema')
        try:
            record = import_native_attempt(args.native_manifest, args.evidence_root, output=args.output)
            written = append_record(args.output, record, native_dedup=True)
        except (ValueError, KeyError, TypeError, OSError, ValidationError, RecursionError) as exc:
            # Paths, source text and arbitrary parser values must not reach logs.
            raise SystemExit('Native evidence import rejected; originals preserved (' + type(exc).__name__ + ')') from None
        print(json.dumps({'records_written': int(written), 'record_id': record['record_id'],
                          'label_status': 'unreviewed', 'training_consent': False},
                         indent=2 if args.pretty else None))
        return 0
    if args.evidence_root:
        raise SystemExit('--evidence-root requires --native-manifest')
    args.output = args.output or DEFAULT_OUTPUT
    project_root = args.project_root.resolve()
    selected_question_ids = [p.strip() for p in args.selected_question_ids.split(",") if p.strip()]
    stack = [s.strip() for s in args.stack.split(",") if s.strip()]
    changed_files = _collect_changed_files(project_root, args.changed_files)
    if not args.issue_title and not args.intent_text:
        raise SystemExit("At least one of --issue-title or --intent-text is required.")
    if not selected_question_ids:
        raise SystemExit("At least one selected question ID is required via --selected-question-ids.")

    record = build_capture_record(
        project_root=project_root,
        task_type=args.task_type,
        issue_title=args.issue_title or args.intent_text,
        issue_id=args.issue_id or "",
        intent_text=args.intent_text or args.issue_title,
        selected_question_ids=selected_question_ids,
        route_target_tier=args.route_target_tier,
        stack=stack or ["unknown"],
        domain=args.domain or "unassigned",
        changed_files=changed_files,
        user_override=args.user_override,
        user_acceptance=args.user_acceptance,
        confidence=args.confidence,
        rationale=args.rationale or "Captured from real project decision context and user route selection.",
        outcome={
            "tests_passed": args.tests_passed,
            "rollback": args.rollback,
            "incident": args.incident,
        },
        source_url=args.source_url or "",
        reviewer=args.reviewer,
        route={"provider":args.route_provider, "modelId":args.route_model,
               "effort":args.route_effort, "accessMode":args.access_mode,
               "bindingId":args.binding_id},
    )

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    append_record(args.output, record)

    summary = {
        "output": str(args.output),
        "records_written": 1,
        "project_id": record["project_id"],
        "task_id": record["task_id"],
        "route_target_tier": record["route_target_tier"],
        "source_schema": str(args.schema),
    }
    print(json.dumps(summary, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
