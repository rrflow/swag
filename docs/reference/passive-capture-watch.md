# Bounded local capture

The tool below is the local SWAG experiment. The repository-owned collector is
implemented in RRFlow [PR188](https://github.com/rrflow/rrflow-development/pull/188),
pending PR180 landing and its own full CI. Its conflict-resolved combined
candidate, `fc7ccb2e`, passed 30 focused collector/review tests. It uses only
Python's standard library and RRFlow's existing exchange helpers.
Its versioned observation format is
described in that PR; do not silently treat experimental SWAG records as engine
receipts or convert either format into admitted training data.

`tools/swag_capture_watch.py` polls an explicitly selected Git repository and a
local task JSON file. It emits schema-validated, unreviewed observations using
the existing passive capture JSONL format. It does not dispatch providers,
replan engine work, authorize training or run a permanent background service.

## Run it

Use a repository with at least one commit. Copy
`config/training/capture_watch_input.example.json` to a local task file and replace
the example title. Route identity and override are optional observations; leave
unknown values null. A client or operator can update this file atomically when
the task title or route preference changes. Do not put credentials in it.

```powershell
python tools/swag_capture_watch.py --repo D:/projects/my-app --context D:/captures/task.json --output D:/captures/observations.jsonl --duration-seconds 300 --interval-seconds 5 --max-records 100
```

Use `--once` for one observation. Output must be outside the watched repository,
preventing the collector's own writes from generating observations. Normal polling
ends at the duration or record limit; Ctrl+C stops it. An active poll can finish
after the scheduling duration. Every Git command has a 20-second read limit.

## What changes produce a record

The snapshot binds HEAD, branch, staged and unstaged diff hashes, changed-path
status and exact task-file bytes. An ordinary content edit produces a new
identity even if Git reports the same modified filename. A title or explicit
route override change also produces a new identity. Repeated identical polls,
including after a restart, produce no extra record. Returning to an older state
after another observation produces a new transition linked to the prior record.

Two consecutive equal observations are required. A changing input or temporarily
invalid task file defers that poll; fixing the input allows later captures.
This is not an atomic source snapshot, an engine read stamp or a guarantee of
observing every edit between polls. Untracked files and remote issue polling are
excluded. Submodule contents require their own explicit repository observation.

## Retention and limits

Raw diffs are hashed in memory and never written to the JSONL. Existing pattern
redaction is applied to titles, intent, issue IDs, branch display and paths.
Sensitive-pattern route identities are rejected rather than silently changed.
Pattern redaction is best effort; hashes are identities, not anonymization. Use
trusted local repositories: this is not a sandbox for hostile Git configuration.

Each diff is bounded to 16 MiB, status to 1 MiB, task input to 64 KiB and changed
paths to 1,000. Logs are bounded to 64 MiB. Preserve a full log and select a new
output explicitly; nothing rotates or deletes it automatically. Append locking
serializes writers. An interrupted JSONL tail is preserved and requires explicit
reconciliation; a stale lock is never silently stolen.

Every record keeps `label_status: unreviewed`, `training_consent: false` and
unknown outcomes. An override is a reported preference, not verified quality.
Independent review, consent and dataset admission remain separate steps.

## Validation

```powershell
python -m unittest discover -s tests -p test_swag_capture_watch.py -v
python -m unittest discover -s tests -p test_swag_passive_capture.py -v
```

The tests use real temporary Git repositories to exercise same-path edits,
staging, reverting, restart deduplication, overrides, input recovery, redaction,
byte limits, partial-tail preservation and rejection of fabricated consent.
