"""SWAG's decision layer: facts, hard rules and preferences turned into decisions and suggestions.

A decision request is a SystemOne request (see `swag_systemone`). Four layers shape how SWAG
answers it, merged in this order, each value keeping the layer it came from:

1. `template`: a shipped knowledge template (`config/knowledge/templates/<id>.json`)
2. `project`: the project's own layer (`<repo>/.swag/layer.json`)
3. `operator`: the operator's AIDevSpec (`operator_preferences`, `operator_rules`, `operator_facts`
   in `config/aiddevspec/default.yaml`, or the file named by `SWAG_AIDEVSPEC`)
4. `request`: the request's own `swag` block

What each part of a layer may do:

- **facts** are statements about the project with a source and a freshness window. Fresh facts are
  added to the state the model reads; stale ones are listed and never used. Later layers replace a
  fact with the same id (a newer observation).
- **rules** are hard. They only ever narrow: a later layer can add rules but cannot remove or replace
  one. A rule can forbid options, require an answer, raise the abstention floor, or say what to do on
  abstention. A rule may depend on a fact; it applies only while that fact is fresh.
- **preferences** are soft. Later layers win key by key. They set abstention thresholds, the binary
  threshold, which options win a near tie, and how many suggestions to return. They can never go
  below a rule's floor or pick a forbidden option.

The model's probabilities are always reported unchanged in `answers`. Everything this module adds is
in the `swag` block: per question the decision, its status (`answered`, `abstained`, `required`,
`defaulted`), the rules and preferences that applied, and a suggestion.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any

import swag_systemone as contract

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ('template', 'project', 'operator', 'request')
NAME = re.compile(r'[a-z][a-z0-9_]{0,95}')
PREFERENCE_KEYS = {'abstainBelow', 'threshold', 'prefer', 'tieMargin', 'suggestionLimit'}
RULE_EFFECTS = {'forbid', 'require', 'abstainBelow', 'onAbstain'}
DEFAULT_PREFERENCES = {
    'abstainBelow': {'noul': 0.0, 'choice': 0.0, 'score': 0.0},
    'threshold': {},
    'prefer': {},
    'tieMargin': 0.05,
    'suggestionLimit': 5,
}


class LayerError(ValueError):
    """A layer that breaks the facts, rules and preferences contract."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def _probability(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


# ---------------------------------------------------------------- validation

def validate_fact(fact: Any) -> dict:
    if not isinstance(fact, dict) or not {'id', 'statement', 'source'} <= set(fact) \
            or not set(fact) <= {'id', 'statement', 'source', 'observedAt', 'freshForDays'}:
        raise LayerError('A fact needs id, statement and source, and may have observedAt and freshForDays.')
    if not isinstance(fact['id'], str) or not NAME.fullmatch(fact['id']):
        raise LayerError('Fact ids are lowercase snake_case.')
    if not isinstance(fact['statement'], str) or not 0 < len(fact['statement']) <= 2000:
        raise LayerError('A fact statement is 1-2000 characters.')
    if not isinstance(fact['source'], str) or not 0 < len(fact['source']) <= 500:
        raise LayerError('A fact source names where it came from (file, operator, rrflow, lfg...).')
    if 'freshForDays' in fact and (type(fact['freshForDays']) is not int or fact['freshForDays'] < 1):
        raise LayerError('freshForDays is a whole number of days.')
    if 'freshForDays' in fact and 'observedAt' not in fact:
        raise LayerError('A fact with a freshness window needs observedAt.')
    if 'observedAt' in fact:
        try:
            date.fromisoformat(str(fact['observedAt'])[:10])
        except ValueError:
            raise LayerError('observedAt is an ISO date.') from None
    return dict(fact)


