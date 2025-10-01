# docker/worker.Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build context = vibecoder/worker
# These two lines must match files that exist in THIS folder.
COPY pyproject.toml ./pyproject.toml
COPY worker ./worker

RUN pip install --no-cache-dir -U pip setuptools wheel \
 && pip install --no-cache-dir -e .

CMD ["python", "-m", "worker"]
