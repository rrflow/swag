# Training and placement operations

These tools prepare, place and inspect training work. None of them is on the decision path, and the retired pipeline jobs still refuse to run. See the [System One plan](../system-one-plan.md), workstream W6, for the model work they serve.

The following older templates are not the active BF16 launch configuration.
Topology and tier settings must be verified before use. SWAG includes a template
for a 3-node Spark GB10-style topology
(384GB unified memory total) and a model catalog template for tier benchmarking.

- [config/training/spark_cluster_profile.template.yaml](../../config/training/spark_cluster_profile.template.yaml)
- [config/training/model_catalog.template.yaml](../../config/training/model_catalog.template.yaml)
- [config/training/tier_metrics.template.json](../../config/training/tier_metrics.template.json)

Use these with the experiment harness to generate execution plans that include:

- provider/key routing plan
- model-tier candidate families (Qwen, Phi, and additional baselines)
- cluster metadata and training defaults for runbook generation
- Historical tier labels: 14B, 7B and 27-28B; not the active BF16 experiment

```powershell
python tools\controller_model_experiment.py --pretty `
  --model-catalog config\training\model_catalog.template.yaml `
  --cluster-profile config\training\spark_cluster_profile.template.yaml `
  --tier-metrics-file config\training\tier_metrics.template.json `
  --emit-promotion-scorecard
```

## Reviewed training and historical scaffolds

New training uses independently reviewed real observations admitted by
`tools/swag_routing_dataset.py`. Invoke `tools/swag_unsloth_train.py` explicitly
with that export's `--admitted-dataset-dir`, exact train/development files, an
explicit `--seed`, and the chosen model/runtime settings. See the
[admission and evaluation guide](routing-data-and-evaluation.md).
Acceptance data must not enter training. Human review, consent and real outcome
evidence are still required; no new dataset is approved by this documentation.

The former synthetic dataset/runbook generator, raw-dataset LoRA trainer and
runbook execution path are retired. They refuse before creating data, importing
GPU libraries or launching commands. The legacy operations UI cannot run that
pipeline. Existing datasets, manifests and runbooks remain historical artifacts;
none are relabelled or deleted. `tools/run_training_job.py --list-steps` and
command printing remain available for inspection, but `--execute` is refused.

## Quality-of-life local UI

The legacy local operations UI supports historical artifact inspection and:

- an explicitly disabled retired training pipeline
- dataset quality run
- experiment generation run
- live job status and latest manifest/quality summaries
- human-in-the-loop dataset review queue (approve/reject/pending with edits and reason tags)
- historical curated exports, which do not satisfy reviewed-data admission

```powershell
python tools\swag_ops_ui.py --host 127.0.0.1 --port 8790
```

Then open: `http://127.0.0.1:8790/`

Reviewer artifacts are generated locally and are not distributed:

- `files/training/data/review_state.json`
- `files/training/data/controller_sft.curated.jsonl`
- `files/training/data/controller_sft.curated.report.json`

## DABO + ring placement planning

Placement is now policy-driven and explicit in code:

- [topology.template.yaml](../../config/training/topology.template.yaml)
- [placement_policy.template.yaml](../../config/training/placement_policy.template.yaml)

Generate plan from CLI:

```powershell
python tools\swag_placement_planner.py --pretty
```

Override mode:

```powershell
python tools\swag_placement_planner.py --mode ring_only --pretty
```

The Ops UI also exposes `/api/placement/plan` and a "Plan DABO/ring placement"
button for quick inspection.

## Spark ring preflight

Use the Spark preflight checker before distributed training to surface missing
SSH access, missing commands/packages, missing paths, and missing env vars.

- [spark_preflight.template.yaml](../../config/training/spark_preflight.template.yaml)

Dry run:

```powershell
python tools\swag_spark_preflight.py --config config\training\spark_preflight.template.yaml --dry-run --pretty
```

Live checks (set `enabled: true` in config first):

```powershell
python tools\swag_spark_preflight.py --config config\training\spark_preflight.template.yaml --pretty
```

Multi-node ring smoke check (run from `spark-01` with the repo + `.venv` on all nodes):

```bash
torchrun --nnodes=3 --nproc_per_node=1 --node_rank=0 \
  --rdzv_backend=c10d --rdzv_endpoint=spark-01:29511 tools/ring_smoke.py
```

If nodes resolve hostnames to loopback during distributed init, set explicit interface bindings:

```bash
export GLOO_SOCKET_IFNAME=eth0
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE=1
```

The former generated training commands are historical and no longer executable
through the SWAG runbook launcher. Cluster preflight does not admit a dataset or
authorize training; use the reviewed training workflow above.
