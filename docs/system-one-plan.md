# SWAG System One controller: product plan

**Date:** 14 November 2026. **Status:** the only active plan. Every "exists" claim below was
checked against the code in the change that aligned SWAG on one decision contract. Earlier plans
are kept under [history](index.md#history). Where they disagree with this one, this one wins.
Terms are defined in the [glossary](glossary.md).

## What SWAG is

SWAG is a System One controller: a fast decision engine that answers typed questions about a
request instead of writing text. Every decision is one of three modes:

| Mode | Question | Answer |
| --- | --- | --- |
| **binary** | Is this proposition true? | yes or no, with a probability |
| **choice** | Which of these options applies? | one option, with a probability for each |
| **score** | How does this rate on a named rubric? | a level, with a probability for each |

Any mode may abstain. A decision proposes; it never authorizes or executes work. Standalone, the
caller acts on it. Inside RRFlow, the engine admits, executes and verifies.

The product must:

1. **Deploy turnkey.** One command, by someone with no technical background, guided by their AI
   assistant. It also plugs into an existing vLLM or llama.cpp server.
2. **Show its work.** Devtools show each decision's mode, answer, probabilities, timings per stage,
   the cited practices behind it and the model that made it.
3. **Let the operator steer.** Templates extended with operator preferences (`operator_preferences`
   in AIDevSpec), facts and hard rules visibly change all three modes.
4. **Run fast and small.** The target is a strong 18B-class controller in 9 GB or less. Virtual
   shards over the user's knowledge activate only the reasoning pathways a request needs.
5. **Fold in proven research** as one system, each optimization at its own layer with no overlap.
6. **Stand alone or integrate** with RRFlow, with LFG adding datapoints and heads-up signals.

## Architecture

```text
request ─▶ Composer ─────────────▶ Engine ─────────────▶ Decision record ─▶ caller or RRFlow
           template                adapter: vLLM,         mode, answer,
           + knowledge markers     llama.cpp, SystemOne,  probabilities,
           + facts, rules, prefs   in-process             timings, citations,
           + LFG heads-up          fast path, escalation  model identity
                                                                │
                                                                ▼
                                                      Devtools and evaluation
```

| Layer | Owns | Research folded in here, and only here |
| --- | --- | --- |
| Contract | The three modes, abstention, and the request and response format | The SystemOne `state` + `questions` format shared by Jev, Clef and KnowLine, so engines and competitors are swappable; TypeSafe's confidence definitions |
| Composer | Turning a request into questions: templates, knowledge, facts, rules, preferences | Owner's markers and virtual shards over the user's knowledge; RRFlow's layer-merge rules (narrow, never widen) |
| Engine | Answering questions as fast as possible | Prefill-only scoring with no generated text ([RIPL](https://www.liquid.ai/blog/low-latency)); first-token label scoring; KnowLine's option rotations; a fast path that escalates when unsure |
| Model | The weights | Expert pruning by router-weighted activation ([REAP](https://arxiv.org/abs/2510.13999)); 4-bit weights; calibration training; owner's RRFlow variants |
| Memory | Where knowledge and pathway state live | Hot and cold tiers: an LSM store for hot state, columnar files for cold history |
| Signals | Advisory inputs | LFG observations; RROFLOW outcomes |
| Devtools | Making all of the above visible and tunable | Content-free tracing plus a local per-decision log |

Each optimization changes one layer: which experts exist, how weights are stored, what is loaded,
or whether tokens are decoded. That keeps their effects separately measurable and stops them
overlapping.

## Where it stands

| Capability | State | Evidence |
| --- | --- | --- |
| Binary, choice and score produced by a model | **Exists** | `tools/swag_decision_model.py` scores all three types through `systemone` and `chat_first_token`; `tools/swag_systemone.py` shapes Jev-compatible answers |
| Option-order bias correction | **Exists, opt-in** | `rotations` in the connection file |
| Facts, hard rules, preferences in four layers | **Exists** | `tools/swag_decide.py`; template, project `.swag/layer.json`, operator AIDevSpec, request |
| Suggestions from templates | **Exists** | `suggest` in knowledge templates v2 |
| Decision server, Jev-compatible | **Exists** | `tools/swag_server.py`, `POST /v1/systemone`; token required beyond loopback |
| Per-decision devtools | **Exists, first version** | decision log plus the Decisions panel in `ui/public/dev.html`; no replay or filters yet |
| Competitor bench | **Exists** | `bench/`; Jev, Clef, KnowLine and SWAG over the same requests ([competitors](competitors.md)) |
| Rules-only fallback with no model | **Exists** | Hard rules decide; everything else abstains with `no_engine` |
| llama.cpp engine | **Untested** | `llama-server` speaks the OpenAI chat API, so `chat_first_token` should work; not yet run |
| Turnkey Docker deployment | **Missing** | launchers start processes; no image or compose file |
| RRFlow second brain supplying layers | **Missing** | the layer format is defined; RRFlow does not produce it yet |
| The older brief on the new contract | **Partial** | `decision_brief` still asks its stakes and domain questions through the choice path |
| Knowledge markers and virtual shards | **Missing** | design only |
| Pruned, quantized or cascaded model | **Missing** | the model is 30.5B parameters, 61.07 GB in BF16 |
| RRFlow selector contract | **Partial** | one real BF16 proposal accepted; see [model-outcome-correlation.md](evidence/model-outcome-correlation.md) |
| Merge gating and repo health | **Exists** | `ci-gate`, auto-merge, `Repo status` workflow; dead-link check in tests |

### Measured quality

| Benchmark | SWAG today | 26-32B median | Jev 1.14 | Source |
| --- | --- | --- | --- | --- |
| CRUXEval, code reasoning (570 rows) | 0.563 | 0.850 | 0.747 | public Decision Index rows, rebuilt and verified against a control model |
| When2Call, tool decisions (3,652 rows) | 0.700 | 0.848 | 0.817 | same |
| Top-option calibration error, CRUXEval / When2Call | 0.362 / 0.242 | not available | 0.080 (all benchmarks) | [competitors](competitors.md); KnowLine-4B scores 0.156 / 0.054 through the same scoring path |
| Stakes F1, held-out requests | 0.78 | not available | not available | assistant-labelled, see the evaluation doc |
| Time per brief, compact questions | 1.11 s | not available | not available | one sequence, eager mode, one GB10 |

The size class matters: on the full index, median score is 40.9 at 4-5B, 46.2 at 9-12B and 66.1 at
26-32B. SWAG's base is a mixture-of-experts model with about 3B active parameters, and it has had 33
training steps on 44 examples. KnowLine-4B loses almost nothing through SWAG's scoring path, so
the gap is in SWAG's model, not its scoring. SWAG's model is also badly overconfident, which
matters because every abstention floor depends on confidence meaning what it says. The gap is
what this plan closes.

## Workstreams

Each workstream lands as short PRs that merge when `ci-gate` passes. Acceptance is something a
person can run or observe, never a document.

### W1. Three modes on any engine

Delivered:

- `swag decide` and `POST /v1/systemone` return typed answers for all three modes.
- Abstention is an explicit status with a reason.
- Conformance tests pin the format.

Remaining:

- Run against llama.cpp `llama-server` and record the result.
- Score a request's questions in parallel after one shared-prefix warm-up, where the engine has a
  prefix cache.
- Move the older `decision_brief` onto `decide`, so there is one decision path.

**Done when** one `decide` call returns a typed answer for each mode against vLLM, llama.cpp and a
SystemOne server.

### W2. Templates, facts, rules and preferences

Delivered:

- The layer schema (facts, hard rules, preferences) and its merge order: template, project,
  operator, request.
- Rules only narrow, and a preference never lowers a rule's floor. Every decision records which
  rules and preferences applied, and from which layer.
- Templates v2 carry Jev-shaped questions and suggestions. See the
  [decision contract](decision-contract.md).

Remaining:

- **A template library.** One shipped template is too few. Each stack and domain in the question
  bank needs a template with facts to fill, rules and suggestions. This is the "ton of templates"
  RRFlow's second brain populates.
- **Fact extraction.** Fill facts from the project automatically: manifests, CI files and
  lockfiles, each with a source and an observation date.
- **Project-specific templates.** Let a project change wording, options and rubric levels without
  copying the whole template.

**Done when** changing one preference changes a mode's answer, the decision record shows why, and
reverting the preference restores the earlier answer. The first two parts are tested; the third
needs the template library.

### W3. Devtools

Delivered:

- The local decision log. It records the request digest, each question's mode, decision, status,
  confidence, rules and preferences with their layers, the model, and the time per step.
- The Decisions panel in the developer workspace.

Remaining:

- Filters, and replay of a logged decision against another engine or preference set. Replay
  needs the state, so it works when `SWAG_LOG_STATE=1`.
- The LFG signal in the record.
- A scoreboard page reading `bench/score.py --json` over time.

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

### W5. Evaluation and competitors

Delivered:

- `bench/` rebuilds the public rows (CRUXEval, When2Call).
- It sends identical requests to SWAG, Jev, Clef and KnowLine.
- It scores accuracy, calibration error, Brier score, latency and paired significance.

Remaining:

- Run the full comparison with Jev's API (needs `TYPESAFE_API_KEY`) and with Clef on a Spark
  (needs the owner's go-ahead to run its released code there).
- Add BFCL, a fresh held-out request set with human labels, and RRFlow selector cases.
- Every result states its label source. Assistant-written labels are development evidence only.

**Done when** any engine or preference change gets a comparable number on every set with one command.

### W6. The model

In order, each step gated on the one before it:

1. **Expert overlap by knowledge domain.** Measure which experts fire per domain on the base model,
   comparing two halves of the same domain against different domains. Masks are only worth building
   if domains separate. The script is written and has not yet run.
2. **Base choice.** Run the same scoring on SWAG's untrained base and a dense 26-32B model, so the
   effect of the base can be separated from the effect of training.
3. **Calibrated decision training** on the chosen base: all three modes, an explicit abstain
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
  [alpha plan](history/decision-router-alpha-plan.md).
- LFG supplies datapoints and heads-up signals to the composer. Absence, disagreement and timeout
  are explicit states, and combinations are compared before becoming defaults.

**Done when** the installed journey in the alpha plan passes with SWAG as the configured selector.

### W8. Docs and structure

Delivered:

- The README states what SWAG is, the three modes and the quickstart.
- `docs/` is split into current, reference, evidence and history, indexed in [index.md](index.md),
  with a [glossary](glossary.md).
- `operator_preferences` is now read and enforced.
- Eleven tools and seven configs with no caller were removed.
- A dead-link check runs with the tests.

Remaining:

- Retire the 14B/7B/27-28B tier policy, which only the legacy preview service reads.
- Retire the training-pipeline stubs, which only refuse to run, together with the training
  operations UI's dependence on them.
- Merge the legacy preview service into `decide`.

**Done when** a newcomer, human or AI, can go from the README to a working deployment without reading
historical material.

## Milestones

| Milestone | Delivers | Depends on |
| --- | --- | --- |
| **M1: turnkey prototype** | Three modes, facts, rules and preferences, decision devtools and Docker, on rules or any compatible model | W1-W4 |
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

Finish M1 with W4: a Docker compose file with `rules`, `vllm`, `llama-cpp` and `external`
profiles, a setup command that detects the machine, and a `DEPLOY.md` an AI assistant can follow.
Next, grow the W2 template library, since RRFlow's second brain will fill those templates.
