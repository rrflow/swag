---
source_doc_id: 1CQgolRDG7QcwMBd-af5HCua7sPDIhAaVEgxKqzgJjGU
title: "Stack — JavaScript (vanilla): Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQl9djUh0byE74ICoRO1PziTGU_TSl9_PcyA9y1HkRx2SMVtgAHi9FBbVSx5SZEsUEL1hJjrzT2dAOyocrMPNKBu_xErNAozEJJYxjNU
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — JavaScript (vanilla): Curriculum and Boundary Questions (Draft v0.1)

stack: vanilla-js

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30. Version at authoring: ECMAScript 2026 (ECMA-262, 17th edition, approved June 30, 2026); Node.js 24 Active LTS, Node.js 26 Current (LTS October 2026); Web Platform Baseline as the browser-compatibility reference.

Purpose: When a boundary is planned or changed in JavaScript that runs without a framework — a browser script, a Web Component, a Node script or service — these predicates fire in addition to the core predicates and any detected domain-boundary predicates. The core predicates (cohesion, coupling, error handling, testing, naming) are not repeated here; this document holds only what is unique to JavaScript as a language and to the browser and Node runtimes. Unlike Next.js or Go, vanilla JavaScript has no single vendor curriculum, so the anchors are the standards bodies (Ecma TC39, WHATWG, W3C) and MDN's structured Learn web development curriculum, which the MDN Curriculum research project defined and which partner courses are built on.

## 1. Canonical label

JavaScript (vanilla) — ECMAScript as specified by TC39, executed in a browser against the WHATWG DOM and HTML living standards and W3C Web APIs, or in Node.js against its standard library. Prototype-based, garbage-collected, single-threaded with an event loop, promises and async/await for concurrency, ES modules for code organization. Deterministic markers: .js or .mjs sources and .html files with no framework dependency in package.json; package.json alone when no framework is declared.

## 2. Lexicon aliases (seed)

just JavaScript, plain JS, no framework, a script, a script tag, a little interactive thing, when they click the button, the button doesn't work, nothing happens when I click, the page reloads when I submit, it says undefined is not a function, this is undefined, the console, a Node script, a quick script to do X, a bookmarklet, it works on my computer but not on my phone, make it work in Safari, the date is wrong, the number is off by a little.

Disambiguation — non-technical word → JavaScript term: "class" or "object" → objects are prototype-based; class is syntax over prototypes; "import" → ES modules (type="module" in the browser, "type": "module" in Node), not CommonJS require; "wait for it" → a promise and async/await; "this is undefined" → this binding — an arrow function or a lost method reference; "the page reloads on submit" → the form's default action, preventDefault; "make it work everywhere" → Web Platform Baseline, not user-agent sniffing; "the date is wrong" → Temporal or explicit time zones, not Date arithmetic; "the number is off" → floating point — Math.sumPrecise, integers, or BigInt; "a Chrome extension" → WebExtensions, a different stack; "jQuery" → legacy, resolve to the DOM APIs; "Node" versus "browser" → the runtime target must be chosen (question 30).

## 3. Curriculum sources

