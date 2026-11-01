---
source_doc_id: 1r0KlUR9_ZK-9IJjhAs7uze0ENdxqU8hZ7Ay3-Kop67w
title: "Stack Category Routing (Draft v0.2)"
version: v0.2
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQnV1buw3zwWT16MJsFOzlwArub-49SdVWldfgSsZVoUSysIOlv3qBASqfHew_YyPj9efEMZlBSadmW_Kjy5pjpnN-Q6-N-YOLXa-T0w
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack Category Routing (Draft v0.2)

Parent: Boundary Question Bank — Core Predicates. Status: Draft. Owner: hades. Date: 2026-09-30.

## The routing rule

The intent model emits one categorical value on the stack dimension. That value is a routing key, not a suggestion: it selects which question set the 9B oracle is handed.

battery = core ∪ stack(value) ∪ domain(detected boundaries)

- core — the parent document. Fires on every boundary, every stack.
- stack(value) — the stack document whose stack: field equals the value. Phrased from that stack's official curriculum and best-practice guidelines.
- domain(detected) — each domain-boundary section whose canonical label the lexicon resolved (user, admin, chat, AI, and the queued boundaries).

Stack detection is deterministic first, model second: file markers in the repository decide the value when they exist; the intent model decides only when markers are absent or ambiguous (a greenfield prompt with no repository yet). A polyglot repository carries more than one stack value. Each boundary binds to one primary stack — the runtime that executes the change — and composable values such as typescript fire alongside it. A contract boundary, where types are generated from another stack (Specta, ts-rs, typeshare, schemars, openapi-typescript), fires both stacks' interface sections plus the typescript composition set (Stack — TypeScript, section 0).

## Registry

| stack value | canonical label | deterministic markers | document | status |
|---|---|---|---|---|
| nextjs | Next.js App Router | next.config.*, app/ directory, next in package.json | Stack — Next.js | drafted |
| rust | Rust | Cargo.toml, Cargo.lock, src/main.rs or src/lib.rs, rust-toolchain.toml | Stack — Rust | drafted |
| go | Go | go.mod, go.sum | Stack — Go | drafted |
| react | React (without a meta-framework) | react in package.json without next, vite.config.* or similar | Stack — React | drafted |
| typescript | TypeScript | tsconfig.json | Stack — TypeScript | drafted |
| vanilla-js | JavaScript (no framework) | package.json or plain .js/.html with no framework dependency | Stack — JavaScript (vanilla) | drafted |
| c | C | Makefile or CMakeLists.txt with .c sources | — | queued |
| cpp | C++ | CMakeLists.txt with .cpp/.cc/.hpp sources | — | queued |
| python | Python | pyproject.toml, requirements.txt, setup.py | — | queued |
| pytorch-lightning | PyTorch Lightning | lightning or pytorch-lightning in dependencies; LightningModule subclasses | — | queued |
| java | Java | pom.xml, build.gradle, build.gradle.kts | — | queued |
| sql | SQL | *.sql files, migrations/ directory, a database URL in configuration | — | queued |
| drizzle | Drizzle ORM (TypeScript) | drizzle-orm in package.json, drizzle.config.* | — | queued |
| prisma | Prisma ORM (TypeScript) | prisma in package.json, schema.prisma | — | queued |
| ruby | Ruby | Gemfile, Gemfile.lock, *.rb, config.ru | — | queued |
| specta | Specta (Rust → TypeScript contract) | specta or tauri-specta in Cargo.toml; generated bindings file | Stack — TypeScript, section 0 | contract tool |
| schemars | schemars (Rust → JSON Schema contract) | schemars in Cargo.toml; JsonSchema derives | Stack — TypeScript, section 0 | contract tool |

## Stack lexicon aliases (seed, for the no-repository case)

- nextjs: Next, Next.js, Vercel, app router, server components, "the website" in a React context
- rust: Rust, cargo, crate, the borrow checker, tokio, "the engine", "the core", "memory safe"
- go: Go, Golang, goroutine, go mod, "the service"
- react: React, components, hooks, JSX, Vite, "the UI"
- typescript: TypeScript, TS, types, tsconfig, "add types"
- vanilla-js: plain JavaScript, no framework, "just JS", script tag
- c: C, gcc, clang, "low level", embedded
- cpp: C++, CMake, STL, "the game engine"
- python: Python, pip, script, notebook, Flask, FastAPI, Django
- pytorch-lightning: Lightning, PyTorch Lightning, LightningModule, Trainer, "train the model"
- java: Java, Spring, Maven, Gradle, JVM
- sql: SQL, the database, queries, tables, joins, Postgres, SQLite, MySQL
- drizzle: Drizzle, drizzle-orm, schema.ts, "the ORM" in a TypeScript project
- prisma: Prisma, schema.prisma, Prisma Client, migrations
- ruby: Ruby, Rails, gem, bundler, rake
- specta: Specta, tauri-specta, rspc, generated bindings from Rust
- schemars: schemars, JsonSchema derive, JSON Schema from Rust types

## Stack document contract

Every stack document declares a stack: field equal to its registry value, and follows the seven-section template set in Stack — Next.js: canonical label and version at authoring; lexicon aliases and disambiguation; curriculum sources; canonical concept map by module; boundary questions grouped by module with canonical term, source, and Binds to: markers; maturity gating; open items.

## Open items

- Resolved 2026-09-30: typescript is a composable stack value. Contract boundaries follow the composition rule in Stack — TypeScript, section 0.
- Decide whether pytorch-lightning is a stack value or a modifier on python. Parked until authored.
- Add the marker-detection order for polyglot repositories once the harness exists.
