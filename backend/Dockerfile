FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production QA_DEVICE=cpu \
    DATABASE_URL=sqlite:////data/bookworm.db UPLOAD_DIR=/data/uploads \
    HF_HOME=/data/huggingface PORT=8000
WORKDIR /app
COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.lock.txt \
    && useradd --uid 10001 --create-home bookworm \
    && mkdir -p /data/uploads && chown -R bookworm:bookworm /data
COPY --chown=bookworm:bookworm app ./app
COPY --chown=bookworm:bookworm scripts ./scripts
USER bookworm
EXPOSE 8000
CMD ["sh", "-c", "python -m scripts.warm_model && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --limit-concurrency 8"]
