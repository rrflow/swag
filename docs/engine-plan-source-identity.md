# Engine-owned planning and custom checkpoint qualification

## Status and authority

Supporting design proposal, updated 2026-10-28. See [current context](current-context.md)
for the running private BF16 baseline. This design does not establish engine
integration, custom-checkpoint qualification, or roadmap completion.

`RrdEngine` owns accepted plans, source snapshots, authorization, budgets,
configuration revisions, effect admission, and durable receipts. SWAG proposes
decisions; clients display and submit proposals; RROFLOW supplies outcome evidence.
Neither a Python manifest, a model answer, nor a client status becomes a second
plan or lifecycle authority.

This proposal was grounded against RRFlow checkout revision
`dd225072bcc639c89b0eef968625cc73303ea998`, specifically:

- `docs/reference/agent-bootstrap.md`: inventory and project-operation preflight.
- `docs/architecture/engine-data-flow.md`: project-tree inventory and incremental attunement.
- `docs/reference/inference/lfg-swag.md`: proposal, admission, and configuration ownership.
- `docs/reference/inference/learning/controller-training.md`: artifact qualification and promotion.
- `crates/authority/rrd-engine/src/engine/installation.rs`: existing installation digest preconditions.

These paths identify the engine's owning records, not runtime dependencies on a
sibling checkout. Its README, objectives, roadmap, and POA&M remain authoritative.
Implementation must extend those owners through reviewed engine PRs. This file is
a handoff proposal, not another delivery ledger. The checkpoint experiment may
proceed offline before integration, with its status explicitly limited to that scope.

## Next milestone: one versioned custom checkpoint behind an endpoint

Qualify one custom Qwen-derived controller candidate using three comparisons:

| Arm | Exact artifact | What the comparison establishes |
|---|---|---|
| A: original Qwen | Pinned base weights, tokenizer, and chat template | Baseline decision behavior |
| B: custom before quantization | That base plus the selected adapter, merged and freshly reloaded | Training effect: B versus A |
| C: custom after quantization | Quantization of exactly B, freshly reloaded | Quantization effect: C versus B; total result: C versus A |

The selected base is `Qwen/Qwen3-Coder-30B-A3B-Instruct`, pinned to
`b2cff646eb4bb1d68355c01b18ae02e7cf42d120`. Start with BF16 A, then train and
evaluate custom BF16 B before quantizing exactly B into C. A public quantized
base cannot stand in for C. The baseline matched 4/8 synthetic smoke cases;
these observed cases are not an acceptance holdout. Earlier Qwen2.5 adapters and
the rejected 1.5B pilot are separate experiments, not this candidate's lineage.

Produce an immutable artifact manifest binding base revision and file digests,
adapter/configuration digests, training export and split digests, trainer revision,
dependency lock, merge procedure, merged shards, tokenizer/template, conversion and
quantization tools/settings, calibration inputs if used, and final artifact digests.
Keep unavailable identities explicitly missing; do not fill them with aliases.

Use the same independently labelled, project/time-separated cases, policy,
eligible choices, prompt, output schema, token limits, and scoring rules for all
three arms. Freeze the protocol before seeing acceptance results. Keep the
deterministic policy baseline alongside the three model arms. Measure incorrect
approvals, incorrect rejections, unauthorized selections, invalid output,
abstention, downstream task outcomes, and per-family counts and uncertainty.
An all-abstaining candidate cannot pass on low violation count alone.

Measure cold/warm decision latency, p50/p95, throughput at declared concurrency,
and peak process/GPU memory with hardware, context length, runtime and sampling
method. The proposed footprint gate is at most **29,000,000,000 bytes** for the
serving workload at a declared context and concurrency, not just the weight file.
This is the later compression target; BF16 A and B may exceed it.
Report host RAM and GPU allocations separately on discrete hardware; on unified
memory avoid double-counting shared allocations. Include server overhead and KV
cache, disclose offload, and record baseline host usage. Training memory is separate.
Q6 is a candidate, not a prequalified solution. Numerical quality/noninferiority
margins and latency limits must be agreed and frozen before acceptance runs;
unfilled limits mean qualification is pending, never an automatic pass.

