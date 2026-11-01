"""Fit a fixed multinomial Naive Bayes baseline on the provisional train split."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import re
import statistics
import time

from swag_routing_contract import canonical_bytes, strict_json
from swag_task_corpus import LABELS, lines, sha, verify

MODEL_NAME = 'multinomial_naive_bayes_cpu'


def tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.casefold(), flags=re.UNICODE)


def fit(training: list[dict]) -> dict:
    """Laplace smoothing alpha=1 and empirical class priors, fixed before eval."""
    documents = Counter()
    counts = {label: Counter() for label in sorted(LABELS)}
    for row in training:
        label = row['taskFamily']
        if label not in LABELS or not isinstance(row['taskText'], str):
            raise ValueError('Invalid intent training row')
        documents[label] += 1
        counts[label].update(tokenize(row['taskText']))
    if set(documents) != LABELS:
        raise ValueError('Training must contain every intent class')
    vocabulary = sorted({word for values in counts.values() for word in values})
    if not vocabulary:
        raise ValueError('Training vocabulary is empty')
    return {'schemaVersion': 1, 'model': MODEL_NAME, 'alpha': 1,
            'tokenizer': 'unicode_word_casefold', 'vocabulary': vocabulary,
            'documentCounts': dict(documents),
            'tokenCounts': {label: dict(values) for label, values in counts.items()}}


def predict(model: dict, text: str) -> tuple[str, dict[str, float]]:
    vocabulary = set(model['vocabulary'])
    observed = Counter(word for word in tokenize(text) if word in vocabulary)
    documents = model['documentCounts']
    scores = {}
    for label in sorted(LABELS):
        counts = model['tokenCounts'][label]
        denominator = sum(counts.values()) + len(vocabulary)
        score = math.log(documents[label] / sum(documents.values()))
        score += sum(n * math.log((counts.get(word, 0) + 1) / denominator)
                     for word, n in observed.items())
        scores[label] = score
    # Alphabetical tie-break is fixed; scores are not calibrated confidence.
    return min(scores, key=lambda label: (-scores[label], label)), scores


def run(corpus: Path, output: Path) -> dict:
    manifest = verify(corpus)
    training = lines(corpus / 'train.cases.jsonl')
    output.mkdir(parents=True, exist_ok=False)
    protocol = {'schemaVersion': 1, 'scope': 'provisional_intent_development',
                'algorithm': MODEL_NAME, 'alpha': 1, 'priors': 'empirical',
                'tokenizer': 'unicode_word_casefold', 'unknownTokens': 'ignore',
                'tieBreak': 'alphabetical', 'tuning': 'none',
                'trainSha256': manifest['files']['train.cases.jsonl'],
                'developmentSha256': manifest['files']['development.cases.jsonl'],
                'runnerSha256': sha(Path(__file__).read_bytes())}
    protocol_bytes = canonical_bytes(protocol) + b'\n'
    (output / 'protocol.json').write_bytes(protocol_bytes)
    started = time.perf_counter()
    model = fit(training)
    fit_seconds = time.perf_counter() - started
    model_bytes = canonical_bytes(model) + b'\n'
    (output / 'model.json').write_bytes(model_bytes)
    # Inference uses the saved/reloaded artifact, never an in-memory-only model.
    reloaded = strict_json((output / 'model.json').read_bytes())
    if reloaded != model:
        raise ValueError('Reloaded baseline differs from fitted model')
    artifact = {'schemaVersion': 1, 'model': MODEL_NAME,
                'modelSha256': sha(model_bytes), 'modelBytes': len(model_bytes),
                'trainingCases': len(training), 'trainSha256': protocol['trainSha256'],
                'fitSeconds': fit_seconds, 'pythonVersion': platform.python_version(),
                'platform': platform.platform(), 'processor': platform.processor(),
                'runnerSha256': protocol['runnerSha256'], 'totalServingMemoryMeasured': False}
    artifact_bytes = canonical_bytes(artifact) + b'\n'
    (output / 'artifact-manifest.json').write_bytes(artifact_bytes)
    corpus_bytes = (corpus / 'manifest.json').read_bytes()
    (output / 'corpus-manifest.json').write_bytes(corpus_bytes)
    # Development labels are first consulted after fitting and saving the artifact.
    results = []
    for case in lines(corpus / 'development.cases.jsonl'):
        started = time.perf_counter()
        choice, scores = predict(reloaded, case['taskText'])
        elapsed = time.perf_counter() - started
        results.append({'taskId': case['taskId'], 'expected': case['taskFamily'],
                        'rawOutput': json.dumps({'taskFamily': choice}),
                        'valid': True, 'matched': choice == case['taskFamily'],
                        'elapsedSeconds': elapsed, 'logScores': scores})
    result_bytes = b''.join(canonical_bytes(row) + b'\n' for row in results)
    (output / 'results.jsonl').write_bytes(result_bytes)
    summary = {'schemaVersion': 1, 'model': MODEL_NAME, 'cases': len(results),
               'matched': sum(row['matched'] for row in results), 'invalid': 0,
               'warmMedianSeconds': statistics.median(row['elapsedSeconds'] for row in results[1:] or results),
               'completedAt': datetime.now(timezone.utc).isoformat(),
               'corpusManifestSha256': sha(corpus_bytes),
               'artifactManifestSha256': sha(artifact_bytes), 'protocolSha256': sha(protocol_bytes),
               'resultsSha256': sha(result_bytes), 'humanReviewed': False,
               'providerRoutingEvaluated': False, 'deploymentQualified': False}
    (output / 'summary.json').write_bytes(canonical_bytes(summary) + b'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.corpus_dir, args.output_dir)))
