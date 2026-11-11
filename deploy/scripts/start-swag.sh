#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [ -f "${ROOT_DIR}/env/swag.env" ]; then
  set -a
  . "${ROOT_DIR}/env/swag.env"
  set +a
fi
exec "${SWAG_PYTHON:-python}" "${ROOT_DIR}/../tools/swag_decision_service.py" --host "${SWAG_HOST:-127.0.0.1}" --port "${SWAG_PORT:-8787}"
