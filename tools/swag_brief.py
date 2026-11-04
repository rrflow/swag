#!/usr/bin/env python3
"""Decision brief: the few checks that matter for one request, or an abstention.

Uses a local decision model when one is configured, and the policy's rules otherwise.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any

from boundary_controller import (
    QUESTION_SETS_DIR,
    STACK_REGISTRY_FILE,
    _load_yaml,
    compose_battery,
    detect_domains,
    detect_stacks_from_intent,
)
from swag_decision_model import DecisionModelError, choices, configured as decision_model_configured
from swag_lfg import LfgBridgeError, assess
from swag_observability import CURRENT, observed

ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = ROOT / "config" / "boundaries" / "decision_brief_policy.yaml"
WORD = re.compile(r"[a-z0-9]+")
SCOPE = (
    "Rules-only selection from the existing question bank. No model, project correctness "
    "or routing quality verdict; RRFlow owns admission and execution."
)
MODEL_SCOPE = (
    "Unqualified decision-model selection from the existing question bank. No project correctness "
    "or routing quality verdict; RRFlow owns admission and execution."
)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _stem(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith(("ss", "us", "is")) and len(word) > 3:
        return word[:-1]
    return word


def _terms(text: str, stop_words: set[str]) -> set[str]:
    return {_stem(word) for word in WORD.findall(text.lower()) if len(word) > 2 and word not in stop_words}


def _normalize(text: str) -> str:
    return " ".join(_stem(word) for word in WORD.findall(text.lower()))


def _without_ignored_phrases(text: str, phrases: list[str]) -> str:
    for phrase in phrases:
        text = re.sub(r"\b(?:" + phrase + r")\b", " ", text, flags=re.IGNORECASE)
    return text


def _signalled(intent_text: str, signals: dict[str, list[str]]) -> list[str]:
    normalized = _normalize(intent_text)
    return sorted(
        domain for domain, terms in signals.items()
        if any(re.search(r"\b" + re.escape(_normalize(str(term))) + r"\b", normalized) for term in terms)
    )


def _rank(
    intent_terms: set[str],
    questions: list[dict[str, Any]],
    named_stacks: set[str],
    firm_domains: set[str],
    policy: dict[str, Any],
) -> list[tuple[dict[str, Any], list[str]]]:
    stop_words = set(policy["stop_words"])
    question_terms = [_terms(str(question["text"]), stop_words) for question in questions]
    frequency = Counter(term for terms in question_terms for term in terms)
    common_limit = max(1.0, len(questions) * float(policy["common_term_share"]))
    matches = [{term for term in intent_terms & terms if frequency[term] <= common_limit} for terms in question_terms]
    # An alias alone is weak evidence: its domain needs a question that fits the request.
    supported_domains = firm_domains | {
        question["domain"] for question, matched in zip(questions, matches)
        if question["kind"] == "domain" and matched
    }
    scored = []
    for position, (question, matched) in enumerate(zip(questions, matches)):
        score = sum(math.log(1 + len(questions) / frequency[term]) for term in matched)
        if question["kind"] == "domain":
            if question["domain"] not in supported_domains:
                continue
            score += float(policy["domain_weight"])
        elif question["kind"] == "stack" and question.get("question_set") in named_stacks:
            if not matched:
                continue
            score += float(policy["named_stack_weight"])
        elif len(matched) < int(policy["min_unnamed_matches"]):
            continue
        scored.append((-score, position, question, sorted(matched)))
    scored.sort(key=lambda row: row[:2])
    return [(question, matched) for _, _, question, matched in scored]


def _lfg_signal(text: str) -> dict[str, Any]:
    if not os.environ.get("SWAG_LFG_CONNECTION_FILE"):
        return {"state": "not_configured"}
    try:
        observation = assess(text)["observation"]
    except LfgBridgeError:
        return {"state": "unavailable"}
    return {
        "state": "available",
        "analyzer": observation["analyzer"],
        "complexity": observation["complexity"]["bracket"],
        "suggestedRole": observation["suggestedRole"],
        "suggestedEffort": observation["suggestedEffort"],
        "assessmentSha256": observation["assessmentSha256"],
        "advisory": True,
    }


def _model_reading(intent_text: str, domains_config: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Ask the decision model for stakes and domains. Thresholds come from the policy."""
    settings = policy["decision_model"]
    criteria = {
        domain["key"]: f"{domain['canonical_label']}. {' '.join(str(domain.get('disambiguation') or '').split())}"
        for domain in domains_config["domains"]
    }
    criteria["none"] = settings["no_domain_option"]
    reading = choices({"request": intent_text}, {
        "stakes": {"type": "choice", "instructions": settings["stakes_question"], "criteria": settings["stakes_options"]},
        "domain": {"type": "choice", "instructions": settings["domain_question"], "criteria": criteria},
    }, int(settings["max_questions_per_request"]))
    stakes = reading["answers"]["stakes"]["elevated"]
    likelihoods = {key: value for key, value in reading["answers"]["domain"].items() if key != "none"}
    return {
        "stakes": stakes,
        "elevated": stakes >= float(settings["stakes_threshold"]),
        "domains": sorted(key for key, value in likelihoods.items() if value >= float(settings["domain_threshold"])),
        "likelihoods": likelihoods,
        "inputTokens": reading["inputTokens"],
        "model": reading["model"],
        "revision": reading["revision"],
    }


