#!/usr/bin/env bash
set -euxo pipefail

echo "[start] PWD=$(pwd)"
echo "[start] Python: $(python --version || true)"

echo "[start] Alembic upgrade..."
python -m alembic -c alembic.ini upgrade head

echo "[start] Launching Uvicorn on :${PORT:-8080}"
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --lifespan on
