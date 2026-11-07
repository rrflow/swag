# SWAG routing observations

Status: local explicit emitter and offline retained-native-attempt importer with
JSON Schema validation. This command does not poll issue services, dispatch
subscriptions, call the engine, or promote training data.

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

## Import a retained native attempt

The opt-in importer handles one accepted native v1 source-only worker and its
preceding accepted selector. These are two stages of one attempt, not two
comparable model outcomes. Supply a private JSON manifest with `schema_version: 1`
and an `artifacts` object. Each artifact has exactly `path` (relative to the
evidence root, using `/`) and `sha256` (the file's actual SHA-256).

Required roles are `task`, `worker`, `selector`, `budget` (successful native
protocol readback envelopes), and `source` (the exact selected source bytes).
Optional `prior_review` accepts the retained `clyffy.private-draft-review.v1`
observation. Optional `prepared_delivery` and `receiver_readback` must occur
together. No evidence paths, prompts, source text, output text, or review prose
are copied into the capture. Keep both inputs and output private.

```powershell
python tools/swag_passive_capture.py --native-manifest .swag/evidence/import.json --evidence-root .swag/evidence --output .swag/capture/native-attempts.jsonl
```

The manifest is limited to 16 KiB, each artifact to 4 MiB, and the destination
JSONL to 64 MiB. Native import requires an explicit dedicated output; it rejects
destinations containing legacy capture rows or aliasing the manifest or selected
evidence, including hard links and lock-file aliases. Duplicate JSON keys,
non-finite numbers, links/reparse points in inputs or destinations,
path escapes, unsupported shapes, and mismatched byte hashes fail before append.
This is a local consistency check, not authenticated origin or loaded-weight
attestation. Preserve the private evidence root against concurrent modification.

The optional `native_attempt` section retains exact engine instance, scope, task
and attempt identities separately from the capture's short local IDs. It verifies
artifact, source and worker-content bytes, joins selection/task/configuration
identities, and marks native typed digests as **engine-reported**. It does not
pretend Python JSON serialization reproduces Rust's typed hashing. Service IDs
remain observed aliases; provider/model/revision/loaded-weight identity remain
unknown. Reported effort, usage and elapsed time retain nulls when absent.

Delivery correlation joins the event to the prepared native source-response
digest, which describes a typed attempt view, not the worker's provider response
or full HTTP envelope. The receiver's absent source digest stays null. A matching
retained receiver event does not prove a cloud deployment or authenticate the
offline files. A prior review stays a prior observation; it is not a review of
the newly captured record.

Exact immutable replay under the writer lock adds no row. Different evidence for
the same native identity fails while preserving the original bytes. Later review
or event supplements must be retained separately; this importer does not merge
them into an existing row. All records remain unreviewed without training consent,
selected questions, inferred success, or inferred best-model labels.

The current offline viewer and paired-outcome review UI do not support this native
metadata record. It deliberately omits raw task text and repository location and
cannot directly satisfy the existing routing dataset admission contract. A future
reviewed adapter must supply genuine task/candidate evidence and explicit consent;
it must preserve independent review, comparable-attempt and frozen-split gates.

## Next live engine integration

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
