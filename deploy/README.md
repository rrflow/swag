# Local development launchers

These files do not deploy a joined SWAG, RRFlow and Connectome stack. The
RRFlow and Connectome launch commands explicitly fail because their installers
and engine/provider integration are not supplied here.

## SWAG decision server

Install the repository's Python dependencies, then run from the repository root:

```sh
bash deploy/scripts/bootstrap-local-stack.sh
bash deploy/scripts/start-swag.sh
```

Bootstrap copies only the SWAG environment example and preserves an existing
file. It starts no service and provisions no credentials. The launcher starts
`tools/swag_server.py` on `127.0.0.1:8792` by default. `SWAG_PYTHON` may select
an installed Python interpreter. A successful `/health` response proves only
that this service is reachable.

The server answers `POST /v1/systemone`, `GET /v1/decisions`, `GET /v1/models`
and `GET /health`; see the [decision contract](../docs/decision-contract.md).
Bound to anything but loopback, it refuses to start without `SWAG_SERVER_TOKEN`
and then requires that bearer token on every request except `/health`. Its
decisions are proposals; they do not authorize anything in RRFlow.

The older preview service (`tools/swag_decision_service.py`, `POST /v1/decision`)
still runs by hand for the legacy `preview` command. It refuses model execution
over HTTP and returns plain errors.

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
See [current context](../docs/history/current-context.md) for evidence and limitations.
