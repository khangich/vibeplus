# docker/backend.Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Node.js for preview runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed to install the backend package
# These paths are relative to the build context (vibecoder/backend)
COPY pyproject.toml ./pyproject.toml
COPY backend ./backend

# Install
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir -e .

# Run API
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
