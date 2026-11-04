"""Rules-only decision brief checks; these are software tests, not routing quality evidence."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import boundary_controller as bc
import swag
import swag_brief
from swag_lfg import LfgBridgeError
import swag_mcp_server as mcp

BILLING = "Add Stripe billing to my Next.js app and make sure webhooks can't double charge customers"


def lfg_result(effort: str) -> dict:
    return {"status": "available", "observation": {
        "analyzer": "deterministic-rules", "complexity": {"bracket": "simple"},
        "suggestedRole": "fast", "suggestedEffort": effort, "assessmentSha256": "a" * 64,
    }}


class BriefTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        environment = patch.dict(os.environ, {"SWAG_TRACE_DIR": str(self.repo / "traces")})
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("SWAG_LFG_CONNECTION_FILE", None)

    def test_billing_request_surfaces_the_webhook_check(self):
        brief = swag_brief.decision_brief(self.repo, BILLING)
        identifiers = [check["id"] for check in brief["checks"]]
        self.assertEqual(brief["status"], "selected")
        self.assertLessEqual(len(identifiers), 7)
        self.assertIn("domains.billing_and_payments.03", identifiers[:3])
        self.assertEqual(brief["stakes"], {"level": "elevated", "domains": ["billing_and_payments"]})
        self.assertTrue(brief["escalate"])

    def test_naming_a_stack_is_not_evidence_for_its_questions(self):
        (self.repo / "package.json").write_text(json.dumps({"dependencies": {"next": "15.0.0"}}), encoding="utf-8")
        identifiers = [check["id"] for check in swag_brief.decision_brief(self.repo, BILLING)["checks"]]
        self.assertIn("nextjs.route_handlers_and_proxy.01", identifiers)
        self.assertFalse([identifier for identifier in identifiers if identifier.startswith("nextjs.css_images_fonts")])

    def test_account_security_request_is_elevated_without_an_exact_alias(self):
        brief = swag_brief.decision_brief(self.repo, "Add password reset and make sure old sessions get revoked")
        self.assertEqual(brief["status"], "selected")
        self.assertEqual(brief["stakes"]["domains"], ["iam"])
        self.assertTrue(all(check["id"].startswith("domains.iam.") for check in brief["checks"]))

    def test_impersonation_request_surfaces_the_impersonation_check(self):
        brief = swag_brief.decision_brief(self.repo, "Let support staff log in as a customer to debug their account")
        self.assertIn("privileged_access_management", brief["stakes"]["domains"])
        self.assertIn("domains.privileged_access_management.13", [check["id"] for check in brief["checks"]])

    def test_mentioning_users_alone_does_not_elevate_stakes(self):
        brief = swag_brief.decision_brief(self.repo, "Let users upload profile pictures to S3")
        self.assertEqual(brief["stakes"], {"level": "standard", "domains": []})
        self.assertFalse(brief["escalate"])
        self.assertEqual(brief["checks"][0]["id"], "domains.files_and_media.01")
        self.assertEqual(brief["routing"]["domains"], ["files_and_media"])

    def test_alias_with_no_fitting_question_is_dropped(self):
        brief = swag_brief.decision_brief(self.repo, "Show the user's name in the header")
        self.assertEqual(brief["status"], "abstained")
        self.assertEqual(brief["routing"]["domains"], [])

    def test_look_alike_phrases_do_not_raise_a_billing_alarm(self):
        requests = (
            "git checkout the release branch and rebase",
            "Who is in charge of the deploy script?",
            "Add a GraphQL subscription for live scores",
        )
        for request in requests:
            with self.subTest(request):
                brief = swag_brief.decision_brief(self.repo, request)
                self.assertEqual(brief["stakes"]["level"], "standard")
                self.assertNotIn("billing_and_payments", brief["routing"]["domains"])

    def test_real_billing_terms_stay_elevated(self):
        for request in ("Add a checkout page with Stripe", "Add a monthly subscription plan", "Charge the card on signup"):
            with self.subTest(request):
                brief = swag_brief.decision_brief(self.repo, request)
                self.assertIn("billing_and_payments", brief["stakes"]["domains"])

    def test_single_shared_word_does_not_select_an_unnamed_stack(self):
        (self.repo / "tsconfig.json").write_text("{}", encoding="utf-8")
        brief = swag_brief.decision_brief(self.repo, "Add a chatbot that answers from our docs and can call tools")
        self.assertIn("llm_application", brief["routing"]["domains"])
        self.assertTrue(brief["checks"])
        self.assertFalse([check["id"] for check in brief["checks"] if check["id"].startswith("typescript.")])

    def test_small_requests_abstain(self):
        (self.repo / "tsconfig.json").write_text("{}", encoding="utf-8")
        for request in ("Fix a typo in the README", "Rename a CSS class on the landing page", "Make it better"):
            with self.subTest(request):
                self.assertEqual(swag_brief.decision_brief(self.repo, request)["status"], "abstained")

    def test_caller_supplied_elevated_domain_is_honored(self):
        brief = swag_brief.decision_brief(self.repo, "zzzz qqqq", domains=["billing_and_payments"])
        self.assertEqual(brief["stakes"]["level"], "elevated")
        self.assertEqual(brief["status"], "selected")

    def test_brief_is_compact_and_accounts_for_what_it_omits(self):
        brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual(brief["omittedCount"], brief["consideredCount"] - len(brief["checks"]))
        self.assertGreater(brief["omittedCount"], 0)
        self.assertLess(len(json.dumps(brief)), 8000)

    def test_checks_stay_inside_the_composed_options(self):
        composed = mcp._run_compose_battery({"repo": str(self.repo), "intent_text": BILLING, "has_test_harness": True})
        options = {question["id"] for question in composed["questions"]}
        brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual(brief["consideredCount"], len(options))
        self.assertLessEqual({check["id"] for check in brief["checks"]}, options)

    def test_abstains_when_nothing_stands_out(self):
        brief = swag_brief.decision_brief(self.repo, "zzzz qqqq")
        self.assertEqual(brief["status"], "abstained")
        self.assertEqual(brief["checks"], [])
        self.assertFalse(brief["escalate"])
        self.assertEqual(brief["stakes"]["level"], "standard")
        self.assertIn("no_specific_checks", brief["reasonIds"])

    def test_same_input_gives_same_brief(self):
        first = swag_brief.decision_brief(self.repo, BILLING)
        second = swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual(first, second)

    def test_brief_writes_nothing_to_the_project(self):
        swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual([path.name for path in self.repo.iterdir() if path.name != "traces"], [])

    def test_empty_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            swag_brief.decision_brief(self.repo, "   ")

    def test_lfg_is_skipped_unless_configured(self):
        with patch.object(swag_brief, "assess") as assess:
            brief = swag_brief.decision_brief(self.repo, BILLING)
        assess.assert_not_called()
        self.assertEqual(brief["signals"]["lfg"], {"state": "not_configured"})

    def test_low_effort_lfg_signal_conflicts_with_elevated_stakes(self):
        with patch.dict(os.environ, {"SWAG_LFG_CONNECTION_FILE": "configured"}), \
                patch.object(swag_brief, "assess", return_value=lfg_result("low")):
            brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual(brief["signals"]["lfg"]["suggestedEffort"], "low")
        self.assertEqual(brief["signals"]["conflicts"], ["lfg_low_effort_on_elevated_stakes"])
        self.assertTrue(brief["escalate"])

    def test_low_effort_lfg_signal_does_not_conflict_with_standard_stakes(self):
        with patch.dict(os.environ, {"SWAG_LFG_CONNECTION_FILE": "configured"}), \
                patch.object(swag_brief, "assess", return_value=lfg_result("low")):
            brief = swag_brief.decision_brief(self.repo, "zzzz qqqq")
        self.assertEqual(brief["signals"]["conflicts"], [])

    def test_lfg_failure_does_not_fail_the_brief(self):
        with patch.dict(os.environ, {"SWAG_LFG_CONNECTION_FILE": "configured"}), \
                patch.object(swag_brief, "assess", side_effect=LfgBridgeError("unavailable")):
            brief = swag_brief.decision_brief(self.repo, BILLING)
        self.assertEqual(brief["signals"]["lfg"], {"state": "unavailable"})
        self.assertEqual(brief["status"], "selected")

    def test_mcp_tool_returns_the_brief(self):
        listed = mcp._handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertIn("decision_brief", [tool["name"] for tool in listed["result"]["tools"]])
        response = mcp._handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "decision_brief", "arguments": {"repo": str(self.repo), "intent_text": BILLING}}})
        brief = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(brief["schema"], "swag.decision-brief/v1")

    def test_cli_brief_uses_the_saved_intent(self):
        swag.initialize(self.repo, BILLING, project="test-project")
        brief = swag.brief(self.repo)
        self.assertEqual(brief["stakes"]["level"], "elevated")

    def test_cli_brief_works_without_a_profile(self):
        brief = swag.brief(self.repo, BILLING)
        self.assertEqual(brief["status"], "selected")
        with self.assertRaises(ValueError):
            swag.brief(self.repo)


class YamlCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "policy.yaml"
        self.path.write_text("value: 1\n", encoding="utf-8")

    def test_changing_a_loaded_mapping_does_not_change_the_next_load(self):
        bc._load_yaml(self.path)["value"] = 2
        self.assertEqual(bc._load_yaml(self.path)["value"], 1)

    def test_an_edited_file_is_read_again(self):
        bc._load_yaml(self.path)
        self.path.write_text("value: 22\n", encoding="utf-8")
        self.assertEqual(bc._load_yaml(self.path)["value"], 22)


class StackDetectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.registry = bc._load_yaml(bc.STACK_REGISTRY_FILE)

    def test_next_dependency_detects_nextjs_without_a_root_app_directory(self):
        (self.repo / "package.json").write_text(json.dumps({"dependencies": {"next": "15.0.0"}}), encoding="utf-8")
        (self.repo / "src" / "app").mkdir(parents=True)
        self.assertIn("nextjs", bc.detect_stacks(self.repo, self.registry)[0])

    def test_typescript_next_config_detects_nextjs(self):
        (self.repo / "next.config.ts").write_text("export default {}\n", encoding="utf-8")
        self.assertIn("nextjs", bc.detect_stacks(self.repo, self.registry)[0])

    def test_the_word_next_does_not_name_nextjs(self):
        stacks, _ = bc.detect_stacks_from_intent(self.registry, "What should I do next on the dashboard?", [])
        self.assertNotIn("nextjs", stacks)

    def test_next_js_still_names_nextjs(self):
        for request in ("Add billing to my Next.js app", "Build it with nextjs"):
            with self.subTest(request):
                self.assertIn("nextjs", bc.detect_stacks_from_intent(self.registry, request, [])[0])


if __name__ == "__main__":
    unittest.main()
