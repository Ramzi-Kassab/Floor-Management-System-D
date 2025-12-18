# ARDT FMS - Development Container
# Python 3.11 with PostgreSQL client and development tools

FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        postgresql-client \
        libpq-dev \
        build-essential \
        git \
        curl \
        vim \
        htop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
# This layer is cached unless requirements.txt changes
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    ipython \
    django-debug-toolbar \
    django-extensions \
    flake8 \
    black \
    isort \
    pytest \
    pytest-django \
    pytest-cov

# Create directories for logs and media
RUN mkdir -p /workspace/logs /workspace/media /workspace/staticfiles

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Default command
CMD ["sleep", "infinity"]
