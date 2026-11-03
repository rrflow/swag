# Reviewed task-outcome workflow

This offline workflow predicts task success and handoff validity separately from
permission checks. It does not launch workers or confer deployment authority.
Use the repository virtual environment after installing `requirements.txt`.

## Capture and review

Write genuine comparable observations to JSONL matching
[`task_outcome.schema.json`](../config/training/task_outcome.schema.json).
Each line contains a real task, stable repository/project/leakage identities,
source/configuration digests, task criteria, candidate model revisions/efforts,
and one retained attempt per eligible option (at least two). Reruns need distinct
recorded identities under the declared experiment plan; never discard failed
attempts to select a flattering result. Unknown cost is `null`, not zero.

Attempts bind their source/configuration snapshots. Receipt artifacts are JSON
envelopes containing `taskId`, `attemptId`, `optionId`, `sourceSha256`,
`configurationSha256`, and `terminalStatus`, with retained native evidence as
additional content. An adapter must map actual engine receipts, not manufacture
those declarations. Output and verification artifacts have relative paths and
SHA-256 hashes under the evidence root. Completed attempts need output; any known
reviewed outcome needs verification. Native adapter/UI collection remains pending.

A separate JSONL review matches
[`task_outcome_review.schema.json`](../config/training/task_outcome_review.schema.json).
It binds the complete canonical observation digest, independent reviewer identity,
explicit training/evaluation consent, redaction evidence, and every attempt's
`taskSuccess` and `handoffValid` verdict (`pass`, `fail`, or `unknown`). These are
local attestations, not cryptographically authenticated reviews. Never fill them
in on someone else's behalf. Ordinary source edits require a new comparable
observation group; old results remain historical.

Use the project/time split policy described in
[routing data and evaluation](routing-data-and-evaluation.md). Admission rejects
cross-split repository/task/leakage reuse, changed evidence, missing consent and
exposed acceptance cases. Unreviewed or objective-unknown cases are withheld and
counted. No eligible reviewed cases means no dataset is created.

## Admit a separate objective

These paths name operator-supplied real records; no sample dataset is shipped:

```powershell
python tools/swag_task_outcomes.py --observations .swag/research/observations.jsonl --reviews .swag/research/reviews.jsonl --split-policy .swag/research/splits.json --evidence-root .swag/research/evidence --objective task_success --output-dir .swag/research/task-success
```

Repeat with `--objective handoff_valid` into a different fresh directory. Missing
handoffs withhold only that objective. Training/development chat exports contain
task/candidate inputs and binary observed targets. Acceptance chat is never
exported. Unknowns do not become negative targets. The completion manifest binds
all output bytes; changing an admitted export requires fresh admission.

The existing `swag_unsloth_train.py --admitted-dataset-dir` path now accepts either
this outcome scope or the existing bounded-policy scope, verifying each under its
own rules before GPU imports. Select only `train.chat.jsonl` for training and
`development.chat.jsonl` for training-time evaluation. Supply a pinned base,
explicit seed and reviewed recipe through the existing trainer arguments. This
change starts no training and does not approve the historical provisional corpus.

Set `SWAG_ADMITTED_DATASET_DIR` to the selected export for the shared developer
UI/MCP status. Status includes counts, scope, objective, withheld count and digest;
it does not expose task text or grant training authorization.

## Freeze and run

Supply a JSON limits object with every field explicit:
`minimumCases`, `maximumInvalidOutputs`, `maximumOrderSensitiveCases`,
`decisionThreshold`, `minimumDecisionAccuracy`, `minimumCoverage`,
`maximumSelectiveRisk`, `maximumBrierScore`, `maximumP95Seconds`,
`maximumCustomAccuracyDrop`, `maximumQuantizedAccuracyDrop`, and
`maximumQuantizedServingBytes`. Rates lie in [0,1]; case/memory minima are positive.
Choose these from development evidence and the agreed acceptance criteria before
examining acceptance outputs. There are no shipped acceptance thresholds.

```powershell
python tools/swag_outcome_eval.py freeze --dataset-dir .swag/research/task-success --split acceptance --limits .swag/research/limits.json --output .swag/research/protocol.json
python tools/swag_outcome_eval.py run --protocol .swag/research/protocol.json --protocol-sha256 PINNED_DIGEST --artifact-manifest ARTIFACT_MANIFEST --arm base_bf16 --base-url CONFIGURED_ENDPOINT --model CONFIGURED_MODEL --api-key-env-file PRIVATE_ENV_FILE --output-dir .swag/research/base-run
```

Run separately for `custom_bf16`, `custom_quantized`, and `small_baseline` against
their explicit endpoints/manifests. The runner uses authenticated chat completions,
HTTPS outside loopback, no redirects/proxies, bounded response size and a socket
timeout. It sends no review labels, retains failures and runs original/reversed
candidate order. Endpoint calls consume real resources: execute only under the
agreed research budget. A native small decision-model adapter is a separate task.

## Compare and measure

```powershell
python tools/swag_outcome_eval.py compare --protocol .swag/research/protocol.json --protocol-sha256 PINNED_DIGEST --maximum-serving-bytes 29000000000 --base-bf16 .swag/research/base-run --custom-bf16 .swag/research/custom-run --custom-quantized .swag/research/quantized-run --small-baseline .swag/research/small-run --output .swag/research/comparison.json
```

Comparison recomputes metrics from retained responses and rejects changed prompt,
protocol, output or artifact identities. It checks exact baseline/custom/quantized
lineage and requires all four arms. Total memory is required for every arm; the
quantized target must equal the frozen protocol target. Missing evidence yields a
failed report, never default success.

Serving identity uses the existing `serving-identity.json`/`.raw` contract from
`swag_model_qualification.py`; the runner's declaration alone is insufficient.
`serving-memory.json` requires `scope: total_serving`, `artifactManifestSha256`,
`protocolSha256`, `processIdentity`, positive integer `bytes`, a measurement
`method`, and `rawEvidenceSha256` matching `serving-memory.raw`. Process identity
must match the observed serving process. Preserve workload, context, concurrency,
sampling interval, runtime/cache configuration and non-overlapping memory accounting
in the raw evidence. This package validates receipts; it does not implement a
hardware memory sampler or independently authenticate those observations.

Reports remain `deploymentQualified: false` and `promotionAuthorized: false`.
Passing an offline comparison cannot close UI, execution, restart, or release gates.
