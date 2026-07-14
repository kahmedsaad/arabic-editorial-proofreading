# Cloud Run Demo A — FastAPI + Vertex Gemini
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    AI_CLIENT=gemini \
    USE_GCP=true \
    DEMO_AUTH_REQUIRED=true \
    SQLITE_PATH=/tmp/app.db \
    ENABLE_LETTER_VARIANT_WARNINGS=false

COPY pyproject.toml README.md ./
COPY app ./app
COPY data ./data
COPY prompts ./prompts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[gemini]" \
    && mkdir -p /tmp

# Ephemeral SQLite for demo (resets on new revision/instance)
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
