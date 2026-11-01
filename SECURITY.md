# Security policy

**Status:** active repository policy
**Owner:** Angryvibes LLC, the repository owner

## Supported versions

SWAG is pre-release. There is no supported-version matrix: only the current `main`
branch of this repository receives fixes. No controller, model or checkpoint from
this project is qualified for production use.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's private vulnerability reporting
for this repository (the repository's **Security** tab, then **Report a
vulnerability**). Do not open a public issue, pull request, or discussion for a
security report, and do not include secrets, credentials, or private data in a
report.

A report should state the affected component (CLI tool, decision service, MCP
bridge, operations UI, evidence viewer, policy configuration, or documentation),
the revision tested, exact steps to reproduce, and the observed impact.

Report credentials or private data found in this repository or its history the same
way.

## Response

The repository owner acknowledges a report, then confirms or declines the finding.
The fix lands through a normal pull request. The reporter is credited in the pull
request unless they ask not to be.

## Scope notes

- `tools/swag_decision_service.py` and `tools/swag_ops_ui.py` bind to `127.0.0.1` by
  default. They are local tools and are not hardened for direct network exposure.
- Preview events stay local until explicitly published. They omit prompt text,
  responses, repository paths and credentials.
- Training data requires provenance, consent and independent review. Reports that
  show a way past dataset redaction or admission checks are in scope.
