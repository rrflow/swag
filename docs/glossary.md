# Glossary

One meaning per word. When another document uses a word differently, this page wins.

| Term | Meaning |
|---|---|
| **SWAG** | The System One controller: it answers binary, choice and score questions fast, abstains when unsure, and applies the project's facts, rules and preferences. Part of the [RRG suite](rrg-suite.md). |
| **System One** | Fast, structured decisions that software uses directly, as opposed to slow free-form reasoning. Also the name of the wire format below. |
| **SystemOne wire format** | `POST /v1/systemone` with `state` and typed `questions`, shared by Jev, Clef, KnowLine and SWAG. See the [decision contract](decision-contract.md). |
| **binary / `noul`** | A yes-or-no question. `noul` is its name on the wire, and the answer is the probability of yes. |
| **choice** | Pick one of 2-255 named options. |
| **score** | Pick a level on an ordered 2-255 level rubric. The answer is the expected level, not a probability. |
| **mode** | Which of binary, choice and score a question is. The older plan called these "routes". "Route" is not used for them any more. |
| **abstain** | Return no decision, with a reason. Better than a confident wrong answer. |
| **confidence** | How concentrated the model's probabilities are, from 0 (uniform) to 1 (certain). Not the same as being right; calibration measures how well they match. |
| **calibration** | Whether confidence matches accuracy: 80% confident should be right 80% of the time. Measured as calibration error (ECE). |
| **layer** | One source of facts, rules and preferences: template, project, operator or request, merged in that order. |
| **fact** | A statement about the project with a source and an optional freshness window. Stale facts are never used. |
| **hard rule** | A constraint that only narrows: forbid options, require an answer, raise the confidence floor, or say what to do on abstention. |
| **preference** | A soft setting: confidence floors, binary thresholds, favoured options in a near tie, how many suggestions to return. |
| **operator preferences** | The operator's own layer, kept in [AIDevSpec](../config/aiddevspec/default.yaml) as `operator_preferences`, `operator_rules` and `operator_facts`. |
| **AIDevSpec** | RRFlow's name for the structured, versioned global development profile. SWAG reads its operator layer from it. |
| **attunement profile** | The older per-project route profile read only by the legacy preview service. It does not shape decisions. |
| **knowledge template** | A reusable set of questions with their own layer and suggestions, each linked to a cited practice. See [`config/knowledge/templates/`](../config/knowledge/templates/). |
| **question set / question bank** | The cited best-practice questions per stack and domain in [`config/boundaries/question_sets/`](../config/boundaries/question_sets/). Templates point into them. |
| **suggestion** | Template text attached to an answer (or to abstaining), returned after a decision. |
| **decision log** | The local record of every decision with its rules, preferences and timings, read by the developer workspace. |
| **engine** | The model SWAG asks: a `/v1/systemone` server or an OpenAI-compatible chat server scored by first-token logprobs. |
| **rotations** | Scoring the same question with options in several orders and averaging, to cancel label-order bias. |
| **brief** | `swag brief`: the older entry point that picks up to seven checks and a stakes call for a request. It is being folded into templates and `decide`. |
| **preview** | `swag preview`: the legacy rules-only route preview. Not a decision. |
| **LFG** | The suite's CPU-side analyser. It supplies data points and heads-up signals; it never decides or authorizes. |
| **RRFlow** | The governed reasoning engine. It owns plans, authorization, execution and receipts. SWAG proposes; RRFlow decides what runs. |
| **RROFLOW** | rroflow.ai, the AI observability and learning sink. A different product from RRFlow, despite the one-letter difference. |
| **Connectome** | The desktop client for RRFlow. |
| **second brain** | RRFlow's store of a project's facts, rules and preferences. It is expected to supply SWAG's project and operator layers. |
| **Jev** | TypeSafe's hosted System One model and the reference competitor. |
| **Clef** | Cloudflare's released decision model (Clef-flash). |
| **KnowLine** | A released decision-model family (4B and 31B) that scores by first-token logprobs. |
| **RIPL** | Liquid AI's Real-time Inference Pipeline, a low-latency serving engine. Its internals are unpublished. SWAG borrows only the prefill-only scoring idea. The owner's own RIPL variant lives in RRFlow. |
| **REAP** | Router-weighted Expert Activation Pruning ([arXiv 2510.13999](https://arxiv.org/abs/2510.13999)), a way to drop rarely used experts from a mixture-of-experts model. The owner's own REAP variant lives in RRFlow. |
| **lane / seam** | RRFLOW naming terms checked by the [naming checker](reference/naming-checker.md). |
