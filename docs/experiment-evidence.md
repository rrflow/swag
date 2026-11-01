# SWAG experiment evidence and execution

Recorded 2026-10-28. These are offline/operator experiments, not completed engine
integration or an independently approved release.

## Real tasks and provisional training

`swag_collect_routing_tasks.py` captured 65 merged PR titles, source revisions,
changed-path metadata and check outcomes from the owner's three development
repositories. Raw source bytes and SHA-256 references are retained under
`.swag/datasets/development-task-review-20261028/`. GitHub path listings can be
limited; they are supporting review evidence, not a complete diff audit.

`config/training/development_task_reviews.jsonl` records this assistant's explicit
intent labels and rationales. They are not human reviews or evidence that a
particular provider/model was optimal. `swag_task_corpus.py` exports 44 RRFlow and
RROFLOW training tasks and 21 held-out Connectome development tasks. Inputs contain
only task titles; paths and outcomes inform review but do not leak into prompts.
The corpus remains separate from strict reviewed-routing admission.
The readable review batch (`files/swag-task-review-20261028.md`) links every task
to its source PR and exposes the proposed label and rationale for correction.

```powershell
python tools/swag_task_corpus.py --source-dir .swag/datasets/development-task-review-20261028 --reviews config/training/development_task_reviews.jsonl --output-dir .swag/datasets/fresh-intent-export
```

The original Qwen BF16 endpoint matched 14/21 intent labels, with no malformed
outputs and about 0.996 seconds warm median. These labels are provisional and the
sample is small; this is not provider-routing or acceptance performance.

Training uses the pinned Qwen3-Coder BF16 base, rank-16 attention LoRA, three epochs,
batch size one, accumulation four, 512-token bound and response-only loss. The
Unsloth image is pinned in the retained launch record. Initial failures exposed
container ownership, explicit chat rendering and CUDA device-map compatibility;
failed attempts are retained. Follow the actual training metadata for completion,
not the existence of an output directory. `swag_export_bf16.py` verifies the base,
merges a completed nonquantized adapter and hashes independently loadable weights.
Export alone is not fresh-process reload or qualification.
The pinned runtime warned that Qwen3-MoE does not accept its batch item-count
argument during accumulation. Exact numerical equivalence to a larger batch has
not been demonstrated; preserve this limitation in any reproducibility claim.

The run completed **33 optimizer steps / three epochs** in 488.66 seconds. It
trained 13,369,344 LoRA parameters, retaining the full BF16 base. Mean training
loss was 0.2982; final development loss was 0.1702. Loss is not intent accuracy.
Peak PyTorch allocated/reserved training memory was 61,652,847,104 /
61,712,891,904 bytes, not total serving footprint. Checkpoints 11, 22 and 33 include
optimizer, scheduler and RNG state; interruption/resume has not been exercised.

Inspection of the saved training arguments recovered `adamw_8bit` optimizer state,
BF16 model computation, seed 3407 and effective warmup ratio **0.1**. The initial
CLI recorded 0.03 but did not forward that ratio, so the pinned runtime default
applied. The trainer now forwards it explicitly and saves effective settings;
reproduce this particular run with `--warmup-ratio 0.1`. An 8-bit optimizer is not
quantized model weights. Exact source/settings for the completed run are retained
in `.swag/evidence/20261028/custom-training/`.

The merged BF16 checkpoint has 61,066,575,648 weight bytes and manifest SHA-256
`ba7bede9963d469f312e06b337cb9241de524bdf77c7fe2ee30e09dd9b126252`.
Its model alias is `swag-qwen3-coder-intent-20261028`. A fresh vLLM process loaded
the merged weights and completed both intent and routing evaluations. The creation
manifest remains immutable; subsequent reload evidence is retained separately.
The saved adapter audit found nonzero values in all 192 LoRA B matrices that
started at zero. The adapter SHA-256 is
`33a40e3961f866dd22ec739032f58acfb0d1210b220d613c1c808c27960e54c7`;
this is an actual trained adapter, not a renamed baseline checkpoint.

## Custom endpoint comparison

The authenticated private endpoint is forwarded to `http://127.0.0.1:8084/v1`.
Unauthenticated model discovery returned 401; authenticated discovery returned 200
and the expected custom alias. Access details are in `.swag/cluster_access.md`.
This is an experimental endpoint, not an RRFlow-installed controller.

| Intent classifier | Matched / 21 | Balanced accuracy | Warm median |
|---|---:|---:|---:|
| Majority training label | 14 | 33.3% | No model call |
| Original Qwen BF16 | 14 | 56.7% | 996 ms |
| Custom Qwen BF16 | 15 | 65.1% | 752 ms |
| d1-3B | 10 | 53.2% | 34 ms |

Balanced accuracy averages recall across the three classes. One additional correct
task is preliminary, not statistically established generalization. Hardware/runtime
and API differences limit latency comparisons. The custom checkpoint still matched
**7/13 routing cases with five policy violations**, the same counts as the original
base; warm median was 1.514 seconds. It did not become a qualified router through
intent fine-tuning. Quantization and autonomous activation have not been performed.

`swag_intent_comparison.py` recomputes these counts and class metrics from retained
outputs and corpus identities. Final results are under `custom-intent/`,
`custom-routing/` and `intent-comparison.json` in the dated evidence directory.
The custom routing report also passed real local RROFLOW ingest/retry/readback.

## Small-model routing comparison

LiquidAI/d1-3B revision `051bcc464b01b9f92942b364d9586b0ef5912432` ran on spark-03
with its inspected custom code, BF16 weights and named-choice API. Two runs matched
9/13 frozen development cases with three policy violations. The second warm median
was 92.18 ms; peak allocated/reserved PyTorch memory was 6,367,813,120 /
6,425,673,728 bytes. Weight files occupy 6,247,065,504 bytes.

Qwen matched 7/13 with five policy violations and 1.310 seconds warm median.
Different hosts/runtimes and d1's structural choice constraints prevent treating
this as an isolated serving-speed experiment. Requested effort was mapped by the
d1 adapter, not predicted. Neither model passed the protocol. PyTorch allocation
is not total serving memory; RIPL itself has not been installed or measured.

