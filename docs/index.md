# Documentation

Start with the [README](../README.md), then the [System One plan](system-one-plan.md). Words are
defined once in the [glossary](glossary.md).

## Current

| Document | What it is for |
|---|---|
| [System One plan](system-one-plan.md) | What SWAG is, what exists, what is missing, and the work that closes the gap. The only active plan |
| [Decision contract](decision-contract.md) | Request and response, the three decision types, facts, rules and preferences, connecting a model |
| [Competitors](competitors.md) | Jev, Clef and KnowLine: how they work, published and measured results, what SWAG adopts |
| [Glossary](glossary.md) | One meaning per term |
| [RRG suite](rrg-suite.md) | Where SWAG fits among the suite's products |
| [Deploy](../deploy/README.md) | Local launchers |
| [Bench](../bench/README.md) | Running the competitor comparison |

## Reference

How-to guides for existing tools. Each is accurate for its own tool. None of them is a plan.

| Document | Covers |
|---|---|
| [Developer workspace](reference/developer-workspace.md) | The local UI at `/dev.html`, its status API and traces |
| [Knowledge template adapter](reference/knowledge-template-adapter.md) | Template previews and answer validation over MCP |
| [Decision modes and knowledge mesh](reference/decision-modes-and-knowledge-mesh.md) | The design notes behind the three modes and the question bank |
| [Deployment readiness](reference/deployment-readiness.md) | Release gates, and the rule that assistant-written labels qualify nothing |
| [Routing data and evaluation](reference/routing-data-and-evaluation.md) | Admitting reviewed training data and running pinned evaluations |
| [Task outcome workflow](reference/task-outcome-workflow.md) | Recording real task outcomes |
| [Training evidence](reference/training-evidence.md) | Training progress and artifact verification |
| [Training operations](reference/training-operations.md) | Placement, preflight and the training operations UI |
| [Serving load measurements](reference/serving-load-measurements.md) | Measuring a model server under load |
| [Passive capture](reference/passive-capture.md) and [capture watch](reference/passive-capture-watch.md) | Recording routing observations |
| [Naming checker](reference/naming-checker.md) | RRFLOW key naming rules and the checker |

## Evidence

Records of specific measurements and verifications, each true on its own date:
[decision brief evaluation](evidence/decision-brief-evaluation.md),
[model outcome correlation](evidence/model-outcome-correlation.md),
[runtime verification](evidence/runtime-verification.md),
[checkpoint binding](evidence/checkpoint-binding-20261031.md),
[testing the native binary](evidence/testing-binary.md),
[legacy training retirement](evidence/legacy-training-retirement.md).

## History

Earlier plans and narratives, kept so decisions can be traced. They are not instructions, and
where they disagree with the System One plan, the plan wins:
[current context log](history/current-context.md),
[decision-router alpha plan](history/decision-router-alpha-plan.md),
[implementation plan](history/implementation-plan.md),
[product direction](history/product-direction.md),
[outcome research plan](history/outcome-research-plan.md),
[decision-router research](history/decision-router-research.md),
[engine plan and source identity](history/engine-plan-source-identity.md),
[training control plan](history/training-control-plan.md),
[controller compression research](history/controller-compression-research.md),
[real task review](history/real-task-review.md),
[experiment evidence](history/experiment-evidence.md),
[engine testing boundary](history/engine-testing-boundary.md),
[former README baseline](history/readme-system-one-baseline.md).
