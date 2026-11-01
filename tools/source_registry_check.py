#!/usr/bin/env python3
"""Validate the canonical source registry.

This is the hard gate that prevents context rot and drift: sources must have
version, owner, last_verified, next_review_due, status, and question bindings.
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

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANON_PATH = ROOT / "config" / "sources" / "official_source_canon.yaml"


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


def validate_registry(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    sources = data.get("sources", []) if isinstance(data, dict) else []
    if not isinstance(sources, list):
        raise SystemExit(f"sources must be a list in {path}")

    errors: list[str] = []
    valid: list[str] = []
    for idx, entry in enumerate(sources):
        if not isinstance(entry, dict):
            errors.append(f"source[{idx}] is not a mapping")
            continue
        key = str(entry.get("key", "")).strip()
        owner = str(entry.get("owner", "")).strip()
        version = str(entry.get("version", "")).strip()
        last_verified = str(entry.get("last_verified", "")).strip()
        next_review_due = str(entry.get("next_review_due", "")).strip()
        status = str(entry.get("status", "")).strip()
        if not key:
            errors.append(f"source[{idx}] missing key")
            continue
        missing = []
        if not owner:
            missing.append("owner")
        if not version:
            missing.append("version")
        if not last_verified:
            missing.append("last_verified")
        if not next_review_due:
            missing.append("next_review_due")
        if not status:
            missing.append("status")
        if not isinstance(entry.get("question_bindings", []), list) or not entry.get("question_bindings"):
            missing.append("question_bindings")
        if missing:
            errors.append(f"{key}: missing {', '.join(missing)}")
        else:
            valid.append(key)

    return {
        "registry": str(path),
        "total_sources": len(sources),
        "valid_sources": valid,
        "error_count": len(errors),
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the canonical source registry used by SWAG.")
    parser.add_argument("--source-registry", type=Path, default=DEFAULT_CANON_PATH, help="Path to the source registry YAML.")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output.")
    return parser.parse_args(argv or sys.argv[1:])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_registry(args.source_registry.resolve())
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
