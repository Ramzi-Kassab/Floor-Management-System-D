# Installation Guide
## ARDT Floor Management System

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB SSD |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 LTS |

### Software Requirements

```bash
# Python 3.11+
python3 --version

# PostgreSQL 16
psql --version

# Node.js 18+ (for Tailwind CSS compilation)
node --version

# Redis (for Celery background tasks)
redis-server --version

# Git
git --version
```

---

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url> ardt-fms
cd ardt-fms
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Setup

#### PostgreSQL Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE ardt_fms;
CREATE USER ardt_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ardt_fms TO ardt_user;

# Grant schema permissions (PostgreSQL 15+)
\c ardt_fms
GRANT ALL ON SCHEMA public TO ardt_user;

# Exit psql
\q
```

### 5. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Environment Variables:**

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DATABASE_URL=postgres://ardt_user:secure_password@localhost:5432/ardt_fms

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 6. Run Migrations

```bash
# Apply all migrations
python manage.py migrate

# Verify migration status
python manage.py showmigrations
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Load Initial Data (Optional)

```bash
# Load fixtures if available
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/step_types.json
python manage.py loaddata fixtures/field_types.json
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Access: http://localhost:8000/admin

---

## Verification

### System Validation

```bash
# Run system validation script
python scripts/system_validation.py
```

Expected output:
- 173 models registered
- 21 apps loaded
- All migrations applied
- Admin registrations complete

### Run Tests

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=apps

# Run specific tests
pytest apps/sales/tests/
```

Expected: 438 tests passing

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

```
django.db.utils.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection settings
psql -h localhost -U ardt_user -d ardt_fms
```

#### 2. Migration Errors

```
django.db.utils.ProgrammingError: relation does not exist
```

**Solution:**
```bash
# Reset migrations (development only)
python manage.py migrate --fake-initial

# Or recreate database
dropdb ardt_fms
createdb ardt_fms
python manage.py migrate
```

#### 3. Permission Denied

```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod -R 755 .
```

#### 4. Import Errors

```
ModuleNotFoundError: No module named 'apps.xxx'
```

**Solution:**
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

---

## Optional Components

### Redis Setup

```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping
# Should return: PONG
```

### Celery Workers

```bash
# Start Celery worker
celery -A ardt_fms worker -l info

# Start Celery beat (scheduler)
celery -A ardt_fms beat -l info
```

### Tailwind CSS (Development)

```bash
# Install Node dependencies
npm install

# Build CSS
npm run build:css

# Watch for changes
npm run watch:css
```

---

## Next Steps

1. Review [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Run tests to verify installation
4. Configure email settings for notifications

---

**Version:** 1.0
**Last Updated:** December 2024
