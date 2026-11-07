#!/usr/bin/env python3
"""Project onboarding and an offline preview of the SWAG system-one controller."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from swag_rroflow import preview_record, publish_record
from swag_observability import CURRENT, observed

ROOT = Path(__file__).resolve().parent.parent
PROFILE = Path(".swag/project.json")


def _write_new(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=True)
        stream.write("\n")


def load_project(repo: Path) -> dict[str, Any]:
    with (repo / PROFILE).open(encoding="utf-8") as stream:
        profile = json.load(stream)
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        raise ValueError("Expected a version 1 .swag/project.json profile.")
    if not isinstance(profile.get("project"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", profile["project"]):
        raise ValueError("Project must be a 1-64 character lowercase slug.")
    if not isinstance(profile.get("intent"), str) or not profile["intent"].strip():
        raise ValueError("Set a non-empty project intent.")
    if profile.get("maturity") not in {"greenfield", "growing", "mature"}:
        raise ValueError("Maturity must be greenfield, growing, or mature.")
    if profile.get("budget_mode") not in {"balanced", "low"}:
        raise ValueError("Budget mode must be balanced or low.")
    if not isinstance(profile.get("has_test_harness"), bool):
        raise ValueError("has_test_harness must be a boolean.")
    if not isinstance(profile.get("attunement_profile"), str) or not profile["attunement_profile"]:
        raise ValueError("Set an attunement_profile from config/attunement/operator_profiles.template.yaml.")
    return profile


def initialize(repo: Path, intent: str, project: str | None = None) -> dict[str, Any]:
    if not repo.is_dir():
        raise ValueError("Choose an existing project directory.")
    if not intent.strip():
        raise ValueError("Describe what you want to build with --intent.")
    slug = project if project is not None else re.sub(r"[^a-z0-9_-]+", "-", repo.name.lower()).strip("-_")[:64]
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", slug):
        raise ValueError("Choose --project with 1-64 lowercase letters, digits, hyphens, or underscores.")
    profile = {
        "schema_version": 1, "project": slug, "intent": intent.strip(),
        "maturity": "growing", "budget_mode": "balanced",
        "has_test_harness": False, "attunement_profile": "default_rollout",
    }
    _write_new(repo / PROFILE, profile)
    return {
        "status": "initialized", "profile": str(repo / PROFILE),
        "next": "Run doctor, then preview. Edit the profile to reflect your project.",
    }


def _service():
    from swag_decision_service import (
        DEFAULT_ATTUNEMENT_CONFIG, DEFAULT_PROVIDER_CONFIG,
        DEFAULT_SYSTEM_ONE_POLICY, DecisionService, ServiceConfig,
    )
    return DecisionService(ServiceConfig(
        provider_config_path=DEFAULT_PROVIDER_CONFIG,
        attunement_config_path=DEFAULT_ATTUNEMENT_CONFIG,
        system_one_policy_path=DEFAULT_SYSTEM_ONE_POLICY,
    ))


def _decide(repo: Path, profile: dict[str, Any], intent: str | None = None) -> dict[str, Any]:
    return _service().decide({
        "repo": str(repo), "intent_text": intent or profile["intent"],
        "maturity": profile["maturity"], "budget_mode": profile["budget_mode"],
        "has_test_harness": profile["has_test_harness"],
        "attunement_profile": profile["attunement_profile"],
        "execute_frontier": False, "execute_local": False,
    })


def doctor(repo: Path) -> dict[str, Any]:
    checks = []
    yaml_available = importlib.util.find_spec("yaml") is not None
    checks.append({"name": "yaml_dependency", "ok": yaml_available,
                   "detail": "Available" if yaml_available else "Run python -m pip install -r requirements.txt"})
    try:
        profile = load_project(repo)
        checks.append({"name": "project_profile", "ok": True, "detail": profile["project"]})
    except (OSError, ValueError) as exc:
        profile = None
        checks.append({"name": "project_profile", "ok": False, "detail": str(exc)})
    if profile and yaml_available:
        try:
            decision = _decide(repo, profile)
            checks.append({"name": "controller_preview", "ok": True,
                           "detail": f"Composed {decision['counts']['questions_total']} questions without model calls"})
        except (Exception, SystemExit) as exc:
            checks.append({"name": "controller_preview", "ok": False, "detail": str(exc)})
    return {
        "status": "ready_for_preview" if all(c["ok"] for c in checks) else "needs_setup",
        "checks": checks,
        "scope": "Local preview readiness only; model execution and remote integrations are unverified.",
        "rroflow": {
            "endpoint_configured": bool(os.environ.get("RROFLOW_INGEST_URL")),
            "credential_configured": bool(os.environ.get("RROFLOW_INGEST_KEY")),
            "connection": "not_checked",
        },
    }


@observed('swag.preview')
def preview(repo: Path, intent: str | None = None) -> dict[str, Any]:
    profile = load_project(repo)
    if intent is not None and not intent.strip():
        raise ValueError("Preview intent cannot be empty.")
    started_at = datetime.now(timezone.utc).isoformat()
    started = perf_counter()
    run_id = str(uuid4())
    try:
        decision = _decide(repo, profile, intent)
    except (Exception, SystemExit) as exc:
        record = preview_record(
            project=profile["project"], session_id=run_id, turn_key="preview",
            started_at=started_at, ended_at=datetime.now(timezone.utc).isoformat(), succeeded=False,
        )
        event_path = repo / ".swag" / "events" / f"{record['event_id']}.json"
        _write_new(event_path, record)
        raise RuntimeError(f"Controller preview failed; failure event saved at {event_path}: {exc}") from exc
    elapsed_ms = round((perf_counter() - started) * 1000, 3)
    record = preview_record(
        project=profile["project"], session_id=run_id, turn_key="preview",
        started_at=started_at, ended_at=datetime.now(timezone.utc).isoformat(), succeeded=True,
    )
    decision_path = repo / ".swag" / "decisions" / f"{run_id}.json"
    event_path = repo / ".swag" / "events" / f"{record['event_id']}.json"
    _write_new(decision_path, decision)
    _write_new(event_path, record)
    span = CURRENT.get()
    if span:
        span.set(eventId=record['event_id'], modelExecuted=False, engineIntegrated=False)
    matrix = decision["system_one_decision_matrix"]
    return {
        "status": "preview_complete", "run_id": run_id, "project": profile["project"],
        "trace_id": span.trace_id if span else None,
        "mode": "rules_only", "model_executed": False,
        "planned_model_tier": decision["decision_context"]["model_tier"],
        "tier_reason": decision["decision_context"]["model_tier_reason"],
        "counts": decision["counts"], "routing": decision["routing"],
        "main_question_band_pass": matrix["main_threshold_pass"],
        "elapsed_ms": elapsed_ms,
        "decision_file": str(decision_path), "rroflow_event_file": str(event_path),
        "uploaded": False,
        "scope": "Question selection and route preview; no project correctness or model quality verdict.",
    }


def brief(repo: Path, intent: str | None = None) -> dict[str, Any]:
    from swag_brief import decision_brief

    try:
        profile = load_project(repo)
    except FileNotFoundError:
        profile = {}
    request = intent if intent is not None else profile.get("intent")
    if not request:
        raise ValueError("Describe the request with --intent.")
    return decision_brief(repo, request, maturity=profile.get("maturity", "growing"),
                          has_test_harness=profile.get("has_test_harness", True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "doctor", "preview", "brief"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, default=Path.cwd())
        if name in {"init", "preview", "brief"}:
            command.add_argument("--intent", required=name == "init")
        if name == "init":
            command.add_argument("--project")
    publish = commands.add_parser("publish", help="Upload one saved content-free preview event to RROFLOW")
    publish.add_argument("--event", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = initialize(args.repo.resolve(), args.intent, args.project)
        elif args.command == "doctor":
            result = doctor(args.repo.resolve())
        elif args.command == "preview":
            result = preview(args.repo.resolve(), args.intent)
        elif args.command == "brief":
            result = brief(args.repo.resolve(), args.intent)
        else:
            with args.event.open(encoding="utf-8") as stream:
                record = json.load(stream)
            result = publish_record(record, os.environ.get("RROFLOW_INGEST_URL", ""),
                                    os.environ.get("RROFLOW_INGEST_KEY", ""))
        print(json.dumps(result, indent=2))
        return 1 if result.get("status") == "needs_setup" else 0
    except (Exception, SystemExit) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
