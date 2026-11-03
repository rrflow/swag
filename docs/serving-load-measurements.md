# Serving-load measurements

`tools/swag_serving_load.py` runs an explicitly bounded load sweep on the Linux
serving host. It is an offline measurement tool, not an RRFlow job scheduler,
training launcher or model-quality evaluator. It leaves serving containers and
their configuration unchanged. Runtime-profile changes require a separate owned
experiment with restoration and retained evidence.

## Inputs and execution

Use a private JSON configuration containing all fields below. There are no default
models, credentials, workloads or resource budgets:

- `baseUrl`: loopback HTTP origin or `/v1` base; `model`: configured serving alias.
- `credentialFile`, `credentialVariable`: existing local credential reference.
- `container`: exact Docker container to observe; `artifactManifest`: declared
  checkpoint manifest matching the alias. This is not loaded-weight attestation.
- `workloadFile`: JSONL with `id`, `sourceReference`, `sourceSha256`, and `messages`.
  Only system/user messages are accepted; expected labels and assistant targets
  are rejected. Preserve real source provenance. Repeated load requests are not
  additional independent task-quality observations.
- `concurrency`: distinct client concurrency values; `rounds`: repetitions of the
  workload; `maxTokens` and `temperature`: generation settings.
- `requestTimeoutSeconds`, `maximumDurationSeconds`, `sampleIntervalSeconds`,
  `minimumAvailableBytes`, `maximumTemperatureC`: explicit operational bounds.

```bash
python3 tools/swag_serving_load.py --config private-config.json --output-dir fresh-results
```

The duration limits new dispatch; in-flight requests can take their socket timeout
to finish. A host process supervisor should also bound the entire experiment.
Low available memory, high/unavailable temperature, container replacement/restart
or telemetry failure stops new dispatch. Failure and undispatched counts remain
visible. Requests use no redirects or environment proxies. Credentials and endpoint
URLs are excluded from the retained protocol. Keep raw workloads and responses
private according to their source permissions.

## Evidence and interpretation

`protocol.json` binds workload, declared artifact, implementation and configuration
digests. `requests.jsonl` retains provider-reported usage, output, errors and elapsed
time. `samples.jsonl` records container/image identity, runtime settings, GPU
activity, process counters and host availability. `summary.json` is written only
after the run and sampler finish; it binds both streams and reports phase latency
and throughput. Partial directories remain incomplete evidence.

Recompute a content-free report, optionally pairing the same workload against a
different runtime profile:

```bash
python3 tools/swag_serving_report.py --baseline baseline-results --candidate candidate-results --output comparison.json
```

The report checks retained hashes, planned request identities, process continuity,
phase counts and latency statistics. Paired profiles must share the workload,
artifact, runtime image, load-runner implementation and generation settings.
Output agreement is reported independently from correctness; it cannot qualify a
model or establish general performance equivalence. The phase wall-clock duration
remains a retained runner observation rather than an independently timed trace.

Client concurrency is not server batch capacity. Record `max-num-seqs`, context,
cache allocation and eager/graph mode. A one-sequence server can show longer queues
without increasing throughput as clients increase. Short, repeated title inputs
do not establish long-context capacity or general development-task performance.

NVIDIA documents that Spark uses unified CPU/GPU memory and that device-level
`nvidia-smi` memory usage can be unsupported while per-process counters remain
available. Its memory-reporting guidance also explains swap/reclamation effects.
[NVIDIA Spark known issues](https://docs.nvidia.com/dgx/dgx-spark/known-issues.html)

Host RSS, cgroup memory, per-process GPU memory and host availability overlap or
cover different scopes. This tool never adds them into a supposed total.
`totalServingBytes` remains null and `totalServingMemoryVerified` remains false.
These measurements cannot alone pass the 29/15/9 GB qualification gate.

## Spark BF16 experiment, 3 November 2026 UTC

The first run used 21 real, previously exposed Connectome PR titles without their
provisional labels, repeated three times at each client concurrency. The custom
BF16 endpoint completed 189/189 requests and every response matched the requested
JSON shape. This establishes response-contract and serving-load observations only;
classification correctness was not scored and no training was performed.

At server capacity one sequence, measured throughput stayed near 1.4 requests/s.
Client-concurrency 1/2/4 produced p95 latencies of approximately 0.77/1.48/2.91 s.
The selected GPU reached 96% sampled utilization and 67 C. Its largest owned
process GPU-memory counter reached 62,995,300,352 bytes, while the cgroup counter
peaked near 3.29 GB. The difference illustrates why cgroup usage alone cannot be
advertised as this model's footprint. Total serving memory remains unverified.

The paired four-sequence run also completed 189/189 requests without errors.
The declared checkpoint, runtime image, workload and generation settings matched;
the recorded runtime configurations differed only in `max-num-seqs` (1 versus 4).
Recomputed observations are in [the content-free report](evidence/serving-load-20261103.json).

| Client concurrency | One sequence: requests/s | Four sequences: requests/s | One sequence: p95 s | Four sequences: p95 s |
| --- | --- | --- | --- | --- |
| 1 | 1.37 | 1.26 | 0.77 | 0.81 |
| 2 | 1.40 | 2.17 | 1.48 | 0.98 |
| 4 | 1.40 | 3.82 | 2.91 | 1.11 |

All 189 paired parsed JSON outputs agreed. These are repeated, previously exposed
inputs, not independent correctness labels or frozen unseen acceptance tasks.
This single ordered sweep supports further batching evaluation; it does not
establish general quality equivalence or a statistically reliable speedup.
Single-client throughput declined and its p99 rose from 0.82 to 3.06 seconds;
no observations were discarded as warmup. Four-sequence sampling reached 96%
GPU utilization, 67 C and a 62,993,203,200-byte owned-process GPU counter.

The first four-sequence startup failed its 300-second readiness deadline. Its
failure and successful restoration were retained. The retry used a 1,200-second
startup allowance; the loader reported 374.6 seconds for checkpoint loading.
The request timeout and load bounds were unchanged. The experiment supervisor
finished successfully and restored the original container/image and one-sequence
configuration. Independent readback at 03:23:25 UTC verified the candidate stopped
and one authenticated inference request succeeded against the restored endpoint.
The candidate is not promoted; raw restoration and failure evidence stays private.
