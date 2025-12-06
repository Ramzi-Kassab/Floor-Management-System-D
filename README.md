# ARDT Floor Management System v5.4

**Advanced Rework & Drill Bits Technology - Floor Management System**
Production-Ready Implementation - All 8 Sprints Complete

---

## Overview

A comprehensive Django 5.1 enterprise application for managing drill bit manufacturing, field services, supply chain, quality control, and workforce operations. Built for ARDT's floor management needs with full HTMX/Alpine.js frontend integration.

**Status:** Production Ready
**Models:** 173 across 21 applications
**Test Coverage:** 438 tests, 63% overall (84-97% model coverage)

---

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd Floor-Management-System-D

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Access at: http://localhost:8000/admin

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Django | 5.1 | Web framework |
| PostgreSQL | 16 | Database |
| HTMX | 2.0 | Dynamic UI |
| Alpine.js | 3.14 | Reactive components |
| Tailwind CSS | 3.4 | Styling |
| Celery + Redis | - | Background tasks |
| pytest | 8.0 | Testing |

---

## Application Structure

```
ardt_fms/
├── ardt_fms/              # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI entry point
├── apps/                  # 21 Django applications
│   ├── core/              # Base models, utilities
│   ├── accounts/          # Authentication, roles
│   ├── organization/      # Departments, positions
│   ├── sales/             # Customers, field service
│   ├── workorders/        # Work orders, drill bits
│   ├── technology/        # Designs, BOMs
│   ├── supplychain/       # Vendors, procurement
│   ├── compliance/        # Quality, NCRs
│   ├── hr/                # Workforce management
│   └── ...                # Additional apps
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── requirements.txt       # Dependencies
```

---

## Core Features

### Work Order Management
- Multiple WO types (NEW, REPAIR, REWORK, RETROFIT)
- Drill bit lifecycle tracking with QR codes
- Material and time tracking
- Quality control integration

### Field Service Operations
- Customer and service site management
- Field service requests with scheduling
- Technician assignments and dispatch
- On-site inspection reporting

### Supply Chain
- Vendor qualification and management
- Purchase requisitions and orders
- Receiving and inventory control
- Invoice and payment tracking

### Quality & Compliance
- Quality control inspections
- Non-conformance reports (NCRs)
- Corrective actions (CAPAs)
- Audit management

### Workforce Management
- Employee records and documents
- Time and attendance tracking
- Leave management
- Performance reviews
- Training and certifications

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test suite
pytest apps/sales/tests/
pytest apps/common/tests/test_integration_suite.py
```

**Test Distribution:**
- Sprint Smoke Tests: 195
- Integration Tests: 21
- Performance Tests: 9
- Edge Case Tests: 17
- Model Tests: 196

---

## Development Commands

```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Django shell
python manage.py shell

# System validation
python scripts/system_validation.py

# Production checks
python manage.py check --deploy
python manage.py collectstatic
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [INSTALLATION.md](docs/INSTALLATION.md) | Detailed setup guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [TEST_COVERAGE_REPORT.md](docs/TEST_COVERAGE_REPORT.md) | Test coverage analysis |
| [DEFERRED_ENHANCEMENTS.md](docs/DEFERRED_ENHANCEMENTS.md) | Future enhancements |

---

## Sprint Completion Status

| Sprint | Focus | Status |
|--------|-------|--------|
| Sprint 1-3 | Core foundation | Complete |
| Sprint 4 | Work orders, quality | Complete |
| Sprint 5 | Field service (40 models) | Complete |
| Sprint 6 | Supply chain (18 models) | Complete |
| Sprint 7 | Compliance (9 models) | Complete |
| Sprint 8 | HR workforce (9 models) | Complete |

---

## Model Categories

| Category | Count | Coverage |
|----------|-------|----------|
| Core Models | 15 | 85%+ |
| Sales/Field Service | 40 | 84%+ |
| Work Orders | 12 | 86%+ |
| Supply Chain | 18 | 86%+ |
| Compliance | 9 | 87%+ |
| HR/Workforce | 9 | 90%+ |
| Technology | 15 | 95%+ |
| Other | 55 | 85%+ |

---

## Environment Variables

```bash
# .env configuration
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@localhost:5432/ardt_fms
ALLOWED_HOSTS=your-domain.com
REDIS_URL=redis://localhost:6379/0
```

---

## License

Proprietary - ARDT Internal Use Only

---

## Support

For issues and feature requests, contact the development team.

---

**Version:** 5.4
**Last Updated:** December 2024
**Maintainer:** ARDT Development Team
