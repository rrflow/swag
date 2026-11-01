---
source_doc_id: 1WiHxZ88HnGgmmAsKlU2E267COed5G7Lwk_99JX91JIQ
title: "Stack — TypeScript: Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQk4UlqLQDDXRZoERGqiIyp8QZSHWr18e0V2vuk9BWXs1YW_XbQ-KIGfjpBqLp-s_sZZUR2s4KWrt7fHeKBsl9r1oohcquqNxHONrAua
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — TypeScript: Curriculum and Boundary Questions (Draft v0.1)

stack: typescript   kind: composable stack value (see section 0)

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30. Version at authoring: TypeScript 7.0 (GA July 8, 2026; Go-native compiler under the standard typescript package). TypeScript 6.0 remains the last JavaScript-based compiler, published in parallel as @typescript/typescript6 for tools that depend on the old compiler API. 7.1 is scheduled for November 2026.

## 0. Composition rule (resolves the routing-registry open item)

typescript is a stack value, and stack values compose. A repository carries every value its markers show, so a Vite React app with tsconfig.json fires react and typescript; a Tauri or Specta project fires rust and typescript. Each boundary still binds to one primary stack — the one whose runtime executes the change — and this document fires alongside it whenever tsconfig.json is present.

Cross-stack contract boundaries. Where TypeScript types are generated from another stack — Specta, ts-rs, tauri-specta, or typeshare from Rust; openapi-typescript from an API spec; protobuf or GraphQL codegen — the boundary is a contract boundary, not a TypeScript boundary. The source stack owns the type as the single source of truth; the .ts output is a derived artifact. On such a boundary the oracle fires: the source stack's type and interface predicates (for Rust: Types 1–3, Traits 3, Naming), this document's section 9, and the core predicates. It does not fire this document's authoring predicates against the generated file.

Registry amendment pending: replace "each boundary binds to exactly one" with "each boundary binds to one primary stack; contract boundaries fire both stacks' interface sections plus the typescript composition set."

## 1. Canonical label

TypeScript — a statically typed superset of JavaScript whose types are erased at compile time; structural typing, union and literal types, narrowing, generics and type-level programming, ESM modules, and a compiler configured through tsconfig.json. Deterministic marker: tsconfig.json (also .ts/.tsx sources without a build config).

## 2. Lexicon aliases (seed)

TypeScript, TS, add types, type it, make it type safe, the types, type error, red squiggles, it says undefined, it might be null, any, the interface, the shape of the data, the JSON shape, tsconfig, strict mode, it compiles but crashes, cast it, make it stop complaining, generics, the d.ts file.

Disambiguation — non-technical word → TypeScript term: "the interface" → an interface or a type alias per project convention (structural, not a contract enforced at runtime); "cast it" → a type assertion, which changes nothing at runtime — prefer narrowing; "make it stop complaining" → fix the type or narrow with unknown, never any or @ts-ignore; "it compiles but crashes" → types are erased — the boundary needed runtime validation; "class" → structural typing, no nominal identity unless branded; "enum" → prefer a union of string literals; "types at runtime" → a schema library, with the static type derived from the schema; "make the build faster" → TypeScript 7's native compiler and project references before restructuring.

## 3. Curriculum sources

- The TypeScript Handbook (typescriptlang.org/docs/handbook) — The Basics; Everyday Types; Narrowing; More on Functions; Object Types; Type Manipulation (Creating Types from Types, Generics, Keyof Type Operator, Typeof Type Operator, Indexed Access Types, Conditional Types, Mapped Types, Template Literal Types); Classes; Modules.
- Handbook Reference — Utility Types; Declaration Merging; Enums; Iterators and Generators; Namespaces; Type Compatibility; Type Inference; Variance Annotations; Declaration Files section; Do's and Don'ts.
- Project Configuration — tsconfig reference; Compiler Options; Project References; Modules reference (module, moduleResolution, verbatimModuleSyntax).
- Release notes — 4.4 useUnknownInCatchVariables; 4.9 satisfies; 5.0 const type parameters, verbatimModuleSyntax; 5.2 using declarations; 5.5 inferred type predicates, isolatedDeclarations; 5.8 erasableSyntaxOnly; 6.0 deprecations; 7.0 native compiler, no legacy compiler API.
- Node.js type stripping — Node runs .ts files directly by erasing type syntax; only erasable syntax is permitted.
- typescript-eslint — recommended-type-checked rule set (community standard).

