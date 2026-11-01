#!/usr/bin/env python3
"""Quality gates, dedupe, and split builder for SWAG JSONL datasets."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "training" / "dataset_quality.template.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required (pip install pyyaml).") from exc
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def _resolve_path(path_like: str) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else (ROOT / path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON at {path}:{i}: {exc}") from exc
            if not isinstance(item, dict):
                raise SystemExit(f"Expected JSON object at {path}:{i}")
            rows.append(item)
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def _find_message(messages: list[dict[str, Any]], role: str) -> str:
    for msg in messages:
        if str(msg.get("role")) == role and isinstance(msg.get("content"), str):
            return str(msg.get("content"))
    return ""


def _stable_bucket(key: str, salt: str) -> float:
    digest = hashlib.sha256((salt + "::" + key).encode("utf-8")).hexdigest()
    value = int(digest[:12], 16)
    return value / float(0xFFFFFFFFFFFF)


def _validate_split(train: float, val: float, test: float) -> None:
    total = train + val + test
    if abs(total - 1.0) > 1e-9:
        raise SystemExit(f"Split ratios must sum to 1.0; got {total}")
    if min(train, val, test) < 0:
        raise SystemExit("Split ratios must be non-negative.")


def _rebalance_splits(
    train_rows: list[dict[str, Any]],
    val_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    min_val_rows: int,
    min_test_rows: int,
) -> None:
    while len(val_rows) < min_val_rows and len(train_rows) > 1:
        val_rows.append(train_rows.pop())
    while len(test_rows) < min_test_rows and len(train_rows) > 1:
        test_rows.append(train_rows.pop())


def run_quality_pipeline(config_path: Path) -> dict[str, Any]:
    cfg = _load_yaml(config_path)
    input_cfg = cfg.get("input", {})
    output_cfg = cfg.get("output", {})
    policy = cfg.get("policy", {})
    split_cfg = cfg.get("split", {})
    if not isinstance(input_cfg, dict) or not isinstance(output_cfg, dict):
        raise SystemExit("input/output sections must be mappings")
    if not isinstance(policy, dict) or not isinstance(split_cfg, dict):
        raise SystemExit("policy/split sections must be mappings")

    input_file = _resolve_path(str(input_cfg.get("jsonl_file", "")))
    if not input_file.exists():
        raise SystemExit(f"Input dataset not found: {input_file}")

    cleaned_file = _resolve_path(str(output_cfg.get("cleaned_jsonl", "files/training/data/cleaned.jsonl")))
    rejected_file = _resolve_path(str(output_cfg.get("rejected_jsonl", "files/training/data/rejected.jsonl")))
    report_file = _resolve_path(str(output_cfg.get("report_json", "files/training/data/quality_report.json")))
    split_dir = _resolve_path(str(output_cfg.get("split_dir", "files/training/data/splits")))
    split_dir.mkdir(parents=True, exist_ok=True)

    require_roles = [str(x) for x in policy.get("require_roles", ["system", "user", "assistant"])]
    parse_assistant_json = bool(policy.get("parse_assistant_json", True))
    min_user_chars = int(policy.get("min_user_chars", 20))
    min_assistant_chars = int(policy.get("min_assistant_chars", 20))
    max_total_chars = int(policy.get("max_total_chars", 30000))
    max_selected_question_ids = int(policy.get("max_selected_question_ids", 500))
    banned_patterns_raw = policy.get("banned_patterns", [])
    if not isinstance(banned_patterns_raw, list):
        raise SystemExit("policy.banned_patterns must be a list")
    banned_patterns = [re.compile(str(pattern), flags=re.IGNORECASE) for pattern in banned_patterns_raw]
    dedupe_cfg = policy.get("dedupe", {})
    if not isinstance(dedupe_cfg, dict):
        dedupe_cfg = {}
    dedupe_enabled = bool(dedupe_cfg.get("enabled", True))
    dedupe_mode = str(dedupe_cfg.get("mode", "user_plus_assistant"))
    gates_cfg = policy.get("solid_dataset_gates", {})
    if not isinstance(gates_cfg, dict):
        gates_cfg = {}

    train_ratio = float(split_cfg.get("train_ratio", 0.9))
    val_ratio = float(split_cfg.get("val_ratio", 0.08))
    test_ratio = float(split_cfg.get("test_ratio", 0.02))
    split_salt = str(split_cfg.get("hash_salt", "swag-default"))
    min_val_rows = int(split_cfg.get("min_val_rows", 1))
    min_test_rows = int(split_cfg.get("min_test_rows", 1))
    _validate_split(train_ratio, val_ratio, test_ratio)

    rows = _read_jsonl(input_file)
    cleaned: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    dedupe_index: set[str] = set()
    reason_counts: dict[str, int] = {}

    for idx, row in enumerate(rows, start=1):
        reasons: list[str] = []
        messages = row.get("messages")
        if not isinstance(messages, list):
            reasons.append("messages_missing_or_not_list")
            messages = []

        normalized_messages: list[dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                reasons.append("message_not_object")
                continue
            role = msg.get("role")
            content = msg.get("content")
            if not isinstance(role, str) or not role:
                reasons.append("role_missing")
                continue
            if not isinstance(content, str) or not content.strip():
                reasons.append("content_missing")
                continue
            normalized_messages.append({"role": role, "content": content})

        roles_present = {item["role"] for item in normalized_messages}
        for role in require_roles:
            if role not in roles_present:
                reasons.append(f"missing_role:{role}")

        system_text = _find_message(normalized_messages, "system")
        user_text = _find_message(normalized_messages, "user")
        assistant_text = _find_message(normalized_messages, "assistant")

        if len(user_text) < min_user_chars:
            reasons.append("user_too_short")
        if len(assistant_text) < min_assistant_chars:
            reasons.append("assistant_too_short")
        if (len(system_text) + len(user_text) + len(assistant_text)) > max_total_chars:
            reasons.append("sample_too_large")

        for pattern in banned_patterns:
            if pattern.search(system_text) or pattern.search(user_text) or pattern.search(assistant_text):
                reasons.append(f"banned_pattern:{pattern.pattern}")

        parsed_assistant: dict[str, Any] | None = None
        if parse_assistant_json:
            try:
                obj = json.loads(assistant_text)
                if not isinstance(obj, dict):
                    reasons.append("assistant_json_not_object")
                else:
                    parsed_assistant = obj
            except json.JSONDecodeError:
                reasons.append("assistant_json_parse_failed")

        if parsed_assistant is not None:
            ids = parsed_assistant.get("selected_question_ids")
            if not isinstance(ids, list):
                reasons.append("selected_question_ids_missing")
            else:
                if len(ids) > max_selected_question_ids:
                    reasons.append("selected_question_ids_too_many")
                for item in ids:
                    if not isinstance(item, str) or not item.strip():
                        reasons.append("selected_question_id_invalid")
                        break

        dedupe_key = ""
        if dedupe_mode == "user_plus_assistant":
            dedupe_key = hashlib.sha256((user_text + "\n" + assistant_text).encode("utf-8")).hexdigest()
        elif dedupe_mode == "full_triplet":
            dedupe_key = hashlib.sha256(
                (system_text + "\n" + user_text + "\n" + assistant_text).encode("utf-8")
            ).hexdigest()

        if dedupe_enabled and dedupe_key:
            if dedupe_key in dedupe_index:
                reasons.append("duplicate_sample")
            else:
                dedupe_index.add(dedupe_key)

        if reasons:
            for reason in reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            rejected.append(
                {
                    "line_index": idx,
                    "reasons": sorted(set(reasons)),
                    "sample": row,
                }
            )
            continue

        cleaned.append(row)

    _write_jsonl(cleaned_file, cleaned)
    _write_jsonl(rejected_file, rejected)

    train_rows: list[dict[str, Any]] = []
    val_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []

    for row in cleaned:
        messages = row.get("messages", [])
        if not isinstance(messages, list):
            continue
        user_text = _find_message([m for m in messages if isinstance(m, dict)], "user")
        assistant_text = _find_message([m for m in messages if isinstance(m, dict)], "assistant")
        bucket = _stable_bucket(user_text + "|" + assistant_text, split_salt)
        if bucket < train_ratio:
            train_rows.append(row)
        elif bucket < train_ratio + val_ratio:
            val_rows.append(row)
        else:
            test_rows.append(row)

    if len(cleaned) >= 10:
        _rebalance_splits(train_rows, val_rows, test_rows, min_val_rows=min_val_rows, min_test_rows=min_test_rows)

    train_file = split_dir / "train.jsonl"
    val_file = split_dir / "val.jsonl"
    test_file = split_dir / "test.jsonl"
    _write_jsonl(train_file, train_rows)
    _write_jsonl(val_file, val_rows)
    _write_jsonl(test_file, test_rows)

    unique_scenarios: set[str] = set()
    unique_selected_question_ids: set[str] = set()
    stack_row_counts: dict[str, int] = defaultdict(int)
    stack_unique_selected_question_ids: dict[str, set[str]] = defaultdict(set)
    rows_with_question_citations = 0
    rows_with_reference_urls = 0
    source_family_counts: dict[str, int] = defaultdict(int)
    synthetic_variant_rows = 0
    user_lengths: list[int] = []
    assistant_lengths: list[int] = []
    for row in cleaned:
        metadata = row.get("metadata")
        if isinstance(metadata, dict):
            scenario = metadata.get("scenario_id")
            if isinstance(scenario, str) and scenario.strip():
                unique_scenarios.add(scenario)
            if bool(metadata.get("synthetic_variant")):
                synthetic_variant_rows += 1
            citation_count = metadata.get("question_citation_count", 0)
            if isinstance(citation_count, (int, float)) and int(citation_count) > 0:
                rows_with_question_citations += 1
            reference_count = metadata.get("question_reference_url_count", 0)
            if isinstance(reference_count, (int, float)) and int(reference_count) > 0:
                rows_with_reference_urls += 1
            family = metadata.get("source_family")
            if isinstance(family, str) and family.strip():
                source_family_counts[family.strip()] += 1
            else:
                source_type = metadata.get("source_type")
                if isinstance(source_type, str) and source_type.strip():
                    source_family_counts[source_type.strip()] += 1
        messages = row.get("messages", [])
        msg_dicts = [m for m in messages if isinstance(m, dict)] if isinstance(messages, list) else []
        user_text = _find_message(msg_dicts, "user")
        assistant_text = _find_message(msg_dicts, "assistant")
        user_lengths.append(len(user_text))
        assistant_lengths.append(len(assistant_text))
        try:
            parsed = json.loads(assistant_text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            ids = parsed.get("selected_question_ids", [])
            if isinstance(ids, list):
                row_prefixes: set[str] = set()
                for item in ids:
                    if isinstance(item, str) and item.strip():
                        unique_selected_question_ids.add(item)
                        prefix = item.split(".", 1)[0].strip().lower()
                        if prefix:
                            row_prefixes.add(prefix)
                            stack_unique_selected_question_ids[prefix].add(item)
                for prefix in row_prefixes:
                    stack_row_counts[prefix] += 1

    avg_user_chars = (sum(user_lengths) / len(user_lengths)) if user_lengths else 0.0
    avg_assistant_chars = (sum(assistant_lengths) / len(assistant_lengths)) if assistant_lengths else 0.0
    rejection_rate = (len(rejected) / len(rows)) if rows else 0.0

    min_accepted_rows = int(gates_cfg.get("min_accepted_rows", 0))
    min_train_rows = int(gates_cfg.get("min_train_rows", 0))
    min_val_gate_rows = int(gates_cfg.get("min_val_rows", min_val_rows))
    min_test_gate_rows = int(gates_cfg.get("min_test_rows", min_test_rows))
    min_unique_scenarios = int(gates_cfg.get("min_unique_scenarios", 0))
    min_unique_selected_ids = int(gates_cfg.get("min_unique_selected_question_ids", 0))
    max_rejection_rate = float(gates_cfg.get("max_rejection_rate", 1.0))
    max_duplicate_rate = float(gates_cfg.get("max_duplicate_rate", 1.0))
    min_distinct_stack_prefixes = int(gates_cfg.get("min_distinct_stack_prefixes", 0))
    required_stack_min_rows_raw = gates_cfg.get("required_stack_min_rows", {})
    required_stack_min_unique_ids_raw = gates_cfg.get("required_stack_min_unique_selected_question_ids", {})
    if not isinstance(required_stack_min_rows_raw, dict):
        raise SystemExit("policy.solid_dataset_gates.required_stack_min_rows must be a mapping")
    if not isinstance(required_stack_min_unique_ids_raw, dict):
        raise SystemExit(
            "policy.solid_dataset_gates.required_stack_min_unique_selected_question_ids must be a mapping"
        )
    required_stack_min_rows = {str(k): int(v) for k, v in required_stack_min_rows_raw.items()}
    required_stack_min_unique_ids = {str(k): int(v) for k, v in required_stack_min_unique_ids_raw.items()}
    min_rows_with_question_citations = int(gates_cfg.get("min_rows_with_question_citations", 0))
    min_rows_with_reference_urls = int(gates_cfg.get("min_rows_with_reference_urls", 0))
    max_synthetic_variant_ratio = float(gates_cfg.get("max_synthetic_variant_ratio", 1.0))
    required_source_family_min_rows_raw = gates_cfg.get("required_source_family_min_rows", {})
    if not isinstance(required_source_family_min_rows_raw, dict):
        raise SystemExit("policy.solid_dataset_gates.required_source_family_min_rows must be a mapping")
    required_source_family_min_rows = {str(k): int(v) for k, v in required_source_family_min_rows_raw.items()}
    fail_on_violation = bool(gates_cfg.get("fail_on_violation", False))
    duplicate_rate = (reason_counts.get("duplicate_sample", 0) / len(rows)) if rows else 0.0
    synthetic_variant_ratio = (synthetic_variant_rows / len(cleaned)) if cleaned else 0.0

    gate_checks = [
        {"name": "accepted_rows", "ok": len(cleaned) >= min_accepted_rows, "actual": len(cleaned), "required_min": min_accepted_rows},
        {"name": "train_rows", "ok": len(train_rows) >= min_train_rows, "actual": len(train_rows), "required_min": min_train_rows},
        {"name": "val_rows", "ok": len(val_rows) >= min_val_gate_rows, "actual": len(val_rows), "required_min": min_val_gate_rows},
        {"name": "test_rows", "ok": len(test_rows) >= min_test_gate_rows, "actual": len(test_rows), "required_min": min_test_gate_rows},
        {
            "name": "unique_scenarios",
            "ok": len(unique_scenarios) >= min_unique_scenarios,
            "actual": len(unique_scenarios),
            "required_min": min_unique_scenarios,
        },
        {
            "name": "unique_selected_question_ids",
            "ok": len(unique_selected_question_ids) >= min_unique_selected_ids,
            "actual": len(unique_selected_question_ids),
            "required_min": min_unique_selected_ids,
        },
        {
            "name": "rejection_rate",
            "ok": rejection_rate <= max_rejection_rate,
            "actual": rejection_rate,
            "required_max": max_rejection_rate,
        },
        {
            "name": "duplicate_rate",
            "ok": duplicate_rate <= max_duplicate_rate,
            "actual": duplicate_rate,
            "required_max": max_duplicate_rate,
        },
        {
            "name": "distinct_stack_prefixes",
            "ok": len(stack_row_counts) >= min_distinct_stack_prefixes,
            "actual": len(stack_row_counts),
            "required_min": min_distinct_stack_prefixes,
        },
        {
            "name": "rows_with_question_citations",
            "ok": rows_with_question_citations >= min_rows_with_question_citations,
            "actual": rows_with_question_citations,
            "required_min": min_rows_with_question_citations,
        },
        {
            "name": "rows_with_reference_urls",
            "ok": rows_with_reference_urls >= min_rows_with_reference_urls,
            "actual": rows_with_reference_urls,
            "required_min": min_rows_with_reference_urls,
        },
        {
            "name": "synthetic_variant_ratio",
            "ok": synthetic_variant_ratio <= max_synthetic_variant_ratio,
            "actual": synthetic_variant_ratio,
            "required_max": max_synthetic_variant_ratio,
        },
    ]
    for stack_key in sorted(required_stack_min_rows.keys()):
        required_min = required_stack_min_rows[stack_key]
        actual = int(stack_row_counts.get(stack_key, 0))
        gate_checks.append(
            {
                "name": f"stack_rows:{stack_key}",
                "ok": actual >= required_min,
                "actual": actual,
                "required_min": required_min,
            }
        )
    for stack_key in sorted(required_stack_min_unique_ids.keys()):
        required_min = required_stack_min_unique_ids[stack_key]
        actual = len(stack_unique_selected_question_ids.get(stack_key, set()))
        gate_checks.append(
            {
                "name": f"stack_unique_selected_question_ids:{stack_key}",
                "ok": actual >= required_min,
                "actual": actual,
                "required_min": required_min,
            }
        )
    for family in sorted(required_source_family_min_rows.keys()):
        required_min = required_source_family_min_rows[family]
        actual = int(source_family_counts.get(family, 0))
        gate_checks.append(
            {
                "name": f"source_family_rows:{family}",
                "ok": actual >= required_min,
                "actual": actual,
                "required_min": required_min,
            }
        )
    overall_gates_pass = all(item["ok"] for item in gate_checks)

    report = {
        "config": str(config_path.resolve()),
        "input_file": str(input_file.resolve()),
        "output": {
            "cleaned_jsonl": str(cleaned_file.resolve()),
            "rejected_jsonl": str(rejected_file.resolve()),
            "split_dir": str(split_dir.resolve()),
            "report_json": str(report_file.resolve()),
        },
        "counts": {
            "input_rows": len(rows),
            "accepted_rows": len(cleaned),
            "rejected_rows": len(rejected),
            "train_rows": len(train_rows),
            "val_rows": len(val_rows),
            "test_rows": len(test_rows),
        },
        "solid_dataset_metrics": {
            "unique_scenarios": len(unique_scenarios),
            "unique_selected_question_ids": len(unique_selected_question_ids),
            "avg_user_chars": round(avg_user_chars, 2),
            "avg_assistant_chars": round(avg_assistant_chars, 2),
            "rejection_rate": round(rejection_rate, 6),
            "rows_with_question_citations": rows_with_question_citations,
            "rows_with_reference_urls": rows_with_reference_urls,
            "synthetic_variant_rows": synthetic_variant_rows,
            "synthetic_variant_ratio": round(synthetic_variant_ratio, 6),
            "source_family_counts": {k: int(v) for k, v in sorted(source_family_counts.items())},
            "distinct_stack_prefixes": len(stack_row_counts),
            "stack_row_counts": {k: int(v) for k, v in sorted(stack_row_counts.items())},
            "stack_unique_selected_question_ids": {
                k: len(v) for k, v in sorted(stack_unique_selected_question_ids.items())
            },
        },
        "solid_dataset_gates": {
            "configured": {
                "min_accepted_rows": min_accepted_rows,
                "min_train_rows": min_train_rows,
                "min_val_rows": min_val_gate_rows,
                "min_test_rows": min_test_gate_rows,
                "min_unique_scenarios": min_unique_scenarios,
                "min_unique_selected_question_ids": min_unique_selected_ids,
                "max_rejection_rate": max_rejection_rate,
                "max_duplicate_rate": max_duplicate_rate,
                "min_distinct_stack_prefixes": min_distinct_stack_prefixes,
                "min_rows_with_question_citations": min_rows_with_question_citations,
                "min_rows_with_reference_urls": min_rows_with_reference_urls,
                "max_synthetic_variant_ratio": max_synthetic_variant_ratio,
                "required_source_family_min_rows": required_source_family_min_rows,
                "required_stack_min_rows": required_stack_min_rows,
                "required_stack_min_unique_selected_question_ids": required_stack_min_unique_ids,
                "fail_on_violation": fail_on_violation,
            },
            "checks": gate_checks,
            "overall_pass": overall_gates_pass,
        },
        "rejection_reasons": reason_counts,
    }
    _write_json(report_file, report)
    if fail_on_violation and not overall_gates_pass:
        failed = [item["name"] for item in gate_checks if not item["ok"]]
        raise RuntimeError(f"Solid dataset gate failure: {', '.join(failed)}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SWAG dataset quality gates and split generation.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Dataset quality config YAML.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_quality_pipeline(args.config.resolve())
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
