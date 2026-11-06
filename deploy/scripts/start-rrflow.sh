#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [ -f "${ROOT_DIR}/env/rrflow.env" ]; then
  set -a
  . "${ROOT_DIR}/env/rrflow.env"
  set +a
fi
python "${ROOT_DIR}/../tools/swag_rrflow.py" || true
