#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

mkdir -p reports

usage() {
  cat <<'EOF'
Usage: clean-artifacts.sh [--reports|--all]

Removes cached test/coverage artifacts. Pass --reports (or --all) to also clear the reports/ directory contents.
EOF
}

PURGE_REPORTS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reports|--all)
      PURGE_REPORTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ARTIFACTS=(
  ".coverage"
  ".coverage.*"
  ".pytest_cache"
  ".ruff_cache"
  "coverage.xml"
  "htmlcov"
  "reports/coverage.xml"
  "reports/htmlcov"
)

for pattern in "${ARTIFACTS[@]}"; do
  rm -rf -- ${pattern}
done

if [[ ${PURGE_REPORTS} -eq 1 ]]; then
  find reports -mindepth 1 ! -name '.gitkeep' -exec rm -rf {} +
  touch reports/.gitkeep
fi

if [[ ${PURGE_REPORTS} -eq 1 ]]; then
  echo "Removed disposable artifacts and cleared reports/ contents."
else
  echo "Removed disposable test and coverage artifacts (reports/ retained; run with --reports to clear)."
fi