- MDN Learn web development — Core module: Dynamic scripting with JavaScript — What is JavaScript; JavaScript walkthrough; Troubleshooting; Variables; Numbers and operators; Strings and string methods; Arrays; Functions; Conditionals; Loops; Events; DOM scripting; Network requests; JSON; Debugging. Followed by the core module JavaScript frameworks and libraries (out of scope here) and the Accessibility, Design for developers, and Version control core modules.
- MDN Extension modules — Advanced JavaScript objects (object basics, prototypes, Classes in JavaScript); Client-side web APIs (manipulating documents, fetching data, third-party APIs, drawing graphics, video and audio, client-side storage); Asynchronous JavaScript (introduction, promises, async and await, sequencing, workers); Web forms; Web performance (including Performant JavaScript); Testing (cross-browser testing, feature detection, automated testing).
- MDN Curriculum (developer.mozilla.org/curriculum) — the structured skillset the Learn modules implement: core modules including JavaScript fundamentals, Accessibility, Design for developers; extensions including Custom JS objects, Web APIs, Security and privacy, Testing, Performance.
- MDN JavaScript Guide — Grammar and types; Control flow and error handling; Loops and iteration; Functions; Expressions and operators; Numbers and strings; Representing dates and times; Regular expressions; Indexed collections; Keyed collections; Working with objects; Using classes; Using promises; Typed arrays; Iterators and generators; Resource management; Internationalization; JavaScript modules. Intermediate: Equality comparisons and sameness; Closures; Enumerability and ownership.
- ECMA-262 ECMAScript 2026 (17th edition) — new in this edition: Array.fromAsync, Error.isError, Math.sumPrecise, Iterator.concat, Uint8Array to and from base64 and hex, Map and WeakMap getOrInsert, JSON.parse source text access and JSON.rawJSON. Prior editions relied on here: ES2023 change-by-copy array methods (toSorted, toReversed, with); ES2025 Iterator helpers, Set methods, Promise.try, Float16Array, import attributes. ECMA-402 for Intl.
- WHATWG HTML and DOM living standards; Fetch standard; W3C Web Components (custom elements, shadow DOM, template), Web Workers, Content Security Policy Level 3, Trusted Types, WAI-ARIA and the ARIA Authoring Practices Guide, WCAG 2.2.
- Web Platform Baseline (web.dev/baseline; WebDX Community Group) — the compatibility reference for "can I use this".
- Node.js documentation — ES modules, node: protocol imports, fs/promises, worker_threads, the built-in test runner (node:test), process and signals, type stripping (stable in 24), release schedule (one major per year from Node 27).
- OWASP ASVS 5.0.0 — V3 Web Frontend Security (DOM XSS sinks, CSP, cookies, browser-side controls), V1 Encoding and Sanitization.
- Style — Google JavaScript Style Guide; ESLint recommended rules; Prettier (community standard).

## 4. Canonical concept map, by module

- Language fundamentals: const, let, block scope, hoisting, strict mode, primitive, object, prototype, this binding, arrow function, closure, template literal, destructuring, spread, rest, optional chaining, nullish coalescing, strict equality, SameValueZero, truthiness, type coercion.
- Objects and collections: object literal, property descriptor, getter, setter, class, constructor, private field, static, inheritance via extends, composition, Array, Map, Set, WeakMap, WeakRef, typed array, structuredClone, change-by-copy methods, getOrInsert, iterator, generator, Iterator helpers, Iterator.concat.
- Asynchronous JavaScript: event loop, task, microtask, callback, Promise, then, catch, finally, async, await, Promise.all, allSettled, any, race, Promise.try, Array.fromAsync, top-level await, AbortController, AbortSignal.timeout, Web Worker, worker_threads, using declaration, Error cause, Error.isError.
- DOM and events: document, element, querySelector, textContent, createElement, DocumentFragment, classList, dataset, event, addEventListener, event delegation, bubbling, capture, preventDefault, passive listener, form, FormData, submit event, custom element, shadow DOM, template, slot, MutationObserver, IntersectionObserver, ResizeObserver.
- Modules and packaging: ES module, import, export, dynamic import, import map, bare specifier, import attribute, JSON module, bundler, lockfile, npm audit, polyfill.
- Network and data: fetch, Request, Response, response.ok, JSON.parse reviver, JSON.stringify, localStorage, sessionStorage, IndexedDB, cookie, CORS, Streams.
- Platform and compatibility: Baseline, browserslist, feature detection, progressive enhancement, runtime target.
- Security: XSS, DOM sink, innerHTML, Content Security Policy, nonce, Trusted Types, Sanitizer API, Subresource Integrity, HttpOnly cookie, same-origin policy.
- Accessibility: semantic element, first rule of ARIA, role, aria-label, focus management, keyboard operability, live region, WCAG 2.2.
- Performance: defer, module script, code splitting, long task, Core Web Vitals (LCP, INP, CLS), scheduler.yield, requestAnimationFrame, layout thrash, memory leak.
- Node.js: node: prefix, ESM, fs/promises, process, signal, unhandledRejection, node:test, worker_threads, type stripping, Active LTS.

## 5. Boundary questions

### Language Fundamentals

