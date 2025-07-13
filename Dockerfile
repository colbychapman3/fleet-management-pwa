# Render-optimized Dockerfile for Fleet Management PWA
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/static/icons /app/static/screenshots

# Create placeholder icons (for PWA)
RUN echo "Icon placeholder" > /app/static/icons/icon-192x192.png && \
    echo "Icon placeholder" > /app/static/icons/icon-512x512.png

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Simple startup command for Render with error handling
CMD python -c "
import sys
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    print('Starting app anyway - database will be initialized on first request')
    pass
" && gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - app:app