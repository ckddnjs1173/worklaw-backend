# ---- Base image ----
FROM python:3.13-slim

# ---- OS deps (optional but useful) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ---- Workdir ----
WORKDIR /app

# ---- Copy metadata first for better layer caching ----
COPY requirements.txt ./

# ---- Python deps ----
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Copy app source ----
COPY . .

# ---- Environment sane defaults ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Expose (informational) ----
EXPOSE 8000

# ---- Start command (Railway uses $PORT) ----
# Alembic 마이그레이션 후 Uvicorn 기동
CMD ["sh","-c","alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT"]
