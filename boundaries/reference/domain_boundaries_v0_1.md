---
title: Domain Boundaries — user, admin, chat, AI (Draft v0.1)
version: v0.1
status: Draft — first authoring pass
date: '2026-09-30'
source: pasted in chat 2026-09-30 (parent agent transcript, user message [t72u])
source_doc_id: null
owner: hades
export_date: '2026-09-30'
exported_via: verbatim copy of /workspace/staging/t72u text
transcription_notes:
- Runs of blank lines from the original paste were collapsed.
- Body below is the pasted text byte-for-byte; no Markdown markup was added (headings are plain lines).
- The Parent line links Google Doc 1c-HSBhxLY-z-A6xn_owLsi47HD10_sIa0FPHZqq0IB4 (Boundary Question Bank).
---

Domain Boundaries — user, admin, chat, AI (Draft v0.1)

Parent: Boundary Question Bank — Core Predicates (https://docs.google.com/document/d/1c-HSBhxLY-z-A6xn_owLsi47HD10_sIa0FPHZqq0IB4/edit). Status: Draft — first authoring pass. Owner: hades. Date: 2026-09-30.

Purpose: For each major boundary a non-technical operator names in plain words, this document gives the platform-aligned canonical label the system routes to, the lexicon aliases that resolve to it, the published curriculum or standard the questions are phrased from, and the boundary-specific yes/no predicates the 9B oracle answers when a new significant boundary of this kind is being planned. The core predicates in the parent document fire on every boundary; these fire in addition.

How to read a boundary

Canonical label is the label the lexicon groups under. Aliases are seed entries — the non-technical phrasings expected to resolve to the label; validate and extend them against the mined session corpus, and treat the inconclusive pile as the source of new aliases. Sources name the standard or curriculum each question is phrased from. Disambiguation lists the false friends that route elsewhere.

1. user → Identity and Access Management (IAM)

Aliases (seed): users, user accounts, accounts, login, log in, sign in, sign up, register, create an account, profiles, forgot password, reset password, remember me, Google login, log in with X, who's logged in, keep them logged in, verify their email.

Disambiguation: "users" in an analytics sentence (how many users, active users) is reporting, not IAM. "admin user" routes to boundary 2 for the privilege model and here for the credential. "user settings" splits: credential and session settings here, preferences to the product surface.

Sources: NIST SP 800-63-4 Digital Identity Guidelines, final July 2025 — 63A Identity Proofing and Enrollment, 63B Authentication and Authenticator Management, 63C Federation and Assertions; assurance levels IAL, AAL, FAL. OWASP ASVS 5.0.0 (May 2025) — V6 Authentication, V7 Session Management, V8 Authorization, V9 Self-contained Tokens, V10 OAuth and OIDC, V14 Data Protection, V16 Security Logging and Error Handling. NIST SP 800-53 Rev 5 — AC-2 Account Management, AC-7 Unsuccessful Logon Attempts, AC-12 Session Termination. CS2023 SEC; SE2014 SEC.

Canonical concept map: subject, identity proofing, enrollment, credential service provider, authenticator, authenticator assurance level, memorized secret, multi-factor, phishing-resistant authenticator, syncable authenticator (passkey), session, session token, re-authentication, federation, assertion, relying party, authorization, role, permission, account lifecycle.

1. Are identity (who the subject is), authentication (proving it), and authorization (what they may do) separated in the design? — Digital identity model (800-63-4); ASVS V6, V8
2. Is the authenticator type and its assurance level (AAL) chosen deliberately and documented? — Authenticator assurance level (800-63B-4)
3. Are memorized secrets stored with an approved hashing method and checked against known-compromised lists? — Password security (ASVS V6.2; 800-63B-4)
4. Is multi-factor or phishing-resistant authentication available where the risk requires it? — Multi-factor authentication (800-63B-4)
5. Are syncable authenticators (passkeys) supported or explicitly deferred with a reason? — Syncable authenticators (800-63B-4)
6. Is a new session token generated on authentication, with sufficient entropy? — Session token lifecycle (ASVS V7.2)
7. Are sessions invalidated on logout and bounded by idle and absolute timeouts? — Session logout and timeout (ASVS V7.3; AC-12)
8. Are cookie-based sessions set Secure, HttpOnly, and SameSite? — Cookie-based session management (ASVS V7.4)
9. Is re-authentication required before sensitive account changes (email, password, authenticator)? — Re-authentication (ASVS V6, V7)
10. Are unsuccessful login attempts limited and monitored? — Unsuccessful logon attempts (AC-7; ASVS V6)
11. Is account recovery treated as an authentication event with its own assurance, not a bypass? — Account recovery (800-63B-4)
12. Is the account lifecycle defined — creation, disable, removal, inactivity? — Account management (AC-2)
13. If federated login is used, are assertions validated and the FAL documented? — Federation and assertions (800-63C-4; ASVS V10)
14. Are self-contained tokens validated for signature, issuer, audience, and expiry? — Self-contained tokens (ASVS V9)
15. Is authorization enforced server-side at function, data, and field level? — Authorization (ASVS V8)
16. Are changes to the values authorization decisions depend on applied immediately? — Authorization (ASVS V8)
17. Is personal data in identity records minimized and its retention defined? — Data protection (ASVS V14; 800-63-4 privacy considerations)
18. Are authentication and authorization failures logged as security events? — Security logging (ASVS V16)

2. admin → Privileged Access and Administration

Aliases (seed): admin, admin panel, admin dashboard, control panel, back office, backend for me, manage users, super user, god mode, owner account, staff view, the place where I change stuff, settings for the whole app, moderation, ban a user, impersonate, log in as.

Disambiguation: "dashboard" alone is a product surface, not administration, unless it manages other users or system configuration. "backend" alone is ambiguous — server code, API, or admin UI; ask. "settings" for one user is boundary 1 or product; for the whole system it is here.

Sources: NIST SP 800-53 Rev 5 — AC-2 Account Management (AC-2(7) Privileged User Accounts, AC-2(9) Restrictions on Shared and Group Accounts), AC-3 Access Enforcement (AC-3(2) Dual Authorization, AC-3(7) Role-Based Access Control, AC-3(8) Revocation, AC-3(10) Audited Override, AC-3(13) Attribute-Based Access Control), AC-5 Separation of Duties, AC-6 Least Privilege (AC-6(2), AC-6(7) Review of User Privileges, AC-6(9) Log Use of Privileged Functions), AU Audit and Accountability family, CM Configuration Management family. OWASP ASVS 5.0.0 — V8 Authorization (administrative interfaces, multi-tenant), V13 Configuration, V16 Security Logging and Error Handling, V2 Validation and Business Logic. ANSI INCITS 359 Role Based Access Control.

Canonical concept map: privileged account, role, permission, role-based access control, attribute-based access control, separation of duties, least privilege, dual authorization, break-glass, audited override, audit record, audit trail protection, privilege review, revocation, tenant isolation, configuration item, controlled change, impersonation.

1. Is the administrative surface separated from the end-user surface (route, deployment, or process)? — Administrative interfaces (ASVS V8)
2. Are administrative roles defined explicitly with non-overlapping duties? — Role-based access control; separation of duties (AC-3(7), AC-5; INCITS 359)
3. Does each administrative role hold only the functions it needs? — Least privilege (AC-6)
4. Are privileged accounts distinct from the same person's ordinary account? — Privileged user accounts (AC-2(7), AC-6(2))
5. Is every privileged action audit-logged with actor, target, time, and outcome? — Log use of privileged functions (AC-6(9); AU)
6. Are audit records protected from modification by the administrators they record? — Audit protection (AU; ASVS V16)
7. Do destructive or irreversible administrative actions require confirmation or a second approver? — Dual authorization (AC-3(2))
8. Is there an audited break-glass or override path rather than an undocumented one? — Audited override (AC-3(10))
9. Are privileges reviewed periodically and is revocation applied immediately? — Review of user privileges; revocation (AC-6(7), AC-3(8); ASVS V8)
10. Are shared or group administrative accounts prohibited? — Shared and group accounts (AC-2(9))
11. In a multi-tenant system, is tenant isolation enforced on every administrative query? — Multi-tenant authorization (ASVS V8)
12. Is system configuration changed through a controlled, versioned path rather than live edits? — Configuration management (CM; ASVS V13)
13. Is impersonation ("log in as user") logged, consented where required, and time-bounded? — Privileged functions logging (AC-6(9); AU)
14. Are administrative sessions shorter-lived and re-authenticated for sensitive functions? — Session termination; re-authentication (AC-12; ASVS V7)
15. Do bulk operations carry scope and rate limits? — Business logic (ASVS V2)
16. Is content moderation separated from account administration as a distinct role? — Separation of duties (AC-5)

3. chat → Real-time Messaging

Aliases (seed): chat, messaging, messages, DMs, inbox, let users talk to each other, live chat, group chat, channels, rooms, threads, replies, comments in real time, typing dots, online status, read receipts, notifications when someone replies.

Disambiguation: "chat" combined with AI, bot, assistant, or "ask it" routes to boundary 4 with a conversational UI; this boundary is human-to-human messaging. "comments" without real-time expectation is a content feature, not messaging. "notifications" alone is its own boundary (queued for a later document).

Sources: CS2023 Parallel and Distributed Computing (PDC) — message-passing and shared-memory models, atomicity, consensus, conditional waiting, replicated state, fault tolerance; CS2023 Networking and Communication (NC) — reliable delivery protocols; CS2023 Data Management (DM). SWEBOK Software Design key issues — concurrency, distribution of components, data persistence, control and handling of events. OWASP ASVS 5.0.0 — V4 API and Web Service (V4.4 WebSocket), V17 WebRTC, V1 Encoding and Sanitization, V5 File Handling, V11 Cryptography. Reference protocols: WebSocket (RFC 6455), XMPP (RFC 6120, 6121), Matrix specification.

Canonical concept map: message-passing, delivery guarantee (at-most-once, at-least-once, effectively-once), idempotency key, ordering (sequence number, logical clock, causal order), acknowledgement, durability, replicated state, presence, ephemeral state, transport (WebSocket, server-sent events, long polling), reconnect and resume cursor, backpressure, fan-out, retention, moderation, end-to-end encryption.

1. Is the delivery guarantee (at-most-once, at-least-once, effectively-once) chosen and documented? — Reliable delivery (CS2023 NC, PDC)
2. Does every message carry a client-generated idempotency key so retries do not duplicate? — Idempotence under at-least-once delivery (PDC)
3. Is ordering within a conversation defined (sequence number or logical clock) and enforced on display? — Ordering; causal order (PDC)
4. Is a message durably persisted before it is acknowledged to the sender? — Atomicity; data persistence (PDC; SWEBOK)
5. Is the transport chosen deliberately (WebSocket, SSE, polling) with reconnect and resume from a last-seen cursor? — Reliable delivery; fault tolerance (NC, PDC)
6. Is the WebSocket connection authenticated, with the token re-validated on reconnect? — WebSocket authentication (ASVS V4.4)
7. Is authorization checked per message and per channel membership, not only at connect? — Authorization (ASVS V8)
8. Is presence (online, typing) modelled as ephemeral state separate from durable messages? — Replicated state (PDC)
9. Is backpressure or rate limiting applied per connection and per user? — Business logic limits (ASVS V2)
10. Is fan-out to group members bounded and asynchronous? — Distribution of components (SWEBOK)
11. Are retention, deletion, and "delete for everyone" semantics defined? — Data persistence (SWEBOK; DM)
12. Are attachments handled through the file-handling boundary rather than inline in the message model? — File handling (ASVS V5)
13. Is message content sanitized before rendering? — Encoding and sanitization (ASVS V1)
14. Is there a report and moderation path with an audit record? — Audit and accountability (AU; boundary 2)
15. If end-to-end encryption is claimed, is the key model documented and the server unable to read content? — Cryptography (ASVS V11)
16. Are offline delivery (queue while disconnected) and read-receipt semantics defined? — Fault tolerance (PDC)
17. Is the conversation model (one-to-one, group, channel, thread) chosen once and named canonically? — Data modelling (CS2023 DM)

4. AI → LLM Integration Layer

Aliases (seed): AI, the AI, the bot, assistant, add ChatGPT, add Claude, make it smart, AI feature, ask the AI, generate with AI, summarize this, auto-write, autocomplete, agent, let it do things for me, RAG, chat with my docs, train it on my data.

Disambiguation: "train it on my data" almost always means retrieval over the operator's documents, not fine-tuning — resolve to retrieval unless fine-tuning is explicitly justified (question 18). "chat" here is a conversational UI over the model, not boundary 3. "agent" means tool-calling with autonomy and pulls in the agency questions.

Sources: OWASP Top 10 for LLM Applications 2025 — LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data and Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector and Embedding Weaknesses, LLM09 Misinformation, LLM10 Unbounded Consumption. NIST AI RMF 1.0 — Govern, Map, Measure, Manage; NIST AI 600-1 Generative AI Profile. ISO/IEC 42001:2023 AI management system. CS2023 Artificial Intelligence (AI) knowledge area. SWEBOK Software Design — separation of interface and implementation (for the provider adapter).

Canonical concept map: model provider, adapter/gateway, system prompt, prompt template and version, context assembly, untrusted content, retrieval (RAG), embedding, vector store, tool calling, agency, human-in-the-loop, output handling, guardrail, evaluation set, regression, observability trace, token accounting, budget, data provenance, fine-tuning.

1. Is the model provider behind an adapter so the provider or model can change without touching callers? — Separation of interface and implementation (SWEBOK); Supply chain (LLM03)
2. Is untrusted content (user input, retrieved documents, tool output) kept distinct from instructions when the prompt is assembled? — Prompt injection, direct and indirect (LLM01)
3. Is model output treated as untrusted data before it is rendered, executed, or stored? — Improper output handling (LLM05)
4. Is the system prompt free of secrets and not relied on as a security control? — System prompt leakage (LLM07)
5. Are the tools the model can call minimal in functionality, permission, and autonomy? — Excessive agency (LLM06)
6. Do consequential actions require human confirmation before execution? — Excessive agency (LLM06); Manage (AI RMF)
7. Is sensitive data filtered before it enters the prompt and before output is returned? — Sensitive information disclosure (LLM02)
8. Are retrieval sources access-controlled so a user cannot retrieve documents they may not read? — Vector and embedding weaknesses (LLM08)
9. Are token, request, and cost budgets enforced per user and per tenant? — Unbounded consumption (LLM10)
10. Are prompts versioned and tested against an evaluation set before release? — Measure (AI RMF)
11. Is there a regression harness with defined quality metrics? — Measure (AI RMF)
12. Are model, provider, and prompt version recorded per request? — Govern; traceability (AI RMF; ISO/IEC 42001)
13. Is there a fallback or degraded mode when the provider fails or times out? — Fault tolerance (SWEBOK)
14. Is training or fine-tuning data provenance recorded and separated from user data? — Data and model poisoning (LLM04)
15. Is AI-generated output labelled where required, with known limitations disclosed? — Misinformation (LLM09); Map (AI RMF)
16. Are third-party models, plugins, and embedding models pinned and verified? — Supply chain (LLM03)
17. Are retention and secondary use of prompts and completions defined and disclosed? — Data governance (ISO/IEC 42001)
18. Does "train it on my data" resolve to retrieval unless fine-tuning is explicitly justified? — Lexicon disambiguation rule

Cross-boundary dependencies

- admin depends on user: every administrative role is an authorization decision over an authenticated subject.
- chat depends on user (authenticated connections) and admin (moderation and audit).
- AI depends on user (per-user budgets, access-controlled retrieval) and admin (prompt and budget configuration is privileged).

Queued boundaries (next documents)

billing and payments; notifications; files and media; search; analytics and reporting; settings and preferences; onboarding.

Open items

- Validate seed aliases against the mined session corpus; promote inconclusive-pile phrasings that resolve here.
- Add requirement identifiers (ASVS 5.0.0 section numbers, 800-63B-4 section numbers) as a citation column once the harness exists.
- Decide which questions gate others within each boundary.
