# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 deps (sqlite, gcc 필요 시)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential sqlite3 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "bcrypt==4.1.3" "passlib==1.7.4"

COPY . .

# .env는 컨테이너 외부에서 주입 권장
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
