# Deployment readiness

Assessment checked 1 November 2026. SWAG is an engineering preview. The current
evidence supports continued development and controlled testing, not a public
release or a qualified routing model.

## What is verified

- RRFlow PR222 merged as `6c069e1462d2b9cbb0237e9c117c379d1482bbaa`;
  protected run `41248811413` completed successfully.
- Connectome PR30 implements public engine-owned plan discovery, lifecycle
  preparation/approval, and source replan preview/accept. It remains draft and
  depends on unmerged engine/UI work. Candidate run `41252267362` has passing
  frontend, Windows/Linux/macOS, process integration and final gate checks. Live
  readback confirms the run completed successfully; PR30 remains draft.
- The matching Windows desktop candidate built from clean UI source `1f2e2a5c`
  and engine `8d475008`. Both frozen executable hashes were rechecked against the
  build receipt (`.swag/controller-ui/1f2e2a5c/build-receipt.json`).
- Local native checks report 42 passes, with 20 opt-in entries ignored. Three
  focused installed-process scenarios pass: source replanning and recovery,
  lost-reply reconciliation without duplicate effects, and lease expiry/cancel.
  These exercise actual engines, not model-quality evaluation data.
- Earlier desktop evidence demonstrates a configured BF16 proposal and task
  recovery. It does not establish successful project-file changes.

## Remaining release gates

1. Land dependent PRs through their required checks and rebuild from accepted
   source. Candidate checks do not substitute for protected acceptance.
2. Implement the governed project-effect path at RRFlow's existing owners,
   then complete the desktop source-edit trial and a real authorized development
   task, including project effects, restart/recovery, and RROFLOW outcome
   correlation. The current desktop trial reached discovery and a replan
   preview; stale-preview rejection and successor acceptance remain unverified
   through this UI. Its target window became unavailable during resumption;
   the reason is unknown.
3. Qualify original Qwen, custom BF16, and that same checkpoint after quantization
   on independently reviewed, held-out real routing cases. Earlier provisional
   assistant-inferred labels are not approved training or qualification data.
4. Validate native and container installation on clean environments, upgrades,
   rollback, configured credentials, resource limits and failure recovery.
   Produce versioned distribution artifacts with checksums and release evidence.
5. Connect the local SWAG repository to the owner's intended delivery repository.
   This checkout now has Git history starting at `3a5b337`, but no configured
   remote. Local commits are not published or reproducible release artifacts.

