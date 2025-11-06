#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

: "${PYTHON_BIN:=.venv/bin/python}"
: "${SKIP_DOCKER:=0}"
: "${SKIP_COVERAGE:=0}"

run_step() {
  local description=$1
  shift
  echo "[local-ci] ${description}" >&2
  "$@"
}

if [[ ! -x ${PYTHON_BIN} ]]; then
  echo "[local-ci] Python binary '${PYTHON_BIN}' not found. Did you bootstrap the virtualenv?" >&2
  exit 1
fi

run_step "Lint (ruff)" ./scripts/dev/lint.sh
run_step "Unit tests" bash -c ". .venv/bin/activate && pytest"

if [[ ${SKIP_COVERAGE} -eq 0 ]]; then
  run_step "Coverage run" make coverage
else
  echo "[local-ci] Skipping coverage (SKIP_COVERAGE=${SKIP_COVERAGE})" >&2
fi

if [[ ${SKIP_DOCKER} -eq 0 ]]; then
  run_step "Docker build" docker compose build
  run_step "Docker tests" docker compose run --rm test
  run_step "Docker cleanup" docker compose down
else
  echo "[local-ci] Skipping docker workflow (SKIP_DOCKER=${SKIP_DOCKER})" >&2
fi

echo "[local-ci] All checks completed successfully." >&2
