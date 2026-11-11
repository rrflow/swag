#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${ROOT_DIR}/env/swag.env" ]; then
  cp "${ROOT_DIR}/env/swag.env.example" "${ROOT_DIR}/env/swag.env"
fi

cat <<'EOF'
SWAG environment example prepared. No services started or credentials provisioned.

Next steps:
1. Review ./deploy/env/swag.env.
2. Start the local preview: bash ./deploy/scripts/start-swag.sh
3. Read ./deploy/README.md for engine and UI integration limits.
EOF
