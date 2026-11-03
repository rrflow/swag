# Research: a 9–12 GB SWAG decision controller

**Reviewed:** 3 November 2026. **Status:** research-backed candidate direction;
no compressed SWAG checkpoint or equivalent-quality result is claimed.

The owner's target is a specialized System One router answering three gates,
with RRFlow owning plans and execution. A 9–12 GB serving candidate is plausible
enough to test directly. Preserve the BF16 reference and the existing 29/15 GB
milestones, but do not require every intermediate footprint before investigating
the smaller candidate. Equal quality means comparable real gate outcomes within
predeclared margins, not equal general-purpose language capability.

## What the primary sources establish

| Evidence | Result and relevance | Limit |
| --- | --- | --- |
| [Cerebras Qwen3-Coder-REAP-25B-A3B](https://huggingface.co/cerebras/Qwen3-Coder-REAP-25B-A3B) | Prunes 20% of experts from SWAG's original Qwen3-Coder-30B base. Reported LiveCodeBench remains 35.2; BFCL overall changes from 63.2 to 62.2. A real compatible-family structural-compression precedent. | A different checkpoint, not our custom weights; neither 9–12 GB total memory nor unchanged quality on every task. |
| [REAP paper, appendix E/table A5](https://arxiv.org/html/2510.13999v3) | Qwen3-30B-A3B with four-bit weights and half its experts retains 77.6 EvalPlus versus 81.4 BF16, at approximately 12.5% relative checkpoint size. Pruning and quantization compose. | This is the non-Coder model and an approximate checkpoint-size result. It shows a quality loss, not equivalence. |
| [LLM Compressor REAP implementation](https://docs.vllm.ai/projects/llm-compressor/en/latest/examples/reap_expert_pruning/) | Provides calibration, expert saliency and physical pruning. Its Qwen3-30B example reports 0.9653 strict GSM8K-Platinum versus 0.9672 baseline at 50% pruning. | One task with a different model variant; no SWAG/GB10 validation. Pin code, calibration and kernel versions before use. |
| [Liquid d1](https://www.liquid.ai/blog/d1-open) and [Arch-Router](https://arxiv.org/abs/2506.16655) | Liquid reports a 3B single-forward-pass decision model matching a 35B-A3B decision model on its public index. Arch-Router uses 1.5B parameters for preference-aligned routing. | Vendor/paper results on their tasks; preference matching is not independently verified development-task success. |
| [SeqMoE](https://arxiv.org/abs/2609.12978) | Investigates predictive expert caching/prefetch and graph-compatible offloading. Supports testing selective residency rather than loading all experts. | Accelerator residency is not total system memory; transfer delays and cache misses require measurement. |

A useful countercheck is the [MoE structural-pruning preprint](https://arxiv.org/pdf/2606.18304),
page 7/table 6: Qwen3's 25%-pruned four-bit entry lists **11.64 GB storage but
17.90 GB runtime memory**. Its 5.27× headline must not be cited as proof of a
roughly 11 GB complete serving system. The draft also contains incomplete table
labels; treat it as exploratory evidence, not a reproducible SWAG qualification.

## What custom shards need to do

File sharding is packaging. Expert-aware residency is a runtime policy. Physical
pruning changes the network. Quantization changes representation. Distillation
trains a smaller network. Measure each mechanism separately before composing them.

Do not assign a third of the existing experts to each application gate: native
MoE routing is learned per token/layer and does not establish that partition.
Profile actual gate inputs, including rare errors and ordinary source edits.
Compare one shared backbone with small decision heads against learned specialist
subsets; three copies of the backbone would defeat the memory objective.

For exact selective loading, retain every expert the native router requests;
cache misses load the real weights rather than silently skipping computation.
For approximate pruning, retain a new architecture and expert-remapping manifest
and evaluate it as a separate derivative. Never relabel it as the unchanged
same-checkpoint quantized arm.

An illustrative 16–20B retained-parameter model needs 8–10 GB of ideal four-bit
weight storage; scales, remaining high-precision tensors, activations, cache and
runtime raise that number. This arithmetic motivates the target, not a measured
budget. A smaller decision student provides another route with more headroom.
Short answers reduce decode work; long input processing can still dominate.

## Candidate experiments and developer-build acceptance

1. **Bind the gates.** Obtain the owner's exact three gate definitions and map
   inputs, outputs, abstention and failure costs to versioned public contracts.
   Keep deterministic permission enforcement in RRFlow. Gate names and candidate
   choices are configuration, not invented model labels or hardcoded rankings.
2. **Measure the unchanged teacher.** Use admitted real task inputs to capture
   per-layer expert contribution, gate coverage and input lengths. Keep profiling
   separate from correctness labels. The repeated title load test is a runtime
   check and cannot serve as unseen gate acceptance.
3. **Compare compression mechanisms on development data.** Establish four-bit
   quantization alone, then calibrated expert/channel pruning plus quantization.
   Test recovery training only with admitted data. Compare a small decision model
   separately. Preserve original BF16, custom BF16 and its unpruned quantized
   derivative in the required four-arm study; use a separate extended protocol
   for pruned and distilled candidates.
4. **Add selective loading if residency remains limiting.** Bind shard hashes,
   tensor/expert mappings, precision and cache policy to one artifact version.
   RRFlow owns job admission and lifecycle; the inference backend executes kernels,
   scheduling and prefetch. Test cold misses, restart, eviction and integrity
   failures. Loading from CPU RAM on Spark still consumes its unified memory.
5. **Freeze and qualify.** Measure each gate and the combined task on unseen
   project/time splits, with independently reviewed outcomes. Compare error costs,
   abstention/coverage, calibration, paired uncertainty, p95/p99 and throughput.
   Select one explicit decimal-byte limit (9 or 12 billion) before acceptance.
   Report total serving residency, disk storage, transfer volume and fallback
   resources separately; include runtime, allocator reserve, buffers and cache
   without double-counting unified pages. A remote teacher fallback does not
   establish a self-contained 9–12 GB build.
6. **Ship one reversible candidate.** The UI must expose artifact/recipe identity,
   gate decisions, abstentions, memory/latency and correlated RRFlow/RROFLOW receipts.
   Prove an ordinary edit triggers scoped replanning and verified project effects.
   Promotion needs quality and developer-build evidence, not a smaller file alone.

Near-term priority: calibrated pruning plus four-bit quantization and a small
decision-model comparison. Custom paging follows measured need; it is not a
prerequisite for trying a compact controller. No training dataset, gate semantics,
quality margin or working kernel is fabricated by this research note.
