---
source_doc_id: 1kfJgAGlGJKuxQPNpQntoG0Lpv__z9Y-X80WCdVn5V68
title: "Stack — Next.js (App Router): Curriculum and Boundary Questions (Draft v0.1)"
version: v0.1
status: Draft
export_date: 2026-09-30
owner: hades
source_revision_id: ANLCKQm2OsNQeq1DHMd3hTJLJyQYSnqsAswt7nbXE5FBmYmJxwCZFOjVusAlV9xyDunBTfMLayLeXO4W4GzGi1Mhfl2MiIGFI_LrknnHmQgo
source_tab: "t.0 (Tab 1)"
exported_via: user-Google-docs read_document (read-only)
---

# Stack — Next.js (App Router): Curriculum and Boundary Questions (Draft v0.1)

stack: nextjs

Parent: Boundary Question Bank — Core Predicates. Routing: Stack Category Routing. Status: Draft — first authoring pass; this document is the template the other stack documents follow. Owner: hades. Date: 2026-09-30. Docs version at authoring: Next.js 16.3.7 (App Router).

Purpose: When a boundary is planned or changed inside a Next.js codebase, these predicates fire in addition to the core predicates and the relevant domain-boundary predicates. Every question is phrased in the vocabulary of the official Next.js documentation and the Next.js Foundations course so the model recognizes it from training.

## Template sections (repeat for every stack document)

- Canonical label and version at authoring
- Lexicon aliases (seed) and disambiguation
- Curriculum sources
- Canonical concept map, by curriculum module
- Boundary questions, grouped by module, each tagged with its canonical term and source; template questions marked Binds to:
- Maturity gating
- Open items

## 1. Canonical label

Next.js App Router — a file-system based router built on React Server Components, Suspense, and Server Functions. The Pages Router is a separate, older model; a prompt that names getServerSideProps, getStaticProps, or pages/api is Pages Router and routes to a different question set.

## 2. Lexicon aliases (seed)

the website, the site, the frontend, the web app, pages, a page for X, landing page, the homepage, the backend (see disambiguation), the API, an endpoint, server stuff, load the data, show the data, form, submit the form, save it, make it fast, loading spinner, SEO, show up on Google, images are slow, the fonts, protect the page, only logged-in people, dark mode, deploy it, put it online, Vercel.

