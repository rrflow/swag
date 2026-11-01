"""Collect real owner-repository PR tasks for review; never invent optimal routes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

REPOSITORIES = ('rrflow/rrflow-development', 'rrflow/connectome-development', 'rrflow/rroflow-development')


def gh_json(arguments: list[str]) -> object:
    completed = subprocess.run(['gh', *arguments], capture_output=True, text=True, timeout=120)
    if completed.returncode:
        raise RuntimeError('GitHub source collection failed; credentials and response bodies omitted')
    return json.loads(completed.stdout)


def suggested_family(paths: list[str]) -> tuple[str | None, str]:
    code = [path for path in paths if not path.endswith(('.md', '.png', '.svg', '.json'))]
    if not code:
        return 'documentation', 'Changed paths are documentation/data only; inspect data-only changes manually.'
    categories = set()
    for path in code:
        if path.startswith(('.github/', 'deploy/', 'scripts/ci/')):
            categories.add('build_release')
        elif path.startswith(('src/', 'src-tauri/')):
            categories.add('interface')
        elif 'rroflow-' in path:
            categories.add('observability')
        elif path.startswith(('crates/persistence/', 'crates/storage/')) or '/rrd-kv/' in path or '/rrd-db/' in path:
            categories.add('storage')
        elif path.startswith('crates/'):
            categories.add('engine')
        else:
            categories.add('other')
    if len(categories) != 1 or 'other' in categories:
        return None, 'Mixed or unmapped changed paths require review; no label assigned.'
    return next(iter(categories)), 'Path-based proposal only; not an independently reviewed intent label.'


def collect(output: Path, limit: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    raw_dir = output / 'sources'
    raw_dir.mkdir()
    rows = []
    for repository in REPOSITORIES:
        pulls = gh_json(['pr', 'list', '--repo', repository, '--state', 'merged', '--limit', str(limit),
                         '--json', 'number,title,url,mergedAt,headRefOid,mergeCommit'])
        for pull in pulls:
            details = gh_json(['pr', 'view', str(pull['number']), '--repo', repository,
                               '--json', 'files,statusCheckRollup,reviewDecision'])
            source = {'repository': repository, **pull, **details}
            encoded = json.dumps(source, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
            sha = hashlib.sha256(encoded).hexdigest()
            (raw_dir / (sha + '.json')).write_bytes(encoded)
            paths = [item['path'] for item in details['files']]
            family, rationale = suggested_family(paths)
            rows.append({'schemaVersion': 1, 'taskId': repository + '#' + str(pull['number']),
                         'sourceUrl': pull['url'], 'sourceSha256': sha, 'sourceRevision': pull['headRefOid'],
                         'project': repository, 'observedAt': pull['mergedAt'], 'taskText': pull['title'],
                         'changedPaths': paths, 'suggestedTaskFamily': family,
                         'suggestionMethod': 'changed_path_rules', 'suggestionRationale': rationale,
                         'reviewStatus': 'pending', 'reviewerId': None, 'label': None,
                         'observedProviderRoute': None, 'optimalProviderRoute': None,
                         'trainingAdmitted': False})
            print(json.dumps({'taskId': rows[-1]['taskId'], 'reviewStatus': 'pending'}), flush=True)
    content = b''.join((json.dumps(row, sort_keys=True, ensure_ascii=True) + '\n').encode() for row in rows)
    (output / 'review-candidates.jsonl').write_bytes(content)
    manifest = {'schemaVersion': 1, 'collectedAt': datetime.now(timezone.utc).isoformat(),
                'sourceKind': 'real_merged_development_tasks', 'repositories': list(REPOSITORIES),
                'tasks': len(rows), 'candidateSha256': hashlib.sha256(content).hexdigest(),
                'reviewedLabels': 0, 'trainingAdmitted': False,
                'limitation': 'Merged code and check metadata are not evidence of optimal model/effort routing.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--limit-per-repository', type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.limit_per_repository <= 100:
        parser.error('limit must be 1..100')
    print(json.dumps(collect(args.output_dir, args.limit_per_repository)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
