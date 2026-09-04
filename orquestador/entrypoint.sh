#!/bin/sh
# Un solo contenedor levanta el Orquestador (FastAPI, :8080) y el
# Dashboard (Streamlit, :8501). Streamlit corre en primer plano; si el
# Orquestador muere, el contenedor se detiene con él.
set -e

uvicorn orchestrator:app --host 0.0.0.0 --port 8080 &
ORCH_PID=$!
trap 'kill -TERM "$ORCH_PID" 2>/dev/null' EXIT INT TERM

for i in $(seq 1 20); do
    if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

exec streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true \
    --browser.gatherUsageStats=false
