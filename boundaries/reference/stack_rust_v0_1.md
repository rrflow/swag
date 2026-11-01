---
source_doc_id: 1BKu8dBkX0smpvmsFgrK18Xvl49YhGYwaiYh2d9Ykl_A
title: "Stack — Rust: Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQnUgMk1bQ7uNKcXsv7UsLsCoA4FvcoQuxXiEdMhaxpVq_oEB39JzsjTyPSm8b-Xzr0BlTwd0-BFR1D9iRmflZQFWfaegZmEhnm8cBP4
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — Rust: Curriculum and Boundary Questions (Draft v0.1)

stack: rust

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30. Version at authoring: The Rust Programming Language, 2024-edition structure (chapters 1–21); Rust 2024 Edition.

Purpose: When a boundary is planned or changed in a Rust codebase, these predicates fire in addition to the core predicates and any detected domain-boundary predicates. Every question is phrased in the vocabulary of The Rust Programming Language ("the Book") and the Rust API Guidelines so the model recognizes it from training.

## 1. Canonical label

Rust — systems language with ownership-based memory safety, no garbage collector, traits for abstraction, and Cargo as build system and package manager. Deterministic markers: Cargo.toml, Cargo.lock, src/main.rs or src/lib.rs, rust-toolchain.toml.

## 2. Lexicon aliases (seed)

Rust, cargo, crate, the engine, the core, the binary, the CLI, the server, memory safe, make it fast, no garbage collector, it won't compile, the borrow checker yelled at me, lifetime error, unwrap everywhere, async, tokio, the trait thing.

Disambiguation — non-technical word → Rust term: package or library → crate; module → mod; interface → trait; class or object → struct with impl blocks (there are no classes); null or nothing → Option; exception, try/catch → Result and the ? operator; garbage collection or memory management → ownership and borrowing; pointer → reference, Box, Rc, or Arc; thread → std::thread or an async task; build tool or npm → Cargo; "the compiler is fighting me" → an ownership, borrowing, or lifetime question, not a bug.

## 3. Curriculum sources

- The Rust Programming Language (Klabnik and Nichols; doc.rust-lang.org/book) — chapters 1 Getting Started, 2 Guessing Game, 3 Common Programming Concepts, 4 Understanding Ownership, 5 Structs, 6 Enums and Pattern Matching, 7 Managing Growing Projects with Packages, Crates, and Modules, 8 Common Collections, 9 Error Handling, 10 Generic Types, Traits, and Lifetimes, 11 Writing Automated Tests, 12 An I/O Project, 13 Functional Language Features: Iterators and Closures, 14 More about Cargo and Crates.io, 15 Smart Pointers, 16 Fearless Concurrency, 17 Fundamentals of Asynchronous Programming: Async, Await, Futures, and Streams, 18 Object-Oriented Programming Features, 19 Patterns and Matching, 20 Advanced Features (Unsafe Rust, Advanced Traits, Advanced Types, Macros), 21 Final Project: Multithreaded Web Server. Third print edition adds Miri for unsafe code and is built on the 2024 Edition.
- Rust API Guidelines (rust-lang.github.io/api-guidelines) — checklist of C-prefixed items across naming, interoperability, macros, documentation, predictability, flexibility, type safety, dependability, debuggability, future proofing, necessities.
- The Cargo Book — manifest, workspaces, features, profiles, lockfile, publishing.
- The Rustonomicon — unsafe Rust; Clippy lint groups and rustfmt as enforced style.
- Comprehensive Rust (Google) and Rust by Example — secondary curricula; same vocabulary.
- The Rust Performance Book — measurement before optimization.

## 4. Canonical concept map, by Book chapter

