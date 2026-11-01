#!/usr/bin/env python3
"""Generate a user-authored seed dataset template for SWAG controller training."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "files" / "training" / "user_seed_dataset.jsonl"
DEFAULT_TEMPLATE = ROOT / "config" / "training" / "user_seed_dataset.template.yaml"

TASK_TYPES = [
    "routing decisions",
    "architecture review",
    "security review",
    "incident/root cause",
    "migration planning",
    "general project triage",
    "other",
]
ROUTE_TIERS = ["14b", "27-28b", "7b"]
STACKS = [
    "vanilla_js",
    "typescript",
    "react",
    "nextjs",
    "python",
    "ruby",
    "go",
    "rust",
    "java",
    "cpp",
    "c",
    "php",
    "sql",
    "other",
]


def _row(index: int, task_type: str) -> dict[str, Any]:
    return {
        "record_id": f"seed-{index:04d}",
        "scenario_id": f"user_seed_{index:04d}",
        "task_type": task_type,
        "stack": "",
        "domain": "",
        "project_name": "",
        "repo_context": "",
        "intent_text": "",
        "selected_question_ids": [],
        "route_target_tier": "",
        "confidence": None,
        "rationale": "",
        "source_provenance": {
            "source_type": "user_seed",
            "source_url": "",
            "reviewer": "",
            "notes": "",
        },
    }


def generate_seed_dataset(output_path: Path, example_count: int, task_types: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_tasks = task_types or TASK_TYPES
    for i in range(1, example_count + 1):
        task = base_tasks[(i - 1) % len(base_tasks)]
        rows.append(_row(i, task))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a user-authored seed dataset template for SWAG training.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path for the user seed dataset.")
    parser.add_argument("--count", type=int, default=50, help="Number of seed records to generate.")
    parser.add_argument(
        "--task-types",
        nargs="*",
        default=TASK_TYPES,
        help="Task categories to distribute across the seed dataset.",
    )
    args = parser.parse_args()
    rows = generate_seed_dataset(args.output, args.count, args.task_types)
    print(json.dumps({
        "output": str(args.output),
        "records_generated": len(rows),
        "task_types": list(dict.fromkeys(args.task_types)),
        "next_step": "Fill in each record with the actual task, stack, selected_question_ids, route_tier, and rationale before training.",
    }, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
