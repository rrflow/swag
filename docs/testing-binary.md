# Testing the native controller binary

## Latest project-plan preview

The latest frozen candidate is
`.swag/controller-ui/1f2e2a5c/connectome.exe`, alongside its
matching `.swag/controller-ui/1f2e2a5c/rrflow.exe` and
build receipt (`.swag/controller-ui/1f2e2a5c/build-receipt.json`).
Clean UI source is `1f2e2a5c96edf7b783297e0f960abed1be9aa955`; engine source is
`8d47500869329f1a5604821138f1a6c8efc349a5`. The executable hashes were rechecked.

- UI: 53,824,000 bytes; SHA256 `abf4a6744bd40e4f001a8d4f052edd9f457aed55ff12ff52faf660c5b9d7102a`.
- Engine: 154,188,288 bytes; SHA256 `4a8ac57f1766b9c06e6816bc820ef027c4dbbfd1b90d408b1c563dfcf6a591f7`.

This adds the Project plan panel. Three actual installed-process scenarios pass;
desktop discovery and first source replan preview were observed. The remaining
desktop trial is incomplete after the target window became unavailable. This is
an unsigned, unoptimized preview, excludes weights, and retains preview UI data.
It is not a turnkey public package. See [release gates](deployment-readiness.md).
Older artifacts and their historical evidence below remain separate.

## Installed-job discovery engine candidate

The new standalone `.swag/evidence/20261031/attunement-job-discovery/rrflow.exe`
is built from clean public PR231 source `8d47500869329f1a5604821138f1a6c8efc349a5`.
It is 154,188,288 bytes; SHA256
`4a8ac57f1766b9c06e6816bc820ef027c4dbbfd1b90d408b1c563dfcf6a591f7`.
The frozen build receipt (`.swag/evidence/20261031/attunement-job-discovery/engine-frozen.json`)
binds its canonical two-pass build, exact clean source and copied-binary version
report. It adds public installed-job discovery needed by the next Connectome
source-replanning package. Existing UI bundles below remain unchanged.

This is an unsigned, unoptimized engineering binary that excludes model weights.
Installed-engine and HTTP component tests pass; an actual installed-primary/UI
discovery trial is still pending. Build provenance is not clean-machine,
update/rollback, model-quality or public-release qualification. Keep its receipt
with the executable; do not substitute it into an older paired bundle's receipt.

## Latest desktop recovery preview

The newest source-bound desktop preview is
`.swag/controller-ui/0f75c015/connectome.exe`, with its matching
`.swag/controller-ui/0f75c015/rrflow.exe` and
build receipt (`.swag/controller-ui/0f75c015/build-receipt.json`).
UI source is `0f75c015`; engine source is `6a4cbb04`.

- UI: 52,248,064 bytes; SHA256 `1cdee435a65acaa92dedabccfd50e4555c210cdfa5be241465a41453ca4ef926`.
- Engine: 154,068,480 bytes; SHA256 `d4cc99d8527b97ba145023e0b1cc4a7c26a0682f6edc8c2d5d8d9ff1ad4ffec0`.