On the separate 21-task real-title intent split, d1 matched **10/21**, versus
Qwen's **14/21**, at about 33.7 ms warm median. Smaller/faster did not mean more
accurate on this task. Preserve both comparisons; the routing smoke result alone
cannot justify choosing d1. Intent labels remain assistant-inferred.

## Actual signal sink and review proposals

The existing RROFLOW Rust ingest was built from local revision
`e27920912a2c24a9c3adc5fc7546be9d14859a7c`. An isolated instance at loopback port 8892
accepted content-free Qwen and d1 reports. Each duplicate replaced one record;
authenticated retrieval returned exactly the submitted event. Receipts are in
`.swag/evidence/20261028/signal-sink-live/` and `d1-signal-sink-live/`.
After deliberately terminating only this isolated ingest and restarting it with
the same store, GET-only verification recovered both unchanged reports. Receipts
are in `signal-sink-restart-readback/` and `d1-signal-restart-readback/`. This proves
local restart readback for these reports, not hosted deployment or engine receipts.

```powershell
python tools/swag_signal_sink.py --run-dir .swag/evidence/20261028/routing-development-baseline --base-url http://127.0.0.1:8892 --credential-file .swag/rroflow-live/credential.txt --devspace swag-local-validation --output-dir .swag/evidence/fresh-sink-check
python tools/swag_learning_candidates.py --run-dir .swag/evidence/20261028/routing-development-baseline --run-dir .swag/evidence/20261028/d1-development-repeat --output .swag/evidence/fresh-review-proposals.json
```

The latter automatically groups verified failures and deduplicates repeated report
identities. It emits review proposals only. It does not implement an engine routine,
infer correct labels, start training or authorize promotion. Changed evidence yields
new proposal identities while previous records remain inspectable.

## Qualification and UI

`swag_model_qualification.py` checks original BF16, custom BF16 and quantization of
exactly that custom artifact. It requires a shared acceptance protocol, admitted
acceptance cases, frozen absolute/relative limits, serving identity evidence and
total serving-memory evidence. Missing evidence produces a failed report. Engine
admission, installed rollback and PR/CI remain required even if offline checks pass.

The TypeScript viewer at `http://127.0.0.1:8891` shows both measured development
routing baselines plus the custom checkpoint, and the four-way intent comparison.
It is a saved evidence view, not a live Connectome integration. See
[the execution plan](implementation-plan.md) for the remaining engine-owned work.

Validation after implementation: **74 Python tests**, **two Node tests**, the
TypeScript build and a Playwright desktop/mobile interaction test passed.
`AGENTS.md` was preserved byte-for-byte. This checkout has no Git history;
no SWAG commit, PR, image release, engine integration or production promotion is claimed.

## Engine-repository paired review package

