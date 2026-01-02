#!/bin/bash
# =============================================================================
# ARDT FMS - Codespaces Post-Create Setup Script
# =============================================================================
# This script runs automatically when a Codespace is created.
# It sets up the development environment completely.
# =============================================================================

set -e  # Exit on error

echo "=============================================="
echo "  ARDT Floor Management System Setup"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Install Python dependencies (must be first for Django SECRET_KEY gen)
# -----------------------------------------------------------------------------
echo "[1/8] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""

# -----------------------------------------------------------------------------
# Step 2: Create .env file from template if it doesn't exist
# -----------------------------------------------------------------------------
echo "[2/8] Setting up environment variables..."

if [ ! -f .env ]; then
    cp .env.example .env

    # Generate a secure SECRET_KEY using Python (handles special chars safely)
    python << 'PYEOF'
import re
from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()

with open('.env', 'r') as f:
    content = f.read()

# Replace SECRET_KEY line safely
content = re.sub(r'SECRET_KEY=.*', f'SECRET_KEY={secret_key}', content)

with open('.env', 'w') as f:
    f.write(content)

print(f"   - Generated SECRET_KEY")
PYEOF

    echo "   - Created .env file"
else
    echo "   - .env file already exists"
    # Ensure SECRET_KEY is set even if .env exists
    if ! grep -q "^SECRET_KEY=." .env || grep -q "^SECRET_KEY=your-secret-key" .env; then
        echo "   - SECRET_KEY appears empty or placeholder, generating..."
        python << 'PYEOF'
import re
from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()

with open('.env', 'r') as f:
    content = f.read()

content = re.sub(r'SECRET_KEY=.*', f'SECRET_KEY={secret_key}', content)

with open('.env', 'w') as f:
    f.write(content)

print(f"   - Generated new SECRET_KEY")
PYEOF
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# Step 3: Create required directories
# -----------------------------------------------------------------------------
echo "[3/8] Creating required directories..."
mkdir -p logs media staticfiles
echo ""

# -----------------------------------------------------------------------------
# Step 4: Run database migrations (with safe fallback for branched migrations)
# -----------------------------------------------------------------------------
echo "[4/8] Running database migrations..."

# Note: This project has branched migrations in inventory and technology apps
# that merge back together. On fresh databases, we use a safe approach.

if python manage.py migrate --no-input 2>&1; then
    echo "   - Migrations applied successfully"
else
    echo "   - Standard migration failed, trying --fake-initial..."
    if python manage.py migrate --fake-initial --no-input 2>&1; then
        echo "   - Migrations applied with --fake-initial"
    else
        echo "   - Fallback: faking problematic apps and retrying..."
        python manage.py migrate inventory --fake --no-input 2>/dev/null || true
        python manage.py migrate technology --fake --no-input 2>/dev/null || true
        python manage.py migrate --no-input
        echo "   - Migrations completed with fallback"
    fi
fi

# Verify migrations
echo "   - Checking migration status..."
PENDING=$(python manage.py showmigrations | grep "\[ \]" | wc -l)
if [ "$PENDING" -eq 0 ]; then
    echo "   - All migrations applied successfully"
else
    echo "   - Warning: $PENDING migrations may be pending"
fi
echo ""

# -----------------------------------------------------------------------------
# Step 5: Collect static files
# -----------------------------------------------------------------------------
echo "[5/8] Collecting static files..."
python manage.py collectstatic --no-input
echo ""

# -----------------------------------------------------------------------------
# Step 6: Seed database with initial data
# -----------------------------------------------------------------------------
echo "[6/8] Seeding database with initial data..."
python manage.py seed_all
echo ""

# -----------------------------------------------------------------------------
# Step 7: Restore technology data if backup exists
# -----------------------------------------------------------------------------
echo "[7/8] Checking for technology data backup..."
if [ -f data/technology_data_latest.json ]; then
    echo "   - Found backup: data/technology_data_latest.json"
    echo "   - Restoring technology data (Designs, BOMs)..."
    python manage.py import_technology_data data/technology_data_latest.json --force
    echo "   ✓ Technology data restored successfully"
else
    echo "   - No backup found (data/technology_data_latest.json)"
    echo "   - To preserve your data before container rebuild, run:"
    echo "     python manage.py export_technology_data"
fi
echo ""

# -----------------------------------------------------------------------------
# Step 8: Create superuser
# -----------------------------------------------------------------------------
echo "[8/8] Creating superuser..."

# Create superuser using Django shell to avoid interactive prompts
python manage.py shell << 'EOF'
from apps.accounts.models import User

# Check if superuser already exists
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='ramzikassab1982@gmail.com',
        password='Ra@mzi@123'
    )
    print(f"   - Superuser 'admin' created successfully")
else:
    print("   - Superuser 'admin' already exists")
EOF

echo ""

# -----------------------------------------------------------------------------
# Run tests to verify setup
# -----------------------------------------------------------------------------
echo "=============================================="
echo "  Running tests to verify setup..."
echo "=============================================="
python manage.py test --verbosity=1 || echo "Some tests may have failed - check output above"
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "  Superuser credentials:"
echo "    Username: admin"
echo "    Password: Ra@mzi@123"
echo "    Email: ramzikassab1982@gmail.com"
echo ""
echo "  To start the development server:"
echo "    python manage.py runserver"
echo ""
echo "  Or use VS Code: Terminal > Run Task > Django: Run Server"
echo ""
echo "  ⚠️  DATA PERSISTENCE:"
echo "  Before rebuilding container, backup your data:"
echo "    python manage.py export_technology_data"
echo ""
echo "  Data will auto-restore on next container rebuild."
echo ""
echo "=============================================="

# Start the development server
echo ""
echo "Starting development server on port 8000..."
python manage.py runserver 0.0.0.0:8000
