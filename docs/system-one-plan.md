# SWAG System One controller: product plan

**Date:** 13 November 2026. **Status:** active product plan. Every "exists" claim below was
checked against `main` at `88eae6f`. The [decision-router alpha plan](decision-router-alpha-plan.md)
remains the delivery sequence for RRFlow integration and governed training; this plan covers the
product as a whole and points to it rather than repeating it.

## What SWAG is

SWAG is a System One controller: a fast decision engine that answers typed questions about a
request instead of writing text. Every decision is one of three routes:

| Route | Question | Answer |
| --- | --- | --- |
| **binary** | Is this proposition true? | yes or no, with a probability |
| **choice** | Which of these options applies? | one option, with a probability for each |
| **score** | How does this rate on a named rubric? | a level, with a probability for each |

Any route may abstain. A decision proposes; it never authorizes or executes work. Standalone, the
caller acts on it. Inside RRFlow, the engine admits, executes and verifies.

The product must:

1. **Deploy turnkey.** One command, by someone with no technical background, guided by their AI
   assistant. It also plugs into an existing vLLM or llama.cpp server.
2. **Show its work.** Devtools show each decision's route, answer, probabilities, timings per stage,
   the cited practices behind it and the model that made it.
3. **Let the operator steer.** Templates extended with `operator.preferences` visibly change all
   three routes.
4. **Run fast and small.** The target is a strong 18B-class controller in 9 GB or less. Virtual
   shards over the user's knowledge activate only the reasoning pathways a request needs.
5. **Fold in proven research** as one system, each optimization at its own layer with no overlap.
6. **Stand alone or integrate** with RRFlow, with LFG adding datapoints and heads-up signals.

## Architecture

```text
request ─▶ Composer ─────────────▶ Engine ─────────────▶ Decision record ─▶ caller or RRFlow
           template                adapter: vLLM,         route, answer,
           + knowledge markers     llama.cpp, SystemOne,  probabilities,
           + operator.preferences  in-process             timings, citations,
           + LFG heads-up          fast path, escalation  model identity
                                                                │
                                                                ▼
                                                      Devtools and evaluation
```

