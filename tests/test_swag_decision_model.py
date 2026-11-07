"""Decision-model brief checks over real local HTTP with a scripted model; these are software tests, not routing quality evidence."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
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
from swag_decision_model import DecisionModelError, choices

REQUEST = "people sometimes pay twice when they hit the button again"
BILLING = "Add Stripe billing to my Next.js app and make sure webhooks can't double charge customers"
SECRET = "test-credential-value"


def favoring(criteria: dict, option: str, weight: float) -> dict:
    rest = (1 - weight) / max(1, len(criteria) - 1)
    return {key: weight if key == option else rest for key in criteria}


def scripted_answer(question_id: str, criteria: dict) -> dict:
    if question_id == "stakes":
        return favoring(criteria, "elevated", 0.9)
    if question_id == "domain":
        return favoring(criteria, "billing_and_payments", 0.9)
    if question_id == "billing_and_payments":
        return favoring(criteria, "domains.billing_and_payments.03", 0.8)
    return favoring(criteria, "none", 0.9)


def harmless_answer(question_id: str, criteria: dict) -> dict:
    return favoring(criteria, "standard" if question_id == "stakes" else "none", 0.95)


class ScriptedSystemOne(BaseHTTPRequestHandler):
    def log_message(self, *arguments):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(body)
        if self.server.status != 200:
            self.send_response(self.server.status)
            self.end_headers()
            return
        answers = {key: {"type": "choice", "probabilities": self.server.answer(key, question["criteria"])}
                   for key, question in body["questions"].items()}
        if self.server.corrupt:
            answers.popitem()
        encoded = json.dumps({"answers": answers, "usage": {"input_tokens": 10}}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class ScriptedChat(BaseHTTPRequestHandler):
    """Answers like an OpenAI-compatible server: the first token's logprobs and no generated text."""

    def log_message(self, *arguments):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append({"path": self.path, "authorization": self.headers.get("Authorization"), "body": body})
        encoded = json.dumps(self.server.response(body)).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def first_token_response(top: list[tuple[str, float]]) -> dict:
    return {"choices": [{"logprobs": {"content": [{"token": top[0][0], "top_logprobs": [
        {"token": token, "logprob": logprob} for token, logprob in top]}]}}], "usage": {"prompt_tokens": 7}}


class Connected(unittest.TestCase):
    handler = ScriptedSystemOne

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.server.requests, self.server.status, self.server.corrupt = [], 200, False
        self.server.answer = scripted_answer
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        environment = patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(self.connect()),
                                              "SWAG_TRACE_DIR": str(self.directory / "traces")})
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("SWAG_LFG_CONNECTION_FILE", None)

    def connect(self, **extra) -> Path:
        connection = self.directory / "connection.json"
        connection.write_text(json.dumps({
            "schemaVersion": 1, "baseUrl": f"http://127.0.0.1:{self.server.server_address[1]}", "model": "scripted",
            "revision": "abc", "timeoutMs": 10000, "maxRequestBytes": 1000000, "maxResponseBytes": 1000000, **extra,
        }), encoding="utf-8")
        return connection


