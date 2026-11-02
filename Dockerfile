FROM python:3.12-slim

WORKDIR /app

# Ensure output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    DATABASE_PATH=/app/data/reservations.db

# Install system dependencies if required (sqlite3 is bundled with python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code and test suite
COPY src/ ./src/
COPY tests/ ./tests/

# Create persistent data volume directory
RUN mkdir -p /app/data

EXPOSE 8000

# Default command: launch FastAPI server with Uvicorn
CMD ["uvicorn", "lab_reservations.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