This exact Windows build completed a real BF16 proposal, UI Stop/resume,
explicit worker request and reload/readback. Original budget/deadline and both
attempts were preserved, with two total steps and 22,528 ms charged.
[Evidence and limitations](https://github.com/rrflow/connectome-development/blob/59526643f0a6d7ae8ef04d1858d988af6d6e1efd/docs/controller-task-recovery-desktop.md)
include the rejected oversized input and subsequent source projection.

This is an unsigned, unoptimized engineering preview with separately configured
model serving. Its owned trial server is stopped; the retained connection is not
a running deployment. It has not passed clean-machine installation, update or
public-release qualification. It does not execute project-file changes. Keep
the matching build receipt and engine together; older bundles below remain
unchanged and do not inherit these capabilities.

## Earlier engine and bundle artifacts

The newest **recovery engineering candidate** is
`.swag/evidence/20261031/task-budget-resume/rrflow.exe`, with its
build receipt (`.swag/evidence/20261031/task-budget-resume/engine-frozen.json`).
It is 154,068,480 bytes, from clean source
`6a4cbb042a13f5a7c41b53d11d62b54a85df3bed` in draft PR230; SHA256
`d4cc99d8527b97ba145023e0b1cc4a7c26a0682f6edc8c2d5d8d9ff1ad4ffec0`.
The canonical builder captured/reproduced its compilation inputs and verified
the frozen copy's version, digest and clean source identity. It adds explicit
`task-budget-resume` for safely completed stopped work without resetting effort
or deadlines. Unknown/active work is denied. Component and authenticated HTTP
checks pass. Its actual installed same-task BF16 recovery trial now passes:
real terminal rejection, explicit resume without resetting effort/deadline,
fresh accepted selection and worker, then exact credential-free reopen and
independent readback. Exactly four actual provider calls occurred; recovery
requested none. See [published receipts](https://github.com/rrflow/rrflow-development/blob/67c197ea2dd60d597e18cc37e1b57d33c45d67cb/docs/evidence/change-journals/gate-g/task-budget-resume-live.md).
This demonstrates controlled recovery, not routing quality or project execution.
This unsigned, unoptimized executable excludes model weights and is separate
from the ZIP and Connectome preview below. Their older binaries are unchanged.

The current Windows x64 engineering bundle (`files/distributions/rrflow-controller-trial-windows-x64-8cf235ac.zip`)
is available locally: **33,976,833-byte ZIP**, containing a **114,013,696-byte primary executable**.
It is unsigned and unqualified. Model weights remain on the separately configured
endpoint; these download sizes are not the LLM's serving footprint.

Its engine and assembly source is `8cf235ac06a92bc16ae74e746ff1928fb8415b47`.
Retained checks cover archive integrity and same-host installation, serving,
restart and quick verification with only System32 on the child PATH. Those checks
did not invoke a model or worker. The newer `9e167aad` engine/SDK test executable
is a separate unoptimized artifact; it is not contained in this ZIP. See
[current context](current-context.md) for subsequent source changes.

## Verify and start

A newer completion-repair candidate is frozen at
`.swag/evidence/20261031/worker-terminal-response/rrflow.exe`, with adjacent
`engine-frozen.json`. It is 154,011,648 bytes, built from clean `75c26a80`, SHA256
`c9f481103d6ba2a2cf1e0b42e386b084d92530bc42375b0039c7cf6722243636`.
The actual installed BF16 baseline, rejected-completion/capacity trial and
independent readback passed on this exact executable. The rejected worker keeps
its stopped budget and spent effort; another real task can use the binding after
reopen. This does not resume the original task. It is an unsigned,
unoptimized engineering artifact, separate from both the ZIP and desktop preview.
Existing uncertain estates must not be cleared or retried using this artifact.

For the newer worker trial, a separate provenance-bound engineering executable
is available at
`.swag/evidence/20261030/engine-source-inventory/task-worker-admission-provenance-rrflow.exe`.
It is **153,999,360 bytes**, built from clean `c75c1896`, with SHA256
`60a708117899a022b04818c096af17a925c60eae06c554c39d00e5fe09e028fa`.
The adjacent `task-worker-admission-provenance-frozen.json` records its build.
This unsigned, unoptimized standalone artifact passed an actual configured
selection/worker draft, missing-credential denial, restart/readback and replay
trial. It is not the ZIP below, a qualified release or a complete UI/project
workflow. The first rejected selector trial is retained separately; see
[current context](current-context.md) for exact results and limits.

A subsequent trial exercised that engine through the Rust SDK built at
`43d18059`. Its engineering example is
`.swag/evidence/20261031/worker-native-client/task_model_call.exe`
(SHA256 `06a8b717ffae2cdce3a2af44eabcccefc7f07e6ec17064fc55b2d1ba5ad1862f`).
It requires explicit engine-operation, installed-project, loopback-address,
request-JSON and timeout arguments; it is not the Connectome UI or a release
installer. Accepted and rejected actual native trials are separately retained
in [PR229's evidence](https://github.com/rrflow/rrflow-development/blob/a3068cf67e3c7afbd75a01ac85662d5afd244483/docs/evidence/change-journals/gate-g/task-worker-native-live.md).

From the SWAG repository, verify the ZIP:

```powershell
Get-FileHash .\files\distributions\rrflow-controller-trial-windows-x64-8cf235ac.zip -Algorithm SHA256
```

Expected SHA256:
`8fc7a5056bde73f29ffb435393d6254cac152ff0f30aea4158e597fb9749f9a3`

Extract into a new directory and inspect the executable:

```powershell
Expand-Archive -LiteralPath .\files\distributions\rrflow-controller-trial-windows-x64-8cf235ac.zip -DestinationPath .\swag-controller-trial
.\swag-controller-trial\rrflow.exe --json version
```

Follow `README.txt` inside the bundle to preview and apply installation to an
empty project, start the engine, check authenticated readiness and verify it.
The primary executable requires no Python, Rust compiler or source checkout.
It chooses a free loopback port; `ready` returns the discovery endpoints.

The optional controller trial tool requires Python 3.11+, an explicit endpoint
profile, an actual task and a private credential file. None is preselected or
embedded in the ZIP. Its runbook includes the exact arguments and credential-free
recovery command. Preserve failed estates and receipts.

## Earlier live endpoint trial

The following observations belong to the retained
54fb845d bundle (`files/distributions/rrflow-controller-trial-windows-x64-54fb845d.zip`),
whose archive SHA256 is
`46b85f824d712cd8e8cceda4a6b0cd01bb1585f3f25a1f8c64ef8b7657f05b6f`.
They do not qualify the newer bundle automatically.

- Eighteen archive integrity/rejection checks passed, including corrupted copies
  of this exact artifact. All relocated file hashes matched.
- The packaged release binary completed a real BF16 proposal, retained identical
  state after restart and rejected replay. Primary readiness and quick verification
  also passed with no provider credentials and only System32 on the child PATH.
- Session closure, Stop and lost-response checks passed with restart readback.
- The configuration-change case exposed a model error: its fresh response chose
  unsupported effort `observed`. The engine rejected it with HTTP 412; recovery
  preserved two spent steps and stopped/uncertain capacity. That case failed.

This is suitable for controlled engineering testing. The profile had one
candidate, so these results do not establish routing quality. The checkpoint
remains provisional; no new training or review consent was inferred.

Engine source: `54fb845dffd702e1504c7f9a0cc2a3c5757d2bf2`. Assembly source:
`98d0de932fecce1a3103c31cb9bab75712a62d48`. The manifest records exact identities.
[PR206](https://github.com/rrflow/rrflow-development/pull/206) and
[draft PR212](https://github.com/rrflow/rrflow-development/pull/212) still require
protected landing. PR206 is now ready at `9371f856`, with candidate run
`41235940488` active; PR212 remains draft. Neither has landed. The older
trial stays bound to the source above. Container delivery, complete connected
workflow, worker execution, model qualification and automatic learning remain
open. Source-edit recovery has newer engine evidence in
[current context](current-context.md); that evidence belongs to its named builds.

## Native desktop preview

The newer selected-worker preview is at
`.swag/controller-ui/95a81077/connectome.exe`, alongside its exact `rrflow.exe`
and `build-receipt.json`. Keep these files together. Connectome source is
`95a81077d89efb5cd14e14bcbdecbc9bfa76d872` in draft
[PR28](https://github.com/rrflow/connectome-development/pull/28); engine source
is `e35283303f4c5823c612686d32fb6bee1ac368ac`. The UI executable is 52,200,960
bytes, SHA256 `5c054ce8d4775bd7d1aa4cb825b181c4bab6bbe586fe2f1a397c3c406d35234f`.
The engine is 154,010,112 bytes, SHA256
`8c323716f02e210ebc211bf4593dde84b03d1b55d50f62e710676cda5a971da0`.
These sizes exclude remotely served model weights.

This unsigned development build adds selected-worker review, an explicit draft
request and retained worker readback. Its actual BF16 desktop trial passed task
creation, one selection, one worker draft, reload and readback. Independent engine
reads found exact task, budget and attempt equality, with two steps spent and no
automatic redispatch. [Source-bound evidence](https://github.com/rrflow/connectome-development/blob/91b89ae46ac23af70c852c79559bc59ecd62eed5/docs/controller-worker-desktop-live.md)
includes screenshots and receipts with original capture hashes. All six CI jobs
passed at `95a81077`; corrected evidence head `91b89ae4` also passed all six jobs
in `41235205588`. Its preceding JSON-formatting failure is retained; the correction
preserves JSON values and these frozen executables. This one-candidate trial does not
qualify routing quality. It requires the desktop WebView runtime and configured
engine/provider access, supplied through an externally managed engine in this trial.
Build mode uses the preview data directory. This is not a signed installer,
clean-machine qualification, complete project-execution workflow or public
release. The older observed desktop trial below remains bound to its old build.

A separate local Windows preview is available at
`.swag/controller-ui/d7eb6ea3/connectome.exe`, alongside its `rrflow.exe` sidecar
and `build-receipt.json`. Keep those files together. It comes from draft
[Connectome PR26](https://github.com/rrflow/connectome-development/pull/26),
implementation `d7eb6ea3027b76e1afd515715ab4958e66083060`, using engine
`61ddb26416811ba7e56edf2e28b8cef3acad5930`. It is a development build and requires
the desktop runtime; no clean-machine or signed-installer claim applies.

The actual desktop trial passed fresh installation, task creation, explicit
budget configuration, reload/readback and Stop. A missing endpoint profile was
shown as unavailable and did not dispatch inference. The retained trial estate
is cancelled; preserve it as evidence. A separate fresh estate subsequently
completed one explicit BF16 proposal through the desktop and recovered the same
accepted receipt after webview reload, with one spent step. Its actual receipts
and screenshots are in PR26's `docs/controller-desktop-live-trial.md`. This used
an externally started engine with an operator-supplied credential mapping; the
one-click launcher does not yet perform that setup. These executable sizes
exclude remotely served model weights.
