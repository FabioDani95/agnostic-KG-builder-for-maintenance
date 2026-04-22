#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

PYTHON_BIN="$(pwd)/.venv/bin/python"

source .venv/bin/activate

if ! "$PYTHON_BIN" -c "import fastapi, fitz, langgraph, jsonschema, networkx" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install -r requirements.txt
fi

# Kill any process already holding the port
PORT="${PORT:-8000}"
lsof -ti tcp:"$PORT" | xargs kill -9 2>/dev/null || true
sleep 0.5

exec "$PYTHON_BIN" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port "$PORT" \
  --reload-exclude "tests/*" \
  --reload-exclude "test-results/*" \
  --reload-exclude "playwright-report/*"
