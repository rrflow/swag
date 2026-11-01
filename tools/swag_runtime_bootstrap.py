#!/usr/bin/env python3
"""Merge global runtime defaults with repo/project RRFlow config.

This keeps SWAG configurable in three scopes:
1. global defaults
2. per-project overrides
3. RRFlow shared sync state

The output is a deterministic effective config that can be consumed by the
controller, MCP integration layer, and deployment tooling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc


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


def _deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    if isinstance(base, list) and isinstance(override, list):
        return list(override)
    return override


def resolve_effective_runtime(
    repo: Path,
    global_config: Path,
    project_config: Path,
) -> dict[str, Any]:
    global_data = _load_yaml(global_config)
    project_data = _load_yaml(project_config)
    if not project_data:
        project_data = {}

    merged = _deep_merge(global_data, project_data)
    if "sync" not in merged and isinstance(project_data.get("sync"), dict):
        merged["sync"] = project_data["sync"]

    runtime_block = merged.get("runtime") if isinstance(merged, dict) else {}
    sync_block = merged.get("sync") if isinstance(merged, dict) else {}
    if isinstance(runtime_block, dict) and isinstance(sync_block, dict):
        runtime_block["rrflow"] = _deep_merge(runtime_block.get("rrflow", {}), sync_block)
        merged["runtime"] = runtime_block

    return {
        "repo": str(repo),
        "schema_version": merged.get("schema_version", 1),
        "runtime": merged.get("runtime", {}),
        "sync": merged.get("sync", {}),
        "mcp": merged.get("mcp", {}),
        "effective_policy": {
            "project_mode": (sync_block or {}).get("project_mode") or (runtime_block or {}).get("rrflow", {}).get("project_mode") or "isolated",
            "parallel_rrflow": bool((runtime_block or {}).get("rrflow", {}).get("parallel_mode", False) or (sync_block or {}).get("parallel_mode", False)),
            "self_hosted": str((runtime_block or {}).get("deployment_mode", "self_hosted")).lower() == "self_hosted",
            "mcp_enabled": bool((merged.get("mcp") or {}).get("enabled", True)),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="Resolve SWAG effective runtime config.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root.")
    parser.add_argument(
        "--global-config",
        type=Path,
        default=Path("config") / "runtime" / "global_defaults.template.yaml",
        help="Global runtime defaults YAML.",
    )
    parser.add_argument(
        "--project-config",
        type=Path,
        default=Path("rrflow.sync.yaml"),
        help="Project RRFlow sync YAML file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for the resolved runtime config JSON.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    effective = resolve_effective_runtime(
        repo=args.repo.resolve(),
        global_config=args.global_config.resolve(),
        project_config=args.project_config.resolve(),
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as fh:
            json.dump(effective, fh, indent=2, ensure_ascii=True)

    print(json.dumps(effective, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
