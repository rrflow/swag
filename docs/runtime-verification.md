# Runtime verification, 2 November 2026

These observations concern the retained provisional custom BF16 experiment on
`spark-02`. They are not a new training run or a qualified router release.
Private raw receipts and access configuration remain outside the tracked tree.

## Artifact bytes

At `2026-11-02T18:28:35.392255+00:00`, the streaming verifier checked all 26
declared files against the retained manifest. Total verified bytes were
61,084,160,920; weight files contributed **61,066,575,648 bytes (61.07 GB)**.
The manifest SHA-256 is
`ba7bede9963d469f312e06b337cb9241de524bdf77c7fe2ee30e09dd9b126252`.
Verification used an 80,000,000,000-byte budget and a 4,096-file ceiling.

This is file integrity evidence, not tensor semantic validation, loaded-weight
attestation or serving memory. The UI matches the retained receipt to its
manifest; it does not rehash remote weights on refresh. The 29 GB serving target
has not been demonstrated.

## GPU and discovery

The existing training image
`sha256:b65306df26ee7d0eb95968b64174de864ee7ec1d34e9a7a78eeb017489148b84`
ran the current trainer's `--preflight` in an ephemeral container with networking
disabled. Unsloth imported, required packages were present, CUDA was available,
and the real CUDA operation passed on NVIDIA GB10. The device reported
130,594,062,336 memory bytes; that is device capacity, not model memory usage.

The existing serving image is
`sha256:654e563e727be1968487d453de0733fb074cb59adf424c779d0f9e7cfcb2b6b6`.
At `2026-11-02T18:31:34.162580+00:00`, `/v1/models` returned HTTP 401 without
credentials and HTTP 200 with credentials, listing
`swag-qwen3-coder-intent-20261028`. The local forward was restored. Discovery
does not prove which bytes the running process loaded. No inference or serving
restart was performed in these artifact and discovery checks.

## Subsequent proposal and correlation trial

A separate [real work-item trial](model-outcome-correlation.md) subsequently
performed one accepted BF16 proposal and delivered its terminal-attempt metadata
to the actual native RROFLOW receiver. Exact task/attempt/configuration/response
correlation and readback survived process restart; delivery replay retained one
event. The capture remains unreviewed with training consent disabled. This is
bounded candidate evidence, not model qualification or a completed UI workflow.

## Remaining acceptance

The historical checkpoint includes optimizer, scheduler and RNG files, but
full resume and new cooperative-stop behavior still require authorized GPU
execution and engine recovery evidence. Independently reviewed routing labels
remain required for new admitted training. Baseline/custom-BF16/quantized
qualification, measured serving footprint, Connectome embedding and deployment
acceptance for complete RROFLOW trace delivery remain open. Follow the
[training-control plan](training-control-plan.md).
