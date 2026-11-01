#!/usr/bin/env python3
"""SWAG decision service with frontier-routing integration.

Endpoints:
  GET  /health
  GET  /v1/providers/status
  GET  /v1/local/providers/status
  POST /v1/decision
"""
from __future__ import annotations

import argparse
import json
import os
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error, request

from boundary_controller import compose_battery


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROVIDER_CONFIG = ROOT / "config" / "frontier" / "providers.template.yaml"
DEFAULT_ATTUNEMENT_CONFIG = ROOT / "config" / "attunement" / "operator_profiles.template.yaml"
DEFAULT_SYSTEM_ONE_POLICY = ROOT / "config" / "boundaries" / "system_one_controller_policy.yaml"
DEFAULT_SYSTEM_ONE_TIER_POLICY = ROOT / "config" / "boundaries" / "system_one_tier_policy.yaml"
DEFAULT_AIDEVSPEC_CONFIG = ROOT / "config" / "aiddevspec" / "default.yaml"
DEFAULT_LOCAL_PROVIDER_CONFIG = ROOT / "config" / "local" / "model_adapters.template.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required (pip install pyyaml).") from exc

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected YAML mapping in {path}")
    return data


def _find_by_key(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for item in items:
        if isinstance(item, dict) and item.get("key") == key:
            return item
    raise RuntimeError(f"Key {key!r} not found.")


@dataclass
class ServiceConfig:
    provider_config_path: Path
    attunement_config_path: Path
    system_one_policy_path: Path
    system_one_tier_policy_path: Path = DEFAULT_SYSTEM_ONE_TIER_POLICY
    aiddevspec_config_path: Path = DEFAULT_AIDEVSPEC_CONFIG
    local_provider_config_path: Path = DEFAULT_LOCAL_PROVIDER_CONFIG


class DecisionService:
    def __init__(self, cfg: ServiceConfig):
        self.cfg = cfg
        self.aiddevspec = self._load_aiddevspec()
        self.local_provider_config = self._load_local_provider_config()

    def _load_aiddevspec(self) -> dict[str, Any]:
        if not self.cfg.aiddevspec_config_path.exists():
            return {"profile": {"name": "swag-system-one-default"}, "quality_gates": {}}
        return _load_yaml(self.cfg.aiddevspec_config_path)

    def _load_local_provider_config(self) -> dict[str, Any]:
        if not self.cfg.local_provider_config_path.exists():
            return {"providers": []}
        return _load_yaml(self.cfg.local_provider_config_path)

    def provider_status(self) -> dict[str, Any]:
        provider_cfg = _load_yaml(self.cfg.provider_config_path)
        statuses = []
        for key_cfg in provider_cfg.get("api_keys", []):
            if not isinstance(key_cfg, dict):
                continue
            env_var = str(key_cfg.get("env_var", ""))
            statuses.append(
                {
                    "key_id": key_cfg.get("key_id"),
                    "provider": key_cfg.get("provider"),
                    "allowed_model_tiers": key_cfg.get("allowed_model_tiers", []),
                    "env_var": env_var,
                    "env_present": bool(env_var and os.environ.get(env_var)),
                    "usage_policy": key_cfg.get("usage_policy", {}),
                }
            )
        return {
            "provider_config": str(self.cfg.provider_config_path),
            "api_keys": statuses,
            "aiddevspec": {
                "name": self.aiddevspec.get("profile", {}).get("name", "swag-system-one-default"),
                "default_model_tier": self.aiddevspec.get("llm_targets", {}).get("default_tier", "14b"),
            },
        }

    def local_provider_status(self) -> dict[str, Any]:
        providers = []
        for entry in self.local_provider_config.get("providers", []):
            if not isinstance(entry, dict):
                continue
            endpoint_env = str(entry.get("endpoint_env", ""))
            key_env = str(entry.get("api_key_env", ""))
            providers.append(
                {
                    "key": entry.get("key"),
                    "label": entry.get("label"),
                    "provider_type": entry.get("provider_type"),
                    "endpoint_env": endpoint_env,
                    "endpoint_present": bool(endpoint_env and os.environ.get(endpoint_env)),
                    "api_key_env": key_env,
                    "api_key_present": bool(key_env and os.environ.get(key_env)),
                    "default_models": entry.get("default_models", []),
                    "usage_policy": entry.get("usage_policy", {}),
                }
            )
        return {
            "provider_config": str(self.cfg.local_provider_config_path),
            "providers": providers,
        }

    def _load_system_one_policy(self) -> dict[str, Any]:
        if not self.cfg.system_one_policy_path.exists():
            return {"policy": {"main_question_threshold": {"min": 50, "max": 75}}}
        return _load_yaml(self.cfg.system_one_policy_path)

    def _load_system_one_tier_policy(self) -> dict[str, Any]:
        if not self.cfg.system_one_tier_policy_path.exists():
            return {
                "policy": {
                    "controller_tier_strategy": {
                        "default_tier": "14b",
                        "fallback_tier": "7b",
                        "escalation_tier": "27-28b",
                    },
                    "low_cost_signals": {"budget_modes": ["low", "constrained"], "subscription_tiers": []},
                    "escalation_signals": {"boolean_flags": ["requires_deep_reasoning"], "intent_keywords": []},
                    "fallback_order": {"14b": ["7b", "27-28b"]},
                }
            }
        return _load_yaml(self.cfg.system_one_tier_policy_path)

    def _select_model_tier(self, payload: dict[str, Any]) -> tuple[str, str]:
        explicit_tier = payload.get("model_tier")
        if isinstance(explicit_tier, str) and explicit_tier.strip():
            return str(explicit_tier).strip(), "explicit_payload"

        policy_cfg = self._load_system_one_tier_policy()
        policy = policy_cfg.get("policy", {}) if isinstance(policy_cfg, dict) else {}
        strategy = policy.get("controller_tier_strategy", {}) if isinstance(policy, dict) else {}
        low_cost = policy.get("low_cost_signals", {}) if isinstance(policy, dict) else {}
        escalation = policy.get("escalation_signals", {}) if isinstance(policy, dict) else {}

        default_tier = str(strategy.get("default_tier", "14b"))
        fallback_tier = str(strategy.get("fallback_tier", "7b"))
        escalation_tier = str(strategy.get("escalation_tier", "27-28b"))

        budget_mode = str(payload.get("budget_mode", "")).strip().lower()
        subscription_tier = str(payload.get("subscription_tier", "")).strip().lower()
        intent_text = str(payload.get("intent_text", "")).lower()
        context_chars_raw = payload.get("context_chars", len(intent_text))
        if isinstance(context_chars_raw, int):
            context_chars = context_chars_raw
        elif isinstance(context_chars_raw, str) and context_chars_raw.strip().isdigit():
            context_chars = int(context_chars_raw.strip())
        else:
            context_chars = len(intent_text)

        low_budget_modes = [str(x).lower() for x in low_cost.get("budget_modes", []) if isinstance(x, str)]
        low_sub_tiers = [str(x).lower() for x in low_cost.get("subscription_tiers", []) if isinstance(x, str)]
        low_flags = [str(x) for x in low_cost.get("boolean_flags", []) if isinstance(x, str)]
        for flag in low_flags:
            if bool(payload.get(flag)):
                return fallback_tier, f"low_cost_flag:{flag}"
        if budget_mode and budget_mode in low_budget_modes:
            return fallback_tier, f"low_cost_budget_mode:{budget_mode}"
        if subscription_tier and subscription_tier in low_sub_tiers:
            return fallback_tier, f"low_cost_subscription_tier:{subscription_tier}"

        escalation_flags = [str(x) for x in escalation.get("boolean_flags", []) if isinstance(x, str)]
        for flag in escalation_flags:
            if bool(payload.get(flag)):
                return escalation_tier, f"escalation_flag:{flag}"
        min_context_chars = int(escalation.get("min_context_chars", 0) or 0)
        if min_context_chars > 0 and context_chars >= min_context_chars:
            return escalation_tier, f"escalation_context_chars:{context_chars}"
        intent_keywords = [str(x).lower() for x in escalation.get("intent_keywords", []) if isinstance(x, str)]
        for keyword in intent_keywords:
            if keyword and keyword in intent_text:
                return escalation_tier, f"escalation_keyword:{keyword}"

        return default_tier, "default_policy"

    def _build_decision_matrix(self, composed: dict[str, Any]) -> dict[str, Any]:
        policy_cfg = self._load_system_one_policy()
        policy = policy_cfg.get("policy", {}) if isinstance(policy_cfg, dict) else {}
        threshold = policy.get("main_question_threshold", {}) if isinstance(policy, dict) else {}
        min_main = int(threshold.get("min", 50))
        max_main = int(threshold.get("max", 75))
        weights = policy.get("mesh_weights", {}) if isinstance(policy, dict) else {}
        w_main = float(weights.get("main", 0.5))
        w_stack = float(weights.get("stack", 0.3))
        w_domain = float(weights.get("domain", 0.2))
        include_ids = bool(
            ((policy.get("decision_matrix") or {}).get("include_question_ids_by_bucket", True))
            if isinstance(policy, dict)
            else True
        )

        questions = [q for q in composed.get("questions", []) if isinstance(q, dict)]
        shared_q = [q for q in questions if q.get("kind") == "shared"]
        stack_q = [q for q in questions if q.get("kind") == "stack"]
        domain_q = [q for q in questions if q.get("kind") == "domain"]

        main_count = len(shared_q)
        within_band = min_main <= main_count <= max_main

        def count_by(items: list[dict[str, Any]], key_name: str) -> dict[str, int]:
            out: dict[str, int] = {}
            for item in items:
                key = str(item.get(key_name, "unknown"))
                out[key] = out.get(key, 0) + 1
            return out

        def section_counts(items: list[dict[str, Any]]) -> dict[str, int]:
            out: dict[str, int] = {}
            for item in items:
                key = str(item.get("section", "unknown"))
                out[key] = out.get(key, 0) + 1
            return out

        stack_by_stack = count_by(stack_q, "stack")
        domain_by_domain = count_by(domain_q, "domain")
        main_by_section = section_counts(shared_q)

        stack_cell_counts: dict[str, dict[str, int]] = {}
        for item in stack_q:
            stack = str(item.get("stack", "unknown"))
            sec = str(item.get("section", "unknown"))
            if stack not in stack_cell_counts:
                stack_cell_counts[stack] = {}
            stack_cell_counts[stack][sec] = stack_cell_counts[stack].get(sec, 0) + 1

        domain_cell_counts: dict[str, dict[str, int]] = {}
        for item in domain_q:
            dom = str(item.get("domain", "unknown"))
            sec = str(item.get("section", "unknown"))
            if dom not in domain_cell_counts:
                domain_cell_counts[dom] = {}
            domain_cell_counts[dom][sec] = domain_cell_counts[dom].get(sec, 0) + 1

        score = (
            (1.0 if within_band else 0.0) * w_main
            + (1.0 if len(stack_by_stack) > 0 else 0.0) * w_stack
            + (1.0 if len(domain_by_domain) > 0 else 0.0) * w_domain
        )

        out: dict[str, Any] = {
            "main_question_threshold": {"min": min_main, "max": max_main},
            "main_question_count": main_count,
            "main_threshold_pass": within_band,
            "mesh_score": round(score, 4),
            "weights": {"main": w_main, "stack": w_stack, "domain": w_domain},
            "mesh_counts": {
                "main_by_section": main_by_section,
                "stack_by_stack": stack_by_stack,
                "domain_by_domain": domain_by_domain,
            },
            "mesh_cells": {
                "stack_section_cells": stack_cell_counts,
                "domain_section_cells": domain_cell_counts,
            },
            "summary": (
                "Main-question threshold is within target band."
                if within_band
                else "Main-question threshold is outside target band; adjust gating/overlap policy."
            ),
        }
        if include_ids:
            out["question_ids_by_bucket"] = {
                "main": [str(q.get("id")) for q in shared_q if q.get("id")],
                "stack": [str(q.get("id")) for q in stack_q if q.get("id")],
                "domain": [str(q.get("id")) for q in domain_q if q.get("id")],
            }
        return out

    def _resolve_route(
        self,
        model_tier: str,
        attunement_profile: str,
        route_profile_override: str | None,
    ) -> dict[str, Any]:
        provider_cfg = _load_yaml(self.cfg.provider_config_path)
        attunement_cfg = _load_yaml(self.cfg.attunement_config_path)

        profiles = [p for p in attunement_cfg.get("profiles", []) if isinstance(p, dict)]
        attn = _find_by_key(profiles, attunement_profile)
        default_route = (
            (attn.get("execution_policy") or {}).get("route_profile")
            if isinstance(attn.get("execution_policy"), dict)
            else None
        )

        def normalize_route_key(value: str | None) -> str:
            raw = (value or "").strip()
            if not raw:
                return str(default_route or "default_frontier_eval")
            lowered = raw.lower()
            if lowered in {"standard", "default", "default_route", "default_frontier_eval"}:
                return "default_frontier_eval"
            return raw

        route_key = normalize_route_key(route_profile_override or str(default_route or ""))
        routing_profiles = [r for r in provider_cfg.get("routing_profiles", []) if isinstance(r, dict)]
        if route_key not in {str(r.get("key")) for r in routing_profiles}:
            route_key = "default_frontier_eval"
        route = _find_by_key(routing_profiles, route_key)

        tier_route = (
            (route.get("model_tier_routes") or {}).get(model_tier)
            if isinstance(route.get("model_tier_routes"), dict)
            else None
        )
        if not isinstance(tier_route, dict):
            raise RuntimeError(f"No route for model tier {model_tier!r} in route profile {route_key!r}.")

        key_index: dict[str, dict[str, Any]] = {}
        for key_cfg in provider_cfg.get("api_keys", []):
            if isinstance(key_cfg, dict) and isinstance(key_cfg.get("key_id"), str):
                key_index[str(key_cfg["key_id"])] = key_cfg

        pool = []
        for key_id in tier_route.get("key_pool", []):
            if not isinstance(key_id, str):
                continue
            key_cfg = key_index.get(key_id)
            if not key_cfg:
                continue
            env_var = str(key_cfg.get("env_var", ""))
            pool.append(
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

        return {
            "attunement_profile": attunement_profile,
            "route_profile": route_key,
            "route": tier_route,
            "key_pool": pool,
        }

    def _choose_key(self, route_info: dict[str, Any]) -> dict[str, Any]:
        for key_info in route_info.get("key_pool", []):
            if key_info.get("env_present"):
                return key_info
        raise RuntimeError("No configured API key env var is present for selected model tier route.")

    def _call_frontier(self, key_info: dict[str, Any], model: str, prompt: str) -> dict[str, Any]:
        provider = str(key_info.get("provider"))
        api_key = os.environ.get(str(key_info.get("env_var", "")), "")
        if not api_key:
            raise RuntimeError(f"Missing API key in env var {key_info.get('env_var')}.")

        if provider == "xai":
            base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
            url = f"{base.rstrip('/')}/chat/completions"
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are SWAG decision model. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            auth_header = f"Bearer {api_key}"
        elif provider == "openai":
            base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            url = f"{base.rstrip('/')}/chat/completions"
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are SWAG decision model. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            auth_header = f"Bearer {api_key}"
        elif provider == "anthropic":
            base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            url = f"{base.rstrip('/')}/v1/messages"
            body = {
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
                "system": "You are SWAG decision model. Return strict JSON only.",
            }
            auth_header = f"Bearer {api_key}"
        elif provider == "google":
            base = os.environ.get("GOOGLE_GENAI_BASE_URL", "https://generativelanguage.googleapis.com")
            url = f"{base.rstrip('/')}/v1beta/models/{model}:generateContent?key={api_key}"
            body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.0},
            }
            auth_header = None
        elif provider == "openrouter":
            base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            url = f"{base.rstrip('/')}/chat/completions"
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are SWAG decision model. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            auth_header = f"******"
        elif provider == "azure_openai":
            base = os.environ.get("AZURE_OPENAI_BASE_URL", "")
            if not base:
                raise RuntimeError("Missing AZURE_OPENAI_BASE_URL for azure_openai provider.")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01")
            deployment = model
            url = (
                f"{base.rstrip('/')}/openai/deployments/{deployment}"
                f"/chat/completions?api-version={api_version}"
            )
            body = {
                "messages": [
                    {"role": "system", "content": "You are SWAG decision model. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            auth_header = None
        else:
            raise RuntimeError(
                f"Provider {provider!r} execution is not implemented in this service yet. "
                "Use xai, openai, anthropic, google, openrouter, azure_openai, or run dry-run."
            )

        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
        if provider == "azure_openai":
            headers["api-key"] = api_key
        if provider == "openrouter":
            headers["HTTP-Referer"] = os.environ.get("SWAG_OPENROUTER_REFERER", "https://swag.local")
            headers["X-Title"] = os.environ.get("SWAG_OPENROUTER_APP_NAME", "SWAG Decision Service")

        req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Provider HTTP error {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Provider connection error: {exc}") from exc

        return payload

    def _call_local_provider(self, provider_name: str, model: str, prompt: str) -> dict[str, Any]:
        provider_cfg = None
        for entry in self.local_provider_config.get("providers", []):
            if isinstance(entry, dict) and entry.get("key") == provider_name:
                provider_cfg = entry
                break
        if provider_cfg is None:
            raise RuntimeError(f"No configured local model adapter named {provider_name!r}.")

        base = os.environ.get(str(provider_cfg.get("endpoint_env", "LOCAL_OPENAI_BASE_URL")), "http://127.0.0.1:11434/v1")
        api_key = os.environ.get(str(provider_cfg.get("api_key_env", "LOCAL_OPENAI_API_KEY")), "")

        url = f"{base.rstrip('/')}/chat/completions"
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are SWAG local decision model. Return strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Local provider HTTP error {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Local provider connection error: {exc}") from exc

        return payload

    def _extract_selected_ids(self, payload: dict[str, Any]) -> list[str]:
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            message = first.get("message", {}) if isinstance(first, dict) else {}
            content = message.get("content")
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        ids = parsed.get("selected_question_ids", [])
                        if isinstance(ids, list):
                            return [str(item) for item in ids]
                except json.JSONDecodeError:
                    pass
        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            for key in ("content", "parts"):
                value = first.get(key)
                if isinstance(value, list):
                    for part in value:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str):
                                try:
                                    parsed = json.loads(text)
                                    if isinstance(parsed, dict):
                                        ids = parsed.get("selected_question_ids", [])
                                        if isinstance(ids, list):
                                            return [str(item) for item in ids]
                                except json.JSONDecodeError:
                                    pass
        return []

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        repo = Path(str(payload.get("repo", ROOT))).resolve()
        maturity = str(payload.get("maturity", "growing"))
        intent_text = str(payload.get("intent_text", ""))
        model_tier, model_tier_reason = self._select_model_tier(payload)
        attunement_profile = str(payload.get("attunement_profile", "default_rollout"))
        route_profile = payload.get("route_profile")
        execute_frontier = bool(payload.get("execute_frontier", False))
        execute_local = bool(payload.get("execute_local", False))
        include_overlaps = bool(payload.get("include_overlaps", False))
        explicit_domains = list(payload.get("domains", []))

        composed = compose_battery(
            repo=repo,
            maturity=maturity,
            has_test_harness=bool(payload.get("has_test_harness", True)),
            unbounded_data_path=bool(payload.get("unbounded_data_path", False)),
            intent_text=intent_text,
            explicit_domains=explicit_domains,
            primary_stack=payload.get("primary_stack"),
            include_overlaps=include_overlaps,
        )

        selected_ids = [
            str(q.get("id")) for q in composed.get("questions", []) if isinstance(q, dict) and q.get("id")
        ]
        route_info = self._resolve_route(
            model_tier=model_tier,
            attunement_profile=attunement_profile,
            route_profile_override=str(route_profile) if route_profile else None,
        )
        tier_policy_cfg = self._load_system_one_tier_policy()
        tier_policy = tier_policy_cfg.get("policy", {}) if isinstance(tier_policy_cfg, dict) else {}
        fallback_order_cfg = tier_policy.get("fallback_order", {}) if isinstance(tier_policy, dict) else {}
        fallback_order = (
            fallback_order_cfg.get(model_tier, [])
            if isinstance(fallback_order_cfg, dict)
            else []
        )

        response: dict[str, Any] = {
            "aiddevspec": {
                "name": self.aiddevspec.get("profile", {}).get("name", "swag-system-one-default"),
                "maturity_default": self.aiddevspec.get("profile", {}).get("default_maturity", maturity),
                "default_model_tier": self.aiddevspec.get("llm_targets", {}).get("default_tier", model_tier),
                "quality_gates": self.aiddevspec.get("quality_gates", {}),
            },
            "decision_context": {
                "repo": str(repo),
                "maturity": maturity,
                "model_tier": model_tier,
                "model_tier_reason": model_tier_reason,
                "attunement_profile": attunement_profile,
                "route_profile": route_info["route_profile"],
                "execute_frontier": execute_frontier,
                "execute_local": execute_local,
            },
            "routing": composed.get("detected", {}),
            "source_sync": composed.get("source_sync", {}),
            "counts": composed.get("counts", {}),
            "system_one_decision_matrix": self._build_decision_matrix(composed),
            "provider_plan": {
                "model_preferences": route_info["route"].get("model_preferences", []),
                "key_pool": route_info.get("key_pool", []),
                "fallback_order_for_tier": fallback_order if isinstance(fallback_order, list) else [],
            },
            "decision": {
                "selected_question_ids": selected_ids,
                "notes": "dry-run; no model execution requested",
            },
        }

        if execute_local or execute_frontier:
            target_model = None
            provider_call = None
            provider_raw = None
            if execute_local:
                local_cfg = self.local_provider_config.get("providers", [])
                if not local_cfg:
                    raise RuntimeError("No local provider adapters are configured.")
                local_provider = local_cfg[0].get("key", "local_openai_compatible")
                target_model = str((local_cfg[0].get("default_models") or ["qwen2.5-coder-14b-instruct"])[0])
                provider_raw = self._call_local_provider(local_provider, target_model, json.dumps({
                    "task": "Select applicable question ids for this request.",
                    "intent_text": intent_text,
                    "detected_stacks": composed.get("detected", {}).get("selected_stacks", []),
                    "detected_domains": composed.get("detected", {}).get("domains", []),
                    "questions": [
                        {"id": q.get("id"), "text": q.get("text")}
                        for q in composed.get("questions", [])
                    ],
                    "required_output": {"selected_question_ids": ["..."], "notes": "short rationale"},
                }))
                provider_call = {"provider": "local", "provider_key": local_provider, "model": target_model}
            else:
                selected_key = self._choose_key(route_info)
                prefs = route_info["route"].get("model_preferences", [])
                if not prefs:
                    raise RuntimeError("No model preference configured for selected route.")
                target_model = str(prefs[0].get("model"))
                provider_raw = self._call_frontier(selected_key, target_model, json.dumps({
                    "task": "Select applicable question ids for this request.",
                    "intent_text": intent_text,
                    "detected_stacks": composed.get("detected", {}).get("selected_stacks", []),
                    "detected_domains": composed.get("detected", {}).get("domains", []),
                    "questions": [
                        {"id": q.get("id"), "text": q.get("text")}
                        for q in composed.get("questions", [])
                    ],
                    "required_output": {"selected_question_ids": ["..."], "notes": "short rationale"},
                }))
                provider_call = {
                    "provider": selected_key.get("provider"),
                    "key_id": selected_key.get("key_id"),
                    "model": target_model,
                }

            selected_question_ids = self._extract_selected_ids(provider_raw)
            if selected_question_ids:
                response["decision"]["selected_question_ids"] = selected_question_ids
            response["decision"]["notes"] = "model execution complete; structured IDs parsed from provider response"
            response["provider_call"] = provider_call
            response["provider_raw"] = provider_raw

        return response


class Handler(BaseHTTPRequestHandler):
    service: DecisionService | None = None

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path.startswith("/health"):
                self._send(HTTPStatus.OK, {"ok": True, "service": "swag-decision-service"})
                return
            if self.path.startswith("/v1/providers/status"):
                assert self.service is not None
                self._send(HTTPStatus.OK, self.service.provider_status())
                return
            if self.path.startswith("/v1/local/providers/status"):
                assert self.service is not None
                self._send(HTTPStatus.OK, self.service.local_provider_status())
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except Exception as exc:  # pragma: no cover
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/decision":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body or "{}")
            if not isinstance(payload, dict):
                raise RuntimeError("JSON body must be an object.")
            assert self.service is not None
            result = self.service.decide(payload)
            self._send(HTTPStatus.OK, result)
        except Exception as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": str(exc),
                    "trace": traceback.format_exc(limit=3),
                },
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SWAG decision service with frontier and local model routing support."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--provider-config", type=Path, default=DEFAULT_PROVIDER_CONFIG)
    parser.add_argument("--attunement-config", type=Path, default=DEFAULT_ATTUNEMENT_CONFIG)
    parser.add_argument("--system-one-policy", type=Path, default=DEFAULT_SYSTEM_ONE_POLICY)
    parser.add_argument("--system-one-tier-policy", type=Path, default=DEFAULT_SYSTEM_ONE_TIER_POLICY)
    parser.add_argument("--aiddevspec-config", type=Path, default=DEFAULT_AIDEVSPEC_CONFIG)
    parser.add_argument("--local-provider-config", type=Path, default=DEFAULT_LOCAL_PROVIDER_CONFIG)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = ServiceConfig(
        provider_config_path=args.provider_config.resolve(),
        attunement_config_path=args.attunement_config.resolve(),
        system_one_policy_path=args.system_one_policy.resolve(),
        system_one_tier_policy_path=args.system_one_tier_policy.resolve(),
        aiddevspec_config_path=args.aiddevspec_config.resolve(),
        local_provider_config_path=args.local_provider_config.resolve(),
    )
    service = DecisionService(cfg)
    Handler.service = service

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        json.dumps(
            {
                "service": "swag-decision-service",
                "host": args.host,
                "port": args.port,
                "provider_config": str(cfg.provider_config_path),
                "attunement_config": str(cfg.attunement_config_path),
                "system_one_policy": str(cfg.system_one_policy_path),
                "system_one_tier_policy": str(cfg.system_one_tier_policy_path),
                "aiddevspec": str(cfg.aiddevspec_config_path),
                "local_provider_config": str(cfg.local_provider_config_path),
            }
        )
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