def _model_rank(
    intent_text: str,
    candidates: list[dict[str, Any]],
    shares: dict[str, float],
    policy: dict[str, Any],
) -> tuple[list[tuple[dict[str, Any], float]], int]:
    """Ask which check matters most within each group, weighted by how strongly that group applies."""
    settings = policy["decision_model"]
    groups: dict[str, list[dict[str, Any]]] = {}
    for question in candidates:
        groups.setdefault(question["domain"] if question["kind"] == "domain" else question["question_set"], []).append(question)
    kept = sorted(groups, key=lambda key: -shares[key])[: int(settings["max_check_groups"])]
    limit = int(settings["max_options_per_question"])
    questions = {}
    for key in kept:
        criteria = {question["id"]: question["text"] for question in groups[key][:limit - 1]}
        # Domains were already chosen for this request. Naming a stack does not mean one of its checks applies.
        if groups[key][0]["kind"] != "domain":
            criteria["none"] = settings["no_check_option"]
        questions[key] = {"type": "choice", "instructions": settings["check_question"], "criteria": criteria}
    reading = choices({"request": intent_text}, questions, int(settings["max_questions_per_request"]))
    scored = []
    for key in kept:
        distribution = reading["answers"][key]
        if distribution.get("none", 0.0) == max(distribution.values()):
            continue
        scored += [(question, shares[key] * distribution[question["id"]]) for question in groups[key] if question["id"] in distribution]
    order = sorted(enumerate(scored), key=lambda row: (-row[1][1], row[0]))
    return [row for _, row in order], reading["inputTokens"]


