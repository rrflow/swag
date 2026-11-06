"""Offline integration checks for the project entry point and RROFLOW projection."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import swag
import swag_mcp_server
import swag_rroflow


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        swag.initialize(self.repo, "Build a TypeScript app with billing", project="test-project")

    def test_reinitialization_preserves_profile(self):
        original = (self.repo / swag.PROFILE).read_bytes()
        with self.assertRaises(FileExistsError):
            swag.initialize(self.repo, "A different project")
        self.assertEqual(original, (self.repo / swag.PROFILE).read_bytes())

    def test_preview_uses_profile_without_network_and_writes_safe_event(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected network call")):
            result = swag.preview(self.repo)
        self.assertFalse(result["model_executed"])
        self.assertFalse(result["uploaded"])
        self.assertGreater(result["counts"]["questions_total"], 0)
        self.assertIn("typescript", result["routing"]["selected_stacks"])
        record = json.loads(Path(result["rroflow_event_file"]).read_text())
        self.assertEqual(record["schema"], "rroflow.turn/v1")
        self.assertEqual(record["termination"], "completed")
        self.assertIsNone(record["content"])
        self.assertEqual(record["cwd"], "")
        self.assertNotIn("TypeScript app", json.dumps(record))
        self.assertNotIn(str(self.repo), json.dumps(record))
        self.assertEqual(record["usage"]["input_tokens"], 0)

    def test_profile_budget_changes_route(self):
        profile = swag.load_project(self.repo)
        profile["budget_mode"] = "low"
        (self.repo / swag.PROFILE).write_text(json.dumps(profile))
        result = swag.preview(self.repo)
        self.assertEqual(result["planned_model_tier"], "7b")
        self.assertEqual(result["tier_reason"], "low_cost_budget_mode:low")

    def test_invalid_profile_is_not_ready(self):
        profile = swag.load_project(self.repo)
        profile["has_test_harness"] = "false"
        (self.repo / swag.PROFILE).write_text(json.dumps(profile))
        self.assertEqual(swag.doctor(self.repo)["status"], "needs_setup")

    def test_doctor_missing_dependency_is_actionable(self):
        with patch("swag.importlib.util.find_spec", return_value=None):
            result = swag.doctor(self.repo)
        self.assertEqual(result["status"], "needs_setup")
        self.assertIn("pip install", result["checks"][0]["detail"])

    def test_failure_is_recorded_without_exception_content(self):
        with patch("swag._decide", side_effect=RuntimeError("private project content")):
            with self.assertRaises(RuntimeError):
                swag.preview(self.repo)
        record = json.loads(next((self.repo / ".swag/events").glob("*.json")).read_text())
        self.assertEqual(record["termination"], "tool_error")
        self.assertNotIn("private project content", json.dumps(record))

    def test_route_is_resolved_once(self):
        service = swag._service()
        with patch.object(service, "_resolve_route", wraps=service._resolve_route) as route:
            result = service.decide({"repo": str(self.repo), "intent_text": "Build an app"})
        self.assertEqual(route.call_count, 1)
        self.assertIn("semantic_router", result)
        self.assertIn("proposal", result["semantic_router"])
        self.assertEqual(result["semantic_router"]["state"], "engine_proposal_not_integrated")
        self.assertIsNone(result["semantic_router"]["proposal"])
        self.assertFalse(result["semantic_router"]["executionAuthorized"])
        self.assertFalse(result["semantic_router"]["engineValidated"])
        self.assertNotIn("rrflow_route_validation", result["decision"])

    def test_mcp_route_preview_cannot_invent_local_candidate_or_engine_admission(self):
        result = swag_mcp_server._handle_message({
            "jsonrpc": "2.0", "id": 9, "method": "tools/call",
            "params": {"name": "decision_route", "arguments": {
                "repo": str(self.repo), "intent_text": "Review dependencies"}},
        })
        self.assertNotIn("error", result)
        self.assertFalse(result["result"].get("isError", False))
        payload = json.loads(result["result"]["content"][0]["text"])
        self.assertIsNone(payload["semantic_router"]["proposal"])
        self.assertNotIn("route_request", payload["semantic_router"])
        self.assertNotIn("rrflow_validation", payload["semantic_router"])
        self.assertFalse(payload["semantic_router"]["executionAuthorized"])

    def test_mcp_project_preview(self):
        result = swag_mcp_server._handle_message({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "project_preview", "arguments": {"repo": str(self.repo)}},
        })
        content = json.loads(result["result"]["content"][0]["text"])
        self.assertEqual(content["status"], "preview_complete")

    def test_mcp_stdio_handshake_ignores_notifications(self):
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        process = subprocess.run(
            [sys.executable, str(ROOT / "tools/swag_mcp_server.py")],
            input="\n".join(json.dumps(m) for m in messages) + "\n",
            capture_output=True, text=True, timeout=20, check=True,
        )
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([r["id"] for r in results], [1, 2])
        self.assertIn("project_preview", [t["name"] for t in results[1]["result"]["tools"]])


class RroflowTests(unittest.TestCase):
    def record(self):
        return swag_rroflow.preview_record(
            project="test", session_id="session-1", turn_key="turn-1",
            started_at="2026-10-26T10:00:00Z", ended_at="2026-10-26T10:00:01Z", succeeded=True,
        )

    def test_event_identity_is_stable_for_retries(self):
        self.assertEqual(self.record()["event_id"], self.record()["event_id"])

    def test_remote_plaintext_and_missing_credentials_are_rejected(self):
        for url, credential in [("http://example.com", "key"), ("https://example.com", "")]:
            with self.assertRaises(ValueError):
                swag_rroflow.publish_record(self.record(), url, credential)

    def test_publish_contract_and_projection(self):
        record = self.record()
        record["content"] = {"input": "private", "output": "private"}
        record["cwd"] = "private-path"
        with patch("swag_rroflow.request.build_opener") as build:
            response = build.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"devspace":"test","accepted":1,"new":1,"replaced":0}'
            result = swag_rroflow.publish_record(record, "https://example.com", "test-key")
            req = build.return_value.open.call_args.args[0]
        self.assertEqual(req.full_url, "https://example.com/v1/turns")
        self.assertEqual(req.get_header("Authorization"), "Bearer test-key")
        body = json.loads(req.data)
        self.assertEqual(body["turns"][0]["event_id"], record["event_id"])
        self.assertIsNone(body["turns"][0]["content"])
        self.assertEqual(body["turns"][0]["cwd"], "")
        self.assertNotIn("test-key", req.data.decode())
        self.assertEqual(result["accepted"], 1)

    def test_rejected_upload_does_not_expose_remote_body(self):
        from urllib.error import HTTPError
        with patch("swag_rroflow.request.build_opener") as build:
            build.return_value.open.side_effect = HTTPError("https://example.com", 401, "secret", {}, None)
            with self.assertRaisesRegex(RuntimeError, "HTTP 401") as context:
                swag_rroflow.publish_record(self.record(), "https://example.com", "test-key")
        self.assertNotIn("secret", str(context.exception))
        self.assertNotIn("test-key", str(context.exception))

    def test_upload_requires_acknowledgement(self):
        with patch("swag_rroflow.request.build_opener") as build:
            response = build.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"ok":true}'
            with self.assertRaisesRegex(RuntimeError, "acknowledge"):
                swag_rroflow.publish_record(self.record(), "https://example.com", "test-key")

    def test_http_transport_retry_and_redirect(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        stored = {}

        class Ingest(BaseHTTPRequestHandler):
            redirect = False

            def log_message(self, *args):
                pass

            def do_POST(self):
                # Drain the body before closing a redirect response. Otherwise a
                # Windows socket can reset before urllib observes the HTTP status.
                raw = self.rfile.read(int(self.headers["Content-Length"]))
                if self.redirect:
                    self.send_response(307)
                    self.send_header("Location", "/redirect-target")
                    self.end_headers()
                    return
                if self.path != "/v1/turns" or self.headers.get("Authorization") != "Bearer test-key":
                    self.send_error(401)
                    return
                body = json.loads(raw)
                record = body["turns"][0]
                new = int(record["event_id"] not in stored)
                stored[record["event_id"]] = record
                response = json.dumps({"devspace": "test", "accepted": 1, "new": new, "replaced": 1 - new}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Ingest)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            first = swag_rroflow.publish_record(self.record(), base, "test-key")
            second = swag_rroflow.publish_record(self.record(), base, "test-key")
            self.assertEqual(first["new"], 1)
            self.assertEqual(second["replaced"], 1)
            self.assertEqual(len(stored), 1)
            Ingest.redirect = True
            with self.assertRaisesRegex(RuntimeError, "HTTP 307"):
                swag_rroflow.publish_record(self.record(), base, "test-key")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
