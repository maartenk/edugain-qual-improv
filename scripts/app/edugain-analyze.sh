#!/usr/bin/env bash
# Wrapper to run the eduGAIN analysis CLI without installing the package.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+":${PYTHONPATH}"}"

exec "${PYTHON_BIN}" -m edugain_analysis.cli.main "$@"
