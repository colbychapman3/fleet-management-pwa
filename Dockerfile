# Multi-stage Dockerfile for Flask Fleet Management System
# Optimized for production deployment with security best practices

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Labels for container metadata
LABEL maintainer="Fleet Management Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0" \
      org.label-schema.name="fleet-management" \
      org.label-schema.description="Maritime Fleet Management System with PWA capabilities" \
      org.label-schema.url="https://github.com/fleet-management/app" \
      org.label-schema.usage="docker run -p 5000:5000 fleet-management:latest" \
      org.label-schema.docker.cmd="docker run -d -p 5000:5000 --name fleet-app fleet-management:latest"

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    PORT=5000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    nginx \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r fleetapp && useradd -r -g fleetapp fleetapp

# Create application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/static/icons /app/static/screenshots && \
    chown -R fleetapp:fleetapp /app

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create placeholder icon files (replace with actual icons)
RUN echo "Icon placeholder" > /app/static/icons/icon-32x32.png && \
    echo "Icon placeholder" > /app/static/icons/icon-72x72.png && \
    echo "Icon placeholder" > /app/static/icons/icon-96x96.png && \
    echo "Icon placeholder" > /app/static/icons/icon-128x128.png && \
    echo "Icon placeholder" > /app/static/icons/icon-144x144.png && \
    echo "Icon placeholder" > /app/static/icons/icon-152x152.png && \
    echo "Icon placeholder" > /app/static/icons/icon-180x180.png && \
    echo "Icon placeholder" > /app/static/icons/icon-192x192.png && \
    echo "Icon placeholder" > /app/static/icons/icon-384x384.png && \
    echo "Icon placeholder" > /app/static/icons/icon-512x512.png && \
    echo "Screenshot placeholder" > /app/static/screenshots/desktop-1.png && \
    echo "Screenshot placeholder" > /app/static/screenshots/mobile-1.png

# Set ownership
RUN chown -R fleetapp:fleetapp /app

# Expose port
EXPOSE 5000 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Initialize database if needed\n\
python -c "from app import app, db; app.app_context().push(); db.create_all(); print(\"Database initialized\")" || true\n\
\n\
# Start supervisor to manage nginx and gunicorn\n\
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER fleetapp

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command is handled by supervisor
CMD []