- Are variables declared with const by default and let only when reassigned, never var? — Grammar and types; Variables (MDN)
- Is strict equality used, with coercion and sameness semantics understood where loose comparison appears? — Equality comparisons and sameness (MDN)
- Does the code run as a module (type="module", or "type": "module" in Node), so strict mode is on and nothing leaks into global scope? — JavaScript modules (MDN Guide)
- Is this binding handled deliberately — arrow functions for lexical this, bound or wrapped methods when passed as callbacks? — Functions; this (MDN)
- Are template literals, destructuring, optional chaining, and nullish coalescing used for clarity rather than concatenation and nested guards? — Expressions and operators (MDN Guide)
- Are dates and times handled with Temporal or explicit time-zone-aware formatting via Intl, never Date arithmetic? — Representing dates and times (MDN Guide); ECMA-402
- Is floating-point handled deliberately — Math.sumPrecise for sums, integer arithmetic or BigInt where exactness matters? — Numbers and strings (MDN Guide); ES2026

### Objects, Collections, Classes

- Is the collection chosen for the access pattern — Array for ordered lists, Map and Set for keyed or unique data, plain objects for fixed-shape records — with getOrInsert for the upsert pattern? — Indexed collections; Keyed collections (MDN Guide); ES2026
- Is shared data treated immutably — spread, toSorted, toReversed, with, structuredClone — rather than mutated in place? — Indexed collections (ES2023 change-by-copy)
- Are classes used only where identity or prototype semantics are needed, with private fields for encapsulation and composition preferred over deep inheritance? — Using classes; Classes in JavaScript (MDN)
- Are iterators and generators used for lazy sequences, with Iterator helpers instead of intermediate arrays? — Iterators and generators (MDN Guide); ES2025

### Asynchronous JavaScript

- Is asynchronous work written with async and await, and is every promise awaited, returned, or explicitly handled? — Asynchronous JavaScript: promises, async and await (MDN)
- Are errors caught at the boundary, chained with cause, and identified with Error.isError rather than instanceof across realms? — Control flow and error handling (MDN Guide); ES2022, ES2026
- Are independent asynchronous operations run in parallel with Promise.all or allSettled rather than awaited in sequence? — Sequencing asynchronous operations (MDN)
- Is CPU-heavy or long-running work moved to a Web Worker or worker_threads so the main thread stays responsive? — Introducing workers (MDN); Web Workers
- Is cancellation implemented with AbortController for fetch, listeners, and timers? — Fetch; AbortController (WHATWG)
- Is deterministic cleanup done with try/finally or using declarations? — Resource management (MDN Guide)

### DOM Scripting and Events

- Are DOM references queried once and cached, and are DOM writes batched or built in a DocumentFragment to avoid layout thrash? — DOM scripting (MDN); Performant JavaScript
- Are listeners attached with addEventListener, removed when no longer needed, and delegated to a parent for dynamic lists? — Events (MDN)
- Is form submission intercepted with preventDefault only where the page must not reload, and does the form still function without JavaScript where feasible? — Web forms; Events (MDN); progressive enhancement
- Is untrusted content inserted with textContent or createElement, never innerHTML? — Security and privacy (MDN Curriculum); ASVS V3
- Are reusable UI pieces built as Web Components — custom elements, shadow DOM, template — rather than a framework added for one widget? — Web Components (W3C; MDN Client-side web APIs)
- Are observers (Mutation, Intersection, Resize) used instead of polling, and disconnected when done? — Client-side web APIs (MDN)

### Modules and Dependencies

- Are ES modules used with explicit imports and exports, bare specifiers resolved by an import map or bundler, and no shared globals between scripts? — JavaScript modules (MDN Guide); import maps (WHATWG HTML)
- Is the module graph free of circular dependencies, with one responsibility per module? — JavaScript modules
- Does the standard library cover the need before a dependency is added — Temporal over a date library, Uint8Array base64 methods over a polyfill, Iterator helpers over a utility library? — ECMAScript 2025–2026 additions
- Are dependencies minimal, pinned by lockfile, and audited? — Client-side tooling (MDN); npm audit
- Is the placement consistent with this project's existing structure? — Project organization. Binds to: file tree.

### Network and Data

- Is fetch used with response.ok checked, a timeout via AbortSignal.timeout, and JSON parsing wrapped in error handling? — Network requests; Fetching data (MDN); Fetch standard
- Is data arriving from JSON, URLs, or storage validated for shape before use? — JSON (MDN); Security and privacy
- Is client-side storage chosen deliberately — localStorage for small synchronous values, IndexedDB for structured or large data, cookies only for what the server needs — with quota and failure handled? — Client-side storage (MDN)

