# Build stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependencies - copy only requirements first
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || true

# Final stage - Minimal Python runtime
FROM python:3.11-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy timezone data
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
ENV TZ=Asia/Almaty

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Make sure venv is accessible and in PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder /app /app

# Copy entrypoint script
COPY --from=builder /app/docker-entrypoint.sh /docker-entrypoint.sh

# Create nonroot user (UID 65532, same as distroless)
RUN groupadd -r nonroot && useradd -r -g nonroot -u 65532 nonroot

# Set working directory
WORKDIR /app

# Make sure scripts are executable and set permissions
# Set ownership for app directory and entrypoint, make venv readable
RUN chmod +x /docker-entrypoint.sh && \
    chown -R nonroot:nonroot /app && \
    chown -R nonroot:nonroot /opt/venv

# Use nonroot user
USER nonroot:nonroot

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
