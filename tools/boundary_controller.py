#!/usr/bin/env python3
"""Compose boundary review batteries from shared + stack + domain question sets.

This controller executes the routing contract:
    battery = shared_predicates U stack(value) U domain(detected boundaries)
"""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BOUNDARIES_DIR = ROOT / "config" / "boundaries"
QUESTION_SETS_DIR = BOUNDARIES_DIR / "question_sets"
STACK_REGISTRY_FILE = BOUNDARIES_DIR / "stack_registry.yaml"
RUNTIME_POLICY_FILE = BOUNDARIES_DIR / "runtime_policy.yaml"
RESEARCH_SYNC_REGISTRY_FILE = BOUNDARIES_DIR / "research_sync_registry.yaml"

KNOWN_FRAMEWORK_DEPS = {
    "next",
    "react",
    "vue",
    "svelte",
    "angular",
    "@angular/core",
}

# Registry aliases that are ordinary English words and cannot name a stack by themselves.
AMBIGUOUS_INTENT_ALIASES = {"next", "go"}

# How an ambiguous stack can still be named: "golang", or a capital "Go" that does not start a sentence.
UNAMBIGUOUS_INTENT_PATTERNS = {"go": re.compile(r"\bgolang\b|(?<=[a-z,] )Go\b")}

# Parsing the question sets dominates a composed battery, so keep each file until it changes.
_YAML_CACHE: dict[Path, tuple[tuple[int, int], dict[str, Any]]] = {}


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime env detail
        raise SystemExit(
            "Missing dependency: PyYAML is required to run boundary_controller.py "
            "(pip install pyyaml)."
        ) from exc

    status = path.stat()
    stamp = (status.st_mtime_ns, status.st_size)
    cached = _YAML_CACHE.get(path)
    if cached and cached[0] == stamp:
        return copy.deepcopy(cached[1])
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    _YAML_CACHE[path] = (stamp, data)
    return copy.deepcopy(data)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _has_any(path: Path, patterns: list[str]) -> bool:
    for pattern in patterns:
        if list(path.glob(pattern)):
            return True
    return False


def _has_files(path: Path, patterns: list[str]) -> bool:
    for pattern in patterns:
        if any(path.glob(pattern)):
            return True
    return False


def _load_optional_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_yaml(path)


