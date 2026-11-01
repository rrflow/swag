#!/usr/bin/env python3
"""Simple setup/install helper for SWAG.

This makes SWAG easy to stand up for vibe coding workflows and local/hosted use:
- validates dependencies
- creates .env.example
- creates runtime compatibility config
- outputs a short install/run checklist
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_env_example(project_name: str) -> str:
    return f"""# SWAG env example for {project_name}
# Copy this to .env and fill in your real values.

# Core runtime
SWAG_PROJECT_NAME={project_name}
SWAG_RUNTIME_MODE=self_hosted
SWAG_PROJECT_MODE=isolated
SWAG_PARALLEL_RRFLOW=true
SWAG_CONFIGURABLE_RUNTIME=true

# Frontier providers
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace_with_your_key
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_API_KEY=replace_with_your_key
XAI_BASE_URL=https://api.x.ai/v1
XAI_API_KEY=replace_with_your_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=replace_with_your_key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments
AZURE_OPENAI_API_KEY=replace_with_your_key

# Local/self-hosted adapters
LOCAL_OPENAI_BASE_URL=http://localhost:8000/v1
LOCAL_OPENAI_API_KEY=local-dev-key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=local-dev-key

# Provider status / controller routing
SWAG_XAI_KEY_SPARK_14B_A=replace_with_your_key
SWAG_XAI_KEY_SPARK_27_28B_A=replace_with_your_key
SWAG_OPENROUTER_KEY_A=replace_with_your_key
SWAG_AZURE_OPENAI_KEY_14B_A=replace_with_your_key
"""


def _render_setup_summary(project_name: str) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "quickstart": [
            "python -m pip install pyyaml requests",
            "python tools\\swag_runtime_bootstrap.py --pretty",
            "python tools\\boundary_controller.py --pretty --intent-text \"secure AI app architecture\"",
            "python tools\\controller_model_experiment.py --pretty --emit-promotion-scorecard --tier-metrics-file .\\files\\controller_experiments\\tier_metrics.spark_latest.json",
            "python tools\\swag_mcp_server.py",
        ],
        "core_files": [
            "rrflow.sync.yaml",
            "config/runtime/global_defaults.template.yaml",
            "config/runtime/agent_compatibility.template.yaml",
            "tools/swag_mcp_server.py",
            "tools/swag_runtime_bootstrap.py",
            "tools/controller_model_experiment.py",
        ],
    }


def _check_dependencies() -> dict[str, Any]:
    missing: list[str] = []
    for module in ["yaml", "requests"]:
        try:
            __import__(module)
        except Exception:
            missing.append(module)
    return {"missing": missing, "ok": not missing}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="Install/setup helper for SWAG runtime and compatibility config.")
    parser.add_argument("--repo", type=Path, default=ROOT, help="Project root to install into.")
    parser.add_argument("--project-name", default="swag", help="Project name used in env defaults.")
    parser.add_argument("--write-env", action="store_true", help="Create .env.example in the repo root.")
    parser.add_argument("--write-agent-config", action="store_true", help="Create the agent compatibility template.")
    parser.add_argument("--check", action="store_true", help="Check that required Python dependencies are installed.")
    parser.add_argument("--dry-run", action="store_true", help="Print the actions without writing files.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result: dict[str, Any] = {"project_name": args.project_name}

    if args.check:
        result["dependency_check"] = _check_dependencies()

    env_path = args.repo / ".env.example"
    compat_path = args.repo / "config" / "runtime" / "agent_compatibility.template.yaml"
    if args.write_env or args.write_agent_config or args.dry_run:
        result["planned_actions"] = []
        if args.write_env or args.dry_run:
            result["planned_actions"].append({
                "action": "write_env_example",
                "path": str(env_path),
                "content": _render_env_example(args.project_name),
            })
        if args.write_agent_config or args.dry_run:
            result["planned_actions"].append({
                "action": "write_agent_compatibility",
                "path": str(compat_path),
                "content": "template: config/runtime/agent_compatibility.template.yaml",
            })

    if not args.dry_run:
        if args.write_env:
            _write_file(env_path, _render_env_example(args.project_name))
            result["env_example_written"] = str(env_path)
        if args.write_agent_config:
            compat_template = ROOT / "config" / "runtime" / "agent_compatibility.template.yaml"
            _write_file(compat_path, compat_template.read_text(encoding="utf-8"))
            result["agent_config_written"] = str(compat_path)

    result["summary"] = _render_setup_summary(args.project_name)
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
