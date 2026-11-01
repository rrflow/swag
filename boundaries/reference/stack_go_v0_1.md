---
source_doc_id: 14iXVT2t-pO_S9cVPOSt_OTRK1o9kDDeAN7Db_7UNohI
title: "Stack — Go: Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQmm7Q2GHnP2pcEgXTV6NX5HMiHy5772DwctvU1mYIDPBPEaxlCww0z-7gAgitAnsJnDhgecCGX6irgP-QxCjiYwQda_d58SBiSYWEMH
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — Go: Curriculum and Boundary Questions (Draft v0.1)

stack: go

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30. Version at authoring: Go 1.27 (August 2026).

Purpose: When a boundary is planned or changed in a Go codebase, these predicates fire in addition to the core predicates and any detected domain-boundary predicates. Every question is phrased in the vocabulary of the official Go documentation — A Tour of Go, Effective Go, the Go Code Review Comments wiki, the Google Go Style Guide, and the Go Modules reference — so the model recognizes it from training.

## 1. Canonical label

Go — statically typed, garbage-collected language with goroutines and channels for concurrency, implicit interface satisfaction, error values instead of exceptions, and a single toolchain (go build, go test, go vet, gofmt, go mod). Deterministic markers: go.mod, go.sum.

## 2. Lexicon aliases (seed)

Go, Golang, gopher, the service, the microservice, the API server, the backend (in a Go context), the CLI tool, goroutines, make it concurrent, single binary, one file to deploy, fast startup, small container, the worker, the queue consumer.

Disambiguation — non-technical word → Go term: class or object → struct with methods (no classes); inheritance → embedding and composition; interface → interface, satisfied implicitly, defined where it is used; exception, try/catch → error return values checked at every call (panic is not exception handling); thread → goroutine; async/await → goroutines and channels; null → nil, and zero values in general; package manager or npm → Go modules; generics → type parameters (since 1.18; generic methods since 1.27); getter → method without a Get prefix; "the standard project layout" → the official Organizing a Go module guidance, not the community project-layout repository.

## 3. Curriculum sources

- A Tour of Go (go.dev/tour) — Basics (packages, imports, exported names, functions, multiple results, variables, basic types, zero values, type conversions, constants); Flow control (for, if, switch, defer); More types (pointers, structs, arrays, slices, maps, function values, closures); Methods and interfaces (methods, pointer receivers, interfaces, implicit implementation, Stringer, errors, readers, type assertions and switches); Generics (type parameters, generic types); Concurrency (goroutines, channels, buffered channels, range and close, select, sync.Mutex).
- Effective Go (go.dev/doc/effective_go) — formatting, commentary, names, control structures, functions, data, initialization, methods, interfaces and other types, the blank identifier, embedding, concurrency, errors. Its own preface states it was written for the 2009 release and has not been updated for modules or generics; the sources below supply the current layer.
- Go Code Review Comments (go.dev/wiki/CodeReviewComments) and Go Test Comments — the canonical review checklist: gofmt, contexts, copying, declaring empty slices, doc comments, don't panic, error strings, examples, goroutine lifetimes, handle errors, imports, in-band errors, indent error flow, initialisms, interfaces, mixed caps, named result parameters, naked returns, package comments, package names, pass values, receiver names, receiver type, synchronous functions, useful test failures, variable names.
- Google Go Style Guide (google.github.io/styleguide/go) — style principles: clarity, simplicity, concision, maintainability, consistency; Style Decisions; Best Practices.
- How to Write Go Code, Organizing a Go module (go.dev/doc/modules/layout), Go Modules Reference, Go Toolchains.
- Go Proverbs (Rob Pike) — the canonical one-line anchors: don't communicate by sharing memory, share memory by communicating; channels orchestrate, mutexes serialize; the bigger the interface, the weaker the abstraction; make the zero value useful; a little copying is better than a little dependency; clear is better than clever; errors are values; don't just check errors, handle them gracefully; don't panic.
- Release notes 1.18 (generics, fuzzing), 1.21 (log/slog), 1.22 (per-iteration loop variables, net/http routing patterns), 1.23 (range-over-func iterators), 1.24 (tool directives in go.mod), 1.25 (WaitGroup.Go), 1.26 (go fix modernizers), 1.27 (generic methods).

## 4. Canonical concept map, by module

