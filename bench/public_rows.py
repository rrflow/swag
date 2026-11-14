"""Rebuild the Decision Index's CRUXEval and When2Call rows from their pinned public sources.

Own code, written from reading the Decision Index kit's published build recipe; no third-party code
runs. Ground truth is not assistant-written: CRUXEval's comes from executing the code, When2Call's from
the published dataset. Row counts are checked against the kit's documented totals (570 and 3,652).

    python bench/public_rows.py            # writes bench/data/public_rows.jsonl (about 9 MB, not committed)

Each row is a SystemOne request (`state`, `questions`) plus `id`, `benchmark` and `expected`.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import random
from urllib import request

BENCH = Path(__file__).resolve().parent
DATA = BENCH / 'data'
CRUX_REVISION = '190faf16d175b5847b0af05d937872b1fb395942'
CRUX_BASE = f'https://raw.githubusercontent.com/facebookresearch/cruxeval/{CRUX_REVISION}'
WHEN2CALL_URL = ('https://huggingface.co/datasets/nvidia/When2Call/resolve/'
                 '0582f7749df63a96fdc3070932e83e72396ace53/test/when2call_test_mcq.jsonl')
WHEN2CALL_SHA256 = '8c3694e583eeeb8dbc297e6cd90da70efc68efa4b6adb7227523e828c6b7b14c'
SEED = 20260917
CRUX_INSTRUCTIONS = 'Choose the correct output of f called with the supplied input arguments. Candidates are Python literal values.'
WHEN2CALL_INSTRUCTIONS = "Which response should the assistant give to the user's question, given the available tools?"
EXPECTED = {'CRUXEval': 570, 'When2Call': 3652}


def fetch(url: str, name: str) -> Path:
    target = DATA / name
    if not target.exists():
        with request.urlopen(request.Request(url, headers={'User-Agent': 'swag-benchmark'}), timeout=120) as response:
            target.write_bytes(response.read())
    return target


def crux() -> list[dict]:
    source = {}
    for line in fetch(f'{CRUX_BASE}/data/cruxeval.jsonl', 'cruxeval.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        source[row['id']] = row
    generations = json.loads(fetch(f'{CRUX_BASE}/samples/model_generations/sample_codellama-7b_temp0.2_output/generations.json',
                                   'generations.json').read_text(encoding='utf-8'))
    flags = json.loads(fetch(f'{CRUX_BASE}/samples/evaluation_results/sample_scored_codellama-7b_temp0.2_output.json',
                             'scored.json').read_text(encoding='utf-8'))['raw_scored_generations']
    rows = []
    for sample_id, item in sorted(source.items()):
        values: list = []
        gold = ast.literal_eval(item['output'])

        def add(value: object) -> None:
            if not any(value == prior for prior in values):
                values.append(value)

        add(gold)
        # Distractors are a reference model's wrong outputs for the same function.
        for raw, passed in zip(generations.get(sample_id, []), flags.get(sample_id, [])):
            if passed:
                continue
            try:
                add(ast.literal_eval(raw))
            except (ValueError, SyntaxError, MemoryError, TypeError):
                continue
        if len(values) < 2:
            continue
        values = values[:10]
        random.Random(f'{SEED}:CRUX:{sample_id}').shuffle(values)
        correct = next(index for index, value in enumerate(values) if value == gold)
        rows.append({'id': f'CRUXEval:{sample_id}', 'benchmark': 'CRUXEval',
                     'state': {'code': item['code'], 'input': item['input'], 'task': 'CRUXEval output selection'},
                     'questions': {'answer': {'type': 'choice', 'instructions': CRUX_INSTRUCTIONS,
                                              'criteria': {f'option_{index}': repr(value) for index, value in enumerate(values)}}},
                     'expected': {'answer': f'option_{correct}'}})
    return rows


def when2call() -> list[dict]:
    path = fetch(WHEN2CALL_URL, 'when2call_test_mcq.jsonl')
    if hashlib.sha256(path.read_bytes()).hexdigest() != WHEN2CALL_SHA256:
        raise SystemExit('The When2Call source changed; refusing to build rows from it.')
    order = ['direct', 'tool_call', 'request_for_info', 'cannot_answer']
    keys = ['A', 'B', 'C', 'D']
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        rows.append({'id': f"When2Call:{row['uuid']}", 'benchmark': 'When2Call',
                     'state': {'tools': [json.loads(tool) for tool in row['tools']], 'question': row['question']},
                     'questions': {'q': {'type': 'choice', 'instructions': WHEN2CALL_INSTRUCTIONS,
                                         'criteria': dict(zip(keys, (row['answers'][key] for key in order)))}},
                     'expected': {'q': keys[order.index(row['correct_answer'])]}})
    return rows


def main() -> int:
    DATA.mkdir(exist_ok=True)
    rows = crux() + when2call()
    counts = {name: sum(row['benchmark'] == name for row in rows) for name in EXPECTED}
    print(json.dumps({'rows': counts, 'expected': EXPECTED}))
    if counts != EXPECTED:
        raise SystemExit("Row counts differ from the kit's documented totals; the rebuild is suspect.")
    with (DATA / 'public_rows.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
