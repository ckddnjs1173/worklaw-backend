#!/usr/bin/env bash
set -euo pipefail

echo "[ENTRYPOINT] Python: $(python -V)"
echo "[ENTRYPOINT] CWD: $(pwd)"
echo "[ENTRYPOINT] PORT=${PORT:-8080}"

# Alembic migration (있으면 수행, 실패해도 서버는 띄움)
if [ -f alembic.ini ]; then
  echo "[ENTRYPOINT] Alembic upgrade..."
  python -m alembic -c alembic.ini upgrade head || echo "[ENTRYPOINT] Alembic failed (continuing)"
else
  echo "[ENTRYPOINT] No alembic.ini; skip migrations."
fi

# Uvicorn
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --lifespan on --log-level debug