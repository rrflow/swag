#!/usr/bin/env python3
"""Convert a user seed JSONL file into a supervised SWAG training dataset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "files" / "training" / "starter_seed_examples.jsonl"
DEFAULT_OUTPUT = ROOT / "files" / "training" / "starter_supervised_dataset.jsonl"
DEFAULT_REPORT = ROOT / "files" / "training" / "starter_seed_validation.json"

REQUIRED_FIELDS = {
    "record_id",
    "scenario_id",
    "task_type",
    "stack",
    "domain",
    "project_name",
    "repo_context",
    "intent_text",
    "selected_question_ids",
    "route_target_tier",
    "confidence",
    "rationale",
    "source_provenance",
}
ROUTE_TIERS = {"7b", "14b", "27-28b"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    valid = 0
    for idx, row in enumerate(rows, start=1):
        missing = sorted(REQUIRED_FIELDS - set(row.keys()))
        if missing:
            failures.append(f"row {idx}: missing fields {missing}")
            continue
        if not isinstance(row["selected_question_ids"], list) or not row["selected_question_ids"]:
            failures.append(f"row {idx}: selected_question_ids must be a non-empty list")
            continue
        tier = str(row["route_target_tier"])
        if tier not in ROUTE_TIERS:
            failures.append(f"row {idx}: invalid route_target_tier {tier!r}")
            continue
        conf = row["confidence"]
        try:
            conf_f = float(conf)
        except (TypeError, ValueError):
            failures.append(f"row {idx}: confidence must be numeric")
            continue
        if conf_f < 0.0 or conf_f > 1.0:
            failures.append(f"row {idx}: confidence out of range [0,1]")
            continue
        if not str(row["rationale"]).strip():
            failures.append(f"row {idx}: rationale is empty")
            continue
        valid += 1

    return {
        "total_rows": len(rows),
        "valid_rows": valid,
        "invalid_rows": len(rows) - valid,
        "failures": failures,
    }


def _to_supervised_record(row: dict[str, Any]) -> dict[str, Any]:
    user_payload = {
        "scenario_id": row["scenario_id"],
        "task_type": row["task_type"],
        "stack": row["stack"],
        "domain": row["domain"],
        "project_name": row["project_name"],
        "repo_context": row["repo_context"],
        "intent_text": row["intent_text"],
        "required_output": {
            "selected_question_ids": ["..."],
            "route_target_tier": "7b|14b|27-28b",
            "confidence": 0.0,
            "rationale": "short rationale",
        },
    }
    assistant_payload = {
        "selected_question_ids": row["selected_question_ids"],
        "route_target_tier": row["route_target_tier"],
        "confidence": float(row["confidence"]),
        "rationale": row["rationale"],
    }
    return {
        "record_id": f"sup-{row['record_id']}",
        "scenario_id": row["scenario_id"],
        "source_type": "user_seed",
        "messages": [
            {
                "role": "system",
                "content": "You are SWAG System-One controller. Choose the minimal required boundary questions and route target tier. Return JSON only.",
            },
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
            {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
        ],
        "labels": {
            "selected_question_ids": row["selected_question_ids"],
            "route_target_tier": row["route_target_tier"],
            "confidence": float(row["confidence"]),
            "rationale": row["rationale"],
        },
        "metadata": {
            "task_type": row["task_type"],
            "stack": row["stack"],
            "domain": row["domain"],
            "project_name": row["project_name"],
            "source_type": row["source_provenance"].get("source_type", "starter_example"),
            "reviewer": row["source_provenance"].get("reviewer", "starter_pack"),
        },
    }


def build_supervised_dataset(input_path: Path, output_path: Path) -> dict[str, Any]:
    rows = _load_jsonl(input_path)
    validation = _validate_rows(rows)
    if validation["invalid_rows"] > 0:
        raise SystemExit(f"Seed validation failed with {validation['invalid_rows']} invalid rows. {validation['failures'][:5]}")

    supervised = [_to_supervised_record(row) for row in rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for rec in supervised:
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

    return {
        "input_rows": len(rows),
        "output_rows": len(supervised),
        "validation": validation,
        "output_path": str(output_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a starter or user seed file and convert it into a supervised dataset.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL file containing user seed examples.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL supervised dataset.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Validation report JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = _load_jsonl(args.input)
    validation = _validate_rows(rows)
    report = {
        "input_path": str(args.input),
        "validation": validation,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=True)

    if validation["invalid_rows"] > 0:
        raise SystemExit(f"Seed validation failed with {validation['invalid_rows']} invalid rows.")

    dataset = build_supervised_dataset(args.input, args.output)
    print(json.dumps(dataset, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
