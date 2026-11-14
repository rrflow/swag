"""The SWAG decision contract: SystemOne requests in, typed answers out.

SWAG speaks the same wire format as TypeSafe's Jev, Cloudflare's Clef and KnowLine
(`POST /v1/systemone` with `state` and `questions`), so any client written for one of
them can call SWAG, and SWAG can be compared with them request for request.

One scorer serves all three question types. Each question is a set of labelled options:

| Type | SWAG name | Options | Jev answer |
|---|---|---|---|
| `noul` | binary | `true`, `false` | `noul`: probability of true |
| `choice` | choice | the criteria keys, in request order | `choice`, `probabilities`, `confidence` |
| `score` | score | levels `0`..`n-1` | `score` (expected level), `probabilities`, `legend`, `confidence` |

An engine returns one probability per option. This module validates requests, shapes
answers exactly as Jev clients expect them, and computes confidence the way TypeSafe's
published adapter does. SWAG's own decision layer (abstention, hard rules, preferences,
suggestions) lives in `swag_decide` and is returned beside the answers, never inside them.
"""
from __future__ import annotations

import math
import re
from typing import Any

TYPES = ('noul', 'choice', 'score')
MODE_NAMES = {'noul': 'binary', 'choice': 'choice', 'score': 'score'}
MAX_QUESTIONS = 64
MAX_OPTIONS = 255
MAX_TEXT = 20_000
QUESTION_ID = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.:-]{0,127}')
QUESTION_FIELDS = {'type', 'instructions', 'criteria'}


class ContractError(ValueError):
    """A request that does not follow the SystemOne contract. Messages never echo request content."""


def _bounded_text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_TEXT


def validate_question(question_id: str, question: Any) -> dict:
    """Return a normalized copy of one question or raise ContractError."""
    if not isinstance(question_id, str) or not QUESTION_ID.fullmatch(question_id):
        raise ContractError('Question ids must be 1-128 characters of letters, digits, _ . : or -.')
    if not isinstance(question, dict) or not set(question) <= QUESTION_FIELDS or 'type' not in question:
        raise ContractError(f'Question {question_id} must have a type and only instructions and criteria besides.')
    kind = question['type']
    if kind not in TYPES:
        raise ContractError(f'Question {question_id} type must be noul, choice or score.')
    instructions = question.get('instructions')
    if instructions is not None and not (_bounded_text(instructions) or isinstance(instructions, (dict, list))):
        raise ContractError(f'Question {question_id} instructions must be text or JSON.')
    criteria = question.get('criteria')
    if kind == 'noul':
        if criteria is not None and (not isinstance(criteria, dict) or not set(criteria) <= {'true', 'false'}
                                     or not all(_bounded_text(value) for value in criteria.values())):
            raise ContractError(f'Question {question_id} noul criteria may only describe true and false.')
    elif kind == 'choice':
        if (not isinstance(criteria, dict) or not 2 <= len(criteria) <= MAX_OPTIONS
                or not all(isinstance(key, str) and 0 < len(key) <= 128 for key in criteria)):
            raise ContractError(f'Question {question_id} choice needs 2-{MAX_OPTIONS} named options.')
    else:
        if not isinstance(criteria, list) or not 2 <= len(criteria) <= MAX_OPTIONS:
            raise ContractError(f'Question {question_id} score needs 2-{MAX_OPTIONS} levels.')
    normalized = {'type': kind}
    if instructions is not None:
        normalized['instructions'] = instructions
    if criteria is not None:
        normalized['criteria'] = criteria
    return normalized


def validate_request(body: Any) -> dict:
    """Validate a /v1/systemone body. Returns {model, state, questions, swag}."""
    if not isinstance(body, dict):
        raise ContractError('The request body must be a JSON object.')
    if 'state' not in body:
        raise ContractError('The request needs a state.')
    questions = body.get('questions')
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        raise ContractError(f'The request needs 1-{MAX_QUESTIONS} questions keyed by id.')
    model = body.get('model')
    if model is not None and not (isinstance(model, str) and 0 < len(model) <= 256):
        raise ContractError('model must be a short string when given.')
    extension = body.get('swag', {})
    if not isinstance(extension, dict):
        raise ContractError('swag must be an object when given.')
    unknown = set(body) - {'model', 'state', 'questions', 'swag'}
    if unknown:
        raise ContractError('The request has fields outside the SystemOne contract.')
    return {
        'model': model,
        'state': body['state'],
        'questions': {key: validate_question(key, value) for key, value in questions.items()},
        'swag': extension,
    }