def _find_rrflow_sync_config(repo: Path) -> tuple[Path | None, dict[str, Any]]:
    candidates = [
        repo / "rrflow.sync.yaml",
        repo / "config" / "rrflow.sync.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path, _load_yaml(path)
    return None, {}


def _question_matches_patterns(question: dict[str, Any], patterns: list[str]) -> bool:
    qid = str(question.get("id", ""))
    qset = str(question.get("question_set", ""))
    section = str(question.get("section", ""))
    for pattern in patterns:
        if fnmatch.fnmatch(qid, pattern):
            return True
        if fnmatch.fnmatch(f"{qset}.{section}", pattern):
            return True
    return False


def _as_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S").date()
        except ValueError:
            return None


def _feed_freshness_status(feed: dict[str, Any], default_interval_days: int) -> tuple[str, str | None, str | None]:
    last_verified = feed.get("last_verified")
    next_review_due = feed.get("next_review_due")
    interval_days = feed.get("review_interval_days", default_interval_days)
    try:
        interval = int(interval_days)
    except (TypeError, ValueError):
        interval = int(default_interval_days)

    today = date.today()
    last_verified_date = _as_date(last_verified)
    due_date = _as_date(next_review_due)

    if due_date is not None and due_date < today:
        return "stale", str(last_verified) if last_verified is not None else None, str(next_review_due) if next_review_due is not None else None
    if last_verified_date is not None and (today - last_verified_date).days > interval:
        return "stale", str(last_verified), str(next_review_due) if next_review_due is not None else None
    if due_date is not None and due_date <= today:
        return "needs_review", str(last_verified) if last_verified is not None else None, str(next_review_due) if next_review_due is not None else None
    if last_verified_date is not None and (today - last_verified_date).days > max(1, interval // 2):
        return "needs_review", str(last_verified), str(next_review_due) if next_review_due is not None else None
    return "ok", str(last_verified) if last_verified is not None else None, str(next_review_due) if next_review_due is not None else None


def _bind_research_feeds(
    questions: list[dict[str, Any]],
    registry: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy = registry.get("policy", {}) if isinstance(registry, dict) else {}
    feeds = policy.get("research_feeds", []) if isinstance(policy, dict) else []
    freshness_policy = (policy.get("freshness_policy") or {}) if isinstance(policy, dict) else {}
    default_interval_days = int(freshness_policy.get("default_review_interval_days", 90) or 90)

    normalized_feeds: list[dict[str, Any]] = []
    for feed in feeds:
        if not isinstance(feed, dict):
            continue
        key = feed.get("key")
        if not isinstance(key, str) or not key:
            continue
        bindings = feed.get("question_bindings", [])
        patterns = [str(p) for p in bindings if isinstance(p, str)]
        status, last_verified, next_review_due = _feed_freshness_status(
            feed,
            default_interval_days,
        )
        normalized_feeds.append(
            {
                "key": key,
                "name": str(feed.get("name", key)),
                "question_bindings": patterns,
                "sources": feed.get("sources", []),
                "version": feed.get("version"),
                "last_verified": last_verified,
                "next_review_due": next_review_due,
                "review_interval_days": int(feed.get("review_interval_days", default_interval_days) or default_interval_days),
                "freshness_status": status,
            }
        )

    coverage: dict[str, int] = {f["key"]: 0 for f in normalized_feeds}
    for question in questions:
        matched: list[str] = []
        for feed in normalized_feeds:
            patterns = feed.get("question_bindings", [])
            if isinstance(patterns, list) and _question_matches_patterns(question, patterns):
                matched.append(str(feed["key"]))
                coverage[str(feed["key"])] += 1
        if matched:
            question["research_feeds"] = matched

    stale_feeds = [
        feed["key"]
        for feed in normalized_feeds
        if feed.get("freshness_status") in {"stale", "needs_review"}
    ]
    unbound_feeds = [key for key, count in coverage.items() if count == 0]
    sync_meta = {
        "research_registry": str(RESEARCH_SYNC_REGISTRY_FILE),
        "feeds_loaded": len(normalized_feeds),
        "question_coverage_by_feed": coverage,
        "unbound_feeds": unbound_feeds,
        "freshness_policy": {
            "default_review_interval_days": default_interval_days,
            **(freshness_policy if isinstance(freshness_policy, dict) else {}),
        },
        "stale_feeds": stale_feeds,
        "feed_freshness": {feed["key"]: {
            "status": feed.get("freshness_status"),
            "last_verified": feed.get("last_verified"),
            "next_review_due": feed.get("next_review_due"),
            "review_interval_days": feed.get("review_interval_days"),
        } for feed in normalized_feeds},
    }
    return normalized_feeds, sync_meta


def detect_stacks(repo: Path, registry: dict[str, Any]) -> tuple[list[str], list[str]]:
    detected: set[str] = set()
    reasons: list[str] = []

    package_json = _read_json(repo / "package.json")
    dependencies = set()
    if package_json:
        deps = package_json.get("dependencies", {})
        dev_deps = package_json.get("devDependencies", {})
        if isinstance(deps, dict):
            dependencies.update(deps.keys())
        if isinstance(dev_deps, dict):
            dependencies.update(dev_deps.keys())

    cargo_toml = _read_text(repo / "Cargo.toml")

    if any((repo / name).exists() for name in ("next.config.js", "next.config.mjs", "next.config.cjs", "next.config.ts")):
        detected.add("nextjs")
        reasons.append("Detected nextjs: next.config.*")
    if "next" in dependencies:
        detected.add("nextjs")
        reasons.append("Detected nextjs: next dependency")

    if (repo / "go.mod").exists():
        detected.add("go")
        reasons.append("Detected go: go.mod")

    if (repo / "Cargo.toml").exists():
        detected.add("rust")
        reasons.append("Detected rust: Cargo.toml")

    if (repo / "tsconfig.json").exists() or _has_any(repo, ["**/*.ts", "**/*.tsx"]):
        detected.add("typescript")
        reasons.append("Detected typescript: tsconfig.json or .ts/.tsx sources")

    if "react" in dependencies and "next" not in dependencies:
        detected.add("react")
        reasons.append("Detected react: react dependency without next")

    js_present = _has_any(repo, ["**/*.js", "**/*.mjs", "**/*.cjs", "**/*.html"])
    has_known_framework = any(dep in KNOWN_FRAMEWORK_DEPS for dep in dependencies)
    if js_present and not has_known_framework:
        detected.add("vanilla_js")
        reasons.append("Detected vanilla_js: JS/HTML sources without known framework deps")

    if "specta" in cargo_toml or "tauri-specta" in cargo_toml:
        detected.add("specta")
        reasons.append("Detected specta: Cargo.toml dependency markers")
    if "schemars" in cargo_toml:
        detected.add("schemars")
        reasons.append("Detected schemars: Cargo.toml dependency markers")

    if (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists() or (repo / "setup.py").exists():
        detected.add("python")
        reasons.append("Detected python: pyproject.toml/requirements.txt/setup.py")
    if "lightning" in dependencies or "pytorch-lightning" in dependencies:
        detected.add("pytorch_lightning")
        reasons.append("Detected pytorch_lightning: dependency marker")

    if (repo / "pom.xml").exists() or (repo / "build.gradle").exists() or (repo / "build.gradle.kts").exists():
        detected.add("java")
        reasons.append("Detected java: Maven/Gradle build files")

    if _has_files(repo, ["**/*.sql"]) or (repo / "migrations").is_dir():
        detected.add("sql")
        reasons.append("Detected sql: .sql files or migrations directory")

    if "drizzle-orm" in dependencies or (repo / "drizzle.config.ts").exists() or (repo / "drizzle.config.js").exists():
        detected.add("drizzle")
        reasons.append("Detected drizzle: dependency or drizzle.config.*")

    if "prisma" in dependencies or (repo / "schema.prisma").exists() or _has_files(repo, ["**/schema.prisma"]):
        detected.add("prisma")
        reasons.append("Detected prisma: dependency or schema.prisma")

    if (repo / "Gemfile").exists() or (repo / "Gemfile.lock").exists() or (repo / "config.ru").exists() or _has_files(repo, ["**/*.rb"]):
        detected.add("ruby")
        reasons.append("Detected ruby: Gemfile/Gemfile.lock/config.ru/.rb files")

    if (repo / "composer.json").exists() or (repo / "composer.lock").exists() or _has_files(repo, ["**/*.php"]):
        detected.add("php")
        reasons.append("Detected php: composer files or .php sources")

    if ((repo / "Makefile").exists() or (repo / "CMakeLists.txt").exists()) and _has_files(repo, ["**/*.c"]):
        detected.add("c")
        reasons.append("Detected c: Makefile/CMakeLists + .c sources")

    if (repo / "CMakeLists.txt").exists() and _has_files(repo, ["**/*.cpp", "**/*.cc", "**/*.cxx", "**/*.hpp", "**/*.hxx"]):
        detected.add("cpp")
        reasons.append("Detected cpp: CMakeLists + C++ source/header files")

    registry_stacks = {
        stack.get("key")
        for stack in registry.get("stacks", [])
        if isinstance(stack, dict) and stack.get("key")
    }
    valid_detected = sorted(k for k in detected if k in registry_stacks)
    return valid_detected, reasons


def detect_stacks_from_intent(
    registry: dict[str, Any], intent_text: str, already_detected: list[str]
) -> tuple[list[str], list[str]]:
    intent = intent_text.lower().strip()
    if not intent:
        return already_detected, []

    detected = list(already_detected)
    reasons: list[str] = []
    for stack in registry.get("stacks", []):
        if not isinstance(stack, dict):
            continue
        key = stack.get("key")
        if not isinstance(key, str) or key in detected:
            continue

        candidates = set()
        source_value = stack.get("source_value")
        canonical_label = stack.get("canonical_label")
        if isinstance(source_value, str):
            candidates.add(source_value.lower())
        candidates.add(key.lower())
        if isinstance(canonical_label, str):
            candidates.add(canonical_label.lower())

        for alias in stack.get("lexicon_aliases", []):
            if isinstance(alias, dict):
                val = alias.get("alias")
                if isinstance(val, str):
                    candidates.add(val.lower())
            elif isinstance(alias, str):
                candidates.add(alias.lower())

        pattern = UNAMBIGUOUS_INTENT_PATTERNS.get(key)
        if pattern and pattern.search(intent_text):
            detected.append(key)
            reasons.append(f"Detected {key}: unambiguous intent name")
            continue

        matched = False
        for candidate in candidates:
            if not candidate.strip() or candidate in AMBIGUOUS_INTENT_ALIASES:
                continue
            if re.search(r"\b" + re.escape(candidate) + r"\b", intent):
                detected.append(key)
                reasons.append(f"Detected {key}: intent alias match '{candidate}'")
                matched = True
                break
        if matched:
            continue

    return sorted(set(detected), key=detected.index), reasons


def detect_domains(
    domains_cfg: dict[str, Any], intent_text: str, explicit_domains: list[str]
) -> tuple[list[str], list[str]]:
    if explicit_domains:
        return sorted(set(explicit_domains)), ["Detected domains: explicit override"]

    intent = intent_text.lower()
    if not intent.strip():
        return [], []

    detected: list[str] = []
    reasons: list[str] = []
    for domain in domains_cfg.get("domains", []):
        if not isinstance(domain, dict):
            continue
        key = domain.get("key")
        if not key:
            continue
        aliases = [str(x).lower() for x in domain.get("aliases", [])]
        aliases.append(str(domain.get("source_label", "")).lower())
        for alias in aliases:
            if alias and re.search(r"\b" + re.escape(alias) + r"\b", intent):
                detected.append(key)
                reasons.append(f"Detected domain {key}: matched alias '{alias}'")
                break
    return sorted(set(detected)), reasons


def _shared_section_included(
    section_key: str,
    shared_cfg: dict[str, Any],
    runtime_policy: dict[str, Any],
    maturity: str,
    has_test_harness: bool,
    unbounded_data_path: bool,
) -> bool:
    section_map = {
        s.get("key"): s for s in shared_cfg.get("sections", []) if isinstance(s, dict)
    }
    section = section_map.get(section_key) or {}
    overrides = (
        (runtime_policy.get("policy") or {}).get("shared_section_gating_overrides") or {}
    )
    override = overrides.get(section_key)
    if override == "on_every_boundary":
        return True
    if override == "growing_or_mature":
        return maturity in ("growing", "mature")
    if override == "mature_only":
        return maturity == "mature"
    if override == "requires_test_harness":
        return has_test_harness
    if override == "requires_unbounded_data_path":
        return unbounded_data_path

    fires_when = section.get("fires_when")

    if not fires_when:
        return True
    text = str(fires_when).lower()
    if "on every boundary" in text:
        return True
    if "once a project is graded past greenfield" in text:
        return maturity in ("growing", "mature")
    if "when a test harness exists" in text:
        return has_test_harness
    if "input size is unbounded" in text:
        return unbounded_data_path
    return True


def _stack_question_included(question: dict[str, Any], maturity: str) -> bool:
    maturity_info = question.get("maturity")
    if not isinstance(maturity_info, dict):
        return True
    if maturity == "greenfield":
        return bool(maturity_info.get("greenfield", False))
    if maturity == "growing":
        return bool(maturity_info.get("growing", True))
    return True


def _default_citation_for_section(
    question_set_key: str,
    section_key: str,
    runtime_policy: dict[str, Any],
) -> str | None:
    if question_set_key != "shared_predicates":
        return None
    section_citations = (
        (runtime_policy.get("policy") or {}).get("shared_section_default_citations") or {}
    )
    value = section_citations.get(section_key)
    return str(value) if isinstance(value, str) else None


def _resolved_citation(
    question: dict[str, Any],
    question_set_key: str,
    runtime_policy: dict[str, Any],
) -> str | None:
    citation = question.get("citation")
    if isinstance(citation, str) and citation.strip():
        return citation
    section_key = str(question.get("section", ""))
    return _default_citation_for_section(question_set_key, section_key, runtime_policy)


def _validate_required_fields(question: dict[str, Any], question_set_name: str) -> None:
    qid = question.get("id")
    text = question.get("text")
    source = question.get("source")
    if not qid or not text:
        raise SystemExit(f"Invalid question in {question_set_name}: missing id/text")
    if not isinstance(source, dict):
        raise SystemExit(f"Invalid question {qid} in {question_set_name}: missing source block")


def compose_battery(
    repo: Path,
    maturity: str,
    has_test_harness: bool,
    unbounded_data_path: bool,
    intent_text: str,
    explicit_domains: list[str],
    primary_stack: str | None,
    include_overlaps: bool,
) -> dict[str, Any]:
    registry = _load_yaml(STACK_REGISTRY_FILE)
    shared_cfg = _load_yaml(QUESTION_SETS_DIR / "shared_predicates.yaml")
    domains_cfg = _load_yaml(QUESTION_SETS_DIR / "domains.yaml")
    runtime_policy = (
        _load_yaml(RUNTIME_POLICY_FILE) if RUNTIME_POLICY_FILE.exists() else {"policy": {}}
    )
    research_sync_registry = _load_optional_yaml(RESEARCH_SYNC_REGISTRY_FILE)
    rrflow_sync_path, rrflow_sync_cfg = _find_rrflow_sync_config(repo)

    detected_stacks, stack_reasons = detect_stacks(repo, registry)
    detected_stacks, intent_stack_reasons = detect_stacks_from_intent(
        registry, intent_text, detected_stacks
    )
    stack_reasons.extend(intent_stack_reasons)
    domain_keys, domain_reasons = detect_domains(domains_cfg, intent_text, explicit_domains)

    if primary_stack and primary_stack not in detected_stacks:
        detected_stacks.insert(0, primary_stack)
        stack_reasons.append(f"Primary stack forced by CLI: {primary_stack}")

    stack_entries = {
        s.get("key"): s for s in registry.get("stacks", []) if isinstance(s, dict) and s.get("key")
    }

    selected_stacks: list[str] = []
    for stack in detected_stacks:
        entry = stack_entries.get(stack) or {}
        status = entry.get("status")
        if status == "queued":
            continue
        if stack == "typescript":
            selected_stacks.append(stack)
            continue
        if status in ("drafted", "contract tool"):
            selected_stacks.append(stack)

    if primary_stack and primary_stack not in selected_stacks:
        selected_stacks.insert(0, primary_stack)

    selected_stacks = sorted(set(selected_stacks), key=selected_stacks.index)

    question_sets: dict[str, dict[str, Any]] = {
        "shared_predicates": shared_cfg,
        "domains": domains_cfg,
    }
    for key in selected_stacks:
        question_file = QUESTION_SETS_DIR / f"{key}.yaml"
        if question_file.exists():
            question_sets[key] = _load_yaml(question_file)

    composed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    suppressed_overlap_ids: set[str] = set()

    for question in shared_cfg.get("questions", []):
        if not isinstance(question, dict):
            continue
        _validate_required_fields(question, "shared_predicates")
        qid = str(question["id"])
        if qid in seen_ids:
            raise SystemExit(f"Duplicate question id found: {qid}")
        if not _shared_section_included(
            str(question.get("section", "")),
            shared_cfg,
            runtime_policy,
            maturity,
            has_test_harness,
            unbounded_data_path,
        ):
            continue
        seen_ids.add(qid)
        composed.append(
            {
                "id": qid,
                "kind": "shared",
                "question_set": "shared_predicates",
                "text": question["text"],
                "section": question.get("section"),
                "source": question.get("source"),
                "citation": _resolved_citation(question, "shared_predicates", runtime_policy),
            }
        )

    for stack in selected_stacks:
        cfg = question_sets.get(stack)
        if not cfg:
            continue
        for question in cfg.get("questions", []):
            if not isinstance(question, dict):
                continue
            _validate_required_fields(question, stack)
            if not _stack_question_included(question, maturity):
                continue
            overlap = question.get("overlaps_shared_question")
            if isinstance(overlap, dict):
                overlap_id = overlap.get("id")
                if isinstance(overlap_id, str) and overlap_id:
                    suppressed_overlap_ids.add(overlap_id)
                    if not include_overlaps:
                        continue
            qid = str(question["id"])
            if qid in seen_ids:
                raise SystemExit(f"Duplicate question id found: {qid}")
            seen_ids.add(qid)
            composed.append(
                {
                    "id": qid,
                    "kind": "stack",
                    "stack": stack,
                    "question_set": stack,
                    "text": question["text"],
                    "section": question.get("section"),
                    "source": question.get("source"),
                    "citation": _resolved_citation(question, stack, runtime_policy),
                    "overlaps_shared_question": overlap,
                }
            )

    if domain_keys:
        domain_questions_by_key: dict[str, list[dict[str, Any]]] = {}
        for domain in domains_cfg.get("domains", []):
            if not isinstance(domain, dict):
                continue
            d_key = domain.get("key")
            if isinstance(d_key, str):
                domain_questions_by_key[d_key] = [
                    q for q in domain.get("questions", []) if isinstance(q, dict)
                ]

        for d_key in domain_keys:
            for question in domain_questions_by_key.get(d_key, []):
                _validate_required_fields(question, f"domains:{d_key}")
                qid = str(question["id"])
                if qid in seen_ids:
                    raise SystemExit(f"Duplicate question id found: {qid}")
                seen_ids.add(qid)
                composed.append(
                    {
                        "id": qid,
                        "kind": "domain",
                        "domain": d_key,
                        "question_set": "domains",
                        "text": question["text"],
                        "section": question.get("section"),
                        "source": question.get("source"),
                        "citation": _resolved_citation(question, "domains", runtime_policy),
                    }
                )

    if not include_overlaps and suppressed_overlap_ids:
        composed = [
            q
            for q in composed
            if not (q.get("kind") == "shared" and q.get("id") in suppressed_overlap_ids)
        ]

    research_feeds, research_sync_meta = _bind_research_feeds(composed, research_sync_registry)
    rrflow_sync = {
        "detected": bool(rrflow_sync_path),
        "config_path": str(rrflow_sync_path) if rrflow_sync_path else None,
        "project_mode": (
            (rrflow_sync_cfg.get("sync") or {}).get("project_mode")
            if isinstance(rrflow_sync_cfg, dict)
            else None
        ),
        "swag_shared_profile": (
            (rrflow_sync_cfg.get("sync") or {}).get("swag_shared_profile")
            if isinstance(rrflow_sync_cfg, dict)
            else None
        ),
        "decision_sources": (
            (rrflow_sync_cfg.get("sync") or {}).get("decision_sources")
            if isinstance(rrflow_sync_cfg, dict)
            else []
        ),
    }
    if not rrflow_sync["project_mode"]:
        rrflow_sync["project_mode"] = "unknown"

    return {
        "routing_contract": "shared_predicates U stack(value) U domain(detected)",
        "input": {
            "repo": str(repo),
            "maturity": maturity,
            "has_test_harness": has_test_harness,
            "unbounded_data_path": unbounded_data_path,
            "intent_text_present": bool(intent_text.strip()),
            "explicit_domains": explicit_domains,
            "primary_stack": primary_stack,
            "include_overlaps": include_overlaps,
        },
        "detected": {
            "stacks": detected_stacks,
            "selected_stacks": selected_stacks,
            "stack_reasons": stack_reasons,
            "domains": domain_keys,
            "domain_reasons": domain_reasons,
        },
        "counts": {
            "questions_total": len(composed),
            "shared": len([q for q in composed if q.get("kind") == "shared"]),
            "stack": len([q for q in composed if q.get("kind") == "stack"]),
            "domain": len([q for q in composed if q.get("kind") == "domain"]),
        },
        "source_sync": {
            "rrflow_sync": rrflow_sync,
            "research_sync": {
                **research_sync_meta,
                "feeds": research_feeds,
            },
        },
        "questions": composed,
    }


def audit_gaps() -> dict[str, Any]:
    registry = _load_yaml(STACK_REGISTRY_FILE)
    shared_cfg = _load_yaml(QUESTION_SETS_DIR / "shared_predicates.yaml")
    domains_cfg = _load_yaml(QUESTION_SETS_DIR / "domains.yaml")
    runtime_policy = (
        _load_yaml(RUNTIME_POLICY_FILE) if RUNTIME_POLICY_FILE.exists() else {"policy": {}}
    )
    research_sync_registry = _load_optional_yaml(RESEARCH_SYNC_REGISTRY_FILE)

    stack_rows = [s for s in registry.get("stacks", []) if isinstance(s, dict)]
    drafted = [s for s in stack_rows if s.get("status") == "drafted"]
    queued = [s for s in stack_rows if s.get("status") == "queued"]
    contract_tools = [s for s in stack_rows if s.get("status") == "contract tool"]

    missing_question_sets: list[str] = []
    for stack in drafted + contract_tools:
        key = stack.get("key")
        if not isinstance(key, str):
            continue
        file_path = QUESTION_SETS_DIR / f"{key}.yaml"
        if not file_path.exists():
            missing_question_sets.append(key)

    shared_sections = shared_cfg.get("sections", [])
    ungated_shared_sections = [
        s.get("key")
        for s in shared_sections
        if isinstance(s, dict) and not s.get("gating_specified_in_source", True)
    ]
    shared_gating_overrides = (
        (runtime_policy.get("policy") or {}).get("shared_section_gating_overrides") or {}
    )
    ungated_shared_sections_without_override = [
        key for key in ungated_shared_sections if key not in shared_gating_overrides
    ]

    def _collect_question_files() -> list[Path]:
        files = list(QUESTION_SETS_DIR.glob("*.yaml"))
        return sorted(files)

    missing_citation: dict[str, int] = {}
    missing_source: dict[str, int] = {}
    overlap_ref_errors: list[dict[str, str]] = []
    shared_ids: set[str] = set()

    for q in shared_cfg.get("questions", []):
        if isinstance(q, dict) and q.get("id"):
            shared_ids.add(str(q["id"]))

    for q_file in _collect_question_files():
        data = _load_yaml(q_file)
        missing_citation[str(q_file.name)] = 0
        missing_source[str(q_file.name)] = 0
        for question in data.get("questions", []):
            if not isinstance(question, dict):
                continue
            if not question.get("citation"):
                qset_key = (
                    ((data.get("question_set") or {}).get("key"))
                    if isinstance(data.get("question_set"), dict)
                    else None
                )
                resolved = _resolved_citation(
                    question,
                    str(qset_key or ""),
                    runtime_policy,
                )
                if not resolved:
                    missing_citation[str(q_file.name)] += 1
            if not isinstance(question.get("source"), dict):
                missing_source[str(q_file.name)] += 1
            overlap = question.get("overlaps_shared_question")
            if isinstance(overlap, dict):
                overlap_id = overlap.get("id")
                if isinstance(overlap_id, str) and overlap_id and overlap_id not in shared_ids:
                    overlap_ref_errors.append(
                        {
                            "file": str(q_file.name),
                            "question_id": str(question.get("id", "")),
                            "bad_overlap_id": overlap_id,
                        }
                    )

    queued_boundary_keys = [
        b.get("key")
        for b in domains_cfg.get("queued_boundaries", [])
        if isinstance(b, dict) and isinstance(b.get("key"), str)
    ]
    rrflow_sync_detected = (ROOT / "rrflow.sync.yaml").exists() or (
        ROOT / "config" / "rrflow.sync.yaml"
    ).exists()

    synthetic_questions: list[dict[str, Any]] = []
    for q in shared_cfg.get("questions", []):
        if isinstance(q, dict):
            synthetic_questions.append(
                {
                    "id": q.get("id"),
                    "question_set": "shared_predicates",
                    "section": q.get("section"),
                }
            )
    for q_file in _collect_question_files():
        if q_file.name == "shared_predicates.yaml":
            continue
        data = _load_yaml(q_file)
        qset_key = (
            ((data.get("question_set") or {}).get("key"))
            if isinstance(data.get("question_set"), dict)
            else q_file.stem
        )
        if qset_key == "domains":
            for domain in data.get("domains", []):
                if not isinstance(domain, dict):
                    continue
                domain_key = domain.get("key")
                for question in domain.get("questions", []):
                    if isinstance(question, dict):
                        synthetic_questions.append(
                            {
                                "id": question.get("id"),
                                "question_set": qset_key,
                                "section": domain_key,
                            }
                        )
            continue
        for question in data.get("questions", []):
            if isinstance(question, dict):
                synthetic_questions.append(
                    {
                        "id": question.get("id"),
                        "question_set": qset_key,
                        "section": question.get("section"),
                    }
                )
    _, research_sync_meta = _bind_research_feeds(synthetic_questions, research_sync_registry)
    recommended_execution_order = [
        "Resolve and annotate overlap policy where stack questions duplicate shared predicates.",
        "Add CI enforcement: run --audit-gaps and fail on non-zero unresolved gaps.",
        "Expand model-tier evaluation scenarios to include each drafted stack and each domain boundary.",
        "Track precision/recall deltas across 7B, 14B, and 27-28B before controller promotion.",
    ]
    if queued_boundary_keys:
        recommended_execution_order.insert(
            0,
            "Author queued domain boundary docs and promote from proposed to drafted.",
        )

    return {
        "summary": {
            "stack_registry_total": len(stack_rows),
            "drafted_stacks": len(drafted),
            "queued_stacks": len(queued),
            "contract_tools": len(contract_tools),
            "queued_domain_boundaries": len(queued_boundary_keys),
        },
        "gaps": {
            "missing_question_sets_for_drafted_or_contract_tools": missing_question_sets,
            "shared_sections_without_explicit_gating": ungated_shared_sections,
            "shared_sections_without_policy_override": ungated_shared_sections_without_override,
            "missing_citation_counts_by_file": missing_citation,
            "missing_source_counts_by_file": missing_source,
            "bad_overlap_references": overlap_ref_errors,
            "queued_stack_keys": [s.get("key") for s in queued if s.get("key")],
            "queued_domain_boundary_keys": queued_boundary_keys,
            "rrflow_sync_config_present": rrflow_sync_detected,
            "research_feed_question_coverage": research_sync_meta.get("question_coverage_by_feed", {}),
            "research_feeds_without_question_bindings": research_sync_meta.get("unbound_feeds", []),
            "research_feed_freshness": research_sync_meta.get("feed_freshness", {}),
            "stale_research_feeds": research_sync_meta.get("stale_feeds", []),
            "research_freshness_policy": research_sync_meta.get("freshness_policy", {}),
        },
        "recommended_execution_order": recommended_execution_order,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose boundary review battery from shared/stack/domain configs."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repo root to inspect.")
    parser.add_argument(
        "--maturity",
        choices=("greenfield", "growing", "mature"),
        default="growing",
        help="Project maturity gate.",
    )
    parser.add_argument(
        "--has-test-harness",
        action="store_true",
        help="Enable shared validation section requiring test harness.",
    )
    parser.add_argument(
        "--unbounded-data-path",
        action="store_true",
        help="Enable algorithmic section requiring unbounded input paths.",
    )
    parser.add_argument(
        "--intent-text",
        default="",
        help="User request text to resolve domain aliases (no-repo/ambiguous routing case).",
    )
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Explicit domain key override (repeat for multiple).",
    )
    parser.add_argument(
        "--primary-stack",
        default=None,
        help="Force a primary stack key (used if detection is ambiguous).",
    )
    parser.add_argument(
        "--include-overlaps",
        action="store_true",
        help="Keep stack questions marked as overlapping with shared predicates.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--audit-gaps",
        action="store_true",
        help="Report structural coverage gaps in boundary routing/question-set configs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.audit_gaps:
        print(json.dumps(audit_gaps(), indent=2 if args.pretty else None, ensure_ascii=True))
        return 0

    result = compose_battery(
        repo=args.repo.resolve(),
        maturity=args.maturity,
        has_test_harness=args.has_test_harness,
        unbounded_data_path=args.unbounded_data_path,
        intent_text=args.intent_text,
        explicit_domains=args.domain,
        primary_stack=args.primary_stack,
        include_overlaps=args.include_overlaps,
    )
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