| Layer | Owns | Research folded in here, and only here |
| --- | --- | --- |
| Contract | The three routes, abstention, and the request and response format | The SystemOne `state` + `questions` format shared by the decision-model ecosystem, so engines are swappable |
| Composer | Turning a request into questions: templates, knowledge, preferences | Owner's markers and virtual shards over the user's knowledge |
| Engine | Answering questions as fast as possible | Prefill-only scoring with no generated text ([RIPL](https://www.liquid.ai/blog/low-latency)); first-token label scoring; a fast path that escalates when unsure |
| Model | The weights | Expert pruning by router-weighted activation ([REAP](https://arxiv.org/abs/2510.13999)); 4-bit weights; calibration training; owner's RRFlow variants |
| Memory | Where knowledge and pathway state live | Hot and cold tiers: an LSM store for hot state, columnar files for cold history |
| Signals | Advisory inputs | LFG observations; RROFLOW outcomes |
| Devtools | Making all of the above visible and tunable | Content-free tracing plus a local per-decision log |

Each optimization changes one layer: which experts exist, how weights are stored, what is loaded,
or whether tokens are decoded. That keeps their effects separately measurable and stops them
overlapping.

## Where it stands

| Capability | State | Evidence on `main` |
| --- | --- | --- |
| Choice route produced by a model | **Exists** | `tools/swag_brief.py`, `tools/swag_decision_model.py` |
| Binary and score routes produced by a model | **Missing** | `tools/swag_knowledge.py` only validates answers someone else supplies |
| Rules fallback with no model | **Exists** | `decision_brief` reports `basis: rules_only`; weak quality, see below |
| SystemOne and OpenAI-compatible engines | **Exists** | `systemone` and `chat_first_token` protocols |
| llama.cpp engine | **Missing** | no references in code or config |
| Turnkey Docker deployment | **Missing** | `deploy/scripts/*.sh` start processes; no image or compose file |
| `operator.preferences` changing routes | **Missing** | `config/aiddevspec/default.yaml` defines them; no code reads them |
| Templates bound to project knowledge | **Partial** | `tools/swag_knowledge.py` previews and validates; it does not drive routes |
| Devtools | **Partial** | `ui/public/dev.html` shows endpoint, training and per-operation p50/p95; nothing per decision |
| LFG signal | **Partial** | the brief reports LFG effort and flags a conflict with elevated stakes |
| Knowledge markers and virtual shards | **Missing** | design only |
| Pruned, quantized or cascaded model | **Missing** | the model is 30.5B parameters, 61.07 GB in BF16 |
| Evaluation harness | **Partial** | results in [decision-brief-evaluation.md](decision-brief-evaluation.md); the harness is not in the repo |
| RRFlow selector contract | **Partial** | one real BF16 proposal accepted; see [model-outcome-correlation.md](model-outcome-correlation.md) |
| Merge gating and repo health | **Exists** | `ci-gate`, auto-merge, `Repo status` workflow |

### Measured quality

| Benchmark | SWAG today | 26-32B median | Jev 1.14 | Source |
| --- | --- | --- | --- | --- |
| CRUXEval, code reasoning (570 rows) | 0.563 | 0.850 | 0.747 | public Decision Index rows, rebuilt and verified against a control model |
| When2Call, tool decisions (3,652 rows) | 0.700 | 0.848 | 0.817 | same |
| Stakes F1, held-out requests | 0.78 | not available | not available | assistant-labelled, see the evaluation doc |
| Time per brief, compact questions | 1.11 s | not available | not available | one sequence, eager mode, one GB10 |

The size class matters: on the full index, median score is 40.9 at 4-5B, 46.2 at 9-12B and 66.1 at
26-32B. SWAG's base is a mixture-of-experts model with about 3B active parameters, and it has had 33
training steps on 44 examples. The gap is what this plan closes.

## Workstreams

Each workstream lands as short PRs that merge when `ci-gate` passes. Acceptance is something a
person can run or observe, never a document.

### W1. Three routes on any engine

- Produce binary and score answers from the model, alongside choice, with abstention as an explicit
  option rather than a low probability.
- Add a llama.cpp engine adapter beside `systemone` and `chat_first_token`.
- Keep the rules path as the visible fallback.

**Done when** one `decide` call returns a typed answer for each route against vLLM, llama.cpp and a
SystemOne server, and conformance tests pin the format for all three.

### W2. Templates and `operator.preferences`

- Define the preference schema and its merge order: shipped template, then project, then operator,
  then request.
- Preferences may change wording, options, rubric levels, thresholds and which checks are required.
  They may not loosen safety floors. Elevated stakes stays elevated.
- Every decision records which preferences applied.

**Done when** changing one preference changes a route's answer, the decision record shows why, and
reverting the preference restores the earlier answer.

### W3. Devtools

- A local decision log recording request digest, route, questions, answer, probabilities, time per
  stage, model identity, preferences applied, LFG signal and cited checks. Content is kept locally
  and is never uploaded.
- A Decisions page in the existing UI to filter, open and replay a decision against another engine
  or preference set.
- A scoreboard page showing W5 results over time.

**Done when** a person can open any recent decision, see why it came out that way and how long each
stage took, and rerun it with one change.

### W4. Turnkey deployment

- Docker images and one compose file with profiles: `rules` (no GPU), `vllm`, `llama-cpp`,
  `external` (an existing OpenAI-compatible or SystemOne server).
- `swag_setup.py` detects the machine and writes the environment file. A health page states
  plainly what is running and what is missing.
- `DEPLOY.md` written for an AI assistant to follow on a user's behalf, with a check at each step.

**Done when** a clean machine reaches a working decision on the devtools page from one command,
following only `DEPLOY.md`, on each profile.

### W5. Evaluation as part of the product

- Move the benchmark harness into the repo: the rebuilt public rows (CRUXEval, When2Call, then BFCL),
  the held-out request set and RRFlow selector cases.
- `swag eval` runs any engine against them and writes results the scoreboard reads.
- Every result states its label source. Assistant-written labels are development evidence only.

**Done when** any engine or preference change gets a comparable number on every set with one command.

### W6. The model

In order, each step gated on the one before it:

1. **Expert overlap by knowledge domain.** Measure which experts fire per domain on the base model,
   comparing two halves of the same domain against different domains. Masks are only worth building
   if domains separate. The script is written and has not yet run.
2. **Base choice.** Run the same scoring on SWAG's untrained base and a dense 26-32B model, so the
   effect of the base can be separated from the effect of training.
3. **Calibrated decision training** on the chosen base: all three routes, an explicit abstain
   option, and a calibration loss. Data follows the RRFlow learning contract; assistant-inferred
   labels are not admitted.
4. **Owner's RIPL/REAP variants.** Expert selection driven by knowledge markers, as virtual shards
   that mask rather than delete.
5. **Footprint.** 4-bit weights, then the 18B-class candidate with a fast path that escalates
   uncertain decisions to the full model. Report the 29, 15 and 9 GB milestones as measured total
   serving memory, not weight size.

**Done when** a candidate beats Jev on CRUXEval and When2Call, holds stakes recall on held-out
requests, and fits its declared memory budget, all measured by W5.

### W7. RRFlow and LFG

- Conform to RRFlow's endpoint-selection contract: one binding plus supported effort, or explicit
  abstention, as strict output. Delivery follows packages P01 to P06 of the
  [alpha plan](decision-router-alpha-plan.md).
- LFG supplies datapoints and heads-up signals to the composer. Absence, disagreement and timeout
  are explicit states, and combinations are compared before becoming defaults.

**Done when** the installed journey in the alpha plan passes with SWAG as the configured selector.

### W8. Docs and structure

- One entry point: the README states what SWAG is, the three routes and the quickstart, and links here.
- A `docs/` index marking each document as current, reference or historical. `current-context.md`
  (1,766 lines) and `experiment-evidence.md` (880 lines) become historical logs, not instructions.
- Retire config that implies features with no code behind them, or wire it up. Today this covers the
  14B/7B/27-28B tier policy, the 6-9 GB fast profile and the unread `operator_preferences`.

**Done when** a newcomer, human or AI, can go from the README to a working deployment without reading
historical material.

## Milestones

| Milestone | Delivers | Depends on |
| --- | --- | --- |
| **M1: turnkey prototype** | Three routes, preferences, decision devtools and Docker, on rules or any compatible model | W1-W4 |
| **M2: measured baseline** | Scoreboard for every engine; base-choice and expert-overlap results | W5, W6 steps 1-2 |
| **M3: trained System One** | A candidate that beats Jev on public rows and holds held-out stakes recall | W6 step 3 |
| **M4: 9 GB controller** | Markers, virtual shards, 4-bit weights and escalation at the measured budget | W6 steps 4-5 |
| **M5: RRFlow integrated** | The alpha plan's installed journey with SWAG as selector | W7 |

M1 needs no training and can ship first. It is the first release worth tagging, as
`v0.1.0-prototype`.

## Decisions needed from the owner

1. **Where the RIPL/REAP variants and CLD are defined in RRFlow.** W6 step 4 builds from them.
2. **Base model:** keep the mixture-of-experts base, or move to a dense 26-32B base. W6 step 2
   produces the evidence for this.
3. **Training data:** which sources may be admitted for W6 step 3 beyond reviewed real outcomes, for
   example public decision datasets with compatible licences.
4. **Turnkey target:** the machine a vibe coder is expected to have. This decides whether the default
   profile is `rules`, a small local model or a hosted engine.
5. **What "03" means** in the training plan, which the alpha plan also leaves open.

## Next step

M1, starting with W1 and W3 together: binary and score from the model, plus the decision log they
write. Every later workstream reads that log.
