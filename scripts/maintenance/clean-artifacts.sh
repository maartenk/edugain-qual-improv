#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

mkdir -p reports

usage() {
  cat <<'EOF'
Usage: clean-artifacts.sh [--reports|--all] [--artifacts-only|--cache-only]

Removes cached test/coverage artifacts and edugain-analysis caches.

Options:
  --reports, --all     Also clear the reports/ directory contents (implies artifacts cleanup)
  --artifacts-only     Run only the dev/test/coverage artifact cleanup
  --cache-only         Run only the edugain-analysis cache cleanup
EOF
}

PURGE_REPORTS=0
DO_ARTIFACTS=1
DO_CACHE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reports|--all)
      PURGE_REPORTS=1
      shift
      ;;
    --artifacts-only)
      DO_ARTIFACTS=1
      DO_CACHE=0
      shift
      ;;
    --cache-only)
      DO_ARTIFACTS=0
      DO_CACHE=1
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

if [[ ${PURGE_REPORTS} -eq 1 && ${DO_ARTIFACTS} -eq 0 ]]; then
  echo "--reports / --all requires artifact cleanup; omit --cache-only." >&2
  exit 1
fi

ARTIFACTS=(
  ".coverage"
  ".coverage.*"
  ".pytest_cache"
  ".ruff_cache"
  "coverage.xml"
  "htmlcov"
  "artifacts/coverage"
  "reports/coverage.xml"
  "reports/htmlcov"
)

if [[ ${DO_ARTIFACTS} -eq 1 ]]; then
  echo "Removing dev/test/coverage artifacts..."
  for pattern in "${ARTIFACTS[@]}"; do
    rm -rf -- ${pattern}
  done

  if [[ ${PURGE_REPORTS} -eq 1 ]]; then
    find reports -mindepth 1 ! -name '.gitkeep' -exec rm -rf {} +
    touch reports/.gitkeep
    echo "Removed disposable artifacts and cleared reports/ contents."
  else
    echo "Removed disposable test and coverage artifacts (reports/ retained; run with --reports to clear)."
  fi
else
  echo "Skipping dev/test/coverage artifact cleanup."
fi

if [[ ${DO_CACHE} -eq 1 ]]; then
  echo "Inspecting edugain-analysis cache..."
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
  else
    PYTHON_CMD=""
  fi

  CACHE_DIR=""
  if [[ -n "${PYTHON_CMD}" ]]; then
    CACHE_DIR="$("${PYTHON_CMD}" - <<'PY'
try:
    from platformdirs import user_cache_dir
except ImportError:
    import os
    import sys
    from pathlib import Path

    home = Path.home()
    if os.name == "nt":
        cache_dir = home / "AppData" / "Local" / "edugain" / "edugain-analysis" / "Cache"
    elif sys.platform == "darwin":
        cache_dir = home / "Library" / "Caches" / "edugain-analysis"
    else:
        cache_dir = home / ".cache" / "edugain-analysis"
else:
    cache_dir = user_cache_dir("edugain-analysis", "edugain")

print(cache_dir, end="")
PY
)"
  fi

  if [[ -n "${CACHE_DIR}" ]]; then
    echo "Clearing edugain-analysis cache at ${CACHE_DIR}..."
    rm -f "${CACHE_DIR}/metadata.xml" \
          "${CACHE_DIR}/federations.json" \
          "${CACHE_DIR}/url_validation.json" 2>/dev/null || true
    if [[ -d "${CACHE_DIR}" ]]; then
      find "${CACHE_DIR}" -type d -empty -delete 2>/dev/null || true
    fi
  else
    echo "No edugain-analysis cache directory detected; nothing to clear."
  fi
else
  echo "Skipping edugain-analysis cache cleanup."
fi
