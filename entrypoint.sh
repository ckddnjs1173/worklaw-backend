#!/usr/bin/env bash
set -euo pipefail
echo "[ENTRYPOINT] Python: $(python -V)"
echo "[ENTRYPOINT] CWD: $(pwd)"
echo "[ENTRYPOINT] PORT=${PORT:-8080}"
echo "[ENTRYPOINT] Before fix: ENV=${ENV:-unset} APP_ENV=${APP_ENV:-unset}"
export ENV="${APP_ENV:-${ENV:-staging}}"
echo "[ENTRYPOINT] After fix:  ENV=${ENV}"
if [ -f alembic.ini ]; then
  echo "[ENTRYPOINT] Alembic upgrade..."
  python -m alembic -c alembic.ini upgrade head || echo "[ENTRYPOINT] Alembic failed (continuing)"
else
  echo "[ENTRYPOINT] No alembic.ini; skip migrations."
fi
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --lifespan on --log-level debug