# SWAG decision-router alpha delivery plan

**Date:** 7 November 2026. **Status:** proposed implementation sequence, grounded
in inspected source. **Goal ID:** `decision_router_alpha`.
**Driver:** the SWAG delivery owner; each implementation PR names its responsible
person/session and successor. Repository owners retain acceptance authority.

This is the active SWAG delivery sequence for the owner's request to build,
train, extend, optimize and trace a personal decision router integrated with
RRFlow. It refines the [implementation plan](implementation-plan.md), preserves
its constraints, and does not change RRFlow's roadmap order or close its gates.
Historical experiments remain evidence for their original inputs and builds.

## Goal and measurable outcomes

Deliver a personal controller that uses the user's project intent, current
authorized project evidence, preferences and eligible capabilities to propose
useful decisions; RRFlow admits and executes authorized work; the user can
inspect, correct and verify the result. Reviewed real outcomes produce versioned
training candidates whose measured improvements can be promoted and rolled back.

Three outcomes belong to this goal:

| Milestone | User-visible result | Completion evidence |
| --- | --- | --- |
| A: supervised integrated alpha | Connect a real project, assess it using choice/score/binary, inspect an eligible route and handoff, authorize work, inspect its verified effects, and recover after an edit or restart. | The installed journey below passes on a matched engine/client build. A proposal or draft alone does not pass. |
| B: trained decision candidate | A new checkpoint learns a declared decision objective from admitted real observations and is evaluated on untouched tasks. | Reviewed export, completed bounded run, artifact verification, fresh reload, frozen evaluation and reported regressions/uncertainty. An unsuccessful experiment still yields evidence but does not satisfy improvement. |
| C: qualified personal default | A candidate meeting frozen quality/resource limits is activated through RRFlow and remains inspectable and reversible. | Engine artifact/configuration admission, authorized shadow comparison, promotion/readback, rollback trial and sustained workload measurements. |

A and B can progress independently where their actual prerequisites permit.
C depends on both. Completing A does not close the complete RRFlow 1.0 alpha,
public distribution, all model qualification or the smaller-memory objectives.

Initial scope is one operator, an explicitly connected project and configured
bindings, bounded development work, one shipped knowledge template, and manual
review/promotion. Multiple independent projects are needed for leakage-resistant
model evaluation. Subscription bindings require their actual supported execution
contract; a login is not an API key or an observed quota.

## Verified starting point and limits

SWAG source inspected: `8de17df2d19ae054cf93ab3d99b602400fc5a796`.
RRFlow local source inspected: `bf6dec69f1ca8c37d97dbd447af128ce33c390be`,
with a clean working tree. Neither identifies today's remote main or a deployed
binary. Remote PR states and installed compatibility must be refreshed in P00.
This was a targeted boundary review, not a whole-codebase review.

- This session ran 200 Python tests and 11 UI tests successfully, including the
  UI build. Browser acceptance, GPU training and installed task execution were
  not run for this plan.
- `DecisionService.decide` returns `engine_proposal_not_integrated`.
  `SemanticRouterAdapter` supplies offline proposals/local checks with no
  execution authority. See [the service](../tools/swag_decision_service.py) and
  [adapter](../tools/semantic_router_adapter.py).
- The connected developer-status probe reported engine and model endpoint
  unavailable from that connection, no configured admitted dataset, and no
  engine training launch. This is a point-in-time connection observation,
  not proof that every remote process is down or every dataset is absent.