## 4. Canonical concept map, by module

- Basics and Everyday Types: static type checking, type erasure, type annotation, type inference, primitives, any, unknown, never, void, array, tuple, object type, union, literal type, type alias, interface, optional property, type assertion, satisfies, null, undefined, strictNullChecks, non-null assertion, enum, const enum.
- Narrowing: typeof guard, truthiness, equality, in operator, instanceof, control-flow analysis, type predicate, discriminated union, discriminant property, exhaustiveness check, never.
- Functions: call signature, parameter types, return type, optional parameter, rest parameter, overload, generic function, constraint, contextual typing, void return for callbacks.
- Object Types and Type Manipulation: readonly, index signature, intersection, generic object type, keyof, typeof, indexed access, conditional type, infer, distributive conditional, mapped type, key remapping, template literal type, utility types (Partial, Required, Readonly, Record, Pick, Omit, Exclude, Extract, NonNullable, ReturnType, Parameters, Awaited).
- Classes: field, constructor, method, accessor, implements, abstract, parameter property, structural compatibility, branded type.
- Modules: ES module, import, export, import type, type-only export, module resolution, verbatimModuleSyntax, isolatedModules, path mapping, declaration file, ambient declaration, module augmentation, @types.
- Configuration and toolchain: tsconfig.json, strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes, noImplicitOverride, target, module, moduleResolution, lib, declaration, isolatedDeclarations, erasableSyntaxOnly, project references, incremental, tsc --noEmit, native compiler, --checkers.

## 5. Boundary questions

### Configuration and Toolchain

- Is strict enabled, with this project's additional strictness flags (noUncheckedIndexedAccess, exactOptionalPropertyTypes, noImplicitOverride) applied consistently? — strict (tsconfig reference). Binds to: tsconfig.
- Do module and moduleResolution match the runtime or bundler (nodenext, bundler), with verbatimModuleSyntax on? — Modules reference (5.0)
- Is type-checking run as tsc --noEmit in CI, separate from the bundler's transpile, so transpile-only tools cannot hide type errors? — Compiler; project configuration
- In a multi-package repository, are project references used with a single root configuration? — Project References
- Is TypeScript on a current 7.x release, with any tool that imports the compiler as a library moved to @typescript/typescript6 or an updated version? — TypeScript 7.0 (no legacy compiler API)
- If Node executes .ts files directly, is erasableSyntaxOnly enabled — no enums, namespaces, or parameter properties? — erasableSyntaxOnly (5.8); Node type stripping

### Everyday Types

- Is any absent, with unknown plus narrowing at every boundary where the type is not known? — any; unknown (Everyday Types; Do's and Don'ts)
- Are the wrapper types Number, String, Boolean, Object, and the bare Function type never used? — Do's and Don'ts: General Types
- Are unions of string literals preferred over enums; where enums remain, is that a recorded project decision? — Literal Types; Enums
- Are null and undefined handled explicitly with optional chaining and nullish coalescing, with no non-null assertions outside a commented boundary? — strictNullChecks; non-null assertion
- Are type assertions confined to boundaries the compiler cannot see, and is satisfies used to check a value without widening it? — Type Assertions; satisfies (4.9)
- Are tuples and as const used where positional or literal structure matters? — Tuple Types; as const

### Narrowing

- Are unions narrowed with typeof, instanceof, in, and discriminant checks rather than assertions? — Narrowing
- Do discriminated unions carry a literal discriminant, with exhaustiveness enforced through never in the default branch? — Discriminated unions; exhaustiveness checking
- Are custom guards written as type predicates, relying on inferred predicates where 5.5+ allows? — Type predicates (5.5)

### Functions

