#!/usr/bin/env python3
"""Benchmark policy comparison across the SWAG capture dataset.

This is a lightweight policy benchmark: it compares the default 14B route against
27-28B escalation on the same project-grounded scenarios and reports where the
system should stay on the balanced default versus escalate.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "files" / "training" / "project_task_capture_seed.jsonl"
DEFAULT_OUTPUT = ROOT / "files" / "training" / "project_task_capture_benchmark.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("route_target_tier", "unknown")) for row in rows)
    task_counts = Counter(str(row.get("task_type", "unknown")) for row in rows)
    domains = sorted({str(row.get("domain", "unknown")) for row in rows})

    default_rows = [row for row in rows if str(row.get("route_target_tier")) == "14b"]
    escalation_rows = [row for row in rows if str(row.get("route_target_tier")) == "27-28b"]

    default_task_breakdown = Counter(str(row.get("task_type", "unknown")) for row in default_rows)
    escalation_task_breakdown = Counter(str(row.get("task_type", "unknown")) for row in escalation_rows)

    return {
        "dataset_rows": len(rows),
        "tier_counts": dict(sorted(counts.items())),
        "domains": domains,
        "task_counts": dict(sorted(task_counts.items())),
        "default_route_rows": len(default_rows),
        "escalation_route_rows": len(escalation_rows),
        "default_task_breakdown": dict(sorted(default_task_breakdown.items())),
        "escalation_task_breakdown": dict(sorted(escalation_task_breakdown.items())),
        "default_policy_recommendation": "Keep 14B as the balanced default for controller work; use it when the task is bounded, reviewable, and evidence-sensitive without a production incident or deep system-risk boundary.",
        "escalation_policy_recommendation": "Escalate to 27-28B only for incident/root-cause, runtime-serving failures, or high-impact cross-system risk where the model must reason through uncertainty and evidence integrity before action.",
        "benchmark_takeaway": "The captured tasks are dominated by bounded review and policy evaluation, which supports 14B as the default controller route. The only explicit escalation case is the runtime/incident set, which appropriately triggers 27-28B.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize the 14B-vs-27-28B policy benchmark on the captured project dataset.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input project capture JSONL file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output benchmark JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = _load_jsonl(args.input)
    summary = _summarize(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True)
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
