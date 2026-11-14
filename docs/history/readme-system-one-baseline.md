# SWAG system-one controller baseline (former README section)

> **Historical record.** Kept as evidence of what was planned, decided or measured at the time. It is not current instructions; see the [System One plan](../system-one-plan.md) and the [docs index](../index.md).

SWAG is intended to function as a system-one decision shell rather than a single static prompt or repo checklist.
The current baseline includes:

- a shared + stack + domain question composition contract
- a system-one controller policy enforcing the 50-75 main-question band
- model-tier planning for 7B, 14B, and 27-28B routes
- frontier provider and per-key usage templates
- operator attunement profiles that define context scope and execution policy
- a default AIDevSpec file for global developer behavior, quality gates, and routing preferences
- a local OpenAI-compatible adapter path for self-hosted model deployment

This keeps the stack configurable and extension-friendly while preserving the core decision matrix.

### SWEBOK + stack research coverage (what already exists)

The research-backed question batteries are already in-repo and active in routing:

- SWEBOK-aligned shared predicates: [shared_predicates.yaml](../../config/boundaries/question_sets/shared_predicates.yaml)
- Next.js battery: [nextjs.yaml](../../config/boundaries/question_sets/nextjs.yaml)
- Rust battery: [rust.yaml](../../config/boundaries/question_sets/rust.yaml)
- Language batteries (including Java, JavaScript, C, C++, PHP, Python, Ruby, SQL): [question_sets/](../../config/boundaries/question_sets/)
- Routing registry and stack detection contract: [stack_registry.yaml](../../config/boundaries/stack_registry.yaml)
- Runtime gating/citation policy: [runtime_policy.yaml](../../config/boundaries/runtime_policy.yaml)
- Research feed bindings for SWEBOK + AI decisions + Cloudflare + JEV + RRFlow alignment: [research_sync_registry.yaml](../../config/boundaries/research_sync_registry.yaml)
- RRFlow project sync template (isolated/shared mode): [rrflow.sync.template.yaml](../../config/rrflow.sync.template.yaml)

The controller composes decisions as:
`shared_predicates ∪ stack(value) ∪ domain(detected boundaries)` via [boundary_controller.py](../../tools/boundary_controller.py).

### Resource optimization hypothesis

