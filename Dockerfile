# syntax=docker/dockerfile:1

# --- STAGE 1: Builder ---
# Use standard Python 3.11 slim image
FROM python:3.11-slim AS builder

# Set working directory for the build process
WORKDIR /app

# Install system dependencies (needed for building wheels, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt .

# Create virtual environment and install dependencies
# The --mount=type=cache is used for faster subsequent builds
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install -r requirements.txt

# Copy application code
COPY app ./app
COPY daily_job_runner.py .


# --- STAGE 2: Final / Runner ---
FROM python:3.11-slim AS final

# Create non-root user and group
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code from builder stage
COPY --from=builder /app/app ./app
COPY --from=builder /app/daily_job_runner.py .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose the application port
EXPOSE 8070

# Healthcheck: Verify the service is responsive (assuming your /metrics endpoint works)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8070/metrics || exit 1

# Switch to non-root user for security
USER appuser

# FIX: Command to run the application using the full path to the uvicorn executable from the venv
# This ensures the container does not exit immediately.
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]