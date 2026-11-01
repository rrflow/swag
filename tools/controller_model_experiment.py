#!/usr/bin/env python3
"""Model experiment harness for the boundary controller.

Generates apples-to-apples scenario packs for model tiers (7B, 14B, 27-28B),
and optionally scores model outputs against controller-derived expected batteries.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from boundary_controller import compose_battery


DEFAULT_MODELS = ["27-28b", "14b", "7b"]
DEFAULT_MODEL_CATALOG = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "training"
    / "model_catalog.template.yaml"
)
DEFAULT_CLUSTER_PROFILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "training"
    / "spark_cluster_profile.template.yaml"
)


def _default_scenarios(repo: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": "s1-vanilla-general",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "refactor module boundaries and improve naming consistency",
            "domains": [],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s2-iam-auth",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "implement login with passkeys, reset password, and tighten session timeout",
            "domains": [],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s3-admin-privileged",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "admin approval workflows and privileged role separation with audit logging",
            "domains": [],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s4-llm-boundary",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": True,
            "intent_text": "add RAG retrieval and prompt safety guardrails with per-user budgets",
            "domains": [],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s5-billing-subscriptions",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "subscription proration, invoices, payment retries, and refund audit trail",
            "domains": ["billing_and_payments"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s6-notification-reliability",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "email and push notifications with opt-out preferences and retry backoff",
            "domains": ["notifications"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s7-files-media-security",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": True,
            "intent_text": "secure file upload scanning, signed download URLs, and retention deletion",
            "domains": ["files_and_media"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s8-search-relevance",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": True,
            "intent_text": "search indexing freshness, ranking rules, and access-trimmed results",
            "domains": ["search"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s9-analytics-governance",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": True,
            "intent_text": "analytics event schema versioning and KPI lineage in reporting dashboards",
            "domains": ["analytics_and_reporting"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s10-settings-precedence",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "user and org settings precedence with safe defaults and settings audit log",
            "domains": ["settings_and_preferences"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s11-onboarding-activation",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "onboarding setup wizard, invitation flow integrity, and activation drop-off metrics",
            "domains": ["onboarding"],
            "primary_stack": None,
            "include_overlaps": False,
        },
        {
            "id": "s12-java-service-robustness",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "tighten java service boundaries, exception mapping, transaction demarcation, and observability",
            "domains": [],
            "primary_stack": "java",
            "include_overlaps": False,
        },
        {
            "id": "s13-javascript-runtime-safety",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "improve javascript async error handling, module boundaries, and browser compatibility discipline",
            "domains": [],
            "primary_stack": "vanilla_js",
            "include_overlaps": False,
        },
        {
            "id": "s14-cpp-reliability-and-performance",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "harden c++ ownership, concurrency, and diagnostics while preserving performance constraints",
            "domains": [],
            "primary_stack": "cpp",
            "include_overlaps": False,
        },
        {
            "id": "s15-php-web-boundary-integrity",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "reinforce php input validation, secret handling, and transactional write integrity for web boundaries",
            "domains": [],
            "primary_stack": "php",
            "include_overlaps": False,
        },
        {
            "id": "s16-c-systems-correctness",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "improve c memory safety boundaries, build portability, and crash diagnosability",
            "domains": [],
            "primary_stack": "c",
            "include_overlaps": False,
        },
        {
            "id": "s17-python-service-quality",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "strengthen python typing, boundary contracts, exception mapping, and test determinism",
            "domains": [],
            "primary_stack": "python",
            "include_overlaps": False,
        },
        {
            "id": "s18-ruby-service-boundaries",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "harden ruby service boundaries, background job retries, and observability consistency",
            "domains": [],
            "primary_stack": "ruby",
            "include_overlaps": False,
        },
        {
            "id": "s19-sql-data-integrity",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": True,
            "intent_text": "enforce sql migration safety, indexing strategy, and query plan-aware boundary checks",
            "domains": [],
            "primary_stack": "sql",
            "include_overlaps": False,
        },
        {
            "id": "s20-go-service-reliability",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "improve go concurrency boundaries, cancellation discipline, and telemetry consistency",
            "domains": [],
            "primary_stack": "go",
            "include_overlaps": False,
        },
        {
            "id": "s21-typescript-contract-discipline",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "tighten typescript contract rigor, runtime validation, and API error envelope consistency",
            "domains": [],
            "primary_stack": "typescript",
            "include_overlaps": False,
        },
        {
            "id": "s22-react-ui-boundary-integrity",
            "repo": str(repo),
            "maturity": "growing",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "improve react state boundaries, effect hygiene, and component-level accessibility guarantees",
            "domains": [],
            "primary_stack": "react",
            "include_overlaps": False,
        },
        {
            "id": "s23-nextjs-app-router-boundaries",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "enforce nextjs app router boundary rules for server/client components, caching, and mutations",
            "domains": [],
            "primary_stack": "nextjs",
            "include_overlaps": False,
        },
        {
            "id": "s24-rust-runtime-integrity",
            "repo": str(repo),
            "maturity": "mature",
            "has_test_harness": True,
            "unbounded_data_path": False,
            "intent_text": "tighten rust ownership boundaries, error taxonomy, and async runtime reliability choices",
            "domains": [],
            "primary_stack": "rust",
            "include_overlaps": False,
        },
    ]


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: PyYAML is required (pip install pyyaml)."
        ) from exc
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def _load_model_catalog(path: Path, tiers: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {tier: [] for tier in tiers}
    data = _load_yaml(path)
    tier_map = data.get("model_tiers", {})
    if not isinstance(tier_map, dict):
        raise SystemExit(f"model_tiers must be a mapping in {path}")
    out: dict[str, list[dict[str, Any]]] = {}
    for tier in tiers:
        candidates = tier_map.get(tier, [])
        if not isinstance(candidates, list):
            raise SystemExit(f"model_tiers.{tier} must be a list in {path}")
        normalized: list[dict[str, Any]] = []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            model = item.get("model")
            family = item.get("family")
            if not isinstance(model, str) or not model:
                continue
            normalized.append(
                {
                    "family": str(family) if isinstance(family, str) else "unknown",
                    "model": model,
                    "local_runtime": str(item.get("local_runtime", "vllm")),
                    "notes": str(item.get("notes", "")),
                }
            )
        out[tier] = normalized
    return out


def _load_cluster_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_yaml(path)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _score_one(expected_ids: set[str], predicted_ids: set[str]) -> dict[str, Any]:
    tp = len(expected_ids.intersection(predicted_ids))
    fp = len(predicted_ids - expected_ids)
    fn = len(expected_ids - predicted_ids)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
    }


def run_generation(
    repo: Path,
    out_dir: Path,
    models: list[str],
    scenarios_file: Path | None,
) -> dict[str, Any]:
    scenarios = _load_json(scenarios_file) if scenarios_file else _default_scenarios(repo)
    if not isinstance(scenarios, list):
        raise SystemExit("Scenarios file must contain a JSON list of scenario objects.")

    generated: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        scenario_id = str(scenario.get("id"))
        result = compose_battery(
            repo=Path(str(scenario.get("repo", repo))).resolve(),
            maturity=str(scenario.get("maturity", "growing")),
            has_test_harness=bool(scenario.get("has_test_harness", False)),
            unbounded_data_path=bool(scenario.get("unbounded_data_path", False)),
            intent_text=str(scenario.get("intent_text", "")),
            explicit_domains=list(scenario.get("domains", [])),
            primary_stack=scenario.get("primary_stack"),
            include_overlaps=bool(scenario.get("include_overlaps", False)),
        )
        expected_ids = [q["id"] for q in result.get("questions", []) if isinstance(q, dict) and q.get("id")]

        scenario_dir = out_dir / scenario_id
        _write_json(scenario_dir / "scenario.json", scenario)
        _write_json(scenario_dir / "expected_battery.json", result)
        _write_json(
            scenario_dir / "model_prompt_contract.json",
            {
                "task": "Select applicable boundary questions for this scenario.",
                "required_output_shape": {
                    "selected_question_ids": ["..."],
                    "skipped_question_ids": ["..."],
                    "notes": "short rationale and uncertainty",
                },
                "expected_question_count": len(expected_ids),
                "allowed_question_ids": expected_ids,
            },
        )

        for model in models:
            template_path = scenario_dir / f"response_template__{model}.json"
            _write_json(
                template_path,
                {
                    "model_tier": model,
                    "selected_question_ids": [],
                    "skipped_question_ids": [],
                    "notes": "",
                },
            )

        generated.append(
            {
                "scenario_id": scenario_id,
                "question_count": len(expected_ids),
                "selected_stacks": result.get("detected", {}).get("selected_stacks", []),
                "detected_domains": result.get("detected", {}).get("domains", []),
            }
        )

    return {
        "output_dir": str(out_dir),
        "models": models,
        "scenarios_generated": generated,
        "how_to_score": "Run again with --responses-dir after filling response_template files.",
    }


def score_responses(out_dir: Path, responses_dir: Path, models: list[str]) -> dict[str, Any]:
    scenario_dirs = [p for p in out_dir.iterdir() if p.is_dir()]
    per_model: dict[str, list[dict[str, Any]]] = {m: [] for m in models}

    for scenario_dir in scenario_dirs:
        expected_file = scenario_dir / "expected_battery.json"
        if not expected_file.exists():
            continue
        expected = _load_json(expected_file)
        expected_ids = {
            q["id"]
            for q in expected.get("questions", [])
            if isinstance(q, dict) and isinstance(q.get("id"), str)
        }
        scenario_id = scenario_dir.name

        for model in models:
            response_file = responses_dir / f"{scenario_id}__{model}.json"
            if not response_file.exists():
                continue
            response = _load_json(response_file)
            selected_ids = set(response.get("selected_question_ids", []))
            metrics = _score_one(expected_ids, selected_ids)
            per_model[model].append({"scenario_id": scenario_id, **metrics})

    summary: dict[str, Any] = {}
    for model, rows in per_model.items():
        if not rows:
            summary[model] = {"scenarios_scored": 0}
            continue
        summary[model] = {
            "scenarios_scored": len(rows),
            "avg_precision": sum(r["precision"] for r in rows) / len(rows),
            "avg_recall": sum(r["recall"] for r in rows) / len(rows),
            "avg_f1": sum(r["f1"] for r in rows) / len(rows),
            "details": rows,
        }
    return summary


def _build_promotion_scorecard(
    models: list[str],
    scoring_summary: dict[str, Any] | None,
    tier_metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    runtime_values: list[float] = []

    for tier in models:
        metrics = tier_metrics.get(tier, {}) if isinstance(tier_metrics, dict) else {}
        runtime_seconds = _to_float(metrics.get("runtime_seconds")) if isinstance(metrics, dict) else None
        if runtime_seconds is not None and runtime_seconds > 0:
            runtime_values.append(runtime_seconds)

    min_runtime = min(runtime_values) if runtime_values else None
    max_runtime = max(runtime_values) if runtime_values else None

    for tier in models:
        score_row = scoring_summary.get(tier, {}) if isinstance(scoring_summary, dict) else {}
        metrics = tier_metrics.get(tier, {}) if isinstance(tier_metrics, dict) else {}

        avg_f1 = _to_float(score_row.get("avg_f1")) if isinstance(score_row, dict) else None
        mean_token_accuracy = _to_float(metrics.get("mean_token_accuracy")) if isinstance(metrics, dict) else None
        train_loss = _to_float(metrics.get("train_loss")) if isinstance(metrics, dict) else None
        runtime_seconds = _to_float(metrics.get("runtime_seconds")) if isinstance(metrics, dict) else None

        quality_components: list[float] = []
        if avg_f1 is not None:
            quality_components.append(max(0.0, min(avg_f1, 1.0)))
        if mean_token_accuracy is not None:
            quality_components.append(max(0.0, min(mean_token_accuracy, 1.0)))
        if train_loss is not None and train_loss >= 0:
            quality_components.append(1.0 / (1.0 + train_loss))
        quality_score = (
            sum(quality_components) / len(quality_components) if quality_components else None
        )

        efficiency_score = None
        if (
            runtime_seconds is not None
            and runtime_seconds > 0
            and min_runtime is not None
            and max_runtime is not None
        ):
            if max_runtime == min_runtime:
                efficiency_score = 1.0
            else:
                efficiency_score = (max_runtime - runtime_seconds) / (max_runtime - min_runtime)

        if quality_score is not None and efficiency_score is not None:
            composite_score = 0.75 * quality_score + 0.25 * efficiency_score
        else:
            composite_score = quality_score

        rows.append(
            {
                "tier": tier,
                "scenarios_scored": (
                    int(score_row.get("scenarios_scored", 0))
                    if isinstance(score_row, dict)
                    else 0
                ),
                "avg_f1": avg_f1,
                "mean_token_accuracy": mean_token_accuracy,
                "train_loss": train_loss,
                "runtime_seconds": runtime_seconds,
                "quality_score": quality_score,
                "efficiency_score": efficiency_score,
                "composite_score": composite_score,
            }
        )

    ranked = sorted(
        rows,
        key=lambda item: item["composite_score"] if isinstance(item.get("composite_score"), (int, float)) else -1.0,
        reverse=True,
    )
    has_scenario_quality = any(
        isinstance(row.get("avg_f1"), (int, float)) and int(row.get("scenarios_scored", 0)) > 0
        for row in rows
    )
    recommended_default_tier = (
        ranked[0]["tier"]
        if ranked and ranked[0].get("composite_score") is not None and has_scenario_quality
        else None
    )
    return {
        "weights": {"quality_score": 0.75, "efficiency_score": 0.25},
        "rows": rows,
        "ranked_tiers": [row["tier"] for row in ranked if isinstance(row.get("composite_score"), (int, float))],
        "recommendation": {
            "policy_candidate_default_tier": "14b" if "14b" in models else (models[0] if models else None),
            "recommended_default_tier": recommended_default_tier,
            "insufficient_evidence": not has_scenario_quality,
            "notes": (
                "recommended_default_tier is withheld until scenario scoring is provided (avg_f1 from --responses-dir)."
                if not has_scenario_quality
                else "recommended_default_tier selected from composite score."
            ),
        },
    }


def _find_profile(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for item in items:
        if isinstance(item, dict) and item.get("key") == key:
            return item
    raise SystemExit(f"Profile {key!r} not found.")


def build_execution_plan(
    out_dir: Path,
    models: list[str],
    provider_config_path: Path,
    attunement_config_path: Path,
    attunement_profile_key: str,
    route_profile_key: str | None,
    model_catalog_path: Path,
    cluster_profile_path: Path,
) -> dict[str, Any]:
    provider_cfg = _load_yaml(provider_config_path)
    attunement_cfg = _load_yaml(attunement_config_path)
    model_catalog = _load_model_catalog(model_catalog_path, models)
    cluster_profile = _load_cluster_profile(cluster_profile_path)

    routing_profiles = provider_cfg.get("routing_profiles", [])
    if not isinstance(routing_profiles, list):
        raise SystemExit("routing_profiles must be a list in provider config.")

    selected_attunement = _find_profile(
        [p for p in attunement_cfg.get("profiles", []) if isinstance(p, dict)],
        attunement_profile_key,
    )
    default_route = (
        ((selected_attunement.get("execution_policy") or {}).get("route_profile"))
        if isinstance(selected_attunement.get("execution_policy"), dict)
        else None
    )
    selected_route_key = route_profile_key or str(default_route or "")
    selected_route = _find_profile(
        [r for r in routing_profiles if isinstance(r, dict)],
        selected_route_key,
    )

    key_index: dict[str, dict[str, Any]] = {}
    for key_cfg in provider_cfg.get("api_keys", []):
        if isinstance(key_cfg, dict) and isinstance(key_cfg.get("key_id"), str):
            key_index[str(key_cfg["key_id"])] = key_cfg

    scenario_dirs = [p for p in out_dir.iterdir() if p.is_dir()]
    scenario_execution: list[dict[str, Any]] = []

    for scenario_dir in sorted(scenario_dirs):
        scenario_file = scenario_dir / "scenario.json"
        if not scenario_file.exists():
            continue
        scenario = _load_json(scenario_file)
        scenario_id = scenario_dir.name
        tier_plans: dict[str, Any] = {}
        for tier in models:
            tier_route = (
                (selected_route.get("model_tier_routes") or {}).get(tier)
                if isinstance(selected_route.get("model_tier_routes"), dict)
                else None
            )
            if not isinstance(tier_route, dict):
                continue
            key_pool = tier_route.get("key_pool", [])
            if not isinstance(key_pool, list):
                key_pool = []
            keys_resolved = []
            for key_id in key_pool:
                if not isinstance(key_id, str):
                    continue
                key_cfg = key_index.get(key_id)
                if not key_cfg:
                    continue
                env_var = str(key_cfg.get("env_var", ""))
                keys_resolved.append(
                    {
                        "key_id": key_id,
                        "provider": key_cfg.get("provider"),
                        "subscription_tier": key_cfg.get("subscription_tier"),
                        "env_var": env_var,
                        "env_present": bool(env_var and os.environ.get(env_var)),
                        "allowed_model_tiers": key_cfg.get("allowed_model_tiers", []),
                        "usage_policy": key_cfg.get("usage_policy", {}),
                    }
                )
            tier_plans[tier] = {
                "model_preferences": tier_route.get("model_preferences", []),
                "model_candidates": model_catalog.get(tier, []),
                "key_pool": keys_resolved,
            }
        scenario_execution.append(
            {
                "scenario_id": scenario_id,
                "intent_text": scenario.get("intent_text", ""),
                "forced_domains": scenario.get("domains", []),
                "execution_by_tier": tier_plans,
            }
        )

    output = {
        "provider_config": str(provider_config_path),
        "attunement_config": str(attunement_config_path),
        "model_catalog": str(model_catalog_path),
        "cluster_profile": str(cluster_profile_path),
        "attunement_profile": attunement_profile_key,
        "route_profile": selected_route_key,
        "context_scope": selected_attunement.get("context_scope", {}),
        "execution_policy": selected_attunement.get("execution_policy", {}),
        "cluster": cluster_profile.get("cluster", {}),
        "nodes": cluster_profile.get("nodes", []),
        "training_defaults": cluster_profile.get("training_defaults", {}),
        "scenarios": scenario_execution,
    }
    _write_json(out_dir / "execution_plan.json", output)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and score model-tier experiments for boundary controller."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("files") / "controller_experiments",
        help="Directory for generated scenarios and expected outputs.",
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated model tiers (default: 27-28b,14b,7b). Start with 28B for the benchmark path.",
    )
    parser.add_argument(
        "--scenarios-file",
        type=Path,
        default=None,
        help="Optional JSON file containing scenario list.",
    )
    parser.add_argument(
        "--responses-dir",
        type=Path,
        default=None,
        help="Optional directory with model responses named <scenario_id>__<model>.json.",
    )
    parser.add_argument(
        "--provider-config",
        type=Path,
        default=Path("config") / "frontier" / "providers.template.yaml",
        help="Frontier provider/key routing config YAML.",
    )
    parser.add_argument(
        "--attunement-config",
        type=Path,
        default=Path("config") / "attunement" / "operator_profiles.template.yaml",
        help="Operator attunement profile YAML.",
    )
    parser.add_argument(
        "--attunement-profile",
        default="default_rollout",
        help="Operator attunement profile key.",
    )
    parser.add_argument(
        "--route-profile",
        default=None,
        help="Override route profile key from provider config.",
    )
    parser.add_argument(
        "--skip-execution-plan",
        action="store_true",
        help="Skip generation of provider/key execution plan.",
    )
    parser.add_argument(
        "--model-catalog",
        type=Path,
        default=DEFAULT_MODEL_CATALOG,
        help="Model catalog YAML mapping model tiers to candidate families/models.",
    )
    parser.add_argument(
        "--cluster-profile",
        type=Path,
        default=DEFAULT_CLUSTER_PROFILE,
        help="Cluster profile YAML used for execution planning metadata.",
    )
    parser.add_argument(
        "--tier-metrics-file",
        type=Path,
        default=None,
        help="Optional JSON mapping tier->metrics (train_loss, mean_token_accuracy, runtime_seconds).",
    )
    parser.add_argument(
        "--emit-promotion-scorecard",
        action="store_true",
        help="Emit promotion_scorecard.json using scoring and/or tier metrics.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    generated = run_generation(
        repo=args.repo.resolve(),
        out_dir=args.output_dir.resolve(),
        models=models,
        scenarios_file=args.scenarios_file.resolve() if args.scenarios_file else None,
    )
    result: dict[str, Any] = {"generation": generated}
    if not args.skip_execution_plan:
        result["execution_plan"] = build_execution_plan(
            out_dir=args.output_dir.resolve(),
            models=models,
            provider_config_path=args.provider_config.resolve(),
            attunement_config_path=args.attunement_config.resolve(),
            attunement_profile_key=args.attunement_profile,
            route_profile_key=args.route_profile,
            model_catalog_path=args.model_catalog.resolve(),
            cluster_profile_path=args.cluster_profile.resolve(),
        )
    if args.responses_dir:
        result["scoring"] = score_responses(
            out_dir=args.output_dir.resolve(),
            responses_dir=args.responses_dir.resolve(),
            models=models,
        )
    tier_metrics_raw = (
        _load_json(args.tier_metrics_file.resolve())
        if args.tier_metrics_file
        else None
    )
    tier_metrics = tier_metrics_raw
    if isinstance(tier_metrics_raw, dict) and isinstance(tier_metrics_raw.get("tiers"), dict):
        tier_metrics = tier_metrics_raw.get("tiers")
    if args.emit_promotion_scorecard:
        scorecard = _build_promotion_scorecard(
            models=models,
            scoring_summary=result.get("scoring") if isinstance(result.get("scoring"), dict) else None,
            tier_metrics=tier_metrics if isinstance(tier_metrics, dict) else None,
        )
        scorecard_path = args.output_dir.resolve() / "promotion_scorecard.json"
        _write_json(scorecard_path, scorecard)
        result["promotion_scorecard"] = {
            "path": str(scorecard_path),
            "ranked_tiers": scorecard.get("ranked_tiers", []),
            "recommendation": scorecard.get("recommendation", {}),
        }
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
