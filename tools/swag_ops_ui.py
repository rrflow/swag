#!/usr/bin/env python3
"""Local SWAG operations UI for dataset quality and training orchestration."""
from __future__ import annotations

import argparse
import json
import traceback
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from controller_model_experiment import (
    DEFAULT_MODELS,
    build_execution_plan,
    run_generation,
)
from swag_dataset_quality import run_quality_pipeline
from swag_placement_planner import plan_placement
from swag_spark_preflight import run_preflight
from swag_training_pipeline import run_pipeline


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PIPELINE_CONFIG = ROOT / "config" / "training" / "pipeline.template.yaml"
DEFAULT_DATASET_QUALITY_CONFIG = ROOT / "config" / "training" / "dataset_quality.template.yaml"
DEFAULT_PROVIDER_CONFIG = ROOT / "config" / "frontier" / "providers.template.yaml"
DEFAULT_ATTUNEMENT_CONFIG = ROOT / "config" / "attunement" / "operator_profiles.template.yaml"
DEFAULT_EXPERIMENT_OUTPUT_DIR = ROOT / "files" / "controller_experiments"
DEFAULT_MANIFEST = ROOT / "files" / "training" / "manifests" / "latest_manifest.json"
DEFAULT_QUALITY_REPORT = ROOT / "files" / "training" / "data" / "controller_sft.quality_report.json"
DEFAULT_REVIEW_STATE = ROOT / "files" / "training" / "data" / "review_state.json"
DEFAULT_CURATED_DATASET = ROOT / "files" / "training" / "data" / "controller_sft.curated.jsonl"
DEFAULT_CURATED_REPORT = ROOT / "files" / "training" / "data" / "controller_sft.curated.report.json"
DEFAULT_TOPOLOGY_CONFIG = ROOT / "config" / "training" / "topology.template.yaml"
DEFAULT_PLACEMENT_POLICY_CONFIG = ROOT / "config" / "training" / "placement_policy.template.yaml"
DEFAULT_SPARK_PREFLIGHT_CONFIG = ROOT / "config" / "training" / "spark_preflight.template.yaml"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return None
    return data


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def _row_key(row: dict[str, Any]) -> str:
    canonical = json.dumps(row, sort_keys=True, ensure_ascii=True)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, canonical))


class JobRegistry:
    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="swag-ui-job")
        self._jobs: dict[str, dict[str, Any]] = {}
        self._futures: dict[str, Future[Any]] = {}

    def submit(self, kind: str, fn: Any, args: tuple[Any, ...]) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "kind": kind,
            "status": "running",
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "result": None,
            "error": None,
        }
        future = self._executor.submit(fn, *args)
        self._futures[job_id] = future
        future.add_done_callback(lambda f, jid=job_id: self._finalize(jid, f))
        return job_id

    def _finalize(self, job_id: str, future: Future[Any]) -> None:
        job = self._jobs[job_id]
        job["updated_at"] = _iso_now()
        try:
            result = future.result()
        except Exception as exc:  # explicit error propagation to client
            job["status"] = "failed"
            job["error"] = {"message": str(exc), "trace": traceback.format_exc(limit=6)}
            return
        job["status"] = "completed"
        job["result"] = result

    def list_jobs(self) -> list[dict[str, Any]]:
        return sorted(self._jobs.values(), key=lambda item: item["created_at"], reverse=True)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


