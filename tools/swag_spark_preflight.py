#!/usr/bin/env python3
"""Spark ring preflight checker for SWAG distributed training."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "training" / "spark_preflight.template.yaml"


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


def _run_local(cmd: list[str], timeout_sec: int) -> tuple[int, str, str]:
    cp = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout_sec)  # noqa: S603
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def _run_remote(host: str, user: str, timeout_sec: int, strict: str, remote_cmd: str) -> tuple[int, str, str]:
    ssh_cmd = [
        "ssh",
        "-o",
        f"ConnectTimeout={timeout_sec}",
        "-o",
        f"StrictHostKeyChecking={strict}",
        f"{user}@{host}",
        remote_cmd,
    ]
    return _run_local(ssh_cmd, timeout_sec + 5)


def _ok(name: str, detail: Any) -> dict[str, Any]:
    return {"name": name, "ok": True, "detail": detail}


def _bad(name: str, detail: Any) -> dict[str, Any]:
    return {"name": name, "ok": False, "detail": detail}


def run_preflight(config_path: Path, dry_run: bool) -> dict[str, Any]:
    cfg = _load_yaml(config_path)
    enabled = bool(cfg.get("enabled", False))
    ssh_cfg = cfg.get("ssh", {})
    pyenv_cfg = cfg.get("python_env", {})
    cluster_cfg = cfg.get("cluster", {})
    checks_cfg = cfg.get("checks", {})
    if (
        not isinstance(ssh_cfg, dict)
        or not isinstance(pyenv_cfg, dict)
        or not isinstance(cluster_cfg, dict)
        or not isinstance(checks_cfg, dict)
    ):
        raise RuntimeError("Invalid config: ssh/python_env/cluster/checks must be mappings.")

    user = str(ssh_cfg.get("user", "swag"))
    timeout_sec = int(ssh_cfg.get("connect_timeout_sec", 8))
    strict = str(ssh_cfg.get("strict_host_key_checking", "accept-new"))
    activate_script = str(pyenv_cfg.get("activate_script", "")).strip()
    control_host = str(cluster_cfg.get("control_host", "spark-01"))
    ring_nodes = cluster_cfg.get("ring_nodes", [])
    if not isinstance(ring_nodes, list) or not ring_nodes:
        raise RuntimeError("cluster.ring_nodes must be a non-empty list")
    ring_nodes = [str(node) for node in ring_nodes]

    require_commands = checks_cfg.get("require_commands", [])
    require_paths = checks_cfg.get("require_paths", [])
    python_imports = checks_cfg.get("python_imports", [])
    require_env_vars = checks_cfg.get("require_env_vars", [])
    for field, value in (
        ("require_commands", require_commands),
        ("require_paths", require_paths),
        ("python_imports", python_imports),
        ("require_env_vars", require_env_vars),
    ):
        if not isinstance(value, list):
            raise RuntimeError(f"checks.{field} must be a list")

    checks: list[dict[str, Any]] = []
    if not enabled:
        checks.append(
            _bad(
                "preflight_enabled",
                "Preflight is disabled in config. Set enabled: true to run live checks.",
            )
        )
        return {
            "config": str(config_path.resolve()),
            "dry_run": dry_run,
            "enabled": enabled,
            "status": "skipped",
            "control_host": control_host,
            "nodes": ring_nodes,
            "checks": checks,
            "overall_pass": True,
        }

    if dry_run:
        checks.append(
            _ok(
                "dry_run",
                {
                    "control_host": control_host,
                    "nodes": ring_nodes,
                    "commands_checked": require_commands,
                    "paths_checked": require_paths,
                    "imports_checked": python_imports,
                },
            )
        )
        return {
            "config": str(config_path.resolve()),
            "dry_run": dry_run,
            "enabled": enabled,
            "status": "dry_run",
            "control_host": control_host,
            "nodes": ring_nodes,
            "checks": checks,
            "overall_pass": True,
        }

    rc, out, err = _run_remote(control_host, user, timeout_sec, strict, "echo SWAG_PRECHECK_OK")
    if rc == 0 and "SWAG_PRECHECK_OK" in out:
        checks.append(_ok("control_host_ssh", {"host": control_host, "user": user}))
    else:
        checks.append(_bad("control_host_ssh", {"host": control_host, "stderr": err, "stdout": out}))

    for node in ring_nodes:
        rc, out, err = _run_remote(node, user, timeout_sec, strict, "hostname")
        if rc == 0:
            checks.append(_ok("node_reachable", {"node": node, "hostname": out}))
        else:
            checks.append(_bad("node_reachable", {"node": node, "stderr": err}))

    for cmd in require_commands:
        check_cmd = f"command -v {shlex.quote(str(cmd))} >/dev/null && echo OK || echo MISSING"
        remote_cmd = f". {shlex.quote(activate_script)} >/dev/null 2>&1; {check_cmd}" if activate_script else check_cmd
        rc, out, err = _run_remote(control_host, user, timeout_sec, strict, remote_cmd)
        if rc == 0 and "OK" in out:
            checks.append(_ok("command_available", {"command": cmd, "host": control_host}))
        else:
            checks.append(_bad("command_available", {"command": cmd, "host": control_host, "stdout": out, "stderr": err}))

    for path in require_paths:
        remote_cmd = f"test -e {shlex.quote(str(path))} && echo OK || echo MISSING"
        rc, out, err = _run_remote(control_host, user, timeout_sec, strict, remote_cmd)
        if rc == 0 and "OK" in out:
            checks.append(_ok("path_exists", {"path": path, "host": control_host}))
        else:
            checks.append(_bad("path_exists", {"path": path, "host": control_host, "stdout": out, "stderr": err}))

    if python_imports:
        imports_expr = "; ".join([f"import {name}" for name in python_imports])
        python_cmd = "python3 -c " + shlex.quote(f"{imports_expr}; print('OK_IMPORTS')")
        remote_cmd = f". {shlex.quote(activate_script)} >/dev/null 2>&1; {python_cmd}" if activate_script else python_cmd
        rc, out, err = _run_remote(control_host, user, timeout_sec, strict, remote_cmd)
        if rc == 0 and "OK_IMPORTS" in out:
            checks.append(_ok("python_imports", {"imports": python_imports, "host": control_host}))
        else:
            checks.append(_bad("python_imports", {"imports": python_imports, "host": control_host, "stdout": out, "stderr": err}))

    for env_name in require_env_vars:
        remote_cmd = f"if [ -n \"${{{env_name}:-}}\" ]; then echo SET; else echo MISSING; fi"
        rc, out, err = _run_remote(control_host, user, timeout_sec, strict, remote_cmd)
        if rc == 0 and "SET" in out:
            checks.append(_ok("env_present", {"name": env_name, "host": control_host}))
        else:
            checks.append(_bad("env_present", {"name": env_name, "host": control_host, "stdout": out, "stderr": err}))

    overall_pass = all(bool(item.get("ok")) for item in checks)
    return {
        "config": str(config_path.resolve()),
        "dry_run": dry_run,
        "enabled": enabled,
        "status": "completed",
        "control_host": control_host,
        "nodes": ring_nodes,
        "checks": checks,
        "overall_pass": overall_pass,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Spark ring readiness preflight checks.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_preflight(_resolve(str(args.config)), dry_run=bool(args.dry_run))
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0 if result.get("overall_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
