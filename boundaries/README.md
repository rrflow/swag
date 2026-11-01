# boundaries — boundary-question reference and derived config

Owner: hades. Export date: 2026-09-30. Source: Google Docs (read-only export via the Google Docs connector).

```
boundaries/reference/*.md               faithful Markdown export of each source doc (front matter: doc id, title, version, export date, owner, revision id)
boundaries/naming_review.md             naming clashes and proposals (nothing here is applied unless marked "applied")
config/boundaries/stack_registry.yaml   stack registry: keys, canonical labels, marker text, lexicon aliases, status, question-set index
config/boundaries/question_sets/*.yaml  one file per question set: stable ids, text, citation, binds_to, maturity gating
config/boundaries/runtime_policy.yaml   runtime policy overrides for explicit shared gating and section-level default citations
config/boundaries/system_one_controller_policy.yaml system-one threshold and mesh/decision-matrix policy (main question target band)
config/frontier/providers.template.yaml  frontier-provider subscriptions, model-tier routing, and per-key usage policy template
config/attunement/operator_profiles.template.yaml  operator-defined attunement and context-scope template
```

| question set | source doc | version | questions |
|---|---|---|---|
| shared_predicates | Boundary Question Bank — Core Predicates | v0.2 | 67 |
| nextjs | Stack — Next.js (App Router) | v0.1 | 38 |
| vanilla_js (JavaScript) | Stack — JavaScript (vanilla) | v0.1 | 52 |
| typescript | Stack — TypeScript | v0.1 | 43 |
| react | Stack — React | v0.1 | 46 |
| go | Stack — Go | v0.1 | 57 |
| rust | Stack — Rust | v0.1 | 53 |
| domains (iam, privileged_access_management, realtime_messaging, llm_application, billing_and_payments, notifications, files_and_media, search, analytics_and_reporting, settings_and_preferences, onboarding) | Domain Boundaries — user, admin, chat, AI + authored expansions | v0.2 | 125 (18 + 16 + 17 + 18 + 8 + 8 + 8 + 8 + 8 + 8 + 8) |
| specta | Stack — TypeScript (composition subset for Specta contracts) | v0.1 | 5 |
| schemars | Stack — TypeScript (composition subset for schemars contracts) | v0.1 | 5 |
| c | Stack — C | v0.1 | 10 |
| cpp | Stack — C++ | v0.1 | 10 |
| python | Stack — Python | v0.1 | 10 |
| pytorch_lightning | Stack — PyTorch Lightning | v0.1 | 10 |
| java | Stack — Java | v0.1 | 10 |
| php | Stack — PHP | v0.1 | 10 |
| sql | Stack — SQL | v0.1 | 10 |
| drizzle | Stack — Drizzle ORM (TypeScript) | v0.1 | 10 |
| prisma | Stack — Prisma ORM (TypeScript) | v0.1 | 10 |
| ruby | Stack — Ruby | v0.1 | 10 |

Total: 591 questions in 20 question sets.

Reference exports without derived YAML: `stack_category_routing_v0_2.md` (feeds `stack_registry.yaml`) and
`lfg_engine_plan_draft_2026_09_26.md` (LFG_ENGINE_PLAN, pasted text, draft researched 2026-09-26; reference only; kept local and not distributed).
The two pasted-text exports keep the text byte-for-byte below their front matter: blank-line runs were collapsed
in the paste, and the engine plan's tables arrived flattened, one cell per line.

Question id format: `<question_set>.<section_key>.<nn>` (domains: `domains.<domain_key>.<nn>`) (nn = position within the section in the source doc).
`doc_ordinal` = position across the whole doc (shared and stack sets; domain questions are numbered per domain in the source). Every YAML file carries `schema_version: 1`.

The YAML is derived from the reference exports. To change question text, edit the source doc,
re-export, and regenerate; do not hand-edit question text in the YAML.

Not exported (not provided): "LFG Boundary Question Battery draft (2026-09-30)" (named in the bank's status line),
and the engine plan's companion documents LFG_NOTES_v3 and the Fork 1 research report.

## Controller runner

Use [boundary_controller.py](../tools/boundary_controller.py) to execute the routing rule from `stack_category_routing_v0_2.md`:

- `shared_predicates` always included (maturity-gated sections are enforced)
- stack question sets selected from repository markers and optional primary-stack override
- domain questions selected from explicit domain keys or alias matches in `--intent-text`
- overlap handling between shared and stack questions (default: suppress overlapped duplicates)

Example:

```powershell
python tools\boundary_controller.py --repo . --maturity growing --has-test-harness --pretty
```

Gap audit:

```powershell
python tools\boundary_controller.py --audit-gaps --pretty
```

Model-tier experiment pack generation (7B, 14B, 27-28B):

```powershell
python tools\controller_model_experiment.py --repo . --pretty
```

This also emits an execution plan (`execution_plan.json`) that binds scenarios to:
- operator attunement profile (context scope)
- route profile (model/provider preferences)
- per-key policy records (key id, env var presence, budget/rate settings)

Custom attunement/profile selection:

```powershell
python tools\controller_model_experiment.py --repo . `
  --provider-config config\frontier\providers.template.yaml `
  --attunement-config config\attunement\operator_profiles.template.yaml `
  --attunement-profile default_rollout `
  --route-profile default_frontier_eval `
  --pretty
```

Decision service endpoints (for frontier integration):

```powershell
python tools\swag_decision_service.py --host 127.0.0.1 --port 8787
```

- `GET /health`
- `GET /v1/providers/status`
- `POST /v1/decision` (supports dry-run composition and optional frontier execution via `execute_frontier: true`)

System-one controller policy:
- main/shared question threshold target band: **50–75**
- endpoint returns `system_one_decision_matrix` including:
  - threshold pass/fail
  - mesh counts for main + stack + domain buckets
  - stack/domain section cells for decision-matrix analysis
- endpoint/runtime composition now also returns `source_sync` with:
  - `rrflow_sync` (isolated/shared project sync mode when `rrflow.sync.yaml` is present)
  - `research_sync` feed coverage (SWEBOK, AI decisions, Cloudflare, JEV, RRFlow alignment)
