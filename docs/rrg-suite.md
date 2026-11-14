# Reason Ready Governance (RRG) suite

SWAG is one product in the Reason Ready Governance (RRG) suite. This page maps the
suite and shows where SWAG fits. The descriptions state product intent; they are
not release or capability claims. Evidence in this repository covers SWAG only.

## Products

| Product | What it does |
|---|---|
| **LFG** | Fine-tuned classifier LLM that runs on CPU. It works in short bursts on text input to analyze chat and gives SWAG a data point. |
| **SWAG** (this repository) | System One controller. It answers binary, choice and score questions under the project's facts, rules and preferences, and proposes rather than executes. |
| **[RRFlow](https://github.com/rrflow/rrflow-development)** | Reasoning engine. It owns accepted plans, authorization, execution and durable receipts, and its second brain holds each project's facts, rules and preferences. |
| **Connectome** | The desktop client for RRFlow. |
| **[RROFLOW](https://github.com/rrflow/rroflow-development) / MakePulse** | The sink AI evolves from: error tracking and product analytics for AI, in the spirit of Sentry and PostHog, that also builds datasets for unsupervised learning. |
| **clyffy.ai** | Middleware AI tuned to get the most from your AI subscriptions. You talk to Clyffy, a custom UI shows the tasks, and Clyffy works through your subscription frontier AI in the browser or terminal while you watch and learn best practices. |
| **chatmaton.io** | Part of clyffy.ai. Cowork and chat, evolved and built to help you learn and grow as you use AI. |
| **devpulse.app** | Local, portable development. |
| **shippin.cloud** | A full hosting experience, built for ease of use, that works with your subscriptions. |
| **vaultix.cloud** | SCIF-style environment that lets AI work with sensitive information. The most sensitive work hands off to a local AI. |
| **devscif.com** | vaultix.cloud tailored for enterprise and government. |

## Where SWAG fits

The intended loop is:

```text
chat signal (LFG) + project intent
  → SWAG decision
  → agent or RRFlow execution
  → RROFLOW evidence
  → candidate improvement
  → held-out evaluation
  → reversible promotion
```

SWAG proposes bounded decisions through public contracts. RRFlow decides what is
accepted and executed. A captured event or a user's correction alone does not show
that a model or policy is better. The complete connected workflow is not yet
qualified; see [current context](history/current-context.md).

## SWAG serving footprint

SWAG only has to route, so its outputs are short. That lowers generation and
KV-cache cost, but it does not remove weight memory. Each smaller stage therefore
needs its own compression or sharding work, and it has to hold routing quality on
held-out evaluation.

| Stage | Serving footprint | Status |
|---|---|---|
| Qwen3-Coder-30B-A3B in BF16 | 61.07 GB on disk; vLLM reported 56.93 GiB of model memory | Measured; isolated peak not measured |
| Custom checkpoint after quantization | 29 GB | Target; not measured |
| Further optimized custom controller | 15 GB | Research target; not measured |
| Specialized 18B-class controller using pruning, quantization and selective residency | 9 GB or less | Owner's target ([plan](system-one-plan.md), W6); quality and total memory unverified |

The [3 November research update](history/controller-compression-research.md) supersedes
the earlier 19 GB aspiration. It defines how custom shards could reduce residency
and how to evaluate quality per decision mode before release.

## Licensing

This repository's [license](../LICENSE) covers SWAG only. Other RRG products have
their own terms.
