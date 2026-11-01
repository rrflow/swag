"""Produce deduplicated review proposals from verified runs, without execution authority."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from swag_evidence_projection import project_run
from swag_routing_contract import canonical_bytes, digest


def propose(directories: list[Path]) -> dict:
    runs, groups = {}, {}
    for directory in directories:
        view = project_run(directory)
        if view['runId'] in runs:
            continue
        runs[view['runId']] = view['provenance']
        for signal in view['signals']:
            group = groups.setdefault(signal['signal'], {'signal': signal['signal'], 'ruleVersion': 1,
                'observedCount': 0, 'evidence': [], 'proposedAction': 'review_source_bound_failure_examples',
                'labelStatus': 'unknown', 'trainingAuthorized': False, 'promotionAuthorized': False})
            group['observedCount'] += int(signal['score'])
            group['evidence'].append({'runId': view['runId'], **view['provenance']})
    candidates = []
    for signal in sorted(groups):
        row = groups[signal]
        row['evidence'].sort(key=lambda item: item['runId'])
        row['candidateId'] = digest(row)
        candidates.append(row)
    return {'schemaVersion': 1, 'kind': 'swag.learning_review_proposals',
            'sourceIdentity': digest(sorted(runs.items())), 'runs': len(runs), 'candidates': candidates,
            'createdAt': datetime.now(timezone.utc).isoformat(), 'engineIntegrated': False,
            'routineExecuted': False, 'note': 'Stateless projection for engine review; no scheduler, training or promotion.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = propose(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical_bytes(result) + b'\n')
    print(json.dumps({'runs': result['runs'], 'candidates': len(result['candidates']),
                      'sourceIdentity': result['sourceIdentity'], 'routineExecuted': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
