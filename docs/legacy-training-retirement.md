# Retirement of unreviewed training paths

Verified 31 October 2026 in the local SWAG workspace. This directory has no Git
metadata; these changes are local, not a merged or deployed package.

## Defect and correction

The Unsloth launcher required reviewed-data admission, but the older operations
UI still invoked a generator that expanded synthetic scenario rows. Its runbooks
could execute shell commands, including a separate raw-dataset LoRA trainer that
did not enforce admission. Those paths contradicted the current owner instruction.

The three legacy generator entry points now refuse before input reads or output
creation. The old LoRA entry point refuses before GPU imports. The runbook tool
allows listing/printing historical commands but rejects `--execute`, including
when combined with `--list-steps`. The legacy UI button is disabled and its job
callable returns an explicit failure. No alternate training framework is selected
silently. Historical runbooks, datasets and model artifacts are preserved.

New training still uses `swag_routing_dataset.py` admission followed by an explicit
`swag_unsloth_train.py` invocation. That launcher requires reviewed real data and
an explicit seed. The correction does not supply missing human review, consent,
training evidence or model qualification.

## Validation and retained failures

An isolated Python 3.11.9 environment installed the repository's declared runtime
dependencies. Targeted checks pass: eight retirement checks, six Unsloth input
checks, seven capture-watcher checks, six passive-capture checks and sixteen
admission/evaluation checks. All generated test records are isolated correctness
fixtures, not training data or model-quality results. No training/provider job ran.

The first retirement test used the wrong UI class name; it was corrected to
`OpsContext`. The ambient Python lacked `jsonschema`; the failure is retained and
the isolated environment resolved it. The existing admission test expected an
older error for synthetic acceptance data; the current implementation rejects
non-real sources in every split earlier. The corrected test checks all three
splits and absence of output. Its first expanded subtest referenced a nonexistent
`split` field; the existing `projectGroup` fixture field now labels the subtest.

Before-images, hashes, failed/successful logs and validation records are retained
under `.swag/evidence/20261031/legacy-training-retirement/`. Original failure
observations without standalone logs remain identified in the validation records.
The shared capture redaction helpers are unchanged. No GPU training, whole-project
test run, desktop UI rendering or deployment is claimed by these CPU checks.