- Ch 3–4: immutability by default, shadowing, ownership, move, borrow, mutable borrow, reference, slice, the borrow checker.
- Ch 5–6: struct, impl, associated function, method, enum, Option, match, exhaustiveness, if let.
- Ch 7: package, crate (binary, library), module tree, mod, use, pub, pub(crate), paths, re-export.
- Ch 8: Vec, String, HashMap; ownership of collection contents.
- Ch 9: panic, unrecoverable vs recoverable error, Result, the ? operator, From conversion, unwrap, expect, error propagation.
- Ch 10: generics, trait, trait bound, impl Trait, lifetime, lifetime elision, 'static.
- Ch 11: #[test], #[cfg(test)], unit tests, integration tests (tests/), doc tests, assert macros.
- Ch 13: closure, iterator, adapter, consumer, zero-cost abstraction.
- Ch 14: release profile, crates.io, documentation comments, workspace, cargo install, features.
- Ch 15: Box, Deref, Drop, Rc, RefCell, interior mutability, reference cycle, Weak.
- Ch 16: thread, spawn, join, message passing, channel, Mutex, Arc, Send, Sync.
- Ch 17: async, await, Future, task, runtime, join, select, Stream, Pin, cancellation.
- Ch 18: trait object, dyn, dynamic dispatch vs static dispatch, state pattern.
- Ch 19: pattern, refutable vs irrefutable, destructuring, match guard.
- Ch 20: unsafe block, raw pointer, FFI, extern, advanced traits (associated types, supertraits, newtype), type alias, never type, declarative and procedural macros.
- API Guidelines: C-CASE, C-CONV, C-GETTER, C-ITER, C-COMMON-TRAITS, C-SEND-SYNC, C-GOOD-ERR, C-NEWTYPE, C-VALIDATE, C-STRUCT-PRIVATE, C-SEALED, C-CRATE-DOC, C-EXAMPLE, C-FAILURE, C-DEBUG, C-FEATURE, C-METADATA.

## 5. Boundary questions

### Ownership, Borrowing, Lifetimes (Ch 4, 10)

- Is the owner of every value clear, and is each borrow scoped no longer than the data it references? — Ownership; borrowing (Ch 4)
- Are clone calls deliberate for semantics rather than used to silence the borrow checker? — Move vs clone (Ch 4)
- Are references preferred over owned copies in function parameters where the callee does not need ownership? — Borrowing in signatures (Ch 4)
- Are lifetimes elided where the rules allow and named only where the compiler requires them? — Lifetime elision (Ch 10)
- Is 'static avoided as a workaround for a lifetime the design should express? — 'static lifetime (Ch 10)

### Types, Structs, Enums, Patterns (Ch 5, 6, 19; API Guidelines)

- Are domain states modelled as enums with exhaustive match rather than booleans, strings, or sentinel values? — Enums; exhaustiveness (Ch 6, 19)
- Are domain identifiers and units wrapped in newtypes rather than passed as raw primitives? — Newtype (C-NEWTYPE; Ch 20)
- Are invariants enforced by construction — private fields, constructors that validate — so an invalid value cannot exist? — Validation; private fields (C-VALIDATE, C-STRUCT-PRIVATE)
- Is absence expressed with Option and never with a sentinel or a panic? — Option (Ch 6)
- Is destructuring used at the boundary so field access is explicit and checked? — Patterns (Ch 19)

### Packages, Crates, Modules, Workspace (Ch 7, 14; Cargo Book)

- Is the module tree explicit, with pub(crate) by default and pub only on the intended public surface? — Module privacy (Ch 7)
- Does the crate and workspace split align with the boundary — one crate per boundary, not one crate for everything? — Workspaces; crate boundaries (Ch 14). Binds to: workspace layout.
- Is the public API re-exported from a deliberate root rather than exposing internal paths? — Re-exports (Ch 7; C-REEXPORT)
- Are dependencies pinned by Cargo.lock, minimal in count, and audited (cargo audit or cargo deny)? — Dependencies (Cargo Book)
- Are optional dependencies behind Cargo features rather than runtime flags? — Features (Cargo Book; C-FEATURE)
- Is the edition current (2024) or pinned deliberately, and is rust-version declared for a library? — Edition; MSRV (Cargo Book)
- Is the placement of the new code consistent with the project's existing crate and module layout? — Project organization. Binds to: file tree.

### Error Handling (Ch 9; API Guidelines)

- Do fallible functions return Result with a typed error rather than panicking? — Recoverable errors (Ch 9)
- Is unwrap or expect confined to tests, prototypes, and cases proven infallible with a comment? — Unwrap discipline (Ch 9)
- Do error types implement Error, Debug, and Display, with structured variants at library boundaries and a catch-all only at the binary edge? — Meaningful error types (C-GOOD-ERR)
- Is the ? operator used with From conversions rather than manual match-and-return? — Error propagation (Ch 9)
- Are panics and error conditions documented in Panics and Errors sections? — Failure documentation (C-FAILURE)

### Traits and Generics (Ch 10, 18; API Guidelines)

- Is behavior abstracted through a trait with the smallest useful surface, not a trait per struct? — Traits (Ch 10)
- Is static dispatch (generics, impl Trait) versus dynamic dispatch (dyn Trait) chosen deliberately, with the reason recorded? — Dispatch (Ch 18)
- Do public types eagerly implement the common traits that apply — Debug, Clone, PartialEq, Eq, Hash, Default, Send, Sync? — Common traits (C-COMMON-TRAITS, C-SEND-SYNC, C-DEBUG)
- Are traits meant to be closed sealed against downstream implementation? — Sealed traits (C-SEALED)
- Do conversions follow the standard traits (From, Into, TryFrom, AsRef) rather than bespoke methods? — Conversion traits (C-CONV-TRAITS)

