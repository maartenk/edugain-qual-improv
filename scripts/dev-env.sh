#!/usr/bin/env bash
# Helper script to create/refresh the local developer environment.
# Usage: scripts/dev-env.sh [--with-coverage] [--with-parallel] [--with-tests] [--fresh]

set -euo pipefail

EXTRAS=("dev")
FRESH=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-coverage)
            EXTRAS+=("coverage")
            shift
            ;;
        --with-parallel)
            EXTRAS+=("parallel")
            shift
            ;;
        --with-tests)
            EXTRAS+=("tests")
            shift
            ;;
        --fresh)
            FRESH=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--with-coverage] [--with-parallel] [--with-tests] [--fresh]" >&2
            exit 1
            ;;
    esac
done

EXTRA_SPEC="$(IFS=,; echo "${EXTRAS[*]}")"

select_python() {
    if [[ -n "${DEVENV_PYTHON:-}" ]]; then
        if command -v "${DEVENV_PYTHON}" >/dev/null 2>&1; then
            echo "${DEVENV_PYTHON}"
            return
        else
            echo "Specified DEVENV_PYTHON='${DEVENV_PYTHON}' not found" >&2
            exit 1
        fi
    fi

    local candidates=(python3.14 python3.13 python3.12 python3.11 python3)
    for candidate in "${candidates[@]}"; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            if "${candidate}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
                echo "${candidate}"
                return
            fi
        fi
    done

    echo "No Python >= 3.11 interpreter found. Install python3.11+ or set DEVENV_PYTHON." >&2
    exit 1
}

PYTHON_BIN="$(select_python)"
echo "Using interpreter: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"

if [[ "${FRESH}" == "true" && -d ".venv" ]]; then
    echo "Removing existing virtual environment (.venv)..."
    rm -rf .venv
fi

if [[ -d ".venv" ]]; then
    echo "Updating existing virtual environment (.venv)..."
else
    echo "Creating virtual environment (.venv)..."
    "${PYTHON_BIN}" -m venv .venv
fi

source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing base requirements..."
python -m pip install -r requirements.txt

echo "Installing extras: ${EXTRA_SPEC}"
python -m pip install -e ".[${EXTRA_SPEC}]"

echo "Developer environment ready."
