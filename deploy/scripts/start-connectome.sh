#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [ -f "${ROOT_DIR}/env/connectome.env" ]; then
  set -a
  . "${ROOT_DIR}/env/connectome.env"
  set +a
fi
printf 'Connectome is expected to consume the public RRFlow contract and SWAG status endpoints; this stub keeps deployment order explicit.\n'
