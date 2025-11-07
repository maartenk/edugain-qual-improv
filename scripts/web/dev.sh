#!/usr/bin/env bash
# Bootstrap and run the eduGAIN web interface locally.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV}" ]]; then
  echo "[web-dev] Creating virtual environment (.venv)..."
  python3 -m venv "${VENV}"
fi

source "${VENV}/bin/activate"

echo "[web-dev] Upgrading pip..."
python -m pip install --upgrade pip

echo "[web-dev] Installing project with web extras..."
python -m pip install -e ".[dev,web]"

export EDUGAIN_WEB_DB_URL="${EDUGAIN_WEB_DB_URL:-sqlite:///$(python - <<'PY'
from edugain_analysis_web.models import get_database_file_path
print(get_database_file_path())
PY
)}"

echo "[web-dev] Database path: ${EDUGAIN_WEB_DB_URL}"

exec uvicorn edugain_analysis_web.app:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" --reload
