#!/usr/bin/env bash
# Local dev launcher — starts FastAPI + Streamlit side-by-side
set -e

[ -f .env ] && export $(grep -v '^#' .env | xargs)

echo "Starting FastAPI on http://localhost:8000 ..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

echo "Starting Streamlit on http://localhost:8501 ..."
streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1
STREAMLIT_EXIT=$?

kill $API_PID 2>/dev/null || true
exit $STREAMLIT_EXIT
