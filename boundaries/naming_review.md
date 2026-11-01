# Naming review — boundary docs (2026-09-30)

Status: items 1, 2, 7 and 8 are decided (8, including the rr1 → swag namespace change, is pending a source-doc edit by its owner); everything else is a proposal for Jesse. The reference exports stay verbatim.

## 1. Stack keys to snake_case (APPLIED in derived YAML)

The RRFLOW naming ADR pattern is `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` (config/rrflow.naming.yaml).
I checked all 17 registry values:

| source value | derived key |
|---|---|
| vanilla-js | vanilla_js |
| pytorch-lightning | pytorch_lightning |

The other 15 values already match. Each registry entry keeps `source_value`. The vanilla JS doc still
says `stack: vanilla-js`, recorded as `stack_field_in_source`. The routing contract says the stack field
must equal the registry value, so the doc and the key will match again once the doc is updated.

## 2. "core" / "kernel" (DECIDED by Jesse 2026-09-30)

Rule: "core" is allowed only where it is the established industry term (Core Web Vitals, CPU core,
MDN Core module). It is never used in our own key, folder or layer names without Jesse's approval.
The checker does not ban core/kernel, and rrflow.naming.yaml is unchanged.

| where | source wording | derived config |
|---|---|---|
| Bank title and set name, plus every stack doc's "Parent:" line | "Core Predicates" | question-set key `shared_predicates` (APPROVED; applied) |
| Routing formula | `battery = core ∪ stack(value) ∪ domain(...)` | `routing.battery: battery = shared_predicates ∪ stack(value) ∪ domain(detected boundaries)` (canonical; the as-written form stays only in the reference export) |
| Stack doc Purpose lines, bank Purpose | "the core predicates", "core battery" | doc prose; reference exports stay verbatim (the source docs would need editing to align) |
| rr1:core, "kernel" (engine plan) | not present in any of the 8 docs | decided in section 8 (kernel → engine, rr1:core → swag:baseline) |

Industry terms kept under the rule: "MDN Learn ... Core module", "MDN core module", "Core Web Vitals".

## 3. Rust lexicon aliases "the engine" / "the core" (FLAGGED, kept)

They appear in the routing doc's lexicon line (quoted, like the other user phrasings: "the UI", "the service")
and in the Rust doc's seed alias list. Both are kept and marked `review:` in stack_registry.yaml.
Related: cpp has "the game engine".
Question: are these words users actually type, or project vocabulary? If they are project words, they would
route every "engine" or "core" mention to Rust.

## 4. ArkType version (FLAGGED, unchanged)

None of the 8 docs pins an ArkType version. The only mention is the TypeScript doc's open item
"schema library choice (zod, valibot, arktype)". I could not verify the 2.2.3 pin (docs), the 2.2.5 pin
(engine plan, unavailable) or the 2.2.6 latest.

## 5. Questions duplicated between stack docs and the shared bank (LISTED, not removed)

Each listed question carries `overlaps_shared_question` in its YAML.

- Placement → shared_predicates.software_construction_practical_considerations.02 (Binds to: file tree):
  nextjs.project_structure_and_installation.03, vanilla_js.modules_and_dependencies.05,
  typescript.lint_structure_naming.03, react.tooling_structure_testing.04,
  go.packages_modules_layout.04, rust.packages_crates_modules_workspace.07
- Canonical naming → shared_predicates.software_construction_practical_considerations.01 (Binds to: canonical name registry):
  vanilla_js.style_and_naming.03, typescript.lint_structure_naming.04,
  go.names_formatting_documentation.07, rust.naming.04
  (related, not annotated: typescript.cross_stack_contract_boundaries.05, "Canonical naming across stacks")
- Secrets → shared_predicates.software_security.02:
  nextjs.project_structure_and_installation.04, nextjs.server_and_client_components.03,
  vanilla_js.security.03
- Other likely overlaps (not annotated): dependency pinning (vanilla_js.modules_and_dependencies.04,
  rust.packages_crates_modules_workspace.04 vs shared I.2); circular dependencies
  (vanilla_js.modules_and_dependencies.02 vs shared C.5); input validation at the trust boundary
  (nextjs.mutating_data.02 vs shared K.1).

The vanilla JS doc says shared topics are "not repeated here", but it still repeats placement,
naming and secrets.

## 6. Other clashes found while deriving

