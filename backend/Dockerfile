# Using Python 3.12 (Has pre-built wheels for Pandas/Prophet)
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install System Dependencies
# 'curl' is needed for health checks or downloading models
# 'libgomp1' is required for Prophet's parallel processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy Requirements
COPY requirements.txt .

# Relax the strict pinning slightly to allow pip to find the best binary match
RUN pip install --no-cache-dir numpy>=1.26.0
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Define the default port environment variable
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Command to run the application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload"