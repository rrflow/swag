"""Read-only, source-bound knowledge templates and typed decision validation.

This adapter neither runs a model nor records fulfillment or engine authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re

from swag_observability import observed

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r'[a-z][a-z0-9_]{0,95}')
LIMIT = 2_000_000


def encode(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def fields(value: object, required: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError('Unexpected contract fields')


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 10000


def read_bytes(path: Path) -> bytes:
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Input exceeds read bound')
    return raw


def under(root: Path, relative: str) -> Path:
    if not text(relative) or '\\' in relative or ':' in relative:
        raise ValueError('Portable relative path required')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Relative path escapes its root')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('Resolved path escapes its root')
    return resolved


def mode_contract(value: dict) -> None:
    if not isinstance(value, dict):
        raise ValueError('Decision contract required')
    mode = value.get('mode')
    if mode == 'binary':
        fields(value, {'mode', 'proposition'})
        if not text(value['proposition']):
            raise ValueError('Explicit proposition required')
    elif mode == 'choice':
        fields(value, {'mode', 'question', 'options'})
        options = value['options']
        if not text(value['question']) or not isinstance(options, list) or not 2 <= len(options) <= 100:
            raise ValueError('Explicit question and options required')
        ids = []
        for option in options:
            fields(option, {'id', 'description'})
            if not isinstance(option['id'], str) or not NAME.fullmatch(option['id']) or not text(option['description']):
                raise ValueError('Invalid option')
            ids.append(option['id'])
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate option')
    elif mode == 'score':
        fields(value, {'mode', 'rubric', 'minimum', 'maximum', 'direction'})
        if (not text(value['rubric']) or value['direction'] not in ('higher_is_better', 'lower_is_better')
                or any(type(value[key]) not in (int, float) or not math.isfinite(value[key]) for key in ('minimum', 'maximum'))
                or value['minimum'] >= value['maximum']):
            raise ValueError('Explicit finite score scale and rubric required')
    else:
        raise ValueError('Unsupported decision mode')


def template(name: str, root: Path = ROOT) -> dict:
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError('Invalid template identity')
    data = json.loads(read_bytes(under(root, f'config/knowledge/templates/{name}.json')))
    fields(data, {'schemaVersion', 'id', 'title', 'requirements'})
    if type(data['schemaVersion']) is not int or data['schemaVersion'] != 1 or data['id'] != name or not text(data['title']):
        raise ValueError('Invalid template version or identity')
    if not isinstance(data['requirements'], list) or not 1 <= len(data['requirements']) <= 100:
        raise ValueError('Nonempty bounded requirements required')
    ids = set()
    for row in data['requirements']:
        fields(row, {'id', 'title', 'practice', 'inputSlots', 'decision'})
        if not isinstance(row['id'], str) or not NAME.fullmatch(row['id']) or row['id'] in ids or not text(row['title']):
            raise ValueError('Invalid requirement identity')
        ids.add(row['id'])
        fields(row['practice'], {'questionSet', 'questionId'})
        slots = row['inputSlots']
        if (not isinstance(slots, list) or not slots or len(slots) != len(set(slots))
                or any(not isinstance(slot, str) or not NAME.fullmatch(slot) for slot in slots)):
            raise ValueError('Explicit input slots required')
        mode_contract(row['decision'])
    return data


def practice(reference: dict, root: Path = ROOT) -> dict:
    import yaml
    name = reference['questionSet']
    if not isinstance(name, str) or not NAME.fullmatch(name) or not text(reference['questionId']):
        raise ValueError('Invalid knowledge reference')
    source = yaml.safe_load(read_bytes(under(root, f'config/boundaries/question_sets/{name}.yaml')))
    candidates = source.get('questions', []) + [q for domain in source.get('domains', []) for q in domain.get('questions', [])]
    matches = [q for q in candidates if q.get('id') == reference['questionId']]
    if len(matches) != 1 or not text(matches[0].get('text')) or not isinstance(matches[0].get('source'), dict):
        raise ValueError('Knowledge reference missing or ambiguous')
    # Keep source metadata and applicability, including draft status. No live freshness claim.
    value = json.loads(json.dumps({'questionSet': name, 'question': matches[0],
        'source': source.get('source'), 'maturityGating': source.get('maturity_gating')}, default=str))
    return {**value, 'sha256': digest(value), 'freshness': 'not_reverified'}


@observed('swag.knowledge_preview')
def preview(binding_path: Path | None = None, root: Path = ROOT) -> dict:
    configured = binding_path or os.environ.get('SWAG_KNOWLEDGE_BINDING_FILE')
    base = {'schema': 'swag.knowledge-preview/v1', 'executionAvailable': False,
            'fulfillmentAvailable': False, 'requirements': []}
    if not configured:
        return {**base, 'state': 'not_configured'}
    binding_path = Path(configured).resolve()
    binding = json.loads(read_bytes(binding_path))
    fields(binding, {'schemaVersion', 'projectId', 'repo', 'template', 'inputs'})
    if type(binding['schemaVersion']) is not int or binding['schemaVersion'] != 1 or not text(binding['projectId']):
        raise ValueError('Invalid project binding')
    if not text(binding['repo']):
        raise ValueError('Project root required')
    repo = Path(binding['repo'])
    repo = (repo if repo.is_absolute() else binding_path.parent / repo).resolve()
    if not repo.is_dir():
        raise ValueError('Project root unavailable')
    definition = template(binding['template'], root)
    inputs = binding['inputs']
    slots = {slot for row in definition['requirements'] for slot in row['inputSlots']}
    if not isinstance(inputs, dict) or set(inputs) - slots:
        raise ValueError('Unknown template input slots')
    observations = {}
    for slot in slots:
        selected = inputs.get(slot, [])
        if (not isinstance(selected, list) or len(selected) > 50
                or any(not isinstance(path, str) for path in selected) or len(set(selected)) != len(selected)):
            raise ValueError('Invalid input paths')
        rows = []
        for relative in sorted(selected):
            path = under(repo, relative)
            try:
                raw = read_bytes(path)
                rows.append({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'state': 'read'})
            except FileNotFoundError:
                rows.append({'path': relative, 'sha256': None, 'bytes': None, 'state': 'missing'})
        observations[slot] = rows
    requirements = []
    for row in definition['requirements']:
        knowledge = practice(row['practice'], root)
        selected = {slot: observations[slot] for slot in row['inputSlots']}
        ready = all(files and all(file['state'] == 'read' for file in files) for files in selected.values())
        context = {'projectId': binding['projectId'], 'templateId': definition['id'],
                   'schemaVersion': definition['schemaVersion'], 'requirement': row,
                   'practiceSha256': knowledge['sha256'], 'inputs': selected}
        requirements.append({**row, 'practice': knowledge, 'inputs': selected,
            'inputSha256': digest(context), 'state': 'unassessed' if ready else 'missing_inputs',
            'fulfillment': 'unassessed'})
    result = {**base, 'state': 'preview', 'projectId': binding['projectId'], 'templateId': definition['id'],
              'title': definition['title'], 'templateSha256': digest(definition), 'requirements': requirements}
    result['projectionSha256'] = digest(result)
    return result


@observed('swag.validate_template_decision')
def validate_decision(requirement_id: str, answer: dict, binding_path: Path | None = None, root: Path = ROOT) -> dict:
    """Check supplied output against freshly read inputs; never attest its truth."""
    current = preview(binding_path, root)
    matches = [row for row in current['requirements'] if row['id'] == requirement_id]
    if len(matches) != 1:
        raise ValueError('Unknown requirement')
    row = matches[0]
    fields(answer, {'schema', 'inputSha256', 'mode', 'status', 'value', 'references'})
    if (answer['schema'] != 'swag.decision-answer/v1' or answer['inputSha256'] != row['inputSha256']
            or answer['mode'] != row['decision']['mode']):
        raise ValueError('Stale or mismatched decision context; refresh preview')
    references = answer['references']
    allowed = {row['practice']['sha256']} | {item['sha256'] for files in row['inputs'].values() for item in files if item['sha256']}
    if (not isinstance(references, list) or any(not isinstance(ref, str) for ref in references)
            or len(references) != len(set(references)) or set(references) - allowed):
        raise ValueError('Unbound evidence reference')
    if answer['status'] == 'abstained':
        if answer['value'] is not None:
            raise ValueError('Abstention has no value')
    elif answer['status'] == 'answered':
        if row['state'] != 'unassessed' or not references:
            raise ValueError('Answer requires bound inputs and references')
        value, contract = answer['value'], row['decision']
        if contract['mode'] == 'binary' and type(value) is not bool:
            raise ValueError('Binary answer must be a boolean')
        if contract['mode'] == 'choice' and value not in [option['id'] for option in contract['options']]:
            raise ValueError('Choice is outside supplied options')
        if contract['mode'] == 'score' and (type(value) not in (int, float) or not math.isfinite(value)
                or not contract['minimum'] <= value <= contract['maximum']):
            raise ValueError('Score is outside the declared rubric')
    else:
        raise ValueError('Unknown answer status')
    return {'schema': 'swag.decision-validation/v1', 'requirementId': row['id'],
            'inputSha256': row['inputSha256'], 'answerSha256': digest(answer), 'contractValid': True,
            'correctnessVerified': False, 'fulfillment': 'unassessed', 'executionAuthorized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    try:
        result = preview(args.binding)
    except Exception:
        result = {'schema': 'swag.knowledge-preview/v1', 'state': 'unavailable',
                  'executionAvailable': False, 'fulfillmentAvailable': False, 'requirements': []}
    print(json.dumps(result, allow_nan=False))
