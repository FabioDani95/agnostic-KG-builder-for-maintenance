#!/bin/bash
# Kill any existing process on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null
echo "Port 8000 cleared."

# Start the server
cd "$(dirname "$0")"
source .venv/bin/activate
python -c "import langgraph, jsonschema, networkx" >/dev/null 2>&1 || python -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