- The registered historical intent run has 33 saved steps and provisional
  labels. Its [routing result](experiment-evidence.md#custom-endpoint-comparison)
  is 7/13 with five policy violations. It is retained as historical evidence.
- [Native capture](passive-capture.md#import-a-retained-native-attempt) preserves
  metadata but omits task text and verified model identity. The existing review
  UI and outcome admission cannot consume it directly. A selector and worker
  from one attempt are not two competing outcomes.
- [Training](training-evidence.md) supports admitted data, pinned revision/seed,
  bounded observations and cooperative stop handling. Full resume and the new
  stop path on GPU are unqualified; multi-process training is explicitly refused.
- [Knowledge previews](knowledge-template-adapter.md) validate source-bound
  answers and refresh affected inputs. They do not execute or verify fulfillment.
- In the inspected RRFlow source, `engine/flight.rs::launch_prompt_flight`
  documents the observe-only path; `engine/endpoint_worker.rs` produces a draft,
  not a project mutation. The current contract also states this explicitly.

## Architecture decision

**Decision:** use SWAG as a replaceable decision capability at RRFlow's existing
public boundary. Keep offline research usable while building governed runtime
training through RRFlow's generic activity machinery.

| Boundary | Owns | Extension rule |
| --- | --- | --- |
| SWAG | Decision adapters, knowledge/template interpretation, offline dataset and experiment tooling, evaluation/read models. | Add a versioned capability and conformance cases; no Python scheduler or canonical project state. |
| RRFlow | Source/read identity, configuration, authorization, aggregate budgets, provider dispatch, durable effects, artifacts and promotion receipts. | Extend existing contract/catalogue and engine owners; generate outward bindings from that owner. |
| Connectome | Project, decision, task, review, training and comparison views. | Consume the generated public client; no renderer credentials, direct trainer invocation or UI-owned completion. |
| RROFLOW | Authorized correlated outcome/diagnostic ingestion and review candidates. | Preserve retry/readback and retention/consent; capture grants neither correctness nor training permission. |
| LFG | Optional bounded advisory observations. | Treat absence, disagreement and timeout explicitly. Compare LFG/SWAG combinations before making them defaults. |

**Alternatives considered:** an independent SWAG orchestration service would
speed an isolated demo but duplicate authority and recovery; waiting for all
engine/UI learning features before any experiment would unnecessarily block
authorized offline research. A separate training database would fragment
lineage. Reuse immutable experiment files offline and engine-owned activation.

The trade-off is more explicit integration work up front, with fewer conflicting
states and a reusable path for additional models, templates and optimizations.
SWAG remains optional to RRFlow's default installation and readiness. A bundled
RRFlow adapter must be built from RRFlow-owned source; the separately versioned
SWAG service/artifact is an explicit optional binding, not a sibling-checkout
build dependency.

### Keep four contracts distinct

1. **Decision mode:** choice from supplied options, score against a named rubric,
   or binary proposition, each with abstention/unknown and evidence references.
2. **Endpoint selection:** choose an eligible binding and supported effort, with
   a separately validated handoff. Hard permissions and budgets remain engine checks.
3. **Reasoning action:** RRFlow's existing `RouteStepDecision` contains
   `SelectRecipe`, `AdvanceBranch` and `RequestContext`. These are not aliases for
   the three decision modes. Its model manifest is not a generic selector manifest.
4. **Execution/fulfillment:** an admitted action and verification establish the
   outcome; a score, binary answer or model draft cannot mark work complete.

P01 must map each required behavior to a real public consumer before changing a
schema. Planned semantic inputs include mode/objective, project intent, bounded
context references, relevant source/configuration/knowledge revisions, options
or rubric, and effective limits. Planned results include a bound answer or
abstention, evidence references, artifact/runtime identity and observed usage.
These are design requirements, not a new implemented wire schema. Keep unknown
confidence/cost/quota explicit; never translate missing evidence into zero or permission.

## One installed acceptance journey

Name the cross-package scenario `decision_router_alpha_journey`. Its executable
driver is to be selected/extended in P00 from the current public client and
installed-engine harness; this name does not imply a driver exists today.
Carry that driver and its last failing boundary through the dependent PRs.

1. Install/open an isolated engram for an owner-selected real development task.
   Record the task's success criteria, relevant source identity, installed
   engine/client/artifact revisions and authorized capability/budget configuration.
2. Bind `python_delivery_review` where applicable, or another explicitly selected
   template. Read the current project evidence; expose all three decision forms
   and unresolved requirements without inventing facts.
3. Submit a bounded proposal through the public engine operation. Show eligible
   options, selected binding/effort, evidence and handoff. An override is a new
   attributed decision, not a silent rewrite of the original.
4. Admit the selected worker and the exact project effect through their owning
   engine boundaries. Independently inspect changed artifacts and run the
   declared verification. A returned draft is an intermediate observation.
5. Change a relevant input before admission: reject the stale effect before
   writes and offer a current successor. An unrelated edit must not invalidate
   unrelated evidence or consume the project with repeated reassessments.
6. Exercise Stop, unavailable provider, lost reply and restart at declared crash
   gaps. Read retained outcomes; do not redispatch an uncertain external effect.
7. Deliver the authorized correlated observation, restart and read it back.
   Open the resulting review packet; preserve unknown/failed outcomes and consent.
8. Repeat using the candidate configuration after qualification, then perform
   rollback as a new authorized revision. Preserve the evidence for both runs.

Steps 1-7 establish milestone A using the explicitly configured supervised
baseline. Step 8 establishes milestone C after B and qualification; it does not
block the first supervised alpha or create a circular training dependency.

Passes require independently observed effects and public readback. Protocol
fixtures test engineering failure paths; they never enter training or acceptance
quality data. The first task and provider budget remain explicit kickoff inputs.

## Delivery packages and dependency order

Every row is planned unless the baseline above identifies an existing component.
Each row becomes one or more bounded PRs with an exact consumer, failure oracle,
source scope, evidence and next action. Existing overlapping work is reconciled
before adding implementation. Gate references name ownership, not blanket
permission to skip the owning repository's prerequisites.

| Package | Owner and implementation boundary | Depends on | Required exit |
| --- | --- | --- | --- |
| P00: reproduce the baseline | SWAG driver with RRFlow/Connectome owners; installed harness, current catalogue, configuration and evidence. | This plan. | Pin accepted/candidate/build identities and generated-client compatibility; identify the real task and exact failing journey call; inventory overlapping PRs and compute. No fictional endpoint or revived stale binary. |
| P01: bind decisions to runtime consumers | RRFlow G-01/G-02/G-03 and H-06/POAM-032; `rrd-contract`, `rrd-inference`, engine proposal/flight owners; SWAG decision and knowledge adapters. | P00 and actual gate prerequisites. | Mode/selector/action contract mapping, real admitted provider result consumed by the prompt/task journey, bounded evidence and invalid/stale/denied-output rejection. Generated clients agree. |
| P02: execute and verify the handoff | RRFlow D-06, I-03/I-07 and task/worker owners. | P01 plus admitted source/effect capabilities. | Exact authorized project effect and verification, source conflict before writes, Stop/uncertain-outcome reconciliation, restart without duplicate effects. Preserve aggregate spent budget. |
| P03: turn actual attempts into reviewed data | SWAG `swag_passive_capture.py`, `swag_task_outcomes.py`, schemas and review UI; RRFlow public evidence export; RROFLOW correlation. | P00 plus authentic retained attempts; new joined captures also depend on P02. | Review adapter joins source/task/candidate/output/verification evidence; independent review and consent; admitted splits with explicit withheld reasons. Missing model identity or comparison remains withheld. |
| P04: prepare and run the training pilot | SWAG training/artifact/observation tools; designated compute operator; offline G-06 experiment boundary. | P03 admitted data, verified compute and explicit bounded experiment authorization. | Pinned recipe, real optimizer observations, completed artifact, fresh reload and development comparison; GPU stop handling characterized in its own attempt. No dependence on finished Connectome controls. |
| P05: qualify decisions and optimize | SWAG outcome/mode evaluators and serving measurement tools; RRFlow G-06. | P04 and independent acceptance data. | Frozen quality/risk/resource profile, required comparison arms, mode coverage, uncertainty, raw serving samples and documented failures. No tuning on acceptance results. |
| P06: integrate training and promotion | RRFlow I-03/I-07, D-06 and G-06; generic activities, artifact/configuration admission; Connectome public client. | Generic activity/recovery prerequisites; P04 informs adapter behavior; P05 required before model promotion. | Durable job admission/progress/cancel/reconcile, verified outputs, CAS promotion and compatible rollback; double completion cannot activate twice. |
| P07: operate and extend the alpha | SWAG/Connectome diagnostics; RRFlow H-05/H-06 and distribution owners; RROFLOW. | A complete P01/P02 journey and qualified P05/P06 candidate. | Clean install, supported client compatibility, bounded trace retention, regression monitoring, recovery and repeatable upgrade/rollback. Public release remains separately gated. |

Execution order: begin P00, then pursue runtime P01/P02 and data/compute
P03/P04 as independent workstreams where ready. P03 can use genuine pre-existing
attempts; it must not manufacture evidence to avoid P02. P06's generic engine
prerequisites can advance alongside offline experiments. Join all paths at P05
qualification, P06 promotion and the installed journey. Review UI work accompanies
P03; public decision/task UI work accompanies P01/P02, rather than arriving last.

Split P03 into the native-to-outcome review/admission adapter first and
mode-specific supervision second. P04's first `task_success` pilot depends on
the first part only. Mode-specific training and claims wait for their own
admission/evaluator support. Design bounded diagnostics during P01; P07 qualifies
their sustained retention/export behavior before wider operation.

## Training plan and the role of 03

The owner's term **03 is unresolved**: it may mean spark-03 or the o3 model.
Use no compute allocation or teacher/provider assumption until clarified. If it
means o3, resolve the exact supported binding, permitted role and budget; model
outputs cannot replace independent real-outcome labels. The plan is otherwise
independent of that choice.

If it means spark-03, propose it as the dedicated bounded training host after
fresh verification. Keep the existing serving workload on its observed host
where capacity permits. Use another available host for independent evaluation
only after measuring its readiness. The three-node template is configuration
intent, not evidence of pooled memory, idle GPUs or distributed training support.

### T0: compute readiness

Read actual workload/process ownership, memory pressure, disk space, driver,
CUDA/container identity and model-cache availability. Verify selected base bytes
and run `swag_unsloth_train.py --preflight` inside the pinned intended runtime.
Record capacity, temperature/resource bounds and the restoration plan. Do not
stop an unrelated workload or silently download a moving dependency. Select
single-process training; qualify distributed training separately if later justified.

### T1: dataset readiness

Start with the supported `task_success` objective, and export `handoff_valid`
separately where its evidence exists. Native metadata needs an authorized join
to actual task text, eligible candidate snapshots, model revision, retained
outputs and verification. Preserve raw artifacts privately; no raw engine-store
reads or reconstructed claims of provenance.

For the paired outcome workflow, collect at least two eligible, comparable
attempts from equivalent initial states with separately bounded execution.
Record failures, cancellations, ties, review disagreements and unknowns. A
selection-plus-worker sequence is one option's attempt. An opaque hosted model
revision stays unknown unless independently supported; it may prevent admission
under the current strict schema and must not be guessed.

Before new collection, select project/time/leakage groups for train,
development and acceptance, with untouched acceptance projects/tasks. Existing
exposed PR-title cases stay outside acceptance. Choose pilot size from available
reviewed task families and budget; record counts per family and exclusions.
The pilot establishes training mechanics and development behavior, not a
statistically sufficient qualification sample. P05 requires a separately agreed
sample-size and uncertainty plan; no arbitrary row count proves readiness.

Choice/score/binary template judgments need their own reviewed supervision and
mode-specific evaluator. The existing binary outcome exporter cannot train or
qualify an ordinal rubric by relabeling it `task_success`. P03 defines those
objective schemas and P05 their scoring before claiming all-mode tuning.

### T2: first real training attempt

Freeze dataset and split digests, exact base/tokenizer revision and file inventory,
trainer/helper source, container/dependency versions, seed, objective, prompt,
sequence length, LoRA target modules/rank, optimizer, learning rate, step/epoch
ceiling, evaluation/save intervals, disk/memory/time ceilings and stop conditions.
Retain resolved configuration; do not silently inherit defaults as the recipe.
Use the existing BF16/LoRA path as the reproducible first candidate, subject to
measured capacity. No new training uses the provisional historical corpus.

An explicitly authorized offline experiment may execute the existing trainer
under RRFlow's G-06 research boundary while P06 is incomplete. Record it as an
offline experiment, never an engine-admitted job. A durable integrated launch
must wait for P06. Training intent does not grant consent for every source dataset.

First run a short bounded attempt on admitted train/development inputs to expose
OOM, invalid targets, missing gradients, nonfinite loss and artifact failures.
Then run the frozen pilot in a fresh output directory. Failures remain retained.
Never mount acceptance targets into the training process. Verify the produced
bytes, export using supported artifact semantics and reload in a fresh process.
Report development outcomes independently from loss reduction.

### T3: cancellation, recovery and iteration

Characterize cooperative stop/checkpoint on the actual GPU stack in a separate
authorized attempt. A killed or incomplete run stays incomplete. Implement and
test resume with exact dataset/runtime/optimizer/scheduler/RNG identities before
using it; the present trainer has no qualified full-resume interface.
Continue experiments only against development evidence, changing one declared
factor or a predeclared bounded sweep. Retain all seeds and failures. Do not run
an unattended tuning loop without an explicit aggregate budget and stop policy.

## Acceptance metrics and optimization order

P00 records the intended workload and P05 freezes numerical quality/latency/cost
limits before acceptance inference. Values are deliberately unset until baseline
measurements and owner trade-offs exist. Missing thresholds block qualification,
not compute preparation, data review or an authorized development pilot.

| Measure | Required interpretation |
| --- | --- |
| Boundary safety | Zero accepted unauthorized/ineligible effects, stale writes or duplicate effects in the declared suite; any violation fails promotion. Rejected invalid proposals remain visible. |
| Choice and routing | Task-success rate, handoff validity, per-family results, option-order sensitivity, unseen bindings and deterministic/simple-baseline comparison. |
| Score | Agreement with independent rubric judgments and ordinal error; do not treat a rubric score as calibrated probability. |
| Binary | False-positive/negative rates with abstention and coverage; unsupported yes/no answers count as failures under the frozen rubric. |
| Calibration | Brier score where probabilities are meaningful, selective risk versus coverage, development-only threshold/calibration fitting, held-out uncertainty. |
| Performance | End-to-end p50/p95, sample counts, queue/context/router/worker/verification timing, observed tokens and cost per successful task; unknown cost remains unknown. |
| Resources | Total serving scope with non-overlapping unified-memory accounting, workload/context/concurrency, training peaks separately, disk/trace growth and cancellation delay. |
| Reliability | All named edit/revocation/timeout/Stop/lost-ACK/restart cases, retained uncertain outcomes and exact readback. |

Compare deterministic selection and simple baselines first. The existing outcome
qualification requires original BF16, custom BF16, its exact quantized derivative
and an explicit small baseline under the frozen protocol. Use fresh reloads and
bind served bytes/runtime evidence; an endpoint alias is insufficient.

Optimization sequence: diagnose errors and context quality; improve knowledge
selection, prompts/handoffs and abstention; tune model weights; measure batching,
sequence length and cache behavior; then evaluate compression or a smaller model.
Maintain the 29 GB total-serving milestone and 15 GB / 9-12 GB research targets.
A smaller candidate can be investigated alongside compression, but no weight-file
size or idle memory figure satisfies a serving target. Profile the actual target
hardware before selecting kernels, pruning or residency mechanisms.

## Traceability, observability and enhancement

Extend the existing `swag.trace/v1` spans and engine causal evidence rather than
creating another authoritative event log. A trace must navigate from user task
through source/configuration/knowledge revisions, decision and engine attempt,
worker/effect verification, RROFLOW observation, review, dataset, experiment,
artifact and promotion. Unsupported joins are explicitly missing. Proposed new
correlation fields require versioned contract/allowlist updates and tests; the
current span writer does not already carry every identity in this chain.

Separate queue wait, context retrieval, decision inference, admission, worker,
verification and export timing. Retain failed and incomplete spans; overlapping
spans are not additive latency. Distinguish observed usage from estimates and
actual liveness from saved progress. Trace metadata excludes prompts, credentials,
private paths and hidden reasoning. Content-bearing review artifacts have separate
consent, redaction and access rules.

P07 defines byte/time retention, bounded export backlog, retry/backoff, disk-full
behavior and deletion policy. Trace loss must be visible and cannot rewrite a
durable receipt. Routine replay/readback is read-only; reinference is new work
requiring its own budget. Load tests measure the overhead of tracing itself.

Add models through descriptors/artifact admission and a shared conformance corpus;
add templates through revisioned practices, bindings and verification methods.
Preference changes, knowledge-pack updates, retrieval examples, policy changes
and weight changes remain separate revisions with separate evaluation. Cache keys
bind relevant source/configuration/knowledge/model inputs and invalidate only
dependent results; authorization is rechecked at effects.

Later assessment triggers may include relevant edits, explicit overrides and
verification failures. Admit them through RRFlow with deduplication, cooldowns,
call/token/time/concurrency limits and cancellation. A completion must not trigger
itself recursively. Drift and disagreement create review candidates, not automatic
correctness labels. Automatic promotion stays disabled until separately qualified.

## First execution handoff and unresolved decisions

The next implementation session starts P00 and prepares P03/T0 in parallel where
independent; this describes workstreams, not authorization to start remote jobs.

1. Refresh actual RRFlow/Connectome source, PR overlap and installed operation
   support. Retain the current journey failure and designate its production consumer.
2. Confirm what 03 denotes. If a host, perform read-only capacity checks, then
   prepare the exact bounded preflight. If a model, inspect supported access and role.
3. Inventory genuine retained attempts and produce a gap report: missing task,
   candidate/revision, comparable output, verification, reviewer or consent evidence.
   Implement the smallest review adapter against those real artifacts; ask only
   for the missing human decisions, not hand-authored JSONL.
4. Select a real task and verification criterion from the owner's active work.
   Agree the candidate set and aggregate comparison/training budget before calls.
5. Prepare the pilot recipe and admit the reviewed export. Run T2 as soon as its
   actual prerequisites and authorization are satisfied, independently of P06 UI readiness.

Open owner inputs: 03 identity; selected real task/project set and success criteria;
eligible provider/compute budgets; reviewer assignment and explicit dataset use;
quality/coverage/latency trade-offs. These block only dependent execution or claims.
No training has been started or permission/labels fabricated by preparing this plan.

Do not assign an ETA before P00 exposes current dependency state. Estimate each
ready bounded package from its inspected diff, acceptance work and compute/data
availability. Progress is the next passing journey boundary and new measured
training/evaluation evidence, not PR count, GPU utilization or document volume.

| Delivery risk | Response and owner |
| --- | --- |
| Existing branches overlap or installed APIs differ | P00 inventories current source/build/catalogue; the relevant RRFlow owner reconciles dependencies before client work. |
| Too few comparable reviewed outcomes | P03 reports exclusions and schedules bounded real comparisons; reduce the experiment's claim rather than generate labels. |
| Training host is occupied, unavailable or out of memory | T0 measures capacity; the compute operator selects an authorized alternative or smaller bounded recipe without interrupting unrelated work. |
| A model succeeds in format but fails decisions | P05 uses outcome/mode metrics and per-family regressions; retain the baseline and withhold promotion. |
| Repeated tuning exposes the holdout | P05 retires that acceptance set from unseen claims and obtains fresh project/time groups before the next qualification. |
| Interrupted work has an unknown external outcome | P02/P06 reconcile the original attempt through its engine owner; never infer failure and retry automatically. |

## Owner references and validation

RRFlow references below are pinned to the inspected revision; refresh them before
implementation instead of copying their old checkboxes into SWAG status:

- [Alpha objectives](https://github.com/rrflow/rrflow-development/blob/bf6dec69f1ca8c37d97dbd447af128ce33c390be/docs/objectives/rrflow-1.0-alpha.md),
  [Gate G](https://github.com/rrflow/rrflow-development/blob/bf6dec69f1ca8c37d97dbd447af128ce33c390be/docs/roadmap/rrflow-1.0/gate-g.md),
  [Gate I](https://github.com/rrflow/rrflow-development/blob/bf6dec69f1ca8c37d97dbd447af128ce33c390be/docs/roadmap/rrflow-1.0/gate-i.md).
- [Controller training contract](https://github.com/rrflow/rrflow-development/blob/bf6dec69f1ca8c37d97dbd447af128ce33c390be/docs/reference/inference/learning/controller-training.md)
  and [change-authoring procedure](https://github.com/rrflow/rrflow-development/blob/bf6dec69f1ca8c37d97dbd447af128ce33c390be/docs/roadmap/rrflow-1.0-execution/change-authoring.md).
- SWAG [task-outcome workflow](task-outcome-workflow.md),
  [training controls](training-control-plan.md),
  [decision modes](decision-modes-and-knowledge-mesh.md),
  [developer workspace](developer-workspace.md), and
  [serving measurements](serving-load-measurements.md).

Implementation validation begins with a reproduced failure, then affected tests,
the owning suite and actual installed/GPU evidence appropriate to that package.
Candidate/merge checks qualify their exact revision. Preserve raw failures and
state checks not run. Public documentation contains only sanitized summaries;
private source material, access configuration and session logs remain ignored.

For this documentation package, run the public-boundary tests, verify relative
links and review the diff. It changes planning/navigation only; no engine gate,
runtime feature, model qualification or release status changes.
