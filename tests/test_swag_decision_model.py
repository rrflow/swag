"""Decision-model brief checks over real local HTTP with a scripted model; these are software tests, not routing quality evidence."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import swag_brief
from swag_decision_model import DecisionModelError, probabilities

REQUEST = "people sometimes pay twice when they hit the button again"


class ScriptedModel(BaseHTTPRequestHandler):
    def log_message(self, *arguments):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(body)
        if self.server.status != 200:
            self.send_response(self.server.status)
            self.end_headers()
            return
        answers = {key: {"type": "noul", "noul": self.server.likelihood(key)} for key in body["questions"]}
        if self.server.corrupt:
            answers.popitem()
        encoded = json.dumps({"answers": answers, "usage": {"input_tokens": 10}}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def scripted_likelihood(key: str) -> float:
    if key == "stakes" or key == "domain:billing_and_payments":
        return 0.9
    if key == "domains.billing_and_payments.03":
        return 0.8
    return 0.1


class DecisionModelBriefTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ScriptedModel)
        self.server.requests, self.server.status, self.server.corrupt = [], 200, False
        self.server.likelihood = scripted_likelihood
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        connection = self.directory / "connection.json"
        connection.write_text(json.dumps({
            "schemaVersion": 1, "baseUrl": f"http://127.0.0.1:{self.server.server_address[1]}", "model": "scripted",
            "revision": "abc", "timeoutMs": 10000, "maxRequestBytes": 1000000, "maxResponseBytes": 1000000,
        }), encoding="utf-8")
        environment = patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(connection),
                                              "SWAG_TRACE_DIR": str(self.directory / "traces")})
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("SWAG_LFG_CONNECTION_FILE", None)

    def test_model_catches_risk_the_rules_cannot_see(self):
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["basis"], "decision_model")
        self.assertTrue(brief["modelExecuted"])
        self.assertFalse(brief["qualified"])
        self.assertEqual(brief["stakes"], {"level": "elevated", "domains": ["billing_and_payments"]})
        self.assertEqual(brief["checks"][0]["id"], "domains.billing_and_payments.03")
        self.assertEqual(brief["checks"][0]["likelihood"], 0.8)
        self.assertEqual(brief["signals"]["decisionModel"]["model"], "scripted")
        self.assertEqual(brief["signals"]["decisionModel"]["revision"], "abc")

    def test_the_same_request_without_a_model_is_visibly_rules_only(self):
        with patch.dict(os.environ):
            os.environ.pop("SWAG_DECISION_MODEL_CONNECTION_FILE")
            brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["basis"], "rules_only")
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "not_configured"})

    def test_model_abstains_on_harmless_work_even_with_a_look_alike_word(self):
        self.server.likelihood = lambda key: 0.05
        brief = swag_brief.decision_brief(self.repo, "Fix the token parser in the billing-free CLI")
        self.assertEqual(brief["status"], "abstained")
        self.assertEqual(brief["checks"], [])
        self.assertFalse(brief["escalate"])

    def test_elevated_stakes_without_a_domain_still_escalates(self):
        self.server.likelihood = lambda key: 0.9 if key == "stakes" else 0.05
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["stakes"], {"level": "elevated", "domains": []})
        self.assertTrue(brief["escalate"])
        self.assertIn("get a review", brief["direction"])

    def test_policy_thresholds_decide_the_reading(self):
        self.server.likelihood = lambda key: 0.35 if key == "domain:search" else 0.39 if key == "stakes" else 0.05
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["routing"]["domains"], ["search"])
        self.assertEqual(brief["stakes"]["level"], "standard")

    def test_caller_supplied_elevated_domain_is_honored(self):
        self.server.likelihood = lambda key: 0.05
        brief = swag_brief.decision_brief(self.repo, REQUEST, domains=["billing_and_payments"])
        self.assertEqual(brief["stakes"]["domains"], ["billing_and_payments"])
        self.assertEqual(brief["status"], "selected")

    def test_unavailable_model_falls_back_to_rules_and_says_so(self):
        self.server.status = 500
        brief = swag_brief.decision_brief(self.repo, "Add Stripe billing")
        self.assertEqual(brief["basis"], "rules_only")
        self.assertFalse(brief["modelExecuted"])
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "unavailable"})
        self.assertEqual(brief["stakes"]["level"], "elevated")

    def test_a_missing_answer_is_not_accepted(self):
        self.server.corrupt = True
        brief = swag_brief.decision_brief(self.repo, "Add Stripe billing")
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "unavailable"})

    def test_request_goes_to_the_model_as_data_with_every_domain_asked(self):
        swag_brief.decision_brief(self.repo, REQUEST)
        first = self.server.requests[0]
        self.assertEqual(first["state"], {"request": REQUEST})
        self.assertEqual(first["model"], "scripted")
        self.assertIn("stakes", first["questions"])
        self.assertEqual(sum(key.startswith("domain:") for key in first["questions"]), 11)

    def test_large_schemas_are_sent_in_batches(self):
        questions = {f"q{index}": {"type": "noul", "instructions": "x"} for index in range(5)}
        result = probabilities({"request": "x"}, questions, 2)
        self.assertEqual(len(self.server.requests), 3)
        self.assertEqual(set(result["answers"]), set(questions))
        self.assertEqual(result["inputTokens"], 30)

    def test_non_loopback_endpoints_are_refused(self):
        connection = self.directory / "remote.json"
        connection.write_text(json.dumps({"schemaVersion": 1, "baseUrl": "http://8.8.8.8:80", "model": "m", "timeoutMs": 1,
                                          "maxRequestBytes": 1, "maxResponseBytes": 1}), encoding="utf-8")
        with patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(connection)}):
            with self.assertRaises(DecisionModelError):
                probabilities({"request": "x"}, {"q": {"type": "noul"}}, 1)


if __name__ == "__main__":
    unittest.main()