def options(question: dict) -> list[str]:
    """Answer keys in request order."""
    if question['type'] == 'noul':
        return ['true', 'false']
    if question['type'] == 'choice':
        return list(question['criteria'])
    return [str(level) for level in range(len(question['criteria']))]


def render(value: Any) -> str:
    """Text for a prompt: strings verbatim, JSON compact."""
    if isinstance(value, str):
        return value
    import json
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def option_texts(question: dict) -> list[str]:
    """What a text model is shown for each option, in the same order as options()."""
    criteria = question.get('criteria')
    if question['type'] == 'noul':
        criteria = criteria or {}
        return [f"Yes: {criteria.get('true', 'yes')}", f"No: {criteria.get('false', 'no')}"]
    if question['type'] == 'choice':
        return [key if value is None else f'{key}: {render(value)}' for key, value in criteria.items()]
    return [f'{level}: {render(value)}' for level, value in enumerate(criteria)]


def instructions_text(question: dict) -> str:
    value = question.get('instructions')
    return 'Answer using the options below.' if value is None else render(value)


def check_distribution(question: dict, probabilities: Any) -> dict[str, float]:
    """Validate an engine's per-option probabilities and rescale them to sum to one."""
    keys = options(question)
    if not isinstance(probabilities, dict) or set(probabilities) != set(keys):
        raise ContractError('The engine answered outside the requested options.')
    values = []
    for key in keys:
        value = probabilities[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ContractError('The engine returned an invalid probability.')
        values.append(float(value))
    total = math.fsum(values)
    if total <= 0:
        return {key: 1.0 / len(keys) for key in keys}
    return {key: value / total for key, value in zip(keys, values)}


def choice_confidence(probabilities: list[float]) -> float:
    """Peak probability rescaled from uniform (0) to certain (1), as TypeSafe's adapter defines it."""
    if len(probabilities) == 1:
        return 1.0
    uniform = 1.0 / len(probabilities)
    return max(0.0, (max(probabilities) - uniform) / (1.0 - uniform))


def score_confidence(probabilities: list[float]) -> float:
    """1 minus the mean distance from the modal level, relative to a uniform spread (TypeSafe's adapter)."""
    if len(probabilities) == 1:
        return 1.0
    mode = max(range(len(probabilities)), key=probabilities.__getitem__)
    spread = math.fsum(p * abs(index - mode) for index, p in enumerate(probabilities))
    center = (len(probabilities) - 1) / 2
    uniform_spread = math.fsum(abs(index - center) for index in range(len(probabilities))) / len(probabilities)
    return max(0.0, 1.0 - spread / uniform_spread)


def confidence(question: dict, distribution: dict[str, float]) -> float:
    values = [distribution[key] for key in options(question)]
    return score_confidence(values) if question['type'] == 'score' else choice_confidence(values)


def answer(question: dict, distribution: dict[str, float]) -> dict:
    """The Jev-compatible answer for one question."""
    keys = options(question)
    if question['type'] == 'noul':
        return {'type': 'noul', 'noul': round(distribution['true'], 6)}
    rounded = {key: round(distribution[key], 6) for key in keys}
    if question['type'] == 'choice':
        best = max(keys, key=distribution.__getitem__)
        return {'type': 'choice', 'choice': best, 'confidence': round(confidence(question, distribution), 6),
                'probabilities': rounded}
    expected = math.fsum(index * distribution[key] for index, key in enumerate(keys))
    return {'type': 'score', 'score': round(expected, 6), 'confidence': round(confidence(question, distribution), 6),
            'legend': {key: level for key, level in zip(keys, question['criteria'])}, 'probabilities': rounded}


def distribution_from_answer(question: dict, returned: Any) -> dict[str, float]:
    """Read the per-option probabilities back out of a Jev-compatible answer from another server."""
    if not isinstance(returned, dict) or returned.get('type') != question['type']:
        raise ContractError('The engine answered with the wrong question type.')
    if question['type'] == 'noul':
        value = returned.get('noul')
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ContractError('The engine returned an invalid probability.')
        return {'true': float(value), 'false': 1.0 - float(value)}
    return check_distribution(question, returned.get('probabilities'))
