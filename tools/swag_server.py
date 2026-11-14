"""SWAG decision server: a SystemOne-compatible `POST /v1/systemone` with SWAG's decision layer.

Any client written for TypeSafe's Jev or another SystemOne server can call SWAG unchanged: the
`answers` it gets back are the model's probabilities in the same shape. SWAG adds a `swag` block
with the decisions, the rules and preferences behind them, suggestions and per-step timings
(see `swag_decide`). Every request is written to the local decision log for the developer tools.

    python tools/swag_server.py                       # 127.0.0.1:8792, no token needed
    SWAG_SERVER_TOKEN=... python tools/swag_server.py --host 0.0.0.0   # any other address needs a token

Endpoints: `POST /v1/systemone`, `GET /v1/decisions?limit=N`, `GET /v1/models`, `GET /health`.
The model behind it is the one named by `SWAG_DECISION_MODEL_CONNECTION_FILE`; without one, only
hard rules can decide and every other question abstains with reason `no_engine`.
"""
from __future__ import annotations

import argparse
import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import parse_qs, urlsplit
import uuid

import swag_decide
import swag_decision_log
import swag_decision_model
import swag_systemone as contract

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 1_000_000
EXTENSION_KEYS = {'template', 'facts', 'rules', 'preferences'}


def template_parts(name: str) -> tuple[dict, dict, dict]:
    """A knowledge template's layer, questions and suggestions."""
    from swag_knowledge import template
    try:
        data = template(name)
    except (ValueError, OSError):
        raise contract.ContractError('Unknown or invalid template.') from None
    questions = {row['id']: row['question'] for row in data['requirements']}
    suggest = {row['id']: row['suggest'] for row in data['requirements'] if 'suggest' in row}
    return swag_decide.template_layer(data), questions, suggest


def run(body: Any, repo: Path | None = None, engine: Any = 'configured', source: str = 'api', log: bool = True) -> dict:
    """Validate, decide and log one SystemOne request. Raises ContractError or LayerError on bad input."""
    if isinstance(body, dict) and 'questions' not in body and isinstance(body.get('swag'), dict) \
            and body['swag'].get('template'):
        # A template alone supplies its own questions.
        _, questions, _ = template_parts(body['swag']['template'])
        body = {**body, 'questions': questions}
    request = contract.validate_request(body)
    extension = request['swag']
    if set(extension) - EXTENSION_KEYS:
        raise contract.ContractError('The swag block may only hold template, facts, rules and preferences.')
    layers = {'template': swag_decide.validate_layer(None), 'project': swag_decide.project_layer(repo),
              'operator': swag_decide.operator_layer(),
              'request': swag_decide.validate_layer({key: extension[key] for key in ('facts', 'rules', 'preferences')
                                                     if key in extension})}
    suggest: dict = {}
    if extension.get('template'):
        layers['template'], _, suggest = template_parts(extension['template'])
    if engine == 'configured':
        engine = swag_decision_model.distributions if swag_decision_model.configured() else None
    response = swag_decide.decide(request, layers, engine, suggest)
    response['id'] = 'swag-' + uuid.uuid4().hex[:16]
    if log:
        swag_decision_log.append(swag_decision_log.record(request, response, source))
    return response


def _loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == 'localhost'


class Handler(BaseHTTPRequestHandler):
    server_version = 'swag'
    sys_version = ''
    repo: Path | None = None
    token: str | None = None

    def log_message(self, *args: Any) -> None:  # request lines stay out of stdout; decisions go to the log
        pass

    def _send(self, status: HTTPStatus, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        if not self.token:
            return True
        supplied = self.headers.get('Authorization', '')
        return hmac.compare_digest(supplied.encode(), ('Bearer ' + self.token).encode())

    def do_GET(self) -> None:  # noqa: N802
        url = urlsplit(self.path)
        if url.path == '/health':
            self._send(HTTPStatus.OK, {'status': 'ok', 'engineConfigured': swag_decision_model.configured()})
            return
        if not self._authorized():
            self._send(HTTPStatus.UNAUTHORIZED, {'error': 'A bearer token is required.'})
            return
        if url.path == '/v1/models':
            self._send(HTTPStatus.OK, {'object': 'list', 'data': [{'id': 'swag', 'object': 'model', 'owned_by': 'swag'}]})
        elif url.path == '/v1/decisions':
            try:
                limit = int(parse_qs(url.query).get('limit', ['50'])[0])
            except ValueError:
                limit = 50
            self._send(HTTPStatus.OK, swag_decision_log.read(limit))
        else:
            self._send(HTTPStatus.NOT_FOUND, {'error': 'Not found.'})

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != '/v1/systemone':
            self._send(HTTPStatus.NOT_FOUND, {'error': 'Not found.'})
            return
        if not self._authorized():
            self._send(HTTPStatus.UNAUTHORIZED, {'error': 'A bearer token is required.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {'error': f'Send a JSON body of at most {MAX_BODY} bytes.'})
            return
        try:
            body = json.loads(self.rfile.read(length))
            self._send(HTTPStatus.OK, run(body, self.repo))
        except (contract.ContractError, swag_decide.LayerError) as exc:
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': str(exc)})
        except (ValueError, UnicodeDecodeError):
            self._send(HTTPStatus.BAD_REQUEST, {'error': 'The body is not valid JSON.'})
        except swag_decision_model.DecisionModelError as exc:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': str(exc)})
        except Exception:  # never send internals to a client; the trace stays local
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {'error': 'The decision failed; check the local decision log and traces.'})


def serve(host: str, port: int, repo: Path | None, token: str | None) -> ThreadingHTTPServer:
    if not _loopback(host) and not token:
        raise SystemExit('Binding beyond loopback needs SWAG_SERVER_TOKEN so other machines cannot use your model.')
    handler = type('BoundHandler', (Handler,), {'repo': repo, 'token': token or None})
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', default=os.environ.get('SWAG_HOST', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=os.environ.get('SWAG_PORT', '8792'))
    parser.add_argument('--repo', type=Path, help='Project whose .swag/layer.json applies to every request')
    arguments = parser.parse_args(argv)
    server = serve(arguments.host, arguments.port, arguments.repo.resolve() if arguments.repo else None,
                   os.environ.get('SWAG_SERVER_TOKEN'))
    print(json.dumps({'service': 'swag', 'url': f'http://{arguments.host}:{arguments.port}/v1/systemone',
                      'engineConfigured': swag_decision_model.configured(),
                      'decisionLog': str(swag_decision_log.location())}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
