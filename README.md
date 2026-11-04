# SWAG - your project's system-one controller

SWAG is the decision router in the [Reason Ready Governance (RRG) suite](docs/rrg-suite.md).
It returns direction and guidance rather than finished content. It is
source-available under the [Business Source License 1.1](LICENSE) and is
pre-release; read the status notes below before relying on any result.

SWAG is being built for vibe coders who want to turn an idea into a real project
or platform. It carries the user's intent and engineering constraints into their
coding workflow, selects relevant checks, and routes work according to project
context. The product goal is a personal, configurable controller that becomes
more useful through measured outcomes.

The intended decision modes are **choice, score and binary**, backed by a built-in
development best-practices knowledge mesh and project templates whose fulfillment
is verified through RRFlow. See [the decision and template design](docs/decision-modes-and-knowledge-mesh.md)
for existing foundations and the remaining implementation.

**RRFlow** owns accepted plans, authorization, execution and durable receipts;
SWAG proposes bounded decisions through its public contracts.
**RROFLOW (rroflow.ai)** is the intended AI observability and learning sink.
The complete connected project workflow and automatic learning remain unqualified.
Start with [current context and verified status](docs/current-context.md), then
[product direction and release gates](docs/product-direction.md).

The model qualification milestone compares the original Qwen baseline, one
versioned custom BF16 checkpoint, and that same checkpoint after quantization.
See the [engine-owned plan and source-identity design](docs/engine-plan-source-identity.md)
for artifact lineage, edit detection, scoped replanning, and PR evidence gates.
Source-edit successor planning and that three-way qualification remain open.

The current experiment starts with **Qwen3-Coder-30B-A3B-Instruct in BF16**;
compression follows baseline and custom-checkpoint evaluation. The
[routing observation collector](docs/passive-capture.md) now validates JSONL,
appends without overwriting prior observations, and records model/effort/access
separately. It remains an explicit emitter, not an automatic background watcher.
The [reviewed routing-data pipeline and evaluator](docs/routing-data-and-evaluation.md)
now validate admission evidence, separate train/development/acceptance data, and
run digest-pinned protocols. A historical custom BF16 intent checkpoint is
merged and serving privately. It was trained on assistant-inferred labels;
15/21 development matches versus the base's 14/21 do not establish independent
routing quality. Its synthetic routing experiment matched 7/13 with five policy
violations. Preserve those results as provisional history. New training requires
admitted real observations, independent outcome reviews and explicit permission.
The [TypeScript evidence viewer](ui/README.md) makes these results inspectable.
See the [research and integration decision](docs/decision-router-research.md) for
Liquid RIPL/d1 comparisons, learning signals and the engine-owned integration path.
The [execution plan](docs/implementation-plan.md) and
[experiment evidence](docs/experiment-evidence.md) track the real task corpus,
custom BF16 work, measured d1 comparison and authenticated local RROFLOW round trip.

## Current engine testing boundary

