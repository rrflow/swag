"""Score competitor runs on the same rows: accuracy, calibration, latency and paired significance.

    python bench/score.py --rows bench/data/public_rows.jsonl bench/results/*.jsonl

For every arm and benchmark:
- accuracy with a Wilson 95% interval; an error or a missing row counts as wrong
- expected calibration error (ten equal-width bins on the top option's probability) and the
  multi-class Brier score; a well-calibrated model's confidence matches how often it is right
- median and 95th percentile seconds per request, as measured by the client (network included)
- an exact McNemar test on the rows both arms answered, for every pair of arms
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_systemone as contract  # noqa: E402


def wilson(hits: int, total: int, z: float = 1.96) -> list[float]:
    if not total:
        return [0.0, 0.0]
    rate = hits / total
    centre = (rate + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [round(centre - margin, 4), round(centre + margin, 4)]


def mcnemar(only_first: int, only_second: int) -> float:
    """Two-sided exact McNemar p-value from the discordant pairs."""
    n = only_first + only_second
    if n == 0:
        return 1.0
    k = min(only_first, only_second)
    tail = math.fsum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def judge(row: dict, result: dict | None) -> dict:
    """Per question: the distribution an arm gave and whether its top option was the expected one."""
    outcome = {'answered': False, 'correct': False, 'top': None, 'brier': None, 'seconds': None}
    if result is None or result.get('status') != 'ok':
        return outcome
    outcome['seconds'] = result.get('seconds')
    hits, tops, briers = [], [], []
    for question_id, expected in row['expected'].items():
        question = contract.validate_question(question_id, row['questions'][question_id])
        try:
            distribution = contract.distribution_from_answer(question, result['answers'][question_id])
        except (contract.ContractError, KeyError, TypeError):
            return outcome
        best = max(distribution, key=distribution.__getitem__)
        hits.append(best == str(expected))
        tops.append(distribution[best])
        briers.append(math.fsum((distribution[key] - (1.0 if key == str(expected) else 0.0)) ** 2 for key in distribution))
    outcome.update(answered=True, correct=all(hits), top=statistics.fmean(tops), brier=statistics.fmean(briers))
    return outcome


def calibration_error(outcomes: list[dict]) -> float | None:
    rows = [item for item in outcomes if item['answered']]
    if not rows:
        return None
    bins: list[list[dict]] = [[] for _ in range(10)]
    for item in rows:
        bins[min(9, int(item['top'] * 10))].append(item)
    return round(math.fsum(len(group) / len(rows) * abs(statistics.fmean(i['top'] for i in group)
                                                           - statistics.fmean(1.0 if i['correct'] else 0.0 for i in group))
                           for group in bins if group), 4)


def summarize(outcomes: list[dict]) -> dict:
    hits = sum(item['correct'] for item in outcomes)
    seconds = sorted(item['seconds'] for item in outcomes if item['seconds'] is not None)
    answered = [item for item in outcomes if item['answered']]
    return {
        'rows': len(outcomes), 'errors': len(outcomes) - len(answered), 'accuracy': round(hits / len(outcomes), 4) if outcomes else None,
        'ci95': wilson(hits, len(outcomes)), 'ece': calibration_error(outcomes),
        'meanTopProbability': round(statistics.fmean(item['top'] for item in answered), 4) if answered else None,
        'brier': round(statistics.fmean(item['brier'] for item in answered), 4) if answered else None,
        'medianSeconds': round(statistics.median(seconds), 4) if seconds else None,
        'p95Seconds': round(seconds[min(len(seconds) - 1, int(0.95 * len(seconds)))], 4) if seconds else None,
    }


def score(rows: list[dict], runs: dict[str, list[dict]]) -> dict:
    by_id = {name: {item['id']: item for item in results} for name, results in runs.items()}
    benchmarks = sorted({row.get('benchmark') or 'all' for row in rows})
    judged = {name: {row['id']: judge(row, results.get(row['id'])) for row in rows} for name, results in by_id.items()}
    report: dict = {'arms': {}, 'pairs': []}
    for name in runs:
        report['arms'][name] = {benchmark: summarize([judged[name][row['id']] for row in rows
                                                      if (row.get('benchmark') or 'all') == benchmark]) for benchmark in benchmarks}
    names = list(runs)
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            for benchmark in benchmarks:
                shared = [row['id'] for row in rows if (row.get('benchmark') or 'all') == benchmark
                          and judged[first][row['id']]['answered'] and judged[second][row['id']]['answered']]
                only_first = sum(judged[first][i]['correct'] and not judged[second][i]['correct'] for i in shared)
                only_second = sum(judged[second][i]['correct'] and not judged[first][i]['correct'] for i in shared)
                report['pairs'].append({'benchmark': benchmark, 'first': first, 'second': second, 'shared': len(shared),
                                        'onlyFirstCorrect': only_first, 'onlySecondCorrect': only_second,
                                        'p': mcnemar(only_first, only_second)})
    return report


def table(report: dict) -> str:
    lines = ['| Arm | Benchmark | Rows | Accuracy (95% CI) | ECE | Brier | Errors | Median s | p95 s |', '|---|---|---|---|---|---|---|---|---|']
    for arm, benchmarks in report['arms'].items():
        for benchmark, value in benchmarks.items():
            lines.append(f"| {arm} | {benchmark} | {value['rows']} | {value['accuracy']} ({value['ci95'][0]}-{value['ci95'][1]}) | "
                         f"{value['ece']} | {value['brier']} | {value['errors']} | {value['medianSeconds']} | {value['p95Seconds']} |")
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--json', type=Path, help='Also write the full report here')
    parser.add_argument('runs', type=Path, nargs='+', help='One results .jsonl per arm, named after the arm')
    arguments = parser.parse_args(argv)
    rows = [json.loads(line) for line in arguments.rows.read_text(encoding='utf-8').splitlines() if line.strip()]
    runs = {path.stem: [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
            for path in arguments.runs}
    # Score every row any arm was sent; a row an arm never answered counts against that arm.
    ran = set.union(*({item['id'] for item in results} for results in runs.values()))
    rows = [row for row in rows if row['id'] in ran]
    report = score(rows, runs)
    if arguments.json:
        arguments.json.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(table(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
