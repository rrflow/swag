# ADR: Qualify SWAG through observed development outcomes

**Status:** Offline outcome admission, training-input integration, protocol runner
and comparison implemented; live research and product acceptance pending.
**Date:** 2026-11-02.
**Deciders:** Product owner for task acceptance and data permission; the existing
RRFlow, Connectome and RROFLOW owners for their integration changes.
This is an experiment plan, not independent senior-engineer approval.

## Owner's five milestones

| Milestone | Implementation and exit evidence | Current boundary |
|---|---|---|
| 1. Complete a real development task through the UI | Use this requested SWAG outcome-research implementation as the proposed real work item. Through the public UI, preview/accept an engine plan, execute a governed project change, make an ordinary relevant edit, accept scoped replanning, inspect changed files and checks, restart, and recover the same receipts without duplicate effects. Correlate task, attempt, source, configuration and RROFLOW event. | Shell edits in this change do not satisfy UI acceptance. Observation PR235 merged with successful protected CI; worker PR229 and discovery PR248 remain drafts at inspection. Current Connectome integration and governed project effects remain necessary. |
| 2. Collect independently reviewed comparable outcomes | Preserve every authorized attempt and its actual output, verification, timing and unknown costs. Compare model/effort options against the same task, source, criteria and configuration. Independent reviewers adjudicate success and handoff validity separately; retain uncertainty and separate consent. | The single-candidate proposal receipt cannot populate this dataset. No paired real reviewed outcomes have been supplied or admitted here. |
| 3. Train suitability and handoff decisions | Export separate `task_success` and `handoff_valid` objectives. Unsloth consumes only the selected admitted train/development bytes. Freeze base revision, seed, recipe and data identities; retain failed runs and evaluate fresh reloads. | Implemented input path; no new GPU training. The historical title-classification checkpoint remains provisional. |
| 4. Compare four arms on unseen tasks | Original Qwen BF16, custom BF16, exactly its quantized derivative, and an explicitly configured small baseline share each objective's frozen protocol. Retain every timeout/invalid output; test candidate order and measure uncertainty. | Runner and comparison implemented; no new live comparison. No default model or provider ranking. |
| 5. Measure total serving memory | Bind measurements to the actual serving process, loaded artifact and workload protocol; measure idle, representative context/concurrency and peak sustained load. Report weights, KV/cache, runtime and host/device accounting separately. | Comparison rejects missing evidence. Neither 29 GB nor release readiness is established. |

## Research basis and hypotheses