- Packages and modules: module, module path, go.mod, go.sum, go directive, toolchain directive, tool directive, package, import path, exported identifier, internal package, cmd directory, go mod tidy, go work, GOPROXY, govulncheck.
- Names and formatting: gofmt, goimports, MixedCaps, initialisms, package name, receiver name, doc comment, package comment.
- Types: struct, method, pointer receiver, value receiver, interface, implicit satisfaction, interface check, embedding, composition, zero value, composite literal, type parameter, constraint, type assertion, type switch, Stringer, io.Reader, io.Writer.
- Errors: error value, sentinel error, custom error type, wrapping with %w, errors.Is, errors.As, errors.Join, panic, recover, in-band error.
- Functions: multiple return values, named result parameters, naked return, defer, closure, variadic.
- Context: context.Context, ctx as first parameter, cancellation, deadline, context values.
- Concurrency: goroutine, goroutine lifetime, channel, buffered channel, close, range over channel, select, sync.Mutex, sync.RWMutex, sync.WaitGroup, WaitGroup.Go, errgroup, race detector, per-iteration loop variable.
- Data: array, slice, capacity, append, make, map, nil slice vs empty slice, aliasing, time.Time, time.Duration, iter.Seq, range-over-func.
- Testing: testing package, _test.go, table-driven tests, t.Run subtests, t.Errorf, got/want, testable Example, benchmark, fuzz test, go test -race, go test -cover.
- Tooling and runtime: go vet, go fix, staticcheck, golangci-lint, log/slog, net/http, ServeMux patterns, static binary, CGO_ENABLED=0.

## 5. Boundary questions

### Packages, Modules, Layout

- Is the code inside a module with a go.mod naming the module path, and is go.sum committed? — Modules (Modules Reference)
- Is each package one directory with a short, lowercase, singular name that does not stutter with its identifiers and is not util, common, or misc? — Package names (Effective Go; Code Review Comments)
- Are binaries under cmd/ and non-public packages under internal/, so privacy is enforced by the toolchain? — Organizing a Go module; internal packages
- Is the placement consistent with this project's existing module layout? — Project organization. Binds to: file tree.
- Is the go directive set deliberately, with a toolchain directive where reproducibility matters? — Go toolchains
- Is the dependency set minimal, go mod tidy clean, and govulncheck run? — A little copying is better than a little dependency (Go Proverbs); Vulnerability management
- Are executable tool dependencies tracked with tool directives rather than a tools file workaround? — Tool directives (Go 1.24)

### Names, Formatting, Documentation

- Is all code gofmt-formatted, with imports grouped standard library first? — gofmt; imports (Code Review Comments)
- Are identifiers MixedCaps with consistent initialisms (URL, ID, HTTP) and no underscores? — Mixed caps; initialisms (Code Review Comments)
- Do getters omit the Get prefix, and do single-method interfaces end in -er? — Getters; interface names (Effective Go)
- Are receiver names short, consistent across a type's methods, and never this or self? — Receiver names (Code Review Comments)
- Does every exported identifier carry a doc comment beginning with its name, and every package a package comment? — Doc comments; package comments (Code Review Comments)
- Are variable names short in small scopes and descriptive in large ones? — Variable names (Code Review Comments)
- Are names the same canonical names used elsewhere in this project for the same thing? — Canonical naming. Binds to: canonical name registry.

### Types, Interfaces, Embedding, Generics

- Are interfaces defined on the consumer side and kept to one or two methods? — Interfaces (Code Review Comments); The bigger the interface, the weaker the abstraction (Go Proverbs)
- Do functions accept interfaces and return concrete types? — Accept interfaces, return structs (Code Review Comments)
- Is composition via embedding used rather than simulated inheritance? — Embedding (Effective Go)
- Is the zero value of each type useful, with a constructor only where invariants require one? — Make the zero value useful (Go Proverbs; Effective Go)
- Is the receiver kind (pointer or value) chosen once per type and applied to all its methods? — Receiver type (Code Review Comments)
- Where a type is intended to satisfy an interface, is a compile-time interface check present? — Interface checks (Effective Go)
- Are type parameters used only where they remove real duplication, with named constraints? — Generics (Tour; Go 1.18, generic methods 1.27)
- Is any interface{} or any justified, rather than used to avoid a type? — interface{} says nothing (Go Proverbs)

### Errors