def validate_rule(rule: Any) -> dict:
    if not isinstance(rule, dict) or not {'id', 'question', 'why'} <= set(rule):
        raise LayerError('A rule needs id, question and why.')
    effects = set(rule) - {'id', 'question', 'why', 'whenFact'}
    if not effects or not effects <= RULE_EFFECTS:
        raise LayerError('A rule needs at least one effect: forbid, require, abstainBelow or onAbstain.')
    if not isinstance(rule['id'], str) or not NAME.fullmatch(rule['id']):
        raise LayerError('Rule ids are lowercase snake_case.')
    if not isinstance(rule['question'], str) or not contract.QUESTION_ID.fullmatch(rule['question']):
        raise LayerError('A rule names one question id.')
    if not isinstance(rule['why'], str) or not 0 < len(rule['why']) <= 2000:
        raise LayerError('A rule says why it exists.')
    if 'whenFact' in rule and (not isinstance(rule['whenFact'], str) or not NAME.fullmatch(rule['whenFact'])):
        raise LayerError('whenFact names a fact id.')
    if 'forbid' in rule and (not isinstance(rule['forbid'], list) or not rule['forbid']
                             or not all(isinstance(item, str) for item in rule['forbid'])):
        raise LayerError('forbid lists option keys.')
    for key in ('require', 'onAbstain'):
        if key in rule and not isinstance(rule[key], str):
            raise LayerError(f'{key} names one option key (true or false for binary).')
    if 'abstainBelow' in rule and not _probability(rule['abstainBelow']):
        raise LayerError('abstainBelow is between 0 and 1.')
    return dict(rule)


def validate_preferences(preferences: Any) -> dict:
    if not isinstance(preferences, dict) or not set(preferences) <= PREFERENCE_KEYS:
        raise LayerError('Preferences may set ' + ', '.join(sorted(PREFERENCE_KEYS)) + '.')
    floors = preferences.get('abstainBelow', {})
    if not isinstance(floors, dict) or not all(
            isinstance(key, str) and _probability(value) for key, value in floors.items()):
        raise LayerError('abstainBelow maps a question type or id to a value between 0 and 1.')
    thresholds = preferences.get('threshold', {})
    if not isinstance(thresholds, dict) or not all(_probability(value) for value in thresholds.values()):
        raise LayerError('threshold maps a binary question id to a value between 0 and 1.')
    prefer = preferences.get('prefer', {})
    if not isinstance(prefer, dict) or not all(
            isinstance(value, list) and all(isinstance(item, str) for item in value) for value in prefer.values()):
        raise LayerError('prefer maps a question id to option keys in order of preference.')
    if 'tieMargin' in preferences and not (_probability(preferences['tieMargin']) and preferences['tieMargin'] <= 0.5):
        raise LayerError('tieMargin is between 0 and 0.5.')
    if 'suggestionLimit' in preferences and (type(preferences['suggestionLimit']) is not int
                                              or not 0 <= preferences['suggestionLimit'] <= 64):
        raise LayerError('suggestionLimit is 0-64.')
    return json.loads(json.dumps(preferences))


def validate_layer(layer: Any) -> dict:
    if layer is None:
        return {'facts': [], 'rules': [], 'preferences': {}}
    if not isinstance(layer, dict) or not set(layer) <= {'facts', 'rules', 'preferences'}:
        raise LayerError('A layer has only facts, rules and preferences.')
    facts = layer.get('facts', [])
    rules = layer.get('rules', [])
    if not isinstance(facts, list) or not isinstance(rules, list) or len(facts) > 500 or len(rules) > 500:
        raise LayerError('facts and rules are lists of at most 500.')
    return {'facts': [validate_fact(item) for item in facts], 'rules': [validate_rule(item) for item in rules],
            'preferences': validate_preferences(layer.get('preferences', {}))}


# ---------------------------------------------------------------- loading layers

def template_layer(template: dict) -> dict:
    return validate_layer({key: template[key] for key in ('facts', 'rules', 'preferences') if key in template})


def project_layer(repo: Path | None) -> dict:
    if repo is None:
        return validate_layer(None)
    path = repo / '.swag' / 'layer.json'
    if not path.is_file():
        return validate_layer(None)
    return validate_layer(json.loads(path.read_text(encoding='utf-8')))