- [RouteLLM](https://arxiv.org/html/2406.18665v4) learns quality/cost routing from
  preference data. Our adaptation tests observed development-task success, with
  preference and permission remaining distinct. We do not import its generated
  data or assume its published savings transfer to SWAG.
- [Arch-Router](https://arxiv.org/html/2506.16655v1) investigates domain/action
  preferences and newly introduced models. Test configurable candidate descriptions,
  unseen bindings and opaque identifier permutations; a user's preference is not
  evidence that the chosen output was correct.
- [Liquid d1](https://www.liquid.ai/blog/d1-open) reports single-pass decisions and
  benefits from answer shuffling and removing data shortcuts. Compare a pinned
  small decision model, with its native API adapter when required. A chat-compatible
  small baseline can use this runner; a native d1 adapter is not implemented here.
- [Liquid RIPL](https://www.liquid.ai/blog/low-latency) reports serving results for
  Liquid models. Qwen compatibility, GB10 suitability and transferable speedups
  remain unestablished. Hold model and precision constant when comparing runtimes.

H1: observed outcomes improve task-success selection over simple baselines.
H2: separate handoff supervision reduces downstream handoff failures.
H3: a smaller specialist preserves required success at lower measured latency/memory.
H4: quantization of the same custom checkpoint stays within frozen quality margins.
Each hypothesis needs held-out measurements; a successful build cannot confirm it.

## Decision and alternatives

Keep the existing bounded selector as a deterministic policy baseline. Its
supplied quality scores and cheapest-eligible labels do not become ground truth
for task suitability. Add an independent observed-outcome dataset and evaluator.
The learner sees task intent, acceptance criteria and configured model/effort
descriptions. Handoff evaluation additionally sees the proposed handoff. It never
sees output verification, reviewer rationales, timing or measured costs as input.

Compare this with training the old selector alone (simpler, but fails to test our
core hypothesis), and training on PR-title intent labels (available, but no provider
outcome attribution). Neither is sufficient for the requested controller.

Binary observed targets supervise probability predictions; predictions are not
calibrated confidence. Evaluate Brier score and risk/coverage, then fit calibration
on development data only in a later package. The current offline decision policy
selects a unique maximum above an explicit threshold and abstains on ties. It is
an evaluation policy, not a provider ranking or RRFlow execution permission.

## Experiment controls

Freeze split membership, thresholds, relative regression margins, prompt, source
hashes, artifact lineage and memory target before acceptance inference. Split by
repository/project and time; related tasks share leakage groups. Never train on
acceptance labels or reclassify exposed tasks as unseen by renaming them.

Run the same task against eligible alternatives from equivalent starting states,
with separately authorized budgets. Record failed/cancelled attempts and missing
reviews. One outcome is one observation, not a model's true success probability.
Collect repetitions under a declared sampling plan before estimating provider
strength. Human review should be blind to provider identity where practicable;
check disagreements rather than converting preferences automatically to labels.

Primary outcome: selected option satisfies the task criteria. Report abstention,
coverage, conditional failure risk, invalid responses and Brier score separately.
Original/reversed candidate order is implemented; repetitions do not increase the
independent task count. Wilson intervals are descriptive and assume independent
tasks. Project-cluster bootstrap, opaque-ID permutations, unseen-binding tests,
simple learned baselines and calibrated risk/coverage sweeps remain follow-ups.
Determine required sample size and practically meaningful margins with the owner
before freezing; no invented accuracy target or statistically sufficient count.

For memory, `29 GB` means 29,000,000,000 bytes unless the owner explicitly changes
the target before freezing. On unified-memory hardware, document non-overlapping
accounting; do not add overlapping host RSS and GPU allocations. Weight file size,
training allocator peaks and idle residency cannot prove total serving footprint.

## Implementation sequence and remaining integration

1. **This package:** strict outcome/review JSONL, independently reviewed admission,
   separate training objectives, frozen endpoint evaluation, four-arm comparison,
   and UI/MCP dataset status. Run negative-path and transport tests. No generated
   research examples, live training or automatic promotion.
2. **Engine/UI task acceptance:** reconcile and land matching owner PRs; add the
   missing governed project-effect operation through existing engine owners. Bind
   relevant inputs, invalidate only affected work, preserve spent budgets and
   committed effects, and prevent duplicate execution after restart. Submit real
   user-visible artifact evidence for independent review.
3. **Collection/review adapter:** map native receipts to the documented normalized
   observation envelope, retain native artifacts, and expose paired review through
   the existing public engine/Connectome interface. The Python CLI is an offline
   research consumer; it does not execute project work or forge engine receipts.
4. **Research execution:** review real attempts, grant dataset use explicitly,
   freeze recipes/protocols, train custom BF16, verify fresh reload, run all four
   arms, calibrate on development, then measure serving resources under load.
5. **Learning routines and packaging:** engine-owned failure/drift routines may
   propose reviews with deduplication/cooldowns; unsupervised signals create no
   correctness labels. Training and promotion need admitted data and engine
   authorization. Qualify rollback, native bundle and image separately.

Follow [the runnable outcome workflow](task-outcome-workflow.md). Existing
integration evidence and historical failures remain unchanged. No milestone closes
until its owning PRs and the relevant real-workload evidence exist.
