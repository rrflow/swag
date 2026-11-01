# SWAG routing observations

Status: local explicit emitter with JSON Schema validation. No background watcher,
issue-service polling, subscription dispatch, engine integration, or training
promotion is implemented here.

## Current capture boundary

`tools/swag_passive_capture.py` accepts a task/issue title, intent, selected checks,
optional route and explicit user observations. It reads changed path names with
Git status, including rename source and destination. It does not collect diff
bodies or inspect private conversation stores. Git failure means unknown paths,
not a clean working tree. Issue titles and outcomes come from the caller, not an
automatic service connection.

The enforced line format is
[`passive_capture.schema.json`](../config/training/passive_capture.schema.json).
The older YAML file is explanatory only. Default output is the ignored
`.swag/capture/observations.jsonl`. Appends serialize local writers; a partial
tail or existing writer lock is an explicit error. After a crash, reconcile the
tail and verify no writer is active before removing its lock. Never truncate the
corpus to recover a collector.

## Route and evidence

Record the observed provider, exact model identifier, effort, access mode and
authorized binding identifier separately. Weight-size tiers are optional legacy
metadata; they cannot describe Claude or Codex subscription routing. Missing
values remain null. The collector does not certify a model's availability,
subscription entitlement, remaining quota, or supported effort levels.

User acceptance and overrides are preference observations. They are not proof
that an action worked. Test/rollback/incident observations are three-state values:
true, false, or unknown. Reported confidence has no assumed calibration. Every
new capture is `unreviewed` with `training_consent: false`; dataset admission is a
separate reviewed export with provenance, consent, label evidence and split IDs.
The [review admission and evaluation pipeline](routing-data-and-evaluation.md)
now implements this offline export boundary. Raw capture records stay unchanged;
reviews are separate hash-bound supplements. Reviewer identity and consent remain
local attestations, not authenticated engine receipts.

## Next engine integration

An admitted observation adapter should correlate plan revision, source/read
identity, task and effect receipt with the eligible candidate set, original route,
override route, quota observation time, effort, deadline, and measured outcome.
Observe edits and issue changes only within registered scope; deduplicate by
source event identity and retain cursor/restart evidence. Editing a file or
accepting a suggestion must never automatically activate a model or train weights.

Handoffs should contain objective, bounded context references, expected artifact,
verification requirements, allowed effects and remaining budget. The engine owns
acceptance and execution. Provider strengths are measured per task family, model
revision and effort; fictional smoke-test scores are not capability evidence.

## Example explicit observation

```powershell
python tools/swag_passive_capture.py --project-root C:/work/app --intent-text "Review a bounded change" --selected-question-ids shared_predicates.software_security.01 --route-provider anthropic --route-model MODEL_ID --route-effort high --access-mode subscription --binding-id AUTHORIZED_BINDING_ID
```

Replace the placeholders with the observed binding. Only supply context you intend
to retain locally. Nothing is uploaded or admitted to training by this command.
