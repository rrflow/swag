# Contributing real tasks and reviews

The first input is a real task you want completed. You do not need to write a
dataset or choose a training framework.

## What to provide first

- Repository and the actual change you want.
- What a correct result must do, including constraints or behavior to preserve.
- Relevant issue or prior attempt, if one exists. Missing history is fine.

We inspect available project context and configured provider access. If budget,
access or permission is missing for a comparison, we ask for that specific input
before its dependent call. Do not include API keys in task text or datasets.

## What we collect from execution

Capture binds the task and source revision to the eligible binding/model, effort,
effective configuration, actual response/artifact and verification result. Retain
observed time and usage; unsupported cost or quota is unknown. Failures and
abstentions remain in the record. Each alternative or rerun is a separate
authorized attempt with its own budget and identity.

## What your review decides

Inspect the actual output and verification evidence. State whether it satisfies
your criterion, identify a concrete defect or correction, and explain any
preference between outputs. A preference is not automatically a correctness
label. If you cannot judge an output, mark it unknown rather than guessing.

Training permission is separate. Reviewing an output does not imply permission
to train or export it. We preserve attribution and supporting evidence; we never
fill in consent or an independent review for you. Additional reviewer evidence
may be needed before a label is admitted.

## What we will not infer

- A completed PR does not prove which model produced it or which alternative
  would have performed better.
- A model name does not establish availability, subscription entitlement or quality.
- An accepted override does not establish that the original route was incorrect.
- A development example does not become unseen acceptance data after renaming it.

The existing review workspace at `http://127.0.0.1:8891/review.html`, when running,
contains 21 real PR-title tasks and retained intent-classification outputs. It
supports review of those labels, not provider-outcome comparisons. New real
execution records will enter the appropriate review package as its engine and
public-client boundaries are implemented.