The RROFLOW engine-correlation receiver merged through
[PR43](https://github.com/rrflow/rroflow-development/pull/43) as
`d552e8ab7e898b21dd5de98caab77f8ed992226e`, from candidate `b4c04cee`.
All 136 local Rust workspace tests pass with disposable PostgreSQL configured,
including JSONL and PostgreSQL ingest/replay/conflict/isolation/restart checks.
Strict lint, formatting and 46 dashboard/release guard checks pass. Candidate
CI run `41255031094` now passes all six jobs, including cross-platform and
hosted-artifact checks. Release-plan run `41255031089` also passes its build
jobs; publication jobs were skipped. Post-merge main CI `41257683331` passes all
six jobs. An isolated Windows trial now verifies the actual installed engine
sender and RROFLOW receiver: an authorized job observation is stored, its source
digest matches, and both records survive process restart. Acknowledged replay
leaves one engine attempt and one receiver event. This used fresh loopback
configuration and JSONL storage, not a hosted deployment.
Actual development-task outcome correlation remains
required. Receiving an observation must not imply task success or training
approval.

## Project execution is an implementation gate

At worker PR229 head `52e2254af0ad616295975f35aef1154ca5634713`, the
[public operation contract](https://github.com/rrflow/rrflow-development/blob/52e2254af0ad616295975f35aef1154ca5634713/crates/transport/rrd-contract/src/operation_reference.rs)
defines `task-worker-execute` as a selected-model call producing draft text.
It explicitly grants no current project-file permission or task-success claim.
Merging worker, resume, discovery and observation delivery cannot alone turn
that draft into an authorized project change.

RRFlow's existing D-06, I-03 and I-07 owners retain capability binding,
durable effect execution and source-bound project mutation. The next execution
package must trace the selected draft into an exact previewed effect with
current source/configuration/authorization checks, bounded execution, durable
receipts and uncertain-outcome recovery. Connectome must consume that public
engine boundary; a Python patch runner or UI-owned executor would violate the
intended ownership. Approval of draft text alone is not approval to execute it.

Acceptance requires independently observed project artifacts to match the
approved effect, rejection before writes after a conflicting source edit,
explicit successor replanning, and restart/readback without duplicate effects.
Only then can the complete real-task trial establish project completion and
correlate its actual outcome to RROFLOW. These are outstanding implementation
and acceptance requirements, not merely a missing demonstration.

## Current engineering gap

The engine sender implementation is published in
[PR235](https://github.com/rrflow/rrflow-development/pull/235), now at
`b856a8fb08200c9117d759c43f9eaad0ec55ef77`. Its earlier `ebeecabb` head's full
[candidate pipeline](https://github.com/rrflow/rrflow-development/actions/runs/41263686147)
completed all 23 jobs successfully. PR235 entered the protected merge queue at
position 3 on 1 November, 02:52 UTC; protected acceptance and merge remain pending.
The queue reported `UNMERGEABLE` against the entries ahead. PR190, PR232 and
packaging PR212 have since landed. The published ordinary integration of accepted
main `daec1f1a` resolves the 19 OpenAPI digest and generated SDK/reference
conflicts, regenerates the canonical projections and preserves both parents'
behavior. Local contract/adapter, owning-suite, binary build, lint, TypeScript
and repository checks pass. GitHub reports the PR mergeable; new candidate and
protected acceptance remain pending. New
[candidate 41342695388](https://github.com/rrflow/rrflow-development/actions/runs/41342695388)
is queued, with normal automatic merge enabled for the exact head. The old
passing run remains evidence for `ebeecabb` only. Follow the
[developer-build execution plan](implementation-plan.md#developer-build-execution-1-november)
for the remaining dependency order and evidence requirements.
The original candidate
exposed missing adapter CI coverage, stale generated storage-test digests and two
recovery-test timestamp assumptions. The correction retains every failing log,
updates those boundaries without changing production clock checks or fixture
outcomes, and passes the affected local engine/evaluator/policy checks. Hosted
candidate confirmation now passes, including all three optimized native recovery
jobs. Persistence, atomic source/configuration/authority guards, historical
source readback, HTTP/native operation wiring and installed-engine fault tests
are now authored locally. Four focused contract tests and eight installed-engine
fault tests pass after retained corrections. Five SDKs regenerate; 74-operation
parity and TypeScript checking pass. After correcting a stale SDK fixture count
from the canonical generator, the engine library suite passes 298 tests with
four existing helper entries ignored. All 165 contract/adapter tests pass, and
HTTP/native wiring compiles. Three additional public transport tests now pass:
approved export and readback through the native client and HTTP server,
acknowledgement persistence across engine reopen, identical-event retry after a
lost reply, and an actual accepted task-attempt source. The outbound HTTP receiver
is a local protocol fixture. A separate installed-binary RROFLOW trial passes,
with evidence in
the retained result (`.swag/evidence/20261031/observation-delivery/installed-roundtrip-20261101T012030Z/result.json`).
Subsequent review fixed a retention-cap deadlock and added concurrency/source
advancement coverage: all 11 focused engine tests pass. The complete engine,
server and client suites now report 427 passes, zero failures and four ignored
subprocess helpers after building their required CLI binaries. One SDK entry
returned early without a manifest; a separate actual-daemon run then passes
Rust SDK conformance. The corrected hosted candidate subsequently passed the
shared live-daemon harness for all six supported languages and both installed
Python attunement checks (job `124722136316`). That shared corpus does not prove
every new observation operation in all languages; protected merge acceptance
remains pending. The complete exact-head candidate and macOS log receipt is
`.swag/evidence/20261031/observation-delivery/candidate-ebeecabb-complete.json`;
adjacent Windows and Linux receipts retain their raw recovery logs.
Strict all-target lint, workspace formatting and generated parity pass.
The rebuilt executable passes the installed receiver trial again in
the current result (`.swag/evidence/20261031/observation-delivery/installed-roundtrip-20261101T013715Z/result.json`),
with one receiver event and one attempt after restart/replay. Earlier failed
suite runs and original binary evidence are retained. Author review and publication are complete; real-task outcome correlation,
required CI, accepted source and a release rebuild remain necessary before
treating this as deployable. The worker, resume and discovery PRs (229, 230, 231) and Connectome
PR30 remain drafts. Mergeability alone is not acceptance.

The architecture follows the intended ownership split, but release execution
still has too many unlanded prerequisites. Prioritize one complete real-task
path on accepted source before expanding research or automatic learning.

A worktree-preserving integration preview of worker `52e2254a` and sender
`ebeecabb` reports 28 conflicting paths: nine source/test files and 19 generated
SDK/reference files. This is not a completed merge. Preserve both policies and
their independent digest frames, all worker/observation authorization and public
operations, then regenerate projections from the combined canonical catalogue.
Recheck legacy profiles with each optional policy absent and profiles containing
both policies; compile and run the affected suites before candidate CI. Repeat
the preview against the actual landed revision before integration. The exact
preview and conflicting object identities are retained in
`../.swag/evidence/20261031/observation-delivery/worker-sender-integration-preview.json`
and its adjacent log. The pending worker publication hold remains unresolved.

The current bundle is unsigned, unoptimized, and excludes model weights. The
custom BF16 weight files total 61.07 GB. Ideal 9-bit packing alone is 34.35 GB
before runtime/cache, so the 29 GB total-serving target remains unproven.

The next acceptance milestone is one complete, repeatable real-task workflow on
an exact versioned build. More infrastructure tests alone cannot establish it.
