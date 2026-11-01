---
source_doc_id: 1c-HSBhxLY-z-A6xn_owLsi47HD10_sIa0FPHZqq0IB4
title: "Boundary Question Bank — Core Predicates (Draft v0.2)"
version: v0.2
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQmX6mlTe3GpUYit5XDxU9uzeiW5NOw6bZiGp4kOt71Fj8jevSGVVdaZcbtgZcXJmCbBRnE_TGlfFESTbs10Ua_tu1BM2i1-McPPASEz
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Boundary Question Bank — Core Predicates (Draft v0.2)

Status: Draft — first authoring pass, not yet run against a session corpus. Owner: hades. Date: 2026-09-30. v0.2 folds in the LFG Boundary Question Battery draft (2026-09-30).

Purpose: The language-agnostic core battery the 9B yes/no oracle answers on every boundary. Every question is phrased in the vocabulary of a published curriculum or body of knowledge so the model recognizes it from training without fine-tuning effort. Each question carries its domain so the operator's attunement step binds it to the right project artifact.

## Sources

- SWEBOK (Guide to the Software Engineering Body of Knowledge, IEEE CS) — knowledge areas and the design principles / construction fundamentals cited below.
- SE2014 — ACM/IEEE Curriculum Guidelines for Undergraduate Degree Programs in Software Engineering; ten SEEK knowledge areas: CMP, FND, PRF, MAA, REQ, DES, VAV, PRO, QUA, SEC.
- CS2023 — ACM/IEEE-CS/AAAI Computer Science Curricula; Software Engineering (SE) knowledge area and its knowledge units.

## How to read a row

Each question lists: Domain (SWEBOK KA / SE2014 KA), the canonical term it tests, and whether it is a template question that must be bound to a project artifact during attunement (marked Binds to:). A question with no binding is answerable from the diff alone.

## A. Software Design — principles

Domain: SWEBOK Software Design / SE2014 DES / CS2023 SE: Software Design

- Does this module have one cohesive responsibility? — Cohesion
- Is coupling to other modules limited to their explicit interfaces (no reaching into internals)? — Coupling
- Is the internal representation hidden behind an interface? — Encapsulation and information hiding
- Can the implementation change without changing callers? — Separation of interface and implementation
- Is each concern (domain logic, persistence, presentation, cross-cutting) handled in exactly one place? — Separation of concerns
- Does every responsibility in this change have a home module, with none left floating? — Decomposition and modularization
- Does the abstraction expose only what callers need, and everything they need? — Sufficiency, completeness, primitiveness
- Does this reinvent something the codebase already provides? — Abstraction / reuse. Binds to: module inventory.
- Is an established design pattern applied where one fits, rather than reinvented? — Design patterns

## B. Software Design — key issues

Domain: SWEBOK Software Design (Key Issues) / SE2014 DES

- Is shared state and its synchronization explicit? — Concurrency
- For each failure this code can produce, is the handler identified? — Error and exception handling and fault tolerance
- Is persistence isolated from domain logic? — Data persistence
- Is control flow explicit rather than hidden in side effects? — Control and handling of events
- Is there exactly one source of truth for this piece of state? — Data persistence / data management
- Where components are distributed, is the boundary between them explicit? — Distribution of components

## C. Software Architecture

Domain: SWEBOK Software Architecture / SE2014 DES (architectural design) / CS2023 SE: Software Design

- Does this change respect the existing layer and boundary rules? — Architectural style / structure. Binds to: boundary map.
- Does this introduce a new dependency direction (a lower layer now depending on a higher one)? — Dependency structure
- Is the architectural decision recorded with its rationale? — Architecture description / design rationale. Binds to: ADR store.
- Does this make anything harder to delete or replace? — Modifiability
- Does this introduce a circular dependency? — Dependency structure
- Is this consistent with decisions already ratified in the ADR store, and does it contradict none of them? — Design rationale; settled decisions. Binds to: ADR store.

## D. Software Construction — fundamentals

Domain: SWEBOK Software Construction (Fundamentals) / SE2014 CMP, DES / CS2023 SE: Software Construction

- Is this the simplest construction that satisfies the requirement? — Minimizing complexity
- Is the expected change localized to one place? — Anticipating change
- Can this be verified without modifying it? — Constructing for verification
- Does this reuse existing code or library rather than duplicate it? — Reuse
- Does this follow the project coding standard? — Standards in construction. Binds to: style guide / linter config.
- Is this configurable because a stated need requires it, not speculative generality? — Anticipating change

## E. Software Construction — practical considerations