- Is every returned error checked, never discarded with the blank identifier? — Handle errors (Code Review Comments)
- Are errors returned rather than panicked, with panic reserved for unrecoverable programmer errors? — Don't panic (Code Review Comments; Go Proverbs)
- Are error strings lowercase without trailing punctuation? — Error strings (Code Review Comments)
- Are errors wrapped with %w and inspected with errors.Is or errors.As, never by string matching? — Error wrapping (errors package, Go 1.13)
- Are sentinel errors and custom error types exported deliberately as part of the API? — Errors are values (Go Proverbs)
- Is the error path handled and returned early so the happy path stays unindented? — Indent error flow (Code Review Comments)
- Are in-band error values (-1, empty string, nil) replaced by a second return value? — In-band errors (Code Review Comments)

### Functions and Control Flow

- Are named result parameters used only where they document meaning, and naked returns avoided? — Named result parameters; naked returns (Code Review Comments)
- Is cleanup deferred immediately after acquisition? — defer (Effective Go)
- Are functions synchronous by default, leaving concurrency to the caller? — Synchronous functions (Code Review Comments)
- Are small values passed by value rather than by pointer for the sake of it? — Pass values (Code Review Comments)

### Context

- Is context.Context the first parameter, named ctx, passed explicitly and never stored in a struct? — Contexts (Code Review Comments)
- Are cancellation and deadlines propagated and honored (select on ctx.Done, or ctx-aware APIs)? — Cancellation (context package)
- Are context values limited to request-scoped data and never used to pass required parameters? — Context values (context package)

### Concurrency

- Does every goroutine have a known lifetime — who stops it, when, and how it exits? — Goroutine lifetimes (Code Review Comments)
- Is channel ownership clear, with the sender the only party that closes? — Channels (Effective Go; Tour)
- Is shared state either protected by a mutex or avoided by passing data over channels? — Share memory by communicating; channels orchestrate, mutexes serialize (Go Proverbs; Effective Go)
- Are goroutines coordinated with sync.WaitGroup (WaitGroup.Go) or errgroup, never time.Sleep? — WaitGroup (sync package, Go 1.25)
- Is go test -race part of the test run? — Race detector
- Is any leftover loop-variable capture workaround removed now that loop variables are per-iteration? — Loop variable semantics (Go 1.22)
- Is concurrency introduced for a measured reason, not by default? — Concurrency is not parallelism (Go Proverbs)

### Data

- Is slice and map aliasing understood, with copies made deliberately where the caller may mutate? — Slices; copying (Tour; Code Review Comments)
- Are empty slices declared as var s []T rather than []T{} unless a non-nil value is required (JSON)? — Declaring empty slices (Code Review Comments)
- Is make used to preallocate where the size is known? — make; append (Effective Go)
- Are time.Time and time.Duration used for time, never bare integers? — time package
- Are sequences exposed as iterators (iter.Seq) where range-over-func fits? — Range over func (Go 1.23)

### Testing

- Are tests table-driven with t.Run subtests, in _test.go files beside the code? — Table-driven tests (Go Test Comments)
- Do failures report got and want with context via t.Errorf, not panics? — Useful test failures (Code Review Comments)
- Are testable Examples provided for exported API? — Examples (Code Review Comments)
- Are benchmarks present for performance-sensitive code and fuzz tests where input is parsed? — Benchmarks; fuzzing (testing package, Go 1.18)
- Is coverage measured against this project's threshold? — go test -cover. Binds to: coverage threshold.

### Tooling, Logging, Runtime

- Do go vet and this project's linter pass, and has go fix been run for modernizers? — go vet; go fix (Go 1.26). Binds to: lint config.
- Is logging structured with log/slog rather than fmt.Println or the legacy log package? — log/slog (Go 1.21)
- Is an HTTP server built on net/http with routing patterns and explicit timeouts before a framework is reached for? — net/http (Go 1.22 patterns)
- Is the binary static where deployment expects one file (CGO_ENABLED=0 when cgo is not needed)? — Static binaries

## 6. Maturity gating

Greenfield: Packages 1–3, 6; Names 1–2, 5; Types 1–2, 4; Errors 1–2, 4, 6; Context 1–2; Concurrency 1–3; Testing 1–2. Growing: all sections. Mature: add the Binds to: questions bound to file tree, canonical name registry, coverage threshold, and lint configuration; Documentation and Tooling sections become mandatory.

## 7. Open items

- Validate seed aliases against the mined session corpus.
- Decide whether common frameworks (chi, gin, echo, gRPC) get sub-sections here or separate stack values, mirroring the Rust open item.
- Pin Code Review Comments headings and Google Style Guide section anchors as the citation column once the harness exists.
