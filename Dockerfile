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

# Copy source code (includes docker-entrypoint.sh)
COPY . .

# Ensure entrypoint script exists and is executable
# List all files to debug
RUN echo "=== Files in /app ===" && \
    ls -la /app/ | head -20 && \
    echo "=== Looking for docker-entrypoint.sh ===" && \
    find /app -name "docker-entrypoint.sh" -type f && \
    if [ ! -f /app/docker-entrypoint.sh ]; then \
        echo "ERROR: docker-entrypoint.sh not found in /app!" && \
        echo "Files in /app:" && \
        ls -la /app/ && \
        exit 1; \
    fi && \
    chmod +x /app/docker-entrypoint.sh && \
    ls -la /app/docker-entrypoint.sh && \
    echo "=== Entrypoint file verified in builder ==="

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || true

# Final stage - Minimal Python runtime
FROM python:3.11-slim

# Install only runtime dependencies (no build tools)
# bash is needed for entrypoint script
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    ca-certificates \
    tzdata \
    bash \
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

# Copy entrypoint script from builder (we verified it exists there)
RUN cp /app/docker-entrypoint.sh /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    ls -la /docker-entrypoint.sh && \
    test -f /docker-entrypoint.sh && \
    echo "=== Entrypoint file copied and verified ===" && \
    head -1 /docker-entrypoint.sh && \
    which bash && \
    echo "=== Bash location ===" && \
    ls -la /bin/bash && \
    echo "Entrypoint script verified successfully"

# Create nonroot user (UID 65532, same as distroless)
RUN groupadd -r nonroot && useradd -r -g nonroot -u 65532 nonroot

# Set working directory
WORKDIR /app

# Set ownership for app directory and entrypoint, make venv readable
# Entrypoint should be readable by nonroot (it's in root, but executable by all)
RUN chown -R nonroot:nonroot /app && \
    chown -R nonroot:nonroot /opt/venv

# Create a wrapper script that verifies entrypoint exists (before user switch)
RUN echo '#!/bin/bash' > /entrypoint-wrapper.sh && \
    echo 'if [ ! -f /docker-entrypoint.sh ]; then' >> /entrypoint-wrapper.sh && \
    echo '  echo "ERROR: Entrypoint file not found at /docker-entrypoint.sh"' >> /entrypoint-wrapper.sh && \
    echo '  echo "Files in /:"' >> /entrypoint-wrapper.sh && \
    echo '  ls -la /' >> /entrypoint-wrapper.sh && \
    echo '  echo "Files in /app:"' >> /entrypoint-wrapper.sh && \
    echo '  ls -la /app/ | head -10' >> /entrypoint-wrapper.sh && \
    echo '  exit 1' >> /entrypoint-wrapper.sh && \
    echo 'fi' >> /entrypoint-wrapper.sh && \
    echo 'exec /bin/bash /docker-entrypoint.sh "$@"' >> /entrypoint-wrapper.sh && \
    chmod +x /entrypoint-wrapper.sh && \
    echo "=== Wrapper script created ===" && \
    cat /entrypoint-wrapper.sh

# Final verification before switching user - ensure entrypoint exists and is accessible
# Also verify bash location
RUN test -f /docker-entrypoint.sh && \
    test -x /docker-entrypoint.sh && \
    test -f /entrypoint-wrapper.sh && \
    test -x /entrypoint-wrapper.sh && \
    file /docker-entrypoint.sh && \
    cat /docker-entrypoint.sh | head -1 && \
    which bash && \
    ls -la /bin/bash /usr/bin/bash 2>/dev/null || echo "Checking bash location..." && \
    echo "=== Final check: Entrypoint file ===" && \
    ls -la /docker-entrypoint.sh && \
    echo "=== File content (first line) ===" && \
    head -1 /docker-entrypoint.sh

# Use nonroot user
USER nonroot:nonroot

# Verify file is still accessible after user switch (as nonroot)
RUN test -f /docker-entrypoint.sh && \
    test -r /docker-entrypoint.sh && \
    test -f /entrypoint-wrapper.sh && \
    echo "Entrypoint file is accessible as nonroot user" || \
    (echo "WARNING: Entrypoint file may not be accessible" && ls -la /docker-entrypoint.sh /entrypoint-wrapper.sh)

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Expose port
EXPOSE 8000

# Entrypoint - use wrapper script (created above)
ENTRYPOINT ["/entrypoint-wrapper.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
