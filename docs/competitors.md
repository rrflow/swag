# Competitors: Jev, Clef and KnowLine

What each decision model does, what SWAG takes from it, and how SWAG measures against it. Each
row cites its source. "Measured" figures come from runs on our hardware; "published" figures come
from the [Decision Index 0.4.1](https://huggingface.co/spaces/multimodalart/jev-decision-index)
(2026-10-21 edition) or the vendor.

## How each one works

| | TypeSafe Jev | Cloudflare Clef-flash | KnowLine (4B, 31B) | SWAG today |
|---|---|---|---|---|
| Access | Hosted API only, closed weights (`POST https://api.typesafe.ai/v1/systemone`) | Released weights plus loader | Released weights plus server | This repository |
| Wire format | SystemOne: `state` + typed `questions` | Same | Same | Same ([decision contract](decision-contract.md)) |
| Base model | Unpublished | Qwen3.5-9B, full fine-tune | Qwen3.5-4B full fine-tune; Gemma-4-31B LoRA | Qwen3-Coder-30B-A3B, 33 training steps |
| How it scores | New architecture, a parallel sampler and "Reinforcement Learning for Calibrated Decisions" (vendor blog) | A learned joint-schema head: option and question spans cross-attend to the whole input, then each field is scored jointly. No generation | Prefill-only first-token logprobs over option labels; option rotations; reads short inputs twice | Prefill-only first-token logprobs; rotations optional |
| Confidence | Per the adapter: rescaled top probability (choice), spread around the mode (score) | Top probability | 1 minus normalised entropy | Adapter definitions |
| Cardinality | Up to 255 options | Any | Up to 255 labels, 64 questions | 255 on the wire; 26 for `chat_first_token` |

Sources:

- Jev: the [TypeSafe announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev),
  and TypeSafe's MIT [system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python),
  which reproduces the client contract and defines confidence.
- Clef and KnowLine: their released code, read in the local review copies; no third-party code
  runs in this repository.
- Model metadata: Decision Index model cards.

## Published results

| Model | Size | CRUXEval | When2Call | Calibration error (all benchmarks) | Median latency |
|---|---|---|---|---|---|
| Jev 1.14 | Unpublished | 0.747 | 0.817 | 0.080 | 196 ms over HTTPS |
| Clef-flash | 9.65B | 0.865 | 0.653 | 0.025 | 53 ms on card |
| KnowLine-4B Gen5.5 | 4.66B | 0.679 | 0.905 | 0.047 | 35 ms on card |
| KnowLine-31B Gen1 | 31.3B | 0.926 | 0.912 | 0.032 | 204 ms on card |
| elephant-1 | 9.41B | 0.912 | 0.915 | 0.058 | 114 ms on card |
| d3-ultra | 26.1B | 0.895 | 0.908 | 0.067 | 201 ms on card |

All figures are from Decision Index 0.4.1 model cards. CRUXEval and When2Call are accuracy;
chance is 0.370 and 0.25. The index measured latency on one RTX PRO 6000. Jev's figure includes
network time, so it is not comparable with the on-card numbers.

## Measured: SWAG on the same rows

Rows are rebuilt from the pinned public sources by [`bench/public_rows.py`](../bench/public_rows.py).
Ground truth comes from executing the code (CRUXEval) or from the published dataset (When2Call),
not from an assistant. "Top-option calibration error" uses ten bins on the top option's
probability. It is close to, but not the same as, the index's metric.

| Arm | CRUXEval (570) | When2Call (3,652) | Top-option calibration error, CRUX / W2C | Mean top probability, CRUX / W2C |
|---|---|---|---|---|
| SWAG custom (30B-A3B, first-token scoring) | 0.563 | 0.701 | 0.362 / 0.242 | 0.923 / 0.943 |
| KnowLine-4B through its own server | 0.668 | 0.906 | 0.132 / 0.058 | 0.798 / 0.964 |
| KnowLine-4B through SWAG's first-token scoring | 0.616 | 0.904 | 0.156 / 0.054 | 0.761 / 0.958 |

All three were measured 2026-11-06 on one GB10.

**What this shows.**

- KnowLine-4B keeps 0.904 on When2Call through SWAG's scoring path. So SWAG's scoring is not
  what loses: it costs 0.002 on When2Call and 0.052 on CRUXEval against KnowLine's own server.
  Which part of KnowLine's layout (read twice, rotations, prompt wording) accounts for the
  CRUXEval difference has not been isolated. The gap is in SWAG's model.
- That model is also badly overconfident: about 0.93 average confidence at 0.56-0.70 accuracy.
- Calibration is the first thing training has to fix (plan W6, step 3). Every abstention floor
  and preference threshold depends on confidence meaning what it says.

## What SWAG adopts, and what it does not

| Technique | Source | In SWAG |
|---|---|---|
| One wire format for all three types | Jev, Clef, KnowLine | Adopted: [`swag_systemone.py`](../tools/swag_systemone.py) |
| Confidence definitions | TypeSafe adapter | Adopted |
| Prefill-only first-token scoring, no generation | KnowLine, Liquid RIPL | Adopted: `chat_first_token` |
| Option rotations against label-order bias | KnowLine | Adopted, opt-in: `rotations` |
| Reading short inputs twice | KnowLine | Not yet. Measure it on dev rows first |
| Shared-prefix warm-up, then parallel per-question scoring | KnowLine (SGLang prefix cache) | Not yet. Needs an engine with a prefix cache; plan W1 |
| Joint schema head (no LM head at decision time) | Clef | Not adopted. It needs head training, and Clef's When2Call score (0.653) shows it can trail plain logprob scoring |
| Calibration as a training objective | Jev (RLCD), Clef's low calibration error | Planned: W6 step 3 |
| Abstention, hard rules, preferences, suggestions | None of the three | SWAG's own layer: [decision contract](decision-contract.md) |

## Running the comparison

Every competitor is one `/v1/systemone` URL, so one runner sends identical requests to all of
them:

```sh
python bench/public_rows.py                      # builds bench/data/public_rows.jsonl
cp bench/arms.example.json bench/arms.json       # list the arms you can reach
python bench/run.py --arms bench/arms.json --rows bench/data/public_rows.jsonl --out bench/results
python bench/score.py --rows bench/data/public_rows.jsonl bench/results/*.jsonl
```

| Arm | How to run it |
|---|---|
| `swag` | `python tools/swag_server.py` with `SWAG_DECISION_MODEL_CONNECTION_FILE` set |
| `jev` | Set `TYPESAFE_API_KEY`. Billed per input token; the index reports $12.26 for its 110,201-request suite |
| `knowline-4b` | KnowLine's released `knowline_server.py` in front of SGLang |
| `clef-flash` | A small server around Clef's released `systemone()` function |

The KnowLine and Clef arms run third-party code, which needs the owner's go-ahead on each
machine.

The scorer reports accuracy with a 95% interval, calibration error, Brier score, latency and an
exact paired McNemar test for every pair of arms. A failed request counts as wrong.
