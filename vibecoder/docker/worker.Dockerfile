FROM python:3.12-slim

WORKDIR /app

COPY worker/pyproject.toml worker/pyproject.toml
COPY worker/worker worker/worker
COPY backend/backend backend/backend
COPY backend/pyproject.toml backend/pyproject.toml

RUN pip install --no-cache-dir pip setuptools wheel
RUN pip install --no-cache-dir -e backend -e worker

ENV PYTHONPATH=/app
CMD ["python", "-m", "worker"]
