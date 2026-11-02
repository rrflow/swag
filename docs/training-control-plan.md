# ADR: Evidence-bound training controls

**Status:** Integration proposed; offline adapter package implemented with local
software validation. Engine activity and GPU acceptance remain open.
**Date:** 2026-11-02
**Deciders:** Repository owner for training and promotion; RRFlow's existing
G-06/I-03 owners for engine acceptance. This document cannot close their gates.

## Context and inspected boundaries

SWAG PR1 provides diagnostics, not a training executor. RRFlow accepted main
`e6f3632b` still marks I-03 durable routines/activities unimplemented. Its
`docs/reference/inference/learning/controller-training.md` requires engine-owned
admission, budgets, durable receipts and reconciliation. No generic training-job
operation was found in the executable catalogue. Observation sender PR235 is
still open and conflicted; it cannot supply accepted delivery evidence.

The Unsloth CLI already verifies a reviewed export before GPU imports and saves
optimizer-capable checkpoints, but has no structured progress/interruption
projection or explicit artifact verification interface for the UI. Its BF16
exporter also embeds one historical model name. The retained run used provisional
labels; it cannot authorize new training. Spark inspection currently needs a
renewed Tailscale SSH identity check.

## Research and decision

- [Transformers Trainer](https://huggingface.co/docs/transformers/main_classes/trainer)
  distinguishes model export from training resume: optimizer, scheduler and RNG
  state are required; `save_only_model` prevents full resume. Bind selected
  checkpoint bytes, input identity and runtime before loading. Never infer resume
  capability from an adapter file or choose an arbitrary latest directory.
- [Transformers callbacks](https://huggingface.co/docs/transformers/main_classes/callback)
  expose actual trainer state and cooperative stop/save controls. Report observed
  steps and numeric metrics; a stopped loop is not successful completion. A hard
  process kill may leave no terminal observation and must remain unresolved.
- [Unsloth checkpoint guidance](https://unsloth.ai/docs/basics/finetuning-from-last-checkpoint)
  uses Trainer checkpoints. Reuse that mechanism rather than inventing a second
  checkpoint format for model/optimizer tensors.
- [OpenTelemetry logs](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
  distinguish event and observation time and correlate trace/span IDs. Keep
  diagnostic records content-free; local observations do not become engine receipts.

Choose a bounded trainer adapter with verifiable observations, consumed by the
existing UI/MCP read model. Reject a Python job queue or browser-owned lifecycle:
it would duplicate the engine authority and make restart/retry unsafe. A managed
external training service is a possible future activity binding, not a substitute
for permission or outcome reconciliation.

## Execution packages and acceptance

1. **SWAG trainer/artifact evidence.** Remove fixed model naming; verify bounded
   manifests and source identities without deserializing tensor/pickle files.
   Surface actual saved progress and explicit incomplete/invalid states in the UI.
   Add content-free trainer observations and distinguish interruption from success.
   Prove tamper, partial-write, stale-input and failure handling in software tests;
   inspect actual retained artifacts when cluster access is restored. Engineering
   fixtures are never training or qualification data.
2. **RRFlow generic activity admission and recovery.** Under I-03, bind explicit
   adapter/runtime, exact input/configuration/artifact digests, permissions, limits,
   idempotency and attempt fences. Persist prepare before dispatch. Expose read,
   cancel and reconcile through generated public operations. Test all crash gaps,
   revocation and duplicate outcomes before adding training as a binding. Do not
   make a training-specific scheduler or silently retry uncertain GPU work.
3. **Connectome/SWAG controls.** Consume the accepted generated API; launch/cancel
   controls submit engine operations, never shell commands. Ordinary unrelated
   project edits do not invalidate a training input. Changed relevant bytes require
   a fresh scoped proposal; they never lock the project or rewrite a prior run.
4. **Reviewed BF16 run and qualification.** Obtain independent real routing labels
   and explicit dataset/training permission. Freeze a reproducible recipe and
   acceptance protocol; compare original, custom BF16 and its quantized derivative
   with actual latency, violations, task outcomes and serving memory. Preserve
   failures and separate training peak memory from the 29 GB serving target.
5. **RROFLOW delivery and improvement.** Use accepted engine delivery with bounded
   retry/readback and correlation. Signals may propose review; no fabricated labels,
   automatic training, promotion or subscription-usage assumptions.

## Stop conditions and trade-offs

Missing review or access stops only dependent training/verification. Missing engine
activity support keeps UI launch unavailable while offline adapter work proceeds.
Corrupt or changed artifacts reject verification before model loading. Strict byte
verification costs disk I/O, so run it explicitly and show its timestamp/digest;
do not rehash tens of gigabytes on every UI refresh or imply a saved receipt is a
fresh verification. Research is guidance, not proof of GPU compatibility or quality.
