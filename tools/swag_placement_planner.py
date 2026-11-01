#!/usr/bin/env python3
"""Placement planner for DABO/ring execution modes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TOPOLOGY = ROOT / "config" / "training" / "topology.template.yaml"
DEFAULT_POLICY = ROOT / "config" / "training" / "placement_policy.template.yaml"


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


def _check_condition(inputs: dict[str, Any], cond: dict[str, Any]) -> bool:
    field = str(cond.get("field", ""))
    op = str(cond.get("op", ""))
    value = cond.get("value")
    current = inputs.get(field)
    if op == "eq":
        return current == value
    if op == "lte":
        try:
            return float(current) <= float(value)
        except (TypeError, ValueError):
            return False
    if op == "gte":
        try:
            return float(current) >= float(value)
        except (TypeError, ValueError):
            return False
    raise RuntimeError(f"Unsupported op {op!r} in placement policy.")


def _rule_matches(inputs: dict[str, Any], rule: dict[str, Any]) -> bool:
    when = rule.get("when", {})
    if not isinstance(when, dict):
        return False
    all_conditions = when.get("all", [])
    if not isinstance(all_conditions, list):
        return False
    for cond in all_conditions:
        if not isinstance(cond, dict):
            return False
        if not _check_condition(inputs, cond):
            return False
    return True


def plan_placement(
    topology_path: Path,
    policy_path: Path,
    override_mode: str | None,
) -> dict[str, Any]:
    topology = _load_yaml(topology_path)
    policy_doc = _load_yaml(policy_path)

    inputs = policy_doc.get("inputs", {})
    if not isinstance(inputs, dict):
        raise RuntimeError("placement policy inputs must be a mapping.")
    policy = policy_doc.get("policy", {})
    if not isinstance(policy, dict):
        raise RuntimeError("placement policy policy must be a mapping.")
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        raise RuntimeError("placement policy rules must be a list.")

    mode_key = None
    matched_rule = None
    if override_mode:
        mode_key = override_mode
        matched_rule = {"key": "manual_override", "rationale": "Mode selected by override flag."}
    else:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if _rule_matches(inputs, rule):
                mode_key = str(rule.get("choose_mode", ""))
                matched_rule = {"key": rule.get("key"), "rationale": rule.get("rationale", "")}
                break

    if not mode_key:
        defaults = policy.get("defaults", {})
        if not isinstance(defaults, dict):
            raise RuntimeError("placement policy defaults must be a mapping.")
        mode_key = str(defaults.get("preferred_mode", "split_dabo_ring"))
        matched_rule = {"key": "default", "rationale": "No explicit rule matched; using default mode."}

    modes = topology.get("modes", [])
    if not isinstance(modes, list):
        raise RuntimeError("topology modes must be a list.")
    selected_mode = None
    for mode in modes:
        if isinstance(mode, dict) and str(mode.get("key")) == mode_key:
            selected_mode = mode
            break
    if selected_mode is None:
        raise RuntimeError(f"Requested mode {mode_key!r} not found in topology file.")

    sites = topology.get("sites", [])
    if not isinstance(sites, list):
        sites = []

    return {
        "topology_path": str(topology_path),
        "policy_path": str(policy_path),
        "inputs": inputs,
        "selected_mode": mode_key,
        "matched_rule": matched_rule,
        "workflow": selected_mode.get("workflow", {}),
        "facts": policy_doc.get("best_practice_facts", []),
        "sites": sites,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DABO/ring workload placement plan.")
    parser.add_argument("--topology", type=Path, default=DEFAULT_TOPOLOGY)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--mode", default=None, help="Optional override mode (split_dabo_ring or ring_only).")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = plan_placement(
        topology_path=_resolve(str(args.topology)),
        policy_path=_resolve(str(args.policy)),
        override_mode=str(args.mode) if args.mode else None,
    )
    print(json.dumps(plan, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
