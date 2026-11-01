#!/usr/bin/env python3
"""Generate an alpha-stage comparison report for SWAG.

This report shows the live decision influence of OpenAI, Cloudflare, JEV, RRFlow,
and SWEBOK while also summarizing the current 7B/14B/27-28B optimization signals.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc

ROOT = Path(__file__).resolve().parent.parent


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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return data


def _normalize_tier_metrics(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tiers = raw.get("tiers", {}) if isinstance(raw, dict) else {}
    out: dict[str, dict[str, Any]] = {}
    for tier, values in tiers.items():
        if not isinstance(values, dict):
            continue
        out[str(tier)] = {
            "train_loss": float(values.get("train_loss", 0.0) or 0.0),
            "mean_token_accuracy": float(values.get("mean_token_accuracy", 0.0) or 0.0),
            "runtime_seconds": float(values.get("runtime_seconds", 0.0) or 0.0),
        }
    return out


def _build_vendor_analysis(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in manifest.get("sources", []):
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", ""))
        family = str(entry.get("family", "unknown"))
        status = str(entry.get("status", "active"))
        summary = str(entry.get("summary", ""))
        if key in {"swebok_core", "openai_reasoning", "openai_structured_outputs", "cloudflare_workers_ai", "cloudflare_durable_objects", "cloudflare_queues", "cloudflare_vectorize", "typesafe_jev", "rrflow_core"}:
            rows.append(
                {
                    "source_key": key,
                    "family": family,
                    "status": status,
                    "name": entry.get("official_name"),
                    "question_bindings": entry.get("question_bindings", []),
                    "why_it_matters": summary,
                    "recommended_use": {
                        "swebok_core": "Shared foundation for software-engineering decision coverage",
                        "openai_reasoning": "AI reasoning and security-sensitive decision quality",
                        "openai_structured_outputs": "Schema-enforced outputs and structured decision contracts",
                        "cloudflare_workers_ai": "Edge runtime and low-latency AI deployment decisions",
                        "cloudflare_durable_objects": "Stateful runtime architecture and durability decisions",
                        "cloudflare_queues": "Background work and delivery reliability",
                        "cloudflare_vectorize": "Retrieval and semantic search memory patterns",
                        "typesafe_jev": "Experimental architecture/process decision framing; not default truth source",
                        "rrflow_core": "Your own project contract, routing, and operational constraints",
                    }.get(key, "Decision support input"),
                }
            )
    return rows


def _build_tier_analysis(metrics: dict[str, dict[str, Any]], tier_policy: dict[str, Any]) -> dict[str, Any]:
    policy = tier_policy.get("policy", {}) if isinstance(tier_policy, dict) else {}
    strategy = policy.get("controller_tier_strategy", {}) if isinstance(policy, dict) else {}
    fallback_order = policy.get("fallback_order", {}) if isinstance(policy, dict) else {}
    rows: list[dict[str, Any]] = []
    for tier in ["7b", "14b", "27-28b"]:
        values = metrics.get(tier, {})
        rows.append(
            {
                "tier": tier,
                "mean_token_accuracy": values.get("mean_token_accuracy", 0.0),
                "train_loss": values.get("train_loss", 0.0),
                "runtime_seconds": values.get("runtime_seconds", 0.0),
                "default_policy_role": {
                    "7b": "low-cost fallback",
                    "14b": "balanced default",
                    "27-28b": "deep reasoning escalation",
                }[tier],
                "fallback_order": fallback_order.get(tier, []),
            }
        )
    return {
        "default_tier": strategy.get("default_tier", "14b"),
        "fallback_tier": strategy.get("fallback_tier", "7b"),
        "escalation_tier": strategy.get("escalation_tier", "27-28b"),
        "rows": rows,
    }


def build_report() -> dict[str, Any]:
    manifest = _load_yaml(ROOT / "config" / "sources" / "official_source_canon.yaml")
    tier_policy = _load_yaml(ROOT / "config" / "boundaries" / "system_one_tier_policy.yaml")
    metrics = _load_json(ROOT / "files" / "controller_experiments" / "tier_metrics.spark_latest.json")
    vendor_rows = _build_vendor_analysis(manifest)
    tier_rows = _build_tier_analysis(_normalize_tier_metrics(metrics), tier_policy)

    # Build a simple optimization view aligned to the current alpha metrics file.
    best_accuracy = max(row["mean_token_accuracy"] for row in tier_rows["rows"])
    lowest_runtime = min(row["runtime_seconds"] for row in tier_rows["rows"])
    recommendation = {
        "balanced_default": tier_rows["default_tier"],
        "low_cost_fallback": tier_rows["fallback_tier"],
        "deep_reasoning_escalation": tier_rows["escalation_tier"],
        "current_alpha_reading": {
            "highest_accuracy_tier": max(tier_rows["rows"], key=lambda x: x["mean_token_accuracy"])["tier"],
            "fastest_tier": min(tier_rows["rows"], key=lambda x: x["runtime_seconds"])["tier"],
            "quality_vs_runtime_note": (
                "7B is the lowest-latency / lowest-cost option, 14B remains the balanced default for controller work, "
                "and 27-28B remains the escalation choice for deep-security and architecture-heavy decisions."
            ),
        },
        "alpha_summary": (
            "The controller remains evidence-led: deploy 14B by default, 7B as a constrained fallback, and 27-28B as a deep reasoning escalation. "
            "OpenAI and Cloudflare provide decision-grade evidence for AI/runtime concerns; JEV informs architecture process thinking but stays experimental."
        ),
    }

    return {
        "report_name": "swag_alpha_vendor_and_tier_comparison",
        "report_scope": "alpha-stage comparison of source evidence, vendor decision families, and model-tier optimization",
        "vendor_decision_families": vendor_rows,
        "tier_policy": tier_rows,
        "optimization_summary": recommendation,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the SWAG alpha comparison report.")
    parser.add_argument("--output", type=Path, default=ROOT / "files" / "alpha_evidence" / "vendor_and_tier_comparison.json", help="Output path for the comparison report.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=True)
    print(json.dumps(report["optimization_summary"], indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
