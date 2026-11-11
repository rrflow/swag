#!/usr/bin/env python3
"""Make CI and branch state loud: comment on failing PRs, open an issue when main is red, flag leftovers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
from typing import Any
from urllib import request

API = "https://api.github.com"
CI_MARKER = "<!-- swag-repo-status:ci -->"
MAIN_RED_MARKER = "<!-- swag-repo-status:main-red -->"
LEDGER_MARKER = "<!-- swag-repo-status:ledger -->"
QUEUE_REF = re.compile(r"^gh-readonly-queue/[^/]+/pr-(\d+)-")
FAILED = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}
GRACE = timedelta(hours=24)


def safe(text: object) -> str:
    """Neutralize contributor-controlled text before it goes into Markdown."""
    return re.sub(r"[`<>\[\]|\r\n]", " ", str(text)).replace("@", "@​")[:120]


def failed_jobs(jobs: list[dict[str, Any]]) -> list[str]:
    return [job["name"] for job in jobs if job.get("conclusion") in FAILED]


def pull_numbers(run: dict[str, Any]) -> list[int]:
    numbers = [int(pull["number"]) for pull in run.get("pull_requests") or []]
    queued = QUEUE_REF.match(run.get("head_branch") or "")
    if queued:
        numbers.append(int(queued[1]))
    return sorted(set(numbers))


def ci_comment(run: dict[str, Any], jobs: list[dict[str, Any]]) -> str:
    sha = run["head_sha"][:7]
    if run["conclusion"] == "success":
        return f"{CI_MARKER}\n**CI passed** on `{sha}`. [View the run]({run['html_url']})"
    heading = "The merge queue rejected this PR" if run["event"] == "merge_group" else "CI failed"
    failed = "\n".join(f"- `{safe(name)}`" for name in failed_jobs(jobs)) or "- No job reported a failure; the run did not complete."
    return f"{CI_MARKER}\n## {heading} on `{sha}`\n\n{failed}\n\nThis PR cannot merge until the required checks pass. [View the run]({run['html_url']})"


def main_red_body(run: dict[str, Any], jobs: list[dict[str, Any]]) -> str:
    failed = "\n".join(f"- `{safe(name)}`" for name in failed_jobs(jobs)) or "- No job reported a failure; the run did not complete."
    return f"{MAIN_RED_MARKER}\n`main` failed CI at `{run['head_sha'][:7]}`.\n\n{failed}\n\n[View the run]({run['html_url']})"


def _age(stamp: str, now: datetime) -> timedelta:
    return now - datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def ledger_problems(pulls: list[dict[str, Any]], branches: list[dict[str, Any]], now: datetime) -> list[str]:
    """List what needs attention: conflicted or stuck PRs, and branches with no open PR."""
    problems = []
    for pull in pulls:
        label = f"#{pull['number']} {safe(pull['title'])}"
        settled = _age(pull["updated_at"], now) > GRACE
        if pull.get("mergeable_state") == "dirty":
            problems.append(f"{label}: has merge conflicts")
        elif pull.get("draft"):
            if settled:
                problems.append(f"{label}: draft with no activity for over a day")
        elif settled and not pull.get("auto_merge"):
            problems.append(f"{label}: auto-merge is not enabled")
        elif settled:
            problems.append(f"{label}: auto-merge is on but it has not merged (state: {safe(pull.get('mergeable_state'))})")
    heads = {pull["head"] for pull in pulls}
    for branch in branches:
        name = branch["name"]
        if name == "main" or name in heads or name.startswith("gh-readonly-queue/"):
            continue
        if _age(branch["committed_at"], now) > GRACE:
            problems.append(f"Branch `{safe(name)}` has no open PR and no commits for over a day")
    return problems


def ledger_body(problems: list[str], pulls: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| #{pull['number']} | {safe(pull['title'])} | {safe(pull.get('mergeable_state'))} | {'yes' if pull.get('auto_merge') else 'no'} |"
        for pull in pulls
    ) or "| none | | | |"
    items = "\n".join(f"- {item}" for item in problems)
    return f"{LEDGER_MARKER}\n## Needs attention\n\n{items}\n\n## Open PRs\n\n| PR | Title | State | Auto-merge |\n|---|---|---|---|\n{rows}"


class GitHub:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(f"{API}/repos/{self.repo}{path}", data=body, method=method, headers={
            "Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}", "X-GitHub-Api-Version": "2022-11-28"})
        with request.urlopen(req, timeout=30) as response:
            raw = response.read()
        return json.loads(raw) if raw else None

    def find_issue(self, marker: str) -> dict[str, Any] | None:
        issues = self.call("GET", "/issues?state=open&per_page=100")
        return next((issue for issue in issues if "pull_request" not in issue and marker in (issue.get("body") or "")), None)

    def set_issue(self, marker: str, title: str, body: str | None) -> None:
        """Open or update one issue for this marker, or close it when there is nothing to report."""
        issue = self.find_issue(marker)
        if body is None:
            if issue:
                self.call("PATCH", f"/issues/{issue['number']}", {"state": "closed", "state_reason": "completed"})
        elif issue:
            self.call("PATCH", f"/issues/{issue['number']}", {"body": body})
        else:
            self.call("POST", "/issues", {"title": title, "body": body})

    def upsert_comment(self, number: int, body: str, create: bool) -> None:
        comments = self.call("GET", f"/issues/{number}/comments?per_page=100")
        existing = next((comment for comment in comments if CI_MARKER in (comment.get("body") or "")), None)
        if existing:
            self.call("PATCH", f"/issues/comments/{existing['id']}", {"body": body})
        elif create:
            self.call("POST", f"/issues/{number}/comments", {"body": body})


def report_run(hub: GitHub, run_id: str) -> int:
    run = hub.call("GET", f"/actions/runs/{run_id}")
    if run["conclusion"] != "success" and run["conclusion"] not in FAILED:
        return 0
    jobs = hub.call("GET", f"/actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    passed = run["conclusion"] == "success"
    for number in pull_numbers(run):
        # A passing run only updates an earlier failure notice, so green PRs stay quiet.
        hub.upsert_comment(number, ci_comment(run, jobs), create=not passed)
    if run["event"] == "push" and run["head_branch"] == "main":
        hub.set_issue(MAIN_RED_MARKER, "main is red", None if passed else main_red_body(run, jobs))
    return 0


def report_ledger(hub: GitHub) -> int:
    pulls = []
    for listed in hub.call("GET", "/pulls?state=open&per_page=100"):
        detail = hub.call("GET", f"/pulls/{listed['number']}")
        pulls.append({"number": detail["number"], "title": detail["title"], "head": detail["head"]["ref"], "draft": detail["draft"],
                      "mergeable_state": detail.get("mergeable_state"), "auto_merge": detail.get("auto_merge"), "updated_at": detail["updated_at"]})
    branches = []
    for listed in hub.call("GET", "/branches?per_page=100"):
        commit = hub.call("GET", f"/commits/{listed['commit']['sha']}")
        branches.append({"name": listed["name"], "committed_at": commit["commit"]["committer"]["date"]})
    problems = ledger_problems(pulls, branches, datetime.now(timezone.utc))
    hub.set_issue(LEDGER_MARKER, "Branches and PRs need attention", ledger_body(problems, pulls) if problems else None)
    for problem in problems:
        print(f"::error::{problem}")
    return 1 if problems else 0


def main() -> int:
    hub = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    if sys.argv[1:] == ["run"]:
        return report_run(hub, os.environ["RUN_ID"])
    if sys.argv[1:] == ["ledger"]:
        return report_ledger(hub)
    raise SystemExit("Usage: swag_repo_status.py run|ledger")


if __name__ == "__main__":
    sys.exit(main())
