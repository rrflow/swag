"""Project verified offline evaluation evidence into a content-free UI/log export."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from swag_routing_contract import digest, score_output, strict_json, validate_request
from swag_routing_eval import summarize


def read_bound(path: Path, sha: str) -> bytes:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != sha:
        raise ValueError('Evaluation artifact digest mismatch')
    return content


def project_run(directory: Path) -> dict:
    summary = strict_json((directory / 'summary.json').read_bytes())
    protocol = strict_json(read_bound(directory / 'protocol.json', summary['protocolSha256']))
    results = [strict_json(line) for line in read_bound(directory / 'results.jsonl',
               summary['resultsSha256']).splitlines() if line.strip()]
    artifact = strict_json(read_bound(directory / 'artifact-manifest.json',
                                      summary['artifactManifestSha256']))
    if not protocol['cases'] or len(results) != len(protocol['cases']):
        raise ValueError('Incomplete evaluation cannot be projected as complete')
    # This projection consumes our existing scorer, not an arbitrary executable from an artifact.
    scorer = Path(__file__).with_name('swag_routing_contract.py').read_bytes()
    if protocol['implementation'].get('tools/swag_routing_contract.py') != hashlib.sha256(scorer).hexdigest():
        raise ValueError('Scorer identity changed; use the matching reviewed projection implementation')
    cases = []
    seen = set()
    for expected_case, row in zip(protocol['cases'], results):
        validate_request(expected_case['request'])
        if row['caseId'] != expected_case['caseId'] or row['caseId'] in seen:
            raise ValueError('Missing, duplicated or reordered case identity')
        seen.add(row['caseId'])
        if row['requestSha256'] != digest(expected_case['request']) or row['expected'] != expected_case['expected']:
            raise ValueError('Case input or label identity mismatch')
        score = score_output(row.get('rawOutput', ''), expected_case['request'], expected_case['expected'])
        if row.get('errorClass'):
            score['validOutput'] = False
            score['matched'] = False
        if any(row.get(key) != value for key, value in score.items()):
            raise ValueError('Reported scores disagree with retained outputs')
        elapsed = row['elapsedSeconds']
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('Invalid latency evidence')
        cases.append({'caseRef': digest(row['caseId'])[:16], **score, 'elapsedSeconds': elapsed})
    metrics = summarize(results, protocol['limits'])
    if any(summary.get(key) != value for key, value in metrics.items()):
        raise ValueError('Summary metrics disagree with retained case evidence')
    if summary['scope'] != protocol['scope'] or summary['scope'] not in {'development', 'acceptance'}:
        raise ValueError('Scope mismatch')
    signals = []
    for key, signal, description in (
        ('policyViolations', 'swag_route_policy_violation', 'Route proposals violated supplied eligibility constraints'),
        ('falseAbstentions', 'swag_route_false_abstention', 'Route proposals abstained despite an eligible choice'),
        ('invalidOutputs', 'swag_route_invalid_output', 'Responses or transport did not satisfy the output contract'),
    ):
        if metrics[key]:
            signals.append({'signal': signal, 'rule_version': 1, 'severity': 'warn',
                            'summary': description, 'score': float(metrics[key]),
                            'evidence': [{'kind': 'turn', 'tool_id': None, 'excerpt': None}]})
    if metrics['matched'] < metrics['cases']:
        signals.append({'signal': 'swag_evaluation_mismatch', 'rule_version': 1, 'severity': 'warn',
                        'summary': 'Evaluation choices differed from expected labels',
                        'score': float(metrics['cases'] - metrics['matched']),
                        'evidence': [{'kind': 'turn', 'tool_id': None, 'excerpt': None}]})
    return {
        'schemaVersion': 1, 'kind': 'swag.offline_evidence',
        # Equal responses from different checkpoints are distinct comparison evidence.
        'runId': digest([summary['protocolSha256'], summary['resultsSha256'],
                         summary['artifactManifestSha256']]),
        'completedAt': summary['completedAt'], 'scope': summary['scope'],
        'model': {'name': artifact.get('model', 'unreported'), 'precision': artifact.get('precision', 'unreported'),
                  'customCheckpoint': artifact.get('custom_checkpoint') is True},
        'provenance': {key: summary[key] for key in ('protocolSha256', 'resultsSha256', 'artifactManifestSha256')},
        'metrics': metrics, 'cases': cases, 'signals': signals,
        'learningSuggestions': [
            {'kind': 'unsupervised_triage', 'state': 'suggested' if signals else 'no_signal',
             'reason': 'Group repeated failure patterns for review; clustering is not a correctness label.'},
            {'kind': 'supervised_review', 'state': 'suggested' if signals else 'no_signal',
             'reason': 'Review source evidence, corrections and consent before dataset admission.'}],
        'authority': {'engineReceipt': None, 'trainingAuthorized': False, 'promotionAuthorized': False,
                      'connectomeIntegrated': False, 'rroflowAccepted': False},
    }


def report_record(projection: dict, project: str) -> dict:
    import re
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', project):
        raise ValueError('Project must be a slug')
    # One point-in-time evidence-report event, not a reconstruction of inference turns.
    identity = str(uuid5(NAMESPACE_URL, 'swag-evidence:' + project + ':' + projection['runId']))
    stamp = projection['completedAt']
    if datetime.fromisoformat(stamp.replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('Completion timestamp requires timezone')
    return {'schema': 'rroflow.turn/v1', 'event_id': identity,
            'agent': 'swag-evidence', 'agent_version': '0.1.0', 'provider': 'none', 'model': None,
            'session_id': projection['runId'], 'turn_key': 'evaluation_report',
            'subagent': None, 'prompt_author': None, 'started_at': stamp, 'ended_at': stamp,
            'cwd': '', 'git_branch': '', 'project': project,
            'usage': {'input_tokens': 0, 'output_tokens': 0, 'cache_read_tokens': 0,
                      'cache_write_tokens': 0, 'input_includes_cache': False},
            'termination': 'completed', 'compacted': False,
            'tools': [], 'tools_unfinished': 0, 'content': None,
            'signals': projection['signals'], 'collector': 'swag-evidence/0.1.0'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--project', default='swag')
    args = parser.parse_args()
    projection = project_run(args.run_dir)
    record = report_record(projection, args.project)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in [('evidence.json', projection), ('rroflow.turn.json', record)]:
        (args.output_dir / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'runId': projection['runId'], 'cases': len(projection['cases']),
                      'signals': len(projection['signals']), 'published': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
