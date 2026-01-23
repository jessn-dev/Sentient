# Using Python 3.12 (Has pre-built wheels for Pandas/Prophet)
FROM python:3.12-slim-bookworm

# --- 1. INSTALL UV ---
# This was missing! We need to copy the 'uv' binary from its official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt .

# --- 2. INSTALL DEPENDENCIES (FAST) ---
# Now 'uv' will work because we installed it above.
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Define the default port environment variable
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Command to run the application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port $PORT"