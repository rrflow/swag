# SWAG current context

Reconciled 2026-10-31 (US Eastern) after worker admission publication and deployment review. Read this before older runbooks and generated reports; full controller delivery remains incomplete.
This records owner direction and evidence; it is not an engine execution plan.

## Compact controller research, 3 November

The owner clarified the intended SWAG role as a three-gate System One decision
router and a 9–12 GB candidate target. The [primary-source research update](controller-compression-research.md)
adds calibrated expert/channel pruning plus quantization, a small decision-model
comparison and selective residency experiments. This corrects the earlier plan's
limited treatment of structural compression. Exact gate contracts require owner
binding; no equivalent-quality or memory-qualified candidate exists yet.

## Outcome research correction, 2 November

The [five-milestone plan](outcome-research-plan.md) separates task success and
handoff supervision from supplied-score policy compliance. Its offline outcome
admission, training-input verification and frozen four-arm evaluation are now
merged through [SWAG PR6](https://github.com/rrflow/swag/pull/6). No new real reviewed dataset, GPU training, quantization,
total-memory measurement or completed UI task is claimed. Observation PR235 has
merged with protected CI success. Discovery PR248 is ready with candidate CI
running; its tree already includes the landed observation dependency. Worker
PR229 remains draft under its existing publication hold. See the plan and owning
PRs before using older status below.

The [Spark serving experiment](serving-load-measurements.md) measures real BF16
requests and overlapping memory counters. Its four-sequence runtime improves
observed throughput at concurrent load, with matching outputs on the repeated
inputs; it does not qualify routing quality, total memory or the joined UI task.

The owner's next compression targets are 15 GB total serving memory, then 9 GB
if controller quality and useful performance can be preserved. The first target
remains 29 GB. These supersede the older 19 GB aspiration below; none is measured
or guaranteed. The research plan distinguishes same-checkpoint quantization from
smaller-model distillation and requires RRFlow-owned artifact/promotion workflows.

## SWAG developer interface, 2 November

Fresh cluster access is restored. A full declared-file hash check passed for
26 files (61,084,160,920 bytes), including 61,066,575,648 weight bytes. The pinned
Unsloth container imported successfully and passed an actual CUDA operation on
the GB10. The restored custom endpoint rejects unauthenticated discovery and
lists the configured model with authentication. These observations supersede the
earlier access failure below. See [runtime verification](runtime-verification.md)
for identities and limits. No new training, inference or model qualification was
performed in this check. The developer interface now exposes explicit configured
model discovery through its shared UI/MCP read model.

The follow-on [training-control research and plan](training-control-plan.md)
identifies the missing generic engine activity runner on accepted RRFlow main
`e6f3632b`. The [training evidence adapter](training-evidence.md) now exposes
actual saved steps/loss, bounded callback observations, interruption records,
explicit artifact verification and configured export identity. Local checks pass
126 Python tests, nine UI tests and four browser tests. Callback stop behavior is
tested at the software boundary; no new GPU training or resume qualification is
claimed. The retained manifest declares 61,066,575,648 weight-file bytes, distinct
from serving memory. Fresh Spark verification requires renewed Tailscale SSH
authentication; the previously configured custom-endpoint forward was unreachable
during this check. Historical evidence remains unchanged and unqualified.

The owner's latest priority is subscription-client/RRFlow integration with
debugging, optimization and a UI path for fine-tuning that Connectome can adopt.
The [developer workspace](developer-workspace.md) now shares a versioned read
model between TypeScript and MCP. Local validation passed 110 Python tests,
eight UI tests and four browser tests. The installed bridge authenticated against
the local RRFlow core prototype and read public storage diagnostics. Codex and
Claude registrations were added locally; Claude reported connected and the exact
Codex registered transport passed a direct stdio lifecycle/probe. This does not
prove an agent used the tool during a task or measure subscription consumption.

The UI reads the retained custom BF16 run's actual metrics and marks its dataset
basis as provisional task-corpus training. There is no configured independently
reviewed routing export. Engine-owned UI training admission, live job control,
Connectome embedding, automatic RROFLOW trace export and promotion remain open.
The workspace document records their implementation order. Local test results
are not PR merge evidence or model qualification.

## Owner direction: RRG suite and public repository (2026-11-01)

SWAG belongs to the [Reason Ready Governance (RRG) suite](rrg-suite.md). The
serving goal beyond 29 GB is 19 GB through a custom RRFlow shard and KV-cache
system; neither footprint has been measured. The tree is prepared for
source-available publication under BSL 1.1. Session logs, generated artifacts
and `.swag/` evidence stay local, and public documents name the development
hosts `spark-01` to `spark-03`. The owner selected
[`rrflow/swag`](https://github.com/rrflow/swag) as the delivery repository on
1 November. It is private; public visibility and release remain separate decisions.

## Developer-build work resumed, 1 November

The owner requested a plan and execution after the readiness review. The
[developer-build execution plan](implementation-plan.md#developer-build-execution-1-november)
keeps the complete workflow, reviewed learning and native/container delivery in
scope. SWAG has Git history starting at `3a5b337` and `origin` now points to
`https://github.com/rrflow/swag.git`. Older statements that this checkout lacks Git metadata are
historical. Fresh local validation passed 97 Python and six viewer tests; both
preview executable hashes still match their recorded receipts.

RRFlow main has advanced to `daec1f1a`; PR190, PR232 and packaging PR212 are
merged. PR235 now publishes ordinary merge `b856a8fb`, resolving all 19
catalogue/projection conflicts and regenerating SDKs from the combined contract.
Its candidate CI has passed; protected acceptance remains pending.
Parent-preservation checks, the primary binary build, 165 contract/adapter tests,
499 reported owning-suite tests, strict lint, TypeScript and repository checks
pass. Four existing tests remain ignored and one SDK entry returns without its
live-daemon manifest; the subsequent hosted conformance check passes. Candidate
[41342695388](https://github.com/rrflow/rrflow-development/actions/runs/41342695388)
completed with all 23 jobs successful for `b856a8fb`. PR235 remains open;
candidate success is not a protected merge receipt.
No combined developer bundle, governed project execution or qualified model is
claimed. The worker publication hold and real-task acceptance input remain
unresolved; the delivery-repository choice is now resolved.

## Latest verified advancement

### Published RROFLOW correlation receiver

[RROFLOW PR43](https://github.com/rrflow/rroflow-development/pull/43) publishes
`b4c04ceec6686db056b53bc48de44137c5c2f885` from base `076eb08e`. The separate
worktree `rroflow-engine-correlation` is clean. Typed, bounded
`engine.observed` metadata preserves collector-reported engine/task/attempt/job
references and source/plan/configuration/response digests in the existing
immutable capture API. It rejects content/provider fields, creates no legacy
turn, and grants no dataset consent or task success. A migration marks the
strict-reader rollback boundary; old readers cannot consume the new shape.

All 136 Rust workspace tests pass with disposable PostgreSQL 17 configured;
JSONL and PostgreSQL replay, conflict, isolation and restart paths ran. Strict
Clippy, formatting, research-index and whitespace checks pass, as do 46
dashboard/release guard checks. The first full run exposed an incorrect new
test assumption about legacy turn-agent policy; the test now verifies the
separate SDK capture allowlist, without changing policy. Failed and corrected
logs remain in `.swag/evidence/20261031/rroflow-engine-correlation/`. All owned
temporary test containers were removed; existing services were untouched.

PR43 merged as `d552e8ab7e898b21dd5de98caab77f8ed992226e` through normal PR
controls with an exact candidate-head check. CI `41255031094` completed all six jobs successfully on
the exact published head. Release-plan run `41255031089` passed its build jobs;
host/announce were skipped, so no release publication follows. This is a receiver prerequisite only;
engine-owned authorized export, real correlated outcomes, independently
reviewed learning and public deployment remain incomplete. Do not substitute
the older SWAG Python preview-turn uploader for the engine-owned export path.

### Published engine sender candidate

[RRFlow PR235](https://github.com/rrflow/rrflow-development/pull/235) now publishes
implementation `19c3eb67` plus CI/test corrections at current candidate
`ebeecabb9815a891611f312c99bfa0afe5afee9e` and is ready for review.
Its isolated worktree is clean. The full candidate pipeline
[41263686147](https://github.com/rrflow/rrflow-development/actions/runs/41263686147)
completed all 23 jobs successfully at exact head `ebeecabb`. PR235 entered the
protected merge queue at position 3 on 1 November, 02:52 UTC. Protected
merge-group acceptance and actual landing remain pending. The candidate monitor
exited successfully; it must not be restarted as though the candidate were live.
Exact job metadata and native recovery logs are retained in
`.swag/evidence/20261031/observation-delivery/candidate-ebeecabb-complete.json`
and adjacent platform receipts. Queue entry was independently read back.

The queue subsequently reports `UNMERGEABLE` at position 3 while the PR remains
mergeable against current main `6c069e14`. It has not been removed: the queue
entry still exists, despite `autoMergeRequest` becoming null. A worktree-preserving
preview against queued prefix `d42abff7` finds 19 conflicts: the canonical OpenAPI
digest constant and generated SDK/reference projections. No source branch or
index changed. The exact preview is retained in
`.swag/evidence/20261031/observation-delivery/queue-prefix-integration-preview.json`.
Preceding PR190 and PR232 protected runs `41263871154` and `41266240986` are live.
Do not re-enqueue unchanged source or treat either prefix as accepted main.
After actual landing, reconcile that source normally, regenerate canonical
projections, run affected checks and qualify the resulting candidate. Candidate
monitor `19006` is complete; queue observer `66701` is a separate local process,
not a restarted CI run or protected acceptance evidence.

Original candidate run `41262802879` exposed three failures: the new adapter was
missing from the explicit CI package partition; generated storage-test digests
still named the old public catalogue; and two recovery tests used fixed request
times that could predate the actual recovery snapshot. The correction adds the
adapter to its owning CI suite, regenerates only four fixture identity fields,
and derives test request times from returned recovery state. No production clock,
policy assertion, workload outcome or training data changed. All 30 policy tests,
eight focused inventory tests, 365 engine tests (four existing helpers ignored),
57 evaluator tests, strict lint and repository checks pass locally. Hosted
candidate confirmation now passes. GitHub cancelled the superseded run; its failures
and logs remain retained. Publication receipt:
`.swag/evidence/20261031/observation-delivery/publication-ebeecabb.json`. Persistence now uses
the existing atomic control store with source, configuration and authority guards.
Retries retain exact event bytes; source readback retains the historical response.
Explicit configuration can retire expired uncertain records without claiming
success. Public HTTP and native operation wiring is authored. Four focused
contract tests and eight installed-engine fault tests pass; failures and their
corrections are retained. Five SDKs regenerate; 74-operation parity and TypeScript
checking pass. The broader engine run exposed a stale SDK fixture count; after
its generator-derived correction, 298 engine library tests pass with four
existing helper entries ignored. All 165 contract/adapter tests pass and
HTTP/native wiring compiles. Receiver post-merge main CI `41257683331` passes all six jobs.
Three public transport tests now pass through the native client, authenticated
HTTP server, installed engine and actual loopback HTTP exporter. They verify
acknowledgement readback across reopening, identical-event retry after a dropped
reply, and export of an actual accepted bounded task attempt. The receiver is a
protocol fixture and the task uses the bundled deterministic embedding adapter;
these are neither RROFLOW integration nor BF16/model-quality evidence. Stale
source/configuration and mismatched payload requests are rejected. The native-client
suite reports 29 passes (one external-daemon harness entry returned early because
its manifest was absent); strict client lint passes.

A separate installed Windows binary trial now passes against the actual RROFLOW
receiver with fresh loopback credentials and isolated JSONL storage. Event
`71ee6ea7-9811-8d26-acc5-3b354403ffd5` correlates the installed job and source-response
digest. Both processes were terminated/reopened; readback is unchanged, and
acknowledged replay leaves one engine attempt and one receiver event. Evidence:
`.swag/evidence/20261031/observation-delivery/installed-roundtrip-20261101T012030Z/`.
Two earlier harness failures are retained: nullable-field handling and a wrong
HTTP method for session close. The corrected harness uses catalogue methods.
This verifies local transport/restart integration, not actual development-task
effects, model quality, learning approval or public deployment. The engine
implementation was still local at that trial; the published candidate is recorded
above. The trial remains bound to its exact precommit debug executable.

The subsequent retention review reproduced and corrected a capacity deadlock:
lowering a full 128-record history to one could not retire enough expired entries
within one control transaction. At most three guarded batches now retire eligible
history. Eleven focused engine tests pass, including competing preparations and
source advancement during export. The architecture manifest now includes the
adapter and explicitly prevents client bypass or adapter-owned storage/authority.

After building all CLI binaries required by process tests, the complete
engine/server/client command passes: 427 reported passes, zero failures and four
existing subprocess helpers ignored. One SDK entry returned early; a separate
run with the repository's actual private daemon harness then passes Rust SDK
conformance. This does not claim the five other language conformance runs.
Strict all-target lint, workspace formatting and 74-operation generated parity
pass. Failed runs are retained: missing architecture declarations/untracked new
targets, followed by a missing estate-controller test executable.

The rebuilt engine (`147770113e31631c20b5b54642afb50fac27715991eeb1ee0265519e5e34b11a`)
passes the installed RROFLOW trial again in
`.swag/evidence/20261031/observation-delivery/installed-roundtrip-20261101T013715Z/`.
Event `02afb39b-8133-8100-aed9-a44fe6fcc850` survives restart and acknowledged
replay still leaves one attempt/event. This supersedes the older executable as
evidence for the retention correction, while preserving the original trial.
Final author review and publication are now recorded in
`.swag/evidence/20261031/observation-delivery/publication-19c3eb67.json`.
The review combines full new-file reads, every changed region, exact whole-file
comparisons and generated parity; it is not independent reviewer approval.
Candidate CI subsequently passed as recorded above. No training approval or complete development-task
workflow is established. A read-only Tailscale check on spark-02 confirms the
existing custom BF16 container is running and its health endpoint returns HTTP
200; no inference or training was launched and routing quality remains unqualified.

The corrected candidate's shared live-daemon SDK harness now passes Rust,
TypeScript, Python, Go, Java and .NET, plus both installed Python attunement
checks. Job `124722136316` binds corpus
`42e2a637a7852dfc4b86ef5993a95f2e59747ad4a7c63f0304425f5c290f90d2`.
The retained log SHA-256 is
`695738d45dd69a9b0c8559193c887fa346cc752295d125e31e76cfb1f229b859`;
`.swag/evidence/20261031/observation-delivery/candidate-ebeecabb-sdk.json`
records the exact job and source. This closes the shared SDK conformance gap,
not exhaustive coverage of every operation in every language or full workflow
qualification. All candidate/native recovery jobs subsequently passed; protected
merge acceptance remains pending.

### Local checkpoint-evidence identity correction

The offline evidence projection previously derived `runId` from only protocol
and result hashes. A reproduced regression showed that distinct checkpoint
manifests with identical result bytes received the same identity; learning
proposal deduplication could discard one checkpoint's evidence. The identity now
also binds `artifactManifestSha256`. The same regression verifies distinct report
event IDs and retention of both checkpoint references while repeated copies of
one run still deduplicate. All 12 focused projection, learning-candidate and
qualification tests pass using `.venv/Scripts/python.exe`. The first ambient
Python invocation lacked `jsonschema`; the repository environment ran the actual
failure oracle and corrected suites.

Original source, failing regression output and passing commands/logs are retained
under `.swag/evidence/20261031/checkpoint-evidence-identity/`. The regression uses
isolated development protocol fixtures, not training or qualification data.
Existing retained runs and exported reports were not rewritten. Reprojection
changes identities even for old runs; do not automatically upload regenerated
reports as new model attempts. This remains unpublished local tooling because
SWAG's delivery repository is unresolved. No endpoint call, learning approval,
RROFLOW upload or deployment follows from these checks.

### Local training-path correction

[Legacy training retirement](legacy-training-retirement.md) closes a discovered
local bypass: the older pipeline could generate synthetic SFT rows and execute
raw runbook training despite the reviewed-data requirement. Generator and raw
trainer entry points now refuse; runbooks remain inspectable but cannot execute;
the legacy UI training control is disabled. Forty-three targeted CPU checks pass.
Historical datasets and checkpoints remain unchanged. SWAG has no Git metadata,
so this is a local correction, not a merged/deployed change or a training run.

Connectome candidate run `41252267362` has completed all six jobs successfully,
including actual-engine process integration and the final gate. This supersedes
the earlier running observations below. Its draft PR30 still requires dependency
acceptance and completion of the desktop trial. Desktop input is held pending
clarification after unexpected text appeared in the project directory field.

### Deployment review update

Worker PR229 now publishes `52e2254a`, reconciling exact landed native main
`6c069e14` through ordinary merge `31313f6e`. Preview, merge and prior worker
trees are identical; only its new journal/index follow. All local admission
checks pass. Automatic approval review rejected the combined PR-description
update/readiness command with only "blocked by policy". Readback confirms the
PR remains draft at the published head; run `41253115659` is skipped, not
candidate acceptance. The final reviewable description is retained locally at
`.swag/evidence/20261031/worker-native-landed/pr-ready.md`. No bypass or retry of
the rejected transition was attempted. Other dependency work remains active.

[Deployment readiness](deployment-readiness.md) supersedes the pending PR222
and missing plan-panel statements below. PR222 merged at `6c069e14` with
successful protected run `41248811413`. Connectome draft PR30 now publishes
engine-owned plan controls at `1f2e2a5c`; its exact matching desktop bundle is
frozen and both executable hashes have been rechecked. Local native and focused
installed-process checks pass. Candidate frontend and three-platform native CI
pass; the separate process-integration job was still running when checked.
The desktop trial reached installed-job discovery and a source replan preview.
The window became unavailable during resumption, including after reopening;
the cause is unknown and remaining UI acceptance is not claimed. No new model
qualification, reviewed learning, public deployment or project effects follow.

### Current deployment assessment, 31 October

PR231 publishes the missing public installed-job discovery prerequisite at
`8d47500869329f1a5604821138f1a6c8efc349a5`. Its isolated worktree adds bounded
`attunement-job-list` through the contract, engine, authenticated HTTP and native
client, with generated SDK projections. Five contract checks, five installed
engine checks and the real HTTP/native replan/reopen test pass. All five SDKs
regenerate; 74-operation parity and TypeScript checks pass. The full engine suite
passes 369 tests (four existing ignored); contract/client/server suites pass 227.
Final strict lint, formatting and repository checks pass. A diagnostic-only
conflict-message correction and simpler test helper are separately recorded;
all five affected engine and five contract checks pass again. The complete
source and [journal](https://github.com/rrflow/rrflow-development/blob/8d47500869329f1a5604821138f1a6c8efc349a5/docs/evidence/change-journals/gate-d/d-02-installed-job-discovery.md)
are published, but not merged. The canonical native build is frozen at
`.swag/evidence/20261031/attunement-job-discovery/rrflow.exe`, 154,188,288 bytes,
SHA256 `4a8ac57f1766b9c06e6816bc820ef027c4dbbfd1b90d408b1c563dfcf6a591f7`.
Its two-pass build, clean source identity and copied executable report agree;
`engine-frozen.json` retains the receipt. This unsigned, unoptimized engineering
candidate has no installed-process or desktop discovery proof yet and excludes
model weights. Existing paired UI binaries are unchanged. The UI is not implemented
by this package. Retained evidence is under
`.swag/evidence/20261031/attunement-job-discovery/`; PR231 stays draft behind
PR222/229/230. An existing page is stored state, explicitly not a current-source
verification; current source changes still require engine preview/accept.

PR206 is merged at `5b4039fe930332895c1b24138891d39f600030c7`;
protected run `41239406940` completed successfully. The older pending-merge
statements below are historical and superseded by this observation.

Connectome PR29 publishes implementation `0f75c015` and desktop evidence at
`59526643f0a6d7ae8ef04d1858d988af6d6e1efd`. The clean Windows preview completed
a real configured BF16 proposal, explicit Stop/resume, reviewed worker draft,
webview reload and readback. Resume preserved spent effort and the original
deadline; final effort was two steps and 22,528 ms. Independent reads matched
the task, both attempts and budget across reload. The task remains open; no
project changes, routing-quality label or training approval follows.
[The published journal](https://github.com/rrflow/connectome-development/blob/59526643f0a6d7ae8ef04d1858d988af6d6e1efd/docs/controller-task-recovery-desktop.md)
binds 44 observations to the exact UI and engine builds and records corrections.
Both frozen executable hashes were independently rechecked locally.

PR29 remains draft. Candidate run `41244693013` completed all six jobs
successfully, including Windows/Linux/macOS native checks and process integration.
This is candidate CI, not accepted release evidence.

PR222 is now ready at `25f722555e0f758aec8135583e7ecd5abc060977`, after ordinary
merge `b93bd2f4` with actual landed main. The incoming delta is documentation
only; non-documentation paths equal the previously tested client source.
Navigation, inventory, documentation and whitespace pass. Full candidate run
`41245163469` has passed all 23 jobs. Protected merge-group run `41248811413`
is now active at `6c069e1462d2b9cbb0237e9c117c379d1482bbaa`; normal merge controls
remain enforced. PR222 is not yet merged. Retained live observations are in
`attunement-job-discovery/pr222-run-*.json`.
PR229 is prepared at `cb42e8a96ad14892690c7e46b222eda93df25762` through ordinary
merge `5ed54bd4` with that native candidate. Its runtime, tests and installed
receipts are unchanged; fresh repository checks pass. It stays draft until
PR222 lands and exact main is reconciled. Journals are published in their PRs;
local command/source/push receipts are under `.swag/evidence/20261031/` in
`native-client-landed-main/` and `worker-native-candidate/`. Required candidate
and protected checks remain enforced, with no intermediate worker CI restart.

PR230 is prepared at `98996a107b28da1f4317cd501135805ae2660d4a`, composing the
worker candidate through ordinary merge `e7500b65`. Direct complete-tree and
parent-ancestry checks handle the multiple merge bases without relying on an
arbitrary triple-dot base. All runtime/SDK/test/harness/receipt bytes are
unchanged; repository checks pass. It remains draft pending actual worker
landing and its own full pipeline. Local receipts: `resume-worker-candidate/`.

A fresh [checkpoint binding audit](checkpoint-binding-20261031.md) matched all
26 custom artifact files to the retained manifest, including 16 BF16 shards,
18,867 tensors and 30,532,122,624 stored elements. Weight files total
61,066,575,648 bytes; ideal packed 9-bit payload alone is 34,348,637,952 bytes.
The same running container mounts those files read-only; authenticated discovery
passes and no model call/restart occurred. This strengthens current disk/runtime
configuration provenance, not in-memory attestation, routing qualification or
the 29 GB total-serving claim. The earlier provisional labels remain unapproved.

Remaining engine/UI dependencies need protected landing. Ordinary-edit
replanning, governed project effects, RROFLOW outcome
correlation, reviewed learning and model qualification remain open. Native and
container clean-install, upgrade/rollback and public-release qualification are
also pending. The new desktop preview is documented in `testing-binary.md`.
It is unsigned and unoptimized, excludes model weights, and its trial server
has been stopped. This supersedes earlier pending desktop-composition notes
only for the bounded Stop/resume and worker-readback workflow.

### Earlier source-bound observations

Installed same-task recovery now passes on the frozen `6a4cbb04` engine.
Clean harness `ce20dc79` used the actual PR230 task and exactly four provider
calls: original selection, real length-terminated rejected worker, fresh selection
after explicit resume, and accepted new worker draft. Resume retained two spent
steps, 2,507 ms and the original deadline; new work brought effort to four steps
and 21,529 ms. In-flight/unauthenticated/stale resume and attempt replay were
denied. Both original attempts remained unchanged. Credential-free reopen and
independent recovery matched all four attempts and the final budget without a
recovery dispatch. Both runners exited zero; all eight owned servers stopped.
No trial failed or was retried. The task remains open, with no project effects.

PR230 evidence head `67c197ea2dd60d597e18cc37e1b57d33c45d67cb` publishes
[the installed journal and 37 byte-preserved receipts](https://github.com/rrflow/rrflow-development/blob/67c197ea2dd60d597e18cc37e1b57d33c45d67cb/docs/evidence/change-journals/gate-g/task-budget-resume-live.md).
All receipt hashes, credential scanning and repository checks pass. The harness
passed 14 focused tests before its clean commit. This supersedes the pending
installed-recovery status below; it does not qualify routing accuracy, training,
unknown-outcome reconciliation, Connectome composition or release readiness.
PR206 remains open with protected run `41239406940` still in progress; no merge
or replacement run is inferred. Next compose the exact public operation/build
into Connectome and reconcile downstream packages after protected landing.

PR230 now publishes explicit budget recovery at
`6a4cbb042a13f5a7c41b53d11d62b54a85df3bed` in its own worktree/branch. The
authenticated `task-budget-resume` operation permits safely completed cancelled
or failed work, retaining original effort, deadline, repetition counts and prior
attempts. Active/unknown work, stale requests and exhausted/expired budgets stay
denied. Resume dispatches nothing; a new attempt passes ordinary admission.
Ten focused worker/recovery checks and real authenticated HTTP recovery pass.
The engine suite passes 364 tests (four existing ignored); six bootstrap checks
pass after a schema-digest correction. Contract/client checks pass 189 tests and
the complete server suite passes 33 after building its CI-required helper.
Strict lint/fmt, five generated SDKs, 73-operation parity, TypeScript checks and
repository checks pass. Failures and corrections are preserved in the
[package journal](https://github.com/rrflow/rrflow-development/blob/6a4cbb042a13f5a7c41b53d11d62b54a85df3bed/docs/evidence/change-journals/gate-g/task-budget-resume.md).
The PR remains draft behind PR206/222/229. Installed same-task BF16 recovery,
Connectome controls and unknown-outcome reconciliation are not yet proven.
Old binaries do not inherit the operation. No training or qualification claim
follows from these control/protocol tests.
The canonical clean-source build is frozen at
`.swag/evidence/20261031/task-budget-resume/rrflow.exe`, 154,068,480 bytes,
SHA256 `d4cc99d8527b97ba145023e0b1cc4a7c26a0682f6edc8c2d5d8d9ff1ad4ffec0`,
with `engine-frozen.json`. It is an unsigned, unoptimized engineering artifact;
its source/build identity passed verification, not the pending provider trial.

PR227 has merged at `df26b35512176428bf4847784501c28d6a123474`, after successful
protected run `41231635508`. PR206 ordinarily incorporated that exact main
revision in merge `dd20b7b8`; the entire merge tree equals its prepared parent.
Published controller head is `9371f8563e7e66e721734b0a7340c10a89af417b`.
Non-documentation paths equal tested `9e167aad`; navigation, documentation,
inventory and whitespace checks pass. PR206 is ready; its full candidate
run [41235940488](https://github.com/rrflow/rrflow-development/actions/runs/41235940488)
passed all 23 jobs. Protected merge-group run
[41239406940](https://github.com/rrflow/rrflow-development/actions/runs/41239406940)
is live at `5b4039fe930332895c1b24138891d39f600030c7`; required checks and the
merge queue remain enforced. It is not merged or protected-accepted. The preceding skipped
draft run is not candidate evidence. PR222 follows its verified landing.

PR28 evidence head is now `91b89ae46ac23af70c852c79559bc59ecd62eed5`.
Its own candidate run `41235205588` passed all six jobs. Earlier `386fdcdb`
failed CI on JSON formatting. The existing formatter corrected those files;
exact JSON values, original capture digests and frozen executables are preserved.
Both the failure and correction remain recorded. PR28 remains draft behind
its dependencies; the actual desktop trial remains bound to `95a81077` and
engine `e3528330`.

PR229 evidence head is `d5151eefc9c85bfea674a0d9184cc6d4d81ba7dd`, retaining
implementation and frozen binary source `75c26a80d5d1d07550070096df463d006aca6680`.
A reproduced engine regression showed a rejected terminal response incorrectly
retaining unknown execution. The common transport now distinguishes completed
generation from lost outcomes; the existing completion transaction releases
known-completed capacity while preserving rejection, charged effort and the
stopped budget. Lost/malformed/mismatched outcomes remain uncertain. The repair
passes 362 engine tests (four existing ignored), 42 inference tests, strict
Clippy, formatting and repository checks. The clean-source primary is frozen at
`.swag/evidence/20261031/worker-terminal-response/rrflow.exe` (154,011,648 bytes,
SHA-256 `c9f481103d6ba2a2cf1e0b42e386b084d92530bc42375b0039c7cf6722243636`).
Its actual installed BF16 selection/worker baseline and independent credential-free
recovery pass: same retained results and budget, two charged steps, no recovery
redispatch. Clean harness `69250d34` also passed the actual installed terminal
rejection trial: the supplied worker allowance was one output token, the real
response ended with `length`, and the engine withheld output while retaining two
steps, the original deadline and a stopped budget with no unknown execution.
After credential-free reopen and denied replay, a separate actual PR206 task
obtained a proposal through the same one-call binding. Its one spent step did not
change the original stopped task. Both histories survived another reopen, and
independent recovery matched the original selector/worker/budget without dispatch.
Exactly three actual provider calls occurred; no trial failed or was retried.
No historical estate is cleared. That frozen binary has no public resume;
PR230 above adds it separately. Old binaries do not inherit this repair.
The existing desktop pin is unchanged.
The [installed terminal-result journal and 20 raw receipts](https://github.com/rrflow/rrflow-development/blob/d5151eefc9c85bfea674a0d9184cc6d4d81ba7dd/docs/evidence/change-journals/gate-g/task-worker-terminal-live.md)
are published with exact byte hashes. Ten focused harness tests and repository
checks pass. PR206's earlier partial candidate observation is superseded by
the full pass and live protected run above. Landing remains pending.
No old trial or current job was restarted.

The preceding PR229 evidence at `e1b5ea465f41fb30096c54dc99fe5b2ad6c6a9b7`
records four actual
installed worker trials now cover configuration revision, session closure, Stop
and lost response delivery. Each used two provider calls and withheld worker
output. Four separate credential-free recoveries preserved exact selector,
worker and budget values without redispatch. Seven focused harness tests and
all 64 published receipt hashes pass. The new trials use frozen engine
`e3528330`; prior interruption evidence retains its original binary identity.
Stop and lost delivery still leave uncertain capacity. Engine-owned validated
reconciliation remains missing; external observations cannot clear leases,
authorize retry or reset effort/deadlines.

Next observe PR206 candidate/protected acceptance, reconcile downstream packages
after landing, and implement usable recovery at the existing engine boundary.
Complete ordinary-edit UI replanning, governed project effects, correlated
RROFLOW outcomes, independently reviewed learning and native/container/model
qualification remain open. No public-release or all-merges claim applies.

## Earlier source-bound observations

The snapshots below retain their original source attribution. Pending CI and PR
states are historical and superseded by the verified status above.

Actual Connectome worker desktop trial now passed on the frozen `95a81077`
preview with engine `e3528330`. Evidence is published in draft PR28 at
`386fdcdb9ea8e4d8f5c08dadbe17a2f94b3b1d08`:
[live journal and receipts](https://github.com/rrflow/connectome-development/blob/386fdcdb9ea8e4d8f5c08dadbe17a2f94b3b1d08/docs/controller-worker-desktop-live.md).
The real PR28 verification task was entered through Tasks. One configured BF16
proposal and one explicit worker draft were accepted; webview reload, coordinate
recovery and readback recovered the same draft. Independent public API reads
show exact task, budget, selector and worker payload equality before/after reload.
Two steps and 17,258 ms remain charged; the task stays open. Worker output is
852 reported tokens / 15,356 ms, not a benchmark or independently reviewed label.
The provider alias does not attest weight identity. No project files were changed.

Candidate CI `41232894117` passed all six jobs at implementation `95a81077`.
The evidence-only head has its own live run `41234351899`; do not attribute the
previous green run to this new head. Local receipt hashes, actual content digest,
selection linkage, unchanged frozen executable hashes and cumulative diff checks
pass. Published text normalizes line endings/trailing accessibility whitespace;
the manifest retains original capture hashes and local raw bytes. The initial
unpublished evidence commit had whitespace failures, corrected before publication.
Both owned desktop and path-verified engine processes are stopped; the estate and
all evidence remain under `.swag/evidence/20261031/connectome-worker-live/`.

This supersedes pending desktop-worker statements below. PR28 remains draft behind
its dependencies. PR227 remains open with protected run `41231635508` live; its
latest detailed observation has 19 successful jobs and three 100-cycle reopen jobs
running. No protected landing or all-merges claim applies. Next complete the
remaining worker policy/credential acceptance and explicit uncertain-attempt
recovery while the prerequisite chain proceeds through its normal required CI.
Ordinary-edit replanning through the full UI, governed project effects, correlated
RROFLOW outcomes, reviewed learning and native/container qualification stay open.

PR227 is now **ready for review** at `974c9d65d28750f89edacf4f4955d4125d2e23ca`.
Ordinary merge `8ea31f5a` incorporates landed main `906bec82` without conflicts.
Its composed Windows validation passed 342 engine tests (four existing ignored),
seven installed CLI lifecycle cases, focused publication/startup regressions,
strict Clippy, formatting and repository checks. Full candidate run
[41227938401](https://github.com/rrflow/rrflow-development/actions/runs/41227938401)
completed successfully with all 23 jobs. Protected merge-group run
[41231635508](https://github.com/rrflow/rrflow-development/actions/runs/41231635508)
is now live at queue revision `df26b35512176428bf4847784501c28d6a123474`;
protected landing is not yet established.
Normal auto-merge was enabled for that exact head at 18:12:39 UTC; GitHub still
reports the PR open, with no merge commit. Required checks and the merge queue
remain enforced. The candidate's earlier partial counts are superseded by its
full success. The latest retained protected observation has 18 successful jobs
and no failed jobs; this is not protected acceptance or a merge claim.
The existing real-repository trial remains bound to its original binary.

Draft PR206 is reconciled at `780c1fba60052ee0a93c4eed9f1bd8de89819af4`,
including the PR227 candidate and current main through ordinary merge `d4d2aea2`.
Only documentation changed; all non-documentation paths equal both its prior
head and tested implementation `9e167aad`. Repository checks pass. Wait for
PR227's verified landing, reconcile that destination, then mark PR206 ready to
start its full candidate pipeline. Candidate/protected checks gate landing;
they do not precede the ready transition that starts candidate CI. PR226 stays
open until its retained behavior has a verified main destination. PR222/229
and packaging remain separate unmerged work; no testing ZIP changed here.

Draft PR222 is now reconciled and published at
`14ee2557f66c6ef52a7093080270ddb4d8b67252`, with tested ordinary merge
`f957e06d44b77fb0130f0ad017df1d3307d97449` over PR206 `780c1fba`.
GitHub reports MERGEABLE. Its native client/validator equal the prior native
parent, while engine/storage/CLI/SDK/locked dependencies equal the incoming
controller parent. Nine focused and 182 complete client/contract tests pass,
as do strict all-target/all-feature Clippy, 32 architecture checks, source
closure, unchanged 71-operation/seven-signal parity and repository checks.
No new provider call or executable was produced. After PR206 actually lands,
reconcile that destination and mark PR222 ready for its full candidate pipeline.
Connectome PR26/27 remain draft at `ed6ed0e5` / `f8139cc7`; their current UI
worktree is `connectome-controller`, on PR27's branch.
The new native reconciliation has not updated that UI pin or the testing bundle.

New draft [Connectome PR28](https://github.com/rrflow/connectome-development/pull/28)
is published at `95a81077d89efb5cd14e14bcbdecbc9bfa76d872` in the separate
`connectome-worker` worktree. It includes PR27 and pins all
SDKs to RRFlow `e3528330`. A retained selection now offers explicit worker review
and one engine-admitted draft request, with coordinate-only recovery and worker
readback. No renderer credential, provider ranking or automatic retry is added.
Local checks pass: 41 ordinary native tests, 17 process-suite cases (one optional
visual helper returns without capture inputs), strict Clippy/fmt, frontend
checks/build and four existing browser smoke cases. The exact pinned engine
regenerated the value fixture and passed its non-writing check. Engine binary:
154,010,112 bytes, SHA-256
`8c323716f02e210ebc211bf4593dde84b03d1b55d50f62e710676cda5a971da0`.
The [implementation evidence](https://github.com/rrflow/connectome-development/blob/95a81077d89efb5cd14e14bcbdecbc9bfa76d872/docs/controller-worker-handoff.md)
binds source and logs. Candidate CI `41232894117` is live. The clean-source
desktop preview is frozen at `.swag/controller-ui/95a81077/`: `connectome.exe`
is 52,200,960 bytes, SHA-256
`5c054ce8d4775bd7d1aa4cb825b181c4bab6bbe586fe2f1a397c3c406d35234f`,
with the matching engine and external build receipt. Build exited zero; its
wrapper later failed printing Unicode log text to the cp1252 console. The
stored successful build result, unchanged clean source, copied hashes and
engine embedded provenance were verified without rebuilding. This is unsigned
and unqualified. Actual BF16 desktop worker click-through and reload evidence
remain required. Existing UI trials and worker receipts do not qualify this
new UI action. PR26/27 and engine dependencies remain unlanded.

Draft PR229 is now published at `e35283303f4c5823c612686d32fb6bee1ac368ac`.
Clean harness `2f7a1a34` completed an actual BF16 worker process-interruption
trial at 18:48 UTC. Exactly two provider calls occurred; the owned engine was
killed after the worker response reached the relay but before acceptance.
Reopen retained the same reserved worker, accepted selector, two spent steps,
original deadline and unchanged task. Independent credential-free recovery
also passed with exact attempt/budget equality and no provider call. Four local
relay tests, compilation/workflow checks, repository metadata and 14 staged
receipt hashes pass. The immutable
[live journal](https://github.com/rrflow/rrflow-development/blob/e35283303f4c5823c612686d32fb6bee1ac368ac/docs/evidence/change-journals/gate-g/task-worker-interruption-live.md)
includes actual provider bytes and recovery observations. The engine remains
the previously frozen `c75c1896` artifact; no new engine or ZIP was built.
This proves retained uncertainty, not reconciliation, safe resume, task success
or model qualification. Remaining policy/credential acceptance and prerequisite
landing still precede readiness and full candidate CI. The worktree is clean;
GitHub reports MERGEABLE and draft.

The preceding dependency evidence head was `8b9ce1fb`.
Ordinary merge `44a85ef0` incorporates the prepared PR222/206/227 chain without
conflicts. All non-documentation paths equal the earlier `a3068cf` head; only
dependency evidence and generated navigation changed. Repository checks pass,
GitHub reports MERGEABLE, and the worktree is clean. No binary, provider call or
recovery capability was added by that merge. Its pending interruption check is
now supplied by the source-specific experiment above.

The recovery audit confirms that adapter `dispatch_may_have_occurred` currently
maps directly to engine `execution_may_continue`, including response-validation
errors. Persisted uncertainty has no public reconciliation operation. No old
attempt or capacity lease was cleared; terminal-response evidence and genuinely
unknown remote outcomes need distinct, explicitly validated recovery handling.

Prior worker evidence head: `a3068cf67e3c7afbd75a01ac85662d5afd244483`.
PR222's native-client dependency is ordinarily composed at `43d18059`; both
selector and worker now share the catalogue-derived one-attempt transport and
contract-owned response validation. The composition passed 189 contract/client
tests, strict Clippy, 32 architecture checks, generated parity and repository
checks. GitHub reports **MERGEABLE**, but required candidate CI/landing remain
outstanding. The worktree is clean. PR222 itself remains open and unmerged.

An exact-source native client built at clean `43d18059` completed actual selector
and worker calls against the separately identified `c75c1896` engine. Missing
credentials spent no additional effort, the task remained unchanged, restart
readback matched and replay was rejected. Separate credential-free recovery read
both attempts. The first native worker response was rejected as incomplete or
requesting unsupported effects; its two-step stopped/uncertain estate remains
retained. A second isolated trial changed only the configured prompt's brevity
instructions and passed; no validator, candidate or generation bound changed.
Both cases are reviewable in the
[native receipts](https://github.com/rrflow/rrflow-development/blob/a3068cf67e3c7afbd75a01ac85662d5afd244483/docs/evidence/change-journals/gate-g/task-worker-native-live.md).
This is not UI completion, a project effect, routing-quality qualification or a
production retry/reconciliation path. No training data or consent was inferred.

The preceding installed HTTP proof and main reconciliation remain source-specific
evidence: `14b43c93` and `adc16769`, respectively. Landed main `906bec82` is included.

The canonical `scripts/build_rrflow.py` successfully rebuilt clean engine
`c75c1896` with embedded source provenance. The frozen engineering executable
is 153,999,360 bytes, SHA-256
`60a708117899a022b04818c096af17a925c60eae06c554c39d00e5fe09e028fa`.
It remains unsigned/unoptimized and is not in the available ZIP.

An actual installed trial now proves selection followed by a worker draft,
unauthenticated/missing-credential denials without added effort, exact draft
identity/content checks, unchanged task state, restart equality and replay
rejection. A separate recovery read both attempts without provider credentials.
It used the real PR229 development task and one configured candidate; no quality
label, training consent, project effect or routing-quality claim follows.
The worker reported 1,872 total tokens and 38,390 ms for this one call.
The later native trial reported 1,934 ms for its selector and 16,902 ms / 1,635
tokens for its shorter worker draft. These isolated calls are not a benchmark.

The first live selector failed with `invalid endpoint selection choice`.
Its retained estate remains stopped/uncertain with one spent step and no worker
dispatch. A second isolated trial clarified the configurable output-schema
instructions and succeeded. The first failure was not replayed or erased.
Raw evidence is under `.swag/evidence/20261031/`; the
[installed journal](https://github.com/rrflow/rrflow-development/blob/adc167691bdc4d1bd500e6db05809eee706761d4/docs/evidence/change-journals/gate-g/task-worker-installed-live.md)
binds the artifact, runner and results. Complete UI/project effects/RROFLOW,
reviewed learning, remaining fault acceptance and release qualification are open.

Published `c75c189612db7e7c8efe016fd92fb1052a3fb056` in draft PR229 implements `task-worker-execute` through the
existing engine task ledger, authorization, context, budget, shared endpoint
capacity and guarded completion. Seven focused engine tests pass, including
actual controlled HTTP exchanges, restart/readback, replay denial, revoked
permissions, Stop, lost responses and fresh work after configuration invalidation
without resetting effort/deadline. Canonical context is assembled and derived
readback is denied after context permission revocation. These protocol fixtures
are not LLM outputs or learning data. Local contract/inference/client checks
(218 tests), engine library checks (298 tests, four existing ignored helpers),
strengthened client checks (18 tests), architecture checks (32 tests), strict
Clippy and generated SDK/TypeScript checks passed. These test sets overlap.
The publication record binds the tested file hashes to the published source.
The installed trial above supplies the subsequent configured-provider worker
evidence; this increment is not part of the available ZIP.

The earlier GitHub observation reported PR229 draft and `DIRTY`. The ordinary
main reconciliation and current MERGEABLE observation above supersede that
status; they do not satisfy candidate CI or complete other dependency PRs.

The initial raw-Cargo native binary compiled, but its evidence script failed because
`--json version` returned `build.provenance: null`. No validated build receipt
or source envelope was produced. Its executable SHA-256 is
`dec189fd96ce57e501dd520a8f106a2ef8520688f3dbcaa379c657e6a13b6837`;
it is an unqualified debug artifact, not a deployable release. The corrected
canonical build above is a separate artifact. The failed script/log and original
artifact remain retained.

PR228 **merged** at `c2a43120375ae9d9d318d48533a42dc05ebe36da` on
2026-10-31 at 16:30:29 UTC after protected run `41216269606` succeeded.
PR224 **merged** at `906bec82c605ed095a2dbf9b0217cd89bd41c05f` on
2026-10-31 at 16:43:15 UTC after protected run `41216747041` succeeded.
Both protected runs finished with all 23 jobs successful; exact GitHub observations
are retained in `task-worker-prerequisites-merged.json` in the evidence directory.
No blanket merge or public-release completion claim applies. Older observations
below retain their source-specific history; these observations take precedence.

## Earlier source-specific observations

The following entries retain historical states and do not override the latest
verified advancement above.

Draft [PR229](https://github.com/rrflow/rrflow-development/pull/229) starts at
`9466ed0c` over the exact PR206 dependency `952e0928`. Local implementation now
separates bounded model text from strict route-choice decoding in one HTTP
transport. Five new protocol tests, including a loopback HTTP exchange, and all
eight existing selector tests pass. Optional worker policy is included in the
existing endpoint-profile approval digest; three worker contract tests pass.
All six real engine endpoint-configuration tests pass, including worker-policy
tamper denial, exact application and restart/readback. The initial missing-API
compiler failure is retained. The broader run exposed the expected pinned
OpenAPI digest change; recursive review found only eight added worker-policy
properties. After the intentional digest update, 216 contract/inference/client
tests and 291 engine-library tests pass (four existing engine helpers ignored).
Strict lint, generated SDK parity, TypeScript checks and six tests, all 32
architecture checks, formatting and repository metadata checks pass. The
increment is published at `cea6c846a1fdc80c5f957933fdd3918117d3e850`; PR229 remains
draft and its worktree is clean. The
[implementation journal](https://github.com/rrflow/rrflow-development/blob/cea6c846a1fdc80c5f957933fdd3918117d3e850/docs/evidence/change-journals/gate-g/task-worker-model-transport-policy.md)
retains failures, scope and exact results. There is still no public
worker dispatch operation, verified project effect, subscription adapter or
new model-quality evidence. No provider call or training occurred in this step.

Published candidate: `ffe3af9f73177a0af3d594a637f78368b6b93c16` in
[PR224](https://github.com/rrflow/rrflow-development/pull/224), now ready for review.
This is documentation-only relative to `168e93c649fe6548187b01db22bd47eb5552e077`.
Both full runs `41161519177` and `41165175925` passed all 23 jobs at `168e93c6`.
Normal
protected merging was enabled at 03:34 UTC on 31 October, but the queue API
refused admission because `pipeline / ci-gate` is still "expected", despite
the exact-head successful check from app 15368. A later skipped workflow on
the same head is observed; causation is unproven. Full normal workflow dispatch
`41165175925` also completed successfully, yet the queue API still refused it.
REST confirms exact-head checks from the required app, and GraphQL marks the
successful gate required for PR224. A linked evidence-only commit now gives the
normal ready-PR pipeline a unique head; run `41206082118` has now passed all
23 jobs at `ffe3af9f`. Normal protected queue admission subsequently succeeded;
the exact PR is queued at position one. The prior gate mismatch is retained,
without claiming its cause established. No rules or checks were bypassed.
PR224 is open and unmerged. Protected run `41210074230` at
`b3c7cb9b6e39846a195a355af381df2a18237d12` reports a macOS reopen-job failure:
Rust 1.99.1 panicked decoding metadata while compiling the release engine,
before the reopen test ran. The log explicitly says no build cache was restored;
the cause is not established. Raw job `124563021519` output is retained in
`source-inventory-protected-macos-job.log`, SHA-256
`2edbf796b6b168d01d2156fb81694a328d83076a9d84b0bb8024edbf3261694e`.
The first protected attempt completed with 21 successful jobs; macOS compilation
and its dependent final gate failed. Windows/Linux reopen jobs passed. The first
result is retained in `source-inventory-protected-first-result.json`. A targeted
rerun of failed job `124563021519` and its dependent gate passed: attempt two
of `41210074230` completed with all 23 jobs successful. The exact PR224 head
was re-admitted through normal merge controls and observed at queue position
two, awaiting checks. It remains open and unmerged; the first failed attempt
is retained and no merge gate is bypassed.

The prior `61bfe5a6` run `41160199235` failed Linux engine-authority job
`124415867194`: `replan_refuses_an_unreconciled_failure` assumed Inventory would
finish within 20 ms. The raw log is retained as
`candidate-41160199235-authority-124415867194.log`. The new correction covers
all four fixtures with this post-Inventory assumption, following returned
completion times through later read/reopen/resume operations. Every original
assertion and runtime check remains. Local validation: focused regression,
31 attunement tests (two existing ignored helpers), all 339 engine tests across
13 targets (four existing ignored helpers), strict Clippy and repository checks.
These are overlapping test sets, not additive totals. The prior failed native
run remains evidence; neither local passes nor a skipped draft run clears it.
[Correction journal](https://github.com/rrflow/rrflow-development/blob/168e93c649fe6548187b01db22bd47eb5552e077/docs/evidence/change-journals/gate-d/d-03-completion-relative-tests.md).
No production source or release binary changed in this increment.

The next bounded source package is draft
[PR226](https://github.com/rrflow/rrflow-development/pull/226), dependent on PR224.
Its separate `engine-inventory-delta-worktree` starts at `168e93c6`. A new installed
regression selects repeated Inventory phases and requires unchanged entries and
edges to retain their versions while each completion publishes its new metadata.
The initial characterization failed at 14 mutations instead of three. Local
implementation now reuses equal current authenticated facts and passes this
regression, three intervening record/edge/retirement cases and the 33-test
attunement module. The revised all-target/all-feature suite passes 341 tests
(four existing ignored helpers); strict lint passed in the dedicated
`target/delta-168e93c6`. Implementation is now published at
`923326ab8feb7b5eb8db38ff1050b7dbece17c3d`; evidence head is `f1a033b7`.
PR226 remains draft and unqualified. The exact-source primary built successfully;
its copied executable SHA-256 is
`df1cb50ddd70873ad22a29668a91618ac05c9a51d0af88c04eec9ab818dead2f`.

The source audit found a necessary recovery constraint for this package: compare
reuse against the actual current authenticated records, not only the last
complete head. Interrupted publication can leave newer partial observations.
Private progress format 2 binds the publication work set, because a newly
computed delta can have fewer groups. Final publication now runs the existing
source recheck for both small and grouped commits; it is not an atomic filesystem
snapshot. An initial broader run failed at the large fixture's Connect deadline,
before reuse executed; that failure is retained and its cause is unresolved.
Limits were not increased. The revised focused and full runs passed. The actual
1,870-path trial installed successfully but its first server startup returned
`ProjectBindingMismatch`. The failed estate remains intact. Offline verification
and a separate restart probe passed without changing the binary or binding;
the cause remains unresolved. A separate continuation on the preserved estate
completed Inventory (4,279 mutations), unchanged repeat (3), restart + README
edit + accepted successor + Inventory (6), unchanged repeat (3), exact final
reopen and offline quick verification. The scheduled Verify phase did not run;
restoring README makes the successor binding stale again. No repeatable-startup,
latency or RSS qualification follows. All seven existing installed CLI lifecycle
regressions pass at documentation-only head `f1a033b7`; they do not explain the
initial real-repository startup rejection.
[Installed trial journal](https://github.com/rrflow/rrflow-development/blob/f1a033b741337a9e9d963fbaa7c0950f0afd09c1/docs/evidence/change-journals/gate-d/d-03-incremental-installed-trial.md).

Draft [PR227](https://github.com/rrflow/rrflow-development/pull/227) is the next
bounded startup package, in `engine-startup-binding-worktree` from `f1a033b7`.
A fresh reproduction failed preview before installation. A native metadata
probe on another fresh clone observed actual `.git/config` replacement and Git
metadata changes during preview, but that probe ended at its time limit. These
observations do not identify the original startup failure's exact guard or cause.
Code inspection independently found that startup calls full source inspection
only to obtain a freshness report whose current-source flag it does not require.
The pre-edit oracle failed at reopen with `Git inventory input: InvalidConfiguration`.
Published source `39a7b6444c933bc2b931f5a00825942f5f0dd46f` now separates private
binding inspection from explicit source inspection. The regression passes:
startup and unchanged job readback survive invalid Git inputs; dependent Start
denies, then succeeds after repair; managed bootstrap tampering still denies
startup. Full verification retains its actual source digest and all 13 checks.
All 342 engine tests, strict lint, architecture/source closure and repository
checks pass. The exact-source primary built successfully; copied binary SHA-256
is `dfcbda6fa7743ca8851b42187e46350291dc6a3970339288a1a4f19cb105a9c3`.
Its new 1,870-path installed trial completed: invalid Git configuration still
permits startup and unchanged job readback; Start denies without changing the job;
restoring configuration permits Start. Initial/repeated Inventory, restart,
README edit, accepted successor and repeated Inventory recorded 4,279/3/6/3
mutations, with exact final reopen. All seven installed CLI lifecycle cases pass.
Offline quick verification passes 13 checks but reports source different from
the original installation precondition; it does not certify the successor's
freshness. The scheduled Verify phase did not execute. README and Git configuration
were restored, making the successor source binding stale again. The expected
invalid-input denial currently appears as HTTP 500/internal. Raw result:
`.swag/evidence/20261030/engine-source-inventory/startup-repository-result.json`,
SHA-256 `fe5ee0b2c93089dd0ba69331ec6473da98b1f394d951a28f4678b5bcd0edc77e`.
The original intermittent rejection remains unexplained. Required candidate and
protected checks, upgrades and public release are not established by this trial.
Published evidence head is `27e87749cb011828a35c8f0e1a9fb88a9a996012` in PR227;
the clean tested implementation remains `39a7b644`. The
[installed journal](https://github.com/rrflow/rrflow-development/blob/27e87749cb011828a35c8f0e1a9fb88a9a996012/docs/evidence/change-journals/gate-d/d-03-startup-installed-trial.md)
retains artifact/result hashes and acceptance limits. Documentation/navigation,
the 2,104-record execution inventory and whitespace checks pass. PR227 remains
draft behind PR224; nothing is declared merged by this evidence publication.

PR227 contains the retained PR226 behavior. Qualify the composed startup and
Inventory candidate after PR224, rather than requiring PR226 and PR227 to land
before each other. Keep PR226 open until a verified main destination retains its
implementation and evidence. Required candidate/protected checks still apply;
neither inherited ancestry nor local tests establishes a merge or delivery.
Checkpoint authority remains with RRFlow. This is write reuse; it does not
establish zero-content-read freshness, upgraded estates or worker execution.

The deployment assessment remains **pre-alpha**. Installed Inventory/restart/edit
evidence is real, but it does not prove task-to-worker execution, qualified model
routing, safe binary upgrades, or a public release. The next product acceptance
is one real task through the UI, engine-authorized worker, verified result and
correlated observation; retain the existing ordered plan and its prerequisites.

PR206's pre-edit integration brief names incoming PR227 `27e87749` against
controller `71d53e1e`. Published draft merge `c5bd4d99` has three resolved conflicts:
engine features/dependencies, public Rust exports and installed Python test
revision. Controller proposal/budget owners match their parent; incoming
Inventory/startup owners match theirs. Generated 71-operation/seven-signal parity,
workflow policy, Python test lint/format, documentation/navigation/inventory and
whitespace checks pass. Task-budget tests pass 27, attunement passes 34 with two
ignored helpers, and the combined planner's SDK identity check passes. The full
engine run fails: concurrent quantization build returns object-store Windows
Access is denied (OS error 5); 289 library and 63 integration tests pass, with
one failure and four ignored helpers. A focused rerun passes but does not clear
the failure. The stopped validation chain has not run its remaining suites,
strict lint or installed combined-binary checks. The
[integration journal](https://github.com/rrflow/rrflow-development/blob/c5bd4d99fa84a107ce7c46171f335107977d0d2d/docs/evidence/change-journals/gate-g/controller-inventory-integration.md)
retains the failure and exact source; no worker or complete integration is claimed.

Separate [PR228](https://github.com/rrflow/rrflow-development/pull/228)
starts at public main `f256c8e1`; opening evidence head is `33e54770`.
Object publication checks existence before a replacing rename. A separate
Windows probe reproduces error 5 with a reader-held winner, while non-replacing
publication reports already-exists and preserves both files. The exact original
error site remains unproven. Two deterministic regressions compiled and failed
on the original code. Published repair `a40a4f8cb8f9657f320d6194c09188add6017466`
now passes both, using anchored non-replacing publication and authenticating the
winner before reuse. Corrupt collisions preserve both files; other I/O failures
propagate. Quarantine semantics and crash hooks remain intact. Windows validation
passes 13 object tests, six native filesystem tests and all 257 storage tests
(two existing ignored), plus strict lint and repository checks. PR228 candidate
CI `41212170341` passed all 23 jobs. Normal queue admission for exact head
`a40a4f8c` succeeded; protected merge-group `41216269606` at `c2a43120` completed
successfully. PR228 merged as `c2a43120375ae9d9d318d48533a42dc05ebe36da`
at 16:30:29 UTC on 31 October. PR206's pre-edit brief
now binds ordinary composition of that exact revision. One POAM conflict is
resolved, retaining both histories; existing source-observation exports remain.
Resolved source tree `82065cd6caf18855b6c365a3665ce53eb45e11a1` passes the original
concurrency case, all 353 engine tests (four existing ignored) and 208
contract/inference/client tests. The earlier failed run remains preserved.
Strict lint, all seven installed CLI lifecycle cases, planner identity, generated
parity and repository checks also pass. The ordinary merge is committed as
`9e167aad55323c964d436a030745900e9f81c0ab`; published evidence head is
`952e0928c55f809b4f9fcce4dcf3808878a0bd65` in draft PR206. Its clean-source
153,362,944-byte Windows engineering primary is retained as
`.swag/evidence/20261030/engine-source-inventory/controller-publication-rrflow.exe`,
SHA-256 `f0f35eacf4e59fc847aa7016906b54359ca73fb3c18a8dc5eb261f7779ad4f92`.
Both installed Python SDK edit/replan cases pass against that exact copied
executable (two passed, no skips). Compact and formatted API hashes were compared
and verified to describe the same schema. No real endpoint or worker call was
made; the prior 1,870-path trial remains bound to its original PR227 binary.
This is an unoptimized, unqualified engineering artifact; main landing, release,
upgrades, model quality and full worker acceptance remain open.
No production repair or passed regression is claimed yet.

Read-only discovery also found Claude Code 2.1.310 reporting a Claude Max login.
Only CLI/version/help and filtered auth metadata were retained; no model task
ran or credential was printed. See implementation-plan's worker-access section
for the supported subscription boundary and still-required adapter qualification.

RROFLOW source was separately inspected at
[`e27920912a2c24a9c3adc5fc7546be9d14859a7c`](https://github.com/rrflow/rroflow-development/tree/e27920912a2c24a9c3adc5fc7546be9d14859a7c).
It contains Codex/Claude collectors, `rroflow.turn/v1`, authenticated ingest and
JSONL/Postgres stores. The engine README's blanket "not yet implemented" wording
is stale for that separate service. Its current turn schema has no typed engine
task/attempt/source/receipt correlation; resend replaces by event ID. Do not
equate an agent turn with an immutable accepted engine effect. The earlier local
evaluation-report ingest evidence below remains bounded evidence, not a hosted
controller journey. No new live-service, learning or deployment check was made
during this source inspection.

Normal merge `6b2b2c20` includes exact PR221 head `f6185c2c` and its seven-case
offline harness repair. PR221's earlier candidate passed, but protected run
`41156697702` has a verified failed optional-engine job `124404956228`: fixed
test timestamps could precede an operation's actual completion. The published
repair derives subsequent times from returned job completions, preserving all
production time/authorization/replay checks. PR221 has not separately landed;
do not close it before its retained behavior has a verified landed destination.

A fresh dedicated Cargo target at
`engine-source-inventory-worktree/target/candidate-6b2b2c205f` passes 276 engine
library tests (four existing ignored), seven installed CLI cases and two real
HTTP SDK tests using the rebuilt copied primary. Final repaired all-target,
all-feature validation passes **339 tests across 13 targets**, four existing
ignored helpers; strict all-feature Clippy and repository checks pass. A first
broader run caught four undeclared test-only journal reads; the exact allowlist
entry now names those bounded Inventory oracles without permitting runtime replay.
The isolated primary SHA-256 is
`4db1c73a4ed08b6652c2d71c13f6b5186a9d4ddbb0819f7e616f8b80480c65a0`;
it predates the final test-only corrections and is not a release artifact.
[Integration journal](https://github.com/rrflow/rrflow-development/blob/61bfe5a60f8c5385cbff856b40540f48704e8959/docs/evidence/change-journals/gate-d/d-03-candidate-integration-clock.md).
Raw logs: `integrated-candidate-*`, `integrated-receipt-clock-*` and
`dependency-221-queue-*` under the existing evidence directory. Native candidate
and protected checks remain required; the full controller/worker/learning goal
is incomplete. No new model call or training was performed in this increment.

## Prior bounded-publication evidence at 63265630

The prior [PR224](https://github.com/rrflow/rrflow-development/pull/224) increment publishes
`63265630d3ab3ec9095e55145c4875717e3f79e8`. Actual installed Inventory on the
1,870-path RRFlow source repository exposed a 16 MiB WAL batch rejection at
`2cfc0bd9`. Reopen proved that rejection had published no Inventory checkpoint.
The repair retains the physical limit and writes bounded observation groups
with engine-owned resumable progress. Only final publication certifies the
complete snapshot, authenticated head, phase checkpoint and command receipt.
Partial observations are not a complete project inventory.

The real copied Windows primary installed the same source revision in a separate
estate, completed Inventory in 14.042 seconds, reopened, accepted an ordinary-edit
successor and completed Inventory again in 17.046 seconds. Cursors were 4281 and
8559. A third process recovered the exact second job; offline quick verify passed.
The original README was restored, making that second source-bound plan stale.
The candidate binary SHA-256 is
`9105fe3a3dd207174cbb26f65e5537b8e06e1f274edaa1c45e0d70f17ab4bb69`.
This is an unoptimized engineering binary, not a signed distribution.

Final validation: 276 engine tests passed, four existing ignored; seven installed
CLI tests; strict all-target engine lint, format, generated surfaces, documentation,
navigation and 2,093-record execution inventory. Large installed tests prove
interruption/reopen without duplicate groups and refusal of stale completion
after an edit during publication, followed by acceptance of a successor plan.

The new executable is rejected against the old estate's sealed executable hash.
The original failed estate was preserved. Safe binary replacement is still a
deployment gap; the successful test is a separate installation, not an upgrade.
The first new-clone preview also rejected changed binding; a later attempt passed
without weakening validation. Its exact changing input was not identified.

[Bounded-publication journal](https://github.com/rrflow/rrflow-development/blob/63265630d3ab3ec9095e55145c4875717e3f79e8/docs/evidence/change-journals/gate-d/d-03-bounded-inventory-publication.md)
records failures, source/binary identities, commands and limits. Raw evidence:
`.swag/evidence/20261030/engine-source-inventory/bounded-*`,
`installed-repository-*`, and `resumed-repository-*`.

Remaining: final-manifest/retirement size, old incomplete-observation retention,
safe native reuse/no-work checkpoints, native race and memory qualification,
Linux/macOS, candidate/protected CI and merge. Explicit Cancel still serializes;
final source recheck is bounded, not an atomic filesystem snapshot. No full
Connectome/model/worker/RROFLOW journey, reviewed learning, new training, current
endpoint health, 29 GB or public-release claim is established.

## Prior smaller-project evidence at 2cfc0bd9

Draft [PR224](https://github.com/rrflow/rrflow-development/pull/224) publishes
`2cfc0bd9f71845ceb45fb0c0d6cf853f0484efd2`. Inventory now prepares source observations
through the installed Git/native traversal and atomically publishes canonical
snapshot, entries, containment, change set, checkpoint, command receipt and
committed head pointer. Prior records are read at their authenticated committed
identity and validated before use. This is implemented and tested on the draft
branch; it is not merged or release-qualified.

The installed engine test proves Inventory replay without a cursor advance,
reopen, edit/add/delete/rename, stale-plan refusal, successor acceptance and a
second Inventory with correct changes and retired identities. Rejected source
and configured output-limit attempts leave runtime/job/head unchanged; the source
attempt can retry its receipt key. The actual relocated primary executes Inventory
through the generated Rust client, survives forced termination, reads back the
checkpoint, and accepts another Inventory after an ordinary-edit successor.

Verified source: 273 engine tests (four existing ignored), 15 Git/config and 21
inventory component tests, 11 native Windows filesystem tests, seven installed
CLI tests, an additional exact copied-primary trial, two installed Python SDK
cases, 32 architecture tests, strict lint/format and repository checks. Retained
failures include obsolete unavailable-Inventory expectations, lint findings and
system Python lacking pytest; the frozen SDK environment passed.

[Immutable engine journal](https://github.com/rrflow/rrflow-development/blob/2cfc0bd9f71845ceb45fb0c0d6cf853f0484efd2/docs/evidence/change-journals/gate-d/d-03-durable-inventory-checkpoint.md).
Local evidence: `.swag/evidence/20261030/engine-source-inventory/durable-*`.
The copied engineering binary SHA-256 is
`078c772ef35c641927dce101cad9e33bc67ba394010eb9b32a5b01266bfcb23e`.
It is unoptimized and is not the signed/release bundle.

PR223's pure component merged as `f256c8e1337d85fa01f2a0c61e895a4d213163fa` after
protected run 41144688431 passed. PR224 includes the earlier Git traversal,
atomic-store composition, native observations and selected-plan integration.
Its preceding `9cc0f770` preflight on a real public repository was read-only;
that evidence must not be relabeled as installed Inventory qualification.

Next: qualify native reuse/no-work checkpoints, filesystem races, cancellation,
resource bounds and larger installed Git/non-Git projects; reconcile and pass
required candidate/protected CI. Eligible content is still reread. Explicit
Cancel serializes behind active Inventory. Linux/macOS execution and durable
incomplete error observations remain open. Parse/later phases, the complete
Connectome task/worker/RROFLOW journey and independently reviewed learning remain
incomplete. No new training, endpoint health, 29 GB or public release claim.

## Active owner constraints

The owner requested an active goal for the complete real-task controller workflow.
Follow [the implementation plan](implementation-plan.md). No fake tasks, results,
labels or consent; no new training on synthetic or assistant-inferred targets.
Provider/model choices, endpoints and operating limits must come from explicit
configuration and actual capability evidence, never task-specific code branches
or embedded provider rankings. Missing training evidence requires real owner
input, not invented examples. [Contribution guide](real-task-review.md).

The current Unsloth launcher now rejects unadmitted and provisional training
before GPU imports and requires an explicit seed. Dataset admission/use rejects
non-real source declarations in every split. This does not authenticate local
review declarations or make legacy training scripts approved bypasses.

## Verified implementation and landing

PR196 and PR205 are merged. [PR188](https://github.com/rrflow/rrflow-development/pull/188)
merged as `2e6ab88ed08340b61513b2b6c3828b202369c49d` after protected run
`40957233182` passed. Later main `2f232cb39dbac82e83371a5689f65ca501b72fb8`
adds an independent CI cache warmer.

[PR206](https://github.com/rrflow/rrflow-development/pull/206) is draft and unmerged.
Its earlier candidate `54fb845dffd702e1504c7f9a0cc2a3c5757d2bf2` passed full
candidate CI, but protected run `40982529726` failed macOS APFS image creation
with `hdiutil: create failed - Resource busy`. This is not a failed controller
routing assertion; its root cause remains unresolved at C-07 / POAM-035.
Main subsequently advanced to `6fe8b7590d913beda9b009551e5d2d2644e406d9`.
Published ordinary merge `f278fa6f4233f32b069eff4e5fa00bf50ba12aac` resolves
19 contract-digest/projection conflicts by
regenerating from both semantic owners. Contract/inference tests, 27 budget tests,
5 endpoint-configuration tests, formatting, strict Clippy and all SDK parity
checks passed. TypeScript lint, type checking and six tests passed. This is
source reconciliation, not qualification of a newly built binary. The old
installed receipts retain their original revisions.

Public main subsequently advanced to `a76faf7046b48819a06c31219e9db973b7f6a06b`
when PR218 and its PR208 dependency landed. PR206 now publishes ordinary merge
`71d53e1e86e17bcc3663dd4d82a7f03451b991dd`, resolving all 29 contract/projection
conflicts and preserving the controller alongside versioned attunement plans
and source-bound replanning. Local checks passed: 207 contract/inference/client
tests, 268 engine tests with four ignored, 11 storage-contract tests, strict
Rust lint/format, SDK tests/parity and repository policy checks. The candidate
has 71 public operations. It remains draft; the original protected native
failure is unresolved. PR212's integration is recorded below, and existing
Connectome/binary receipts retain their earlier source identities. Landed
attunement executes Connect only; this is not selected-worker execution or
ordinary-edit recovery of arbitrary effects.

PR222 now integrates that controller/attunement dependency at
`c376e27126c0fd513f8ffeb1e8e17a8befe87602`. One Cargo-time Rust operation generator
replaces the two branch projections, preserving the sealed proposal call and
typed attunement helpers. Nine focused tests and 182 client/contract tests passed,
along with strict lint/format, 71-operation parity and repository checks. The
initial Rust visibility error and its correction are retained in the integration
journal. These are component and real-server fixture checks, not a new packaged
binary or model observation. PR222 remains draft; Connectome's refresh is recorded
below. No existing
desktop/BF16 receipt acquires the new revision's identity.

PR212 now integrates PR222 at `8cf235ac06a92bc16ae74e746ff1928fb8415b47` through
a conflict-free ordinary merge. Runtime, contract and SDK sources match `c376e271`.
All 18 packaging checks against the original archive, four build-provenance tests,
71-operation parity and repository checks passed. The canonical release build
finished successfully from this clean revision. The new Windows archive is
`files/distributions/rrflow-controller-trial-windows-x64-8cf235ac.zip`, 33,976,833
bytes, SHA256 `8fc7a5056bde73f29ffb435393d6254cac152ff0f30aea4158e597fb9749f9a3`.
All 18 checks passed against this new archive. Its extracted primary installed,
served, reopened and passed 13 quick checks after each owned process stop with
only System32 on PATH. Instance, plan, inventory and runtime identities matched
across reopen. Evidence is retained in `.swag/evidence/20261030/controller-bundle-refresh/`
and the PR212 refreshed-artifact journal. No new BF16 observation, worker effect,
clean-machine or signed-release qualification is claimed. The original ZIP and
receipts remain unchanged. PR212 remains draft behind PR222/206.
The artifact evidence is published at PR212 head
`9471226bd6631c024b2d8e12b10a39286096d952`; its build remains bound to `8cf235ac`.
GitHub reports the PR open, draft and conflict-free. This is not a merge or
candidate-CI acceptance claim.

Connectome [PR27](https://github.com/rrflow/connectome-development/pull/27),
stacked on PR26, closes the desktop-owned endpoint credential mapping startup gap.
Implementation/build source `6de73eec58be5cea4cdae42fea6001772006ee3a` passed
complete CI run 41134260205. Evidence head `7a37a6a7327db92553fa7fb00d122a43b641e5f4`
adds actual desktop installation/start/stop/reopen receipts and screenshots; it
failed CI run 41135105707 because Biome required formatting of seven raw JSON
reports and their manifest; native platform and actual-process jobs passed.
Correction `f8139cc725a6f546fdf177b522ff4772121bf8ca` preserves raw reports as gzip,
formats only the manifest, and passes full local `pnpm check` plus verification
of all 16 evidence files and their original bytes. No check was disabled.
Correction CI run 41136356561 passed all jobs at `f8139cc7`: frontend/render,
Windows/macOS/Linux native, actual-engine process integration and ci-gate. The app passed an explicitly chosen empty
mapping to its owned engine; both native readiness checks and two 13-check quick
verification runs passed with matching instance/plan/inventory/runtime identities.
No provider credentials, profile admission or model request occurred. Native tests
passed (40 ordinary; 16 actual process cases plus one inactive capture helper).
The first browser smoke run retained a JavaScript `ERR_NO_BUFFER_SPACE` failure;
one serialized run passed all four, without claiming a root-cause fix. The
source-bound preview is retained under `.swag/controller-ui/6de73eec/`. The app and
owned trial engines were stopped. UI environment/profile onboarding and the full
worker workflow remain open; prior BF16 evidence retains its original identity.

The public `task-endpoint-propose` operation has dedicated authorization,
configured experimental policy/credentials, bounded native transport, atomic
freshness checks and capacity/attempt accounting in the existing task budget.
It grants no worker effect. The earlier 63-operation implementation's relevant Rust suites,
27 budget tests, strict lint and SDK parity passed in the implementation stage.

## Live installed controller evidence

The owner completed Tailscale authentication at 23:16 UTC. The existing private
BF16 container was healthy and idle. Owned SSH process 95740 restored loopback
port 8084. Configuration, endpoint and credentials were read from the existing
operator files; no provider identity/ranking was embedded in product code.

The source-identified d365 Windows development binary completed a real BF16
proposal: HTTP 200, 1,797 reported input tokens, 26 output tokens, adapter elapsed
2,362 ms. Accepted proposal and budget survived restart with identical readback;
same-attempt replay was rejected, leaving one reserved step. This is one
single-candidate transport/admission observation, not quality or performance
qualification. Binary SHA256:
`7fe07a7198b864a2642c5a9a521e8e13ac7a7d935fd62e8477f2c075fd7680b9`.

Four installed fault histories used actual engine requests/provider responses,
held or dropped by bounded repository-owned proof tooling:

- Configuration replacement invalidated stale output; a fresh request on the
  same task succeeded with two spent steps and the original deadline retained.
- Session closure invalidated output and retained spent effort.
- Stop prevented publication and retained cancelled state plus conservative
  remote uncertainty through restart.
- Lost response retained failed-attempt state and uncertainty through restart.

These six total actual provider calls created no training labels or admission.
Stop was applied after the real provider response reached the relay; this proves
local cancellation of acceptance, not remote GPU termination. Ordinary repository
edits and engine-owned successor plans remain a separate implementation requirement.
The previous uncertain estate was preserved, never reset or automatically retried.

Thirty-three exact public/relay receipts and their digest manifest are published
with the immutable live journal in PR206. Secrets/session tokens were checked
absent. All trial runs, mixed-mode rejection, syntax, receipt hashes and final
repository checks passed; capture tests (8) and cache-policy tests (3) passed after
main integration. CRLF capture handling and one transient GitHub metadata
assertion are retained as validation history, not hidden or treated as runtime bugs.

## Connectome native task workspace

Connectome now pins both SDKs to engine `c376e271`; source `a3d179dc4d2efa812f925ca23eeb74cb7b20de5a`
built a matching Windows preview. Evidence head `ed6ed0e59d68fe310bf2b719fd721eee167a1c10`
is published on draft PR26. The value fixture was regenerated through actual engine
I/O; 39 ordinary native tests, 15 actual process cases, strict lint/format, full
frontend checks and four rendering tests passed. The process runner reports 16
passes because it includes one inactive visual-capture helper; earlier aggregate
claims of 16 actual process cases need that qualification.
The new pair is retained at `.swag/controller-ui/a3d179dc/` with its build receipt.
Connectome SHA256: `08057184b7aaafbb22d5a53ce022739d07d9235924a137add32fdf2ac1af0a90`;
engine SHA256: `bf1f17f116246dacb4ee55c46484698b57f3184bfffe38c2d0b7d7d4207e8848`.
It contains no model weights. No new desktop interaction or BF16 call was performed
with this pair. Exact-head [CI run 41127990158](https://github.com/rrflow/connectome-development/actions/runs/41127990158)
passed frontend/rendering, all three native platforms, actual-engine SDK/process
integration and the required gate. Dependency landing, signed/clean-machine/container
delivery and the full worker/outcome workflow remain distinct requirements.

The earlier evidence head `9f7050525e63a98a75c69127ec18147545145b24` passed
the complete [Connectome CI run 41122658199](https://github.com/rrflow/connectome-development/actions/runs/41122658199),
including Windows/macOS/Linux, frontend and actual-engine SDK/process integration.
This does not land the draft PR or its engine dependencies.

[Draft Connectome PR26](https://github.com/rrflow/connectome-development/pull/26)
implements the native task/budget/proposal/readback/Stop workspace at
`d7eb6ea3027b76e1afd515715ab4958e66083060`, pinning both SDKs to PR222's
`61ddb26416811ba7e56edf2e28b8cef3acad5930`. Requests use native credentials and
validated contracts; reads never dispatch inference. Known preflight failures
permit input review again; transport uncertainty requires attempt readback.

Local frontend checks/build, four existing rendering smoke tests, 39 native
tests and all 16 real-engine process cases passed. A built Windows preview app
installed a fresh estate, recorded the real PR26 maintenance task, configured an
explicit budget, displayed the missing endpoint profile, retained task/budget
through webview reload, and cancelled via Stop with zero charged work. After
closing it, quick engine verification passed all 13 checks. Detailed evidence
and the actual screenshot are in PR26's `docs/controller-proposal-verification.md`.
The local preview is `.swag/controller-ui/d7eb6ea3/connectome.exe`; this is a
development build, not an installer or clean-machine qualification.

The subsequent live desktop trial used a fresh, operator-configured engine and
the existing experimental BF16 profile. One explicit UI request was accepted:
1,017 input tokens, 20 output tokens, 1,890 ms adapter elapsed and 1,919 ms budget
charge. Webview reload, Recover last attempt and explicit readback retained the
same receipt and one spent step. Independent public task/budget/attempt reads
before and after UI recovery were identical. Post-close quick verification passed
13 checks. PR26's `docs/controller-desktop-live-trial.md` retains receipts,
screenshots and the auxiliary readback-helper HTTP 400 failure.

PR26 remains draft and depends on unmerged engine work. This proves one live
UI-to-engine-to-configured-endpoint proposal, not general routing quality or
public release. Operator-managed credential setup is still required. No worker
execution, source-edit successor plan, RROFLOW delivery or reviewed training
outcome was produced by the desktop trial.

## Native client proposal integration

[Draft PR222](https://github.com/rrflow/rrflow-development/pull/222) is published
at `61ddb26416811ba7e56edf2e28b8cef3acad5930`; implementation/build source is
`dccfc41962d6ff998c9e309ebd550d8f5fadcbdf`. It generates fixed-session operation
metadata from the engine catalogue and adds a semantically validated native
proposal call. Metadata for 51 operations is not callable coverage: only the
proposal has this new validator. The call sends once, checks request/response
identity, status/media and bounds, and leaves uncertain attempts for readback.
The existing legacy SDK methods remain unchanged.

The real native-client trial completed one BF16 proposal on a fresh installed
estate using the actual PR222 maintenance task. The native example SHA256 is
`7eb1ff25d0c3a60492d81e226f1032eda2da3b5d088a05581d55889178c0a72c`;
the primary executable remains the earlier `54fb845d` release build. Actual
receipt fields report 1,731 input tokens, 20 output tokens and 1,881 ms adapter
elapsed. Restart returned the identical proposal/budget; repeated attempt identity
was denied and one step remained spent. This is one transport/admission observation,
not model quality, worker execution or full cross-version catalogue qualification.
The driver explicitly terminated its own Windows servers (exit 1 retained), so
this is not graceful-shutdown proof. Postflight found the provider idle and the
authorized/reopened server PIDs absent.

Four focused cases, 170 client/contract tests, strict lint, example build,
generator tests, parity and repository checks passed. Initial fixture/compiler/
format/encoding failures and their corrections remain in immutable journals.
Sixteen exact public receipts and hashes are linked from PR222. No training,
labels, consent or output repair was introduced. This branch remains draft behind
PR206 and the shared native CI failure. Connectome's native/UI task-proposal flow
is the next integration boundary; the complete real project task and independent
review input remain pending.

## Next execution

Cluster authentication was resolved for the previous trials. Verify the current
listener/service before any further call; the prior postflight is not a current
health check. Preserve uncertain attempts. Earlier full candidate runs
`40973523756` and `40978912042` passed; the latter entered the protected queue.
Protected run `40982529726` subsequently failed as recorded above. Do not describe
PR206 as queued or merged. The reconciliation is published; resolve the native failure at
its owner, then obtain exact-candidate and protected merge evidence. New main's
additional diagnostics do not themselves prove the failure repaired.

[Draft PR212](https://github.com/rrflow/rrflow-development/pull/212) now supplies
the [native Windows engineering bundle and testing guide](testing-binary.md).
Its refreshed head is `19ef6a04c9f3e409439ca567eb6f5f0285b58938`, ordinarily
merging PR206 `f278fa6f` without conflicts. All 18 archive checks passed again
against the original ZIP; all 14 captured receipt hashes remain exact. Generated
surface and repository policy checks passed. It remains draft behind PR206
and required candidate/protected CI. The historical artifact is unchanged.
The optimized executable is 113,481,216 bytes; the ZIP is 33,850,986 bytes. Engine
source is `54fb845d`, assembly source `98d0de93`. ZIP SHA256:
`46b85f824d712cd8e8cceda4a6b0cd01bb1585f3f25a1f8c64ef8b7657f05b6f`.
All 18 archive checks passed, including corruption of actual archive copies.
Extracted hashes matched, and the packaged binary/helper/relative receipt completed
a real BF16 proposal, identical restart readback and replay denial. Primary ready
and quick verification passed with only System32 on the child PATH and no provider
credentials. These are engineering observations, not clean-machine Gate J proof.

The two optimized build passes completed in 39m21s and 19m53s. The outer PowerShell
wrapper returned 1 after treating Cargo stderr progress as an error; its accepted
receipt was independently checked against the actual executable hash, version
report and clean source. Assembly exited 0. The shell result is retained.

Session, Stop and disconnect release fault tests passed. Configuration replacement
invalidated the first output, but the fresh second model response requested an
unsupported effort `observed`; the engine rejected it with 412. That case FAILED.
Recovery retained two spent steps, 4,688 ms charged and stopped/uncertain capacity.
No retry, response repair, training label or uncertainty reset followed. The
other three cases used independent estates. Six real release-trial provider calls
were made; model quality remains unqualified. Fourteen exact public receipts and
their digest manifest accompany PR212. The provisional checkpoint is not promoted.
Postflight at 00:56 UTC found the provider idle, SSH forward 95740 listening and
no owned RRFlow trial server left running. PR206 was then `AWAITING_CHECKS`;
that historical observation is superseded by the protected failure above. Final
repository checks and all 14 receipt hashes passed for that original artifact.

Continue the real task/plan/worker and Connectome/RROFLOW journey from the
[implementation plan](implementation-plan.md). Independently reviewed real
outcomes still gate new training. Release/image delivery and measured 29 GB
serving remain unqualified. No full-goal completion is claimed.

Local evidence is under `.swag/evidence/20261029/installed-controller-proposal-connected/`,
`installed-controller-fault-*/`, `controller-access-restored/` and
`controller-operation-plan/`. Existing build/baseline/failure receipts remain intact.
Release artifact observations are under `installed-controller-release-*`,
`controller-release-primary-checks/` and the same operation-plan directory.

## Product direction

Build a turnkey System One controller for people building real projects. SWAG
captures intent, proposes bounded decisions and assigns work to suitable models.
It does not need to generate the implementation itself. Short outputs can reduce
generation and cache costs; they do not remove resident model weights or make
reliable decisions trivial.

RRFlow owns the single accepted plan, source revisions, permissions, budgets,
effect admission and receipts. SWAG proposes; the engine independently validates.
RROFLOW supplies correlated outcomes through an integration still to be proven.
Ordinary edits invalidate affected dependencies and lead to a successor plan;
they must not permanently block exploration or unrelated work.

Prioritize Claude Fable, Sonnet and Opus, with Codex support. Bind routes to exact
model, supported effort, authorized access method, available quota and task-family
evidence. A subscription is not an API credential. Capability and entitlement
must be checked through the actual binding; model names alone prove neither.
Handoffs carry objective, context references, expected artifact, verification,
allowed effects and remaining budget. No subscription dispatch is implemented here.

## Verified baseline and limits

| Item | Evidence as of this review |
|---|---|
| Base | `Qwen/Qwen3-Coder-30B-A3B-Instruct`, revision `b2cff646eb4bb1d68355c01b18ae02e7cf42d120` |
| Precision | BF16; original weights, not a custom SWAG checkpoint |
| Endpoint | Authenticated private experiment; local forwarded `/health` returned 200 on recheck |
| Runtime | vLLM; one GB10; 4096-token context; one concurrent sequence; 1 GiB KV cache |
| Weights | 61,066,575,656 bytes on disk; vLLM reported 56.93 GiB model memory |
| Smoke | 4/8 synthetic cases matched, before and after reducing KV cache from 26.57 GiB |
| Failures | Cost limit, effort support, unauthorized selection under prompt injection, and cheapest eligible choice |
| Latency | Recorded warm median 1.893 seconds across seven short requests; not a production benchmark |
| Memory | Host used-memory snapshot 74,693,566,464 bytes, including other workloads; isolated peak unmeasured |
| Unsloth | Completed 33 BF16 LoRA steps; custom merged checkpoint freshly loaded into a private endpoint |
| Existing adapters | Earlier Qwen2.5 7B/14B/32B artifacts include two-step runs; not controller qualification |

Evidence lives locally in `.swag/evidence/20261028/`, especially
`baseline_manifest.json`, `compact-smoke.jsonl`, `compact-runtime-evidence.json`
and `current-summary.json`. Access instructions are in `.swag/cluster_access.md`.
These ignored files are not distributed with a checkout. Credentials stay outside
documentation. Endpoint liveness can change; recheck before using it.

Docker/cgroup counters omit substantial model allocations on this GB10. Their
roughly 2.9 GiB reading is not the model footprint. Cache reduction is real but
does not establish a 29 GB model or preserve quality beyond these eight cases.

## Delivery sequence and acceptance

1. Freeze a reviewed routing schema and evaluation protocol. Include intent
   ambiguity, changed inputs, unsupported effort, quota exhaustion, authorization,
   injection, abstention and handoff verification. Keep deterministic policy
   enforcement outside the model. Synthetic smoke cases remain development data.
2. Admit consented observations with provenance, independently reviewed outcomes
   and project/time-separated train, development and held-out acceptance splits.
   Overrides are preferences, not automatically correct labels.
3. Train one versioned custom candidate from the pinned base. Record data, trainer,
   adapter and tokenizer identities; export and freshly reload BF16 weights.
   Verify a supported BF16 training configuration and resource budget before launch.
4. Evaluate original BF16 base A against custom BF16 B on the same frozen protocol.
   Keep training loss, HTTP success and routing quality as separate measurements.
5. Quantize exactly B into C only after evaluating B. Compare A/B/C with frozen
   quality margins, latency limits and workload. The later footprint target is
   **29,000,000,000 bytes for serving**, including runtime and cache, not just files.
   BF16 is the first milestone and is not required to fit that later target.
6. Promote reversibly only with retained evidence. Native executable packaging
   where feasible and a GitHub-built scale-out image remain delivery requirements;
   neither is complete. A binary does not eliminate weights or GPU dependencies.

The longer-term research goal is a genuinely from-scratch 14B routing specialist.
Assess token/data quality, compute budget and training feasibility before committing
to that run. Fine-tuning or distillation is not from-scratch training. Beating 30B
on a declared routing workload is a hypothesis to test, not universal superiority.

## Open boundaries and stale context

- Engine [PR #176](https://github.com/rrflow/rrflow-development/pull/176) merged
  on 2026-10-28 at `2f1424283e257ce41b2413cf17dcc86fe45a34e1`.
  Schema/design work does not prove runtime enforcement or completed integration.
- Capture includes an explicit emitter and a bounded local watcher for tracked
  Git diffs and a caller-supplied issue/title/override file. It retains diff hashes,
  suppresses unchanged polls across restarts and preserves prior observations.
  Remote issue polling, provider dispatch and automatic training admission remain
  unimplemented. See [capture usage and scope](passive-capture-watch.md).
- Preserve persistent project intent when applying task intent; verify this before
  claiming complete project-context handling. Provider/output admission also
  requires implementation review and evidence before autonomous effects.
- Legacy 7B/14B/27–28B defaults are existing policy scaffolds, not a selected
  deployment. Old Qwen2.5, AWQ-first and 6–9 GB plans are superseded experiments.
- Python CLI/MCP previews and offline publisher tests are not landed RRFlow or
  RROFLOW integration. Require relevant PRs and real correlated receipts.
- This workspace has no Git history. Do not claim a commit, PR or image release
  from local edits. `AGENTS.md` is preserved; its older testing paragraph predates
  the current unittest suite. Run `python -m unittest discover -s tests -p "test_*.py"`.

## Resumed implementation: routing data and evaluation

Offline review admission, project/time-separated exports, strict route schemas and
a digest-pinned evaluator are implemented. See [data and evaluation](routing-data-and-evaluation.md)
for their limits and commands. Training can verify the admitted train/development
files before GPU work; no real reviewed dataset has yet been admitted.

A new development-only protocol ran against the original BF16 endpoint: **7/13
matched, 5 eligibility violations**, warm median **1.310 s**, p95 **1.962 s**.
Different prompt/input framing means this is not an improvement claim over 4/8.
Evidence is in `.swag/evidence/20261028/routing-development-baseline/`.
The protocol failed; the model remains unqualified. Local tests cover evidence
changes, consent, split leakage and real loopback HTTP transport. Tests do not
qualify training or production routing.

Next boundary: independently review actual provider-task outcomes and freeze a
fresh acceptance protocol. The provisional intent training described below is
complete, but its data does not establish optimal provider routes. Do not reuse
observed development cases as acceptance data or label the original base custom.

## Research and visual evidence: 2026-10-28

The [research decision](decision-router-research.md) distinguishes Liquid RIPL
serving claims from d1 single-pass decision models and maps the proposed work to
existing RRFlow, Connectome and RROFLOW owners. Pinned Liquid d1-3B now ran twice
on spark-03: 9/13, three policy violations, about 92 ms warm median. RIPL itself
has not been installed. The Qwen BF16-first sequence is retained.

`tools/swag_evidence_projection.py` verifies retained evaluation artifacts and
exports content-free UI data plus a local RROFLOW-shaped report event. The
[TypeScript evidence viewer](../ui/README.md) displays the actual 7/13 snapshot,
failure signals and proposed learning stages. It cannot train, promote or execute
work. Signals suggest review; they are not automatic supervised/unsupervised jobs.
Live engine/Connectome integration remains pending its owning PRs. A real local
RROFLOW ingest now accepted both evaluation reports, handled duplicate retries
and returned exact stored readback. Hosted integration is still unverified.

Validation results, screenshots and exported signal records are retained under
`.swag/evidence/20261028/` and recorded with the current experiment evidence.

## Earlier experiments and review workflow

PR179 and PR180 merged before the current operation work. The following records
describe those earlier experiments; current landing and transport status are above.

Use [the implementation plan](implementation-plan.md) and
[experiment evidence](experiment-evidence.md) for the resumed work. Sixty-five
real merged PR tasks now have assistant-inferred intent labels; 44 train tasks and
21 separate-project development tasks are exported. This is provisional intent
specialization, not an independently reviewed provider-routing dataset. Original
Qwen scored 14/21 on that development split. Unsloth completed 33 BF16 LoRA steps
on spark-02 and exported a 61.07 GB merged checkpoint. A private endpoint deployed for that experiment
(`http://127.0.0.1:8084/v1` through SSH) served
`swag-qwen3-coder-intent-20261028`. It scored 15/21 intent tasks, with 65.1% balanced
accuracy versus the base's 56.7%. A majority-label rule also scores 14/21 overall.
The one-task gain remains preliminary. Custom routing stayed 7/13 with five policy
violations, so no autonomous routing qualification or compression claim is made.

Live access was rechecked at 03:55 UTC: unauthenticated model discovery returned
401; authenticated discovery returned 200 and the exact custom alias above.
Receipt: `.swag/evidence/20261029/custom-endpoint-health-035549.json`.
This verifies endpoint identity/access, not a new inference-quality measurement.

Stateless learning-review proposals and an A/B/C qualification evidence checker
are implemented. Neither starts an engine routine or grants promotion authority.

Engine [PR #179](https://github.com/rrflow/rrflow-development/pull/179) implements
the next bounded offline preparation package under RRFlow's `scripts/inference`:
source-bound paired-outcome review packets. The local run retains all 63 outputs
from the three models on 21 tasks, with independent review pending. Changed
inputs produce a new packet; previous evidence stays intact. See the
readable review table (`files/swag-paired-intent-review-20261028.md`).
This is PR implementation evidence, not merged runtime integration, admitted
provider-routing data or an automatic learning routine.

The local review workflow is now implemented at
`http://127.0.0.1:8891/review.html`: accept/correct/exclude labels, rationale and
evidence references, draft download/resume, exact packet binding and stale-file
rejection. [PR180](https://github.com/rrflow/rrflow-development/pull/180) adds the
RRFlow-repository validator, depending on PR179. A synthetic assistant browser
export passed the real validator twice with the same result; this proves the
file-exchange workflow, not independent human review or training admission.
No actual human decisions have been recorded. See [UI usage](../ui/README.md).

## Native endpoint configuration evidence

On 28 October, a clean-source Windows RRFlow development binary was built from
PR180 candidate `ba1203165de297c0e16977650658f1d32fe77a88`, with embedded source
and compilation provenance. A byte-identical, single-link executable was installed
in an isolated local project. Through the actual authenticated engine HTTP API,
the custom BF16 endpoint profile passed preview-without-write, apply/readback,
idempotent replay, two process restarts, revocation, stale-plan/revision rejection
and fresh revision publication. Final configuration revision is 3. Test servers
were stopped; the separate custom model endpoint remained available.

That earlier run proved durable configuration integration, not model dispatch.
Its then-unimplemented credential resolver has since been implemented in draft
PR206, with the unsuccessful installed dispatch described above. The profile
contains a 100 GiB capacity declaration rather than measured serving memory. The native
binary is a development build, not a qualified release or a bundled model.
Receipts and the executable are under
`.swag/evidence/20261028/native-endpoint-integration/`. See the experiment log for
identities, the initial packaging rejection and the exact verified scope.

## Next execution prerequisite identified

The engine dependency spine requires D-03 committed source inventory before
D-04 parsing and later worker handoff. The current installation inventory hash
is explicitly not that snapshot. Current attunement advances Connect only;
prepared prompt flights and open task records do not execute a selected worker.
D-03 must give stable source identities, exclusions/containment, explicit change
sets, unchanged-rerun content-read avoidance and atomic publication despite
concurrent edits/interruption. Downstream handoffs and successor plans must
consume that admitted snapshot instead of promoting the installation hash.
[PR223](https://github.com/rrflow/rrflow-development/pull/223) now supplies the pure
inventory proposal component at `a13ce981db6b25c358ccce6cc8afd83fba09d025`, branched
from current main `a76faf70`. Nineteen inventory tests and 32 workspace architecture
checks passed, along with strict lint/format and repository policy checks. The
initial truncated-file completeness regression was reproduced and fixed. Stable
scope/path identities, Merkle digests, explicit incomplete/error state, changed
entry sets and unambiguous rename candidates are implemented. Unchanged content
reuse is proved at the lazy iterator boundary only. The new crate is included
in existing candidate CI; PR223 is ready for review, not merged. Candidate run
41138038457 completed successfully at that exact implementation head. The protected
merge queue accepted PR223 at 23:28 UTC; run 41144688431 is still in progress at
merge-group revision `f256c8e1337d85fa01f2a0c61e895a4d213163fa`. No failure was
reported at the latest observation; this is not a completed merge. Earlier draft
runs were skipped and are not acceptance evidence.

The installed engine does not consume the proposal yet. Engine-authorized reads,
versioned Git/secret policy, strong filesystem-change observations, atomic source
records/change-set/checkpoint publication and real-project restart/edit proof are
the next integration package. No complete D-03, owner acceptance or ordinary-edit
worker recovery is claimed. No new model request or training data was generated.


## Engine inventory integration in progress

[PR224](https://github.com/rrflow/rrflow-development/pull/224) owns full D-03 engine
integration and remains draft. It starts from main `a76faf70`, ordinarily merges
PR223 in `da5662e9`, and publishes the native prerequisite at
`ef029fde4c98311b637e548f0304a5a261fa3dd1`. Existing anchored filesystem authority
now exposes handle-bound source metadata observations with native object identity,
change/modified timestamps, conservative age checks and named-path/read-handle
comparison. Four new actual-file Windows cases passed; the complete filesystem
target passed ten cases, plus strict Clippy, format and documentation checks.
Linux/macOS execution has not yet tested these new methods. Exact receipt:
`docs/evidence/change-journals/gate-d/d-03-native-source-observations.md` in PR224.

The next work stays in PR224: admitted versioned source policy, bounded Git-aware
reads, metadata-race handling and atomic runtime source-record/change-set/checkpoint
publication. The existing `commit_with_control_transitions` is the composition
boundary. No inventory worker was activated; no helper test establishes a
committed snapshot, ordinary-edit recovery or complete workflow. At the native
increment, Gitoxide packages were research only; the subsequent parser increment
below now pins and links the required buffer parsers. No new provider request or
training data was produced. PR223 candidate run 41138038457 passed all jobs; its
protected merge-group run 41144688431 remains active. No merge is claimed.

PR224 now publishes `22bbd5ff17a6e092391a1d0d0268d2610bd79289`: bounded pure Git
index/ignore parsing with checksum verification, explicit case/precedence rules,
tracked-descendant discovery and a preflight bound on compressed path expansion.
Unsupported split/sparse indexes return errors instead of partial tracking facts.
Fourteen focused Git tests, including 46 decisions recorded from Git itself,
19 inventory tests, all 32 architecture checks, strict Clippy, format and
repository checks passed. Fixture files are authored parser cases, not training
or routing evaluation data. Initial compile, fixture-order, target-tracking and
journal-coordinate failures are retained in the immutable partial journal
`docs/evidence/change-journals/gate-d/d-03-git-inventory-inputs.md`. PR224 remains
draft, open and conflict-free; full candidate acceptance is not claimed.

Next bind admitted versioned policy and bounded native source reads to these
parsers, then publish canonical source/containment/change sets atomically with
the attunement checkpoint. Git metadata/config/global-ignore admission, complete
filesystem safety/cancellation, real-repository traversal and installed restart/
edit/replan evidence remain required. The installed Inventory phase is still
unavailable. No worker, model, training or release artifact changed.


PR224 publishes installation-policy increment
`de29d92eb8c6921b158164f156da86362691e331`. Version-three bundled profiles now
admit typed source policy, and a version-two installation precondition binds its
hash. Positive rules exclude generated outputs, environment/key files and private
`.swag` state before content reads; eligible hidden project configuration remains
included. An actual locked-file regression reproduced the missing `server.env`
exclusion before correction. The corrected test leaves `.env`, `server.env` and
`.swag/session` unopened, while an eligible locked source file still fails.

All 10 installation checks, 262 engine tests (four existing ignored), 32
architecture checks, strict lint/format and generated/documentation/inventory
checks passed locally on Windows. The initial SDK refresh missed three scope
projections, and the first full suite retained an old profile identity; both
failures and independent hash/planner corrections are recorded in
`docs/evidence/change-journals/gate-d/d-03-installation-inventory-policy.md`.
No public configuration API was added. Future walker limits/settings in the
policy are not yet proof of their execution. Inventory remains unavailable,
PR224 remains draft, and no existing binary receipt inherits this source identity.
Next compose staged runtime state and its exact checkpoint read stamp in one
transaction, then finish the bounded walker and installed ordinary-edit proof.


PR224 now publishes atomic checkpoint composition at
`806813a9a1c1d309a655e8d0f4352aa864346f0a`. The existing store transaction can
stage the runtime plan, obtain its resulting authenticated read stamp, construct
control transitions and commit them together. Existing prebuilt-transition callers
use the same implementation. Actual rrflowMX/rrflowKV tests prove matching runtime
and checkpoint identity; rejected builders/stale control CAS leave every fixture
row unchanged, and successful native reopen recovers both from one WAL frame.
Five installed-lifecycle tests, 251 storage tests (two existing ignored), 262 engine
tests (four existing ignored), strict storage lint, format and repository checks
passed on Windows. Journal:
`docs/evidence/change-journals/gate-d/d-03-atomic-runtime-checkpoint.md`.
The bounded walker and actual Inventory phase are still unimplemented. Next connect
engine-authorized traversal and validated prior snapshots to canonical runtime
records and this checkpoint boundary, then prove installed ordinary-edit replanning.
No new binary, model call, training or end-to-end outcome is claimed.
