FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/backend backend/backend

RUN pip install --no-cache-dir pip setuptools wheel
RUN pip install --no-cache-dir -e backend

ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
