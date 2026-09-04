FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CHROMA_PATH=/app/chroma_db

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/chroma_db \
    && chown -R appuser:appuser /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser agent.py ingest.py main.py models.py retriever.py .env.example ./
COPY --chown=appuser:appuser data ./data

USER appuser

VOLUME ["/app/chroma_db"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]