class DecisionModelBriefTests(Connected):
    def test_model_catches_risk_the_rules_cannot_see(self):
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["basis"], "decision_model")
        self.assertTrue(brief["modelExecuted"])
        self.assertFalse(brief["qualified"])
        self.assertEqual(brief["stakes"], {"level": "elevated", "domains": ["billing_and_payments"]})
        self.assertEqual(brief["checks"][0]["id"], "domains.billing_and_payments.03")
        self.assertAlmostEqual(brief["checks"][0]["likelihood"], 0.72)
        self.assertEqual(brief["signals"]["decisionModel"]["model"], "scripted")
        self.assertEqual(brief["signals"]["decisionModel"]["revision"], "abc")

    def test_the_same_request_without_a_model_is_visibly_rules_only(self):
        with patch.dict(os.environ):
            os.environ.pop("SWAG_DECISION_MODEL_CONNECTION_FILE")
            brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["basis"], "rules_only")
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "not_configured"})

    def test_model_abstains_on_harmless_work_even_with_a_look_alike_word(self):
        self.server.answer = harmless_answer
        brief = swag_brief.decision_brief(self.repo, "Fix the token parser in the billing-free CLI")
        self.assertEqual(brief["status"], "abstained")
        self.assertEqual(brief["checks"], [])
        self.assertFalse(brief["escalate"])

    def test_elevated_stakes_without_a_domain_still_escalates(self):
        self.server.answer = lambda key, criteria: favoring(criteria, "elevated" if key == "stakes" else "none", 0.9)
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["stakes"], {"level": "elevated", "domains": []})
        self.assertTrue(brief["escalate"])
        self.assertIn("get a review", brief["direction"])

    def test_policy_thresholds_decide_the_reading(self):
        def answer(key, criteria):
            if key == "stakes":
                return {"elevated": 0.49, "standard": 0.51}
            if key == "domain":
                return {option: 0.15 if option == "search" else 0.85 if option == "none" else 0.0 for option in criteria}
            return favoring(criteria, next(iter(criteria)), 0.9)
        self.server.answer = answer
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["routing"]["domains"], ["search"])
        self.assertEqual(brief["stakes"]["level"], "standard")

    def test_caller_supplied_elevated_domain_is_honored(self):
        def answer(key, criteria):
            return harmless_answer(key, criteria) if key in ("stakes", "domain") else favoring(criteria, next(iter(criteria)), 0.9)
        self.server.answer = answer
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

    def test_an_option_outside_the_question_is_not_accepted(self):
        self.server.answer = lambda key, criteria: {**favoring(criteria, next(iter(criteria)), 0.5), "invented": 0.1}
        brief = swag_brief.decision_brief(self.repo, "Add Stripe billing")
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "unavailable"})

    def test_request_goes_to_the_model_as_data_with_every_domain_offered(self):
        swag_brief.decision_brief(self.repo, REQUEST)
        first = self.server.requests[0]
        self.assertEqual(first["state"], {"request": REQUEST})
        self.assertEqual(first["model"], "scripted")
        self.assertEqual(set(first["questions"]["stakes"]["criteria"]), {"elevated", "standard"})
        self.assertEqual(len(first["questions"]["domain"]["criteria"]), 12)
        self.assertIn("none", first["questions"]["domain"]["criteria"])

    def test_a_brief_takes_few_questions(self):
        swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(sum(len(call["questions"]) for call in self.server.requests), 3)

    def test_a_named_stack_adds_checks_only_when_one_applies(self):
        (self.repo / "package.json").write_text(json.dumps({"dependencies": {"next": "15.0.0"}}), encoding="utf-8")
        brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertFalse([check["id"] for check in brief["checks"] if check["id"].startswith("nextjs.")])
        self.assertIn("none", self.server.requests[-1]["questions"]["nextjs"]["criteria"])

        def answer(key, criteria):
            return favoring(criteria, next(iter(criteria)), 0.9) if key == "nextjs" else scripted_answer(key, criteria)
        self.server.answer = answer
        brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertTrue([check["id"] for check in brief["checks"] if check["id"].startswith("nextjs.")])

    def test_large_schemas_are_sent_in_batches(self):
        self.server.answer = lambda key, criteria: favoring(criteria, "a", 0.9)
        questions = {f"q{index}": {"type": "choice", "instructions": "x", "criteria": {"a": "x", "b": "y"}} for index in range(5)}
        result = choices({"request": "x"}, questions, 2)
        self.assertEqual(len(self.server.requests), 3)
        self.assertEqual(set(result["answers"]), set(questions))
        self.assertEqual(result["inputTokens"], 30)

    def test_non_loopback_endpoints_are_refused(self):
        connection = self.directory / "remote.json"
        connection.write_text(json.dumps({"schemaVersion": 1, "baseUrl": "http://8.8.8.8:80", "model": "m", "timeoutMs": 1,
                                          "maxRequestBytes": 1, "maxResponseBytes": 1}), encoding="utf-8")
        with patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(connection)}):
            with self.assertRaises(DecisionModelError):
                choices({"request": "x"}, {"q": {"type": "choice", "instructions": "x", "criteria": {"a": "x", "b": "y"}}}, 1)

    def test_an_unknown_protocol_is_refused(self):
        with patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(self.connect(protocol="telepathy"))}):
            with self.assertRaises(DecisionModelError):
                choices({"request": "x"}, {"q": {"type": "choice", "instructions": "x", "criteria": {"a": "x", "b": "y"}}}, 1)


