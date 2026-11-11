# Local development launchers

These files do not deploy a joined SWAG, RRFlow and Connectome stack. The
RRFlow and Connectome launch commands explicitly fail because their installers
and engine/provider integration are not supplied here.

## SWAG preview service

Install the repository's Python dependencies, then run from the repository root:

```sh
bash deploy/scripts/bootstrap-local-stack.sh
bash deploy/scripts/start-swag.sh
```

Bootstrap copies only the SWAG environment example and preserves an existing
file. It starts no service and provisions no credentials. The launcher starts
`tools/swag_decision_service.py` on loopback by default. `SWAG_PYTHON` may select
an installed Python interpreter. A successful `/health` response proves only
that this service is reachable.

Implemented paths are `GET /health`, `GET /v1/providers/status`,
`GET /v1/local/providers/status`, and `POST /v1/decision`. There is no
`/v1/preview` endpoint. Decisions default to a local preview; legacy explicit
model-call options do not implement RRFlow admission. Do not expose this
unauthenticated experimental service publicly or treat its results as engine
authorization.

## Engine and UI integration

Install RRFlow through its own
[development repository](https://github.com/rrflow/rrflow-development).
Discover the installed engine's actual operation catalogue at
`GET /v1/schema/endpoints`; SWAG does not define an alternate engine contract.
Use `deploy/swag/rrflow-connection.json.example` only as a shape reference for
the explicitly configured read-only `tools/swag_rrflow.py` client. Supply the
actual installed instance and credential file privately; configuration alone
does not start or authorize an engine.

The current developer evidence UI is built with `cd ui && npm ci && npm test`
and served with `npm run dev`. Connectome embedding, engine-owned template
execution and triggered LFG/SWAG assessment cycles remain unimplemented here.
See [current context](../docs/current-context.md) for evidence and limitations.
