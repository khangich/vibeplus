# docker/worker.rootcontext.Dockerfile
FROM python:3.12-slim
WORKDIR /app

# Build context will be repo root (vibecoder)
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/backend backend/backend

COPY worker/pyproject.toml worker/pyproject.toml
COPY worker/worker worker/worker

RUN pip install --no-cache-dir -U pip setuptools wheel \
 && pip install --no-cache-dir -e backend -e worker

CMD ["python", "-m", "worker"]
