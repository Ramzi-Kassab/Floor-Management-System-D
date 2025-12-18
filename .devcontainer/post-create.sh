#!/bin/bash
set -e

echo "======================================"
echo "  ARDT FMS - Codespaces Setup"
echo "======================================"
echo ""

# Function to wait for service
wait_for_service() {
    local service=$1
    local check_cmd=$2
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service..."
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_cmd" > /dev/null 2>&1; then
            echo "  $service is ready!"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "  WARNING: $service may not be ready after $max_attempts attempts"
    return 1
}

# Wait for PostgreSQL
echo ""
echo "Step 1: Checking database connection..."
wait_for_service "PostgreSQL" "pg_isready -h db -U ardt"

# Wait for Redis
echo ""
echo "Step 2: Checking Redis connection..."
wait_for_service "Redis" "redis-cli -h redis ping"

# Install/upgrade Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null 2>&1 || pip install -r requirements.txt
echo "  Dependencies installed!"

# Create .env file if it doesn't exist
echo ""
echo "Step 4: Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.codespaces ]; then
        cp .env.codespaces .env
        echo "  Created .env from .env.codespaces"
    else
        # Create minimal .env from docker-compose environment
        cat > .env << EOF
# Auto-generated for Codespaces
DEBUG=True
SECRET_KEY=dev-secret-key-for-codespaces-only-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.app.github.dev,*.preview.app.github.dev
DATABASE_URL=postgresql://ardt:ardt_password@db:5432/ardt_fms
REDIS_URL=redis://redis:6379/0
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOF
        echo "  Created default .env file"
    fi
else
    echo "  .env file already exists"
fi

# Run Django checks
echo ""
echo "Step 5: Running Django system checks..."
python manage.py check --deploy 2>/dev/null || python manage.py check

# Run database migrations
echo ""
echo "Step 6: Running database migrations..."
python manage.py migrate --no-input
echo "  Migrations complete!"

# Create superuser if it doesn't exist
echo ""
echo "Step 7: Setting up admin user..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@ardt.local',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("  Created superuser: admin / admin123")
else:
    print("  Superuser 'admin' already exists")
EOF

# Load fixtures if available
echo ""
echo "Step 8: Loading initial data..."
if [ -f fixtures/initial_data.json ]; then
    python manage.py loaddata fixtures/initial_data.json 2>/dev/null && echo "  Loaded initial_data.json" || echo "  Skipped initial_data.json"
fi

# Collect static files (optional, can be slow)
echo ""
echo "Step 9: Collecting static files..."
python manage.py collectstatic --no-input --clear > /dev/null 2>&1 || echo "  Static collection skipped"
echo "  Static files ready!"

# Final message
echo ""
echo "======================================"
echo "  ARDT FMS Setup Complete!"
echo "======================================"
echo ""
echo "Quick Start:"
echo "  1. Run server:    python manage.py runserver 0.0.0.0:8000"
echo "  2. Admin panel:   http://localhost:8000/admin"
echo "                    Username: admin"
echo "                    Password: admin123"
echo "  3. Run tests:     python manage.py test"
echo "  4. Django shell:  python manage.py shell"
echo ""
echo "Happy coding!"
echo ""