### Naming (API Guidelines)

- Do identifiers follow RFC 430 casing — UpperCamelCase types and traits, snake_case functions and modules, SCREAMING_SNAKE_CASE constants? — Casing (C-CASE)
- Do conversion methods follow as_, to_, into_ semantics by cost and ownership? — Conversion naming (C-CONV)
- Do getters omit the get_ prefix, and do collections expose iter, iter_mut, into_iter? — Getter and iterator naming (C-GETTER, C-ITER)
- Are names the same canonical names used elsewhere in this project for the same thing? — Canonical naming. Binds to: canonical name registry.

### Testing and Documentation (Ch 11, 14; API Guidelines)

- Are unit tests in #[cfg(test)] modules beside the code and integration tests in tests/? — Test organization (Ch 11)
- Does the public API carry documentation comments with runnable examples (doc tests)? — Crate documentation; examples (C-CRATE-DOC, C-EXAMPLE)
- Is the crate metadata (description, license, repository, keywords) complete for anything published? — Metadata (C-METADATA)

### Iterators, Closures, Performance (Ch 13; Performance Book)

- Are iterator adapters used where they are clearer than index loops, with collect only when a collection is actually needed? — Iterators (Ch 13)
- Are allocations in hot paths measured before being optimized, with a benchmark for performance-sensitive code? — Measurement (Performance Book)
- Is the release profile configured deliberately (opt-level, LTO, debug symbols)? — Release profiles (Ch 14)

### Smart Pointers and Concurrency (Ch 15, 16)

- Is shared ownership (Rc, Arc) justified by the design rather than used by default? — Reference counting (Ch 15)
- Is interior mutability (RefCell, Mutex, RwLock) minimal, and is each lock's scope kept short and documented? — Interior mutability; shared state (Ch 15, 16)
- Are reference cycles impossible or broken with Weak? — Reference cycles (Ch 15)
- Is message passing chosen over shared state where the design allows? — Message passing (Ch 16)
- Are types that cross thread boundaries Send and Sync by design, not by unsafe impl? — Send and Sync (Ch 16; C-SEND-SYNC)

### Async (Ch 17)

- Is async used only where I/O-bound concurrency demands it, with compute-bound work on threads? — Futures, tasks, and threads (Ch 17)
- Is the async runtime chosen once for the project and not mixed? — Runtime (Ch 17). Binds to: runtime choice.
- Are blocking calls kept off the executor (spawn_blocking or a dedicated thread)? — Blocking in async (Ch 17)
- Are futures that hold resources cancellation-safe, and are timeouts explicit? — Cancellation (Ch 17)
- Are Streams used for sequences of async values rather than hand-rolled loops over channels? — Streams (Ch 17)

### Unsafe and FFI (Ch 20; Rustonomicon)

- Is unsafe absent, or isolated in a minimal module with a SAFETY comment stating the invariant upheld? — Unsafe Rust (Ch 20; Rustonomicon)
- Is every FFI boundary wrapped in a safe API that owns the invariants? — FFI (Ch 20)
- Is unsafe code checked under Miri? — Miri (Book, 3rd edition)
- Are macros used only where functions and generics cannot express the abstraction? — Macros (Ch 20)

### Tooling and Style

- Does the change pass cargo fmt and cargo clippy with this project's lint configuration and no new warnings? — rustfmt; Clippy. Binds to: clippy and rustfmt config.
- Is the toolchain pinned (rust-toolchain.toml) where reproducibility matters? — Toolchain (Cargo Book)

## 6. Maturity gating

Greenfield: Ownership 1–2; Types 1, 3, 4; Packages 1, 2, 4, 6; Error Handling 1–3; Traits 1–3; Naming 1; Testing 1; Async 1–2; Unsafe 1. Growing: all sections. Mature: add the Binds to: questions bound to workspace layout, canonical name registry, runtime choice, and lint configuration; Performance and Documentation sections become mandatory.

## 7. Open items

- Validate seed aliases against the mined session corpus; the "compiler is fighting me" family is expected to be large.
- Decide whether the Rust document carries framework sub-sections (tokio, axum, serde) or whether those become separate stack values.
- Pin API Guidelines item identifiers to their current checklist text once the harness exists.
