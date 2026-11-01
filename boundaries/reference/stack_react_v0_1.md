---
source_doc_id: 1dqcX24VooJY4CcZGhwL3E6WniRQ4fCpI2QHeDKPhWKs
title: "Stack — React: Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQlH9uW4ywo6S7YNf51CtdiHm2wy__i5lKrkVk2Nl1Lg6jbEgV5kOWwxZb_YZChaR6sZDdNlLazTJv-7aHX4PNLvQHQN9C3d4GPCOFp9
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — React: Curriculum and Boundary Questions (Draft v0.1)

stack: react

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30. Version at authoring: React 19.3.0 (September 9, 2026); React Compiler 1.0 (October 2025).

Purpose: When a boundary is planned or changed in a React codebase that is not under a meta-framework, these predicates fire in addition to the core predicates and any detected domain-boundary predicates. Every question is phrased in the vocabulary of the react.dev Learn curriculum, the Rules of React, and the React 19 reference so the model recognizes it from training. When Next.js markers are present the nextjs document fires instead and imports this document's component-level sections.

## 1. Canonical label

React — a library for building user interfaces from components: pure functions of props and state, rendered declaratively, with Hooks for state and side effects, and (since 19) Actions for mutations and Server Components as an optional architecture. Deterministic markers: react in package.json without a meta-framework dependency; vite.config.* or an equivalent build tool.

## 2. Lexicon aliases (seed)

the UI, the frontend, the interface, components, make it interactive, when they click, a button that does X, a dropdown, a modal, a popup, a form, the state, it's not updating, it updates twice, it re-renders too much, it's slow when I type, infinite loop, the page flickers, the list is slow, Vite, a dashboard, a widget, dark mode toggle.

Disambiguation — non-technical word → React term: "page" or "screen" → a component tree, and a router only if navigation is requested; "it's not updating" → state mutated in place or a missing key, not a rendering bug; "load the data" → data fetching via a framework or a Suspense-enabled data library, not useEffect plus fetch; "remember this across pages" → lifted state, Context, or a store, decided by the Managing State questions; "class component" → legacy, route to function components and Hooks; "React Native" or "mobile app" → a different stack, not this document; "Next" or "server components" with a framework present → nextjs; "make it faster" → Profiler first, React Compiler second, manual memoization last.

## 3. Curriculum sources