- Are parameter and return types explicit on exported functions and inferred inside modules? — More on Functions; isolatedDeclarations (5.5)
- Are overloads avoided where a union parameter or optional parameter suffices, and ordered specific-to-general where kept? — Do's and Don'ts: Overloads
- Is void the return type of callbacks whose result is ignored? — Do's and Don'ts: Callback Types
- Are promises always awaited or returned, with catch variables typed unknown? — useUnknownInCatchVariables (4.4); no-floating-promises

### Object Types and Type Manipulation

- Is interface versus type alias chosen per this project's convention and applied consistently? — Object Types. Binds to: declaration convention.
- Are readonly properties and Readonly applied to data that must not be mutated? — readonly
- Is a generic introduced only when a type relationship must be preserved, with a constraint and a meaningful name? — Generics; constraints
- Are utility types used instead of hand-duplicated shapes derived from an existing type? — Utility Types
- Are mapped, conditional, and template literal types used only where they remove duplication, with a comment stating the derivation? — Type Manipulation
- Is a const type parameter used where a literal must be preserved through a generic call? — const type parameters (5.0)

### Classes and Compatibility

- Are classes used only where identity, encapsulated state, or lifecycle justify them, with plain objects and functions otherwise? — Classes
- Is structural compatibility understood, with branded types where nominal identity is genuinely required? — Type Compatibility; branded types

### Modules and Declarations

- Are ES modules used with import type for type-only imports and no namespaces? — Modules; import type
- Are barrel files used deliberately, with circular imports checked? — Modules; community best practice
- Are tsconfig path aliases mirrored in the bundler and runtime configuration? — paths
- Do third-party types come from @types or bundled declarations, with local gaps filled by a declared .d.ts rather than any? — Declaration Files
- Does a published library emit declarations (declaration, isolatedDeclarations)? — Declaration emit

### Runtime Boundaries

- Is every value crossing a runtime edge — JSON.parse, HTTP response, environment variable, IPC message, form data — validated with a schema, with the static type derived from the schema? — Type erasure; runtime validation
- Are environment variables typed through a validated config module rather than read as any? — Runtime validation

### Cross-Stack Contract Boundaries (composition set)

- Where types are generated from another stack (Specta, ts-rs, typeshare, openapi-typescript, protobuf, GraphQL codegen), is the source stack the single source of truth, and is the .ts output never hand-edited? — Contract boundary; single source of truth
- Are generated files marked as generated, excluded from lint and formatting, and regenerated in the build so that drift fails CI? — Codegen discipline
- Is the contract versioned so a source-type change surfaces as a visible boundary change on the TypeScript side? — Contract versioning
- Is the IPC or HTTP edge still runtime-validated, since generated types are erased like any other? — Type erasure at the contract edge
- Do generated type names match the source stack's canonical names under the codegen tool's casing rule? — Canonical naming across stacks. Binds to: canonical name registry.

### Lint, Structure, Naming

- Is typescript-eslint active with the type-checked rule set — no-explicit-any, no-floating-promises, consistent-type-imports? — typescript-eslint. Binds to: lint config.
- Are @ts-ignore comments absent, with @ts-expect-error used only with a stated reason? — Compiler directives
- Is the placement consistent with this project's existing structure? — Project organization. Binds to: file tree.
- Are names the same canonical names used elsewhere in this project for the same thing? — Canonical naming. Binds to: canonical name registry.

## 6. Maturity gating

Greenfield: Configuration 1–3, 5; Everyday Types 1, 4, 5; Narrowing 1–2; Functions 1, 4; Modules 1; Runtime Boundaries 1; Cross-Stack 1–2 when codegen is present. Growing: all sections. Mature: add the Binds to: questions bound to tsconfig, declaration convention, lint config, file tree, and canonical name registry; Type Manipulation and Declarations sections become mandatory.

## 7. Open items

- Amend the routing registry line per section 0 once the Google Docs connector is available.
- Pin the 6.0 deprecation list and 7.0 default changes as a citation column.
- Validate seed aliases against the mined session corpus; "make it stop complaining" is expected to resolve to Everyday Types 1 and Lint 2.
- Decide whether schema library choice (zod, valibot, arktype) is a project binding or a recommendation.
