# SWAG - your project's System One controller

SWAG answers the quick decisions in a software project: yes or no, which option, how well. It
answers fast and in a fixed shape, says how sure it is, and abstains when it isn't sure enough.
It follows the facts, hard rules and preferences you give it, and every decision shows why it
came out the way it did.

SWAG is part of the [Reason Ready Governance (RRG) suite](docs/rrg-suite.md). It runs on its own
or inside [RRFlow](docs/glossary.md), which owns plans, permissions and execution. It is
pre-release and source-available under the [Business Source License 1.1](LICENSE).

## What a decision looks like

You send a state (any text or JSON) and some questions. Each question is one of three types:

| Type | Question | Answer |
|---|---|---|
| binary | "Could this change move money?" | The probability of yes, and SWAG's yes or no |
| choice | "Which test layout fits: directories, groups or flat?" | One option, with a probability for each |
| score | "How many of the four CI check categories run?" | A level from 0 to 4, with a probability for each |

SWAG returns:

- the model's raw probabilities, in the same format TypeSafe's Jev uses, so Jev clients work unchanged
- SWAG's decision for each question: `answered`, `abstained`, `required` by a hard rule, or
  `defaulted` by a rule after abstaining
- which rules and preferences applied, and which layer each came from
- suggestions for what to do next
- the time each step took

The full format is in the [decision contract](docs/decision-contract.md).

## Try it

Python 3.10 or newer:

```sh
python -m pip install -r requirements.txt
python tools/swag.py decide --template python_delivery_review --state "pyproject.toml lists pytest under dependencies"
```

With no model connected, every question abstains with reason `no_engine`, and you get the
template's suggestions for what to share. That is the honest answer without a model.

To connect a model, point `SWAG_DECISION_MODEL_CONNECTION_FILE` at a small JSON file naming a
model server on this machine. It can be vLLM, a llama.cpp `llama-server`, SGLang, or any
`/v1/systemone` server. See [connecting a model](docs/decision-contract.md#connecting-a-model).

Run SWAG as a server for your tools and agents:

```sh
python tools/swag_server.py          # POST http://127.0.0.1:8792/v1/systemone
```

See every decision, with its probabilities, rules, preferences and timings:

```sh
cd ui && npm ci && npm run dev       # http://127.0.0.1:8891/dev.html, Decisions panel
```

## Make it yours: facts, rules and preferences

Four layers shape each decision, merged in this order:

1. the knowledge **template**
2. your **project** (`.swag/layer.json`)
3. your **operator** profile ([`config/aiddevspec/default.yaml`](config/aiddevspec/default.yaml))
4. the **request** itself

| Part | What it does |
|---|---|
| Facts | Statements with a source and an optional freshness window. Fresh facts reach the model; stale ones are listed and never used |
| Hard rules | Only narrow what SWAG may answer. They forbid options, require an answer, raise the confidence floor, or set the answer to use when unsure. A later layer cannot remove them |
| Preferences | Soft settings: how sure SWAG must be before answering, the yes threshold, which option wins a near tie, how many suggestions to return |

```json
{"rules": [{"id": "money_is_risky", "question": "risky", "require": "true",
            "why": "Every change near billing gets a careful review."}],
 "preferences": {"abstainBelow": {"choice": 0.4}, "prefer": {"layout": ["groups"]}}}
```

When SWAG runs inside RRFlow, RRFlow's second brain is meant to supply these layers. That
integration is planned, not built.

## Where it stands

| Area | State |
|---|---|
| Binary, choice and score decisions from a model | Working through `chat_first_token` and `systemone`. Software-tested; quality not yet qualified |
| Facts, hard rules, preferences, suggestions | Working, with tests |
| Decision server, decision log, Decisions panel | Working, local |
| Comparison with Jev, Clef and KnowLine | [Bench](bench/README.md) in the repo. [Results so far](docs/competitors.md): SWAG's current model trails, and is badly overconfident |
| Docker, llama.cpp setup, one-command install | Not built |
| RRFlow second-brain layers | Not built |
| A model that beats Jev at 9 GB | Not built. See the [plan](docs/system-one-plan.md), workstream W6 |

The [System One plan](docs/system-one-plan.md) has the workstreams and milestones. The
[docs index](docs/index.md) lists every document by whether it is current, reference, evidence
or history.

## Other entry points

- `python tools/swag.py brief --intent "..."`: the older decision brief. It picks up to seven
  cited checks and a stakes call for a request; it is also available as the MCP tool
  `decision_brief`.
- `python tools/swag_mcp_server.py`: the MCP bridge for coding agents. It offers
  `decision_brief`, `knowledge_preview`, `validate_template_decision` and status tools.
- `python tools/swag.py preview`, `init`, `doctor` and `publish`: the legacy rules-only preview,
  and sending preview events to RROFLOW. See the [former README baseline](docs/history/readme-system-one-baseline.md).
- [Naming checker](docs/reference/naming-checker.md) for RRFLOW keys.

## Develop

```sh
python -m unittest discover -s tests -p "test_*.py"
python tools/check_doc_links.py
cd ui && npm ci && npm test
```

Work on one short branch, open a pull request, and turn on auto-merge. It merges when `ci-gate`
passes. See [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

This repository holds source, configuration, tests and documentation. Session logs, datasets,
model weights and `.swag/` state stay local. Two small evidence files under
`files/controller_experiments/` are included because tools read them.

## Security and license

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

SWAG is licensed under the [Business Source License 1.1](LICENSE), with a grant for
non-commercial production use. It is source-available, not open source. Each version converts
to the Apache License 2.0 four years after it is first published. The license covers this
repository only, not other RRG products.
