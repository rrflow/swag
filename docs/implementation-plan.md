# SWAG implementation plan

Owner direction: 2026-10-29. Goal: a usable System One controller that completes
real development work through RRFlow, learns from reviewed outcomes, and can
ship locally and as a scale-out image. This is SWAG's work plan; RRFlow's existing
roadmap owns engine dependency order and gate completion.

## Required constraints

- Use real tasks, source revisions, provider attempts and observed outcomes.
  Never invent tasks, labels, consent, capabilities, usage, confidence or results.
  Unknown evidence remains unknown and blocks only its dependent claim.
- No new training on synthetic cases or assistant-inferred targets. Preserve the
  earlier provisional checkpoint and synthetic scores as historical experiments;
  they are not approved training data or qualification.
- No task-specific routing branches, embedded provider rankings, fixed model names,
  credentials, host paths or endpoint URLs in product behavior. Resolve supported
  bindings, policies, effort, limits and identities from revisioned engine-owned
  configuration. Missing configuration is visibly unavailable, never fabricated.
- RRFlow owns accepted plans, authorization, budgets, durable effects and receipts.
  SWAG proposes; Connectome projects public engine state; RROFLOW receives authorized
  correlated signals. No parallel Python or UI lifecycle authority.
- One bounded package per PR, required checks and protected landing. Preserve
  failures. Local scripts, configurations and dev binaries do not prove distribution.

## Developer-build execution, 1 November

Deliver one matched developer bundle before public distribution. RRFlow remains
the execution authority; this plan coordinates integration and cannot close its
roadmap gates. The longer-term real-task, reviewed-learning, model-comparison,
native/container and measured-memory goals remain in scope.

| Order | Work | Required exit evidence |
|---|---|---|
| 1 | Reconcile sender PR235 with accepted RRFlow main, regenerate the canonical public projections, validate and land through protected CI. | No unresolved conflicts, retained behavior from both parents, exact candidate and merge receipts. The old 23-pass run qualifies only `ebeecabb`. |
| 2 | Integrate worker PR229, recovery PR230, discovery PR231 and Connectome PR30 in dependency order. Resolve the worker publication hold before its rejected actions. | Required checks on each final head, accepted source, regenerated SDK parity and no client-owned execution state. |
| 3 | Assemble one versioned native developer bundle from accepted engine/UI source using the landed packaging tooling. Configure the BF16 endpoint and credentials explicitly. | Build/manifest/checksum verification, clean-start instructions, authenticated readiness, actual routing/handoff and restart readback. Model weights and serving memory are reported separately. |
| 4 | Implement the missing governed project-effect path under D-06/I-03/I-07, then exercise the owner's real task through the same public engine/UI operations. | Exact approved change matches independent artifact inspection; ordinary edits require scoped replanning; recovery avoids duplicate effects; RROFLOW retains correlated outcomes. Draft text alone cannot pass. |
| 5 | Admit independently reviewed real outcomes; compare original Qwen, custom BF16 and its quantized derivative under one frozen protocol. | Explicit data permission, held-out evidence, artifact lineage, measured serving footprint and no automatic promotion from model-generated labels. |
| 6 | Qualify container delivery and public release. | Reproducible image/binary provenance, clean installation, upgrades/rollback, credential isolation and the complete user workflow. |

