# Decision brief evaluation, 4 November 2026

This is a development comparison, not a qualification. Assistants wrote the labels, so under
[deployment readiness](deployment-readiness.md) these results neither qualify a route nor admit
training data. Independent human review remains open.

## Method

An agent that read only the question bank wrote 90 software requests and labelled them. A second agent
labelled the same requests without seeing those labels. They agreed on stakes for 89 of the 90, but both
were the same kind of model, so that shows the labels are stable, not that they are right.

- **Categories:** 30 use a domain's ordinary words, 30 describe the same risks without them, 15 contain a
  word that only looks like a domain, and 15 are routine work.
- **Scoring:** stakes counts only where the labellers agree. A domain only one of them chose is neither
  required nor penalised.
- **Splits:** 27 development and 63 test, split by hash. Thresholds and schema were chosen on development
  alone, and per-item errors were read there alone. Each arm's test score below is final; that split is
  no longer unseen for these arms.

The requests and harness stay local so that they remain useful for later comparisons.

## Results on the 63 test requests

| | Rules | Custom model, one question per item | Custom model, compact | [Clef-flash](https://huggingface.co/Cloudflare/clef-flash) |
| --- | --- | --- | --- | --- |
| Stakes F1 | 0.44 | 0.78 | 0.78 | **0.87** |
| Elevated requests caught | 6 of 16 | **16 of 16** | **16 of 16** | 13 of 16 |
| Normal requests marked elevated | 5 of 46 | 9 of 46 | 9 of 46 | **1 of 46** |
| Domain F1 (micro) | 0.55 | 0.50 | **0.86** | 0.84 |
| Real risks it stayed silent on | 15 of 38 | 4 of 38 | **1 of 38** | 3 of 38 |
| Harmless requests given checks | 12 of 25 | 10 of 25 | **3 of 25** | **3 of 25** |
| A required check in the top seven | 47% | 79% | 84% | **89%** |

- **Custom model, compact** is the frozen `decision_brief` path with the policy's thresholds, run over a
  local tunnel against the existing custom BF16 endpoint on a GB10 Spark.
- **Clef-flash** used one question per item with its development-chosen thresholds (0.4 stakes, 0.3
  domains). Its compact schema has not been run.
- On stakes, compact and Clef-flash disagree on 11 requests, 8 to 3 in Clef-flash's favour. With so few
  requests that gap could be chance (exact McNemar p = 0.23).
- A later fix stops the word "go" naming the Go stack. It came after this scoring, so it isn't reflected
  above.

The compact schema asks one question across all domains and one per selected group, instead of one per
domain and per check. Domain routing improved and that gain held on test. Asking stakes as two explicit
outcomes raised stakes F1 from 0.875 to 0.97 on development, but test stayed at 0.78, so **it should not
be treated as an improvement**.

## All three models on the same questions

A later run gave [KnowLine-4B-Gen5.5](https://huggingface.co/PelaAI/KnowLine-4B-Gen5.5) and Clef-flash the
compact questions on the same GB10 Spark, one model at a time. Each model's thresholds came from one rule
applied to development. For domains: fewest silent misses, then fewest harmless requests flagged, then best
domain F1. For stakes: best F1. The test split had already been seen, and this was the custom model's third
look at it, so read this as a same-schema comparison and not as a fresh held-out result.

| 63 test requests | Custom model | KnowLine-4B | Clef-flash |
| --- | --- | --- | --- |
| Stakes F1 | 0.79 | 0.87 | **0.91** |
| Elevated requests caught | 15 of 16 | **16 of 16** | 15 of 16 |
| Normal requests marked elevated | 7 of 46 | 5 of 46 | **2 of 46** |
| Domain F1 (micro) | **0.83** | 0.74 | 0.82 |
| Real risks it stayed silent on | **0 of 38** | **0 of 38** | 1 of 38 |
| Harmless requests given checks | **1 of 25** | 5 of 25 | 2 of 25 |
| A required check in the top seven | 84% | **87%** | **87%** |
| Time per brief, median | 0.96 s | 0.63 s | **0.48 s** |
| Time per brief, p95 | 1.01 s | 1.12 s | **0.91 s** |
| Size on disk | 61.07 GB | **9.34 GB** | 19.08 GB |
| GPU memory, peak | about 63 GB | **9.95 GB** | 19.37 GB |

- **No pair differs reliably on stakes.** Exact McNemar: custom and Clef-flash 0 to 5 (p = 0.06), custom and
  KnowLine 0 to 3 (p = 0.25), KnowLine and Clef-flash 1 to 3 (p = 0.63).
- **Thresholds move these numbers as much as the choice of model.** KnowLine's stakes F1 was 0.91 at the
  policy's thresholds and 0.87 at its own tuned ones, so tuning on 27 requests did not help it. The shipped
  thresholds were chosen for the custom model, and another model needs its own.
- **Serving differs.** The custom model runs behind its existing endpoint in eager mode with one sequence.
  The other two run in-process through Transformers, and KnowLine's documented SGLang path was not used.
  Memory figures come from different counters and are not a total serving footprint.

On the 21 retained real tasks with assistant labels, always answering `implementation` matches 14. The custom
model matches 17, KnowLine 13 and Clef-flash 11. The custom model was trained on labels written the same way,
which favours it here, and its two extra tasks over its own earlier JSON output could be chance (p = 0.5).

Clef-flash's holdout outputs did not change between a laptop GPU and the Spark: no stakes decision flipped
across the 90 requests at its threshold.

## Speed before the schema change

| | Time per brief | Size on disk |
| --- | --- | --- |
| Rules, warm | 12 ms | not applicable |
| Custom model, one question per item | 5.45 s (median) | 61.07 GB |
| Custom model, compact through `decision_brief` and a tunnel | 1.11 s median, 1.62 s p95 | 61.07 GB |

[Cloudflare publishes](https://blog.cloudflare.com/clef-decision-models/) a 38.8 ms median for Clef-flash on its
own hardware, per request. Reading one token instead of generating JSON also took the custom model from 0.75 s
to 0.24 s on the 21 real tasks.

## What this does not establish

- **That a smaller model can replace the larger one.** These are 63 short routing requests, which is where small
  models do best. On the public
  [Decision Index 0.4.1](https://huggingface.co/spaces/multimodalart/jev-decision-index), median full scores are
  40.9 at 4-5B, 46.2 at 9-12B and 66.1 at 26-32B. Among each class's leaders, the widest gap is code reasoning
  (CRUXEval), 0.83 against 0.43 at 4-5B. This test is too small and too easy to show a gap like that, so finding
  no reliable difference here says little.
- **Fixed stakes false alarms.** The custom model's probabilities sit near 0 or 1, so on development thresholds
  from 0.3 to 0.95 left its false alarms unchanged. That points at calibration in training rather than settings.
- **Requests touching two domains.** Domains compete in one question, so one of them can be lost.
- **Real outcomes.** These are selected questions against assistant labels, not checks that prevented a defect
  in a real project. Comparing further changes needs new held-out requests, ideally human-reviewed.