### Compatibility and Runtime Target

- Is every web feature checked against Web Platform Baseline or this project's browserslist before use, with polyfills only where the target requires them? — Baseline (web.dev); Web standards and semantics (MDN Curriculum). Binds to: browser support target.
- Is feature detection used rather than user-agent sniffing? — Cross-browser testing; feature detection (MDN Testing)
- Is the runtime target explicit — browser, Node 24 LTS (26 when it enters LTS), or both — and is the code free of the other runtime's globals? — Runtime target. Binds to: runtime.

### Security

- Is a Content Security Policy in place, with no inline scripts and no eval or new Function? — Content Security Policy (W3C); ASVS V3
- Are DOM XSS sinks — innerHTML, insertAdjacentHTML, document.write, javascript: URLs — avoided, or guarded by Trusted Types or the Sanitizer API? — DOM sinks; Trusted Types; ASVS V3, V1
- Are tokens and secrets kept out of client code and out of localStorage where an HttpOnly cookie serves? — Security and privacy (MDN Curriculum); ASVS V3
- Are third-party scripts loaded with Subresource Integrity and reviewed for the permissions they take? — Subresource Integrity (W3C)

### Accessibility

- Are native semantic elements used before ARIA, with ARIA only where no native element exists? — First rule of ARIA use (W3C); Accessibility (MDN core module)
- Is every interactive element keyboard operable with visible focus, and is dynamic content announced through live regions where needed? — Accessibility (MDN); WCAG 2.2; ARIA Authoring Practices Guide

### Performance

- Is script loading non-blocking (module or defer), split by route, and is bundle size measured? — Performant JavaScript (MDN Web performance)
- Are Core Web Vitals measured, with long tasks broken up using scheduler.yield or requestAnimationFrame? — Web performance (MDN); web.dev
- Are timers, intervals, listeners, and observers released so nothing leaks across navigations or component lifetimes? — Performant JavaScript (MDN)

### Testing and Debugging

- Are unit tests present (node:test or this project's runner) and end-to-end tests for critical flows? — Testing (MDN extension module); node:test. Binds to: test runner.
- Are console.log statements removed, with structured error reporting in their place? — Debugging JavaScript (MDN)

### Style and Naming

- Does the code pass ESLint recommended rules plus this project's rules, and Prettier? — ESLint; Google JavaScript Style Guide. Binds to: lint config.
- Are exported functions documented with JSDoc types where TypeScript is not in use, so editors can type-check? — JSDoc
- Are names the same canonical names used elsewhere in this project for the same thing? — Canonical naming. Binds to: canonical name registry.

### Node.js (fires when the runtime target is Node)

- Are built-in modules imported with the node: prefix, and are promise-based APIs (fs/promises) used over callbacks and sync calls on hot paths? — Node.js documentation
- Are unhandled rejections and process signals handled for graceful shutdown? — process (Node.js)
- If .ts files run directly under Node, is only erasable syntax used? — Type stripping (Node 24 stable)
- Is the Node version pinned to Active LTS in package.json engines and CI? — Release schedule (Node.js)

## 6. Maturity gating

Greenfield: Language 1–4; Async 1–3; DOM 2–4; Modules 1, 3; Network 1–2; Compatibility 1, 3; Security 1–2; Accessibility 1. Growing: all sections. Mature: add the Binds to: questions bound to file tree, browser support target, runtime, test runner, lint config, and canonical name registry; Performance and Testing sections become mandatory.

## 7. Open items

- Secondary sources disagree on whether Temporal and explicit resource management (using) are in the 17th edition text or only shipping in engines (Node 26 enables Temporal by default). Verify against the ECMA-262 introduction before pinning the citation column.
- Validate seed aliases against the mined session corpus; the "nothing happens when I click" family is expected to resolve to DOM 2 and Language 4.
- Registry additions queued from this session: sql, drizzle, prisma, ruby, plus Rust contract-boundary tools specta and schemars (JSON Schema from Rust types) under the composition rule in Stack — TypeScript section 0.