@observed("swag.decision_brief")
def decision_brief(
    repo: Path,
    intent_text: str,
    maturity: str = "growing",
    has_test_harness: bool = True,
    domains: list[str] | None = None,
    primary_stack: str | None = None,
) -> dict[str, Any]:
    if not isinstance(intent_text, str) or not intent_text.strip():
        raise ValueError("Describe the request with a non-empty intent.")
    policy = _load_yaml(POLICY_FILE)
    domains_config = _load_yaml(QUESTION_SETS_DIR / "domains.yaml")
    # Routing reads the request without look-alike phrases; LFG and the digest see the original.
    routed_text = _without_ignored_phrases(intent_text, policy["ignored_phrases"])
    caller_elevated = set(domains or []) & set(policy["elevated_signals"])

    model_signal: dict[str, Any] = {"state": "not_configured"}
    reading = None
    if decision_model_configured():
        try:
            reading = _model_reading(intent_text, domains_config, policy)
        except DecisionModelError:
            model_signal = {"state": "unavailable"}

    if reading:
        firm_domains = set(domains or []) | set(reading["domains"])
        elevated = sorted(caller_elevated | (firm_domains if reading["elevated"] else set()))
        aliased: list[str] = []
    else:
        elevated = sorted(set(_signalled(routed_text, policy["elevated_signals"])) | caller_elevated)
        firm_domains = set(domains or []) | set(elevated) | set(_signalled(routed_text, policy["domain_signals"]))
        aliased = [] if domains else detect_domains(domains_config, routed_text, [])[0]
    composed = compose_battery(
        repo=repo,
        maturity=maturity,
        has_test_harness=has_test_harness,
        unbounded_data_path=False,
        intent_text=routed_text,
        explicit_domains=sorted(firm_domains | set(aliased)),
        primary_stack=primary_stack,
        include_overlaps=False,
    )
    questions = [question for question in composed["questions"] if isinstance(question, dict)]
    detected = composed.get("detected", {})
    named_stacks, _ = detect_stacks_from_intent(_load_yaml(STACK_REGISTRY_FILE), routed_text, [])
    if primary_stack:
        named_stacks.append(primary_stack)

    # Naming a stack selects its questions; the name itself is not evidence that one applies.
    intent_terms = _terms(routed_text, set(policy["stop_words"]) | set(named_stacks))
    ranked = _rank(intent_terms, questions, set(named_stacks), firm_domains, policy)
    selected: list[tuple[dict[str, Any], Any]] = ranked[: int(policy["max_checks"])]
    applied_domains = sorted({question["domain"] for question, _ in ranked if question["kind"] == "domain"})

    if reading:
        # The model decides which domains apply, so the rules' shared-word matches no longer add checks.
        applied_domains = sorted(firm_domains)
        candidates = [
            question for question, matched in ranked
            if (question["kind"] == "domain" and question["domain"] in firm_domains)
            or (question["kind"] == "stack" and question.get("question_set") in named_stacks and matched)
        ]
        check_tokens = 0
        selected = []
        if candidates:
            try:
                shares = reading["likelihoods"] | {key: 1.0 for key in domains or []}
                shares |= {str(key): float(policy["decision_model"]["named_stack_share"]) for key in named_stacks}
                rank, check_tokens = _model_rank(intent_text, candidates, shares, policy)
                selected = rank[: int(policy["max_checks"])]
            except DecisionModelError:
                selected = [(question, []) for question in candidates[: int(policy["max_checks"])]]
        model_signal = {
            "state": "available",
            "model": reading["model"],
            "revision": reading["revision"],
            "stakesLikelihood": round(reading["stakes"], 4),
            "domainLikelihoods": {key: round(reading["likelihoods"][key], 4) for key in reading["domains"]},
            "inputTokens": reading["inputTokens"] + check_tokens,
            "advisory": True,
        }

    is_elevated = bool(elevated) or bool(reading and reading["elevated"])
    reason_ids = [f"domain:{domain}" for domain in applied_domains]
    reason_ids += [f"elevated:{domain}" for domain in elevated]
    lfg = _lfg_signal(intent_text)
    conflicts = []
    if is_elevated and lfg.get("suggestedEffort") in policy["low_efforts"]:
        conflicts.append("lfg_low_effort_on_elevated_stakes")
    reason_ids += [f"conflict:{conflict}" for conflict in conflicts]
    if not selected:
        reason_ids.append("no_specific_checks")

    if not selected and is_elevated:
        direction = (
            "Treat as elevated stakes: a mistake here could move money or change who can access what. "
            "No specific check stands out, so get a review before changing code."
        )
    elif not selected:
        direction = "No check stands out for this request. Proceed normally, or describe the risk if you see one."
    elif is_elevated:
        direction = (
            f"Treat as elevated stakes ({', '.join(elevated) or 'money or access'}). Answer these checks before "
            "changing code, and escalate any you cannot answer."
        )
    else:
        direction = "Answer these checks as you work. Nothing here calls for escalation."

    span = CURRENT.get()
    if span:
        span.set(modelExecuted=bool(reading), engineIntegrated=False)
    return {
        "schema": "swag.decision-brief/v1",
        "mode": "choice",
        "status": "selected" if selected else "abstained",
        "basis": "decision_model" if reading else "rules_only",
        "modelExecuted": bool(reading),
        "qualified": False,
        "direction": direction,
        "stakes": {"level": "elevated" if is_elevated else "standard", "domains": elevated},
        "escalate": is_elevated,
        "checks": [
            {
                "id": question["id"],
                "kind": question["kind"],
                "text": question["text"],
                "citation": question.get("citation"),
                **({"likelihood": round(evidence, 4)} if isinstance(evidence, float) else {"matchedTerms": evidence}),
            }
            for question, evidence in selected
        ],
        "consideredCount": len(questions),
        "omittedCount": len(questions) - len(selected),
        "routing": {"stacks": list(detected.get("selected_stacks", [])), "domains": applied_domains},
        "signals": {"lfg": lfg, "decisionModel": model_signal, "conflicts": conflicts},
        "reasonIds": reason_ids,
        "inputSha256": hashlib.sha256(intent_text.encode("utf-8")).hexdigest(),
        "optionsSha256": _digest([[question["id"], question["text"]] for question in questions]),
        "policySha256": _digest(policy),
        "scope": MODEL_SCOPE if reading else SCOPE,
    }
