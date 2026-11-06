#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${ROOT_DIR}/env/rrflow.env" ]; then
  cp "${ROOT_DIR}/env/rrflow.env.example" "${ROOT_DIR}/env/rrflow.env"
fi
if [ ! -f "${ROOT_DIR}/env/swag.env" ]; then
  cp "${ROOT_DIR}/env/swag.env.example" "${ROOT_DIR}/env/swag.env"
fi
if [ ! -f "${ROOT_DIR}/env/connectome.env" ]; then
  cp "${ROOT_DIR}/env/connectome.env.example" "${ROOT_DIR}/env/connectome.env"
fi

if [ ! -f "${ROOT_DIR}/rrflow/connection.json" ]; then
  cp "${ROOT_DIR}/rrflow/connection.json.example" "${ROOT_DIR}/rrflow/connection.json"
fi
if [ ! -f "${ROOT_DIR}/swag/rrflow-connection.json" ]; then
  cp "${ROOT_DIR}/swag/rrflow-connection.json.example" "${ROOT_DIR}/swag/rrflow-connection.json"
fi
if [ ! -f "${ROOT_DIR}/connectome/manifest.json" ]; then
  cp "${ROOT_DIR}/connectome/manifest.json.example" "${ROOT_DIR}/connectome/manifest.json"
fi

mkdir -p "${ROOT_DIR}/evidence/reviewed" "${ROOT_DIR}/evidence/training" "${ROOT_DIR}/evidence/rejected"

cat <<'EOF'
Local stack bootstrap complete.

Next steps:
1. Review env files under ./deploy/env/.
2. Start RRFlow: ./deploy/scripts/start-rrflow.sh
3. Start SWAG: ./deploy/scripts/start-swag.sh
4. Start Connectome: ./deploy/scripts/start-connectome.sh

The engine remains the authority; SWAG proposes and Connectome reads public status.
EOF