Serve the candidate under an immutable artifact revision. A friendly alias may
resolve to it, but each accepted response/receipt must bind the resolved artifact,
runtime and effective configuration identities. A configured alias or a health
response alone is not proof of the loaded weights: retain verified file-load
evidence, startup identity, and a fresh-process inference probe. If the backend
cannot attest identity, record that limitation and withhold qualification.
Evaluate sequentially on the same host where necessary; a stable service address
does not require all three models resident together.

Engine admission must independently check schema, eligible selections, policy,
permissions, locality, remaining budget and endpoint revision. A candidate may
abstain; it cannot grant itself authority. Preserve the existing separation between
endpoint selection and recipe/branch/context `RouteStepDecision` proposals.

## Source identity: stable object, changing revision

The following are proposed semantics to map onto existing engine types, not a new
wire schema or parallel database:

| Identity | Meaning |
|---|---|
| Project/estate identity | Stable identity of the authorized project; ordinary edits do not change it |
| Source identity | Stable source reference within its authority; a path or model alias alone is insufficient |
| Source revision | Exact captured bytes plus relevant type/mode/link semantics and acquisition provenance |
| Snapshot/read identity | Authorized scope, inventory policy revision, entries, coverage and read stamp |
| Plan identity and revision | Stable work objective with immutable successive proposals; each references its parent and inputs |
| Effect identity | One admitted action and its idempotency identity, dispatch state and receipt |
| Evidence identity | Inputs, evaluator/runtime, protocol and output digests for a particular observation |

Use versioned canonical encoding and domain-separated SHA-256 digests. Define
sorting, path encoding and platform case rules at the inventory owner. Hash actual
working bytes: a Git commit is useful provenance but cannot identify dirty or
untracked inputs. Include authorized non-Git projects. Record absent paths and
directory/glob membership dependencies so a newly added file can invalidate an
assumption even when previously read files are unchanged. Incomplete scans cannot
claim complete coverage. Unreadable files are unknown, not absent.

Record dependencies on effective policy, instructions, project goal, task request,
templates, tool/runtime versions, endpoint configuration and external revisions as
well as files. Keep the persistent project goal and current task separate. Relevant
external data needs a verified revision/content identity and freshness policy;
an unchanged URL does not establish unchanged content. Credential references and
authorization revisions belong in protected records; secret values do not.

Inventory excludes engine-owned journals, caches and generated observations by
explicit policy to avoid self-invalidating loops. Generated project source remains
an input when consumed by later work. Bind exclusion policy to the snapshot and
test it; excluding everything that changes would defeat validation. Enforce root,
symlink and authorization boundaries before reading or hashing.

Map file identity to the existing estate plus normalized root-relative path contract.
A rename can therefore produce old/new entry identities with a supported rename
relationship; it need not preserve an invented global file identifier. Content
equality alone does not establish ownership or authorization.

## Detect changes and replan without trapping the project

1. **Observe.** Explicit refresh invokes the engine's bounded inventory capability.
   Future filesystem notifications are authenticated hints only, after their Gate I
   boundary exists. File size/mtime and Git status may accelerate discovery but
   cannot certify unchanged content; revalidate relevant bytes at effect admission.
2. **Capture.** Produce a consistent snapshot or report incomplete/unstable input.
   Detect files changing during capture; retry within the existing budget. Compare
   entry, membership and configuration identities to produce a change set.
3. **Scope invalidation.** Mark affected proposals and derived evidence stale by
   dependency intersection, including transitive and absence dependencies. Preserve
   unrelated work and immutable past receipts. Unknown dependency coverage requires
   conservative invalidation of that operation, not permanent project rejection.
4. **Propose a successor.** Keep the project and objective identities. Create a new
   immutable plan revision with the current snapshot, changed inputs, affected
   actions and reuse rationale. Preserve already accepted effects; reuse computed
   results only when their full dependency and authorization identities still hold.
5. **Admit explicitly.** Apply never substitutes a new digest for the one accepted.
   Recheck expected plan/configuration revisions with CAS, current permissions and
   remaining budget. Existing explicit policy may authorize bounded replanning and
   application; otherwise present the concrete revised effects for authorization.
   An edit does not automatically widen permissions or reset spending/deadlines.
6. **Commit and continue.** Revalidate input and target preconditions at the mutation
   boundary. Use qualified atomic/conditional application or an isolated immutable
   input snapshot; a hash followed by an unprotected write is insufficient. After
   a project mutation, re-inventory before treating derived state as current.