class ReviewStore:
    def __init__(self, state_path: Path, source_file: Path):
        self.state_path = state_path
        self.source_file = source_file
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        data = _load_json_if_exists(self.state_path)
        if data and isinstance(data.get("items"), dict):
            return data
        return {"schema_version": 1, "updated_at": _iso_now(), "items": {}}

    def _persist(self) -> None:
        self._state["updated_at"] = _iso_now()
        _write_json(self.state_path, self._state)

    def _base_rows(self) -> list[dict[str, Any]]:
        return _read_jsonl(self.source_file)

    def list_items(self, status: str = "pending", limit: int = 25, offset: int = 0) -> dict[str, Any]:
        rows = self._base_rows()
        out: list[dict[str, Any]] = []
        items = self._state.get("items", {})
        if not isinstance(items, dict):
            items = {}
        for idx, row in enumerate(rows, start=1):
            item_id = f"row-{idx:06d}"
            row_hash = _row_key(row)
            review = items.get(item_id, {})
            decision = review.get("decision", "pending") if isinstance(review, dict) else "pending"
            if status != "all" and decision != status:
                continue
            out.append(
                {
                    "item_id": item_id,
                    "line_index": idx,
                    "decision": decision,
                    "reason_tags": review.get("reason_tags", []) if isinstance(review, dict) else [],
                    "notes": review.get("notes", "") if isinstance(review, dict) else "",
                    "row_hash": row_hash,
                    "sample": row,
                }
            )
        total = len(out)
        window = out[offset : offset + limit]
        return {"status": status, "total": total, "offset": offset, "limit": limit, "items": window}

    def summary(self) -> dict[str, Any]:
        rows = self._base_rows()
        items = self._state.get("items", {})
        if not isinstance(items, dict):
            items = {}
        counts = {"pending": 0, "approved": 0, "rejected": 0}
        for idx, _row in enumerate(rows, start=1):
            item_id = f"row-{idx:06d}"
            review = items.get(item_id, {})
            decision = review.get("decision", "pending") if isinstance(review, dict) else "pending"
            if decision not in counts:
                decision = "pending"
            counts[decision] += 1
        return {
            "source_file": str(self.source_file),
            "state_file": str(self.state_path),
            "total_rows": len(rows),
            "counts": counts,
            "updated_at": self._state.get("updated_at"),
        }

    def apply_decision(
        self,
        item_id: str,
        decision: str,
        reason_tags: list[str],
        notes: str,
        edited_sample: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if decision not in {"approved", "rejected", "pending"}:
            raise RuntimeError("decision must be approved, rejected, or pending")
        rows = self._base_rows()
        if not item_id.startswith("row-"):
            raise RuntimeError("item_id must match row-######")
        try:
            index = int(item_id.split("-", 1)[1])
        except ValueError as exc:
            raise RuntimeError("Invalid item_id format.") from exc
        if index < 1 or index > len(rows):
            raise RuntimeError(f"item_id {item_id} is out of range for source dataset.")
        if edited_sample is not None and not isinstance(edited_sample, dict):
            raise RuntimeError("edited_sample must be a JSON object when provided.")

        items = self._state.get("items", {})
        if not isinstance(items, dict):
            items = {}
            self._state["items"] = items

        items[item_id] = {
            "decision": decision,
            "reason_tags": [str(tag) for tag in reason_tags if str(tag).strip()],
            "notes": notes,
            "edited_sample": edited_sample,
            "updated_at": _iso_now(),
        }
        self._persist()
        return {"item_id": item_id, "decision": decision}

    def export_curated(self, curated_file: Path, report_file: Path, include_pending: bool) -> dict[str, Any]:
        rows = self._base_rows()
        items = self._state.get("items", {})
        if not isinstance(items, dict):
            items = {}
        curated: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for idx, row in enumerate(rows, start=1):
            item_id = f"row-{idx:06d}"
            review = items.get(item_id, {})
            decision = review.get("decision", "pending") if isinstance(review, dict) else "pending"
            if decision == "rejected":
                skipped.append({"item_id": item_id, "reason": "rejected"})
                continue
            if decision == "pending" and not include_pending:
                skipped.append({"item_id": item_id, "reason": "pending"})
                continue
            candidate = row
            if isinstance(review, dict):
                edited = review.get("edited_sample")
                if isinstance(edited, dict):
                    candidate = edited
            curated.append(candidate)

        _write_jsonl(curated_file, curated)
        report = {
            "source_file": str(self.source_file),
            "state_file": str(self.state_path),
            "curated_file": str(curated_file),
            "include_pending": include_pending,
            "counts": {
                "source_rows": len(rows),
                "curated_rows": len(curated),
                "skipped_rows": len(skipped),
            },
            "skipped": skipped,
            "generated_at": _iso_now(),
        }
        _write_json(report_file, report)
        return report


class OpsContext:
    def __init__(self, args: argparse.Namespace):
        self.pipeline_config = args.pipeline_config.resolve()
        self.dataset_quality_config = args.dataset_quality_config.resolve()
        self.provider_config = args.provider_config.resolve()
        self.attunement_config = args.attunement_config.resolve()
        self.attunement_profile = args.attunement_profile
        self.route_profile = args.route_profile
        self.experiment_output_dir = args.experiment_output_dir.resolve()
        self.manifest_path = args.manifest_path.resolve()
        self.quality_report_path = args.quality_report_path.resolve()
        self.review_state_path = args.review_state_path.resolve()
        self.curated_dataset_path = args.curated_dataset_path.resolve()
        self.curated_report_path = args.curated_report_path.resolve()
        self.topology_config = args.topology_config.resolve()
        self.placement_policy_config = args.placement_policy_config.resolve()
        self.spark_preflight_config = args.spark_preflight_config.resolve()
        self.job_registry = JobRegistry(max_workers=2)
        self.review_store = ReviewStore(
            state_path=self.review_state_path,
            source_file=self._resolve_review_source_file(),
        )

    def _resolve_review_source_file(self) -> Path:
        cfg = _load_json_if_exists(self.manifest_path)
        if cfg:
            dataset_path = cfg.get("dataset_for_training")
            if isinstance(dataset_path, str) and dataset_path.strip():
                return Path(dataset_path).resolve()
        return ROOT / "files" / "training" / "data" / "controller_sft.cleaned.jsonl"

    def run_training_pipeline(self) -> dict[str, Any]:
        result = run_pipeline(self.pipeline_config)
        dataset_for_training = result.get("dataset_for_training")
        if isinstance(dataset_for_training, str) and dataset_for_training.strip():
            self.review_store.source_file = Path(dataset_for_training).resolve()
        return result

    def run_dataset_quality(self) -> dict[str, Any]:
        result = run_quality_pipeline(self.dataset_quality_config)
        cleaned = ((result.get("output") or {}).get("cleaned_jsonl")) if isinstance(result, dict) else None
        if isinstance(cleaned, str) and cleaned.strip():
            self.review_store.source_file = Path(cleaned).resolve()
        return result

    def run_experiments(self) -> dict[str, Any]:
        models = list(DEFAULT_MODELS)
        generation = run_generation(
            repo=ROOT,
            out_dir=self.experiment_output_dir,
            models=models,
            scenarios_file=None,
        )
        execution_plan = build_execution_plan(
            out_dir=self.experiment_output_dir,
            models=models,
            provider_config_path=self.provider_config,
            attunement_config_path=self.attunement_config,
            attunement_profile_key=self.attunement_profile,
            route_profile_key=self.route_profile,
            model_catalog_path=ROOT / "config" / "training" / "model_catalog.template.yaml",
            cluster_profile_path=ROOT / "config" / "training" / "spark_cluster_profile.template.yaml",
        )
        return {"generation": generation, "execution_plan": execution_plan}

    def summary(self) -> dict[str, Any]:
        return {
            "pipeline_config": str(self.pipeline_config),
            "dataset_quality_config": str(self.dataset_quality_config),
            "manifest_path": str(self.manifest_path),
            "quality_report_path": str(self.quality_report_path),
            "review_state_path": str(self.review_state_path),
            "curated_dataset_path": str(self.curated_dataset_path),
            "topology_config": str(self.topology_config),
            "placement_policy_config": str(self.placement_policy_config),
            "spark_preflight_config": str(self.spark_preflight_config),
            "latest_manifest": _load_json_if_exists(self.manifest_path),
            "latest_quality_report": _load_json_if_exists(self.quality_report_path),
            "review_summary": self.review_store.summary(),
            "placement_plan": self.placement_plan(),
        }

    def review_summary(self) -> dict[str, Any]:
        return self.review_store.summary()

    def review_queue(self, status: str, limit: int, offset: int) -> dict[str, Any]:
        return self.review_store.list_items(status=status, limit=limit, offset=offset)

    def review_decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        item_id = str(payload.get("item_id", ""))
        decision = str(payload.get("decision", "pending"))
        reason_tags_raw = payload.get("reason_tags", [])
        reason_tags = [str(tag) for tag in reason_tags_raw] if isinstance(reason_tags_raw, list) else []
        notes = str(payload.get("notes", ""))
        edited_sample = payload.get("edited_sample")
        result = self.review_store.apply_decision(
            item_id=item_id,
            decision=decision,
            reason_tags=reason_tags,
            notes=notes,
            edited_sample=edited_sample if isinstance(edited_sample, dict) else None,
        )
        return {"updated": result, "summary": self.review_store.summary()}

    def review_export(self, include_pending: bool) -> dict[str, Any]:
        return self.review_store.export_curated(
            curated_file=self.curated_dataset_path,
            report_file=self.curated_report_path,
            include_pending=include_pending,
        )

    def placement_plan(self, mode: str | None = None) -> dict[str, Any]:
        return plan_placement(
            topology_path=self.topology_config,
            policy_path=self.placement_policy_config,
            override_mode=mode,
        )

    def run_spark_preflight(self, dry_run: bool) -> dict[str, Any]:
        return run_preflight(config_path=self.spark_preflight_config, dry_run=dry_run)


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SWAG Ops UI</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background:#111827; color:#e5e7eb; }
    h1, h2 { margin: 0 0 12px; }
    .row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; }
    button { border:0; padding:10px 14px; border-radius:8px; cursor:pointer; background:#2563eb; color:white; }
    button.secondary { background:#374151; }
    button.warn { background:#b45309; }
    button.good { background:#15803d; }
    .card { background:#1f2937; border:1px solid #374151; border-radius:10px; padding:12px; margin-bottom:12px; }
    pre { background:#0b1220; border:1px solid #334155; border-radius:8px; padding:10px; overflow:auto; max-height:320px; }
    textarea, input { width:100%; background:#0b1220; color:#e5e7eb; border:1px solid #334155; border-radius:8px; padding:8px; }
    textarea { min-height:180px; }
    .muted { color:#9ca3af; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
  </style>
</head>
<body>
  <h1>SWAG Ops UI</h1>
  <p class="muted">Dataset quality, training scaffold, experiments, and human review workflow.</p>
  <div class="row">
    <button id="runPipeline" disabled>Legacy training pipeline retired</button>
    <p>New training requires independently reviewed real observations and explicit training permission. Use the reviewed routing-data workflow.</p>
    <button id="runQuality">Run quality only</button>
    <button id="runExperiments">Run experiments</button>
    <button id="planPlacement" class="secondary">Plan DABO/ring placement</button>
    <button id="sparkPreflight" class="secondary">Run Spark preflight</button>
    <button id="refresh" class="secondary">Refresh summary</button>
  </div>
  <div class="card">
    <h2>Latest Summary</h2>
    <pre id="summary">loading...</pre>
  </div>
  <div class="card">
    <h2>Jobs</h2>
    <pre id="jobs">loading...</pre>
  </div>
  <div class="card">
    <h2>Dataset Review Queue</h2>
    <div class="row">
      <button id="loadPending" class="secondary">Load pending queue</button>
      <button id="prevItem" class="secondary">Prev</button>
      <button id="nextItem" class="secondary">Next</button>
      <button id="approveItem" class="good">Approve</button>
      <button id="rejectItem" class="warn">Reject</button>
      <button id="savePending" class="secondary">Save as pending</button>
      <button id="exportCurated">Export curated dataset</button>
    </div>
    <div class="grid">
      <div>
        <h3>Queue/Status</h3>
        <pre id="reviewSummary">loading...</pre>
        <h3>Current Item</h3>
        <pre id="reviewItem">none</pre>
      </div>
      <div>
        <h3>Edit sample JSON</h3>
        <textarea id="editedSample"></textarea>
        <h3>Reason tags (comma separated)</h3>
        <input id="reasonTags" placeholder="format,error,policy,signal" />
        <h3>Reviewer notes</h3>
        <textarea id="reviewNotes"></textarea>
      </div>
    </div>
  </div>
<script>
let reviewQueue = [];
let reviewIndex = 0;

async function api(path, method="GET", body=null){
  const opts={method, headers:{"Content-Type":"application/json"}};
  if(body){ opts.body=JSON.stringify(body); }
  const resp=await fetch(path, opts);
  const data=await resp.json();
  if(!resp.ok){ throw new Error(JSON.stringify(data)); }
  return data;
}
function setPre(id, value){ document.getElementById(id).textContent = JSON.stringify(value, null, 2); }
function currentItem(){ return reviewQueue.length ? reviewQueue[reviewIndex] : null; }
function renderCurrentItem(){
  const item = currentItem();
  if(!item){
    setPre("reviewItem", {message:"No review item loaded"});
    document.getElementById("editedSample").value = "";
    document.getElementById("reasonTags").value = "";
    document.getElementById("reviewNotes").value = "";
    return;
  }
  setPre("reviewItem", {index: reviewIndex + 1, total: reviewQueue.length, item});
  document.getElementById("editedSample").value = JSON.stringify(item.sample, null, 2);
  document.getElementById("reasonTags").value = (item.reason_tags || []).join(",");
  document.getElementById("reviewNotes").value = item.notes || "";
}
async function refresh(){
  try{
    setPre("summary", await api("/api/summary"));
    setPre("jobs", await api("/api/jobs"));
    setPre("reviewSummary", await api("/api/review/summary"));
  }catch(err){
    setPre("jobs", {error:String(err)});
  }
}
async function start(path){
  try{
    const out = await api(path, "POST", {});
    setPre("jobs", out);
    await refresh();
  }catch(err){
    setPre("jobs", {error:String(err)});
  }
}
async function loadPending(){
  const out = await api("/api/review/queue?status=pending&limit=200");
  reviewQueue = out.items || [];
  reviewIndex = 0;
  renderCurrentItem();
  setPre("reviewSummary", await api("/api/review/summary"));
}
function parseEditedSample(){
  const raw = document.getElementById("editedSample").value;
  return JSON.parse(raw);
}
function parseReasonTags(){
  const raw = document.getElementById("reasonTags").value;
  return raw.split(",").map(x=>x.trim()).filter(Boolean);
}
async function submitDecision(decision){
  const item = currentItem();
  if(!item){ return; }
  try{
    const payload = {
      item_id: item.item_id,
      decision,
      reason_tags: parseReasonTags(),
      notes: document.getElementById("reviewNotes").value,
      edited_sample: parseEditedSample(),
    };
    await api("/api/review/decide", "POST", payload);
    await loadPending();
  }catch(err){
    setPre("reviewSummary", {error:String(err)});
  }
}
async function exportCurated(){
  try{
    const out = await api("/api/review/export", "POST", {include_pending:false});
    setPre("reviewSummary", out);
  }catch(err){
    setPre("reviewSummary", {error:String(err)});
  }
}
document.getElementById("runPipeline").onclick=()=>start("/api/jobs/pipeline");
document.getElementById("runQuality").onclick=()=>start("/api/jobs/quality");
document.getElementById("runExperiments").onclick=()=>start("/api/jobs/experiments");
document.getElementById("planPlacement").onclick=async ()=>{ try{ setPre("summary", await api("/api/placement/plan")); }catch(err){ setPre("summary",{error:String(err)});} };
document.getElementById("sparkPreflight").onclick=()=>start("/api/jobs/spark-preflight");
document.getElementById("refresh").onclick=refresh;
document.getElementById("loadPending").onclick=loadPending;
document.getElementById("prevItem").onclick=()=>{ if(reviewQueue.length){ reviewIndex=(reviewIndex-1+reviewQueue.length)%reviewQueue.length; renderCurrentItem(); } };
document.getElementById("nextItem").onclick=()=>{ if(reviewQueue.length){ reviewIndex=(reviewIndex+1)%reviewQueue.length; renderCurrentItem(); } };
document.getElementById("approveItem").onclick=()=>submitDecision("approved");
document.getElementById("rejectItem").onclick=()=>submitDecision("rejected");
document.getElementById("savePending").onclick=()=>submitDecision("pending");
document.getElementById("exportCurated").onclick=exportCurated;
setInterval(refresh, 3000);
refresh();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    ctx: OpsContext | None = None

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, status: int, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        parsed = json.loads(body or "{}")
        if not isinstance(parsed, dict):
            raise RuntimeError("JSON body must be an object.")
        return parsed

    def do_GET(self) -> None:  # noqa: N802
        assert self.ctx is not None
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/" or path.startswith("/index.html"):
            self._html(HTTPStatus.OK, HTML_PAGE)
            return
        if path == "/health":
            self._json(HTTPStatus.OK, {"ok": True, "service": "swag-ops-ui"})
            return
        if path == "/api/summary":
            self._json(HTTPStatus.OK, self.ctx.summary())
            return
        if path == "/api/placement/plan":
            mode = str((query.get("mode", [""])[0])).strip() or None
            self._json(HTTPStatus.OK, self.ctx.placement_plan(mode=mode))
            return
        if path == "/api/spark/preflight":
            dry_run = str((query.get("dry_run", ["false"])[0])).lower() in {"1", "true", "yes"}
            self._json(HTTPStatus.OK, self.ctx.run_spark_preflight(dry_run=dry_run))
            return
        if path == "/api/jobs":
            self._json(HTTPStatus.OK, {"jobs": self.ctx.job_registry.list_jobs()})
            return
        if path == "/api/review/summary":
            self._json(HTTPStatus.OK, self.ctx.review_summary())
            return
        if path == "/api/review/queue":
            status = str((query.get("status", ["pending"])[0]))
            try:
                limit = int((query.get("limit", ["25"])[0]))
                offset = int((query.get("offset", ["0"])[0]))
            except ValueError as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid limit/offset: {exc}"})
                return
            limit = max(1, min(limit, 500))
            offset = max(0, offset)
            self._json(HTTPStatus.OK, self.ctx.review_queue(status=status, limit=limit, offset=offset))
            return
        if path.startswith("/api/jobs/"):
            job_id = path.split("/api/jobs/", 1)[1]
            job = self.ctx.job_registry.get_job(job_id)
            if not job:
                self._json(HTTPStatus.NOT_FOUND, {"error": "job_not_found", "job_id": job_id})
                return
            self._json(HTTPStatus.OK, job)
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        assert self.ctx is not None
        try:
            payload = self._read_json_body()
            if self.path == "/api/jobs/pipeline":
                job_id = self.ctx.job_registry.submit("pipeline", self.ctx.run_training_pipeline, ())
            elif self.path == "/api/jobs/quality":
                job_id = self.ctx.job_registry.submit("quality", self.ctx.run_dataset_quality, ())
            elif self.path == "/api/jobs/experiments":
                job_id = self.ctx.job_registry.submit("experiments", self.ctx.run_experiments, ())
            elif self.path == "/api/jobs/spark-preflight":
                dry_run = bool(payload.get("dry_run", False))
                job_id = self.ctx.job_registry.submit(
                    "spark-preflight",
                    self.ctx.run_spark_preflight,
                    (dry_run,),
                )
            elif self.path == "/api/review/decide":
                self._json(HTTPStatus.OK, self.ctx.review_decide(payload))
                return
            elif self.path == "/api/review/export":
                include_pending = bool(payload.get("include_pending", False))
                self._json(HTTPStatus.OK, self.ctx.review_export(include_pending=include_pending))
                return
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            self._json(HTTPStatus.ACCEPTED, {"job_id": job_id, "status": "running"})
        except Exception as exc:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"error": str(exc), "trace": traceback.format_exc(limit=4)},
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SWAG local operations UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--pipeline-config", type=Path, default=DEFAULT_PIPELINE_CONFIG)
    parser.add_argument("--dataset-quality-config", type=Path, default=DEFAULT_DATASET_QUALITY_CONFIG)
    parser.add_argument("--provider-config", type=Path, default=DEFAULT_PROVIDER_CONFIG)
    parser.add_argument("--attunement-config", type=Path, default=DEFAULT_ATTUNEMENT_CONFIG)
    parser.add_argument("--attunement-profile", default="default_rollout")
    parser.add_argument("--route-profile", default=None)
    parser.add_argument("--experiment-output-dir", type=Path, default=DEFAULT_EXPERIMENT_OUTPUT_DIR)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--quality-report-path", type=Path, default=DEFAULT_QUALITY_REPORT)
    parser.add_argument("--review-state-path", type=Path, default=DEFAULT_REVIEW_STATE)
    parser.add_argument("--curated-dataset-path", type=Path, default=DEFAULT_CURATED_DATASET)
    parser.add_argument("--curated-report-path", type=Path, default=DEFAULT_CURATED_REPORT)
    parser.add_argument("--topology-config", type=Path, default=DEFAULT_TOPOLOGY_CONFIG)
    parser.add_argument("--placement-policy-config", type=Path, default=DEFAULT_PLACEMENT_POLICY_CONFIG)
    parser.add_argument("--spark-preflight-config", type=Path, default=DEFAULT_SPARK_PREFLIGHT_CONFIG)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ctx = OpsContext(args)
    Handler.ctx = ctx
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        json.dumps(
            {
                "service": "swag-ops-ui",
                "host": args.host,
                "port": args.port,
                "pipeline_config": str(ctx.pipeline_config),
                "dataset_quality_config": str(ctx.dataset_quality_config),
                "manifest_path": str(ctx.manifest_path),
                "review_state_path": str(ctx.review_state_path),
                "curated_dataset_path": str(ctx.curated_dataset_path),
                "topology_config": str(ctx.topology_config),
                "placement_policy_config": str(ctx.placement_policy_config),
                "spark_preflight_config": str(ctx.spark_preflight_config),
            },
            ensure_ascii=True,
        )
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