def operator_layer(path: Path | None = None) -> dict:
    import yaml
    selected = path or Path(os.environ.get('SWAG_AIDEVSPEC') or ROOT / 'config' / 'aiddevspec' / 'default.yaml')
    if not selected.is_file():
        return validate_layer(None)
    spec = yaml.safe_load(selected.read_text(encoding='utf-8')) or {}
    return validate_layer({'facts': spec.get('operator_facts') or [], 'rules': spec.get('operator_rules') or [],
                           'preferences': spec.get('operator_preferences') or {}})


# ---------------------------------------------------------------- merging

def merge(layers: dict[str, dict], today: date | None = None) -> dict:
    """Merge layers in LAYERS order. Returns the effective facts, rules and preferences with their origins."""
    today = today or datetime.now(timezone.utc).date()
    facts: dict[str, dict] = {}
    rules: dict[str, dict] = {}
    conflicts: list[dict] = []
    preferences = json.loads(json.dumps(DEFAULT_PREFERENCES))
    origins: dict[str, str] = {key: 'default' for key in DEFAULT_PREFERENCES}
    for name in LAYERS:
        layer = layers.get(name) or validate_layer(None)
        for fact in layer['facts']:
            facts[fact['id']] = {**fact, 'layer': name}
        for rule in layer['rules']:
            if rule['id'] in rules:
                # Rules only narrow: an existing rule is never replaced or removed by a later layer.
                conflicts.append({'rule': rule['id'], 'layer': name, 'kept': rules[rule['id']]['layer'],
                                  'reason': 'rules_cannot_be_replaced'})
                continue
            rules[rule['id']] = {**rule, 'layer': name}
        for key, value in layer['preferences'].items():
            if isinstance(value, dict) and isinstance(preferences.get(key), dict):
                preferences[key] = {**preferences[key], **value}
                for item in value:
                    origins[f'{key}.{item}'] = name
            else:
                preferences[key] = value
                origins[key] = name
    fresh, stale = [], []
    for fact in facts.values():
        if 'freshForDays' in fact:
            observed = date.fromisoformat(str(fact['observedAt'])[:10])
            if (today - observed).days > fact['freshForDays']:
                stale.append(fact)
                continue
        fresh.append(fact)
    effective = {'facts': fresh, 'staleFacts': stale, 'rules': list(rules.values()),
                 'preferences': preferences, 'preferenceOrigins': origins, 'ruleConflicts': conflicts}
    effective['digest'] = _digest({key: effective[key] for key in ('facts', 'rules', 'preferences')})
    return effective


def compose_state(state: Any, facts: list[dict]) -> Any:
    """The state the model reads: the caller's state plus fresh fact statements."""
    if not facts:
        return state
    statements = [fact['statement'] for fact in facts]
    if isinstance(state, dict) and 'facts' not in state:
        return {**state, 'facts': statements}
    return {'request': state, 'facts': statements}


# ---------------------------------------------------------------- deciding

def _rules_for(question_id: str, effective: dict) -> tuple[list[dict], list[dict]]:
    fresh_ids = {fact['id'] for fact in effective['facts']}
    applied, skipped = [], []
    for rule in effective['rules']:
        if rule['question'] != question_id:
            continue
        if 'whenFact' in rule and rule['whenFact'] not in fresh_ids:
            skipped.append({'rule': rule['id'], 'reason': 'fact_missing_or_stale', 'fact': rule['whenFact']})
            continue
        applied.append(rule)
    return applied, skipped


