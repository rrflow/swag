# Custom BF16 checkpoint binding observation

Observed 31 October 2026, 21:59–22:00 UTC. This is a read-only operator audit
of the existing experiment; it is not model qualification or a new deployment.

The running container retained its ID, image, PID, start time and configuration
through the audit. It mounts `merged-intent-bf16` read-only at `/model`, selects
that directory with BF16, and serves `swag-qwen3-coder-intent-20261028`. Its
creation manifest SHA256 remains
`ba7bede9963d469f312e06b337cb9241de524bdf77c7fe2ee30e09dd9b126252`.

All 26 manifest entries matched their recorded sizes and SHA256 hashes. The
16 weight shards contain 18,867 BF16 tensors and **30,532,122,624 stored tensor
elements**. Header shapes, byte ranges and complete shard/index mapping agree;
each file's metadata stayed unchanged during its read. The inspection follows
the [Safetensors format](https://github.com/safetensors/safetensors#format), reads
with an 8 MiB hash buffer, and does not load another model or allocate GPU memory.

| Observation or calculation | Bytes |
|---|---:|
| Current BF16 weight files, including headers | 61,066,575,648 |
| Tensor payload alone | 61,064,245,248 |
| Ideal packed 9-bit payload: elements × 9 ÷ 8 | 34,348,637,952 |
| Later total-serving target | 29,000,000,000 |

Plain 9-bit storage exceeds the target before cache, runtime and quantization
metadata. Compression choice remains gated on quality comparison and measured
total serving memory; these file measurements do not establish serving RSS.

Authenticated health/model discovery returned 200, unauthenticated model discovery
returned 401, and the endpoint reported zero running/waiting requests. The
existing SSH listener maps to the same host/container port. No provider generation,
training, restart, configuration change or promotion occurred. The manifest still
marks the experiment unqualified; its earlier assistant-inferred training labels
remain provisional.

The raw receipt (`.swag/evidence/20261031/custom-weight-binding/receipt.json`)
has SHA256 `c357399a54af8f6fc4d88446db0f044fcfb235d529920eab16fab3225e04f560`.
Adjacent scripts, command/log digests, discovery and forwarding observations
retain the method and outputs. Credential scanning passed. These local ignored
artifacts are not shipped with a checkout. This binds observed disk contents and
deployment configuration; it does not independently attest in-memory GPU tensors
or retroactively attach a weight attestation to earlier trials.
