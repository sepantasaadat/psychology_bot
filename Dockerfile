# ==============================================================================
# Psychology Clinic Application - Multi-stage Production Dockerfile
# Base: python:3.12-slim
# ==============================================================================

# Stage 1: Build & wheels preparation
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies for Pillow and C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtualenv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Hardened runtime environment
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Tehran \
    PATH="/opt/venv/bin:$PATH"

# Install runtime shared libraries for Pillow and timezone data
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create non-root unprivileged user (UID 1000)
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set up working directory and persistent volume mount targets
WORKDIR /app
RUN mkdir -p /app/private_uploads /data /data/uploads && \
    chown -R appuser:appuser /app /data /opt/venv

# Copy application source tree
COPY --chown=appuser:appuser . /app

# Switch to non-root execution
USER appuser

EXPOSE 5000

# Default command launches web server via Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]
