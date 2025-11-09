#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAKE_CMD="${MAKE:-make}"

exec "$MAKE_CMD" -C "$ROOT_DIR" neo4j-refresh "$@"
