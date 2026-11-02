# Reviewed routing data and evaluation

For observed task success and handoff validity, use the separate
[outcome workflow](task-outcome-workflow.md). The bounded selector below remains
a supplied-score policy test; it is not the learned-suitability objective.

Owner update, 2026-10-29: new data admission and dataset use require reviewed real
observations in every split. The current Unsloth launcher requires that admission
and an explicit `--seed`; provisional task-corpus training is retired. Historical
synthetic commands and results below are retained for audit, not approved for new
training or qualification. Follow [the current plan](implementation-plan.md) and
[real-task contribution guide](real-task-review.md). Local review declarations
still need actual human evidence; declaring a row real does not prove it is real.

Status: offline admission, export and protocol runner implemented. The first live
run used synthetic development cases. No real provider-routing dataset has been
admitted and no acceptance protocol is approved. A separate provisional intent
corpus has now produced a custom BF16 checkpoint; see [its measured evidence](experiment-evidence.md).
It is not a substitute for this routing-review admission process.

## Contract and scope

[`routing_request.schema.json`](../config/training/routing_request.schema.json)
keeps persistent `projectIntent` separate from `taskText`. A candidate identifies
provider, exact model, effort support, access mode and binding, with explicit
authorization, health, quota, locality, quality and cost observations. Unknown
values cannot silently become permission or quota. The current bounded selector
uses supplied scores; it does not establish provider strengths or fetch quotas.

The target is exactly `{ "bindingId": "...", "effort": "..." }` or both null.
The offline reference selector checks eligibility, then lowest cost, then binding
identity for ties. The engine must independently enforce actual admission.
Intent interpretation, source-change replanning and rich handoff quality need
additional contracts and evaluation; passing this selector does not qualify them.

## Admission workflow

1. Preserve the original capture JSONL. Its `training_consent: false` and
   `label_status: unreviewed` remain unchanged.
2. Create a separate review JSONL matching
   [`routing_review.schema.json`](../config/training/routing_review.schema.json).
   Bind each review to the canonical SHA-256 of its observation, a stable project
   group and a leakage group covering related tasks and variants. Use
   `swag_routing_contract.digest(record)` for the canonical digest.
3. Record the label author, independent reviewer, review timestamp, explicit
   training/evaluation consent and redaction review. Attach nonempty local
   consent, label, redaction and candidate-snapshot artifacts with byte SHA-256s.
   Evidence paths are relative to the supplied root; escapes and hash changes fail.
   The candidate snapshot artifact is the exact JSON candidate array. Label evidence
   must justify scores, constraints and the correct choice using observed outcomes.
4. Supply the sanitized request and reviewed target. Task text must match the
   reviewed capture's intent. If sanitization changes an observation, capture and
   review a new revision rather than pretending the old digest still applies.
5. Assign disjoint project groups and ordered, disjoint UTC capture-time windows
   for train, development and acceptance. Related tasks, identical requests,
   normalized duplicate task text and task IDs cannot cross splits. Near-duplicate
   paraphrases still require reviewer grouping; no semantic duplicate detector exists.
6. Export to a fresh directory. Unreviewed observations are withheld; malformed,
   stale or conflicting reviews fail the batch before any export is created.

Review identities, consent and provenance are local attestations, not authenticated
signatures. Hashes establish content consistency, not whether evidence is truthful.
The pipeline checks evidence presence and consistency; it cannot independently
certify consent, reviewer independence, redaction completeness or outcome validity.
Never fabricate these assertions to make a dataset pass.

Split policy shape (replace projects and timestamps with reviewed assignments):

```json
{
  "schemaVersion": 1,
  "splits": {
    "train": {"projects": ["project-a"], "startInclusive": "2026-01-01T00:00:00Z", "endExclusive": "2026-02-01T00:00:00Z"},
    "development": {"projects": ["project-b"], "startInclusive": "2026-02-01T00:00:00Z", "endExclusive": "2026-03-01T00:00:00Z"},
    "acceptance": {"projects": ["project-c"], "startInclusive": "2026-03-01T00:00:00Z", "endExclusive": "2026-04-01T00:00:00Z"}
  }
}
```

