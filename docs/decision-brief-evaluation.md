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

## Speed and size

| | Time per brief | Size on disk |
| --- | --- | --- |
| Rules, warm | 12 ms | not applicable |
| Custom model, one question per item | 5.45 s (median) | 61.07 GB |
| Custom model, compact | 1.11 s median, 1.62 s p95 | 61.07 GB |
| Clef-flash | not measured on the same hardware | 19.08 GB |

The endpoint runs one sequence in eager mode and is unchanged, so these are not its best possible times.
Clef-flash took 0.39 s per question on a laptop GPU, on a slower attention path than it was built for, and
[Cloudflare publishes](https://blog.cloudflare.com/clef-decision-models/) 38.8 ms on its own hardware.

Reading one token instead of generating JSON also changed the 21 retained real tasks, with the same
assistant labels: 15 to 17 matched, and 0.75 s to 0.24 s. Always answering `implementation` matches 14, and
two more tasks could be chance (p = 0.5).

## What this does not establish

- **Stakes false alarms remain.** The custom model's probabilities sit near 0 or 1, and on development no
  threshold from 0.3 to 0.95 reduced them. That points at calibration in training rather than settings.
- **Requests touching two domains can lose one.** Domains compete in one question.
- **The comparison is incomplete.** Higher-scoring small models on the public
  [Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index), such as KnowLine-4B at
  9.34 GB, have not been run here.
- **Nothing here measures real outcomes.** These are selected questions against assistant labels, not
  checks that prevented a defect in a real project.
