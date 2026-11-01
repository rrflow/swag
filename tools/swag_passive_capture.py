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
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = ROOT / "config" / "training" / "passive_capture.schema.json"
DEFAULT_OUTPUT = ROOT / ".swag" / "capture" / "observations.jsonl"


def append_record(path: Path, record: dict[str, Any], *, snapshot_dedup: bool = False) -> bool:
    """Serialize local writers; never truncate observations or repair tails silently."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    handle = lock.open("xb")
    try:
        with handle:
            if path.exists() and path.stat().st_size:
                with path.open("rb") as stream:
                    stream.seek(-1, os.SEEK_END)
                    if stream.read(1) != b"\n":
                        raise ValueError("Incomplete JSONL tail; preserve and reconcile it before appending")
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
            if snapshot_dedup and (path.stat().st_size if path.exists() else 0) + len(encoded) > 64 * 1024 * 1024:
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="JSON Schema enforced before appending.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
