#!/usr/bin/env python3
"""Minimal MCP-compatible server for SWAG runtime and controller integration.

This is intentionally lightweight and portable: a stdio JSON-RPC server that can
be used by external MCP clients or local orchestrators without requiring a third-
party SDK.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from boundary_controller import compose_battery
from swag_runtime_bootstrap import resolve_effective_runtime
from swag_observability import Span, summarize, trace_directory
from swag_lfg import LfgBridgeError


def _run_compose_battery(params: dict[str, Any]) -> dict[str, Any]:
    repo = Path(str(params.get("repo", ROOT))).resolve()
    return compose_battery(
        repo=repo,
        maturity=str(params.get("maturity", "growing")),
        has_test_harness=bool(params.get("has_test_harness", False)),
        unbounded_data_path=bool(params.get("unbounded_data_path", False)),
        intent_text=str(params.get("intent_text", "")),
        explicit_domains=list(params.get("explicit_domains", []) or []),
        primary_stack=params.get("primary_stack"),
        include_overlaps=bool(params.get("include_overlaps", False)),
    )


def _run_resolve_runtime(params: dict[str, Any]) -> dict[str, Any]:
    repo = Path(str(params.get("repo", ROOT))).resolve()
    global_config = Path(str(params.get("global_config", ROOT / "config" / "runtime" / "global_defaults.template.yaml"))).resolve()
    project_config = Path(str(params.get("project_config", ROOT / "rrflow.sync.yaml"))).resolve()
    return resolve_effective_runtime(repo=repo, global_config=global_config, project_config=project_config)


def _run_decision_route(params: dict[str, Any]) -> dict[str, Any]:
    from swag_decision_service import DecisionService, ServiceConfig

    if params.get('execute_frontier') or params.get('execute_local'):
        raise ValueError('MCP routing is preview-only; model execution requires RRFlow admission.')

    repo = Path(str(params.get("repo", ROOT))).resolve()
    provider_cfg = Path(str(params.get("provider_config", ROOT / "config" / "frontier" / "providers.template.yaml"))).resolve()
    attunement_cfg = Path(str(params.get("attunement_config", ROOT / "config" / "attunement" / "operator_profiles.template.yaml"))).resolve()
    system_policy = Path(str(params.get("system_one_policy", ROOT / "config" / "boundaries" / "system_one_controller_policy.yaml"))).resolve()
    tier_policy = Path(str(params.get("system_one_tier_policy", ROOT / "config" / "boundaries" / "system_one_tier_policy.yaml"))).resolve()
    aiddevspec = Path(str(params.get("aiddevspec_config", ROOT / "config" / "aiddevspec" / "default.yaml"))).resolve()
    local_cfg = Path(str(params.get("local_provider_config", ROOT / "config" / "local" / "model_adapters.template.yaml"))).resolve()

    service = DecisionService(
        ServiceConfig(
            provider_config_path=provider_cfg,
            attunement_config_path=attunement_cfg,
            system_one_policy_path=system_policy,
            system_one_tier_policy_path=tier_policy,
            aiddevspec_config_path=aiddevspec,
            local_provider_config_path=local_cfg,
        )
    )

    payload = {
        "repo": str(repo),
        "intent_text": str(params.get("intent_text", "")),
        "maturity": str(params.get("maturity", "growing")),
        "has_test_harness": bool(params.get("has_test_harness", True)),
        "unbounded_data_path": bool(params.get("unbounded_data_path", False)),
        "domains": list(params.get("domains", []) or []),
        "primary_stack": params.get("primary_stack"),
        "include_overlaps": bool(params.get("include_overlaps", False)),
        "budget_mode": params.get("budget_mode"),
        "subscription_tier": params.get("subscription_tier"),
        "attunement_profile": str(params.get("attunement_profile", "default_rollout")),
        "route_profile": params.get("route_profile"),
        "model_tier": params.get("model_tier"),
        "execute_frontier": bool(params.get("execute_frontier", False)),
        "execute_local": bool(params.get("execute_local", False)),
    }
    return service.decide(payload)


def _tool_list() -> list[dict[str, Any]]:
    return [
        {
            "name": "project_preview",
            "description": "Preview a project's saved SWAG profile without model calls. Writes local decision and content-free RROFLOW event files; does not upload.",
            "inputSchema": {
                "type": "object",
                "properties": {"repo": {"type": "string"}, "intent": {"type": "string"}},
                "required": ["repo"],
                "additionalProperties": False,
            },
        },
        {
            "name": "compose_battery",
            "description": "Compose the SWAG boundary question battery for a repo + intent context.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "maturity": {"type": "string"},
                    "has_test_harness": {"type": "boolean"},
                    "unbounded_data_path": {"type": "boolean"},
                    "intent_text": {"type": "string"},
                    "explicit_domains": {"type": "array", "items": {"type": "string"}},
                    "primary_stack": {"type": "string"},
                    "include_overlaps": {"type": "boolean"},
                },
                "required": ["repo"],
            },
        },
        {
            "name": "resolve_runtime",
            "description": "Merge global defaults with the project RRFlow config into one effective runtime state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "global_config": {"type": "string"},
                    "project_config": {"type": "string"},
                },
                "required": ["repo"],
            },
        },
        {
            "name": "decision_route",
            "description": "Resolve the SWAG decision route and selected battery for the current request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "intent_text": {"type": "string"},
                    "maturity": {"type": "string"},
                    "has_test_harness": {"type": "boolean"},
                    "unbounded_data_path": {"type": "boolean"},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "primary_stack": {"type": "string"},
                    "include_overlaps": {"type": "boolean"},
                    "budget_mode": {"type": "string"},
                    "subscription_tier": {"type": "string"},
                    "attunement_profile": {"type": "string"},
                    "route_profile": {"type": "string"},
                    "model_tier": {"type": "string"},
                },
                "required": ["repo", "intent_text"],
            },
        },
        {
            "name": "developer_status",
            "description": "Read the versioned UI model: engine connection, traces, reviewed-dataset readiness and registered training artifacts. Does not launch training or promote models.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "lfg_assess",
            "description": "Assess a request through an explicitly configured local LFG instance. Returns an advisory observation; it does not authorize, route, or dispatch work. LFG and SWAG record local diagnostics.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string", "description": "The request to assess; sent only to the configured local LFG instance."}},
                "required": ["text"],
            },
            "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
        },
        {
            "name": "rrflow_status",
            "description": "Read the explicitly configured RRFlow engine through authenticated public operations. Does not dispatch a model or execute project work.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "observability_summary",
            "description": "Read measured SWAG client timings, failures and incomplete traces. No model quality or subscription usage is inferred.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "health",
            "description": "Simple liveness check for the SWAG MCP bridge.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _dispatch_message(message: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    if "id" not in message:
        # MCP initialized/cancelled notifications are one-way messages.
        return None
    method = message.get("method")
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "swag-mcp-server", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": message.get("id"), "result": {"tools": _tool_list()}}
    if method == "tools/call":
        tool_name = str((params or {}).get("name") or "")
        tool_args = (params or {}).get("arguments") if isinstance((params or {}).get("arguments"), dict) else {}
        if tool_name == "project_preview":
            from swag import preview

            if not isinstance(tool_args.get("repo"), str) or not tool_args["repo"].strip():
                raise ValueError("project_preview requires a repo path.")
            if "intent" in tool_args and not isinstance(tool_args["intent"], str):
                raise ValueError("intent must be a string.")
            result = preview(Path(tool_args["repo"]).resolve(), tool_args.get("intent"))
        elif tool_name == "compose_battery":
            result = _run_compose_battery(tool_args)
        elif tool_name == "resolve_runtime":
            result = _run_resolve_runtime(tool_args)
        elif tool_name == "decision_route":
            result = _run_decision_route(tool_args)
        elif tool_name == "health":
            result = {"status": "ok", "runtime": "swag-mcp-server", "repo": str(ROOT)}
        elif tool_name == 'rrflow_status':
            from swag_rrflow import status
            result = status()
        elif tool_name == 'lfg_assess':
            from swag_lfg import assess
            result = assess(tool_args.get('text'))
        elif tool_name == 'observability_summary':
            result = summarize(trace_directory())
        elif tool_name == 'developer_status':
            from swag_dev_status import status
            result = status()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        return {"jsonrpc": "2.0", "id": message.get("id"), "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=True, indent=2)}]}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": message.get("id"), "result": {"ok": True}}
    return {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32601, "message": "Method not found"}}


def _handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(message, dict) or 'id' not in message:
        return _dispatch_message(message)
    params = message.get('params')
    metadata = params.get('_meta', {}) if isinstance(params, dict) else {}
    parent = metadata.get('traceparent') if isinstance(metadata, dict) else None
    try:
        span = Span('mcp.request', traceparent=parent)
    except ValueError:
        return {'jsonrpc': '2.0', 'id': message['id'],
                'error': {'code': -32602, 'message': 'Invalid traceparent'}}
    try:
        with span:
            name = params.get('name') if isinstance(params, dict) else None
            known = {tool['name'] for tool in _tool_list()}
            if message.get('method') == 'tools/call' and isinstance(name, str) and name in known:
                with Span('mcp.tool.' + name):
                    response = _dispatch_message(message)
            else:
                response = _dispatch_message(message)
            if response is not None and 'error' in response:
                span.fail('ProtocolError')
    except LfgBridgeError as exc:
        # Bridge errors are fixed strings, never prompts or connection details.
        response = {'jsonrpc': '2.0', 'id': message['id'], 'result': {
            'isError': True, 'content': [{'type': 'text', 'text': str(exc)}]}}
    except (Exception, SystemExit):
        # Trace exit records the actual error class and safe code locations.
        # Do not return exception text: it may contain credentials or prompts.
        response = {'jsonrpc': '2.0', 'id': message['id'], 'result': {
            'isError': True, 'content': [{'type': 'text', 'text':
                'SWAG operation failed; inspect the correlated local trace.'}]}}
        if message.get('method') != 'tools/call':
            response = {'jsonrpc': '2.0', 'id': message['id'],
                        'error': {'code': -32603, 'message': 'SWAG request failed'}}
    if response is not None:
        metadata = {'swag/traceId': span.trace_id, 'swag/spanId': span.span_id}
        if isinstance(response.get('result'), dict):
            response['result']['_meta'] = metadata
        elif isinstance(response.get('error'), dict):
            response['error']['data'] = metadata
    return response


def main() -> int:
    while True:
        raw_line = sys.stdin.readline(1_048_577)
        if not raw_line:
            break
        if len(raw_line) > 1_048_576:
            print(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': {
                'code': -32600, 'message': 'Request exceeds its bound'}}), flush=True)
            return 1
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {exc.msg}"}}), flush=True)
            continue
        try:
            response = _handle_message(message)
        except (Exception, SystemExit) as exc:  # pragma: no cover - runtime path
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id") if isinstance(message, dict) else None,
                "error": {"code": -32603, "message": "SWAG request failed; inspect local traces for the error class and code location."},
            }
        if response is not None:
            print(json.dumps(response, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