Disambiguation: "backend" or "API" inside a Next.js project resolves first to a Server Function (mutation from the app's own UI) and only to a Route Handler when an external client, webhook, or non-React consumer needs it (question 25). "middleware" in older material is now Proxy. "make it fast" fans out to streaming, caching, and image optimization — ask which is slow. "SEO" resolves to the Metadata API and rendering strategy, not to content writing.

## 3. Curriculum sources

- Next.js documentation, App Router → Getting Started (17 modules): Installation, Project Structure, Layouts and Pages, Linking and Navigating, Server and Client Components, Fetching Data, Mutating Data, Caching, Revalidating, Error Handling, CSS, Image Optimization, Font Optimization, Metadata and OG images, Route Handlers, Proxy, Deploying, Upgrading. Version 16.3.7.
- Next.js Foundations course (nextjs.org/learn/dashboard-app) — full-stack financial dashboard built chapter by chapter: styling, fonts and images, layouts and pages, navigation, database setup, fetching data, static and dynamic rendering, streaming, partial prerendering, search and pagination, mutating data, error handling, accessibility, authentication, metadata.
- React Foundations course (nextjs.org/learn/react-foundations) — prerequisite: components, props, state, hooks, Server Components, Suspense.
- Next.js Authentication guide — Data Access Layer pattern: authorization checks live next to the data, not only in Proxy.
- OWASP ASVS 5.0.0 — V3 Web Frontend Security, V4 API and Web Service, V13 Configuration, for the HTTP and configuration edges.

## 4. Canonical concept map, by module

- Installation: create-next-app, TypeScript, ESLint, module path aliases, environment variables (NEXT_PUBLIC_ prefix).
- Project Structure: app directory; file conventions layout, page, loading, error, not-found, route, template, global-error; route groups, private folders, colocation, dynamic segments, catch-all segments.
- Layouts and Pages: root layout, nested layouts, page, params, searchParams.
- Linking and Navigating: Link component, prefetching, prerendering, client-side navigation, useRouter, redirect.
- Server and Client Components: Server Component (default), Client Component, the 'use client' directive, the server-client boundary, serializable props, composition (passing Server Components as children), server-only.
- Fetching Data: async Server Components, fetch, ORM or database client, streaming, Suspense, loading.js, parallel and sequential fetching, request memoization.
- Mutating Data: Server Functions, Server Actions, the 'use server' directive, form action, useActionState, useFormStatus, revalidatePath, revalidateTag, redirect after mutation.
- Caching: cached data and UI, fetch caching, full route cache, router cache, Cache Components and the 'use cache' directive.
- Revalidating: time-based revalidation, on-demand revalidation, revalidateTag, revalidatePath.
- Error Handling: expected errors returned as values, uncaught exceptions, error.js boundary, global-error.js, notFound and not-found.js.
- CSS: Tailwind CSS, CSS Modules, global CSS, CSS-in-JS constraints with Server Components.
- Image Optimization: next/image, width and height or fill, sizes, remote patterns.
- Font Optimization: next/font, self-hosting, subsetting.
- Metadata and OG images: Metadata API, static metadata, generateMetadata, opengraph-image, sitemap, robots.
- Route Handlers: route.ts, Web Request and Response, HTTP method exports.
- Proxy: proxy.ts, rewrite, redirect, headers, respond before completion; not an authorization boundary on its own.
- Deploying: Vercel, self-hosted Node server, static export, feature support per target.
- Upgrading: codemods, canary, breaking-change notes.

## 5. Boundary questions

### Project Structure and Installation

- Do route files use the App Router file conventions (layout, page, loading, error, not-found, route) rather than ad-hoc names? — File conventions (Project Structure)
- Is non-route code colocated in private folders or outside app, and are route groups used only for organization and shared layouts? — Route groups; private folders; colocation (Project Structure)
- Is the placement consistent with this project's existing structure (app, ui or components, lib)? — Project organization (Project Structure). Binds to: file tree.
- Are secrets only in server-side environment variables, with NEXT_PUBLIC_ reserved for values that are safe to ship to the browser? — Environment variables (Installation); Configuration (ASVS V13)
- Are module path aliases used instead of deep relative imports? — Module path aliases (Installation)

### Layouts, Pages, Navigation

- Is shared UI in a layout and page-specific UI in a page, with exactly one root layout? — Root layout; nested layouts (Layouts and Pages)
- Are internal links rendered with the Link component so prefetching and client-side navigation apply? — Link; prefetching (Linking and Navigating)
- Are params and searchParams awaited and typed for dynamic segments? — Dynamic segments; params (Layouts and Pages)
- Are redirects performed with redirect on the server rather than client-side effects where possible? — Redirect (Linking and Navigating)

### Server and Client Components

- Is 'use client' applied only where interactivity or browser APIs are required, at the leaves of the tree? — Server-client boundary (Server and Client Components)
- Are all props crossing the server-to-client boundary serializable? — Serializable props (Server and Client Components)
- Are server-only modules (database client, secrets) never imported into Client Components, with server-only marking where it matters? — server-only (Server and Client Components)
- Are Server Components passed into Client Components as children rather than imported by them? — Composition (Server and Client Components)

### Fetching Data

- Is data fetched in Server Components (or through Route Handlers for client consumers), not in client effects by default? — Server-side data fetching (Fetching Data)
- Is slow or non-critical data wrapped in Suspense or loading.js so the shell streams? — Streaming; Suspense (Fetching Data)
- Are independent requests fetched in parallel rather than as a sequential waterfall? — Parallel data fetching (Fetching Data)
- Is database access isolated in a data layer (lib/data) rather than inline in components? — Data Access Layer (Authentication guide; Foundations course)

### Mutating Data

- Are mutations implemented as Server Functions or Server Actions under 'use server' rather than client-side fetches to hand-rolled endpoints? — Server Functions (Mutating Data)
- Does every Server Function validate its input and check authorization server-side, since it is a public endpoint? — Input validation; authorization (Mutating Data; ASVS V4)
- After a mutation, is the affected cache revalidated with revalidatePath or revalidateTag before redirecting? — Revalidation after mutation (Mutating Data; Revalidating)
- Are pending and error states surfaced with useActionState or useFormStatus? — Form state (Mutating Data)

### Caching and Revalidating

- Is the caching strategy for each route and data source explicit (static, dynamic, or Cache Components with 'use cache') rather than assumed from defaults? — Caching (Caching)
- Is revalidation chosen deliberately — time-based or on-demand — and are cache tags named canonically? — Revalidation strategy (Revalidating)
- Is user-specific or session-specific data excluded from shared caches? — Cache scope (Caching)

### Error Handling

- Are expected errors returned as values to the UI, and only uncaught exceptions left to error.js boundaries? — Expected errors; error boundaries (Error Handling)
- Is not-found handled with notFound and a not-found.js at the right segment? — Not found (Error Handling)
- Is a global-error.js present to catch root layout failures? — Global error (Error Handling)

### CSS, Images, Fonts

- Is styling done with this project's chosen method (Tailwind or CSS Modules) rather than mixed ad hoc? — Styling method (CSS). Binds to: style choice.
- Are images rendered with next/image with dimensions or fill and sizes set? — Image optimization (Image Optimization)
- Are fonts loaded with next/font rather than external stylesheet links? — Font optimization (Font Optimization)

### Metadata

- Is metadata defined through the Metadata API — static or generateMetadata — including Open Graph images for public pages? — Metadata API (Metadata and OG images)
- Are sitemap and robots generated through the file conventions where the site is public? — Sitemap; robots (Metadata and OG images)

### Route Handlers and Proxy

- Is a Route Handler used only where a Server Function does not fit (webhooks, external clients), with correct HTTP method exports and Web Response objects? — Route Handlers (Route Handlers)
- Is Proxy limited to rewrites, redirects, headers, and optimistic checks — never the sole authorization gate? — Proxy (Proxy; Authentication guide)
- Is authorization enforced in the Data Access Layer next to the data it protects? — Data Access Layer (Authentication guide)

### Deploying and Upgrading

- Is the deployment target (Vercel, self-hosted Node, static export) chosen, and are the features used supported on that target? — Deployment targets (Deploying)
- Is the Next.js version current or pinned deliberately, with upgrade codemods applied when moving? — Upgrading (Upgrading)
- Does the plan honor the React Foundations prerequisite — components, props, state, hooks, Suspense — before introducing Server Component patterns? — Prerequisite (React Foundations course)

## 6. Maturity gating

Greenfield: Project Structure and Installation 1, 2, 4; Server and Client Components 1–3; Mutating Data 1–2; Caching 1. Growing: all sections. Mature: add the Binds to: questions bound to the project's file tree and style choice, and the Data Access Layer questions become mandatory.

## 7. Open items

- Confirm exact naming of Cache Components / 'use cache' against the 16.x Caching module before the harness runs.
- Author the Pages Router variant only if the corpus shows Pages Router projects.
- Validate seed aliases against the mined session corpus.
