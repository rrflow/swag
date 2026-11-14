# Repository Guidelines

## Project Structure & Module Organization

SWAG is a System One controller: it answers binary (`noul`), choice and score questions in the SystemOne wire format, abstains when unsure, and applies facts, hard rules and preferences from four layers. It is part of the Reason Ready Governance (RRG) suite; see `docs/rrg-suite.md`. The only active plan is `docs/system-one-plan.md`; the contract is `docs/decision-contract.md`; terms are defined in `docs/glossary.md`. Documents under `docs/history/` and `docs/evidence/` are records, not instructions.

- `tools/`: Python tools. The decision path is `swag_systemone.py` (wire format), `swag_decide.py` (layers and decisions), `swag_decision_model.py` (engines), `swag_server.py` (HTTP) and `swag_decision_log.py` (the log the devtools read).
- `bench/`: the competitor comparison (Jev, Clef, KnowLine, SWAG over the same `/v1/systemone` requests). `bench/data/` and `bench/results/` stay local.
- `ui/`: the developer workspace (`dev.html`), including the Decisions panel.
- `config/`: shipped YAML policies, runtime/provider templates, question sets, and training configuration. Source datasets live in `config/training/real_sources/`.
- `tests/fixtures/`: naming-check input lists, including intentional violations.
- `boundaries/`: naming reviews and reference documentation.
- `files/`: generated reports, runtime artifacts, datasets, and training runbooks. Local-only, except the evidence files allowlisted in `.gitignore`.
- `chat-archive/` and `chat-candidates/`: historical conversations and draft material. Local-only and ignored; never commit them. Keep implementation changes focused on active code and configuration.

## Build, Test, and Development Commands

Run from the repository root with Python 3.10+. There is no separate application build step.

- `python -m pip install -r requirements.txt`: install runtime and test dependencies; the naming checker itself uses only the standard library.
- `python -m unittest discover -s tests -p "test_*.py" -v`: run the test suite.
- `cd ui; npm ci; npm test`: build and test the evidence viewer.
- `python tools/check_naming.py --no-user --dry-run`: inspect shipped naming configuration without user overrides.
- `python tools/check_naming.py --no-user --kind lane_key tests/fixtures/lane_keys.txt`: validate the lane fixture.
- `python tools/check_naming.py --no-user tests/fixtures/sample_seam_keys.txt`: exercise seam-name validation.
- `python tools/swag_runtime_bootstrap.py --pretty`: inspect merged runtime configuration.
- `python tools/boundary_controller.py --pretty --intent-text "secure AI app architecture"`: exercise controller routing.
- `python tools/swag.py decide --template python_delivery_review --state "..."`: ask a template's binary, choice and score questions.
- `python tools/swag_server.py`: serve `POST /v1/systemone` on 127.0.0.1:8792.
- `cd ui; npm run dev`: the developer workspace at http://127.0.0.1:8891/dev.html.
- `python tools/check_doc_links.py`: fail on dead relative links in Markdown.
- `python tools/swag.py brief --repo . --intent "Add password reset"`: get the older compact decision brief for one request.
- `python tools/swag_ops_ui.py --host 127.0.0.1 --port 8790`: the training operations UI (training jobs only; not the developer workspace).

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, type annotations, `snake_case` functions, and uppercase constants. Use two-space YAML indentation. No formatter or linter configuration is provided.

Follow `config/rrflow.naming.yaml`: lane/seam keys use `snake_case`, payload fields use lowerCamelCase, and names such as `new_*` and `*_v2` are prohibited. Keep naming overrides within the checker's supported YAML subset.

## Testing Guidelines

Tests use `unittest`, and CI runs them with the evidence viewer tests and a secret scan. No numeric coverage target is configured. Behavior changes require reproducible checks and relevant fixtures. Fixture files use descriptive `.txt` names, one key per line. Intentional violations should produce diagnostics and exit code 1 in error mode; do not expect every fixture to pass. Record commands and expected results in the PR.

## Commit & Pull Request Guidelines

Use concise imperative commit subjects, such as `Fix boundary routing fallback`. PRs should explain behavior changes, link relevant issues, list validation results, and include screenshots for UI changes.

Work on one short branch at a time. `main` only accepts a pull request once `ci-gate` passes. After opening the PR, run `gh pr merge --auto`; it merges when green and its branch is deleted. The `Repo status` workflow comments on failing PRs, opens a `main is red` issue, and keeps one issue listing conflicted or stuck PRs and leftover branches. Treat any of those as work to finish.

## Security & Configuration

Use `.env.example` as the configuration reference; keep credentials out of committed files. Preserve dataset redaction and provenance checks when changing training workflows.

This repository is public-facing. Do not commit session logs, private hostnames, tailnet addresses, or home-directory paths; `tests/test_public_boundary.py` checks the tree. Report vulnerabilities as described in `SECURITY.md`.

## Licensing

SWAG is source-available under BSL 1.1 (`LICENSE`). Do not describe it as open source.
