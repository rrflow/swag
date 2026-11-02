# BF16 proposal and RROFLOW correlation, 2 November 2026

An isolated run passed one real work-item proposal through the configured BF16
endpoint, RRFlow's durable task-attempt boundary, and the native RROFLOW receiver.
This is candidate integration evidence. It does not establish a complete
Connectome workflow, successful project changes, routing quality or release readiness.

The [measured summary](evidence/model-outcome-correlation-20261102.json) binds the
binary, source, task, attempt, configuration, event and response identities. Raw
session logs and the unreviewed capture remain private.

## What actually ran

The input was the exact title and first problem paragraph of real
[RRFlow PR248](https://github.com/rrflow/rrflow-development/pull/248), captured at
head `59e48ebfc24025a063619ce14714e545b8f4775b`. No task or expected route was
generated for this run. The existing experimental profile offered one configured
candidate. RRFlow constructed the proposal from its stored task and configuration;
the harness used the canonical Rust contract helper for request digests.

The configured `swag-qwen3-coder-intent-20261028` endpoint returned a selection
with default effort, which the engine accepted and retained. Its receipt reports
HTTP 200, 1,008 prompt tokens, 20 completion tokens and 1,860 ms proposal elapsed
time. The task budget charged 1,900 ms and retained one reserved step. Token counts
are provider-reported; this single observation is not a latency benchmark.

The engine prepared and delivered the terminal attempt's metadata to RROFLOW.
Task ID, attempt ID, configuration digest and retained-response digest matched.
After abrupt termination and reopening of only the harness-owned engine and
receiver, attempt and delivery readback matched. Acknowledged delivery replay
left one receiver event and one delivery attempt, with the model budget still at
one reserved step and no active attempt.

RROFLOW received correlation references. Prompt text, draft output and model/usage
fields were absent from its event. The engine's authorized source readback retained
the proposal and usage. This proves local native metadata transport and recovery,
not a hosted log service or full trace coverage.

## Failure retained and corrected

The first setup requested a 90-second step allowance against an estate cap of
60 seconds. RRFlow returned `resource_exhausted` before model dispatch. The
corrected harness reads the public capabilities and uses the estate's actual
reasoning limits, restricting the task to one step. It does not raise estate
caps, retry a model response or alter an observed choice. Both attempts remain
retained under their original identities.

## Learning and acceptance boundaries

One schema-valid capture, `passive-e3b9afc2a381`, records the observed route with
`label_status: unreviewed` and `training_consent: false`. A separate hash-bound
provenance artifact joins it to the engine attempt and RROFLOW event. User
acceptance, route correctness and project outcome remain unknown. No independent
review, dataset admission, training, evaluation consent or promotion occurred.

The historical checkpoint remains provisional. Its declared manifest identity
does not attest loaded weights; one eligible candidate cannot qualify model or
provider selection. The original-Qwen/custom-BF16/quantized comparison and 29 GB
serving target remain open.

The engine binary was an unqualified debug build of the combined source behind
[PR235](https://github.com/rrflow/rrflow-development/pull/235), before its final
evidence commit. Its native source matches published candidate `74ace47c`; the
summary retains the pre-commit source tree and executable hash. The receiver uses
the retained binary associated with merged
[RROFLOW PR43](https://github.com/rrflow/rroflow-development/pull/43).
Required engine candidate/protected CI, selected-worker integration, governed
project effects, the current Connectome workspace and an independently reviewed
real-task journey remain necessary. No release or completion gate closes here.
