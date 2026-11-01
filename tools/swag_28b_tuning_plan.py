#!/usr/bin/env python3
"""Render the BF16-first controller research plan (legacy command filename)."""
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
DEFAULT_CONFIG = ROOT / "config" / "training" / "swag_28b_tuning_plan.template.yaml"


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


def build_plan(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    data = _load_yaml(config_path)
    model = data.get("model", {})
    runtime = data.get("runtime", {})
    training = data.get("training", {})
    tactics = data.get("research_tactics", [])
    execution = data.get("execution_sequence", [])
    notes = data.get("research_notes", {})

    plan = {
        "status": data.get("status", "unqualified"),
        "description": data.get("description", ""),
        "target_tier": model.get("primary_tier"),
        "preferred_candidates": model.get("preferred_candidates", []),
        "runtime_budget": {
            "precision": runtime.get("precision"),
            "target_memory_gb": runtime.get("target_memory_gb"),
            "target_memory_mode": runtime.get("target_memory_mode"),
            "future_serving_target_bytes": runtime.get("future_serving_target_bytes"),
            "preferred_quantization": runtime.get("preferred_quantization"),
            "max_context_tokens": runtime.get("max_context_tokens", 4096),
            "max_concurrent_sequences": runtime.get("max_concurrent_sequences"),
            "kv_cache_memory_bytes": runtime.get("kv_cache_memory_bytes"),
            "fallback_if_memory_unavailable": runtime.get("fallback_if_memory_unavailable"),
        },
        "training_objective": str(training.get("objective", "")),
        "dataset_mix": training.get("dataset_mix", {}),
        "lora": training.get("lora", {}),
        "optimizer": training.get("optimizer", {}),
        "quality_gate": training.get("quality_gate", {}),
        "benchmark_suite": data.get("benchmark_suite", []),
        "gpu_requirements": data.get("gpu_requirements", {}),
        "research_tactics": tactics,
        "execution_sequence": execution,
        "implementation_principle": notes.get("implementation_principle", ""),
    }
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render SWAG's BF16-first research plan; no training or qualification is performed.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="YAML plan template to render.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "files" / "training" / "swag_28b_tuning_plan.json",
        help="JSON output path.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2 if args.pretty else None, ensure_ascii=True)
    print(json.dumps(plan, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