Domain: SWEBOK Software Construction (Practical Considerations) / SE2014 CMP

- Are identifiers the same canonical names used elsewhere for the same thing? — Naming conventions. Binds to: canonical name registry.
- Is the folder and file placement consistent with the existing structure? — Source code organization. Binds to: file tree.
- Are inputs at boundaries validated or asserted? — Defensive programming
- Are acquired resources (files, connections, memory, handles) bounded and released? — Resource management
- Are literal values replaced by named constants or configuration? — Coding practices
- Does the code express its intent without needing an external explanation? — Code documentation
- Is dead or unreachable code removed? — Code quality
- Is the operation safe to run twice? — Idempotence
- Does this introduce a dead name — a term retired elsewhere in the system? — Naming conventions. Binds to: canonical name registry.

## F. Software Requirements

Domain: SWEBOK Software Requirements / SE2014 REQ / CS2023 SE: Requirements Engineering

- Is the requirement stated as what, not how, before construction? — Requirements specification
- Is there an acceptance criterion that can be checked? — Verifiable requirements
- Are non-functional requirements (performance, security, reliability) explicit? — Quality attributes / non-functional requirements
- Is this change traceable to a requirement or decision? — Requirements tracing. Binds to: task / ADR reference.
- Is the scope bounded to the stated requirement and not a speculative future one? — Requirements validation / scope

## G. Verification and Validation

Domain: SWEBOK Software Testing, Software Quality / SE2014 VAV / CS2023 SE: Software Verification and Validation

- Is there a unit test that exercises this change? — Unit testing
- Is the touched boundary covered by an integration test? — Integration testing
- Does the existing suite still pass? — Regression testing
- Are failure paths and edge cases tested, not only the happy path? — Boundary-value analysis, error guessing
- Is static analysis / lint clean? — Static analysis
- Has the change been reviewed or inspected? — Reviews and inspections

## H. Software Quality and Maintenance

Domain: SWEBOK Software Quality, Software Maintenance / SE2014 QUA / CS2023 SE: Refactoring and Code Evolution

- Does this preserve or improve maintainability (analyzability, modifiability, testability)? — Maintainability quality attributes
- If technical debt is introduced, is it recorded? — Technical debt. Binds to: debt register.
- If this is a refactoring, is it behavior-preserving? — Refactoring
- Is the change's blast radius identified (what else depends on this)? — Impact analysis

## I. Software Configuration Management

Domain: SWEBOK Software Configuration Management / SE2014 PRO, PRF

- Is the change on a version-controlled branch with a descriptive commit? — Configuration control
- Are dependencies and toolchain versions identified and pinned? — Configuration identification
- Is the build reproducible from a clean checkout? — Build management
- Is the version bumped where the public surface changed? — Release management

## J. Software Engineering Process

Domain: SWEBOK Software Engineering Process / SE2014 PRO / CS2023 SE: Software Project Management

- Is the definition of done for this task explicit? — Process definition
- Is the work sized as a small, reviewable increment? — Incremental process
- Is the project mature enough that the existing file tree must be read before anything is written? — Maturity gate
- Is the operator expected to be involved at this decision point? — Operator involvement

## K. Software Security

Domain: SWEBOK Software Security / SE2014 SEC / CS2023 SEC

- Is input validated at the trust boundary? — Input validation
- Are secrets kept out of source and logs? — Secure coding practices
- Is least privilege applied to any new access? — Least privilege
- Does this change widen the attack surface — new endpoints, inputs, permissions, or dependencies exposed? — Attack surface

## L. Professional Practice

Domain: SWEBOK Software Engineering Professional Practice / SE2014 PRF

- Is the rationale for this decision recorded where the next person will find it? — Documentation and communication
- Would a new contributor find this discoverable without being told where to look? — Documentation and communication

## M. Algorithmic Foundations

Domain: CS2023 Algorithmic Foundations (AL) / SE2014 CMP

- Is the time and space complexity acceptable for the expected input size? — Complexity analysis
- Is the chosen data structure right for the dominant access pattern? — Data structure selection

## Gating by project maturity (to author next)

Sections A, D, E, F fire on every boundary. Sections C, H, I fire once a project is graded past greenfield. Section G fires when a test harness exists. Attunement binds every Binds to: question to the named artifact before it fires. Section M fires when the change touches a data path whose input size is unbounded.

## Open items

- Run the battery against past sessions; retire any question answering the same way more than 90% of the time.
- Decide which questions gate others (flat battery vs decision tree).
- Pull SWEBOK v4 section numbers for each canonical term as the citation column.
