#!/usr/bin/env bash
# Remove local virtual environment and transient build/test artifacts.

set -euo pipefail

paths=(
    ".venv"
    ".pytest_cache"
    "htmlcov"
    "coverage.xml"
    "dist"
)

for path in "${paths[@]}"; do
    if [[ -e "${path}" ]]; then
        echo "Removing ${path}"
        rm -rf "${path}"
    fi
done

echo "Environment cleaned."
