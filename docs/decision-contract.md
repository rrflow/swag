# Decision contract

How to ask SWAG for a decision, what comes back, and how facts, hard rules and preferences
shape it. The code is [`tools/swag_systemone.py`](../tools/swag_systemone.py) (wire format),
[`tools/swag_decide.py`](../tools/swag_decide.py) (layers and decisions) and
[`tools/swag_server.py`](../tools/swag_server.py) (HTTP and logging).

## The three decision types

SWAG uses the SystemOne wire format that TypeSafe's Jev, Cloudflare's Clef and KnowLine also
use, so any client written for one of them can call SWAG unchanged.

| SWAG name | Wire `type` | `criteria` | The model returns |
|---|---|---|---|
| binary | `noul` | optional `{"true": "...", "false": "..."}` | `noul`: probability the answer is yes |
| choice | `choice` | 2-255 named options `{"key": "description"}` | `choice`, `probabilities` per key, `confidence` |
| score | `score` | 2-255 levels `["level 0", "level 1", ...]` | `score` (expected level), `probabilities` per level, `legend`, `confidence` |

A score is an ordinal level with a probability for each level. It is not itself a calibrated
probability, and `score` is the expected level under those probabilities.

`confidence` follows TypeSafe's published adapter: for a choice, the top probability rescaled
from uniform (0) to certain (1); for a score, one minus the spread around the most likely level
relative to a uniform spread. For a binary question SWAG uses the choice formula over yes and no,
so 0.5/0.5 is confidence 0 and 1.0/0.0 is confidence 1.

## Request

```json
{
  "model": "swag",
  "state": {"request": "Add Stripe checkout", "files": ["billing/webhooks.py"]},
  "questions": {
    "risky": {"type": "noul", "instructions": "Could this change move money or expose customer data?"},
    "layout": {"type": "choice", "instructions": "Which test layout fits?",
               "criteria": {"directories": "Separate directories", "groups": "One tree with groups"}},
    "ci": {"type": "score", "instructions": "How many CI check categories run?",
           "criteria": ["none", "one", "two", "three", "four"]}
  },
  "swag": {
    "template": "python_delivery_review",
    "preferences": {"abstainBelow": {"choice": 0.4}},
    "facts": [{"id": "uses_stripe", "statement": "The project bills through Stripe.", "source": "package.json"}],
    "rules": [{"id": "money_is_risky", "question": "risky", "whenFact": "uses_stripe", "require": "true",
               "why": "Every change near billing gets a careful review."}]
  }
}
```

- `state` is anything JSON: text, an object, or a chat transcript. It is material to evaluate;
  instructions written inside it are not followed.
- `questions` holds 1-64 questions keyed by id.
- `swag` is optional. Jev clients never send it.
  - `template` names a [knowledge template](../config/knowledge/templates/). With a template and no
    `questions`, SWAG asks the template's own questions.
  - `facts`, `rules` and `preferences` form the request layer described below.

## Response

```json
{
  "id": "swag-...",
  "model": "swag",
  "answers": {"risky": {"type": "noul", "noul": 0.83}, "layout": {"type": "choice", "choice": "groups", "...": "..."}},
  "usage": {"input_tokens": 412, "output_tokens": 0},
  "swag": {
    "schema": "swag.decision/v1",
    "decisions": {
      "risky": {"mode": "binary", "status": "required", "value": true, "reason": "hard_rule", "rules": ["money_is_risky"]},
      "layout": {"mode": "choice", "status": "answered", "value": "groups", "confidence": 0.61,
                 "abstainBelow": 0.4, "abstainBelowOrigin": "request", "probability": 0.81, "engineMs": 38.2}
    },
    "suggestions": [{"question": "layout", "when": "groups", "text": "Keep one test tree and mark groups...", "byRule": false}],
    "engine": {"consulted": true, "model": "...", "protocol": "chat_first_token", "rotations": true},
    "timings": {"composeMs": 0.2, "engineMs": 81.0, "decideMs": 0.1},
    "effective": {"digest": "...", "facts": [], "staleFacts": [], "rules": [], "ruleConflicts": [],
                  "preferences": {}, "preferenceOrigins": {}}
  }
}
```

`answers` is exactly what the model said, in the shape Jev clients expect. SWAG never edits it.
Everything SWAG adds is in `swag`:

| Decision `status` | Meaning |
|---|---|
| `answered` | The model decided, above the confidence floor, within the rules |
| `abstained` | No decision. `reason` says why: `below_confidence_floor`, `no_engine`, `all_options_forbidden`, `rules_require_different_answers` and others |
| `required` | A hard rule set the answer. The model was not asked this question |
| `defaulted` | The model abstained, and a rule's `onAbstain` answer was used. `abstainReason` keeps why |

A question answered by a rule never appears in `answers`, so a rule's answer is never presented
as the model's.

## Layers: facts, hard rules and preferences

Four layers shape every decision, merged in this order:

| Order | Layer | Where it comes from |
|---|---|---|
| 1 | `template` | The knowledge template named in the request |
| 2 | `project` | `<repo>/.swag/layer.json` (the server's `--repo`, or the CLI's `--repo`) |
| 3 | `operator` | `operator_preferences`, `operator_rules` and `operator_facts` in [AIDevSpec](../config/aiddevspec/default.yaml), or the file named by `SWAG_AIDEVSPEC` |
| 4 | `request` | The request's `swag` block |

