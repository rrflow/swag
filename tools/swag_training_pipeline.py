#!/usr/bin/env python3
"""Historical training helpers; unreviewed generation and runbooks are retired."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from swag_training_policy import LEGACY_TRAINING_RETIRED


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PIPELINE_CONFIG = ROOT / "config" / "training" / "pipeline.template.yaml"
BOUNDARY_QUESTION_SETS_DIR = ROOT / "config" / "boundaries" / "question_sets"

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".toml",
    ".ini",
    ".cfg",
}


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


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL in {path}:{line_num}: {exc}") from exc
            if not isinstance(item, dict):
                raise SystemExit(f"Expected object row in {path}:{line_num}")
            rows.append(item)
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")
            count += 1
    return count


def _resolve_path(path_like: str) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else (ROOT / path)


def _is_excluded(path: Path, excluded_roots: list[Path]) -> bool:
    for root in excluded_roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _iter_input_files(includes: list[str], excludes: list[str]) -> list[Path]:
    include_paths = [_resolve_path(item) for item in includes]
    excluded_roots = [_resolve_path(item) for item in excludes]
    files: list[Path] = []
    for include in include_paths:
        if include.is_file():
            if include.suffix.lower() in TEXT_EXTENSIONS and not _is_excluded(include, excluded_roots):
                files.append(include)
            continue
        if include.is_dir():
            for file_path in include.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in TEXT_EXTENSIONS
                    and not _is_excluded(file_path, excluded_roots)
                ):
                    files.append(file_path)
    files.sort()
    return files


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _truncate(value: str, limit: int = 8000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]


def _redact_text(text: str, replacement: str, keep_private_ips: bool) -> tuple[str, dict[str, int]]:
    patterns: list[tuple[str, re.Pattern[str]]] = [
        ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
        ("phone", re.compile(r"\+?\d[\d\-\s()]{7,}\d")),
        ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("bearer", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{16,}\b")),
        ("secret_assignment", re.compile(r"(?i)\b(api[_\-]?key|token|secret|password)\s*[:=]\s*[\"']?([A-Za-z0-9._\-]{8,})")),
        ("github_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
        ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
        ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b")),
    ]
    if keep_private_ips:
        ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        patterns.append(("public_ip", ip_pattern))
    else:
        ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        patterns.append(("ip", ip_pattern))

    counts: dict[str, int] = {}
    output = text
    for key, pattern in patterns:
        output, n = pattern.subn(replacement, output)
        if n:
            counts[key] = counts.get(key, 0) + n
    return output, counts


def build_redacted_corpus(
    includes: list[str],
    excludes: list[str],
    output_file: Path,
    replacement: str,
    keep_private_ips: bool,
) -> dict[str, Any]:
    files = _iter_input_files(includes, excludes)
    rows: list[dict[str, Any]] = []
    total_redactions: dict[str, int] = {}

    for file_path in files:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        redacted, counts = _redact_text(raw, replacement=replacement, keep_private_ips=keep_private_ips)
        for key, value in counts.items():
            total_redactions[key] = total_redactions.get(key, 0) + value
        rows.append(
            {
                "source": str(file_path),
                "sha256": _sha256_text(redacted),
                "char_count": len(redacted),
                "redaction_counts": counts,
                "text": _truncate(redacted),
            }
        )

    row_count = _write_jsonl(output_file, rows)
    return {
        "output_file": str(output_file),
        "files_processed": len(files),
        "rows_written": row_count,
        "total_redactions": total_redactions,
    }


def _scenario_dirs(controller_experiments_dir: Path) -> list[Path]:
    if not controller_experiments_dir.exists():
        return []
    return sorted([p for p in controller_experiments_dir.iterdir() if p.is_dir()])


def _chunk_text(text: str, max_chars: int) -> list[str]:
    clean = text.strip()
    if not clean:
        return []
    if max_chars <= 0:
        return [clean]
    chunks: list[str] = []
    start = 0
    length = len(clean)
    while start < length:
        end = min(length, start + max_chars)
        chunks.append(clean[start:end].strip())
        start = end
    return [c for c in chunks if c]


def _load_question_set_index() -> dict[str, list[dict[str, Any]]]:
    if not BOUNDARY_QUESTION_SETS_DIR.exists():
        return {}
    index: dict[str, list[dict[str, Any]]] = {}
    for file_path in sorted(BOUNDARY_QUESTION_SETS_DIR.glob("*.yaml")):
        data = _load_yaml(file_path)
        questions = [q for q in data.get("questions", []) if isinstance(q, dict) and q.get("id")]
        key = file_path.stem
        index[key] = questions
    return index


def _infer_stack_key_from_reference_file(path: Path) -> str:
    name = path.stem.lower()
    mapping = {
        "stack_nextjs": "nextjs",
        "stack_rust": "rust",
        "stack_go": "go",
        "stack_react": "react",
        "stack_typescript": "typescript",
        "stack_vanilla_js": "vanilla_js",
        "domain_boundaries": "domains",
        "boundary_question_bank": "shared_predicates",
    }
    for marker, key in mapping.items():
        if marker in name:
            return key
    return "shared_predicates"


def _select_question_bundle(
    question_index: dict[str, list[dict[str, Any]]],
    stack_key: str,
    min_selected_ids: int,
    question_preview_limit: int,
) -> tuple[list[str], int, int, list[dict[str, str]]]:
    shared_questions = question_index.get("shared_predicates", [])
    stack_questions = question_index.get(stack_key, [])
    selected_questions = (stack_questions[:min_selected_ids] or shared_questions[:min_selected_ids])
    selected_ids = [str(q.get("id")) for q in selected_questions if q.get("id")]
    citation_count = sum(
        1 for q in selected_questions if isinstance(q.get("citation"), str) and q.get("citation").strip()
    )
    reference_url_count = 0
    for q in selected_questions:
        source = q.get("source")
        if not isinstance(source, dict):
            continue
        reference = source.get("reference")
        if isinstance(reference, str) and reference.lower().startswith(("http://", "https://")):
            reference_url_count += 1
    question_preview = [
        {"id": str(q.get("id")), "text": str(q.get("text"))}
        for q in selected_questions
        if q.get("id") and q.get("text")
    ][:question_preview_limit]
    return selected_ids, citation_count, reference_url_count, question_preview


def _build_project_history_reference_rows(adapter_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    include_patterns_raw = adapter_cfg.get("include", ["boundaries/reference/*.md"])
    include_patterns = (
        [str(x) for x in include_patterns_raw]
        if isinstance(include_patterns_raw, list)
        else [str(include_patterns_raw)]
    )
    max_chunks_per_file = int(adapter_cfg.get("max_chunks_per_file", 4))
    max_chars_per_chunk = int(adapter_cfg.get("max_chars_per_chunk", 1800))
    min_selected_ids = int(adapter_cfg.get("min_selected_question_ids", 8))
    question_preview_limit = int(adapter_cfg.get("question_preview_limit", 6))
    source_family = str(adapter_cfg.get("source_family", "project_history_reference"))
    source_type = str(adapter_cfg.get("source_type", "real_source_adapter"))

    question_index = _load_question_set_index()
    rows: list[dict[str, Any]] = []

    for pattern in include_patterns:
        for source_path in sorted(ROOT.glob(pattern)):
            if not source_path.is_file():
                continue
            stack_key = _infer_stack_key_from_reference_file(source_path)
            selected_ids, citation_count, reference_url_count, question_preview = _select_question_bundle(
                question_index=question_index,
                stack_key=stack_key,
                min_selected_ids=min_selected_ids,
                question_preview_limit=question_preview_limit,
            )

            raw = source_path.read_text(encoding="utf-8", errors="replace")
            chunks = _chunk_text(raw, max_chars=max_chars_per_chunk)[:max_chunks_per_file]
            for idx, chunk in enumerate(chunks, start=1):
                scenario_id = f"realref::{source_path.stem}::chunk{idx:03d}"
                user_payload = {
                    "task": "Use source-grounded evidence to select boundary question IDs for this change context.",
                    "scenario_id": scenario_id,
                    "source_file": str(source_path.resolve()),
                    "source_excerpt": chunk,
                    "source_family": source_family,
                    "primary_stack": stack_key,
                    "detected_stacks": [stack_key],
                    "question_count": len(selected_ids),
                    "question_ids": selected_ids,
                    "question_text_preview": question_preview,
                    "required_output": {
                        "selected_question_ids": ["..."],
                        "notes": "cite relevant evidence from the source excerpt",
                    },
                }
                assistant_payload = {
                    "selected_question_ids": selected_ids,
                    "notes": "Source-grounded initialization from repository reference material.",
                }
                rows.append(
                    {
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are SWAG System-One controller. Return strict JSON with "
                                    "selected_question_ids and concise notes."
                                ),
                            },
                            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
                            {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
                        ],
                        "metadata": {
                            "scenario_id": scenario_id,
                            "question_count": len(selected_ids),
                            "maturity": "mature",
                            "primary_stack": stack_key,
                            "stacks": [stack_key],
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "source_family": source_family,
                            "source_type": source_type,
                            "question_citation_count": citation_count,
                            "question_reference_url_count": reference_url_count,
                            "synthetic_variant": False,
                        },
                    }
                )
    return rows


def _build_structured_real_input_rows(adapter_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    include_patterns_raw = adapter_cfg.get("include", ["config/training/real_sources/*.jsonl"])
    include_patterns = (
        [str(x) for x in include_patterns_raw]
        if isinstance(include_patterns_raw, list)
        else [str(include_patterns_raw)]
    )
    min_selected_ids = int(adapter_cfg.get("min_selected_question_ids", 8))
    question_preview_limit = int(adapter_cfg.get("question_preview_limit", 6))
    variants_per_record = max(1, int(adapter_cfg.get("variants_per_record", 1)))
    variant_focuses_raw = adapter_cfg.get("variant_focuses", [])
    variant_focuses = (
        [str(x).strip() for x in variant_focuses_raw if isinstance(x, str) and str(x).strip()]
        if isinstance(variant_focuses_raw, list)
        else []
    )
    default_source_family = str(adapter_cfg.get("source_family", "structured_real_inputs"))
    source_type = str(adapter_cfg.get("source_type", "real_source_adapter"))

    question_index = _load_question_set_index()
    rows: list[dict[str, Any]] = []
    for pattern in include_patterns:
        for source_path in sorted(ROOT.glob(pattern)):
            if not source_path.is_file():
                continue
            for item in _read_jsonl_objects(source_path):
                scenario_id = str(item.get("scenario_id") or item.get("id") or "")
                intent_text = str(item.get("intent_text") or item.get("summary") or "").strip()
                primary_stack = str(item.get("primary_stack") or item.get("stack") or "shared_predicates").strip()
                if not scenario_id or not intent_text:
                    continue
                domains_raw = item.get("domains", [])
                domains = [str(x) for x in domains_raw if isinstance(x, str)] if isinstance(domains_raw, list) else []
                detected_stacks_raw = item.get("stacks", [])
                detected_stacks = (
                    [str(x) for x in detected_stacks_raw if isinstance(x, str)]
                    if isinstance(detected_stacks_raw, list)
                    else [primary_stack]
                )
                selected_ids_raw = item.get("selected_question_ids", [])
                if isinstance(selected_ids_raw, list) and selected_ids_raw:
                    selected_ids = [str(x) for x in selected_ids_raw if isinstance(x, str) and str(x).strip()]
                    citation_count = int(item.get("question_citation_count", 0) or 0)
                    reference_url_count = int(item.get("question_reference_url_count", 0) or 0)
                    question_preview = []
                else:
                    selected_ids, citation_count, reference_url_count, question_preview = _select_question_bundle(
                        question_index=question_index,
                        stack_key=primary_stack,
                        min_selected_ids=min_selected_ids,
                        question_preview_limit=question_preview_limit,
                    )
                source_family = str(item.get("source_family") or default_source_family)
                notes = str(item.get("notes") or "Structured real-source initialization row.")
                maturity = str(item.get("maturity") or "growing")
                for variant_idx in range(variants_per_record):
                    scenario_variant = scenario_id
                    variant_focus = ""
                    if variants_per_record > 1:
                        scenario_variant = f"{scenario_id}::v{variant_idx + 1:02d}"
                        if variant_focuses:
                            variant_focus = variant_focuses[variant_idx % len(variant_focuses)]
                        else:
                            variant_focus = f"variant-{variant_idx + 1:02d}"
                    user_payload = {
                        "task": "Select applicable boundary question IDs for this request.",
                        "scenario_id": scenario_variant,
                        "intent_text": intent_text,
                        "maturity": maturity,
                        "domains": domains,
                        "primary_stack": primary_stack,
                        "detected_stacks": detected_stacks,
                        "source_family": source_family,
                        "source_record": str(source_path.resolve()),
                        "question_count": len(selected_ids),
                        "question_ids": selected_ids,
                        "question_text_preview": question_preview,
                        "required_output": {
                            "selected_question_ids": ["..."],
                            "notes": "cite relevant evidence from the source record",
                        },
                    }
                    if variant_focus:
                        user_payload["decision_focus"] = variant_focus
                    variant_notes = notes
                    if variant_focus:
                        variant_notes = f"{notes} Focus: {variant_focus}."
                    assistant_payload = {"selected_question_ids": selected_ids, "notes": variant_notes}
                    rows.append(
                        {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are SWAG System-One controller. Return strict JSON with "
                                        "selected_question_ids and concise notes."
                                    ),
                                },
                                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
                                {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
                            ],
                            "metadata": {
                                "scenario_id": scenario_variant,
                                "question_count": len(selected_ids),
                                "maturity": maturity,
                                "primary_stack": primary_stack,
                                "stacks": detected_stacks,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "source_family": source_family,
                                "source_type": source_type,
                                "question_citation_count": citation_count,
                                "question_reference_url_count": reference_url_count,
                                "synthetic_variant": False,
                                "record_variant_index": variant_idx + 1,
                            },
                        }
                    )
    return rows


def _build_incident_support_rows(adapter_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    include_patterns_raw = adapter_cfg.get("include", ["config/training/real_sources/incident_support_cases.jsonl"])
    include_patterns = (
        [str(x) for x in include_patterns_raw]
        if isinstance(include_patterns_raw, list)
        else [str(include_patterns_raw)]
    )
    min_selected_ids = int(adapter_cfg.get("min_selected_question_ids", 10))
    question_preview_limit = int(adapter_cfg.get("question_preview_limit", 6))
    variants_per_record = max(1, int(adapter_cfg.get("variants_per_record", 1)))
    variant_focuses_raw = adapter_cfg.get("variant_focuses", [])
    variant_focuses = (
        [str(x).strip() for x in variant_focuses_raw if isinstance(x, str) and str(x).strip()]
        if isinstance(variant_focuses_raw, list)
        else []
    )
    source_family = str(adapter_cfg.get("source_family", "incident_support_transcripts"))
    source_type = str(adapter_cfg.get("source_type", "real_source_adapter"))

    question_index = _load_question_set_index()
    required_fields = [
        "scenario_id",
        "record_type",
        "incident_id",
        "intent_text",
        "primary_stack",
        "maturity",
        "evidence_excerpt",
        "root_cause",
        "corrective_action",
        "confidence",
    ]

    rows: list[dict[str, Any]] = []
    for pattern in include_patterns:
        for source_path in sorted(ROOT.glob(pattern)):
            if not source_path.is_file():
                continue
            for line_item in _read_jsonl_objects(source_path):
                missing = [field for field in required_fields if not str(line_item.get(field, "")).strip()]
                if missing:
                    raise SystemExit(
                        f"Incident/support source row missing required fields in {source_path}: {', '.join(missing)}"
                    )

                scenario_id = str(line_item["scenario_id"]).strip()
                record_type = str(line_item["record_type"]).strip()
                incident_id = str(line_item["incident_id"]).strip()
                intent_text = str(line_item["intent_text"]).strip()
                primary_stack = str(line_item["primary_stack"]).strip()
                maturity = str(line_item["maturity"]).strip()
                evidence_excerpt = str(line_item["evidence_excerpt"]).strip()
                root_cause = str(line_item["root_cause"]).strip()
                corrective_action = str(line_item["corrective_action"]).strip()
                confidence = str(line_item["confidence"]).strip()
                domains_raw = line_item.get("domains", [])
                domains = [str(x) for x in domains_raw if isinstance(x, str)] if isinstance(domains_raw, list) else []
                detected_stacks = [primary_stack]

                selected_ids_raw = line_item.get("selected_question_ids", [])
                if isinstance(selected_ids_raw, list) and selected_ids_raw:
                    selected_ids = [str(x) for x in selected_ids_raw if isinstance(x, str) and str(x).strip()]
                    citation_count = int(line_item.get("question_citation_count", 0) or 0)
                    reference_url_count = int(line_item.get("question_reference_url_count", 0) or 0)
                    question_preview = []
                else:
                    selected_ids, citation_count, reference_url_count, question_preview = _select_question_bundle(
                        question_index=question_index,
                        stack_key=primary_stack,
                        min_selected_ids=min_selected_ids,
                        question_preview_limit=question_preview_limit,
                    )

                for variant_idx in range(variants_per_record):
                    scenario_variant = scenario_id
                    variant_focus = ""
                    if variants_per_record > 1:
                        scenario_variant = f"{scenario_id}::v{variant_idx + 1:02d}"
                        if variant_focuses:
                            variant_focus = variant_focuses[variant_idx % len(variant_focuses)]
                        else:
                            variant_focus = f"variant-{variant_idx + 1:02d}"
                    user_payload = {
                        "task": "Select applicable boundary question IDs for this incident/support context.",
                        "scenario_id": scenario_variant,
                        "incident_id": incident_id,
                        "record_type": record_type,
                        "intent_text": intent_text,
                        "maturity": maturity,
                        "domains": domains,
                        "primary_stack": primary_stack,
                        "detected_stacks": detected_stacks,
                        "source_family": source_family,
                        "source_record": str(source_path.resolve()),
                        "evidence_excerpt": evidence_excerpt,
                        "root_cause": root_cause,
                        "corrective_action": corrective_action,
                        "confidence": confidence,
                        "question_count": len(selected_ids),
                        "question_ids": selected_ids,
                        "question_text_preview": question_preview,
                        "required_output": {
                            "selected_question_ids": ["..."],
                            "notes": "ground selection in evidence and corrective action",
                        },
                    }
                    if variant_focus:
                        user_payload["decision_focus"] = variant_focus
                    variant_notes = "Incident/support grounded initialization row."
                    if variant_focus:
                        variant_notes = f"{variant_notes} Focus: {variant_focus}."
                    assistant_payload = {
                        "selected_question_ids": selected_ids,
                        "notes": variant_notes,
                    }
                    rows.append(
                        {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are SWAG System-One controller. Return strict JSON with "
                                        "selected_question_ids and concise notes."
                                    ),
                                },
                                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
                                {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
                            ],
                            "metadata": {
                                "scenario_id": scenario_variant,
                                "question_count": len(selected_ids),
                                "maturity": maturity,
                                "primary_stack": primary_stack,
                                "stacks": detected_stacks,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "source_family": source_family,
                                "source_type": source_type,
                                "question_citation_count": citation_count,
                                "question_reference_url_count": reference_url_count,
                                "synthetic_variant": False,
                                "record_type": record_type,
                                "incident_id": incident_id,
                                "record_variant_index": variant_idx + 1,
                            },
                        }
                    )
    return rows


def _build_real_source_rows(dataset_generation_cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    adapters_cfg = dataset_generation_cfg.get("real_source_adapters", {})
    if not isinstance(adapters_cfg, dict):
        adapters_cfg = {}

    rows: list[dict[str, Any]] = []
    adapter_stats: dict[str, Any] = {}

    ref_cfg = adapters_cfg.get("project_history_reference", {})
    if isinstance(ref_cfg, dict) and bool(ref_cfg.get("enabled", False)):
        ref_rows = _build_project_history_reference_rows(ref_cfg)
        rows.extend(ref_rows)
        adapter_stats["project_history_reference"] = {
            "enabled": True,
            "rows_written": len(ref_rows),
            "source_family": str(ref_cfg.get("source_family", "project_history_reference")),
        }
    else:
        adapter_stats["project_history_reference"] = {"enabled": False, "rows_written": 0}

    structured_cfg = adapters_cfg.get("structured_real_inputs", {})
    if isinstance(structured_cfg, dict) and bool(structured_cfg.get("enabled", False)):
        structured_rows = _build_structured_real_input_rows(structured_cfg)
        rows.extend(structured_rows)
        adapter_stats["structured_real_inputs"] = {
            "enabled": True,
            "rows_written": len(structured_rows),
            "source_family": str(structured_cfg.get("source_family", "structured_real_inputs")),
        }
    else:
        adapter_stats["structured_real_inputs"] = {"enabled": False, "rows_written": 0}

    official_cfg = adapters_cfg.get("official_best_practice_docs", {})
    if isinstance(official_cfg, dict) and bool(official_cfg.get("enabled", False)):
        official_rows = _build_structured_real_input_rows(official_cfg)
        rows.extend(official_rows)
        adapter_stats["official_best_practice_docs"] = {
            "enabled": True,
            "rows_written": len(official_rows),
            "source_family": str(official_cfg.get("source_family", "official_best_practice_docs")),
        }
    else:
        adapter_stats["official_best_practice_docs"] = {"enabled": False, "rows_written": 0}

    incident_cfg = adapters_cfg.get("incident_support_transcripts", {})
    if isinstance(incident_cfg, dict) and bool(incident_cfg.get("enabled", False)):
        incident_rows = _build_incident_support_rows(incident_cfg)
        rows.extend(incident_rows)
        adapter_stats["incident_support_transcripts"] = {
            "enabled": True,
            "rows_written": len(incident_rows),
            "source_family": str(incident_cfg.get("source_family", "incident_support_transcripts")),
        }
    else:
        adapter_stats["incident_support_transcripts"] = {"enabled": False, "rows_written": 0}

    return rows, adapter_stats


def build_controller_sft_dataset(
    controller_experiments_dir: Path,
    output_file: Path,
    dataset_generation_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raise RuntimeError(LEGACY_TRAINING_RETIRED)


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._\-]+", "-", value).strip("-").lower()


def build_runbooks(
    model_catalog_path: Path,
    cluster_profile_path: Path,
    training_cfg: dict[str, Any],
    output_dir: Path,
    sft_dataset_file: Path,
) -> dict[str, Any]:
    raise RuntimeError(LEGACY_TRAINING_RETIRED)


def run_pipeline(config_path: Path) -> dict[str, Any]:
    raise RuntimeError(LEGACY_TRAINING_RETIRED)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_PIPELINE_CONFIG,
        help="Training pipeline YAML config path.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_pipeline(args.config.resolve())
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