def decide_question(question_id: str, question: dict, distribution: dict[str, float] | None, effective: dict) -> dict:
    """One question's decision. `distribution` is None when no engine was consulted."""
    keys = contract.options(question)
    kind = question['type']
    preferences = effective['preferences']
    applied, skipped = _rules_for(question_id, effective)
    record: dict[str, Any] = {'mode': contract.MODE_NAMES[kind], 'rules': [rule['id'] for rule in applied],
                              'skippedRules': skipped, 'preferences': []}

    required = {rule['require'] for rule in applied if 'require' in rule}
    if required - set(keys):
        return {**record, 'status': 'abstained', 'value': None, 'reason': 'rule_requires_unknown_option'}
    if len(required) > 1:
        return {**record, 'status': 'abstained', 'value': None, 'reason': 'rules_require_different_answers'}
    forbidden = {option for rule in applied for option in rule.get('forbid', [])}
    if required & forbidden:
        return {**record, 'status': 'abstained', 'value': None, 'reason': 'rule_requires_a_forbidden_option'}
    if required:
        value = next(iter(required))
        # A required answer belongs to the rule, not the model.
        return {**record, 'status': 'required', 'value': _typed(kind, value), 'option': value, 'reason': 'hard_rule'}
    if distribution is None:
        # A rule's safe default applies when no model can answer, as it does when the model is unsure.
        return _on_abstain({**record, 'status': 'abstained', 'value': None, 'reason': 'no_engine'}, applied, kind, forbidden)

    allowed = {key: (0.0 if key in forbidden else distribution[key]) for key in keys}
    mass = math.fsum(allowed.values())
    if mass <= 0:
        return _on_abstain({**record, 'status': 'abstained', 'value': None, 'reason': 'all_options_forbidden'}, applied, kind, forbidden)
    allowed = {key: value / mass for key, value in allowed.items()}
    if forbidden:
        record['forbidden'] = sorted(forbidden & set(keys))

    preference_floor = preferences['abstainBelow'].get(question_id, preferences['abstainBelow'].get(kind, 0.0))
    rule_floor = max([rule['abstainBelow'] for rule in applied if 'abstainBelow' in rule], default=0.0)
    floor = max(preference_floor, rule_floor)
    level = contract.confidence(question, allowed)
    record.update(confidence=round(level, 6), abstainBelow=floor,
                  abstainBelowOrigin='rule' if rule_floor >= preference_floor and rule_floor > 0 else
                  effective['preferenceOrigins'].get(f'abstainBelow.{question_id}',
                                                      effective['preferenceOrigins'].get(f'abstainBelow.{kind}', 'default')))
    if level < floor:
        return _on_abstain({**record, 'status': 'abstained', 'value': None, 'reason': 'below_confidence_floor'},
                           applied, kind, forbidden)

    if kind == 'noul':
        threshold = preferences['threshold'].get(question_id, 0.5)
        if question_id in preferences['threshold']:
            record['preferences'].append({'key': f'threshold.{question_id}', 'value': threshold,
                                          'layer': effective['preferenceOrigins'].get(f'threshold.{question_id}')})
        if forbidden & {'true', 'false'}:
            option = 'false' if 'true' in forbidden else 'true'
        else:
            option = 'true' if allowed['true'] >= threshold else 'false'
        return {**record, 'status': 'answered', 'value': option == 'true', 'option': option, 'probability': round(allowed['true'], 6)}

    ranked = sorted(keys, key=allowed.__getitem__, reverse=True)
    option = ranked[0]
    favourites = [item for item in preferences['prefer'].get(question_id, []) if item in keys and item not in forbidden]
    margin = preferences['tieMargin']
    for favourite in favourites:
        if favourite != option and allowed[option] - allowed[favourite] <= margin:
            record['preferences'].append({'key': f'prefer.{question_id}', 'value': favourite,
                                          'layer': effective['preferenceOrigins'].get(f'prefer.{question_id}'),
                                          'reason': 'near_tie', 'margin': round(allowed[option] - allowed[favourite], 6)})
            option = favourite
            break
        if favourite == option:
            break
    if kind == 'choice':
        return {**record, 'status': 'answered', 'value': option, 'option': option, 'probability': round(allowed[option], 6)}
    expected = math.fsum(index * allowed[key] for index, key in enumerate(keys))
    return {**record, 'status': 'answered', 'value': round(expected, 6), 'option': option, 'level': int(option),
            'probability': round(allowed[option], 6)}


def _typed(kind: str, option: str) -> Any:
    if kind == 'noul':
        return option == 'true'
    if kind == 'score':
        return int(option)
    return option


