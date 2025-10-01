# docker/backend.Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy only what's needed to install the backend package
# These paths are relative to the build context (vibecoder/backend)
COPY pyproject.toml ./pyproject.toml
COPY backend ./backend

# Install
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir -e .

# Run API
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
