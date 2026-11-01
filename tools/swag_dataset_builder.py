#!/usr/bin/env python3
"""Build supervised and unsupervised SWAG controller datasets from captured patterns."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML is required (pip install pyyaml).") from exc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPERIMENT_DIR = ROOT / "files" / "controller_experiments"
DEFAULT_SUPERVISED_OUT = ROOT / "files" / "training" / "data" / "swag_supervised.jsonl"
DEFAULT_UNSUPERVISED_OUT = ROOT / "files" / "training" / "data" / "swag_unsupervised.jsonl"
DEFAULT_MANIFEST_OUT = ROOT / "files" / "training" / "manifests" / "swag_dataset_manifest.json"

TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".ts", ".tsx", ".js", ".jsx"}


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


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _chunk_text(text: str, target_chars: int = 1200) -> list[str]:
    clean = text.strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + target_chars)
        segment = clean[start:end].strip()
        if segment:
            chunks.append(segment)
        start = end
    return chunks


def _collect_scenario_batteries(experiment_dir: Path) -> list[dict[str, Any]]:
    if not experiment_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for scenario_dir in sorted(p for p in experiment_dir.iterdir() if p.is_dir()):
        battery_path = scenario_dir / "expected_battery.json"
        if not battery_path.exists():
            continue
        try:
            battery = _load_json(battery_path)
        except json.JSONDecodeError:
            continue
        if not isinstance(battery, dict):
            continue
        questions = battery.get("questions", []) if isinstance(battery.get("questions", []), list) else []
        selected_ids = [str(q.get("id")) for q in questions if isinstance(q, dict) and q.get("id")]
        if not selected_ids:
            continue
        rows.append({
            "scenario_id": scenario_dir.name,
            "battery": battery,
            "selected_ids": selected_ids,
            "intent_text": str(battery.get("input", {}).get("intent_text", "")) if isinstance(battery.get("input", {}), dict) else "",
            "repo": str(battery.get("input", {}).get("repo", ROOT)) if isinstance(battery.get("input", {}), dict) else str(ROOT),
        })
    return rows


def _build_supervised_rows(experiment_dir: Path) -> list[dict[str, Any]]:
    supervised: list[dict[str, Any]] = []
    scenario_rows = _collect_scenario_batteries(experiment_dir)
    for idx, record in enumerate(scenario_rows, start=1):
        scenario_id = record["scenario_id"]
        battery = record["battery"]
        selected_ids = record["selected_ids"]
        route_tier = "27-28b" if len(selected_ids) >= 80 else "14b"
        user_payload = {
            "scenario_id": scenario_id,
            "repo": record["repo"],
            "intent_text": record["intent_text"],
            "task": "Select the minimal boundary question set for this system-one decision context.",
            "maturity": str((battery.get("input") or {}).get("maturity", "growing")),
            "domains": list((battery.get("detected") or {}).get("domains", [])),
            "stacks": list((battery.get("detected") or {}).get("selected_stacks", [])),
            "allowed_question_ids": selected_ids,
            "required_output": {
                "selected_question_ids": ["..."],
                "skipped_question_ids": ["..."],
                "route_target_tier": "14b|27-28b|7b",
                "confidence": 0.0,
                "notes": "short rationale",
            },
        }
        assistant_payload = {
            "selected_question_ids": selected_ids,
            "skipped_question_ids": [],
            "route_target_tier": route_tier,
            "confidence": 0.92,
            "notes": "The battery is already grounded by the controller routing contract and source-sync metadata.",
        }
        supervised.append({
            "record_id": f"sup-{idx:05d}",
            "scenario_id": scenario_id,
            "source_type": "swag_generated_scenarios",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are SWAG System-One controller. Choose the smallest valid boundary question set "
                        "that is required to make a correct decision. Return JSON only."
                    ),
                },
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
                {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
            ],
            "labels": {
                "selected_question_ids": selected_ids,
                "skipped_question_ids": [],
                "route_target_tier": route_tier,
                "confidence": 0.92,
            },
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "maturity": str((battery.get("input") or {}).get("maturity", "growing")),
                "has_test_harness": bool((battery.get("input") or {}).get("has_test_harness", False)),
                "unbounded_data_path": bool((battery.get("input") or {}).get("unbounded_data_path", False)),
                "stacks": list((battery.get("detected") or {}).get("selected_stacks", [])),
                "domains": list((battery.get("detected") or {}).get("domains", [])),
                "source_family": "controller_expected_battery",
            },
        })
    return supervised


def _iter_source_files(include_patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in include_patterns:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
                files.append(path)
    # de-dupe
    unique: list[Path] = []
    seen: set[str] = set()
    for path in files:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _build_unsupervised_rows() -> list[dict[str, Any]]:
    include_patterns = [
        "README.md",
        "config/**/*.yaml",
        "config/**/*.yml",
        "boundaries/**/*.md",
        "tools/*.py",
    ]
    rows: list[dict[str, Any]] = []
    source_files = _iter_source_files(include_patterns)
    for file_path in source_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(text.strip()) < 80:
            continue
        for chunk_index, chunk in enumerate(_chunk_text(text, target_chars=1400), start=1):
            rows.append({
                "record_id": f"uns-{_hash(str(file_path.resolve()) + f'::{chunk_index}')[:12]}",
                "source_type": "project_code_and_history",
                "messages": [
                    {"role": "user", "content": f"Continue from the project context below.\n\n{chunk}"},
                    {"role": "assistant", "content": "Use the project context to preserve the controller contract, source provenance, and decision structure."},
                ],
                "metadata": {
                    "source_file": str(file_path.resolve()),
                    "source_family": "project_history_reference",
                    "chunk_index": chunk_index,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            })
    return rows


def build_dataset(experiment_dir: Path = DEFAULT_EXPERIMENT_DIR) -> dict[str, Any]:
    supervised = _build_supervised_rows(experiment_dir)
    unsupervised = _build_unsupervised_rows()
    supervised_path = DEFAULT_SUPERVISED_OUT
    unsupervised_path = DEFAULT_UNSUPERVISED_OUT
    _write_jsonl(supervised_path, supervised)
    _write_jsonl(unsupervised_path, unsupervised)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(experiment_dir.resolve()),
        "supervised_path": str(supervised_path),
        "unsupervised_path": str(unsupervised_path),
        "counts": {
            "supervised_rows": len(supervised),
            "unsupervised_rows": len(unsupervised),
        },
        "source_breakdown": {
            "controller_expected_battery": len(supervised),
            "project_history_reference": len(unsupervised),
        },
        "quality_gate_summary": {
            "min_supervised_rows": len(supervised) >= 24,
            "min_unsupervised_rows": len(unsupervised) >= 200,
            "min_unique_scenarios": len({row["scenario_id"] for row in supervised}) >= 24,
        },
    }
    DEFAULT_MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_MANIFEST_OUT.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=True)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SWAG supervised + unsupervised training datasets.")
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR, help="Directory containing controller experiment results.")
    parser.add_argument("--supervised-out", type=Path, default=DEFAULT_SUPERVISED_OUT, help="Output .jsonl for supervised training rows.")
    parser.add_argument("--unsupervised-out", type=Path, default=DEFAULT_UNSUPERVISED_OUT, help="Output .jsonl for unsupervised training rows.")
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT, help="Manifest file for the dataset build.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    global DEFAULT_SUPERVISED_OUT, DEFAULT_UNSUPERVISED_OUT, DEFAULT_MANIFEST_OUT
    DEFAULT_SUPERVISED_OUT = args.supervised_out
    DEFAULT_UNSUPERVISED_OUT = args.unsupervised_out
    DEFAULT_MANIFEST_OUT = args.manifest_out
    manifest = build_dataset(args.experiment_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
