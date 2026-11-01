"""Content-free SWAG preview records for the existing RROFLOW ingest API."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib import error, parse, request
from uuid import NAMESPACE_URL, uuid5


def preview_record(
    *, project: str, session_id: str, turn_key: str,
    started_at: str, ended_at: str, succeeded: bool,
) -> dict[str, Any]:
    """A preview runs rules only: zero model usage is known, not estimated."""
    event_id = str(uuid5(NAMESPACE_URL, json.dumps(["swag", session_id, turn_key])))
    return {
        "schema": "rroflow.turn/v1",
        "event_id": event_id,
        "agent": "swag",
        "agent_version": "0.1.0",
        "provider": "none",
        "model": None,
        "session_id": session_id,
        "turn_key": turn_key,
        "subagent": None,
        "prompt_author": None,
        "started_at": started_at,
        "ended_at": ended_at,
        "cwd": "",
        "git_branch": "",
        "project": project,
        "usage": {
            "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "input_includes_cache": False,
        },
        "termination": "completed" if succeeded else "tool_error",
        "compacted": False,
        "tools": [{
            "id": event_id, "name": "swag.preview",
            "started_at": started_at, "ended_at": ended_at,
            "status": "ok" if succeeded else "error",
            "input": None, "output": None,
        }],
        "tools_unfinished": 0,
        "content": None,
        "signals": [],
        "collector": "swag/0.1.0",
    }


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def publish_record(record: dict[str, Any], base_url: str, credential: str) -> dict[str, Any]:
    """Explicit upload only; preserve event identity for retry/upsert semantics."""
    url = parse.urlsplit(base_url)
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not url.hostname or url.username or url.password or url.query or url.fragment
        or (url.scheme != "https" and not (url.scheme == "http" and local))
    ):
        raise ValueError("Use an HTTPS ingest base URL, or HTTP on localhost.")
    if not credential.strip():
        raise ValueError("Set RROFLOW_INGEST_KEY before publishing.")
    # This connector only sends its own content-free preview projection. Rebuild it
    # from the identity fields so a modified local artifact cannot upload content.
    if not isinstance(record, dict) or record.get("schema") != "rroflow.turn/v1" or record.get("collector") != "swag/0.1.0":
        raise ValueError("Expected a SWAG preview event.")
    if not isinstance(record.get("project"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", record["project"]):
        raise ValueError("Expected a project slug in the preview event.")
    if record.get("termination") not in {"completed", "tool_error"}:
        raise ValueError("Expected a completed or failed preview event.")
    for field in ("started_at", "ended_at"):
        value = record.get(field)
        if not isinstance(value, str) or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError(f"Expected a timestamp with timezone for {field}.")
    clean = preview_record(
        project=record["project"], session_id=record["session_id"],
        turn_key=record["turn_key"], started_at=record["started_at"],
        ended_at=record["ended_at"], succeeded=record["termination"] == "completed",
    )
    if clean["event_id"] != record.get("event_id"):
        raise ValueError("Event identity does not match its session and turn key.")
    req = request.Request(
        base_url.rstrip("/") + "/v1/turns",
        data=json.dumps({"turns": [clean]}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {credential}"},
        method="POST",
    )
    try:
        with request.build_opener(_NoRedirect()).open(req, timeout=10) as response:
            result = json.load(response)
    except error.HTTPError as exc:
        raise RuntimeError(f"RROFLOW rejected the upload (HTTP {exc.code}); event retained for retry.") from None
    except (error.URLError, TimeoutError, OSError):
        raise RuntimeError("RROFLOW is unreachable; event retained for retry.") from None
    if not isinstance(result, dict) or result.get("accepted") != 1 or not result.get("devspace"):
        raise RuntimeError("RROFLOW did not acknowledge one event; event retained for retry.")
    return {key: result.get(key) for key in ("devspace", "accepted", "new", "replaced")}
