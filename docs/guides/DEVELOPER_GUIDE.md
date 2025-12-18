# Developer Guide
## ARDT Floor Management System

---

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Node.js 18+ (for frontend assets)
- Git

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Floor-Management-System-D

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

---

## Project Structure

```
Floor-Management-System-D/
├── ardt_fms/              # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI entry point
├── apps/                  # Django applications
│   ├── accounts/          # Authentication, roles
│   ├── common/            # Shared utilities
│   ├── compliance/        # Quality, NCRs
│   ├── hr/                # Workforce management
│   ├── sales/             # Customers, field service
│   ├── supplychain/       # Vendors, procurement
│   ├── workorders/        # Work orders, drill bits
│   └── ...                # Additional apps
├── docs/                  # Documentation
├── fixtures/              # Initial data
├── scripts/               # Utility scripts
├── templates/             # Global templates
└── requirements.txt       # Dependencies
```

---

## Coding Standards

### Python Style

Follow PEP 8 with these additions:
- Line length: 120 characters max
- Use type hints for function parameters
- Docstrings for all public methods

```python
def calculate_total(items: list[dict], tax_rate: float = 0.0) -> float:
    """
    Calculate total amount with optional tax.

    Args:
        items: List of items with 'price' and 'quantity' keys
        tax_rate: Tax rate as decimal (0.1 = 10%)

    Returns:
        Total amount including tax
    """
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    return subtotal * (1 + tax_rate)
```

### Model Conventions

```python
class MyModel(models.Model):
    """
    Brief description of the model.

    Used for: [purpose]
    Related to: [other models]
    """

    # Fields with help_text
    name = models.CharField(max_length=100, help_text="Display name")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status"
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_%(class)ss"
    )

    class Meta:
        db_table = "my_model"
        ordering = ["-created_at"]
        verbose_name = "My Model"
        verbose_name_plural = "My Models"

    def __str__(self):
        return self.name
```

### Auto-ID Generation

Use the auto-ID pattern for models requiring generated IDs:

```python
def save(self, *args, **kwargs):
    if not self.my_number:
        prefix = "MY"
        last = MyModel.objects.order_by("-id").first()
        if last and last.my_number:
            num = int(last.my_number.split("-")[1]) + 1
        else:
            num = 1
        self.my_number = f"{prefix}-{num:06d}"
    super().save(*args, **kwargs)
```

---

## Permission System

### Using Decorators (Function-Based Views)

```python
from apps.accounts.decorators import role_required, permission_required

@role_required('ADMIN')
def admin_only_view(request):
    ...

@permission_required('workorders.create')
def create_work_order(request):
    ...

@role_required(['ADMIN', 'MANAGER'])
def management_view(request):
    ...
```

### Using Mixins (Class-Based Views)

```python
from apps.accounts.mixins import RoleRequiredMixin, PermissionRequiredMixin

class AdminView(RoleRequiredMixin, View):
    required_roles = 'ADMIN'

class WorkOrderCreateView(PermissionRequiredMixin, CreateView):
    required_permissions = ['workorders.create']
```

### Template Permission Checks

```html
{% if perms.has_role.ADMIN %}
    <a href="{% url 'admin:index' %}">Admin Panel</a>
{% endif %}

{% if perms.has_permission.workorders_create %}
    <button>Create Work Order</button>
{% endif %}
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/workorders/tests/

# Run specific test file
pytest apps/common/tests/test_views.py

# Verbose output
pytest -v

# Run in parallel
pytest -n auto
```

### Writing Tests

```python
import pytest
from django.test import Client

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )

class TestMyView:
    def test_view_requires_login(self, client):
        response = client.get('/my-url/')
        assert response.status_code == 302

    def test_view_accessible_when_logged_in(self, client, user):
        client.force_login(user)
        response = client.get('/my-url/')
        assert response.status_code == 200
```

---

## Database

### Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name migration_number
```

### Query Optimization

Always use `select_related` and `prefetch_related`:

```python
# Bad - N+1 queries
orders = WorkOrder.objects.all()
for order in orders:
    print(order.customer.name)  # Query per order

# Good - Single query
orders = WorkOrder.objects.select_related('customer').all()
for order in orders:
    print(order.customer.name)  # No additional queries
```

### Admin Optimization

```python
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ["wo_number", "customer", "status"]
    list_select_related = ["customer", "assigned_to"]  # Add this!
```

---

## API Development

### Creating an API Endpoint

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def api_work_orders(request):
    orders = WorkOrder.objects.select_related('customer')[:50]
    data = [{
        'id': o.id,
        'wo_number': o.wo_number,
        'customer': o.customer.name,
        'status': o.status,
    } for o in orders]
    return JsonResponse({'orders': data})
```

---

## Debugging

### Django Debug Toolbar

Enabled in development. View at: `/__debug__/`

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Processing started")
    try:
        # ... code ...
        logger.debug("Detail info")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
```

### Shell Commands

```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Run script
python manage.py runscript my_script
```

---

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Production fixes

### Commit Messages

```
type: Brief description

Longer explanation if needed.

Types: feat, fix, docs, style, refactor, test, chore
```

---

## Useful Commands

```bash
# System validation
python scripts/system_validation.py

# Production checks
python manage.py check --deploy

# Collect static files
python manage.py collectstatic

# Clear cache
python manage.py clear_cache

# Load demo data
python manage.py load_demo_data
```

---

**Version:** 5.4
**Last Updated:** December 2024
