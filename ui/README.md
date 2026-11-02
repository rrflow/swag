# SWAG controller evidence viewer

TypeScript evidence viewer and local label-review workspace displaying retained
BF16 development runs. The evidence dashboard is read-only; the review page
authors downloadable exchange files without server-side state or uploads.
The bundled snapshot is **7/13 matched, five eligibility violations**; it is not
a live feed, trained checkpoint, Connectome integration or production qualification.

```powershell
cd ui
npm ci
npm run build
npm run dev
```

Open `http://127.0.0.1:8891` for saved evidence or `/dev.html` for the
[developer workspace](../docs/developer-workspace.md). The loopback Node server
also exposes `GET /api/dev/status`, invoking the configured Python interpreter
to read local traces/artifacts and optionally authenticate with RRFlow for
diagnostics. There are no training or project mutation endpoints. Import another `evidence.json` locally;
the browser validates its shape and count consistency without uploading it.
The dashboard exports exclude prompts, raw responses, credentials and original
case titles. The separate review packet includes public task titles and retained
model outputs so a reviewer can inspect them; it contains no credentials.
The browser does not authenticate provenance or attest a running model.

Generate an export from a completed evaluation, from the repository root:

```powershell
python tools/swag_evidence_projection.py --run-dir .swag/evidence/20261028/routing-development-baseline --output-dir .swag/exports/another-run
```

The exporter verifies source hashes, identities, case scores and aggregate metrics.
It writes `evidence.json` and a local `rroflow.turn/v1` report record. The latter
is not uploaded, and the older preview publisher does not support this event.
`tools/swag_signal_sink.py` separately performed authenticated local ingest, duplicate
retry and exact readback against the actual Rust service. The UI does not publish
events. Hosted RROFLOW and engine integration remain pending.

The bundled comparison also shows Liquid d1-3B: 9/13, three policy violations,
about 92 ms warm median. Both runs use the same development cases; different
runtimes and d1's typed API limit direct performance comparisons.

The comparison now includes the actual custom BF16 checkpoint: 7/13 routing
cases, five violations. A separate intent table shows original Qwen 14/21,
custom Qwen 15/21, d1 10/21 and a majority-label rule 14/21, with balanced
accuracy so minor classes remain visible. These labels are assistant-inferred;
the one-task gain does not establish production reliability.

A fifth row now reports the fixed CPU multinomial Naive Bayes baseline:
12/21 and 34.5% balanced accuracy. It was trained on the same 44 training titles,
saved/reloaded and evaluated without development-set tuning. Its 5,361-byte
artifact does not match the custom Qwen's measured quality. The retained
three-model review packet stays unchanged.

```powershell
npm test
npx playwright test
```

The browser test checks actual saved data, filtering, rejected imports and mobile
layout. Its screenshots go to the root `.swag/evidence/20261028/` directory.

This is a rendering reference for a future Connectome public-SDK view. No engine
state, training routine or provider credentials belong in this UI. See the
[architecture and research decision](../docs/decision-router-research.md).

## Review the real task labels

Open `http://127.0.0.1:8891/review.html`. The shipped local packet has 21 tasks
and 63 retained outputs; its exact SHA-256 is checked before rendering. Inspect
the source PR, enter your reviewer identity and choose accept, correct or exclude.
Every finalized decision needs a rationale and evidence reference. Identities
are declarations, not authenticated identities; do not claim a human review
when an assistant made the decisions.

Download a draft to save progress, then use **Resume saved review**. The server
does not store your work. Unsaved edits trigger a navigation warning. A stale
review cannot be imported into a different packet. **Export completed review**
becomes available only when all tasks have complete decisions. No training
consent is inferred and no training process starts.

Validate the downloaded file from the RRFlow PR180 checkout (depends on PR179):

```powershell
python scripts/inference/review_decisions.py --manifest $SWAG_CHECKOUT/.swag/evidence/20261028/engine-outcome-review/export/manifest.json --packet $SWAG_CHECKOUT/.swag/evidence/20261028/engine-outcome-review/packets/e54bfeeef61fef3cd0e31f00d4c45460ce67336badf51138692102fa99d34bb6.json --reviews YOUR_DOWNLOADED_REVIEW.json --output-dir reviewed
```

The validator reconstructs the packet from original files and writes immutable
review evidence. This is a working local file-exchange workflow, not a landed
Connectome/engine runtime integration. The data remains development-only; it
cannot be relabelled as an untouched acceptance set.

## Native configuration snapshot

The dashboard also describes the 28 October native RRFlow endpoint configuration
experiment. This is a saved, local test result. Authenticated configuration,
restart readback, revocation and stale-plan rejection passed; engine-dispatched
model calls and credential resolution are not implemented. The engine test
processes were stopped. See `../docs/experiment-evidence.md` for retained receipts.
