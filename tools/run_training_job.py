#!/usr/bin/env python3
"""Inspect historical SWAG runbooks without executing unadmitted commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swag_training_policy import LEGACY_TRAINING_RETIRED


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", type=Path, required=True, help="Path to runbook.json.")
    parser.add_argument(
        "--step",
        default=None,
        help="Runbook command step key (for example train_lora_distributed or serve_vllm_awq4).",
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="List available runbook command steps and exit.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Retired: execution is refused; omit to inspect historical commands.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.execute:
        raise SystemExit(LEGACY_TRAINING_RETIRED)
    runbook = _load_json(args.runbook.resolve())
    commands = runbook.get("commands", {})
    if not isinstance(commands, dict):
        raise SystemExit("runbook commands section is missing or invalid")

    if args.list_steps:
        for key in sorted(commands.keys()):
            print(key)
        return 0

    if not args.step:
        raise SystemExit("--step is required unless --list-steps is provided.")

    command = commands.get(args.step)
    if not isinstance(command, str) or not command.strip():
        raise SystemExit(f"Command {args.step!r} missing in runbook")

    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
