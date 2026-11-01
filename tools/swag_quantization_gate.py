#!/usr/bin/env python3
"""Quantization benchmark gate evaluator for SWAG controller models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "training" / "quantization_gate.template.yaml"


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


def _resolve(path_like: str) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else (ROOT / path)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _thresholds_for_tier(policy: dict[str, Any], tier: str) -> dict[str, float]:
    defaults = policy.get("default_thresholds", {})
    if not isinstance(defaults, dict):
        defaults = {}
    by_tier = policy.get("thresholds_by_tier", {})
    if not isinstance(by_tier, dict):
        by_tier = {}
    tier_overrides = by_tier.get(tier, {})
    if not isinstance(tier_overrides, dict):
        tier_overrides = {}
    merged = {
        "max_quality_delta_abs": float(defaults.get("max_quality_delta_abs", 0.03)),
        "min_latency_tokens_per_sec_gain": float(defaults.get("min_latency_tokens_per_sec_gain", 0.05)),
        "min_memory_reduction_ratio": float(defaults.get("min_memory_reduction_ratio", 0.15)),
    }
    for key in list(merged.keys()):
        if key in tier_overrides:
            merged[key] = float(tier_overrides[key])
    return merged


def evaluate_quantization_gate(config_path: Path) -> dict[str, Any]:
    cfg = _load_yaml(config_path)
    input_cfg = cfg.get("input", {})
    output_cfg = cfg.get("output", {})
    policy = cfg.get("policy", {})
    if not isinstance(input_cfg, dict) or not isinstance(output_cfg, dict) or not isinstance(policy, dict):
        raise RuntimeError("input/output/policy sections must be mappings.")

    results_file = _resolve(str(input_cfg.get("benchmark_results_file", "")))
    if not results_file.exists():
        raise RuntimeError(f"Quantization benchmark results file not found: {results_file}")
    report_file = _resolve(str(output_cfg.get("gate_report_file", "files/training/benchmarks/quantization_gate_report.json")))

    payload = _load_json(results_file)
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("benchmark_results_file must contain {\"results\": [...]} with at least one entry.")

    baseline_key = str(policy.get("baseline_profile_key", "bf16"))
    baseline_by_tier = policy.get("baseline_profile_key_by_tier", {})
    if not isinstance(baseline_by_tier, dict):
        baseline_by_tier = {}
    fail_on_violation = bool(policy.get("fail_on_violation", False))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        tier = str(row.get("tier", "")).strip()
        family = str(row.get("family", "")).strip()
        model = str(row.get("model", "")).strip()
        profile_key = str(row.get("profile_key", "")).strip()
        if not (tier and family and model and profile_key):
            continue
        key = f"{tier}::{family}::{model}"
        grouped.setdefault(key, []).append(row)

    evaluations: list[dict[str, Any]] = []
    model_failures: list[dict[str, Any]] = []
    promotion_candidates: list[dict[str, Any]] = []

    for model_key, model_rows in grouped.items():
        tier_from_key = model_key.split("::", 1)[0]
        effective_baseline_key = str(baseline_by_tier.get(tier_from_key, baseline_key))
        baseline = None
        for row in model_rows:
            if str(row.get("profile_key", "")) == effective_baseline_key:
                baseline = row
                break
        if baseline is None:
            model_failures.append(
                {"model_key": model_key, "reason": f"Missing baseline profile {effective_baseline_key!r}."}
            )
            continue

        try:
            base_quality = float(baseline.get("quality_score"))
            base_tps = float(baseline.get("latency_tokens_per_sec"))
            base_mem = float(baseline.get("memory_gb"))
        except (TypeError, ValueError) as exc:
            model_failures.append({"model_key": model_key, "reason": f"Invalid baseline numeric fields: {exc}"})
            continue

        tier = str(baseline.get("tier"))
        thresholds = _thresholds_for_tier(policy, tier)
        model_evals: list[dict[str, Any]] = []

        for row in model_rows:
            profile_key = str(row.get("profile_key", ""))
            if profile_key == effective_baseline_key:
                continue
            try:
                quality = float(row.get("quality_score"))
                tps = float(row.get("latency_tokens_per_sec"))
                mem = float(row.get("memory_gb"))
            except (TypeError, ValueError) as exc:
                model_evals.append({"profile_key": profile_key, "pass": False, "reason": f"Invalid numeric fields: {exc}"})
                continue

            quality_delta_abs = abs(base_quality - quality)
            tps_gain = (tps - base_tps) / base_tps if base_tps > 0 else 0.0
            mem_reduction = (base_mem - mem) / base_mem if base_mem > 0 else 0.0

            checks = {
                "quality_delta_abs_ok": quality_delta_abs <= thresholds["max_quality_delta_abs"],
                "latency_gain_ok": tps_gain >= thresholds["min_latency_tokens_per_sec_gain"],
                "memory_reduction_ok": mem_reduction >= thresholds["min_memory_reduction_ratio"],
            }
            passed = all(checks.values())
            eval_row = {
                "profile_key": profile_key,
                "pass": passed,
                "metrics": {
                    "quality_delta_abs": round(quality_delta_abs, 6),
                    "latency_tokens_per_sec_gain": round(tps_gain, 6),
                    "memory_reduction_ratio": round(mem_reduction, 6),
                },
                "checks": checks,
            }
            model_evals.append(eval_row)

        best_promotion = None
        passing = [item for item in model_evals if item.get("pass")]
        if passing:
            passing.sort(
                key=lambda item: (
                    float((item.get("metrics") or {}).get("latency_tokens_per_sec_gain", 0.0)),
                    float((item.get("metrics") or {}).get("memory_reduction_ratio", 0.0)),
                ),
                reverse=True,
            )
            best_promotion = passing[0]
            promotion_candidates.append({"model_key": model_key, "profile_key": best_promotion.get("profile_key")})
        else:
            model_failures.append({"model_key": model_key, "reason": "No quantized profile met gate thresholds."})

        evaluations.append(
            {
                "model_key": model_key,
                "tier": tier,
                "family": baseline.get("family"),
                "model": baseline.get("model"),
                "baseline_profile": effective_baseline_key,
                "thresholds": thresholds,
                "profiles": model_evals,
                "recommended_profile": best_promotion.get("profile_key") if best_promotion else baseline_key,
            }
        )

    overall_pass = len(model_failures) == 0
    report = {
        "config": str(config_path.resolve()),
        "benchmark_results_file": str(results_file.resolve()),
        "baseline_profile_key": baseline_key,
        "overall_pass": overall_pass,
        "evaluations": evaluations,
        "promotion_candidates": promotion_candidates,
        "failures": model_failures,
    }
    _write_json(report_file, report)
    if fail_on_violation and not overall_pass:
        raise RuntimeError(f"Quantization gate failed for {len(model_failures)} model groups.")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate quantization benchmark gate results.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = evaluate_quantization_gate(_resolve(str(args.config)))
    print(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