The Python preview narrows a decision surface using shared, stack and domain
question batteries. Its legacy size-tier defaults are not the engine's model
selection authority. The engine accepts explicitly configured bindings, limits
and evidence. Short controller outputs can reduce generation/cache costs, but
they do not remove resident model weights. Latency, quality and a 29 GB serving
footprint require measurement against the same qualified checkpoint. A later goal
is a 19 GB footprint through a custom RRFlow shard and KV-cache system; that
system is not built and the number is not measured. See the
[footprint stages](../rrg-suite.md#swag-serving-footprint).

### RRFlow integration path

SWAG is intentionally RRFlow-friendly:

1. RRFlow naming/governance baseline: [rrflow.naming.yaml](../../config/rrflow.naming.yaml)
2. System-one policy + question composition: [system_one_controller_policy.yaml](../../config/boundaries/system_one_controller_policy.yaml) + [boundary_controller.py](../../tools/boundary_controller.py)
3. Runtime decision endpoint for orchestration: [swag_decision_service.py](../../tools/swag_decision_service.py)
4. Provider/tier routing and operator profiles: [providers.template.yaml](../../config/frontier/providers.template.yaml) + [operator_profiles.template.yaml](../../config/attunement/operator_profiles.template.yaml)
5. Legacy tier-policy scaffold (not a qualified model selection): [system_one_tier_policy.yaml](../../config/boundaries/system_one_tier_policy.yaml)

### Hosted + configurable runtime profile

SWAG is designed to run in three modes without breaking the controller contract:

- standalone/self-hosted operation
- RRFlow-parallel projects sharing decision sources
- per-project overrides layered over global defaults

The runtime bootstrap layer is now explicit:

- Global runtime defaults: [global_defaults.template.yaml](../../config/runtime/global_defaults.template.yaml)
- MCP server templates: [mcp_servers.template.yaml](../../config/runtime/mcp_servers.template.yaml)
- Agent compatibility template: [agent_compatibility.template.yaml](../../config/runtime/agent_compatibility.template.yaml)
- Effective runtime merge script: [swag_runtime_bootstrap.py](../../tools/swag_runtime_bootstrap.py)
- One-command setup helper: [swag_setup.py](../../tools/swag_setup.py)

This gives you a single runtime contract for:

- global default behavior
- project-specific overrides
- RRFlow parallel awareness
- MCP integration for repo and system context
- deterministic deploy-time configuration
- smoother compatibility across Codex, Claude, Grok, and local OpenAI-compatible agents

### Vibe-coder installation path (easy setup)

The project is intentionally set up so a non-advanced user can get a working controller without custom scripting:

```powershell
python -m pip install -r requirements.txt
python tools\swag_setup.py --project-name swag --write-env --write-agent-config
python tools\swag_runtime_bootstrap.py --pretty
python tools\boundary_controller.py --pretty --intent-text "secure AI app architecture"
```

This produces the baseline environment file, loads the compatibility profile, and validates the routing contract before any model calls are executed.

### Agent compatibility and provider stack

SWAG is intentionally provider-agnostic. The compatibility file is built around the practical baseline used by the major coding agents:

- Codex: OpenAI-compatible or local OpenAI-compatible deployment
- Claude: Anthropic-compatible route
- Grok: xAI-compatible route
- Generic local model: local OpenAI-compatible endpoints / Ollama

This keeps the controller compatible with the ways real vibe coders actually operate, while still preserving strong routing and quality controls.

### SWAG control panel: one intake form to one decision output

The project also includes a single-entry control-panel flow to turn a user intake into a single controller output and a source provenance report without scattering the user across multiple config files.

```powershell
python tools\swag_control_panel.py --intake config\control_panel\swag_control_panel_input.example.yaml --output-dir files\swag_control_panel --pretty
```

This generates:

- project_config.yaml
- controller_decision.json
- source_provenance_report.json
- control_panel_summary.json

This is the workflow that makes the operating model feel like a real SWAG control panel rather than a bag of scripts:

1. user fills a single intake form
2. runtime + project config are merged once
3. controller composes the decision battery
4. source provenance attaches OpenAI / Cloudflare / JEV / SWEBOK / RRFlow evidence
5. a concise summary is exported for follow-on decision work

### Alpha evidence and optimization comparison

The project also emits an alpha-stage comparison report that explicitly shows how vendor decision families and tier optimization tradeoffs are encoded in the controller.

```powershell
python tools\swag_alpha_comparison.py --output files\alpha_evidence\vendor_and_tier_comparison.json --pretty
```

This produces a comparison of:

- OpenAI reasoning + structured outputs
- Cloudflare runtime and edge/queue/vector patterns
- TypeSafe/JEV as an experimental architecture decision input
- RRFlow + project-level override logic as your own governing layer
- current 7B / 14B / 27-28B optimizer tradeoffs from the active metrics artifact

This report describes encoded policies and supplied metrics. Generating it does not establish measured vendor performance or an optimal model tier.

### BF16-first custom controller milestone

The selected base is **Qwen3-Coder-30B-A3B-Instruct in BF16**. The private
baseline serves requests but matched only 4/8 synthetic routing smoke cases.
It is not a custom SWAG checkpoint or a qualified autonomous controller.

Build reviewed datasets and a frozen evaluator, train and reload custom BF16,
then quantize that exact checkpoint toward a **29 GB total serving footprint**.
Compare the original BF16 base, custom BF16 and custom quantized artifacts.
Short routing outputs do not eliminate weight memory. No 6–9 GB promise or
qualified 14B fallback is established. A from-scratch 14B specialist is a later
research goal with its own data and compute feasibility gates.

The tuning blueprint (`config/training/swag_28b_tuning_plan.template.yaml`, removed 2026-11-14) and
`tools/swag_28b_tuning_plan.py` retain legacy filenames for compatibility, but
now describe this sequence. The older fast-28B profile is superseded.
See [current context](current-context.md) for measurements and next work.

### Synthetic dataset scaffolding

The project now includes a concrete dataset builder that takes the captured controller patterns and turns them into real training rows for the SWAG controller.

```powershell
python tools\swag_dataset_builder.py --experiment-dir files\controller_experiments\28b_first_validation --supervised-out files\training\data\swag_supervised.jsonl --unsupervised-out files\training\data\swag_unsupervised.jsonl --manifest-out files\training\manifests\swag_dataset_manifest.json
```

This creates:

- `files/training/data/swag_supervised.jsonl`
- `files/training/data/swag_unsupervised.jsonl`
- `files/training/manifests/swag_dataset_manifest.json`

The supervised set is built from the generated controller scenario batteries, with strict JSON labels for selected_question_ids, skipped_question_ids, route_target_tier, and confidence. The unsupervised set is built from repo source files and boundary docs so the controller also gets real next-token and context-preservation data grounded in the SWAG project itself.

These generated scenarios support development checks. They are not independently labelled real-world outcomes or a fresh acceptance holdout; dataset admission remains separate.

### Optional user-authored seed dataset flow

This older helper creates placeholders for manually supplied examples. Reviewed
workflow observations can also supply data; users need not fill a large static
dataset to use SWAG. Placeholders must never enter training or evaluation.

Optional seed-file command:

```powershell
python tools\swag_dataset_capture.py --count 50 --output files\training\user_seed_dataset.jsonl
```

This generates a JSONL seed file with placeholder records that you fill in with actual project examples. The required fields are:

- `record_id`
- `scenario_id`
- `task_type`
- `stack`
- `domain`
- `project_name`
- `repo_context`
- `intent_text`
- `selected_question_ids`
- `route_target_tier`
- `confidence`
- `rationale`
- `source_provenance`

Template config:
- [config/training/user_seed_dataset.template.yaml](../../config/training/user_seed_dataset.template.yaml)

Completed examples still need provenance, consent, independent label review and
split assignment. Filling the file alone does not qualify it for training.

### Capture observations for reviewed training data

`tools/swag_passive_capture.py` explicitly emits observations supplied by a caller
and changed path names from Git status. It does not watch diffs, fetch issue
titles or collect route overrides automatically. Records append to ignored local
JSONL and are validated against
[passive_capture.schema.json](../../config/training/passive_capture.schema.json).

Every record starts unreviewed with training consent false. Unknown outcomes stay
null; user acceptance is not ground truth. Record provider, exact model, effort,
access mode and authorized binding separately. See the
[capture guide](../reference/passive-capture.md) for the current CLI and admission boundary.

### Canonical repository layout for scale and growth

The project now includes a canonical structure manifest to keep the repo organized as it grows.

Manifest:
- `config/organization/canonical_layout.yaml` (removed 2026-11-14)

The structure is designed so that:

- `.swag/` holds ignored runtime secrets and cluster access instructions
- `config/` holds source-of-truth policy, source manifests, runtime templates, and training configs
- `tools/` holds operational scripts and data-pipeline logic
- `files/` holds generated artifacts, evals, manifests, and benchmark outputs, and stays local apart from two evidence files
- `boundaries/` and `tests/` remain focused on governance, validation, and decision contracts
- `chat-archive/` and `chat-candidates/` are archival/experimental space, not active runtime logic, and stay local

This is the 10x-engineer pattern: separate source of truth, generated artifacts, secrets, and experimental space so the project remains coherent as it grows.

### Delivery order

Use the [current delivery sequence](current-context.md#delivery-sequence-and-acceptance).
Existing scripts, generated scenarios and runbooks are scaffolding. They do not
establish trained-controller quality, distributed-training qualification or
landed engine integration. Release claims require the relevant PRs and evidence.

### System-one documentation index

If you want one place to understand and operate the controller, start here:

1. Controller policy and threshold contract
   - [config/boundaries/system_one_controller_policy.yaml](../../config/boundaries/system_one_controller_policy.yaml)
2. Core battery composition logic (shared + stack + domain)
   - [tools/boundary_controller.py](../../tools/boundary_controller.py)
3. Decision service runtime and routing behavior
   - [tools/swag_decision_service.py](../../tools/swag_decision_service.py)
4. Provider routing and key pools
   - [config/frontier/providers.template.yaml](../../config/frontier/providers.template.yaml)
5. Operator scope and execution profile
   - [config/attunement/operator_profiles.template.yaml](../../config/attunement/operator_profiles.template.yaml)
6. AIDevSpec quality gates and runtime policy
   - [config/aiddevspec/default.yaml](../../config/aiddevspec/default.yaml)
7. Local model adapter definitions
   - [config/local/model_adapters.template.yaml](../../config/local/model_adapters.template.yaml)
8. Tier experiment harness (scenario pack + scoring + execution plan)
   - [tools/controller_model_experiment.py](../../tools/controller_model_experiment.py)
9. Tier promotion policy signals and fallback order
   - [config/boundaries/system_one_tier_policy.yaml](../../config/boundaries/system_one_tier_policy.yaml)
10. SWAG↔RRFlow sync and research-feed bindings
   - [config/boundaries/research_sync_registry.yaml](../../config/boundaries/research_sync_registry.yaml)
   - [config/rrflow.sync.template.yaml](../../config/rrflow.sync.template.yaml)
11. Global runtime defaults, project override behavior, and MCP-ready deployment
   - [config/runtime/global_defaults.template.yaml](../../config/runtime/global_defaults.template.yaml)
   - [config/runtime/mcp_servers.template.yaml](../../config/runtime/mcp_servers.template.yaml)
   - [tools/swag_runtime_bootstrap.py](../../tools/swag_runtime_bootstrap.py)

### Documentation status (system-one scope)

- [x] Controller architecture and threshold policy documented
- [x] Routing and provider template documentation in repo
- [x] Attunement and AIDevSpec behavior documented
- [x] Training scaffold and dataset-quality docs documented
- [ ] End-to-end trace/replay contract doc (next gap)
- [ ] Production rollout runbook (next gap)
