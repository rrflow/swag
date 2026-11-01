#!/usr/bin/env python3
"""Unified SWAG control-panel compiler.

This turns a single user intake into four artifacts:
1. a single project config layer
2. an executable controller decision output
3. a source provenance report
4. a concise control-panel summary

The intake is intentionally lightweight: project_name, repo, stack, intent, and
policy fields are enough to drive the controller and source provenance.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from boundary_controller import compose_battery
from swag_decision_service import DecisionService, ServiceConfig


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


def _load_any(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh) if path.suffix.lower() == ".json" else yaml.safe_load(fh)
    return payload if isinstance(payload, dict) else {}


def _normalize_intake_path(value: str | None, repo: Path) -> Path:
    if value is None or value == "":
        return repo
    raw = Path(value)
    return raw if raw.is_absolute() else (repo / raw).resolve()


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


def _match_question_pattern(question: dict[str, Any], pattern: str) -> bool:
    if not pattern:
        return False
    qid = str(question.get("id", "")).strip()
    qset = str(question.get("question_set", "")).strip()
    section = str(question.get("section", "")).strip()
    if fnmatch.fnmatch(qid, pattern):
        return True
    if fnmatch.fnmatch(f"{qset}.{section}", pattern):
        return True
    return False


def _build_project_config(intake: dict[str, Any]) -> dict[str, Any]:
    repo = _normalize_intake_path(intake.get("repo"), Path.cwd()).resolve()
    project_name = str(intake.get("project_name") or intake.get("name") or repo.name)
    return {
        "project": {
            "name": project_name,
            "repo": str(repo),
            "maturity": str(intake.get("maturity", "growing")),
            "primary_stack": intake.get("primary_stack") or None,
            "domains": _normalize_list(intake.get("domains")),
            "intent_text": str(intake.get("intent_text", "")),
            "has_test_harness": bool(intake.get("has_test_harness", True)),
            "unbounded_data_path": bool(intake.get("unbounded_data_path", False)),
            "project_mode": str(intake.get("project_mode", "isolated")),
            "parallel_rrflow": bool(intake.get("parallel_rrflow", False)),
            "shared_decision_space": bool(intake.get("shared_decision_space", True)),
        },
        "runtime": {
            "deployment_mode": str(intake.get("deployment_mode", "self_hosted")),
            "budget_mode": str(intake.get("budget_mode", "balanced")),
            "subscription_tier": str(intake.get("subscription_tier", "pro")),
            "attunement_profile": str(intake.get("attunement_profile", "default_rollout")),
            "route_profile": str(intake.get("route_profile", "default_frontier_eval")),
            "model_tier": str(intake.get("model_tier", "14b")),
            "mcp_enabled": bool(intake.get("mcp_enabled", True)),
            "include_overlaps": bool(intake.get("include_overlaps", False)),
        },
        "sources": {
            "canonical_manifest": "config/sources/official_source_canon.yaml",
            "research_registry": "config/boundaries/research_sync_registry.yaml",
            "require_owner_and_version": True,
            "experimental_sources": ["typesafe_jev"],
        },
    }


def _build_provenance_report(questions: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = _load_yaml(ROOT / "config" / "sources" / "official_source_canon.yaml")
    registry = _load_yaml(ROOT / "config" / "boundaries" / "research_sync_registry.yaml")
    source_entries = manifest.get("sources", []) if isinstance(manifest, dict) else []
    registry_feeds = registry.get("policy", {}).get("research_feeds", []) if isinstance(registry, dict) else []

    by_key: dict[str, dict[str, Any]] = {}
    for entry in source_entries:
        if isinstance(entry, dict):
            key = str(entry.get("key") or "").strip()
            if key:
                by_key[key] = entry

    matched_by_source: dict[str, list[str]] = {}
    for question in questions:
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or "")
        if not qid:
            continue
        for key, entry in by_key.items():
            patterns = entry.get("question_bindings", [])
            matched = any(_match_question_pattern(question, str(p)) for p in patterns if isinstance(p, str))
            if matched:
                matched_by_source.setdefault(key, []).append(qid)

    provenance = []
    for key, entry in by_key.items():
        if key not in matched_by_source:
            continue
        provenance.append(
            {
                "source_key": key,
                "source_name": entry.get("official_name") or entry.get("key"),
                "family": entry.get("family"),
                "status": entry.get("status"),
                "owner": entry.get("owner"),
                "last_verified": entry.get("last_verified"),
                "next_review_due": entry.get("next_review_due"),
                "matched_question_ids": sorted(set(matched_by_source.get(key, []))),
            }
        )

    # Include registry evidence from research_sync_registry for operator visibility.
    registry_report = []
    for feed in registry_feeds:
        if not isinstance(feed, dict):
            continue
        key = str(feed.get("key") or "").strip()
        if not key:
            continue
        registry_report.append(
            {
                "feed_key": key,
                "name": feed.get("name"),
                "version": feed.get("version"),
                "last_verified": feed.get("last_verified"),
                "next_review_due": feed.get("next_review_due"),
                "question_bindings": feed.get("question_bindings", []),
            }
        )

    return {
        "source_family_count": len(provenance),
        "matched_sources": provenance,
        "research_registry_feeds": registry_report,
    }


def _build_summary(project_config: dict[str, Any], decision: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    decision_context = decision.get("decision_context", {})
    route_profile = decision_context.get("route_profile", "default_frontier_eval")
    model_tier = decision_context.get("model_tier", "14b")
    return {
        "project_name": project_config["project"]["name"],
        "repo": project_config["project"]["repo"],
        "model_tier": model_tier,
        "route_profile": route_profile,
        "source_families_in_scope": [item["source_name"] for item in provenance.get("matched_sources", [])],
        "question_count": len(decision.get("decision", {}).get("selected_question_ids", [])),
        "status": "ready",
        "notes": (
            "Global defaults, project override, and RRFlow routing are merged into a single controller output. "
            "OpenAI / Cloudflare / JEV / SWEBOK / RRFlow evidence is attached through source provenance."
        ),
    }


def build_panel(intake: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    project_config = _build_project_config(intake)
    repo = Path(project_config["project"]["repo"]).resolve()
    decision_payload = {
        "repo": str(repo),
        "intent_text": str(project_config["project"]["intent_text"]),
        "maturity": str(project_config["project"]["maturity"]),
        "has_test_harness": bool(project_config["project"]["has_test_harness"]),
        "unbounded_data_path": bool(project_config["project"]["unbounded_data_path"]),
        "domains": project_config["project"]["domains"],
        "primary_stack": project_config["project"]["primary_stack"],
        "include_overlaps": bool(project_config["runtime"]["include_overlaps"]),
        "budget_mode": project_config["runtime"]["budget_mode"],
        "subscription_tier": project_config["runtime"]["subscription_tier"],
        "attunement_profile": project_config["runtime"]["attunement_profile"],
        "route_profile": project_config["runtime"]["route_profile"],
        "model_tier": project_config["runtime"]["model_tier"],
        "execute_frontier": False,
        "execute_local": False,
    }

    service = DecisionService(
        ServiceConfig(
            provider_config_path=ROOT / "config" / "frontier" / "providers.template.yaml",
            attunement_config_path=ROOT / "config" / "attunement" / "operator_profiles.template.yaml",
            system_one_policy_path=ROOT / "config" / "boundaries" / "system_one_controller_policy.yaml",
            system_one_tier_policy_path=ROOT / "config" / "boundaries" / "system_one_tier_policy.yaml",
            aiddevspec_config_path=ROOT / "config" / "aiddevspec" / "default.yaml",
            local_provider_config_path=ROOT / "config" / "local" / "model_adapters.template.yaml",
        )
    )
    decision = service.decide(decision_payload)
    battery = compose_battery(
        repo=repo,
        maturity=str(project_config["project"]["maturity"]),
        has_test_harness=bool(project_config["project"]["has_test_harness"]),
        unbounded_data_path=bool(project_config["project"]["unbounded_data_path"]),
        intent_text=str(project_config["project"]["intent_text"]),
        explicit_domains=project_config["project"]["domains"],
        primary_stack=project_config["project"]["primary_stack"],
        include_overlaps=bool(project_config["runtime"]["include_overlaps"]),
    )
    provenance = _build_provenance_report(battery.get("questions", []))
    summary = _build_summary(project_config, decision, provenance)

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "project_config.yaml").open("w", encoding="utf-8") as fh:
        yaml.safe_dump(project_config, fh, sort_keys=False, default_flow_style=False)
    with (output_dir / "controller_decision.json").open("w", encoding="utf-8") as fh:
        json.dump(decision, fh, indent=2, ensure_ascii=True)
    with (output_dir / "source_provenance_report.json").open("w", encoding="utf-8") as fh:
        json.dump(provenance, fh, indent=2, ensure_ascii=True)
    with (output_dir / "control_panel_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=True)

    return {
        "project_config": project_config,
        "controller_decision": decision,
        "source_provenance": provenance,
        "summary": summary,
        "artifacts": {
            "project_config": str(output_dir / "project_config.yaml"),
            "controller_decision": str(output_dir / "controller_decision.json"),
            "source_provenance": str(output_dir / "source_provenance_report.json"),
            "summary": str(output_dir / "control_panel_summary.json"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a SWAG control panel from one intake document.")
    parser.add_argument("--intake", type=Path, default=ROOT / "config" / "control_panel" / "swag_control_panel_input.example.yaml", help="YAML/JSON intake file.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "files" / "swag_control_panel", help="Directory for generated control panel artifacts.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    intake_path = args.intake.resolve()
    if not intake_path.exists():
        raise SystemExit(f"Intake file not found: {intake_path}")
    intake = _load_any(intake_path)
    if not intake:
        raise SystemExit(f"Intake file is empty or invalid: {intake_path}")
    panel = build_panel(intake, args.output_dir.resolve())
    print(json.dumps(panel["summary"], indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