The current inventory design permits metadata-based reuse and zero-content-read
no-work refreshes. The source-identity PR must reconcile that optimization with
same-size/mtime changes: cached metadata is an observation, while freshness for an
effect requires re-reading its relevant dependencies or a qualified immutable
snapshot. Do not claim that today's metadata optimization proves this stronger
precondition. Preserve bounded scope rather than rehashing every project for every
exploratory request.

An old proposal remains inspectable as superseded or stale. A rejected stale apply
returns a structured changed-input result and a refresh/replan path. Refresh must
accept the stable authorized project identity and current source, without requiring
the obsolete snapshot digest to match. Installation ownership checks stay strict;
an installed project's creation snapshot must not become a permanent equality
condition for ordinary project access. No reinstall, clean Git tree, deleted state,
or discarded user edit is the recovery procedure.

Concurrent planners publish through expected-revision checks: one wins; the other
refreshes and proposes again within a bounded allowance. Continuous edits report
that affected work is waiting for stable inputs, with retry/cancel available; other
inspection and unaffected work remain usable. Do not spin or mark the whole project
failed. A reverted file may recover a reusable content identity, but history and
current authorization are still checked.

Already dispatched external effects require reconciliation, not blind replay. A
timeout or lost response is an uncertain outcome; query the original effect's
receipt/idempotency state before retrying. Restart restores accepted plan revisions,
effect identities and remaining budgets. Replanning cannot erase an uncertain call
or issue a fresh identity to repeat it unnoticed.

## Change impact for the checkpoint milestone

| Changed input | Required response |
|---|---|
| Unrelated documentation outside declared dependencies | Keep checkpoint/evaluation evidence; record current inventory |
| Project goal, task policy, prompt or output grammar | Replan affected decisions and rerun applicable evaluations |
| Training labels, split, base or adapter bytes | New candidate lineage; invalidate dependent merge, quantization and scores |
| Merge code or tokenizer/template | Rebuild/reload affected artifacts and rerun B/C comparisons |
| Quantization settings/calibration data | New C artifact; keep valid A/B evidence only under the same protocol |
| Evaluation labels, scorer or acceptance limits | New protocol revision; rescore retained outputs only where valid, otherwise rerun; disclose prior exposure |
| Serving runtime, context, concurrency or hardware | Requalify affected quality/resource evidence; weights need not be retrained |
| Endpoint credentials, permissions or binding | Re-admit affected calls; no automatic retraining or new sharing permission |

## PR boundaries and required evidence

Proposed packages below are not PRs. Assign actual links and exact candidate SHAs
in the engine's existing owning records when opened; no PR number or merge status
is inferred here. Relevant engine source belongs in `rrflow/rrflow-development`.

| Package | Scope | Acceptance evidence |
|---|---|---|
| Source identity and successor plans | Existing inventory, read-stamp and revision/CAS boundaries | Relevant edit rejects stale apply; refresh creates an admissible successor without reinstall; unrelated edit preserves reusable work |
| Offline checkpoint qualification | Pinned exports, merge/quantization and three-arm harness under the existing learning owner | Fresh reload of A/B/C; lineage/digest checks; held-out quality and measured memory/latency report; rejected candidates retained |
| Endpoint admission and execution | Existing endpoint/model contracts and engine dispatch | Actual loaded artifact matches receipt; malformed/out-of-set output denied; budgets, revocation, failure and restart exercised |
| Outcome evidence and reversible promotion | Engine-owned promotion plus optional RROFLOW public-contract adapter | Correlated real decision/action/verification; deduplicated ingest; authorized CAS promotion and rollback, including interrupted/uncertain effects |

The source-identity acceptance corpus must also cover add/delete/rename, absent-file
creation, same-size/mtime edits, ignored versus relevant generated files, changing
ignore policy, non-Git projects, unreadable/unstable files, symlink escape, concurrent
planners, policy revocation, restart, continuous edits, and no budget reset. Prove a
later valid operation succeeds after each recoverable rejection. A test that only
shows stale work is denied does not prove recovery.

The milestone is complete only when the versioned custom checkpoint serves real
requests and the frozen three-way qualification gates pass with retained evidence.
Engine integration additionally requires the relevant landed PRs, passing candidate
CI, and a real engine receipt for that exact artifact/configuration. RROFLOW
integration additionally requires real accepted/retrieved correlated outcomes.
Local mocks, documentation, generated runbooks, training loss, and a listening port
do not satisfy those claims.
