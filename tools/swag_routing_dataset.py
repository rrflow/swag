"""Admit reviewed observations into immutable, project/time-separated exports."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from swag_routing_contract import (canonical_bytes, digest, expected_route, messages,
                                   strict_json, validate, validate_request)

SPLITS = ('train', 'development', 'acceptance')


def read_jsonl(path: Path) -> tuple[list[dict], str]:
    content = path.read_bytes()
    if content and not content.endswith(b'\n'):
        raise ValueError('Incomplete JSONL tail')
    rows = [strict_json(line) for line in content.splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('JSONL rows must be objects')
    return rows, hashlib.sha256(content).hexdigest()


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    return result.astimezone(timezone.utc)


def validate_split_policy(policy: dict) -> dict:
    if set(policy) != {'schemaVersion', 'splits'} or policy['schemaVersion'] != 1:
        raise ValueError('Invalid split policy')
    if set(policy['splits']) != set(SPLITS):
        raise ValueError('Require train, development and acceptance split windows')
    project_owners, previous_end = {}, None
    for split in SPLITS:
        entry = policy['splits'][split]
        if set(entry) != {'projects', 'startInclusive', 'endExclusive'}:
            raise ValueError('Each split requires project identities and a time window')
        start, end = timestamp(entry['startInclusive']), timestamp(entry['endExclusive'])
        if start >= end or (previous_end is not None and start < previous_end):
            raise ValueError('Split time windows must be ordered and disjoint')
        previous_end = end
        if not isinstance(entry['projects'], list):
            raise ValueError('projects must be a list')
        for project in entry['projects']:
            if not isinstance(project, str) or not project.strip() or project in project_owners:
                raise ValueError('Project identities must be nonempty and split-disjoint')
            project_owners[project] = split
    return project_owners


def verify_artifact(reference: dict, evidence_root: Path) -> bytes:
    root = evidence_root.resolve(strict=True)
    relative = Path(reference['path'])
    if relative.is_absolute() or relative.drive or '..' in relative.parts:
        raise ValueError('Evidence must use a relative path inside evidence root')
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Evidence escapes root or is not a file')
    content = path.read_bytes()
    if not content.strip() or hashlib.sha256(content).hexdigest() != reference['sha256']:
        raise ValueError('Evidence missing content or digest mismatch')
    return content


def admit(observations_path: Path, reviews_path: Path, policy_path: Path,
          evidence_root: Path, output: Path) -> dict:
    observations, observations_sha = read_jsonl(observations_path)
    reviews, reviews_sha = read_jsonl(reviews_path)
    policy_bytes = policy_path.read_bytes()
    policy = strict_json(policy_bytes)
    project_owners = validate_split_policy(policy)
    by_id = {}
    for observation in observations:
        validate(observation, 'passive_capture.schema.json')
        if observation['record_id'] in by_id:
            raise ValueError('Duplicate observation identity')
        by_id[observation['record_id']] = observation
    exports = {split: [] for split in SPLITS}
    seen_reviews, groups, requests, task_texts, tasks, repositories = set(), {}, {}, {}, {}, {}
    # Fully validate before reserving output: a rejected review creates no dataset.
    for review in reviews:
        validate(review, 'routing_review.schema.json')
        if review['sourceKind'] != 'real_observation':
            raise ValueError('New dataset admission requires reviewed real observations in every split')
        record_id = review['recordId']
        if record_id in seen_reviews or record_id not in by_id:
            raise ValueError('Duplicate review or missing observation')
        seen_reviews.add(record_id)
        observation = by_id[record_id]
        if review['observationSha256'] != digest(observation):
            raise ValueError('Observation changed after review')
        if review['reviewerId'].strip().casefold() == review['labelAuthorId'].strip().casefold():
            raise ValueError('Label requires an independent reviewer identity')
        captured = timestamp(observation['captured_at'])
        reviewed = timestamp(review['reviewedAt'])
        if reviewed < captured or reviewed > datetime.now(timezone.utc):
            raise ValueError('Review time must follow capture and not be in the future')
        split = project_owners.get(review['projectGroup'])
        if split is None:
            raise ValueError('Project has no declared split')
        repository = observation['repo_context']['repo_root'].replace('\\', '/').rstrip('/').casefold()
        if not repository:
            raise ValueError('Observation needs an explicit repository identity')
        if repository in repositories and repositories[repository] != review['projectGroup']:
            raise ValueError('One repository cannot be relabelled as multiple project groups')
        repositories[repository] = review['projectGroup']
        window = policy['splits'][split]
        if not timestamp(window['startInclusive']) <= captured < timestamp(window['endExclusive']):
            raise ValueError('Capture lies outside its project split time window')
        if not review['consent']['training' if split == 'train' else 'evaluation']:
            raise ValueError('Required dataset consent not granted')
        if split == 'acceptance' and (review['previouslyUsed'] or review['sourceKind'] != 'real_observation'):
            raise ValueError('Acceptance requires unseen real observations')
        evidence = {kind: verify_artifact(ref, evidence_root)
                    for kind, ref in review['evidence'].items()}
        request, expected = review['request'], review['expected']
        validate_request(request)
        validate(expected, 'routing_decision.schema.json')
        if request['taskText'] != observation['intent_text']:
            raise ValueError('Request task must match reviewed capture intent')
        snapshot = strict_json(evidence['candidateSnapshot'])
        if snapshot != request['candidates']:
            raise ValueError('Candidate snapshot does not match request')
        if expected_route(request) != expected:
            raise ValueError('Reviewed label contradicts the bounded policy')
        # Reject leakage rather than silently rebalance or relabel examples.
        for mapping, key in ((groups, review['leakageGroup']), (requests, digest(request)),
                             (task_texts, ' '.join(request['taskText'].casefold().split())),
                             (tasks, observation['task_id'])):
            if key in mapping and mapping[key] != split:
                raise ValueError('Cross-split task, request or leakage-group overlap')
            mapping[key] = split
        if any(row['requestSha256'] == digest(request) for row in exports[split]):
            raise ValueError('Duplicate request within split')
        exports[split].append({
            'caseId': record_id, 'projectGroup': review['projectGroup'],
            'leakageGroup': review['leakageGroup'], 'sourceKind': review['sourceKind'],
            'observationSha256': digest(observation), 'reviewSha256': digest(review),
            'requestSha256': digest(request), 'request': request, 'expected': expected,
        })
    if not any(exports.values()):
        raise ValueError('No reviewed observations admitted')
    output.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for split, rows in exports.items():
        # Acceptance is intentionally never exported as assistant-target chat data.
        artifacts[f'{split}.cases.jsonl'] = rows
        if split != 'acceptance':
            artifacts[f'{split}.chat.jsonl'] = [
                {'messages': messages(row['request'], row['expected'])} for row in rows]
    hashes = {}
    for name, rows in artifacts.items():
        content = b''.join(canonical_bytes(row) + b'\n' for row in rows)
        (output / name).write_bytes(content)
        hashes[name] = hashlib.sha256(content).hexdigest()
    manifest = {
        'schemaVersion': 1, 'scope': 'offline_reviewed_bounded_routing',
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'observationsSha256': observations_sha, 'reviewsSha256': reviews_sha,
        'splitPolicySha256': hashlib.sha256(policy_bytes).hexdigest(),
        'splitPolicy': policy, 'counts': {split: len(rows) for split, rows in exports.items()},
        'unreviewedCount': len(by_id) - len(seen_reviews), 'files': hashes,
        'reviewAuthentication': 'local_attestations_not_cryptographically_verified',
        'deploymentQualified': False,
    }
    # Completion marker written last; interruption leaves an unusable partial export.
    (output / 'manifest.json').write_bytes(canonical_bytes(manifest) + b'\n')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', type=Path, required=True)
    parser.add_argument('--reviews', type=Path, required=True)
    parser.add_argument('--split-policy', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = admit(args.observations, args.reviews, args.split_policy,
                   args.evidence_root, args.output_dir)
    print(json.dumps({'counts': result['counts'], 'unreviewedCount': result['unreviewedCount'],
                      'output': str(args.output_dir), 'deploymentQualified': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