Current action: PR235 publishes ordinary merge `b856a8fb`, incorporating accepted
main `daec1f1a` and resolving the 19 OpenAPI/projection conflicts. Local validation
passes; [candidate 41342695388](https://github.com/rrflow/rrflow-development/actions/runs/41342695388)
completed with all 23 jobs successful. Protected acceptance remains pending.
The linked journal
records 165 contract/adapter passes, 499 reported owning-suite passes, four
ignored cases and one SDK entry lacking its live-daemon manifest, plus build,
lint, TypeScript and repository checks. PR190/232 and packaging PR212 have landed.
The owner selected [`rrflow/swag`](https://github.com/rrflow/swag), an empty private
repository, for SWAG delivery. `origin` is configured to that repository;
Git history starts at `3a5b337`. The owner is also asked for a real task and acceptance criteria;
that answer grants no training permission. The latest local checkout check
passed 97 Python tests and six TypeScript viewer tests.

Next integration risk: a read-only preview of sender `b856a8fb` with published
worker `52e2254a` lists 29 conflicted paths, including engine invocation,
endpoint policy, transport contracts and generated projections. The preview
warns that its path list may be incomplete. It changes no source or refs and
does not clear the worker publication hold. Resolve that bounded integration
under its own brief and tests; do not describe the complete stack as conflict-free.

## Earlier execution, 31 October

Latest receiver package: RROFLOW PR43 merged as `d552e8ab`, from `b4c04cee`, with typed
engine-observation references in its existing immutable capture API. Local
workspace tests (136, PostgreSQL configured), lint, format and 46 dashboard/
release checks pass; CI `41255031094` now passes all six jobs. The release-plan
builds also pass, without publication. Complete the engine-owned
authorization/export/durable-retry path
and prove one real correlated outcome. The receiver neither attests engine
identity nor creates a successful task or approved training record. Existing
observation-source configuration alone does not activate an exporter.

Sender [PR235](https://github.com/rrflow/rrflow-development/pull/235) now publishes
implementation and CI/test corrections at `ebeecabb9815a891611f312c99bfa0afe5afee9e`.
It is ready for review, with the full
[candidate pipeline](https://github.com/rrflow/rrflow-development/actions/runs/41263686147)
complete with all 23 jobs successful. PR235 is queued for protected acceptance
(position 3 observed on 1 November, 02:52 UTC), not yet merged.
The queue now reports generated catalogue/SDK conflicts with its preceding
entries. Their protected runs are live; reconcile actual landed source and
regenerate projections before qualifying a successor. Preserve the successful
`ebeecabb` run under its original identity. The previous run
exposed missing adapter CI coverage, stale generated
storage-test digests and recovery-test timestamp assumptions. Those failures are
retained and corrected; affected local policy, engine and evaluator checks pass.
The installed sender/receiver trial proves metadata transport and restart/replay
persistence on exact recorded debug binaries. It does not prove a completed
project task, training approval or public release. The
[current context](current-context.md) and
[deployment readiness](deployment-readiness.md) retain exact proof and limits.

Next land the sender only after its required candidate and protected checks.
The worker/resume/discovery and UI dependencies still need accepted source before
the complete private-alpha trial. Their acceptance is not sufficient: worker
PR229 at `52e2254a` returns draft text, with no project-file permission or
task-success claim. Implement the governed project-effect path under RRFlow's
existing D-06/I-03/I-07 owners before treating real-task completion as a test-only
gap. Bind exact effect previews and source/configuration/authorization, preserve
uncertainty across crashes, and expose the behavior through engine-owned public
operations. No external patch runner or UI executor may supply missing authority.
The [execution gate](deployment-readiness.md#project-execution-is-an-implementation-gate)
records the inspected contract and acceptance boundary.
Keep that milestone focused on one real task,
its observable project effects, ordinary-edit recovery and the matching RROFLOW
record. SWAG's own delivery repository is still unspecified; a repository URL
or a name for a new private repository has been requested. Do not initialize this
checkout or publish its local configuration/data to a guessed destination.

Latest correction: PR222 has landed at `6c069e14` with successful protected
checks. Reconcile its exact landing into PR229 before advancing that package.
Connectome PR30 now contains the bounded plan panel at `1f2e2a5c`, with a clean
matching desktop build. Complete its interrupted source-edit desktop trial;
component checks already pass but do not replace UI acceptance. Then prove an
authorized real project task and correlated outcome before adding more release
claims. [Deployment readiness](deployment-readiness.md) lists the outstanding
model, integration and native/container distribution gates. The older pending
PR222 and not-yet-implemented UI statements below are historical.

PR231 publishes installed-job discovery at `8d475008`. It adds bounded public
engine/HTTP/native/SDK discovery over the existing installed lineage; stored
source digests are explicitly not a current-source verification. Local engine
and transport suites, focused discovery/replan/reopen checks, SDK parity,
TypeScript, strict lint, formatting and repository checks pass with retained
corrections. Keep the candidate draft behind PR222/229/230. Its exact-source
native executable is now frozen with a verified canonical build receipt at
`.swag/evidence/20261031/attunement-job-discovery/engine-frozen.json`; it is an
unsigned, unoptimized engineering candidate without installed discovery proof.
Next pin this SDK in a bounded Connectome package,
display engine-owned plans and discover/preview/approve ordinary-edit successors
through public operations, then prove the path on the matching primary binary.
Do not treat this prerequisite as a complete project, learning or release flow.

PR206 has landed at `5b4039fe` with successful protected run `41239406940`.
Connectome recovery implementation `0f75c015` and evidence head `59526643`
now prove actual desktop Stop/resume, an explicitly requested BF16 worker draft,
and exact task/attempt/budget readback across reload. Final effort was two steps
and 22,528 ms under the original deadline. Forty-four observations preserve
source/build identities and corrections. PR29 remains draft; candidate run
`41244693013` passed all six jobs. This is a Windows preview, not a qualified release.

PR222 has now reconciled actual landed main without runtime changes, passed
repository checks and become ready at `25f72255`. Full candidate run
`41245163469` passed all 23 jobs. Protected merge-group run `41248811413` is
active at `6c069e14`; PR222 is not yet merged. PR229 is
prepared against that native candidate at `cb42e8a9`; its runtime/test/receipt
bytes are unchanged and repository checks pass. It remains draft until the
native dependency actually lands. Observe the existing run without replacing
it, reconcile the exact landing into PR229 and run its own required pipeline.
Then advance the recovery and UI dependencies through their required checks.
Recovery PR230 is now prepared at `98996a10` against worker `cb42e8a9`, with
unchanged runtime/test/receipt bytes and passing repository checks. Keep it
draft until its actual dependency landing and final pipeline acceptance.
Follow with the full real-task
journey: ordinary-edit successor planning, authorized project effects, correlated
RROFLOW outcomes and independent outcome review. Release acceptance requires
clean-install and upgrade/rollback evidence for native and container artifacts.
Model acceptance requires reviewed held-out comparisons of original Qwen,
custom BF16 and the same custom checkpoint after quantization, with measured
serving memory. No 29 GB, automatic-learning or public-readiness claim is made.
The [current custom artifact audit](checkpoint-binding-20261031.md) verified
61.07 GB of BF16 weight files and 30.53 billion stored elements. Plain 9-bit
payload would be 34.35 GB before runtime/cache; it cannot by itself meet the
29 GB total-serving target. Choose compression only after reviewed quality
acceptance, then measure the complete serving footprint.
The historical pending statuses below are superseded only by these verified
merge and bounded desktop-recovery observations.

Installed same-task recovery is now evidenced at PR230 head `67c197ea` using
clean harness `ce20dc79` and the frozen `6a4cbb04` executable. Four actual model
calls demonstrate rejection, explicit resume under the original budget, fresh
selection and accepted worker draft. Independent credential-free recovery matches
all four attempts and final effort; 37 published receipts retain exact bytes.
Original deadline and spent effort remain intact. The 14 harness tests and
repository/publication checks pass. No task completion, project effects, quality
label or training record follows. Next compose resume into Connectome with the
matching engine build, prove ordinary-edit/project-effect/RROFLOW flow and land
dependencies through protected CI. PR206's protected run remains live; existing
Connectome and ZIP binaries are unchanged. Earlier pending same-task trial notes
below are superseded only by this narrow installed recovery result.

PR227 has now landed at `df26b355` after successful protected CI. PR206 includes
that exact destination through tree-identical ordinary merge `dd20b7b8` and is
published at `9371f856`. Source equals tested `9e167aad` outside documentation;
repository checks pass. PR206 candidate run `41235940488` passed all 23 jobs.
Protected merge-group run `41239406940` is active at `5b4039fe`; observe it without
restarting or bypassing required checks. PR222 follows verified PR206 landing.

PR230 at `6a4cbb04` now implements public explicit budget resume under the
existing engine authority. Known-completed cancelled/failed tasks retain their
original spent effort/deadline, repetition history and prior attempts; unknown
or active work remains denied. Engine, authenticated HTTP/native, contract,
server, generated-SDK and repository checks pass with preserved failures and
corrections. The PR stays draft behind PR206/222/229. Its clean-source binary is
now frozen with an accepted build receipt. Next prove actual same-task BF16
recovery and new authorized work, then
compose its exact SDK/engine with Connectome. This does not implement unknown
lease reconciliation, extend budgets or establish model quality.

Connectome PR28 evidence head `91b89ae4` passed all six jobs in `41235205588`.
Its preceding JSON-formatting failure is retained; the correction preserves
JSON values, original capture hashes and the frozen `95a81077`/`e3528330`
desktop artifacts. No actual trial was replaced.

Worker PR229 evidence head `d5151eef` includes completion repair `75c26a80`: a
completed-but-rejected response no longer retains unknown capacity. Its task
budget remains stopped and charged; lost outcomes retain uncertainty. The
reproduced engine failure now passes, as do 362 engine tests (four existing
ignored), 42 inference tests, strict lint, formatting and repository checks.
The exact clean source is frozen; its actual installed BF16 baseline, terminal
rejection/capacity proof and independent recovery pass. Clean harness `69250d34`
observed the real length-terminated reply, denied original replay, and admitted
a separate real task through the same one-call binding after reopen. Exactly
three provider calls occurred; the original stopped budget remains unchanged.
PR230 supplies the separate public resume implementation described above;
its installed proof remains open. Unknown-outcome reconciliation remains
separate work; historical uncertain leases must remain untouched.

Earlier worker evidence `e1b5ea46` publishes four actual completion-fault histories
(configuration revision, session closure, Stop and lost delivery), each with
independent credential-free recovery. Seven harness tests, repository checks
and 64 receipt hashes pass. Each history used two real provider calls; recovery
did not redispatch. Stop and lost delivery still retain uncertain capacity.
Implement typed engine-owned reconciliation before claiming usable resume;
never clear leases from external observations or reset effort/deadlines.
Then prove ordinary-edit UI replanning, governed project effects and correlated
RROFLOW outcomes. Reviewed learning and deployment/model qualification stay open.

### Earlier dependency and validation snapshots

The following records preserve their original source identities. Their pending
PR/CI statements are superseded by the current execution status above.

Startup prerequisite PR227 now includes landed main and is ready at `974c9d65`.
Composed local engine/lifecycle/lint checks pass; full candidate run
`41227938401` passed all 23 jobs. Protected merge-group run `41231635508` is
live; landing remains unproven. PR206 is prepared at `780c1fba` by ordinary,
documentation-only reconciliation with that candidate. After PR227 actually
lands, reconcile PR206 with the landed destination and mark it ready for its
own full candidate pipeline. Preserve required protected qualification; no
dependency closes merely because its source was composed. The next action is
to inspect the running PR227 jobs, handle any exact failure, and proceed through
the normal merge controls when all required checks pass. Normal auto-merge is
enabled for exact PR227 head `974c9d65`; no bypass or landing claim applies.

Native-client PR222 is also prepared at `14ee2557`, with ordinary dependency
merge `f957e06d` and fresh passing client/contract, lint, architecture, surface
and repository checks. Keep it draft until PR206 actually lands, then reconcile
and mark ready for its own complete candidate pipeline. The Connectome pin,
worker package and testing bundle did not change through that reconciliation.

Connectome PR28 implements the selected-worker review/request/readback UI at
`95a81077`, with all SDK pins at worker candidate `e3528330`. Its exact frozen
desktop passed the actual BF16 selector/worker/reload trial. Independent engine
reads match task, budget and both attempts exactly; two steps remain charged.
The real verification task stays open and the draft is not a correctness label.
All six candidate CI jobs passed at that implementation. Evidence-only head
`386fdcdb` publishes screenshots/readbacks and has separate live CI `41234351899`.
Keep the UI draft through dependency landing and remaining qualification. Next
complete worker policy/credential acceptance and safe explicit reconciliation;
then prove ordinary-edit replanning, project effects and correlated RROFLOW
outcomes. The native preview remains unsigned with operator-managed endpoint setup.

PR229 is published at `e3528330`, including clean harness `2f7a1a34` and actual
installed worker interruption evidence. Exactly two BF16 calls occurred; the
engine was killed after the worker response arrived at the relay but before
acceptance. Reopen and separate credential-free recovery retained the same
reserved worker, selector, budget and unchanged task without redispatch. Four
relay tests, compilation/workflow/repository checks and 14 captured receipt
hashes pass. This qualifies that fault case only, not safe reconciliation or
resume. The engine remains the frozen `c75c1896` binary. Remaining installed
policy/credential cases and usable recovery remain open. Prior prerequisite
reconciliation `44a85ef0` remains included.
Do not clear retained uncertainty or reset effort/deadlines. Local acceptance
and dependency landing precede readiness; the ready transition starts candidate
CI, and candidate/protected checks gate landing.

Prior evidence `a3068cf` includes native-client composition `43d18059`,
installed native receipts and landed main `906bec82`. Its `c75c1896` engine implements the worker operation on the
existing engine attempt/budget/capacity owners. Seven focused protocol/engine
tests pass, including changed-input recovery, Stop, lost response, reopen and
context readback authorization. Broader local tests, strict lint, architecture
checks and generated SDK/API checks passed. The exact provenance-bound engine
binary completed a real configured selection/worker draft, missing-credential
denial, restart/readback and replay rejection. A separate recovery read both
attempts without provider credentials. The first invalid model-choice trial and
its uncertain estate remain retained; a second isolated trial with explicit
schema instructions passed. No routing-quality or training claim follows.
Draft text remains separate from governed project effects.

PR229 is MERGEABLE but remains draft; a skipped pipeline is not acceptance.
The initial debug artifact's missing provenance was corrected using the canonical
builder, preserving both artifacts. PR222's native-client surface is now composed
and its installed selector/worker path passed with separately identified client
and engine builds. The first rejected native worker response and its uncertain
state remain retained; only a second isolated, explicitly shorter-response trial
passed. The 189 contract/client tests, strict lint, architecture and surface
checks also passed. No model-quality or complete UI claim follows.

Next reconcile and qualify the prerequisite PR chain through required candidate
CI and normal protected landing; ordinary source composition does not close those
PRs. Complete remaining worker fault/reconciliation acceptance, connect the typed
worker path to Connectome, and rebuild the testing bundle from the exact composed
source. Then prove project effects and correlated RROFLOW outcomes before claiming
the full user journey. Qualify native/container artifacts before distribution.

PR228 landed as `c2a43120375ae9d9d318d48533a42dc05ebe36da` after protected
run `41216269606` passed. PR224 landed as
`906bec82c605ed095a2dbf9b0217cd89bd41c05f` after protected run `41216747041`
passed. Both protected runs passed all 23 jobs. Reconcile dependency source through ordinary merges after verified
landing, then qualify the exact composed build. Continue with the real UI/worker/
project-effect/RROFLOW journey and independently reviewed data. Historical
execution sections below do not override this current order.

## Verified starting point

PR196 merged as `6bcb136cb94749b581d927c5e05b858874ac8b43`; PR205's foundation
merged as `47d979b1624a65c342d42a373d3c116534b56482` after protected checks passed.
PR179/180 are also merged. PR188 merged as
`2e6ab88ed08340b61513b2b6c3828b202369c49d` after candidate `40948411087` and
protected merge-group `40957233182` passed.
Collector/review source is unchanged. No blanket merge-completion claim applies.

Actual Unsloth BF16 training and endpoint reload exist; weights occupy about
61.07 GB. The 44 training titles had assistant-inferred labels. Intent development
scored 15/21 versus base 14/21. This is not provider-routing qualification. The
synthetic routing experiment failed. No independently reviewed provider-outcome
dataset is admitted.

Endpoint configuration persistence, local signal ingest/readback and a TypeScript
viewer were exercised. PR206 implements experimental controller admission and
credential resolution; its later installed dispatch succeeded after access
restoration, with actual restart/replay and controlled fault evidence. Connected UI, worker execution and governed learning remain open. See [experiment evidence](experiment-evidence.md).

## Connected workspace progress, 2026-10-30

Draft [Connectome PR26](https://github.com/rrflow/connectome-development/pull/26)
implements native task, budget, reviewed proposal inputs, one-shot dispatch,
readback and Stop on PR222's contracts. Its actual desktop maintenance trial
passed installation, task/budget creation, reload and cancellation. A subsequent
live desktop trial accepted one configured BF16 proposal and recovered identical
attempt/budget state after reload. Local native and frontend validation passed.
This advances package 5; protected dependency landing, worker effects, ordinary-edit successor plans,
correlated signals and independently reviewed outcomes remain required.

Public main's PR218/208 now supplies versioned attunement plans and bounded
source-replan operations. PR206 incorporates them at `71d53e1e`, with 29 merge
conflicts resolved and local contract/engine/SDK checks passing. Dependent
PR222 now incorporates that revision at `c376e271`, consolidating the Rust client
generation with 182 client/contract tests and repository checks passing. Connectome
now consumes that revision at `a3d179dc`, with a new Windows preview, regenerated
engine-value fixture, 39 ordinary native tests, 15 actual process cases and full
frontend checks passing. Draft evidence head `ed6ed0e5` passed its own CI; no new
desktop interaction or BF16 observation is attributed to the refreshed pair.
PR212 incorporates the same dependency at `8cf235ac`. Its canonical release build
and new 33,976,833-byte Windows archive completed; all 18 archive checks passed.
The extracted primary installed, served, reopened and passed 13 quick checks
after each owned process stop, using only System32 on PATH. This is same-host
packaging evidence, without model/worker execution or clean-machine qualification.
Only Connect executes in that attunement
implementation; this does not satisfy per-prompt worker handoff or recovery of
arbitrary effects. Required dependency landing and final candidate checks remain
open; the original protected failures remain in their evidence records.

Exact Connectome head `ed6ed0e5` subsequently passed complete CI run 41127990158,
including Windows/macOS/Linux and actual-engine process integration. It remains
draft behind its unmerged engine dependencies.

## First user-visible milestone

The next worker package is draft [PR229](https://github.com/rrflow/rrflow-development/pull/229),
based on exact PR206 dependency `952e0928`. Published increment `cea6c846`
provides shared model-text transport and explicitly configured worker policy.
Focused protocol/contract and real engine preview/apply/reopen checks pass.
Affected contract/inference/client
checks pass 216 tests; engine-library checks pass 291 with four existing ignored;
strict lint, 32 architecture checks, generated SDK parity, TypeScript checks and
repository metadata checks pass. Continue with accepted-choice/task/context
admission, existing budget/capacity reservation, guarded completion/readback and
the generated public operation. These prerequisites are not worker execution or
an end-to-end user result; keep the package draft until its entire brief is met.

The next setup increment is Connectome PR27: per-project optional engine credential
mapping selection, engine-owned validation, explicit stop/start for startup changes,
and clearing selection when changing projects. Implementation `6de73eec` passed
complete CI and actual desktop install/serve/stop/reopen using an empty mapping.
This removes the need for an externally launched engine to pass a mapping, while
environment provisioning and endpoint-profile admission remain separate. It made
no model call and does not complete the worker handoff. Receipts and screenshots
are on evidence head `7a37a6a7`, whose CI failed on raw-report JSON formatting.
Correction `f8139cc7` preserves report bytes in gzip and formats the manifest;
full local checks and all 16 evidence hashes pass. CI 41136356561 passed all jobs at that exact head; dependency landing remains
required. PR27 is still draft and unmerged.

Current candidate: PR224 publishes documentation-only head `ffe3af9f` and is ready
for review. Both full runs `41161519177` and `41165175925` passed all 23 jobs at
implementation/test head `168e93c6`, but queue admission still reported the
required gate expected. The evidence-only head has a normal ready-PR run,
`41206082118`; all 23 jobs now pass. Normal protected queue admission succeeded
and PR224 entered the protected queue. Merge-group `41210074230` subsequently
reported a macOS compiler panic during release-engine metadata decoding, before
the reopen test executed. No build cache was restored; the cause is unproven.
Raw job `124563021519` output and the first completed result are retained: 21
jobs succeeded; macOS compilation and the dependent final gate failed. A targeted
failed-job retry completed successfully: attempt two of `41210074230` passed
all 23 jobs. PR224's exact head was re-admitted to the normal protected queue
and observed at position two, awaiting checks. No checks were bypassed and
no merge is established. Prior run `41160199235` failed Linux
engine-authority job `124415867194` in `replan_refuses_an_unreconciled_failure`.
All four fixtures with the same 20 ms post-Inventory assumption now derive
dependent times from returned completions. Runtime enforcement and assertions
are unchanged. Local focused/module/all-feature checks pass, including 339
engine tests; strict lint and repository checks pass. The corrected candidate
and protected checks must still qualify this exact revision. No merge is
implied. Normal merge `6b2b2c20` carries exact PR221 `f6185c2c`.
Its protected run failed a receipt test's fixed-time assumption; the candidate
now follows returned completion times and preserves runtime enforcement. A fresh
isolated build passes 276 library, seven installed CLI and two real SDK tests.
Final all-target/all-feature checks pass 339 tests (four existing ignored), and
strict lint/repository checks pass. No dependency or candidate merge is implied.
See the [integration record](https://github.com/rrflow/rrflow-development/blob/61bfe5a60f8c5385cbff856b40540f48704e8959/docs/evidence/change-journals/gate-d/d-03-candidate-integration-clock.md).

Draft PR226 starts the next bounded D-03 publication package from `168e93c6`:
reuse equal entries/edges from current authenticated records, and bind partial
progress to the exact publication work set. An installed repeated-Inventory
regression first failed at 14 mutations instead of three. Local implementation
now passes the reuse/current-record cases, interruption/reopen tests and the
revised 341-test full engine suite. Strict lint passed. The real-repository binary
trial first hit an unresolved startup binding rejection, then continued on the
preserved estate: 4,279 initial mutations, 3 unchanged, 6 after README edit/replan,
3 unchanged again, exact reopen and offline verification. Native startup
qualification remains open; evidence head is `f1a033b7`. An earlier Connect deadline failure is
retained; its cause is not established and limits were not increased. The code
is published at `923326ab`; keep this dependency draft through remaining qualification.
Full source reads remain mandatory; this does not establish zero-content-read
freshness or worker execution.

PR227 at `39a7b644` separates valid installed-engine startup from its unused full
source-inspection report. A retained failing regression now passes startup/job
readback with invalid project input while dependent Start still denies; repaired
input starts, real inspection evidence remains intact and bootstrap tampering
still denies. All 342 engine tests and strict lint pass. The exact-source primary
now passes the combined installed trial: startup/readback with invalid Git input,
denied Start with unchanged job, repair and normal admission, then real
Inventory/restart/edit/replan/repeat with 4,279/3/6/3 mutations. Seven installed CLI
lifecycle cases pass. Offline quick verification passes its 13 checks while
explicitly reporting divergence from the original installed source precondition;
the scheduled Verify phase did not execute. The invalid-input error remains HTTP
500/internal. These are Windows engineering-binary correctness observations,
not release, upgrade or performance qualification. Complete candidate/protected
checks for the composed source, with PR224 as the landing predecessor. This avoids
a circular startup gate; close no retained dependency until its actual main
destination and behavior are verified. Full worker execution remains the next
product integration requirement, not a claim established by these source checks.
PR227's installed evidence is published at `27e87749`; its implementation and
copied executable remain bound to `39a7b644`. No candidate or protected acceptance
is inferred from that documentation-only publication.

PR206 now composes that source in draft `c5bd4d99`. All three conflicts are resolved;
27 task-budget and 34 attunement tests pass. The full engine suite exposed Windows
object-publication Access is denied during concurrent quantization build. Preserve
that failure; a focused pass does not clear it. PR228 publishes the persistence
repair at `a40a4f8c`, after both original regressions failed. Windows owner checks
pass 257 storage tests, six filesystem tests and strict lint. Candidate CI
`41212170341` passed all 23 jobs. Exact head `a40a4f8c` entered the normal merge
queue at position one; protected run `41216269606` is in progress. A pre-edit
PR206 brief now binds ordinary integration of
that exact source; its one POAM conflict retains both failure and repair records,
and native source-observation exports remain intact. Resolved tree `82065cd6`
passes the original concurrency case, all 353 engine tests (four existing ignored)
and 208 contract/inference/client tests. Strict lint, seven installed CLI cases,
planner identity and repository checks pass. Ordinary merge `9e167aad` now has
a clean-source 153,362,944-byte engineering primary, SHA-256 `f0f35eac...779ad4f92`;
both installed Python SDK edit/replan cases pass against its copied executable.
Evidence head `952e0928` is published in draft PR206. No public-main landing,
new live model call, repeat of the full 1,870-path corpus, release or upgrade
qualification is inferred. Complete required dependency/native checks. The actual worker handoff remains the next
product capability; this is a discovered prerequisite, not a replacement goal.

Earlier D-03 increment: PR224 published `63265630`. The actual 1,870-path
repository exposed the earlier one-batch Inventory limit. Bounded observation
groups now retain private engine progress; only the final atomic transaction
publishes a complete snapshot/head/checkpoint/receipt. Installed interruption
resumes without duplicate groups; an edit during publication rejects completion
and allows an accepted successor. The real copied primary completed Inventory,
restart, ordinary-edit replan, second Inventory, another restart and quick verify
on a separate same-revision installation. Final checks: 276 engine tests (four
existing ignored), seven installed CLI tests and strict repository/lint checks.
The rebuilt binary cannot open the old sealed executable binding: safe upgrade
remains required. Final manifest/retirement bounds, retention, native race/reuse
and candidate qualification are still open. See the
[latest journal](https://github.com/rrflow/rrflow-development/blob/63265630d3ab3ec9095e55145c4875717e3f79e8/docs/evidence/change-journals/gate-d/d-03-bounded-inventory-publication.md).

Earlier smaller-project evidence follows; its single-batch implementation is
superseded by the bounded publication above.

Before worker execution, finish the engine dependency spine's D-03 source
inventory qualification. PR223's pure proposal component merged as `f256c8e1`
after protected run 41144688431 passed. Draft PR224 now publishes `2cfc0bd9`:
its installed Git/native traversal supplies a pure proposal, and one engine
transaction commits canonical source records/change set, receipt, authenticated
head and exact checkpoint. No client-side lifecycle or inventory database is added.

Installed engine evidence covers replay, restart, edits/additions/deletions/renames,
stale-plan rejection, accepted successors and source-record retirements. The
relocated primary executes Inventory through its generated Rust client, survives
forced termination, reopens the exact checkpoint and executes Inventory under an
ordinary-edit successor. Configured output-limit rejection and stale source leave
runtime/job/head unchanged. Tests: 273 engine (four existing ignored), 36 component,
11 native filesystem, seven installed CLI, additional copied-primary trial, two
Python SDK and 32 architecture; strict lint/format and repository checks passed.
See the [immutable package journal](https://github.com/rrflow/rrflow-development/blob/2cfc0bd9f71845ceb45fb0c0d6cf853f0484efd2/docs/evidence/change-journals/gate-d/d-03-durable-inventory-checkpoint.md).
This is Windows draft-branch implementation evidence, not protected landing or
release qualification. Earlier independent increments retain their own journals.

Complete native reuse/no-content-read checkpoints, wider race/cancellation and
resource qualification, large installed repository evidence, incomplete error
observations and Linux/macOS tests. Current Inventory rereads eligible content;
explicit Cancel serializes behind the active writer. Later worker authorization
must consume committed source identity. Parse and later phases remain unavailable;
neither an open task nor a prepared prompt flight proves worker dispatch. Preserve
this complete acceptance scope instead of substituting more precondition checks.

Complete one owner-supplied real development task through the installed engine:

1. Open the authorized project and supply the task and concrete success criterion.
2. Resolve bounded context and configured eligible provider bindings.
3. Have the configured BF16 controller propose a binding, effort and handoff, or
   abstain. Show the actual proposal and evidence gaps; never attribute a rule's
   output to the model. Initially require review before effects.
4. RRFlow independently admits the proposal and executes through an authorized
   adapter, retaining source/configuration/artifact identities and observed usage.
5. Verify the actual artifact. After an ordinary edit, affected effects require a
   successor plan; unrelated work remains usable and earlier evidence is preserved.
6. Show results, failures and uncertain effects in Connectome, retain a correlated
   RROFLOW signal, and prepare a reviewable learning record.

One task proves a workflow, not general reliability or optimal model selection.
Restart, cancellation and lost-ACK handling need actual process evidence. Reading
or replaying evidence must not invoke a provider again.

## Ordered packages and exit evidence

Each row becomes bounded PRs at its existing owners. Do not skip their prerequisites
or introduce a competing engine roadmap.

| Order | Existing owner and implementation | Required exit |
|---|---|---|
| 1. Real inputs | G-06a: finish capture/review landing; obtain the owner's real task and rubric; enforce reviewed-real-data admission before GPU work. | Source-bound observations, actual reviews, consent and exclusions. Provisional/unadmitted input rejected before model loading; no manufactured accepted dataset. |
| 2. Public capability decision | G-01a/G-01b, D-06, H-04: define endpoint selection at `rrd-contract` using existing endpoint/configuration owners. Specify admission operation, descriptors, input/output bounds, credential references and failure semantics. | Reviewed capability contract and generated schemas/clients when admitted. Endpoint selection remains distinct from `RouteStepDecision`'s recipe/branch/context union. No unrelated API overloaded. |
| 3. One real admitted call | G-01a/G-01b and actual prerequisites: adapter at `rrd-inference`, admission at `rrd-engine`, configured transport and explicit credential resolution. | Installed engine calls the actual endpoint; denied/revoked/stale configurations cause no dispatch. Retain timeout/cancellation/late-result/restart evidence; unsupported termination and usage stay explicit. |
| 4. Task, plan and handoff | D-02/D-03/D-06, G-02 through G-05, I external-activity owner: join real context, budget and provider handoff through existing durable authority. | Proposal-to-effect receipts, no duplicate accepted effect after lost ACK, ordinary-edit successor plan, original budget consumption survives restart. Missing public admission holds dependent implementation. |
| 5. Connected experience | H-04/H-05/H-06 and Connectome: public task/proposal/approval/Stop/result views; RROFLOW receives authorized outcomes. | Real UI-to-engine-to-provider history; reload retains engine state; signal retry/readback preserves identity. No sample rows or optimistic success screens; sink outage preserves local receipts. |
| 6. Routing evidence | G-06a: authorized alternative providers on real tasks in isolated runs, actual outputs/failures/costs and independent outcome review. | Observed results justify preferences; unchosen alternatives remain unknown. Freeze project/time-separated splits and acceptance rubric before training/evaluation. |
| 7. BF16 qualification | G-06b/G-06c: pinned base/tokenizer/trainer/runtime and reviewed data; export/reload BF16 B; compare original BF16 A and a small-model baseline. | Held-out downstream success, constraint violations, abstention, per-family quality, latency/cost/memory and declared thresholds. Training loss never qualifies routing. |
| 8. Learning and delivery | I-03/I-07: bounded proposals, review, approved training, qualification and rollback. Gate J: reproducible native package and GitHub image. Quantize exactly qualified B into C. | Deduplication, revoked consent, rejected candidate, restart and rollback histories; clean-install/image proof; frozen A/B/C comparison and measured total serving footprint before claiming 29 GB. |

The engine dependency spine permits evaluation preparation early but places runtime
G/I work after real-project and admission prerequisites. Inspect current source
before each package. Unrelated benchmarks do not block preparation; missing
permissions, storage or public operations block effects that consume them. Do not
substitute standalone Python dispatch for missing engine execution.

## Next implementation: one authorized experimental proposal

This is the next execution slice of package 3, not a replacement for the complete
first-task milestone. Source inspection used PR205 candidate
`169b010a714ae7ea09895b2f82504d07ea9ecf0f`. Keep these changes together in one
reviewable engine candidate; register no operation until its handler and actual
authorization exist. Publish the code-grounded change brief before implementation.

### Scope and implementation order

1. **Close admission decisions before dispatch.** At `rrd-contract` and the
   existing security owner, define the endpoint-proposal permission separately
   from embedding generation. Require an authenticated installed estate, task
   read permission, reasoning-write permission and explicit experimental policy.
   A task/configuration digest identifies bytes; it grants no permission.
2. **Resolve a bounded engine packet.** At `rrd-engine`, read the existing task
   objective and approved endpoint policy. Bind task identity, read coordinate,
   configuration/policy digest, candidate facts and exact controller request.
   The initial task-text scope must be explicit: it does not imply repository
   context ingestion or source freshness. Never accept a caller-supplied URL,
   secret, candidate catalogue or claimed principal as engine authority.
3. **Keep declarations distinct from evidence.** Current candidate and manifest
   declarations do not prove effort support, entitlement, quality or loaded
   weights. An experimental profile must disclose unverified facts and grant
   no worker-effect permission. Requirements that depend on verified facts stay
   unavailable until the existing adapter/descriptor owner supplies them.
   Do not weaken a hard requirement to get a successful demonstration.
4. **Compose the existing execution owners.** Use `reserve_admitted_task_attempt`,
   `PreparedEndpointChat`, and the existing cancellation/deadline control. Resolve
   a credential reference through explicit operator configuration only after
   admission. Bound concurrency at the configured binding. Provider access must
   not scan arbitrary environment variables or enter prompts, receipts or logs.
   No second scheduler, budget ledger, automatic retry or Python dispatch path.
5. **Complete and replay through the same attempt ledger.** Extend the currently
   embedding-specific `AttemptRecord`, completion path and `TaskAttemptView` with
   a typed proposal receipt. Retain actual identities, choice, reported usage,
   elapsed time and uncertainty; missing values remain unknown. A receipt read
   or repeated attempt ID must never cause another provider call.
6. **Guard completion against changes.** Bind the task, endpoint configuration,
   session and security authority used for admission. Prove their freshness at
   the publication boundary, including concurrent revocation/configuration
   replacement; a separate pre-commit read is insufficient. Inspect and test
   the existing runtime/control transaction mechanism before choosing its guard.
   A stale proposal consumes its spent budget but cannot advance a plan. Do not
   map an ordinary input change to a permanent whole-task failure. Unknown remote
   execution remains unresolved until reconciled; freshness is not retry permission.
7. **Expose and exercise the real operation.** Add the authenticated server
   handler, executable catalogue entry and generated clients together. Supply
   process-owned credential configuration through the installed executable.
   Run against the actual private BF16 service, retain the exact engine and model
   identities available, then read the receipt through a restarted engine.

PR206 now implements the complete experimental proposal path above, including
dedicated authorization, configured credential resolution, atomic admission and
publication guards, and public dispatch. Installed development and optimized
engineering binaries have made actual BF16 calls, with restart/replay and fault
receipts. The optimized configuration case exposed an invalid model effort choice;
retain that failure. PR206 remains draft and unmerged after the protected native
APFS failure. These observations do not establish worker execution, routing
quality, source-edit replanning or the complete project workflow.

### Required evidence before this slice can be called live

| Case | Required observation |
|---|---|
| Authorized real task | Actual BF16 call, decoded choice/abstention and durable typed receipt linked to the engine request. |
| Missing permission, credential or configuration | Explicit denial; no provider dispatch. |
| Revocation or configuration replacement during execution | Late output cannot become an accepted current proposal; original evidence and consumed budget remain. |
| Stop or deadline | Bounded local return and retained remote uncertainty; no claim of remote termination without evidence. |
| Lost response and process restart | Same attempt remains readable or explicitly unresolved; no second model call on replay. |
| Changed task/source dependencies | Stale evidence is never relabeled current. Repository-edit successor-plan behavior remains package 4's separate acceptance requirement. |
| Public surface | Generated schema/client parity, actual authenticated installed-process proof and required candidate/merge-group CI. |

Use existing real maintenance tasks only to characterize this transport/admission
slice. They do not become human-reviewed routing labels or held-out quality data.
Controlled denial tests must identify their in-memory perturbations and stay out
of training exports. If atomic guards, scoped authorization, descriptor evidence
or installed credential admission cannot be supported at their current owners,
record the exact missing capability and implement it there before dependent calls.

## Worker access and next implementation boundary (October 31)

Read-only local discovery found Claude Code 2.1.310 with a reported `claude.ai`
Max login. The binary/version/help hashes and filtered authentication metadata
are retained in `.swag/evidence/20261030/engine-source-inventory/worker-access-observation.json`.
No agent task ran; login does not prove model availability, quota or execution.
The first real task/success criterion and preferred worker access are requested.
The existing direction favors Claude first, with provider-neutral engine authority.

The installed CLI and [official headless guide](https://code.claude.com/docs/en/headless)
agree that `--bare` disables subscription OAuth. A subscription adapter must
therefore qualify a controlled non-bare configuration, including hooks, plugins,
MCP, working directory and environment. A tool allow-list alone is not process or
filesystem isolation. Keep subscription login within the supported CLI; it is
not a bearer credential for the generic HTTP endpoint adapter.

The [CLI reference](https://code.claude.com/docs/en/cli-reference) documents JSON
events, explicit session identity, permission handling and turn limits. These are
adapter observations and local controls, not RRFlow receipts. Its cost cap uses
an estimate and can overshoot; it cannot establish a hard spend guarantee. Model
and effort must come from a qualified binding, never embedded provider rankings.

Next engine package: preview an exact task/proposal/source/capability-bound worker
activity; authorize its digest; reserve the existing task allowance and persist
its effect identity before dispatch; accept bounded results only after current
authorization, source and configuration checks. Preserve charged effort and
uncertainty on Stop, lost output or restart. A relevant edit produces a newly
approved successor; it must not reset effort or block unrelated exploration.
RRFlow owns this plan and acceptance. The CLI adapter returns observations;
Connectome renders public records and RROFLOW receives authorized correlation.

The current proposal transport decodes selector choices only. It must not be
relabeled a worker. Generic prepared activity/recovery and the actual worker
adapter need their own bounded PR and before/after tests, followed by an actual
owner task. No authored test output becomes a routing label or training sample.

## Data and owner participation

Start with an actual repository change and the owner's definition of a correct
result. A PR title cannot establish the best provider or effort. Capture context,
source revision, eligible models/access, actual attempts/artifacts, verification,
usage and corrections. Training consent is separate from task execution and review.

The existing 21-task review packet answers a limited intent-label question. It is
already development-exposed and cannot become untouched acceptance data. Routing
supervision requires actual provider outputs and evidence of their quality. The
agent prepares records and gaps; it cannot impersonate an owner or independent
reviewer. See [real task contribution](real-task-review.md).

Do not claim a fixed number of examples is sufficient. Set coverage/sample-size
requirements from declared task families, observed variation and desired confidence
before acceptance evaluation. Hold real acceptance tasks out of prompts, training,
tuning and repeated test-driven selection.

## Earlier execution record

The full objective is unchanged. PR196/205/188 are merged. PR206 is draft and
unmerged after protected run `40982529726` failed APFS image creation with
`Resource busy`. The current-main reconciliation preserves both controller and
storage contracts; focused Rust and SDK checks passed. Shared native failure
resolution and new candidate/protected evidence remain required. Historical
binary receipts do not qualify the combined source.

Tailscale authentication is resolved. The existing model endpoint was healthy and
idle before a new bounded installed trial. The real engine call returned a typed
proposal and observed usage; restart returned identical records and repeated
attempt identity was rejected. Four real-response fault histories passed:
configuration/session changes invalidate output, Stop and response loss preserve
uncertainty, and a fresh request after configuration replacement succeeds on the
same task without resetting effort or deadline. These are task-text transport and
completion proofs, not worker execution, repository-edit planning or quality tests.

Next steps remain ordered:

1. PR206's tested main reconciliation is published at `f278fa6f`. Resolve the shared native failure
   at C-07 / POAM-035, and complete exact-candidate/protected checks before landing.
2. PR212 is refreshed at `19ef6a04`; complete dependency/CI gates before landing its
   [actual Windows engineering bundle](testing-binary.md). Packaging,
   relocation, real proposal/reopen and primary readiness passed; preserve the
   release configuration-case model failure (unsupported effort) as an open
   qualification issue. Model serving stays separate. Signed/image delivery remains.
3. Implement the real task/plan/worker handoff at engine owners, with source-bound
   successor planning after ordinary edits and preserved spent effort.
4. Connect the public UI and authorized correlated RROFLOW outcomes to that flow.
5. Admit independently reviewed real task/outcome records before further BF16
   training or A/B/C qualification and quantization.

No uncertain estate was cleared and no fabricated response, label or consent was
introduced. The owner task/review request still applies to routing-quality and
learning admission. Existing real public maintenance tasks supplied the transport
proof context. Relevant Rust/SDK checks and live receipts are recorded in the
immutable PR journals; final repository/capture/cache-policy checks passed.

No GPU run compensates for missing labels. No provider subscription is treated as
an API credential; discover supported bindings before promising use. Legacy SWAG
training scripts are not approved alternate entry points to bypass admission.
The current Unsloth launcher requires admitted data and an explicit experiment seed.

The eventual 29 GB target includes weights, runtime and cache. A from-scratch 14B
controller remains a separate research objective requiring data/compute feasibility
after real routing evidence exists.


## Audited integration dependencies (October 30)

The proposal and packaging refreshes are published at PR206 `f278fa6f` and
PR212 `19ef6a04`; both are draft, mergeable and unmerged at this observation.
The native UI integration must use the engine's generated public boundary.
Draft PR222 now supplies the typed proposal binding at `61ddb264`, with actual
native-client/installed-engine BF16 delivery, restart and replay-denial evidence.
Its implementation/build source is `dccfc419`; the tested primary engine remains
`54fb845d`. H-04 / POAM-011 still owns full generated binding migration and semantic
conformance; the 51 projected metadata markers do not imply 51 callable new APIs.
Connectome can now implement task/proposal/Stop/readback through its native session
against the explicitly pinned dependency. Keep renderer credentials, duplicate
HTTP clients and parallel lifecycle stores out of that integration.

Connectome has advanced beyond the old prototype audit. The pinned checkout
`38142b77` has a native workbench; public main was observed at `5ba5a9d5` and
pins engine client/contract revision `86adada6`. Inspect that current source and
its own contribution procedure before UI edits. Existing open lifecycle PR24
owns local-project engine management; avoid overlapping or replacing it.
A current workbench is not evidence of the missing controller/task journey.

Source replanning is already owned by PR200/202 and their integrated descendants
PR208/218/221. Their attunement evidence does not establish development-task
execution: the current public `task.rs` explicitly says a task groups work and
orchestrates nothing. G-02a/G-04 own durable dispatch identity and governed
transitions; D-03 owns committed source input. Join these actual owners for the
proposal-to-worker flow, preserving uncertain attempts and spent effort through
ordinary-edit successor plans. No parallel UI/Python plan store or automatic
retry is an acceptable replacement. A genuine owner task and success criterion
have been requested for the complete workflow trial; independent review and
training consent remain separate requirements.

## Acceptance and reporting

RROFLOW's separate source at `e27920912a2c24a9c3adc5fc7546be9d14859a7c`
already implements agent-turn capture and authenticated ingest. Package 5 must
extend the actual public integration boundary with engine task/attempt/source/
receipt correlation and define retry/readback semantics; the current turn store
replaces records by event ID. Preserve existing local evaluation-ingest evidence
without calling it the full controller journey. Hosted health, authorization and
delivery still need fresh evidence. Do not build a duplicate collector from an
outdated assumption that no service code exists.

Report planned, implemented, tested, merged, live and qualified separately. Retain
exact source revision, input hashes, commands, raw results, failures and limits.
Use real histories and controlled actions against real processes for validation;
any derived perturbation remains traceable and outside learning data. Never populate
missing receipts or measurements.

Freeze quality, latency, cost and memory thresholds before acceptance measurement.
The first task and provider budget are still needed to define that profile; those
thresholds are unresolved, while authorization and identity checks already apply.
No completion percentage or ETA is inferred from PR counts.