class FirstTokenTests(Connected):
    handler = ScriptedChat
    QUESTION = {"q": {"type": "choice", "instructions": "Pick one", "criteria": {"first": "one", "second": "two", "third": "three"}}}

    def setUp(self):
        super().setUp()
        (self.directory / "server.env").write_text(f"OTHER=1\nAPI_KEY={SECRET}\n", encoding="utf-8")
        self.server.response = lambda body: first_token_response([(" B", -0.1), (" A", -2.5), ("the", -3.0)])
        environment = patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(self.connect(
            protocol="chat_first_token", credentialFile="server.env", credentialVariable="API_KEY"))})
        environment.start()
        self.addCleanup(environment.stop)

    def test_labels_map_back_to_options_and_probabilities_sum_to_one(self):
        result = choices({"request": "x"}, self.QUESTION, 40)
        answer = result["answers"]["q"]
        self.assertEqual(max(answer, key=answer.get), "second")
        self.assertAlmostEqual(math.fsum(answer.values()), 1.0)
        self.assertLess(answer["third"], answer["first"])
        self.assertEqual(result["inputTokens"], 7)

    def test_the_model_writes_one_token_after_the_prompted_answer(self):
        choices({"request": "my request"}, self.QUESTION, 40)
        call = self.server.requests[0]
        self.assertEqual(call["path"], "/v1/chat/completions")
        self.assertEqual(call["authorization"], f"Bearer {SECRET}")
        body = call["body"]
        self.assertEqual(body["max_tokens"], 1)
        self.assertTrue(body["continue_final_message"])
        self.assertEqual(body["messages"][0]["content"], "request: my request")
        self.assertEqual(body["messages"][-1], {"role": "assistant", "content": "Answer:"})
        self.assertIn("A. first: one\nB. second: two\nC. third: three", body["messages"][1]["content"])

    def test_the_credential_never_reaches_the_result_or_the_request_body(self):
        result = choices({"request": "x"}, self.QUESTION, 40)
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn(SECRET, json.dumps(self.server.requests[0]["body"]))

    def test_a_brief_runs_through_this_protocol(self):
        self.server.response = lambda body: first_token_response([(" A", -0.05), (" B", -3.0)])
        brief = swag_brief.decision_brief(self.repo, REQUEST)
        self.assertEqual(brief["basis"], "decision_model")
        self.assertEqual(len(self.server.requests), 3)

    def test_a_malformed_response_falls_back_to_rules(self):
        self.server.response = lambda body: {"choices": []}
        brief = swag_brief.decision_brief(self.repo, "Add Stripe billing")
        self.assertEqual(brief["basis"], "rules_only")
        self.assertEqual(brief["signals"]["decisionModel"], {"state": "unavailable"})

    def test_a_missing_credential_is_refused_without_naming_it(self):
        with patch.dict(os.environ, {"SWAG_DECISION_MODEL_CONNECTION_FILE": str(self.connect(
                protocol="chat_first_token", credentialFile="missing.env", credentialVariable="API_KEY"))}):
            with self.assertRaises(DecisionModelError) as caught:
                choices({"request": "x"}, self.QUESTION, 40)
        self.assertNotIn("API_KEY", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