def _on_abstain(record: dict, applied: list[dict], kind: str, forbidden: set[str]) -> dict:
    defaults = [rule for rule in applied if 'onAbstain' in rule and rule['onAbstain'] not in forbidden]
    if not defaults:
        return record
    rule = defaults[0]
    return {**record, 'status': 'defaulted', 'value': _typed(kind, rule['onAbstain']), 'option': rule['onAbstain'],
            'defaultedBy': rule['id'], 'abstainReason': record['reason'], 'reason': 'rule_default_on_abstain'}


def suggestions(questions: dict, decisions: dict, suggest: dict[str, dict], limit: int) -> list[dict]:
    """Template suggestions for the decided options, rule-driven ones first, in question order."""
    rows = []
    for question_id in questions:
        decision = decisions[question_id]
        texts = suggest.get(question_id) or {}
        key = 'abstain' if decision['status'] == 'abstained' else decision.get('option')
        text = texts.get(key)
        if text:
            rows.append({'question': question_id, 'when': key, 'text': text, 'status': decision['status'],
                         'byRule': decision['status'] in ('required', 'defaulted')})
    rows.sort(key=lambda row: not row['byRule'])
    return rows[:limit]


# ---------------------------------------------------------------- one call

def decide(request: dict, layers: dict[str, dict], engine: Any = None, suggest: dict[str, dict] | None = None,
           today: date | None = None) -> dict:
    """Run a validated request through the layers and the engine.

    `engine(state, questions)` returns `swag_decision_model.distributions()` output, or is None when no
    model is configured; then only hard rules can decide and every other question abstains.
    """
    timings: dict[str, float] = {}
    started = time.perf_counter()
    effective = merge(layers, today)
    state = compose_state(request['state'], effective['facts'])
    questions = request['questions']
    # Questions a hard rule already answers never reach the model.
    to_score = {key: value for key, value in questions.items()
                if not any('require' in rule for rule in _rules_for(key, effective)[0])}
    timings['composeMs'] = round((time.perf_counter() - started) * 1000, 3)

    scored: dict = {'answers': {}, 'elapsedMs': {}, 'inputTokens': 0}
    engine_info: dict[str, Any] = {'consulted': False}
    if to_score and engine is not None:
        started = time.perf_counter()
        scored = engine(state, to_score)
        timings['engineMs'] = round((time.perf_counter() - started) * 1000, 3)
        engine_info = {'consulted': True, **{key: scored.get(key) for key in ('model', 'protocol', 'rotations', 'revision')},
                       'inputTokens': scored.get('inputTokens', 0)}

    started = time.perf_counter()
    answers, decisions = {}, {}
    for question_id, question in questions.items():
        distribution = scored['answers'].get(question_id)
        if distribution is not None:
            distribution = contract.check_distribution(question, distribution)
            answers[question_id] = contract.answer(question, distribution)
        decision = decide_question(question_id, question, distribution, effective)
        if question_id in scored.get('elapsedMs', {}):
            decision['engineMs'] = scored['elapsedMs'][question_id]
        decisions[question_id] = decision
    rows = suggestions(questions, decisions, suggest or {}, effective['preferences']['suggestionLimit'])
    timings['decideMs'] = round((time.perf_counter() - started) * 1000, 3)

    return {
        'model': request.get('model') or engine_info.get('model') or 'swag',
        'answers': answers,
        'usage': {'input_tokens': engine_info.get('inputTokens', 0), 'output_tokens': 0},
        'swag': {
            'schema': 'swag.decision/v1',
            'decisions': decisions,
            'suggestions': rows,
            'engine': engine_info,
            'timings': timings,
            'effective': {
                'digest': effective['digest'],
                'facts': [{'id': fact['id'], 'layer': fact['layer'], 'source': fact['source']} for fact in effective['facts']],
                'staleFacts': [{'id': fact['id'], 'layer': fact['layer'], 'observedAt': str(fact['observedAt'])}
                               for fact in effective['staleFacts']],
                'rules': [{'id': rule['id'], 'question': rule['question'], 'layer': rule['layer']} for rule in effective['rules']],
                'ruleConflicts': effective['ruleConflicts'],
                'preferences': effective['preferences'],
                'preferenceOrigins': effective['preferenceOrigins'],
            },
        },
    }
