# System Architecture
## ARDT Floor Management System

---

## Overview

The ARDT Floor Management System is a modular Django application designed for managing drill bit manufacturing operations, field services, supply chain, and workforce management.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Browser │  │  Mobile  │  │   API    │  │  Admin   │   │
│  │  (HTMX)  │  │   App    │  │ Clients  │  │  Panel   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼─────────┐
│                      Nginx (Reverse Proxy)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Django Application                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   URL Routing                       │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Middleware Stack                       │    │
│  │  (Auth, Session, CSRF, Security, Audit)            │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │                 Application Layer                   │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │    │
│  │  │  Views  │ │  Forms  │ │ Signals │ │  Utils  │  │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │                    Model Layer                      │    │
│  │           173 Models across 21 Apps                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  PostgreSQL   │ │     Redis     │ │  File Storage │
│   Database    │ │  Cache/Queue  │ │    (Media)    │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## Application Modules

### Core Applications

| App | Purpose | Models |
|-----|---------|--------|
| `core` | Base models, utilities | 5 |
| `accounts` | Authentication, users, roles | 8 |
| `organization` | Departments, positions | 6 |

### Business Applications

| App | Purpose | Models |
|-----|---------|--------|
| `sales` | Customers, field service | 40 |
| `workorders` | Work orders, drill bits | 12 |
| `technology` | Designs, BOMs | 15 |
| `supplychain` | Vendors, procurement | 18 |
| `compliance` | Quality, NCRs, audits | 9 |
| `hr` | Workforce, attendance | 9 |

### Support Applications

| App | Purpose | Models |
|-----|---------|--------|
| `inventory` | Stock management | 8 |
| `scancodes` | QR/barcode tracking | 4 |
| `notifications` | Alerts, tasks | 6 |
| `documents` | Document management | 5 |
| `reports` | Report generation | 4 |

---

## Data Flow Patterns

### Work Order Lifecycle

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  DRAFT  │───▶│ PLANNED │───▶│RELEASED │───▶│IN_PROG  │
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
                                                  │
     ┌────────────────────────────────────────────┘
     │
┌────▼────┐    ┌─────────┐    ┌─────────┐
│QC_PEND  │───▶│QC_PASS  │───▶│COMPLETED│
└────┬────┘    └─────────┘    └─────────┘
     │
┌────▼────┐
│QC_FAIL  │
└─────────┘
```

### Field Service Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Customer   │───▶│   Request    │───▶│  Assignment  │
│   Request    │    │   Approval   │    │  Scheduling  │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
     ┌─────────────────────────────────────────┘
     │
┌────▼─────────┐    ┌──────────────┐    ┌──────────────┐
│  Technician  │───▶│   On-Site    │───▶│    Report    │
│   Dispatch   │    │   Service    │    │   Complete   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Procurement Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Requisition  │───▶│   Approval   │───▶│   Purchase   │
│   (Draft)    │    │   Workflow   │    │    Order     │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
     ┌─────────────────────────────────────────┘
     │
┌────▼─────────┐    ┌──────────────┐    ┌──────────────┐
│   Vendor     │───▶│   Goods      │───▶│   Invoice    │
│   Shipment   │    │   Receipt    │    │   Payment    │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Model Relationships

### Core Entity Relationships

```
                    ┌─────────────┐
                    │    User     │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
    │Employee │      │ Customer  │     │  Vendor   │
    └────┬────┘      └─────┬─────┘     └─────┬─────┘
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
    │ TimeLog │      │ServiceSite│     │    PO     │
    │  Leave  │      │ServiceReq │     │ Invoice   │
    └─────────┘      └───────────┘     └───────────┘
```

### Work Order Relationships

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│ DrillBit  │────▶│ WorkOrder │◀────│  Design   │
└───────────┘     └─────┬─────┘     └───────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
┌───▼───┐         ┌─────▼─────┐       ┌─────▼─────┐
│WOTask │         │WOMaterial │       │  WOTime   │
└───────┘         └───────────┘       └───────────┘
```

---

## Auto-ID Generation

The system uses consistent auto-generated IDs:

| Model | Pattern | Example |
|-------|---------|---------|
| Employee | EMP-#### | EMP-0001 |
| Work Order | WO-YYYY-###### | WO-2024-000001 |
| Vendor | VND-#### | VND-0001 |
| Purchase Order | PO-YYYY-#### | PO-2024-0001 |
| Customer | CUST-#### | CUST-0001 |
| Service Site | SITE-#### | SITE-0001 |
| Drill Bit | DB-###### | DB-000001 |
| NCR | NCR-YYYY-#### | NCR-2024-0001 |

---

## Security Architecture

### Authentication Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  Login   │───▶│   Session    │───▶│   Request    │
│  Form    │    │   Creation   │    │   Handling   │
└──────────┘    └──────────────┘    └──────────────┘
```

### Permission Model

```
┌───────────┐    ┌───────────┐    ┌───────────┐
│   User    │───▶│   Role    │───▶│Permission │
└───────────┘    └───────────┘    └───────────┘
      │
      ▼
┌───────────┐
│Department │
└───────────┘
```

### Role-Based Access

| Role | Access Level |
|------|--------------|
| Admin | Full system access |
| Manager | Department + reports |
| Supervisor | Team management |
| Technician | Work orders + tasks |
| Viewer | Read-only access |

---

## Database Design Principles

### Standard Fields

All models include:
- `id` - UUID primary key
- `created_at` - Timestamp
- `updated_at` - Timestamp
- `created_by` - User FK (where applicable)
- `is_active` - Soft delete flag

### Naming Conventions

- Tables: `app_modelname` (e.g., `sales_customer`)
- Foreign Keys: `model_id` (e.g., `customer_id`)
- Status Fields: `status` with TextChoices
- Boolean Fields: `is_*` prefix (e.g., `is_active`)

---

## Integration Points

### External Systems

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| Email (SMTP) | Outbound | Notifications |
| File Storage | Local/S3 | Document storage |
| Redis | In-memory | Caching, queues |

### Future Integrations (P1)

- REST API for mobile app
- ERP system sync
- ARAMCO DRSS integration

---

## Scalability Considerations

### Horizontal Scaling

```
                    ┌─────────────┐
                    │Load Balancer│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
     │  Django   │   │  Django   │   │  Django   │
     │ Instance 1│   │ Instance 2│   │ Instance 3│
     └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
     │PostgreSQL │   │   Redis   │   │   S3/     │
     │  Primary  │   │  Cluster  │   │  Storage  │
     └───────────┘   └───────────┘   └───────────┘
```

### Performance Optimizations

1. **Database**: Indexes on frequently queried fields
2. **Caching**: Redis for session and query caching
3. **Queries**: select_related and prefetch_related
4. **Static**: CDN for static file delivery

---

## Testing Architecture

### Test Categories

| Type | Coverage | Purpose |
|------|----------|---------|
| Unit Tests | 84-97% | Model logic |
| Integration | 21 tests | Cross-app flows |
| Performance | 9 tests | Query optimization |
| Edge Cases | 17 tests | Boundary conditions |

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Parallel execution
pytest -n auto
```

---

**Version:** 1.0
**Last Updated:** December 2024
