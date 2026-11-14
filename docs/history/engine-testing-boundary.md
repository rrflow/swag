# RRFlow engine testing boundary (from the README, November 2026)

> **Historical record.** Kept as evidence of what was planned, decided or measured at the time. It is not current instructions; see the [System One plan](../system-one-plan.md) and the [docs index](../index.md).

[PR206](https://github.com/rrflow/rrflow-development/pull/206) implements the
engine-owned experimental proposal operation. A source-identified Windows
development executable made real BF16 calls and passed restart, replay rejection,
configuration replacement, session closure, Stop and lost-response checks.
The profile had one candidate; this proves transport and admission behavior,
not provider selection quality, worker execution or ordinary-edit replanning.
Earlier protected merging failed during macOS APFS image creation (`Resource
busy`); that failure is retained. PR206 subsequently merged as `5b4039fe`, with
successful protected checks. See [deployment readiness](../reference/deployment-readiness.md)
for the remaining release gates and [current context](current-context.md)
for exact build identities.

[Merged PR222](https://github.com/rrflow/rrflow-development/pull/222) adds the
catalogue-derived Rust client proposal binding needed by Connectome. Its native
example completed a real BF16 proposal with identical restart readback and replay
denial. Connectome draft PR30 now contains the proposal/recovery and plan-panel
integration, with passing candidate CI. Its dependencies and complete real-task
acceptance remain open; this is not a released controller.

The [native Windows engineering bundle](../evidence/testing-binary.md) is now available
locally: a 33.9 MB ZIP with the optimized primary executable, provenance, verifier
and trial instructions. Actual relocation, proposal/reopen/replay and three fault
cases passed. A configuration-change trial also exposed an invalid model effort
choice, which the engine rejected; that failure is retained. The model remains
unqualified. [Merged PR212](https://github.com/rrflow/rrflow-development/pull/212)
provides the packaging tooling; signed releases, container deployment and the
complete Connectome workflow remain open. See [current context](current-context.md).
