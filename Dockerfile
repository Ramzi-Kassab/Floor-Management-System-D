# ARDT Floor Management System - Docker Configuration
# Multi-stage build for production deployment

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Create non-root user
RUN addgroup --system --gid 1001 ardt \
    && adduser --system --uid 1001 --gid 1001 ardt

# Copy application code
COPY --chown=ardt:ardt . .

# Create directories for static/media files
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R ardt:ardt /app/staticfiles /app/media

# Switch to non-root user
USER ardt

# Collect static files
RUN python manage.py collectstatic --noinput --settings=ardt_fms.settings || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "ardt_fms.wsgi:application"]
