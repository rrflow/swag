# SWAG decision modes and development knowledge mesh

**Owner clarification:** 3 November 2026. **Status:** product contract direction;
the [local read-only adapter](knowledge-template-adapter.md) implements typed
answer validation and source-bound template previews. The complete engine decision
API, knowledge mesh and fulfillment lifecycle are not implemented.

SWAG is a System One controller with three decision modes: **choice, score and
binary**. These are reusable output forms, not three fixed application gates,
three candidate models or three predetermined groups of MoE experts. SWAG also
needs built-in development best-practices knowledge and deployable templates
that are fulfilled against the user's actual project.

## Decision contract

| Mode | Intended behavior | Required context and evidence |
| --- | --- | --- |
| Choice | Select an applicable option from the supplied set, or abstain. | Stable option IDs, task intent, applicability constraints and referenced knowledge. Option count is variable. |
| Score | Assess an option, artifact or requirement against a declared rubric. | Rubric/version, scale, direction, units where relevant, and evidence. An ordinal score is not automatically a probability or calibrated confidence. |
| Binary | Answer a specified yes/no proposition. | Proposition, relevant project snapshot and supporting evidence. Insufficient evidence produces explicit abstention/unknown rather than an invented yes or no. |

Requests bind mode, project/source identity, template and knowledge revisions,
and the explicit options, rubric or proposition. Responses bind the same inputs,
model/artifact identity, result or abstention, and supporting references. Returned
references must resolve to the provided context; a citation alone proves neither
correctness nor applicability. Deterministic validation rejects malformed results
and choices outside the supplied options. RRFlow enforces execution permissions
independently of any model result.

One template can use several modes: choose an applicable pattern, score its
evidence against a rubric, then assess whether a concrete requirement is met.
This does not require three copies of a model. Compare a shared backbone with
typed decoding or decision heads on real tasks before choosing an architecture.

## Built-in knowledge and templates

The existing `config/boundaries/question_sets/` and `boundaries/reference/`
provide source-linked stack/domain questions, maturity rules and project bindings.
`tools/boundary_controller.py` composes relevant checks; `config/aiddevspec/`
contains project preferences and quality policies. These are foundations for the
mesh, not evidence that a complete grounded fulfillment system already exists.
Generated question text retains its source/export workflow.

The proposed mesh connects versioned practices, applicability conditions,
dependencies, conflicts, exceptions, templates and verification methods. Each
practice keeps its authoritative source and revision. Package a versioned local
knowledge pack with the developer build so built-in knowledge works without an
unrecorded external lookup. Model tuning should teach application of the knowledge;
explicit retrievable sources allow correction and updates without retraining for
every changed practice. A graph/query backend remains an integration decision.

Templates declare required project bindings, applicable practices, expected
artifacts, prerequisites and checks. After deployment, instantiate them from
actual project inputs. Missing information stays unresolved and can request
clarification; do not silently fill it with invented architecture or test results.
The same lifecycle supports initial implementation and checks that require a
running deployment, such as observing the configured service's actual behavior.

## Fulfillment through RRFlow and Connectome

1. Bind a template revision to the project snapshot and relevant knowledge pack.
2. Let SWAG propose applicable choices, assessments and missing work.
3. Let RRFlow admit the plan and execute authorized work through selected agents.
4. Collect file changes, test results and, where required, deployment observations.
5. Mark a requirement fulfilled only when its declared verification succeeds;
   preserve failed, unknown, blocked and explicitly excepted results separately.
6. On relevant source, template or knowledge edits, stale only affected evidence
   and replan the affected work. Preserve history and already committed effects.

The template view projects engine-owned state; it must not create a second plan
or completion ledger in SWAG. Connectome should expose requirements, missing
bindings, cited practices, decisions and fulfillment evidence. RROFLOW receives
authorized correlated observations for debugging and reviewed learning. A model's
binary yes or high score alone cannot mark a project requirement complete.

## Evaluation and delivery sequence

First bind these modes to the public engine proposal contract and project-source
identity. Then add the versioned knowledge/template adapter and Connectome view.
Prove one real template through binding, execution, verification, an ordinary
edit, scoped replanning and restart. Capture independently reviewed outcomes
without treating inferred best-practice labels as task-success evidence.

Evaluate choice correctness and option-order sensitivity; score agreement with
independent rubric judgments; binary false positives/negatives and abstention.
Also measure retrieval coverage, source applicability, conflicting/stale knowledge
and actual template fulfillment. Keep suitability and handoff objectives separate
from these output modes and deterministic permission checks.

The 9–12 GB research target covers the declared running controller, including
resident knowledge indexes/retrieval, caches and template-service allocations.
Report RRFlow and external worker/fallback resources separately and state the
scope explicitly. Weight compression alone cannot qualify this complete workload.
