"""Recompute intent metrics and a majority baseline from retained experiment outputs."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from swag_task_corpus import LABELS, canonical_bytes, lines, strict_json, verify


def metrics(expected: list[str], actual: list[str | None]) -> dict:
    if not expected or len(expected) != len(actual) or any(label not in LABELS for label in expected):
        raise ValueError('Require complete, nonempty, known intent targets')
    matrix = {label: {choice: 0 for choice in sorted(LABELS) + ['invalid']} for label in sorted(LABELS)}
    for target, prediction in zip(expected, actual):
        matrix[target][prediction if prediction in LABELS else 'invalid'] += 1
    recall = {label: matrix[label][label] / sum(matrix[label].values()) for label in LABELS
              if sum(matrix[label].values())}
    matched = sum(a == b for a, b in zip(expected, actual))
    return {'cases': len(expected), 'matched': matched, 'accuracy': matched / len(expected),
            'balancedAccuracy': sum(recall.values()) / len(recall), 'recallByClass': recall,
            'confusionMatrix': matrix}


def compare(corpus: Path, runs: list[Path]) -> dict:
    manifest = verify(corpus)
    corpus_sha = hashlib.sha256((corpus / 'manifest.json').read_bytes()).hexdigest()
    cases = lines(corpus / 'development.cases.jsonl')
    expected = [row['taskFamily'] for row in cases]
    counts = Counter(row['taskFamily'] for row in lines(corpus / 'train.cases.jsonl'))
    majority = sorted(counts, key=lambda label: (-counts[label], label))[0]
    results = [{'model': 'majority_training_label', 'label': majority,
                **metrics(expected, [majority] * len(cases))}]
    for run in runs:
        summary = strict_json((run / 'summary.json').read_bytes())
        content = (run / 'results.jsonl').read_bytes()
        if summary['corpusManifestSha256'] != corpus_sha or hashlib.sha256(content).hexdigest() != summary['resultsSha256']:
            raise ValueError('Corpus identity or result hash mismatch')
        rows = lines(run / 'results.jsonl')
        if len(rows) != len(cases):
            raise ValueError('Incomplete intent run')
        predictions = []
        for case, row in zip(cases, rows):
            if row['taskId'] != case['taskId'] or row['expected'] != case['taskFamily']:
                raise ValueError('Changed, missing or reordered intent cases')
            prediction = None
            if 'answer' in row:
                prediction = row['answer'].get('choice')
            elif row.get('valid'):
                parsed = strict_json(row['rawOutput'])
                if isinstance(parsed, dict) and set(parsed) == {'taskFamily'}:
                    prediction = parsed['taskFamily']
            if prediction not in LABELS:
                prediction = None
            if row['matched'] != (prediction == case['taskFamily']):
                raise ValueError('Intent score does not match retained output')
            predictions.append(prediction)
        recomputed = metrics(expected, predictions)
        if summary['matched'] != recomputed['matched'] or summary['cases'] != recomputed['cases']:
            raise ValueError('Intent summary disagrees with raw results')
        results.append({'model': summary['model'], 'resultsSha256': summary['resultsSha256'],
                        'warmMedianSeconds': summary['warmMedianSeconds'], **recomputed})
    return {'schemaVersion': 1, 'scope': 'provisional_intent_development',
            'corpusManifestSha256': corpus_sha, 'results': results, 'deploymentQualified': False,
            'limitations': ['21 project-held-out tasks with assistant-inferred labels; no independent human review.',
                           'Typed d1 choices and Qwen chat generation use different interfaces.',
                           'These are task-family labels, not measured best-provider choices.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-dir', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.corpus_dir, args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical_bytes(result) + b'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