Each layer is `{"facts": [...], "rules": [...], "preferences": {...}}`. When RRFlow is connected,
its second brain is expected to supply the project and operator layers in this same shape. That
integration is workstream W7 of the [System One plan](system-one-plan.md).

**Facts** are statements about the project.

```json
{"id": "uses_stripe", "statement": "The project bills through Stripe.", "source": "package.json",
 "observedAt": "2026-11-01", "freshForDays": 30}
```

- Fresh facts are added to the state the model reads, as `facts`.
- A fact past its freshness window is listed in `staleFacts` and never used.
- A later layer replaces a fact with the same id, as a newer observation.

**Hard rules** only ever narrow.

```json
{"id": "no_flat_tests", "question": "layout", "forbid": ["flat"], "why": "Our runner needs groups."}
```

| Effect | What it does |
|---|---|
| `forbid` | Removes options. The remaining probabilities are rescaled to sum to one |
| `require` | Sets the answer. The model is not asked |
| `abstainBelow` | A confidence floor no preference can lower |
| `onAbstain` | The answer to use when the model abstains |
| `whenFact` | The rule applies only while that fact is fresh. Otherwise it is reported in `skippedRules` |

A later layer can add rules but cannot replace or remove one. An attempt is reported in
`ruleConflicts`, and the earlier rule is kept. Rules that contradict each other make the
question abstain.

**Preferences** are soft. Later layers win key by key, and every value's layer is reported in
`preferenceOrigins`.

| Key | Meaning |
|---|---|
| `abstainBelow` | Abstain under this confidence, set by type (`noul`, `choice`, `score`) or by question id |
| `threshold` | Probability of yes needed for a binary yes, by question id. Default 0.5 |
| `prefer` | Option keys to favour, by question id. They only win a near tie |
| `tieMargin` | How close counts as a near tie. Default 0.05 |
| `suggestionLimit` | The most suggestions returned. Default 5 |

A preference never lowers a rule's floor and never selects a forbidden option.

These semantics follow RRFlow's configuration contract:

- defaults, then project preferences, then request overrides, merged into one effective digest
  that records where each field came from
- hard policy intersects every layer
- an override may narrow authority but never widen it
- a stale fact cannot satisfy a requirement

## Templates

A [knowledge template](../config/knowledge/templates/python_delivery_review.json)
(`schemaVersion` 2) is a reusable set of questions with their own layer. Each requirement has:

- an `id`
- a `practice` that links it to the cited question bank in
  [`config/boundaries/question_sets/`](../config/boundaries/question_sets/)
- `inputSlots` naming the project files it reads
- a `question` in the wire format above
- optional `suggest` text keyed by answer (`"true"`, an option key, a score level, or `"abstain"`)

Suggestions come from the decided answer. Rule-driven ones come first.

## Asking SWAG

Command line:

```sh
python tools/swag.py decide --template python_delivery_review --state "pyproject.toml lists pytest under dependencies"
python tools/swag.py decide --request my-request.json --repo C:/work/my-app
```

Server:

```sh
python tools/swag_server.py                    # http://127.0.0.1:8792/v1/systemone
```

| Method and path | Purpose |
|---|---|
| `POST /v1/systemone` | Ask questions |
| `GET /v1/decisions?limit=N` | Read the decision log |
| `GET /v1/models` | List models |
| `GET /health` | Check the server is up |

On loopback the server needs no token. Bound to any other address it refuses to start without
`SWAG_SERVER_TOKEN`, then requires `Authorization: Bearer <token>`. Errors are plain messages
with no internals.

Every request is appended to the decision log (`.swag/decision-log.jsonl`, or
`SWAG_DECISION_LOG`). The log records each question's decision, the rules and preferences behind
it, and the time each step took. The caller's state is stored as a digest and length only,
unless `SWAG_LOG_STATE=1`. The **Decisions** panel of the developer workspace (`cd ui && npm run dev`,
then `http://127.0.0.1:8891/dev.html`) reads it.

## Connecting a model

Set `SWAG_DECISION_MODEL_CONNECTION_FILE` to a JSON file. Without one, only hard rules decide and
every other question abstains with reason `no_engine`.

| `protocol` | Talks to | How it scores |
|---|---|---|
| `systemone` (default) | Any `/v1/systemone` server: KnowLine's server, a Clef wrapper, another SWAG | The server's own probabilities |
| `chat_first_token` | Any OpenAI-compatible chat server: vLLM, llama.cpp `llama-server`, SGLang | Prefill only. Options are labelled A, B, C... and the logprobs of the first answer token are read. No text is generated |

```json
{"schemaVersion": 1, "protocol": "chat_first_token", "baseUrl": "http://127.0.0.1:8084",
 "model": "your-model", "revision": "pinned-revision", "rotations": true,
 "credentialFile": "server.env", "credentialVariable": "API_KEY",
 "timeoutMs": 60000, "maxRequestBytes": 262144, "maxResponseBytes": 262144}
```

- **Loopback only.** The model URL must be on this machine. Reach a remote model through a tunnel.
- **Credentials.** `credentialFile` holds `NAME=value` lines and is read at request time; the
  value never appears in responses or logs.
- **`rotations`.** Scores each question with the options in two orders and averages them. When
  the two orders disagree on a question with three or more options, it adds two more. This
  cancels a model's bias towards whichever label comes first. It is the correction KnowLine's
  release documents, and costs one to three extra prefill passes per question.
- **Option limit.** `chat_first_token` handles up to 26 options per question, one letter each.
