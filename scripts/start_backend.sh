#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

PYTHON_BIN="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