- react.dev Learn — Describing the UI (Your First Component; Importing and Exporting Components; Writing Markup with JSX; JavaScript in JSX with Curly Braces; Passing Props to a Component; Conditional Rendering; Rendering Lists; Keeping Components Pure; Your UI as a Tree). Adding Interactivity (Responding to Events; State: A Component's Memory; Render and Commit; State as a Snapshot; Queueing a Series of State Updates; Updating Objects in State; Updating Arrays in State). Managing State (Reacting to Input with State; Choosing the State Structure; Sharing State Between Components; Preserving and Resetting State; Extracting State Logic into a Reducer; Passing Data Deeply with Context; Scaling Up with Reducer and Context). Escape Hatches (Referencing Values with Refs; Manipulating the DOM with Refs; Synchronizing with Effects; You Might Not Need an Effect; Lifecycle of Reactive Effects; Separating Events from Effects; Removing Effect Dependencies; Reusing Logic with Custom Hooks).
- Thinking in React — the five steps: break the UI into a component hierarchy; build a static version; find the minimal but complete representation of state; identify where state should live; add inverse data flow.
- Rules of React — Components and Hooks must be pure; React calls Components and Hooks; Rules of Hooks.
- React 19 reference and release posts — Actions, useActionState, useFormStatus, useOptimistic, use, ref as a prop, Suspense, useTransition, useDeferredValue, useId; 19.2: Activity, useEffectEvent, Performance Tracks, Partial Pre-rendering; 19.3: independent transitions, Trusted Types integration. React Compiler 1.0 and the compiler docs.
- Creating a React App / Build a React app from Scratch (react.dev) — framework-first guidance; Create React App sunset (February 2025).
- Accessibility — react.dev accessibility guidance and the WAI-ARIA Authoring Practices Guide.
- Testing — React Testing Library query priorities (community standard referenced from react.dev).

## 4. Canonical concept map, by module

- Describing the UI: component, JSX, curly braces, props, children, conditional rendering, list, key, purity, render tree, module dependency tree.
- Adding Interactivity: event handler, state, useState, render, commit, snapshot, batching, updater function, immutable update, spread.
- Managing State: declarative UI, state structure, redundant state, derived state, lifting state up, controlled component, preserving and resetting state with keys, reducer, useReducer, Context, useContext, provider.
- Escape Hatches: ref, useRef, DOM node, Effect, useEffect, synchronization, external system, dependency array, cleanup, reactive value, Effect Event, useEffectEvent, custom Hook.
- Rules of React: idempotent render, side effects outside render, immutable props and state, Hooks at top level, StrictMode double-invocation.
- React 19: Action, useActionState, useFormStatus, useOptimistic, use, ref prop, Suspense boundary, fallback, transition, useTransition, useDeferredValue, useId, Activity, ViewTransition, React Compiler, automatic memoization, memo, useMemo, useCallback, Profiler, Performance Tracks.
- Tooling: Vite, framework, StrictMode, eslint-plugin-react-hooks, React DevTools, React Testing Library, error boundary.

## 5. Boundary questions

### Describing the UI

- Is each component a pure function of its props and state, with no side effects during render? — Keeping Components Pure (Learn); Rules of React
- Does the component tree map to a UI hierarchy identified before coding, with a static version buildable first? — Thinking in React, steps 1–2
- Is each component small enough to name by one responsibility, and exported consistently with this project's convention? — Importing and Exporting Components. Binds to: export convention.
- Are list items keyed by stable, unique data identifiers — never the array index when items can reorder or be inserted? — Rendering Lists; key
- Is conditional rendering expressed in JSX (ternary, &&, or early return of null) rather than imperative branches building markup? — Conditional Rendering
- Are props treated as read-only, with children used for composition rather than render-prop workarounds? — Passing Props to a Component

### Adding Interactivity

- Are event handlers passed as functions and named handleX on the component, onX on the prop? — Responding to Events
- Is state reserved for values that change over time and drive rendering, with derived values computed during render? — State: A Component's Memory; Choosing the State Structure
- Are state updates treated as snapshots, using an updater function whenever the next value depends on the previous? — State as a Snapshot; Queueing a Series of State Updates
- Are objects and arrays in state replaced immutably, never mutated in place? — Updating Objects in State; Updating Arrays in State

### Managing State

- Is the state structure minimal — no redundant, duplicated, contradictory, or deeply nested state? — Choosing the State Structure; Thinking in React, step 3
- Is shared state lifted to the closest common parent, and otherwise kept local? — Sharing State Between Components; Thinking in React, step 4
- Where a component must reset, is the reset done with a key change rather than an Effect? — Preserving and Resetting State
- Are many related state transitions consolidated in a reducer rather than scattered across setters? — Extracting State Logic into a Reducer
- Is Context used only for data needed deep in the tree (theme, current user, locale), not to avoid passing a prop one level? — Passing Data Deeply with Context
- Is an external state library introduced only after reducer plus Context is shown insufficient, and is the choice recorded? — Scaling Up with Reducer and Context. Binds to: state-management choice.
- Does data flow down through props and up through callbacks, with no hidden channels? — Thinking in React, step 5 (inverse data flow)

### Escape Hatches

- Is every Effect synchronizing with an external system, and is no Effect transforming data for render or responding to a user event? — Synchronizing with Effects; You Might Not Need an Effect
- Does each Effect declare its reactive dependencies honestly, with the lint rule enforced and no suppression comments? — Lifecycle of Reactive Effects; Removing Effect Dependencies
- Does every Effect that subscribes, connects, or starts something return a cleanup? — Lifecycle of Reactive Effects
- Are non-reactive reads inside Effects separated with useEffectEvent? — Separating Events from Effects (19.2)
- Are refs used only for values that do not affect rendering and for DOM access, never read or written during render? — Referencing Values with Refs; Manipulating the DOM with Refs
- Is reusable stateful logic extracted into a custom Hook named useX, with a clear input and return contract? — Reusing Logic with Custom Hooks
- Are Hooks called only at the top level of a component or custom Hook, never conditionally or in loops? — Rules of Hooks

### Rules of React and Strictness

- Are components and Hooks idempotent, so double-invocation under StrictMode produces the same result? — Components and Hooks must be pure; StrictMode
- Are props, state, and Hook return values never mutated? — Rules of React
- Is StrictMode enabled at the root in development? — StrictMode

### Data, Actions, Suspense (React 19)

- Is data fetched through the framework or a Suspense-enabled data library rather than raw useEffect plus fetch? — You Might Not Need an Effect; Suspense
- Are form submissions implemented as Actions with useActionState and useFormStatus, surfacing pending and error state? — Actions (React 19)
- Is optimistic UI implemented with useOptimistic where perceived latency matters? — useOptimistic
- Is the use API used to read promises or Context in render where it simplifies the code, and never called conditionally? — use (React 19; 19.3 warning)
- Are Suspense boundaries placed around slow subtrees with fallbacks at the level the design intends? — Suspense
- Are non-urgent updates wrapped in transitions to keep input responsive? — useTransition; useDeferredValue (19.3 independent transitions)
- Is ref passed as an ordinary prop, with forwardRef removed? — ref as a prop (React 19)
- Are generated ids for accessibility attributes produced with useId, never Math.random? — useId

### Performance

- Is the React Compiler enabled; and if not, is manual memoization (memo, useMemo, useCallback) added only after profiling shows a need? — React Compiler 1.0; Profiler; Performance Tracks
- Is hidden-but-preserved UI implemented with Activity rather than conditional unmounting where state must survive? — Activity (19.2)
- Are long lists virtualized, and are large components split so a keystroke does not re-render the page? — Render and Commit; community best practice

### Accessibility and Errors

- Are semantic elements, labels, keyboard operability, and ARIA used per the Authoring Practices Guide rather than div-and-onClick? — Accessibility (react.dev; WAI-ARIA APG)
- Are error boundaries placed around risky subtrees so one failure does not blank the app? — Error boundaries

### Tooling, Structure, Testing

- Was the project created with a framework or Vite per current guidance, never Create React App? — Creating a React App (CRA sunset, February 2025)
- Is eslint-plugin-react-hooks active (rules-of-hooks, exhaustive-deps) together with the compiler's lint rules? — Tooling
- Is React pinned at a current 19.x release, with the react-server-dom security advisories accounted for? — Versions (patched releases 19.0.4, 19.1.5, 19.2.4)
- Is the placement consistent with this project's existing component and feature structure? — Project organization. Binds to: file tree.
- Are component props typed as interfaces where the project uses TypeScript? — Typing. Binds to: typescript stack value.
- Do tests query by role, label, and text rather than implementation details? — Testing Library query priorities

## 6. Maturity gating

Greenfield: Describing the UI 1, 2, 4; Adding Interactivity 2–4; Managing State 1–2; Escape Hatches 1–3, 7; Rules 1, 3; Data 1–2; Tooling 1–2. Growing: all sections. Mature: add the Binds to: questions bound to export convention, state-management choice, file tree, and the TypeScript stack; Performance and Accessibility sections become mandatory.

## 7. Open items

- Validate seed aliases against the mined session corpus; the "it's not updating" family is expected to be large and to resolve mostly to Adding Interactivity 3–4 and Describing the UI 4.
- Decide how nextjs imports this document's component-level sections without duplicating them.
- Decide whether React Router or TanStack Router becomes a sub-section or a separate stack value.
- React Native is out of scope here; add to the routing registry if the corpus shows mobile requests.
