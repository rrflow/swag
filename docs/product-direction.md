# SWAG product direction

SWAG is the decision router in the [Reason Ready Governance (RRG) suite](rrg-suite.md).
Read [current context](current-context.md) for the dated evidence and next work.

## Intended outcome

A vibe coder describes what they are building, connects their project and coding
agent, and gets a personal system-one controller. It remembers their intent,
applies relevant engineering constraints, helps choose the next action, and
escalates uncertainty with evidence. Users should be able to ship and maintain
real platforms without assembling a training pipeline or understanding model
parameter counts.

The initial delivery target is local operation with an optional hosted path.
Model training is an advanced capability, not a prerequisite for onboarding.

## Product responsibilities

| Component | Responsibility |
|---|---|
| SWAG | Propose fast controller decisions, relevant checks, and eligible routes using engine-bound project intent and preferences |
| RRFlow, the reasoning engine | Own accepted plans, source identity, authorization, budgets, execution, durable state, and evaluated controller promotion |
| RROFLOW, Sentry for AI | Capture outcomes; identify failures, friction, and waste; supply corrections and improvement evidence through explicit integration |

The intended loop is: project intent → SWAG decision → agent/RRFlow execution →
RROFLOW evidence → candidate improvement → held-out evaluation → reversible
promotion. A captured event or a user's correction alone does not demonstrate
that a model or policy is better.

This split follows the owner direction and the adjacent RROFLOW checkout's
`docs/plan/rroflow-ai-plan.md` and `docs/ux/vibe-coder-onboarding.md`. The latter
sets an onboarding target of a first useful signal within ten minutes. That is
a target, not a measured result for SWAG.

## Implemented foundation

- Existing shared, stack, and domain question composition, tier policies,
  attunement profiles, model adapters, and training/evaluation tooling.
- A single project entry point: `tools/swag.py init`, `doctor`, and `preview`.
  The saved project profile drives the actual controller preview.
- CLI and MCP `project_preview` produce the same local decision artifacts and
  content-free preview events, including failed controller runs.
- An explicit publisher targeting RROFLOW's existing `rroflow.turn/v1` and
  `POST /v1/turns` contract. Credentials select the devspace on the server.

This remains a preview alpha. It does not yet provide a complete, optimized
turnkey controller. A successful preview proves that rules and configuration
can execute, not that a model has reasoned correctly or a project is ready to ship.

## Evidence required before release

1. **First useful session.** Fresh Windows and Linux installs reach a useful
   project-specific result through a guided flow. Setup checks show actual
   dependency, provider, and agent connectivity results with actionable fixes.
2. **Reliable execution.** Validate provider/model pairing, structured outputs,
   allowed question IDs, actual budget enforcement, failures, and fallback
   behavior. Preserve the project objective across tasks and sessions.
3. **Measured optimization.** Compare the rules-only path and candidate model
   routes on held-out project scenarios. Record decision quality, escalation
   accuracy, p50/p95 latency, memory, tokens, and known/unknown cost. Report
   hardware and policy/model revisions. Select the smallest route that meets
   declared quality constraints; do not equate a model size with capability.
4. **Engine integration.** Exercise a real RRFlow workflow consuming the project
   controller result, including escalation and failure. The engine checkout and
   its current registration contract must be inspected before implementation.
5. **Observed outcomes.** Send, retrieve, and correlate a real SWAG event in a
   RROFLOW devspace. Verify retry/upsert behavior and metadata-only operation.
   Connect later execution outcomes and user corrections to the decision that
   caused them; the current preview event is only the first part of that trace.
6. **Governed improvement.** Evaluate a candidate against held-out cases, record
   its provenance, promote it reversibly, and verify rollback after regression.

The checked-in `files/controller_experiments/promotion_scorecard.json` reports
zero scored scenarios, `avg_f1: null`, and `insufficient_evidence: true`. It
withholds a recommended default tier. Current 14B/7B/27–28B settings are routing
policy, not proof of an optimal deployment. Older 6–9 GB profiles are superseded. The active sequence is Qwen3-Coder-30B
BF16 base, custom BF16, then evaluated compression toward 29 GB serving memory.
A custom RRFlow shard and KV-cache system aiming for 19 GB is a later goal; it is
not built or measured.
A from-scratch 14B specialist remains a later research goal, not the default.
Claude Fable/Sonnet/Opus and Codex handoffs must account for exact model, effort,
authorized access and measured task strengths.

## Next delivery boundary

Qualify one versioned custom Qwen checkpoint behind an endpoint, comparing the
original base, the custom checkpoint before quantization, and that same checkpoint
after quantization. Bind artifact lineage, a frozen evaluation protocol, and measured
quality, latency and memory to the result. Existing runbooks are not qualification.

The [engine-owned planning and source-identity proposal](engine-plan-source-identity.md)
defines how changed inputs invalidate affected work and produce a successor plan
without trapping an edited project. It is a supporting design for the engine's
existing owners, not a second runtime or completion ledger. Keep this checkout's
Python tools as offline/reference tooling. Engine integration, RROFLOW integration,
and completion claims wait for their relevant PRs and retained acceptance evidence.
