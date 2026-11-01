# Contributing to SWAG

SWAG is pre-release and part of the
[Reason Ready Governance (RRG) suite](docs/rrg-suite.md). Bug reports and focused
pull requests are welcome. Please open an issue before starting a large change.
Report security issues as described in [SECURITY.md](SECURITY.md), not in a public
issue.

## Set up

Use Python 3.10 or later and Node.js 22 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Check your change

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python tools/check_naming.py --no-user --kind lane_key tests/fixtures/lane_keys.txt
cd ui; npm ci; npm test
```

Some naming fixtures contain intentional violations and exit with code 1. See
[AGENTS.md](AGENTS.md) for project structure, style and naming rules.

## Pull requests

Explain the behavior change, link related issues, list the commands you ran with
their results, and include screenshots for UI changes. Claims about model quality,
latency or memory need retained evidence; see
[routing data and evaluation](docs/routing-data-and-evaluation.md).

## Data and privacy

Do not commit session logs, credentials, private hostnames or home-directory paths.
Training data needs provenance, consent and independent review before it can be
admitted.

## Licensing

Contributions are submitted under the repository's [license](LICENSE). The project
owner may ask you to sign a contributor agreement before merging.
