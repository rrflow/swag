"""Repository status reporting: what gets flagged, and that contributor text cannot inject Markdown or mentions."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import swag_repo_status as status

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
OLD = (NOW - timedelta(days=3)).isoformat()
FRESH = (NOW - timedelta(hours=1)).isoformat()


def run(conclusion="failure", event="pull_request", branch="feature"):
    return {"conclusion": conclusion, "event": event, "head_branch": branch, "head_sha": "abcdef1234", "html_url": "https://example.test/run",
            "pull_requests": [{"number": 7}]}


def pull(**changes):
    base = {"number": 7, "title": "Change", "head": "feature", "draft": False, "mergeable_state": "clean", "auto_merge": {"enabled": True}, "updated_at": FRESH}
    return {**base, **changes}


JOBS = [{"name": "python (ubuntu-latest, 3.10)", "conclusion": "failure"}, {"name": "secret-scan", "conclusion": "success"}]


class RunReportTests(unittest.TestCase):
    def test_failure_names_only_the_failing_jobs(self):
        comment = status.ci_comment(run(), JOBS)
        self.assertIn("CI failed", comment)
        self.assertIn("python (ubuntu-latest, 3.10)", comment)
        self.assertNotIn("secret-scan", comment)
        self.assertIn(status.CI_MARKER, comment)

    def test_a_cancelled_job_counts_as_failed(self):
        self.assertEqual(status.failed_jobs([{"name": "a", "conclusion": "cancelled"}]), ["a"])

    def test_merge_queue_rejection_says_so(self):
        self.assertIn("merge queue rejected", status.ci_comment(run(event="merge_group"), JOBS))

    def test_merge_queue_run_maps_back_to_its_pull_request(self):
        queued = run(event="merge_group", branch="gh-readonly-queue/main/pr-42-abc123")
        queued["pull_requests"] = []
        self.assertEqual(status.pull_numbers(queued), [42])

    def test_a_pass_is_reported_as_a_pass(self):
        self.assertIn("CI passed", status.ci_comment(run("success"), []))

    def test_main_red_issue_lists_failures(self):
        body = status.main_red_body(run(event="push", branch="main"), JOBS)
        self.assertIn(status.MAIN_RED_MARKER, body)
        self.assertIn("python (ubuntu-latest, 3.10)", body)


class LedgerTests(unittest.TestCase):
    def problems(self, pulls=(), branches=()):
        return status.ledger_problems(list(pulls), list(branches), NOW)

    def test_a_fresh_pr_with_auto_merge_is_quiet(self):
        self.assertEqual(self.problems([pull()], [{"name": "feature", "committed_at": OLD}, {"name": "main", "committed_at": OLD}]), [])

    def test_conflicts_are_flagged_immediately(self):
        self.assertIn("merge conflicts", self.problems([pull(mergeable_state="dirty")])[0])

    def test_a_settled_pr_without_auto_merge_is_flagged(self):
        self.assertIn("auto-merge is not enabled", self.problems([pull(auto_merge=None, updated_at=OLD)])[0])

    def test_a_settled_pr_stuck_with_auto_merge_is_flagged(self):
        self.assertIn("has not merged", self.problems([pull(mergeable_state="blocked", updated_at=OLD)])[0])

    def test_a_stale_draft_is_flagged(self):
        self.assertIn("draft", self.problems([pull(draft=True, auto_merge=None, updated_at=OLD)])[0])

    def test_a_leftover_branch_is_flagged(self):
        self.assertIn("no open PR", self.problems([], [{"name": "old-work", "committed_at": OLD}])[0])

    def test_a_branch_pushed_today_gets_time_to_open_a_pr(self):
        self.assertEqual(self.problems([], [{"name": "new-work", "committed_at": FRESH}]), [])

    def test_merge_queue_branches_are_ignored(self):
        self.assertEqual(self.problems([], [{"name": "gh-readonly-queue/main/pr-1-abc", "committed_at": OLD}]), [])


class SafetyTests(unittest.TestCase):
    def test_contributor_text_cannot_inject_markdown(self):
        cleaned = status.safe("[x](http://evil) <img> `code`|\nnext")
        for character in "[]<>`|\n":
            self.assertNotIn(character, cleaned)

    def test_mentions_cannot_notify_anyone(self):
        self.assertNotIn("@someone", status.safe("@someone please"))

    def test_a_malicious_pr_title_stays_inert_in_the_ledger(self):
        body = status.ledger_body(["x"], [pull(title="<!-- swag-repo-status:ledger --> @everyone")])
        self.assertEqual(body.count(status.LEDGER_MARKER), 1)
        self.assertNotIn("@everyone", body)


if __name__ == "__main__":
    unittest.main()
