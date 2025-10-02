# docker/worker.Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy backend and worker projects so both can be installed.
COPY backend ./backend
COPY worker ./worker

RUN pip install --no-cache-dir -U pip setuptools wheel \
 && pip install --no-cache-dir -e ./backend \
 && pip install --no-cache-dir -e ./worker

CMD ["python", "-m", "worker"]