[PR206](https://github.com/rrflow/rrflow-development/pull/206) implements the
engine-owned experimental proposal operation. A source-identified Windows
development executable made real BF16 calls and passed restart, replay rejection,
configuration replacement, session closure, Stop and lost-response checks.
The profile had one candidate; this proves transport and admission behavior,
not provider selection quality, worker execution or ordinary-edit replanning.
Earlier protected merging failed during macOS APFS image creation (`Resource
busy`); that failure is retained. PR206 subsequently merged as `5b4039fe`, with
successful protected checks. See [deployment readiness](docs/deployment-readiness.md)
for the remaining release gates and [current context](docs/current-context.md)
for exact build identities.

[Merged PR222](https://github.com/rrflow/rrflow-development/pull/222) adds the
catalogue-derived Rust client proposal binding needed by Connectome. Its native
example completed a real BF16 proposal with identical restart readback and replay
denial. Connectome draft PR30 now contains the proposal/recovery and plan-panel
integration, with passing candidate CI. Its dependencies and complete real-task
acceptance remain open; this is not a released controller.

The [native Windows engineering bundle](docs/testing-binary.md) is now available
locally: a 33.9 MB ZIP with the optimized primary executable, provenance, verifier
and trial instructions. Actual relocation, proposal/reopen/replay and three fault
cases passed. A configuration-change trial also exposed an invalid model effort
choice, which the engine rejected; that failure is retained. The model remains
unqualified. [Merged PR212](https://github.com/rrflow/rrflow-development/pull/212)
provides the packaging tooling; signed releases, container deployment and the
complete Connectome workflow remain open. See [current context](docs/current-context.md).

## Get a decision brief

Describe a request and SWAG returns the few checks that matter, a stakes call and
a direction, or abstains when nothing stands out. It runs without a project profile,
and it writes nothing to your project.

```powershell
python tools/swag.py brief --repo C:/work/my-app --intent "Add Stripe billing and make sure webhooks can't double charge"
```

Agents get the same result from the `decision_brief` MCP tool. A brief holds up to
seven checks with their text, in under 4 KB in the requests tried so far.
`decision_route` still lists every composed question ID without text. When
`SWAG_LFG_CONNECTION_FILE` is set, the request is also sent to that local LFG
instance, and a low-effort signal on elevated stakes is reported as a conflict.

Without a decision model, the brief is a rules-only baseline whose stakes call comes
from [policy terms](config/boundaries/decision_brief_policy.yaml). Treat it as a weak
signal: on a held-out development set it found none of the elevated requests described
without the usual words, and it raised checks on about half of the harmless ones.

To use a decision model, set `SWAG_DECISION_MODEL_CONNECTION_FILE` to a JSON file naming
a loopback service that answers `POST /v1/systemone`:

```json
{"schemaVersion": 1, "baseUrl": "http://127.0.0.1:8791", "model": "your-model", "revision": "pinned-revision",
 "timeoutMs": 10000, "maxRequestBytes": 262144, "maxResponseBytes": 262144}
```

The model then decides stakes and domains and ranks the checks, and the brief reports
`basis: decision_model` with its likelihoods. If the service fails, the brief falls back
to the rules and reports `basis: rules_only` with `decisionModel.state: unavailable`.

Either way, the brief selects existing questions and does not judge whether your project
is correct. Model thresholds were chosen on assistant-labelled development data, so no
route is qualified.

## Legacy policy preview

The [developer workspace](docs/developer-workspace.md) adds a live local UI at
`/dev.html`, a versioned status API, content-free traces and an authenticated
RRFlow diagnostics probe. It reads registered training artifacts and dataset
readiness. UI training launch, subscription usage measurement, Connectome
integration and automatic promotion remain unavailable.
The [training-control research and execution plan](docs/training-control-plan.md)
maps the remaining work. [Training evidence tools](docs/training-evidence.md)
provide recorded progress/loss, interruption observations and explicit artifact
verification without introducing a UI-owned training scheduler.

Current status: **local preview alpha**. This path runs the existing question
composition and routing policies without calling a model. A preview is not a
verdict that the application is correct or that the planned model is available.

From this checkout, using Python 3.10+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/swag.py init --repo C:/work/my-app --intent "Build a booking platform"
.\.venv\Scripts\python.exe tools/swag.py doctor --repo C:/work/my-app
.\.venv\Scripts\python.exe tools/swag.py preview --repo C:/work/my-app
```

`init` creates `.swag/project.json` in an existing project directory and refuses
to overwrite it. The profile holds intent, maturity, budget mode, test-harness
availability, and the operator attunement profile. Set those values to match the
project. `preview --intent "Add billing"` previews a particular task without
changing the saved intent. Add `.swag/` to the target project's ignore rules;
local decision artifacts can contain repository paths.

`doctor` checks the profile, YAML dependency, and a real local controller run.
`preview` prints detected stacks, the planned tier and its reason, question
counts, measured local duration, and the paths to saved decision/event files.
The question-band check measures policy coverage, not answer correctness.

### Use from RRFlow or a coding agent

The stdio bridge at `tools/swag_mcp_server.py` exposes `project_preview` with
`{"repo":"C:/work/my-app","intent":"Add billing"}`. Launch it using the
absolute path to this checkout's virtual-environment Python and script. The tool
uses the same saved profile and records as the CLI. Registering it in RRFlow's
actual engine runtime remains to be verified in the engine checkout.

The existing `POST /v1/decision` service remains available for explicit payloads;
it does not automatically load the new project profile.

### Send a preview record to RROFLOW

Each preview saves a `rroflow.turn/v1` event under `.swag/events/`. It includes
the project slug, run identity, timestamps, and tool outcome. Prompt text,
responses, repository paths, and credentials are omitted. Preview token counts
are zero because no model was invoked; this is not a model-usage estimator.

Set `RROFLOW_INGEST_URL` to your ingest base URL and `RROFLOW_INGEST_KEY` through
your environment, then explicitly publish the event path printed by `preview`:

```powershell
python tools/swag.py publish --event C:/work/my-app/.swag/events/EVENT_ID.json
```

Publishing uses the existing authenticated `POST /v1/turns` contract. Retrying
the same event keeps its ID so ingest can upsert it. Events stay local until
published; no hosted endpoint is assumed. The adapter has offline contract and
transport tests; live deployment acceptance remains unverified.

### Validate changes

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## Naming governance baseline

Shipped defaults and a stdlib-only checker for RRFLOW key naming, derived from the
**Clyffy 09 Glossary ADR (Canonical Naming)**, section 2 rule 3 ("Absorb jargon, don't dump it").

```
config/rrflow.naming.yaml    naming rules (shipped defaults)
config/swag.paths.yaml       per-platform user config/data/state/cache folders
tools/check_naming.py        checker (Python 3.10+, stdlib only)
tests/fixtures/*.txt         sample key lists (lane keys, sample seams, Doc 10 seam snapshot)
```

## SWAG system-one controller baseline

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

- SWEBOK-aligned shared predicates: [shared_predicates.yaml](./config/boundaries/question_sets/shared_predicates.yaml)
- Next.js battery: [nextjs.yaml](./config/boundaries/question_sets/nextjs.yaml)
- Rust battery: [rust.yaml](./config/boundaries/question_sets/rust.yaml)
- Language batteries (including Java, JavaScript, C, C++, PHP, Python, Ruby, SQL): [question_sets/](./config/boundaries/question_sets/)
- Routing registry and stack detection contract: [stack_registry.yaml](./config/boundaries/stack_registry.yaml)
- Runtime gating/citation policy: [runtime_policy.yaml](./config/boundaries/runtime_policy.yaml)
- Research feed bindings for SWEBOK + AI decisions + Cloudflare + JEV + RRFlow alignment: [research_sync_registry.yaml](./config/boundaries/research_sync_registry.yaml)
- RRFlow project sync template (isolated/shared mode): [rrflow.sync.template.yaml](./config/rrflow.sync.template.yaml)

The controller composes decisions as:
`shared_predicates ∪ stack(value) ∪ domain(detected boundaries)` via [boundary_controller.py](./tools/boundary_controller.py).

### Resource optimization hypothesis

The Python preview narrows a decision surface using shared, stack and domain
question batteries. Its legacy size-tier defaults are not the engine's model
selection authority. The engine accepts explicitly configured bindings, limits
and evidence. Short controller outputs can reduce generation/cache costs, but
they do not remove resident model weights. Latency, quality and a 29 GB serving
footprint require measurement against the same qualified checkpoint. A later goal
is a 19 GB footprint through a custom RRFlow shard and KV-cache system; that
system is not built and the number is not measured. See the
[footprint stages](docs/rrg-suite.md#swag-serving-footprint).

### RRFlow integration path

SWAG is intentionally RRFlow-friendly:

1. RRFlow naming/governance baseline: [rrflow.naming.yaml](./config/rrflow.naming.yaml)
2. System-one policy + question composition: [system_one_controller_policy.yaml](./config/boundaries/system_one_controller_policy.yaml) + [boundary_controller.py](./tools/boundary_controller.py)
3. Runtime decision endpoint for orchestration: [swag_decision_service.py](./tools/swag_decision_service.py)
4. Provider/tier routing and operator profiles: [providers.template.yaml](./config/frontier/providers.template.yaml) + [operator_profiles.template.yaml](./config/attunement/operator_profiles.template.yaml)
5. Legacy tier-policy scaffold (not a qualified model selection): [system_one_tier_policy.yaml](./config/boundaries/system_one_tier_policy.yaml)

### Hosted + configurable runtime profile

SWAG is designed to run in three modes without breaking the controller contract:

- standalone/self-hosted operation
- RRFlow-parallel projects sharing decision sources
- per-project overrides layered over global defaults

The runtime bootstrap layer is now explicit:

- Global runtime defaults: [global_defaults.template.yaml](./config/runtime/global_defaults.template.yaml)
- MCP server templates: [mcp_servers.template.yaml](./config/runtime/mcp_servers.template.yaml)
- Agent compatibility template: [agent_compatibility.template.yaml](./config/runtime/agent_compatibility.template.yaml)
- Effective runtime merge script: [swag_runtime_bootstrap.py](./tools/swag_runtime_bootstrap.py)
- One-command setup helper: [swag_setup.py](./tools/swag_setup.py)

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

The [tuning blueprint](config/training/swag_28b_tuning_plan.template.yaml) and
`tools/swag_28b_tuning_plan.py` retain legacy filenames for compatibility, but
now describe this sequence. The older fast-28B profile is superseded.
See [current context](docs/current-context.md) for measurements and next work.

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
- [config/training/user_seed_dataset.template.yaml](./config/training/user_seed_dataset.template.yaml)

Completed examples still need provenance, consent, independent label review and
split assignment. Filling the file alone does not qualify it for training.

### Capture observations for reviewed training data

`tools/swag_passive_capture.py` explicitly emits observations supplied by a caller
and changed path names from Git status. It does not watch diffs, fetch issue
titles or collect route overrides automatically. Records append to ignored local
JSONL and are validated against
[passive_capture.schema.json](config/training/passive_capture.schema.json).

Every record starts unreviewed with training consent false. Unknown outcomes stay
null; user acceptance is not ground truth. Record provider, exact model, effort,
access mode and authorized binding separately. See the
[capture guide](docs/passive-capture.md) for the current CLI and admission boundary.

### Canonical repository layout for scale and growth

The project now includes a canonical structure manifest to keep the repo organized as it grows.

Manifest:
- [config/organization/canonical_layout.yaml](./config/organization/canonical_layout.yaml)

The structure is designed so that:

- `.swag/` holds ignored runtime secrets and cluster access instructions
- `config/` holds source-of-truth policy, source manifests, runtime templates, and training configs
- `tools/` holds operational scripts and data-pipeline logic
- `files/` holds generated artifacts, evals, manifests, and benchmark outputs, and stays local apart from two evidence files
- `boundaries/` and `tests/` remain focused on governance, validation, and decision contracts
- `chat-archive/` and `chat-candidates/` are archival/experimental space, not active runtime logic, and stay local

This is the 10x-engineer pattern: separate source of truth, generated artifacts, secrets, and experimental space so the project remains coherent as it grows.

### Delivery order

Use the [current delivery sequence](docs/current-context.md#delivery-sequence-and-acceptance).
Existing scripts, generated scenarios and runbooks are scaffolding. They do not
establish trained-controller quality, distributed-training qualification or
landed engine integration. Release claims require the relevant PRs and evidence.

### System-one documentation index

If you want one place to understand and operate the controller, start here:

1. Controller policy and threshold contract
   - [config/boundaries/system_one_controller_policy.yaml](./config/boundaries/system_one_controller_policy.yaml)
2. Core battery composition logic (shared + stack + domain)
   - [tools/boundary_controller.py](./tools/boundary_controller.py)
3. Decision service runtime and routing behavior
   - [tools/swag_decision_service.py](./tools/swag_decision_service.py)
4. Provider routing and key pools
   - [config/frontier/providers.template.yaml](./config/frontier/providers.template.yaml)
5. Operator scope and execution profile
   - [config/attunement/operator_profiles.template.yaml](./config/attunement/operator_profiles.template.yaml)
6. AIDevSpec quality gates and runtime policy
   - [config/aiddevspec/default.yaml](./config/aiddevspec/default.yaml)
7. Local model adapter definitions
   - [config/local/model_adapters.template.yaml](./config/local/model_adapters.template.yaml)
8. Tier experiment harness (scenario pack + scoring + execution plan)
   - [tools/controller_model_experiment.py](./tools/controller_model_experiment.py)
9. Tier promotion policy signals and fallback order
   - [config/boundaries/system_one_tier_policy.yaml](./config/boundaries/system_one_tier_policy.yaml)
10. SWAG↔RRFlow sync and research-feed bindings
   - [config/boundaries/research_sync_registry.yaml](./config/boundaries/research_sync_registry.yaml)
   - [config/rrflow.sync.template.yaml](./config/rrflow.sync.template.yaml)
11. Global runtime defaults, project override behavior, and MCP-ready deployment
   - [config/runtime/global_defaults.template.yaml](./config/runtime/global_defaults.template.yaml)
   - [config/runtime/mcp_servers.template.yaml](./config/runtime/mcp_servers.template.yaml)
   - [tools/swag_runtime_bootstrap.py](./tools/swag_runtime_bootstrap.py)

### Documentation status (system-one scope)

- [x] Controller architecture and threshold policy documented
- [x] Routing and provider template documentation in repo
- [x] Attunement and AIDevSpec behavior documented
- [x] Training scaffold and dataset-quality docs documented
- [ ] End-to-end trace/replay contract doc (next gap)
- [ ] Production rollout runbook (next gap)

## Legacy cluster and training scaffolds

The following older templates are not the active BF16 launch configuration.
Topology and tier settings must be verified before use. SWAG includes a template
for a 3-node Spark GB10-style topology
(384GB unified memory total) and a model catalog template for tier benchmarking.

- [config/training/spark_cluster_profile.template.yaml](./config/training/spark_cluster_profile.template.yaml)
- [config/training/model_catalog.template.yaml](./config/training/model_catalog.template.yaml)
- [config/training/tier_metrics.template.json](./config/training/tier_metrics.template.json)

Use these with the experiment harness to generate execution plans that include:

- provider/key routing plan
- model-tier candidate families (Qwen, Phi, and additional baselines)
- cluster metadata and training defaults for runbook generation
- Historical tier labels: 14B, 7B and 27-28B; not the active BF16 experiment

```powershell
python tools\controller_model_experiment.py --pretty `
  --model-catalog config\training\model_catalog.template.yaml `
  --cluster-profile config\training\spark_cluster_profile.template.yaml `
  --tier-metrics-file config\training\tier_metrics.template.json `
  --emit-promotion-scorecard
```

## Reviewed training and historical scaffolds

New training uses independently reviewed real observations admitted by
`tools/swag_routing_dataset.py`. Invoke `tools/swag_unsloth_train.py` explicitly
with that export's `--admitted-dataset-dir`, exact train/development files, an
explicit `--seed`, and the chosen model/runtime settings. See the
[admission and evaluation guide](docs/routing-data-and-evaluation.md).
Acceptance data must not enter training. Human review, consent and real outcome
evidence are still required; no new dataset is approved by this documentation.

The former synthetic dataset/runbook generator, raw-dataset LoRA trainer and
runbook execution path are retired. They refuse before creating data, importing
GPU libraries or launching commands. The legacy operations UI cannot run that
pipeline. Existing datasets, manifests and runbooks remain historical artifacts;
none are relabelled or deleted. `tools/run_training_job.py --list-steps` and
command printing remain available for inspection, but `--execute` is refused.

## Quality-of-life local UI

The legacy local operations UI supports historical artifact inspection and:

- an explicitly disabled retired training pipeline
- dataset quality run
- experiment generation run
- live job status and latest manifest/quality summaries
- human-in-the-loop dataset review queue (approve/reject/pending with edits and reason tags)
- historical curated exports, which do not satisfy reviewed-data admission

```powershell
python tools\swag_ops_ui.py --host 127.0.0.1 --port 8790
```

Then open: `http://127.0.0.1:8790/`

Reviewer artifacts are generated locally and are not distributed:

- `files/training/data/review_state.json`
- `files/training/data/controller_sft.curated.jsonl`
- `files/training/data/controller_sft.curated.report.json`

## DABO + ring placement planning

Placement is now policy-driven and explicit in code:

- [topology.template.yaml](./config/training/topology.template.yaml)
- [placement_policy.template.yaml](./config/training/placement_policy.template.yaml)

Generate plan from CLI:

```powershell
python tools\swag_placement_planner.py --pretty
```

Override mode:

```powershell
python tools\swag_placement_planner.py --mode ring_only --pretty
```

The Ops UI also exposes `/api/placement/plan` and a "Plan DABO/ring placement"
button for quick inspection.

## Spark ring preflight

Use the Spark preflight checker before distributed training to surface missing
SSH access, missing commands/packages, missing paths, and missing env vars.

- [spark_preflight.template.yaml](./config/training/spark_preflight.template.yaml)

Dry run:

```powershell
python tools\swag_spark_preflight.py --config config\training\spark_preflight.template.yaml --dry-run --pretty
```

Live checks (set `enabled: true` in config first):

```powershell
python tools\swag_spark_preflight.py --config config\training\spark_preflight.template.yaml --pretty
```

Multi-node ring smoke check (run from `spark-01` with the repo + `.venv` on all nodes):

```bash
torchrun --nnodes=3 --nproc_per_node=1 --node_rank=0 \
  --rdzv_backend=c10d --rdzv_endpoint=spark-01:29511 tools/ring_smoke.py
```

If nodes resolve hostnames to loopback during distributed init, set explicit interface bindings:

```bash
export GLOO_SOCKET_IFNAME=eth0
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE=1
```

The former generated training commands are historical and no longer executable
through the SWAG runbook launcher. Cluster preflight does not admit a dataset or
authorize training; use the reviewed training workflow above.

## Layering

Later layers win:

1. **Shipped defaults**: `config/` in this repo (or `--shipped-dir`, or env `SWAG_SHIPPED_CONFIG_DIR`).
2. **User override**: `<user config dir>/rrflow.naming.yaml`. The dir comes from `swag.paths.yaml`
   for the current platform, or from env `SWAG_CONFIG_DIR` if set.
3. **CLI overrides**: each `--config FILE`, in order.

Merge rule: mappings merge key by key; **lists and scalars replace**. So a user file that only sets
`reserved_words:` / `  words: [security]` bans only `security`, and every other field keeps the shipped value.
If the user file is missing, the shipped defaults apply. `--no-user` skips layer 2.

## Per-user folders (app name `swag`)

| platform | config | data | state | cache |
|---|---|---|---|---|
| Windows | `%APPDATA%\swag` | `%LOCALAPPDATA%\swag` | `%LOCALAPPDATA%\swag\state` | `%LOCALAPPDATA%\swag\cache` |
| Linux | `$XDG_CONFIG_HOME/swag` (`~/.config/swag`) | `$XDG_DATA_HOME/swag` (`~/.local/share/swag`) | `$XDG_STATE_HOME/swag` (`~/.local/state/swag`) | `$XDG_CACHE_HOME/swag` (`~/.cache/swag`) |
| macOS | `~/Library/Application Support/swag` | same as config | `.../Application Support/swag/state` | `~/Library/Caches/swag` |

Templates use `${VAR}` and `${VAR:-fallback}`. `${APP}` is `app_name`. The checker only
**resolves** these paths and never creates folders. Deployment creates them.

## rrflow.naming.yaml fields

| field | meaning |
|---|---|
| `schema_version` | config format version (1) |
| `source.*` | the ADR this file implements |
| `lanes.keys` | closed lane set (ADR section 5). Replacement targets must be in it |
| `lanes.enforce_closed_set` | `lane_key` values outside the set are violations (fail closed, section 2 rule 4) |
| `reserved_words.words` | banned capability words (section 2 rule 3) |
| `reserved_words.citation` | the ADR rule text |
| `reserved_words.applies_to` | key kinds the ban covers: `lane_key`, `api_seam_key` (`payload_field` is also allowed) |
| `reserved_words.match.mode` | `whole_segment`: the key is split on `segment_separator` (`_`) and a segment must equal a word |
| `reserved_words.match.case_sensitive` | `false`, so `Security_x` is also a hit |
| `reserved_words.match.extra_forms` | optional extra spellings per word (e.g. `testing: [test]`). Empty by default |
| `reserved_words.replacements` | suggested lane key per word (used to build the suggested key) |
| `reserved_words.report_replacement_collisions` | warn when two words map to one lane |
| `on_violation.mode` | `error` (exit 1, default) or `warn` (exit 0). CLI `--on-violation` overrides it |
| `patterns.<kind>.regex` | allowed shape: snake_case for lane/seam keys, lowerCamel for payload fields |
| `patterns.anti_names.globs` | never-mint names: `*_v2`, `new_*` (section 3) |

**Known collision:** `design` and `implementation` both map to `shape`. The ADR says shape
absorbs "implementation + design form", but orient also absorbs "design framing". The checker
prints a config warning about this until the mapping is decided.

## Running the checker

```powershell
# show resolved paths and loaded layers (creates nothing)
python tools\check_naming.py --dry-run

# lane keys (also enforces the closed lane set)
python tools\check_naming.py --kind lane_key tests\fixtures\lane_keys.txt

# API seam keys (the default kind)
python tools\check_naming.py tests\fixtures\sample_seam_keys.txt

# large lists: per-word counts plus the first 10 violations
python tools\check_naming.py --summary --limit 10 tests\fixtures\doc10_seam_keys.txt
```

Input: a `.txt` file with one key per line (`#` comments allowed), or a `.yaml` file holding
a list, a `keys:` list, or a block mapping of kind to list
(`lane_key:` / `api_seam_key:` / `payload_field:`, each with a list under it).
Output: one line per violation, with a suggested replacement for reserved-word hits.
Exit code: 1 when there are violations in `error` mode, otherwise 0.

The config reader supports a YAML subset only (block maps and lists, `[a, b]` inline lists,
quoted or plain scalars, comments) so the checker stays stdlib-only. Keep user overrides in that subset.

## Repository contents

This repository holds source, configuration, tests and documentation. Session
logs, generated datasets, model artifacts, binaries and `.swag/` evidence stay
local and are not distributed. Documents that cite paths under `files/` or
`.swag/` record evidence from the development environment; those paths may not
exist in a fresh clone. Two small evidence files under
`files/controller_experiments/` are included because the docs and tools read them.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for checks and pull-request expectations.
Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## License

SWAG is licensed under the [Business Source License 1.1](LICENSE), with a grant for
non-commercial production use. It is source-available, not open source. Each
version converts to the Apache License 2.0 four years after it is first published.
The license covers this repository only, not other RRG products.