- Binding artifact names vary:
  "lint config" (vanilla_js, typescript, go), "style guide / linter config" (shared),
  "clippy and rustfmt config" (rust), "lint configuration" (go and rust mature clauses);
  "runtime" (vanilla_js) vs "runtime choice" (rust);
  "ADR store" vs "task / ADR reference" (shared).
  Proposal: one binding key per artifact, e.g. `lint_config`, `runtime_target`.
- Broken question references:
  - Next.js disambiguation says "(question 25)" for Route Handlers, but question 25 is
    nextjs.error_handling.01. The Route Handler question is nextjs.route_handlers_and_proxy.01 (#33).
  - Vanilla JS says "(question 30)" for the runtime target, but question 30 is
    vanilla_js.network_and_data.02. The runtime-target question is
    vanilla_js.compatibility_and_runtime_target.03 (#34).
  - The TypeScript section 0 cites "this document's section 9", but the doc has sections 0–7. The likely
    target is "5 > Cross-Stack Contract Boundaries".
- Mature-clause bindings that are not named in the clause:
  react.tooling_structure_testing.05 (binding "typescript stack value"; the clause says "the TypeScript stack"),
  rust.packages_crates_modules_workspace.07 ("file tree"), rust.tooling_and_style.01 ("clippy and rustfmt config").
- Shortened gating references were resolved to sections by title match. All are recorded as `greenfield_refs`
  and `match`. Five use word containment and need confirming: typescript "Type Manipulation" →
  object_types_and_type_manipulation, "Declarations" → modules_and_declarations; go "Documentation" →
  names_formatting_documentation; rust "Performance" → iterators_closures_performance,
  "Documentation" → testing_and_documentation.
- Marker text differs between the registry and the stack docs for react and vanilla_js. Both texts are kept
  (`markers.registry_text`, `markers.stack_doc_text`).
- The registry status has a third value, "contract tool" (specta, schemars), alongside drafted/queued.
  It is kept verbatim.
- Section keys hit the RRFLOW reserved words (checker output below). They are not renamed: the ban applies
  to lane and seam keys, and the ADR has not said whether it covers section keys.

## Checker output (python tools\check_naming.py --no-user, kind api_seam_key, 116 keys)

```
config warning: replacement collision: design and implementation both map to 'shape'
ERROR software_design_principles   reserved_word 'design'       -> software_shape_principles
ERROR software_design_key_issues   reserved_word 'design'       -> software_shape_key_issues
ERROR verification_and_validation  reserved_word 'verification' -> seal_and_validation
ERROR software_security            reserved_word 'security'     -> software_bound
ERROR security                     reserved_word 'security'     -> bound
ERROR testing_and_debugging        reserved_word 'testing'      -> stress_and_debugging
ERROR tooling_structure_testing    reserved_word 'testing'      -> tooling_structure_stress
ERROR testing                      reserved_word 'testing'      -> stress
ERROR testing_and_documentation    reserved_word 'testing'      -> stress_and_documentation
ERROR test_runner                  reserved_word 'test'         -> stress_runner
checked 116 keys: 10 violations on 10 keys (mode=error)
reserved-word hits: testing=5, design=2, security=2, verification=1
```
No pattern (snake_case) violations. The checker's suggestions are mechanical; none were applied.

---

# Additions 2026-09-30 (pasted docs: Domain Boundaries v0.1, LFG_ENGINE_PLAN)

## 7. Domain keys (DECIDED by Jesse 2026-09-30, applied in config/boundaries/question_sets/domains.yaml)

| source label | canonical label (source) | key | reason |
|---|---|---|---|
| user | Identity and Access Management (IAM) | iam | as proposed |
| admin | Privileged Access and Administration | privileged_access_management | PAM is the standard industry term |
| chat | Real-time Messaging | realtime_messaging | as proposed |
| AI | LLM Integration Layer | llm_application | matches OWASP Top 10 for LLM Applications |

The queued-boundary keys stay PROPOSED: billing_and_payments, notifications, files_and_media,
search, analytics_and_reporting, settings_and_preferences, onboarding.
Question ids use `domains.<domain_key>.<nn>`. The source numbering is preserved: the AI disambiguation's
"(question 18)" points correctly at domains.llm_application.18.

## 8. Strict-core rule: engine plan and domain doc (DECIDED by Jesse 2026-09-30)

Rule (Jesse, 2026-09-30): "core" only as an established industry term, and never in our own key, folder or
layer names without Jesse's approval. The checker does not ban core/kernel. Line numbers below refer to the
pasted text (the export body).

Final replacements: "kernel" → "engine"; `rr1:core` → `swag:baseline` (the rr1 prefix is dropped in favour of the swag namespace); "core addresses / embedded core tree /
embedded core / core keys" → "baseline addresses / embedded baseline tree / embedded baseline / baseline keys".

| where (LFG_ENGINE_PLAN) | source wording | final wording |
|---|---|---|
| L14 Scope | "How LFG's kernel is actually built" | "How LFG's engine is actually built" |
| L165 §3 heading | "The regex rule engine (tier 1, LFG kernel)" | "(tier 1, LFG engine)" |
| L226 §3.5 | "the kernel never invents them" | "the engine never invents them" |
| L274 §7 step 3 | "Kernel evaluate for one node" | "Engine evaluate for one node" |
| L129 §2.2 | `tree("rr1:core", …)` | `tree("swag:baseline", …)` |
| L236 §4.2 | "core addresses", "the embedded core tree" | "baseline addresses", "the embedded baseline tree" |
| L298 §7 step 7 | "layered over embedded core" | "layered over embedded baseline" |
| L300 §7 step 7 | "core keys unchanged" | "baseline keys unchanged" |

The reference export (boundaries/reference/lfg_engine_plan_draft_2026_09_26.md) stays verbatim. The source
document needs editing by its owner (hades) to adopt these. The engine plan has no derived config, so nothing
else in this repo changes.

Domain doc: the Parent line ("Core Predicates") and the Purpose line ("The core predicates in the parent document")
use our own name. The approved key is `shared_predicates`. The export stays verbatim, so the source text needs
editing by its owner.

DECIDED 2026-09-30 (Jesse): the `rr1` prefix is dropped and replaced by the `swag` namespace, so `rr1:core` → `swag:baseline`. Nothing about this item is open now.

## 9. ArkType version (FLAGGED only, no change)

| claim | where | checked against the npm registry 2026-09-30 |
|---|---|---|
| 2.2.5 "(Sep 25, 2026 release note)", "current when checked … not pins" | LFG_ENGINE_PLAN §1 | 2.2.5 was published to npm 2026-09-24 5:39 PM ET, a day earlier than the plan's date |
| 2.2.3 pin | brief says "docs pinned 2.2.3" | not found in any of the 10 exported docs; published 2026-07-07 4:07 PM ET |
| 2.2.6 latest | brief | confirmed: npm `latest` = 2.2.6, published 2026-09-30 4:45 PM ET |

The plan's own policy ("latest stable … they are not pins") contradicts any 2.2.3 pin. Where does the 2.2.3 pin live?

## 10. Other new clashes

- The plan's example tree uses `domain` options `["auth", "ui", "data"]`. The domain doc's boundaries are
  user/admin/chat/AI, keyed iam/privileged_access_management/realtime_messaging/llm_application. Two vocabularies for "domain".
- The plan's example `framework` extract (`svelte|react|vue|next`) uses `next` where the stack key is `nextjs`.
  svelte and vue are not in the stack registry.
- Not covered by the domain doc: maturity gating and Binds to: markers (both absent; recorded as
  `maturity_gating.specified_in_source: false`).
- Chat Q12 points to "the file-handling boundary". That is the queued `files_and_media`, which has no document yet.
- Domain questions that likely repeat shared or stack questions (not annotated): admin Q3 least privilege vs shared K.3;
  AI Q4 system prompt free of secrets vs shared K.2; chat Q2 idempotency key vs shared E.8 idempotence;
  user Q15 server-side authorization vs nextjs Data Access Layer questions.
- The plan names companion docs that were not provided: LFG_NOTES_v3 (decisions) and the Fork 1 research report.

## Checker output for the domain keys (python tools\check_naming.py --no-user, 12 keys, re-run 2026-09-30 after approval)

```
config warning: replacement collision: design and implementation both map to 'shape'
checked 12 keys: 0 violations on 0 keys (mode=error)
```
Keys: domains, iam, privileged_access_management, realtime_messaging, llm_application, billing_and_payments, notifications,
files_and_media, search, analytics_and_reporting, settings_and_preferences, onboarding.