```powershell
python tools/swag_routing_dataset.py --observations .swag/capture/observations.jsonl --reviews .swag/review/reviews.jsonl --split-policy .swag/review/splits.json --evidence-root .swag/review/evidence --output-dir .swag/datasets/reviewed-routing
```

Exports include each split's cases, train/development chat JSONL, and a manifest
written last as the completion marker. Acceptance targets are never exported as
training chat. Synthetic or previously used examples cannot enter acceptance.
Interrupted exports must be retained and inspected; restart into a fresh directory.

For a real BF16 training invocation, pass `--admitted-dataset-dir` to
`tools/swag_unsloth_train.py`, with that directory's `train.chat.jsonl` and optional
`development.chat.jsonl`. It validates artifact hashes and split paths before GPU
imports, and records the admission-manifest digest. Legacy raw-dataset training,
synthetic pipeline generation and runbook execution
are retired. They refuse without generating data, importing GPU libraries or
launching a job. Historical artifacts remain available for inspection. Do not mount
acceptance cases in the training job. Model/resource preflight is still required.

## Freeze before measuring

Freeze an admitted development or acceptance split with explicit minimum case
count, minimum accuracy, maximum eligibility violations, maximum invalid outputs
and maximum p95 latency. Missing thresholds block freezing. Protocol bytes bind
cases, labels, prompt, schema/scorer implementation and generation settings.
Keep the printed SHA-256 outside the protocol file and pass it to every run.
Freeze a new protocol when those dependencies change; preserve the old results.

```powershell
python tools/swag_routing_eval.py freeze --dataset-dir .swag/datasets/reviewed-routing --split development --limits .swag/review/limits.json --output .swag/evaluation/protocol.json
```

The checked-in `routing_development.jsonl` contains thirteen fictional cases,
including the eight previously observed smoke cases. Its thresholds are strict
development checks, not agreed production acceptance criteria. Direct case files
can only be frozen as development:

```powershell
python tools/swag_routing_eval.py freeze --development-cases config/training/routing_development.jsonl --limits config/training/routing_development_limits.json --output .swag/evaluation/development-protocol.json
```

On the serving host, run with a private environment file containing
`VLLM_API_KEY`, an artifact manifest, the frozen protocol digest, and a fresh output
directory. `--arm` records `base_bf16`, `custom_bf16` or `custom_quantized`:

```bash
python tools/swag_routing_eval.py run --protocol protocol.json --protocol-sha256 PROTOCOL_SHA256 --artifact-manifest baseline_manifest.json --arm base_bf16 --base-url http://127.0.0.1:8083 --model swag-qwen3-coder-bf16-baseline --api-key-env-file server.env --output-dir baseline-evaluation
```

Requests contain no gold assistant answer. Remote HTTP and redirects are rejected;
HTTPS or loopback HTTP is required. Results retain outputs, usage, timing and input
hashes. Failures count against accuracy and output validity. Metrics distinguish
ineligible selection, unnecessary selection, false abstention and exact match;
an eligible but unnecessarily expensive route fails exact match.

The manifest is retained as declared provenance, not server attestation. A friendly
model alias is not proof of loaded weights. This runner always reports
`deploymentQualified: false`; full three-arm lineage, statistical uncertainty,
resource measurement and engine receipts remain separate qualification work.

## Actual development run: 2026-10-28

The original BF16 endpoint matched **7/13**, with **5 eligibility violations**, no
invalid JSON outputs, and one false abstention. Warm median was **1.310 s**; nearest
rank p95 across all thirteen requests was **1.962 s**. The protocol failed.
These are short serial synthetic requests, not a load or generalization benchmark.
No model weights changed. Prompt/input changes prevent direct comparison with the
earlier 4/8 smoke result as evidence of improvement.

Local evidence: `.swag/evidence/20261028/routing-development-baseline/`.
Protocol SHA-256: `fa1177ae56ca3c014b43979a5c2cdb5827d60ef18c974fe6ddbb931521fe795b`.
The exact runner/schema sources are retained in its `implementation/` directory.
