# 🚀 CODESPACES SETUP GUIDE
## ARDT FMS - GitHub Codespaces Configuration

**Date:** December 6, 2024  
**Project:** ARDT Floor Management System v5.4  
**Target:** Production-ready Codespaces environment  

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Files to Create](#files)
4. [Configuration Steps](#steps)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## 📊 OVERVIEW {#overview}

### **What is Codespaces?**

GitHub Codespaces provides a complete development environment in the cloud:
- Pre-configured VS Code editor
- Full terminal access
- PostgreSQL database
- Redis cache
- All dependencies installed
- Ready to code in 2-3 minutes

### **What We'll Configure:**

1. ✅ Development container (.devcontainer/)
2. ✅ PostgreSQL database
3. ✅ Redis cache  
4. ✅ VS Code extensions
5. ✅ Auto-setup scripts
6. ✅ Environment variables

### **Timeline:**

- Setup files: 30 minutes
- First Codespace launch: 2-3 minutes
- Total: You'll be coding in 30-35 minutes!

---

## 🎯 PREREQUISITES {#prerequisites}

### **Required:**

1. ✅ GitHub repository (you have this)
2. ✅ GitHub account with Codespaces access
3. ✅ Basic knowledge of GitHub

### **Not Required:**

- ❌ Local Python installation
- ❌ Local PostgreSQL installation
- ❌ Local Redis installation
- ❌ Local IDE setup

**Everything runs in the cloud!**

---

## 📁 FILES TO CREATE {#files}

### **Directory Structure:**

```
your-project/
├── .devcontainer/
│   ├── devcontainer.json      # Main config
│   ├── docker-compose.yml     # Services
│   ├── Dockerfile             # Custom image
│   └── post-create.sh         # Setup script
├── .env.codespaces            # Environment template
└── docs/
    └── CODESPACES_QUICKSTART.md
```

---

## 🔧 CONFIGURATION FILES {#files-detail}

### **FILE 1: .devcontainer/devcontainer.json**

Create this file:

```json
{
  "name": "ARDT FMS Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11",
      "installTools": true
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "18"
    },
    "ghcr.io/devcontainers/features/git:1": {
      "version": "latest"
    }
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.isort",
        "batisteo.vscode-django",
        "mtxr.sqltools",
        "mtxr.sqltools-driver-pg",
        "esbenp.prettier-vscode",
        "bradlc.vscode-tailwindcss",
        "GitHub.copilot",
        "eamodio.gitlens"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": false,
        "python.linting.flake8Enabled": true,
        "python.formatting.provider": "black",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.organizeImports": true
        },
        "files.exclude": {
          "**/__pycache__": true,
          "**/*.pyc": true
        }
      }
    }
  },
  
  "forwardPorts": [
    8000,  // Django
    5432,  // PostgreSQL
    6379   // Redis
  ],
  
  "portsAttributes": {
    "8000": {
      "label": "Django Application",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "PostgreSQL Database"
    },
    "6379": {
      "label": "Redis Cache"
    }
  },
  
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  
  "remoteUser": "vscode"
}
```

---

### **FILE 2: .devcontainer/docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    
    volumes:
      - ..:/workspace:cached
    
    command: sleep infinity
    
    environment:
      # Database
      DATABASE_URL: postgresql://ardt:ardt_password@db:5432/ardt_fms
      
      # Django
      SECRET_KEY: 'dev-secret-key-change-in-production-12345678901234567890'
      DEBUG: 'True'
      ALLOWED_HOSTS: 'localhost,127.0.0.1,*.githubpreview.dev,*.preview.app.github.dev'
      
      # Logging
      DJANGO_LOG_LEVEL: 'INFO'
      
      # Redis
      REDIS_URL: redis://redis:6379/0
    
    depends_on:
      - db
      - redis
    
    networks:
      - ardt-network
  
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    
    volumes:
      - postgres-data:/var/lib/postgresql/data
    
    environment:
      POSTGRES_USER: ardt
      POSTGRES_PASSWORD: ardt_password
      POSTGRES_DB: ardt_fms
    
    networks:
      - ardt-network
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ardt"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
    volumes:
      - redis-data:/data
    
    networks:
      - ardt-network
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  redis-data:

networks:
  ardt-network:
    driver: bridge
```

---

### **FILE 3: .devcontainer/Dockerfile**

```dockerfile
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
# Note: This layer is cached unless requirements.txt changes
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    ipython \
    django-debug-toolbar \
    django-extensions \
    werkzeug

# Create logs directory
RUN mkdir -p /workspace/logs

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Default command
CMD ["sleep", "infinity"]
```

---

### **FILE 4: .devcontainer/post-create.sh**

```bash
#!/bin/bash
set -e

echo "======================================"
echo "🚀 ARDT FMS Post-Create Setup"
echo "======================================"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until python -c "import psycopg; psycopg.connect('$DATABASE_URL')" 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready!"
echo ""

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; do
  echo "   Redis is unavailable - sleeping"
  sleep 1
done
echo "✅ Redis is ready!"
echo ""

# Install/upgrade Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.codespaces .env
    echo "✅ .env file created!"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations --no-input
python manage.py migrate --no-input
echo "✅ Migrations complete!"
echo ""

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@ardt.local',
        password='admin',
        first_name='Admin',
        last_name='User'
    )
    print('✅ Superuser created: admin / admin')
else:
    print('ℹ️  Superuser already exists')
EOF
echo ""

# Load demo data
echo "🎭 Loading demo data..."
python manage.py load_demo_data
echo "✅ Demo data loaded!"
echo ""

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input --clear
echo "✅ Static files collected!"
echo ""

# Display success message
echo "======================================"
echo "✅ ARDT FMS Setup Complete!"
echo "======================================"
echo ""
echo "🎉 You're ready to start developing!"
echo ""
echo "Quick commands:"
echo "  • Run server:    python manage.py runserver"
echo "  • Run tests:     pytest"
echo "  • Django shell:  python manage.py shell_plus"
echo "  • Admin panel:   http://localhost:8000/admin"
echo "                   Username: admin"
echo "                   Password: admin"
echo ""
echo "Happy coding! 🚀"
echo ""
```

Make it executable:
```bash
chmod +x .devcontainer/post-create.sh
```

---

### **FILE 5: .env.codespaces**

```bash
# =============================================================================
# ARDT FMS - Codespaces Environment Variables
# =============================================================================
# 
# This file is used by Codespaces for local development.
# DO NOT commit actual .env file to git!
# =============================================================================

# Database
DATABASE_URL=postgresql://ardt:ardt_password@db:5432/ardt_fms

# Django Core
SECRET_KEY=dev-secret-key-change-in-production-12345678901234567890
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.preview.app.github.dev

# Logging
DJANGO_LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://redis:6379/0

# Email (Optional - for testing)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Static/Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Security (Disabled in development)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

---

### **FILE 6: docs/CODESPACES_QUICKSTART.md**

```markdown
# 🚀 Codespaces Quick Start Guide

## Launch Codespace

1. Go to your GitHub repository
2. Click "Code" → "Codespaces" → "Create codespace on main"
3. Wait 2-3 minutes for setup
4. Codespace opens with VS Code

## First Time Setup

The setup script runs automatically:
- ✅ Installs dependencies
- ✅ Creates database
- ✅ Runs migrations
- ✅ Creates superuser (admin/admin)
- ✅ Loads demo data

## Start Development

### 1. Run the Server

```bash
python manage.py runserver
```

Click the notification to open in browser, or:
- Open "Ports" tab
- Click the globe icon next to port 8000

### 2. Access Admin Panel

```
URL: http://localhost:8000/admin
Username: admin
Password: admin
```

### 3. Run Tests

```bash
# All tests
pytest

# Specific app
pytest apps/workorders/tests/

# With coverage
pytest --cov=apps --cov-report=html
```

### 4. Database Access

```bash
# Django shell
python manage.py shell_plus

# Direct PostgreSQL
psql $DATABASE_URL
```

## Common Commands

```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load demo data
python manage.py load_demo_data

# Run tests
pytest

# Format code
black apps/
isort apps/

# Lint code
flake8 apps/
```

## Stopping Codespace

- Click your avatar (top right)
- "Stop current codespace"

Your work is automatically saved!

## Troubleshooting

### Database Connection Error

```bash
# Restart database
docker compose restart db

# Wait for it to be ready
until psql $DATABASE_URL -c "SELECT 1" > /dev/null 2>&1; do
  echo "Waiting for database..."
  sleep 2
done
```

### Port Already in Use

```bash
# Kill the process
pkill -f runserver

# Or use a different port
python manage.py runserver 0.0.0.0:8001
```

## Support

For issues, see:
- [Troubleshooting Guide](guides/TROUBLESHOOTING.md)
- [Developer Guide](guides/DEVELOPER_GUIDE.md)
```

---

## 🔄 CONFIGURATION STEPS {#steps}

### **Step 1: Create .devcontainer Directory (2 min)**

```bash
cd /path/to/your/project
mkdir -p .devcontainer
```

### **Step 2: Create All Config Files (10 min)**

Copy content from above into each file:

```bash
# Create each file
touch .devcontainer/devcontainer.json
touch .devcontainer/docker-compose.yml
touch .devcontainer/Dockerfile
touch .devcontainer/post-create.sh
touch .env.codespaces
touch docs/CODESPACES_QUICKSTART.md

# Make post-create.sh executable
chmod +x .devcontainer/post-create.sh
```

### **Step 3: Update .gitignore (2 min)**

Add to `.gitignore`:

```bash
# Environment
.env
.env.local

# Codespaces
.devcontainer/.env

# Keep .devcontainer config files
!.devcontainer/devcontainer.json
!.devcontainer/docker-compose.yml
!.devcontainer/Dockerfile
!.devcontainer/post-create.sh
```

### **Step 4: Commit Configuration (5 min)**

```bash
git add .devcontainer/
git add .env.codespaces
git add docs/CODESPACES_QUICKSTART.md
git add .gitignore

git commit -m "feat: Add GitHub Codespaces configuration

- Configured dev container with Python 3.11
- Added PostgreSQL 16 and Redis 7
- Auto-setup script for migrations and demo data
- VS Code extensions for Django development
- Environment template for Codespaces
- Quick start documentation"

git push
```

### **Step 5: Test in Codespaces (3 min)**

1. Go to GitHub repository
2. Click "Code" → "Codespaces"
3. Click "Create codespace on main"
4. Wait for setup (2-3 minutes)
5. Terminal should show: "✅ ARDT FMS Setup Complete!"

---

## ✅ TESTING {#testing}

### **Test 1: Server Starts**

```bash
python manage.py runserver
```

Expected:
- Server starts on port 8000
- No errors
- Can access http://localhost:8000

### **Test 2: Admin Access**

Visit: http://localhost:8000/admin
- Username: admin
- Password: admin

Expected:
- Login succeeds
- See all apps and models

### **Test 3: Database Works**

```bash
python manage.py shell
```

```python
from apps.workorders.models import WorkOrder
print(WorkOrder.objects.count())
# Should show demo data count
```

### **Test 4: Tests Pass**

```bash
pytest
```

Expected:
- 438 tests pass
- No failures

### **Test 5: Demo Data Loaded**

Visit admin and check:
- Users: Should have demo users
- Work Orders: Should have demo orders
- Customers: Should have demo customers

---

## 🔧 TROUBLESHOOTING {#troubleshooting}

### **Issue: Codespace Won't Start**

**Solution:**
1. Delete the Codespace
2. Create a new one
3. Check logs for errors

### **Issue: Database Connection Failed**

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
docker compose restart db

# Check connection
psql $DATABASE_URL -c "SELECT 1"
```

### **Issue: Port 8000 Already in Use**

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
python manage.py runserver 0.0.0.0:8001
```

### **Issue: Migrations Error**

```bash
# Reset database
python manage.py flush --no-input

# Re-run migrations
python manage.py migrate

# Reload demo data
python manage.py load_demo_data
```

### **Issue: Missing Dependencies**

```bash
# Reinstall
pip install -r requirements.txt

# Or rebuild container
# (From VS Code command palette)
# > Rebuild Container
```

---

## 🎯 NEXT STEPS

### **After Codespaces is Working:**

1. ✅ **Start Development**
   - Fix high-priority issues from system review
   - Add role-based permissions
   - Optimize N+1 queries

2. ✅ **Create Pull Requests**
   - Small, focused changes
   - Good commit messages
   - Tests included

3. ✅ **Collaborate**
   - Share Codespace link with team
   - Code together in real-time
   - Review code in browser

4. ✅ **Deploy**
   - When ready, deploy to production
   - See DEPLOYMENT.md guide

---

## 📊 SUMMARY

### **What You Get:**

✅ **Full Dev Environment** in 2-3 minutes
✅ **PostgreSQL Database** pre-configured
✅ **Redis Cache** ready to use
✅ **VS Code Extensions** auto-installed
✅ **Demo Data** pre-loaded
✅ **Superuser** created (admin/admin)
✅ **All Tests** passing

### **No Local Setup Needed:**

❌ No Python installation
❌ No PostgreSQL installation
❌ No Redis installation
❌ No environment configuration
❌ No dependency management

### **Just Code!**

🚀 Open Codespace
🚀 Start server
🚀 Start coding

---

## 🎉 YOU'RE READY!

**Your Codespaces environment is configured and ready to use!**

**To launch:**
1. Go to GitHub
2. Click "Code" → "Codespaces"
3. Click "Create codespace on main"
4. Wait 2-3 minutes
5. **Start coding!** 🎯

---

**END OF CODESPACES SETUP GUIDE**

**Next:** Review COMPREHENSIVE_SYSTEM_REVIEW.md for development priorities