RRFlow PR176 merged at `2f1424283e257ce41b2413cf17dcc86fe45a34e1`.
[PR179](https://github.com/rrflow/rrflow-development/pull/179) adds the next
offline G-06a preparation tool in the engine repository. It does not introduce
a SWAG sibling dependency, runtime scheduler or promotion path. Fifteen focused
failure-boundary tests passed locally, including unchanged-input reuse and
changed-input successor packets without overwriting earlier evidence.

The explicit local export in
`.swag/evidence/20261028/engine-outcome-review/export/` retains source results,
artifact manifests, corpus cases and normalization provenance. Manifest SHA-256:
`18f60542adce89a92fb4a98baafcabb0b12e93b8422f7a4f0b891b412f04e732`.
Running the engine tool twice yielded the same packet with **21 tasks, three
candidates and 63 outcomes**. Packet SHA-256:
`e54bfeeef61fef3cd0e31f00d4c45460ce67336badf51138692102fa99d34bb6`.
Executed tool SHA-256:
`8705270c047d3162ba54cc269c84c3ea056a009c89c6e50e0011af381f80b0d9`.

From the PR179 engine checkout, run:

```powershell
python scripts/inference/review_outcomes.py --manifest $SWAG_CHECKOUT/.swag/evidence/20261028/engine-outcome-review/export/manifest.json --output-dir $SWAG_CHECKOUT/.swag/evidence/20261028/engine-outcome-review/packets
```

The readable review table (`files/swag-paired-intent-review-20261028.md`)
links the 21 source PRs and all model choices. Verification stays unknown:
assistant-inferred labels have not received independent human review and do not
measure best-provider task completion. No additional training, quantization,
model activation or hosted integration occurred in this package. Exact PR
candidate CI and review remain required; local checks are not merge evidence.

## Implemented review UI and explicit decision validation

The local TypeScript page at `http://127.0.0.1:8891/review.html` now loads the
exact 21-task packet and displays all 63 model outputs. It supports accept,
correct and exclude decisions, rationale/evidence references, draft download
and resume, stale-packet rejection and completed review export. No review is
uploaded or stored on the server; downloaded files preserve progress.

RRFlow [PR180](https://github.com/rrflow/rrflow-development/pull/180), candidate
`ba1203165de297c0e16977650658f1d32fe77a88`, adds
`scripts/inference/review_decisions.py`. It reconstructs the packet from the
original export before validating every decision. It writes immutable review
evidence with identity authentication, training admission, acceptance-data and
deployment qualification flags all false. The draft depends on PR179, whose
full candidate CI was still queued at the last check. Neither is reported merged.

Validation: seven new Python validator tests, 15 packet dependency tests, six
Node tests, TypeScript build, and two Playwright browser tests passed. Engine
workflow/documentation/navigation/inventory checks passed. The browser test
first failed on a textarea text-content assertion, then passed after changing
the assertion to check the restored value. Desktop/mobile screenshots are
`review-ui-desktop.png` and `review-ui-mobile.png` in the dated evidence folder.

A clearly marked synthetic assistant browser export was validated twice against
the actual source packet. Both produced
`c29d18aed738d293de1abceed5b88625208b06e0a7ab5d4e32117d5c866af67f`.
This test excludes all tasks and proves file exchange, not semantic review.
It is retained separately in `.swag/evidence/20261028/review-ui-test-only/` and
must never be used as real human review or admitted training data. No additional
training, quantization, runtime learning or hosted integration occurred.

## CPU classifier baseline and merge follow-through

The fixed multinomial Naive Bayes baseline in `tools/swag_intent_baseline.py`
uses word counts, alpha=1 smoothing and empirical class priors. It fits only
the same 44 training titles, saves/reloads its artifact, then scores the 21
project-held-out development titles. No hyperparameter search or tuning against
development results was performed. Three focused baseline tests passed.

Actual result: **12/21**, balanced accuracy **34.5%**, versus majority 14/21
(33.3% balanced), original Qwen 14/21 (56.7%), custom BF16 15/21 (65.1%) and
d1 10/21 (53.2%). The baseline missed all documentation tasks. Its serialized
model is 5,361 bytes; local classifier-call warm median was approximately
14 microseconds. This excludes service/queue/transport costs and is not an
end-to-end latency or total serving-memory measurement. Small sample size and
assistant-inferred labels still limit every comparison.

Retained model, exact runner source, protocol and results are under
`.swag/evidence/20261028/intent-naive-bayes/`. Model SHA-256:
`fb9309c62a3e8b458e7acbadbbbfc16af70971aaf1714fb29c41651b90eda57e`.
The recomputed five-way comparison is `intent-comparison-with-cpu.json` and
is displayed in the local evidence dashboard. The original three-model review
packet is preserved; adding this result does not silently alter existing review
identities.

At the owner's merge request, PR180 was marked ready for full CI because the
exact PR179 dependency is already integrated and tested in its candidate.
Landing order remains PR179 then PR180. GitHub rejected the initial PR179
merge request while checks were pending because repository auto-merge is off.
A bounded local operator process now follows the two exact heads, requires all
23 CI partition/gate checks, and uses only the normal merge queue. It stops on
head/destination changes, failed checks or its four-hour limit. No branch rule
was relaxed. Events live in `.swag/evidence/20261028/merge-followthrough/`;
inspect them and GitHub for actual completion rather than assuming a merge.

## Source-identified native endpoint configuration

Executed on 28 October at 21:41 UTC against clean PR180 candidate
`ba1203165de297c0e16977650658f1d32fe77a88`. The repository-owned
`scripts/build_rrflow.py --profile dev` built a Windows executable with embedded
source, Cargo lock, compiler, feature closure and build-environment identities.
The build used two jobs and an isolated target directory. Binary SHA-256:
`9a2207573cf58a450dfc030fccc8d8118ef6c530322f4223ccccd487c7b7d70e`.
It remains explicitly unqualified.

The first installation preview rejected Cargo's two-link executable. The project
remained empty. A byte-identical single-link distribution copy passed admission;
no engine policy was changed. Both the rejected attempt and corrected runner are
retained. The isolated installed project is
`.swag/rrflow-controller-integration/packaged-project`.

The actual engine API passed all of these checks:

- API-key session creation; unauthenticated configuration preview rejected (401).
- Preview left configuration unchanged; approved apply matched canonical readback.
- Reapplying the accepted plan was idempotent.
- Configuration survived two separate process terminations and fresh starts.
- Revocation retained revision history; stale plan and stale revision returned 409.
- A fresh preview restored the profile at revision 3.

The profile pins the custom BF16 model alias and merged manifest digest. It names
the operator's private SSH-forwarded endpoint and a credential reference; no key
or session token is included in receipts. An independent operator probe verified
model listing: 401 unauthenticated, 200 authenticated, exact expected alias.
That probe was **not engine-dispatched inference**. The declared 100 GiB capacity
is not a measured peak or progress toward the 29 GB qualification target.

Evidence directory: `.swag/evidence/20261028/native-endpoint-integration/`.
`build-receipt.json`, `packaging-receipt.json`, installation/configuration plans,
applied records, restart readbacks and `result.json` retain the execution evidence.
`native-product/rrflow.exe` is the staged executable. `runner.py` is the exact
successful operator script, SHA-256
`4320ffea43e0315ab47c19d00f005e9aba52be0ac91d5aa4da74d0838bca3f18`.
The script deliberately refuses to overwrite an existing project or receipt.
All three owned test-server processes were stopped afterward. Model-serving
containers and other projects were left running.

This establishes local durable endpoint configuration. Credential resolution,
learned endpoint selection, engine-dispatched provider calls, Connectome views,
hosted deployment and release qualification remain separate unfinished work.

The dashboard now displays this bounded result. TypeScript compilation and the
desktop/mobile browser check passed after the update; screenshots were refreshed.
`evidence-manifest.json` binds 20 retained experiment files, verifies the executed
runner identity and records a successful scan for both experiment credentials.

## Protected merge queue and bounded capture polling

PR179's exact candidate `6f37ae55644e6807f2fb25fac227d5e061ffdc90` passed all
23 checks. The CLI merge command nevertheless attempted auto-merge, which this
repository disables. At 22:05 UTC, the normal GitHub `enqueuePullRequest` API
accepted the same expected head into the protected merge queue. No branch rule
or repository setting changed. Merge-group CI still applies; queued is not merged.
The corrected bounded follower uses that API, observes an existing queue entry,
stops if it leaves the queue without merging and preserves PR179-before-PR180
landing order. Evidence is under `merge-queue-followthrough/`; the earlier failed
attempt remains under `merge-followthrough/`.

`tools/swag_capture_watch.py` now provides bounded polling over tracked Git diffs
and an explicit local task-title/route-override JSON file. It reuses the passive
capture schema and serialized append path. Snapshot identities include actual
staged/unstaged content hashes, so repeated edits to one filename are detected.
Prior records remain intact; unchanged observations deduplicate across process
restart, and returning to an older state records a new transition. Invalid or
moving input defers a poll and can recover after an ordinary edit.

Seven tests exercised real temporary Git repositories, including a running
polling process that observed a later edit and stopped at its record limit.
The six existing passive-capture tests also passed. A 20-second run against the
actual PR180 worktree emitted one unreviewed observation and stopped; a fresh
process returned `unchanged` and preserved the JSONL bytes. No route, successful
outcome or training consent was inferred. Evidence is retained under
`.swag/evidence/20261028/passive-watch/`; synthetic test observations are separate
temporary fixtures, not training data.

Raw diffs are not retained. Existing pattern redaction, byte/time limits and
append locking apply; see [the operating instructions](passive-capture-watch.md)
for exclusions and limits. This local collection adapter is not an engine
routine, automatic learning scheduler, accepted source read stamp or Connectome
integration. SWAG has no Git repository here, so these local changes have not
been committed or released as a container image.

## Verified landing and PR180 refresh

PR179 merged into development/main on 2026-10-29 at 00:29:14 UTC, merge commit
`11a0fe1b16d70d91334e95efa3975e0b4a439b32`. Both its candidate head and merge
commit are ancestors of fetched main. The follower then stopped because GitHub
reported PR180 conflicting. The clean isolated PR180 worktree integrated that
main revision with an ordinary merge; Git resolved the combined tree automatically,
with no unmerged index entries or manual content resolution.

All 22 packet/validator tests, workflow policy, documentation policy, generated
navigation, execution inventory and diff checks passed. Refreshed commit
`21fb12c2a48f97aef7d0b66368a2903a0f153327` was pushed to the public development
branch, preserving the existing candidate and landed main as its two parents.
GitHub now reports PR180 mergeable. Fresh candidate CI is pending; the old head's
passing checks are not acceptance evidence for this head. PR180 remains open.

The corrected follower has resumed against the new exact head, retaining events
under `.swag/evidence/20261029/pr180-refreshed-merge-followthrough/`. It still
requires all 23 candidate checks and the normal protected merge queue. Other
agents' open PRs were inspected for status but were not changed or merged.

## Repository-owned observation collector

[PR188](https://github.com/rrflow/rrflow-development/pull/188), candidate
`323e6e74ac1c065d053453e2c41e9a1ddf1eedd4`, adapts the local watcher into
`scripts/inference/capture_observations.py` in RRFlow. It imports only standard
library modules and the landed `review_outcomes.py` helpers. Its explicit
observation format binds collector/helper sources and Python version as well as
Git/context identity; it verifies retained record identities and predecessor
order before appending. It does not import SWAG code or become an engine runtime
dependency. Its outputs are not implicitly accepted by review or training tools.

Eight real-Git/process tests and all 15 existing exchange tests passed. Workflow,
documentation, generated navigation, inventory and diff checks passed. A real
10-second observation of the clean PR180 checkout emitted one unreviewed record;
fresh-process replay with `-S` returned unchanged. An archive containing only the
two committed Python sources also ran with site packages disabled and preserved
the exact output. The local receipts and archive are retained under
`.swag/evidence/20261029/engine-capture/`.

Collector SHA-256: `4c6a66f2ea692162df28db7957adaf9e7fde757d4b2e7cb661ad84d071753d7c`.
Observation SHA-256: `fc64b45e007e66f51b23c5359eccd46b1971e2836226965b2b32ce22af34500a`.
No model, outcome, consent or review correctness was inferred from the captured
task. The canonical candidate has been pushed publicly, but remains draft until
PR180 lands because their CI block and generated indexes overlap. Integrate main
and preserve both test commands before starting its full candidate pipeline.
This source-package proof is not hosted deployment or automatic engine learning.

At 01:22 UTC the existing custom BF16 endpoint was rechecked: 401 without a key,
200 with the configured key, and exact alias `swag-qwen3-coder-intent-20261028`.
The receipt is `20261029/custom-endpoint-health.json`. Model qualification and
the 29 GB serving target remain unchanged and unproved.

## Combined review/capture candidate: 2026-10-29

At 03:15 UTC, PR179 remains merged. PR180 passed all 23 candidate checks and
is first in the normal protected queue; its queue run is `40801817553`. Actual
landing remains pending. The prior instruction to leave PR188 draft is superseded:
it was already marked ready at 01:34 UTC, and its source needed dependency repair.

A read-only merge preflight found three genuine overlaps with PR180: the reusable
CI workflow, Gate G generated index and file inventory. Candidate
`fc7ccb2ef929b141304d8f13976a50c67b5e59fe` merges collector head
`323e6e74ac1c065d053453e2c41e9a1ddf1eedd4` with PR180's exact queued candidate
`45a0cd82733abc93a1374796c47bf5d68bd2bbcc`. Queued source is not merged-source
evidence. The workflow retains all three packet/decision/capture test commands;
the generated conflicts were rebuilt through their owning tools. Collector and
review source/test files match their respective parent revisions byte for byte.

All 30 focused tests passed. Workflow/documentation policy, navigation, inventory
and diff checks passed; the index has no unresolved entries and the worktree is
clean. The linked immutable engine journal is
`docs/evidence/change-journals/gate-g/controller-capture-review-integration.md`.
The public PR188 head was verified after push. Fresh full CI is run `40810426309`;
checks on the previous head are not acceptance evidence for this source.

The previous exact-head follower was stopped and its logs preserved with an
operator handoff. The current bounded follower and its source snapshot are under
`.swag/evidence/20261029/integrated-review-capture-merge-followthrough/`.
It observes PR180's existing queue entry, waits for actual landing, then requires
all 23 PR188 candidate checks before requesting its normal protected queue.
Changed heads, conflicts, failures or the four-hour deadline stop follow-through.
This operator helper is not an engine learning routine or product scheduler.

## Real-data goal and training entry: 2026-10-29

An active goal now targets the complete real-task controller workflow, with the
ordered implementation and prerequisites in `implementation-plan.md`. Owner
constraints prohibit fabricated tasks/outcomes/labels and hardcoded routing.
The current Unsloth entry rejects missing admission and the retired provisional
task-corpus option before importing GPU libraries. Dataset admission and use
require real-observation declarations in every split. The experiment seed is
explicit and passed to both Unsloth adapter setup and the trainer configuration.

Checks used the actual retained 44-row provisional training corpus: missing
admission and provisional input both exited 2 without output creation; passing
its manifest as an admitted dataset was rejected. Existing chat rows still parse.
All three changed Python sources parsed successfully. No GPU training, fabricated
dataset or new labels were produced. No positive reviewed training run is claimed:
the needed independently reviewed real dataset is absent. Local declarations do
not cryptographically authenticate reviews or truth.

Original sources, the old plan, exact check hashes and the first native CI failure
are retained in `.swag/evidence/20261029/controller-goal-start/`. These SWAG edits
are local because the workspace has no Git history; they are not engine commits.

PR180 is verified merged at `45a0cd82733abc93a1374796c47bf5d68bd2bbcc` in fetched
main `291fee511887932572ecc9935e9786e098727677`. PR188 was independently returned
to draft at 15:02 UTC with a documented native-failure hold, which is preserved.
One failed-job retry is running on its unchanged head. A current-main merge
preflight identifies one generated-inventory conflict; no merge was performed.
The earlier merge follower stopped on failure and is not represented as active.

## Collector recovery and endpoint-selection contract

The unchanged-source native retry, run `40810426309` attempt two, passed. The
first failed attempt remains retained; a successful retry does not diagnose its
APFS setup failure. PR188 integrated main `291fee511887932572ecc9935e9786e098727677`
and resolved its sole generated-inventory conflict by preserving the landed
retirement marker. New head `d092124039f9902d270b26caa9bce81542e7128e` is pushed.
Collector/review sources and tests are unchanged. Workflow/documentation policy,
navigation, inventory and diff checks passed. A real capture against the existing
PR180 worktree/context emitted one unreviewed record; fresh-process restart emitted
zero. Evidence is `controller-goal-start/integrated-capture.jsonl`.

The draft hold was reconciled; fresh full CI is `40913102114`. The active bounded
exact-head follower is now `collector-main-integration-followthrough/`. Its source
snapshot and events retain the selected revision and normal protected queue.

PR196's separate candidate `db0ae5927848a87a674616f91f5bd06d09778f32` specifies
the missing endpoint-selection capability at the existing LFG/SWAG owner, with
real-data constraints in the training owner and handoffs in Gate G/POAM-009.
Six files changed, all documentation or generated navigation. Documentation,
workflow, navigation, inventory and diff checks passed; candidate CI and landing
remain pending. No public operation, model dispatch, training or fake data was
added. This advances the contract decision, not runtime integration.


## Endpoint-choice validation and actual BF16 wire observations

PR198 contains candidate `63375dd42c77986ea8bd64a9c6034c07af2d3c9a`, pushed
normally to the public development remote. Its journal records the bounded
implementation, eight focused tests, passing full contract suite and strict lint,
actual response provenance, corrections and limitations. No runtime operation or
provider dispatcher is registered. PR196 must land first; its macOS installed
capacity job failed with a bounded metadata-fill panic. The full raw log is
retained under `.swag/evidence/20261029/endpoint-contract-ci-failure/` (SHA-256
`c3dce0a295c930370fb3b18b57d02704dae8e5bae922f4b4798444f233c2a6ce`).
The failure is not diagnosed as infrastructure noise or waived.

Live capture directories `.swag/evidence/20261029/endpoint-choice-live/` and
`endpoint-choice-withheld/` contain actual requests and outputs for the real PR198
maintenance task. Four calls returned HTTP 200. The configured binding was chosen
when supplied; the model abstained when the operator withheld all candidates.
The Rust verifier accepted both. These establish wire compatibility only, not
provider quality, weight attestation, independent review, training admission,
engine authorization or end-to-end execution. No worker was dispatched and no
training labels were invented. Test denial cases perturb those actual inputs in
memory, remain explicitly labelled and are excluded from learning data.

The first owner's real task and correctness rubric remain requested. No reviewed
training dataset exists yet. The goal remains active; native admitted execution,
ordinary-edit replanning, Connectome/RROFLOW integration and qualification are
still required before deployment or 29 GB claims.


## Native selector transport package

PR199 candidate `5ee39f39942f610e4414fec287ce21dbe88b2d8b` is pushed to the
public development branch and remains draft behind PR198/196. The optional
`rrd-inference/endpoint-chat` adapter made actual calls to the configured BF16
service. Six probes retained four valid selections/abstentions and two failures:
100 ms deadline with unknown remote outcome, and cancellation rejecting late
output. This does not prove a remote hard stop. The final raw response digest is
`15683a1a120ca67d4ef7eced30660a9fcab323216ae6253c9af58ae2376faad8`.
The complete local observations are in
`.swag/evidence/20261029/native-controller-chat/`; 39 captured files and their
hash index are also retained in the PR. Final adapter/example/lockfile hashes
match the final live capture. No credentials, invented outputs or training labels
were introduced; denial perturbations are isolated in-memory test inputs.

The owning inference suite passed 33 tests; seven focused checks, strict Clippy,
formatting and documentation/navigation/workflow/inventory checks passed. Review
added a final post-decoding deadline/cancellation check and rejection of legacy
function-call and declared reasoning payloads; actual successful calls were
repeated after those source changes. The example is an operator transport probe,
not an engine-authorized task runner or release binary. Task/source admission,
durable fencing/budgets, UI/RROFLOW integration and reviewed quality remain open.

The previous PR188 follower was confirmed terminal after a cancelled macOS job.
Run 40913102114 attempt 2 was already active, so no duplicate retry was issued.
A new bounded exact-head follower uses
`.swag/evidence/20261029/collector-rerun-followthrough/`; it can only request the
normal protected queue after all required checks pass. PR196 run 40914270128
still has the previously recorded macOS capacity failure. No checks were waived.

## Governed selector-policy configuration

PR201 candidate `2c3f6bff9db9c87731899ebe4640bd3008324799` is pushed to the
public development branch and stays draft behind PR196/198/199. Optional policy
now participates in the existing endpoint-profile approval and persistence path.
Controller/candidate identities, prompt, limits and generation settings are
explicit configuration. Missing policy remains absent; previous profile hashes
are preserved. Changed settings invalidate approval, and revocation invalidates
policy projection.

The embedded engine/store test derives a configuration proposal from retained
actual BF16 settings in a fresh test estate. Preview does not write, tampering
fails, apply/read/replay survives close/reopen, and revocation rejects old plans.
This is not an installed binary test, provider call, accepted learning record or
engine-admitted controller execution. In-memory denial perturbations remain
validation probes and are excluded from training/evaluation data.

Passed: 148 contract tests, 33 inference tests, all five engine configuration
tests, strict Clippy for the affected libraries and engine tests, formatting,
all SDK generation checks, TypeScript typecheck/lint/six tests, generated
surface, documentation, workflow, navigation, inventory and whitespace checks.
The initial borrow error and intentional OpenAPI-digest mismatch were corrected
and are retained in the PR journal. The OpenAPI digest is
`c1c8c59f888c3c1425789feec81c008d3aa0cd0676f6155a526ccd96aca2c606`, with
62 unchanged operations. Local logs and exact push identity are retained under
`.swag/evidence/20261029/controller-policy-configuration/`.

PR196 run 40914270128 attempt 2 is now running after one failed-job retry;
the earlier macOS failure/log is preserved without a root-cause claim. At
18:07 UTC PR188 and PR196 each have 21 successful required checks and a macOS
job still running. A separate bounded exact-head follower for PR196 is retained
under `.swag/evidence/20261029/endpoint-contract-rerun-followthrough/`. Both
followers may request only the normal protected queue after all 23 checks pass.
No new merge, training, model-quality, live-integration or 29 GB claim is made.

## Shared task-attempt admission

PR203 candidate `241509b33941d0e4851e161230a705d04158d44f` is pushed and remains
draft behind PR201 and its dependencies. The existing embedding reservation
delegates to a shared engine-internal admission input and function. It retains
the same persisted budget/attempt records, keys, CAS, deadlines, steps and Stop
behavior. Effect-specific identity preparation retains the original monotonic
start; replay and exhausted/stopped budgets do not resolve an adapter again.

Two new tests use hash-verified actual PR198 task/request bytes in a fresh
embedded test estate. No provider is installed or called. Reservation survives
reopen; conflicting replay fails; an embedding attempt sees that same unresolved
budget; malformed/failed identity preparation creates no budget mutation. Faults
are explicit validation probes, excluded from observations and learning data.

The 14 pre-change budget tests passed; the final owning engine suite passed 306
tests, including all 16 budget cases. Three declared cases remain ignored in that
invocation: attunement/installation subprocess child fixtures and privileged
foreign-owner validation. Strict all-target Clippy, formatting, documentation,
workflow, navigation, inventory and whitespace checks passed. A missing test
`Instant` import surfaced after the timing correction and was fixed before the
final suite; failure and final logs plus exact push identity are retained in
`.swag/evidence/20261029/task-attempt-admission/`. No public schema changed.

PR196 run 40914270128 attempt 2 and PR188 run 40913102114 attempt 2 both completed
successfully with all 23 candidate checks. They entered the normal protected
queue at 18:11 and 18:18 UTC respectively. Merge-group results/landing remain
pending. The first PR188 follower exited after an API connection error; its
terminal exec result was inspected before starting the replacement under
`collector-network-followthrough/`. No CI job was restarted for that network loss.

Typed controller completion/replay, authenticated task/source/capability/credential
admission, worker effects, Connectome/RROFLOW and genuine reviewed data remain
required. These results do not establish a live controller workflow or model
qualification. The full goal remains active.

## Queued collector conflict resolved

PR188's queue entry reported unmergeable even though each branch was mergeable
into main separately. Read-only Git merge-tree reproduced one conflict between
its exact head and PR196: the generated Gate G journal index. The live PR188
follower was stopped, PR188 dequeued normally and returned to draft before repair.
An ordinary merge of PR196 and regeneration resolved the conflict; no collector
or review source changed. Candidate `35112bdba18914b137d28fd65ad2c75b49e2263e`
is pushed. The real collector wrote one unreviewed observation from retained task
context, then a fresh process wrote zero. Local documentation/workflow/navigation/
inventory/diff checks passed. Evidence is retained in
`.swag/evidence/20261029/collector-endpoint-integration/` and its immutable PR journal.

PR196's merge-group run `40928446398` is separate and still pending. Once it
lands, PR188 must refresh current main and pass fresh full candidate checks;
the previous green run cannot qualify this changed head. No collector follower
remains active for the superseded head. No merge, training admission or new live
controller integration is claimed.

## Controller foundation consolidation

PR205 candidate `169b010a714ae7ea09895b2f82504d07ea9ecf0f` now replaces the
sequential landing path for PR198/199/201/203. Those drafts were closed as
superseded only after exact source retention, replacement review and combined
validation; their branches, commits, original journals and captured files remain.
The opening tree exactly matched PR203. Only the consolidation journal and its
generated index link differ in the pushed candidate. A package-specific map
identifies each canonical implementation and its retained tests. All 59 actual
capture files match their indexed hashes.

Combined contract/inference/engine tests passed 487 cases; the same three
declared fixture/privileged cases remain ignored in that invocation. Strict
all-target Clippy, workspace formatting, generated surface parity,
documentation/workflow/navigation/inventory and staged whitespace passed. No
application source, provider configuration, dataset, original evidence or SDK
behavior changed. Evidence is in `.swag/evidence/20261029/controller-foundation/`.
The immutable consolidation journal records the unsupported opening Git option
and successful corrected merge. No required CI gate was waived.

PR205 stays draft until PR196 lands and the refreshed exact candidate passes full
CI. Prior BF16 calls are not relabeled as calls from this candidate. Source-bound
admission, typed completion/replay, worker effects, UI/RROFLOW and independently
reviewed learning remain open. Consolidation is neither a merge nor completion
of the complete controller goal.

## Endpoint-contract landing and controller-operation implementation

PR196 merged as `6bcb136cb94749b581d927c5e05b858874ac8b43` after protected
merge-group run `40928446398` passed. Its bounded follower returned completed.
PR205 was ordinarily refreshed to `5069fbc6067a225ed5c410ba8a1dc8801f718010`;
its complete tree is unchanged from the locally validated consolidation. It is
ready and fresh candidate run `40938462865` is in progress. PR188 refreshed to
`0e8493ec089ad5c3150028d48136c72a7bd71dcb`; the expected tree-equality guard stopped
when older-main SDK privacy changes appeared. Review proved the upstream blobs
match current main, with the workflow preserving the existing collector test.
Collector/review source is unchanged. Capture tests 8, review tests 7 and Windows
privacy checks 4 passed; one POSIX-only check was skipped. Documentation,
navigation, inventory, workflow and whitespace passed. PR188 is ready with
candidate run `40938745913` queued. Neither dependent PR is claimed merged.

PR206's complete-operation brief was published before implementation. Source
commit `917ebb9098aa7cff365317ff76c9cc6de47061b0` adds Rust request, task projection,
packet, proposal and token-usage types at the existing contract owner. The native
chat adapter shares usage validation and now rejects contradictory partial totals
and overflow. It preserves missing measurements as unknown. Its subsequent
history-only dependency refresh gives head
`6e039ce8c36dd978af49f71e140281479809128b`, with unchanged tested tree
`c6b39520d77b45e1a532cd392bce5360163352cc`.

Two focused engine task-projection/tuple tests and all 182 contract/inference
tests passed. Strict all-target Clippy, formatting, generated parity (unchanged
62 operations/OpenAPI), documentation/navigation/inventory/workflow and whitespace
checks passed. The initial missing task-read bound compile error was retained and
fixed by adding an explicit bounded read field. The linked immutable stage journal
records limitations and checks. In-memory tuples based on actual task/provider
records test consistency; they are not persisted engine receipts or causal claims
that the historical provider call used the new packet. No capture bytes, new
training records, review decisions, model outputs or qualification scores were
manufactured.

The public operation, authenticated engine dispatch, credential setup, typed
durable completion and atomic freshness guards remain implementation work in
the same draft. No new provider call or GPU training ran. Worker effects,
ordinary-edit replanning, connected UI/signal flow, independently reviewed
learning and measured deployment/quantization remain open. Retained local records
are under `.swag/evidence/20261029/controller-operation-plan/` and
`.swag/evidence/20261029/after-contract-landing/`.

## Guarded task-attempt completion

PR206 advanced to `a92127e337e4745ca133d30ca13fe09b5ef1ffea`, tree
`459f3b370643d7f4864c68209d11df210a27afe0`. Typed proposals now use the existing
attempt/budget transaction and public readback. Atomic control-byte guards and
runtime-cursor checks prevent stale completion; invalidation preserves spent
effort and the original deadline while permitting fresh eligible admission.
Stop/deadline remain stronger. Uncertain endpoint failures are retained without
automatic retry. No public controller writer/dispatcher is registered.

Five added isolated-engine tests exercise supplied-output persistence/reopen,
same-attempt replay, charged invalidation, actual session/task changes between
check and commit, and cancellation/uncertainty. Supplied tuples reuse real
task/provider fields for bookkeeping tests; they are not evidence of a model
answering those new packets and are excluded from learning. A test-estate reopen
is not an installed-process crash/restart proof.

Full combined tests passed 495 with three declared subprocess/privileged skips.
After strict lint identified a large private output enum, its payloads were boxed;
all 313 engine tests and strict all-target lint then passed. The strengthened
budget suite passed 23 tests. All five SDK generator checks, TypeScript checks and
six tests, surface parity and repository checks passed. OpenAPI changed to
`af8488aa64d477c1b2d6f7c705c5ce131a7b3b15e3f4d04755621dccc6cd2526`; the catalogue
still has 62 operations. Initial visibility/import, console-print and stale-signal
projection failures are retained in the completion-stage journal/logs. An immediate
post-push metadata assertion failed; a fresh read confirmed the expected draft head
before its description was updated. No duplicate push was made.

The exact completion-stage journal is committed in the public draft. Dedicated
authorization, experimental-policy admission, credential resolution, actual
dependency guards and the installed BF16 operation remain next in that package.
PR205/PR188 candidate checks remain in progress. No new training or provider call
ran, and the complete source/worker/UI/signal/learning/delivery goal remains active.

## Installed admission, transport failure and recovery (29 October)

PR205 merged as `47d979b1624a65c342d42a373d3c116534b56482` after candidate
`40938462865` and protected merge-group `40946137720` passed. PR188 remains open
at `584b29a99a642653d39629b1923c92e111df6ca1`; its fresh CI is still running.

PR206 draft head `d365d02891350590aa4495b46fc665ef313aec24` implements dedicated
EndpointPropose/TaskRead/ReasoningWrite authorization, explicit experimental policy,
immutable startup credential mapping, configured native dispatch, transactional
capacity and fresh task/configuration/session/security completion guards.
The public catalogue has 63 operations. Relevant Rust suites, 27 budget tests,
strict lint, SDK parity and repository checks passed after recorded corrections.
A clean native build produced executable SHA256
`7fe07a7198b864a2642c5a9a521e8e13ac7a7d935fd62e8477f2c075fd7680b9`.

The first installed proof stopped at a driver task-open 404 before dispatch.
The corrected driver discovers paths/methods from the actual engine catalogue.
A fresh trial proved unauthorized and missing-credential denial without reservation,
then returned 412 for the authorized proposal: chat transport failed, remote
outcome unknown, retryable false. No successful proposal is claimed. The task
was a bounded projection of the actual PR206 body, not a generated training task.

Later local connection to forwarded port 8084 was refused. A subsequent SSH
attempt required Tailscale reauthentication. Neither fact proves historical
non-dispatch. Recovery reopened the same estate with the identified binary and
read the public attempt/budget without proposal/replay or provider credential
mapping. It retained status stopped, one reserved step, 2,057 ms charged effort,
`execution_may_continue: true`, and `attempt_failed`. Owned servers were stopped;
no capacity or receipt was manually reset. This is actual installed persistence
of uncertainty, not remote cancellation, successful routing or qualification.

Receipts: `.swag/evidence/20261029/installed-controller-proposal/`,
`installed-controller-proposal-discovery/`, `installed-controller-proposal-recovery/`
and `controller-operation-plan/`. Recovery runner SHA256:
`77e25e637ae49beed29aafe00ef396c2f2ffc5a4237db962876ad3501bd60950`.
That driver correction is separate from the source-identified d365 engine binary.
Successful execution, remaining fault cases, CI and integration are pending.
No GPU training, new learning labels or quality scores were created.

The recovery correction and immutable journal were committed/pushed to the public
development remote as `bda5321b79d98cfd704edf01f08d786a98819260`. Two installed
readbacks were identical. Recovery rejects mixed dispatch arguments before
creating any output/process. Syntax, navigation, documentation, inventory,
workflow and whitespace checks passed. PR206 remains draft; its description now
records the failed live call and pending evidence. AGENTS.md remained byte-identical.

## Installed predispatch denial evidence

PR206 head `a8d0bceb6ffaea0ac616769eb89cb969084a7ff4` adds admission-only proof
using the actual d365 binary, real profile and bounded PR206 task. It supplied no
provider credential mapping. Actual outcomes: network-disabled policy 403;
stale configuration 412 InputsChanged; profile revocation 400 profile absent;
closed session 412 SessionExpired. Restoration/reactivation and a process restart
preserved configuration, and fresh requests reached missing-credential 412.
All public budget reads remained absent. Owned processes were stopped. This proves
predispatch denials and restoration, not in-flight cancellation or remote success.

Two mixed-mode argument checks rejected before process/output creation. Recovery
against the original failed estate again preserved exact attempt/budget. Syntax,
navigation/documentation/inventory/workflow and whitespace checks passed. Immutable
engine journal: `controller-task-proposal-installed-denials.md`. Evidence directory:
`.swag/evidence/20261029/installed-controller-admission-denials/`; runner SHA256
`27e9fc99981f2daa1908d5bff9c032a10e295b5e69453633add59490d2fddbd1`.
No model call, new training record or fabricated label was produced. SSH identity
check and PR188 macOS candidate job remain pending; full goal stays active.

## Resumed access and protected capture landing

On owner resume at 21:46 UTC, PR188 candidate `40948411087` was verified complete
and successful for exact head `584b29a99a642653d39629b1923c92e111df6ca1`.
An enqueue request returned already queued. Authoritative queue state is position 1,
AWAITING_CHECKS, merge head `2e6ab88ed08340b61513b2b6c3828b202369c49d` based on
landed PR205. Protected run `40957233182` is in progress; no merge is claimed.
The queue/run was preserved. Records are in `after-contract-landing/` under
`pr188-enqueue-qualified.json` and `pr188-queue-resumed.json`.

Old SSH observation 55133 terminated with failed next-action retrieval/connection
closed. A fresh connection using the documented route, observation 69659, requires
a new Tailscale identity check. Local forwarded port 8084 has no listener. The
owner has the fresh link; no authentication bypass or provider call occurred.
The resumed goal remains active; the prior blocked audit is historical.

## Restored access and actual installed BF16/fault proof

At 23:16 UTC the owner's Tailscale identity check succeeded. The existing custom
container remained running; authenticated discovery/health passed and metrics
showed zero active/waiting requests. Owned SSH forward PID 95740 restored port8084.
A separate bounded trial preserved the earlier uncertain estate.

The d365 native binary returned a real typed proposal: HTTP200, reported 1,797
input/26 output tokens, 2,362ms adapter time. Restart readback was identical,
same-attempt replay rejected, one step charged. Provider success counters increased
43 to44 during that trial. This single-candidate observation is not routing quality
or latency qualification.

A repository-owned bounded relay forwarded actual engine request bytes and held
or dropped actual provider response bytes. Configuration change invalidated the
old result; a fresh request on the same task succeeded with both steps and original
deadline retained. Session closure invalidated completion. Stop and lost response
retained stopped state and conservative uncertainty through restart. All four
histories passed; six actual provider calls total including the baseline. Stop
was exercised after remote response receipt, not as GPU termination. No training
records/labels/consent or fabricated model output were introduced.

PR206 live-stage commit `f89c358b` publishes 33 exact public/provider receipts with
hash manifest, token/credential exclusion and local captured-byte Git attributes.
The first whitespace check flagged CRLF; matching the existing capture policy
preserved exact bytes instead of normalizing evidence. All final repository checks
passed. Ordinary main merge produced `54fb845dffd702e1504c7f9a0cc2a3c5757d2bf2`
without conflicts; runtime crates/SDKs/Cargo inputs equal d365. Capture8 and cache
policy3 tests passed. An immediate post-push metadata assertion saw stale GitHub
state; a fresh read confirmed the exact head and no duplicate push occurred.
PR206 is ready for review and full CI; it is not merged. PR188 has merged through
protected run40957233182 as `2e6ab88ed08340b61513b2b6c3828b202369c49d`.

Evidence remains in `installed-controller-proposal-connected/`,
`installed-controller-fault-*/`, `controller-access-restored/`, and
`controller-operation-plan/` under `.swag/evidence/20261029/`. Full task/worker/UI/
signal/learning integration, test distribution and memory qualification remain open.

## Optimized portable Windows engineering trial, 2026-10-30 UTC

The two-pass release build at source `54fb845dffd702e1504c7f9a0cc2a3c5757d2bf2`
produced executable SHA256 `fb9b5727e6ea0de668c723e63d008bfd976a02ca020aad218b122b61142afee0`
(113,481,216 bytes). The outer PowerShell wrapper reported 1 for native stderr
progress; the build log ends with an accepted receipt. Independent version,
hash and clean-source checks passed. This shell result was retained.

Assembly source `98d0de932fecce1a3103c31cb9bab75712a62d48` produced the 33,850,986-byte
ZIP, SHA256 `46b85f824d712cd8e8cceda4a6b0cd01bb1585f3f25a1f8c64ef8b7657f05b6f`.
Assembly exited 0. Eighteen checks passed, including six against the actual ZIP
and corrupted copies. All extracted hashes matched. The packaged trial completed
an actual BF16 proposal: 1,805 reported prompt tokens, 20 output tokens, 1,879 ms,
restart equality and replay rejection. This single-candidate observation is not
a performance/quality comparison. Primary readiness and quick verification passed
with no provider credentials and only System32 on the child PATH.

Session, Stop and disconnect actual-response cases passed. Configuration
replacement invalidated the first output, but the fresh model response selected
unsupported effort `observed`. The engine rejected it with HTTP 412. The case
failed and was not retried or repaired. Credential-free recovery retained the
original invalidated attempt and current budget: two spent steps, 4,688 ms charged,
stopped/attempt-failed and conservative uncertainty. Recovery did not separately
read the successor attempt. Six release-trial calls created no training data or
consent. This real failure remains a model qualification gap.

[Testing instructions and artifact](testing-binary.md). PR212 contains fourteen
exact public receipts and hashes; the legacy checkpoint remains provisional.
PR206's first full candidate run passed, but protected enqueue reported its
required aggregate check expected. The actual aggregate rerun also passed without
clearing that rejection. Fresh eligible run `40978912042` passed all 23 jobs on
the same head; protected enqueue succeeded at 00:53 UTC, position 1. Automatic
merge was rejected as disabled before that success. No bypass or check fabrication.
Protected integration, signed releases, container delivery and the complete
project/UI/learning journey remain open.
