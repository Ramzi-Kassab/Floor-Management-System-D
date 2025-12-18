# Administrator Guide
## ARDT Floor Management System

---

## Overview

This guide covers administrative tasks for system administrators, including user management, role configuration, and system settings.

---

## User Management

### Creating Users

1. Navigate to Admin > Users
2. Click "Add User"
3. Fill in required fields:
   - Username (unique)
   - Email
   - First/Last name
   - Password
4. Assign department and position
5. Assign roles
6. Save

### Editing Users

1. Navigate to Admin > Users
2. Click on the username
3. Update information as needed
4. Save changes

### Deactivating Users

1. Navigate to Admin > Users
2. Click on the username
3. Uncheck "Is Active"
4. Save

**Note:** Deactivating is preferred over deleting to maintain audit history.

### Password Reset

1. Navigate to Admin > Users
2. Click on the username
3. Click "Reset Password"
4. Set temporary password
5. Notify user to change on first login

---

## Role Management

### Available Roles

| Role | Level | Description |
|------|-------|-------------|
| ADMIN | 100 | Full system access |
| MANAGER | 80 | Department oversight, approvals |
| PLANNER | 60 | Work order creation, scheduling |
| ENGINEER | 60 | Technical documentation |
| TECHNICIAN | 40 | Shop floor execution |
| QC | 50 | Quality inspections |
| SALES | 50 | Customer management |
| LOGISTICS | 50 | DRSS, dispatch |
| WAREHOUSE | 40 | Inventory management |
| MAINTENANCE | 50 | Equipment maintenance |
| PROCUREMENT | 50 | Purchasing |
| VIEWER | 10 | Read-only access |

### Assigning Roles

1. Navigate to Admin > Users
2. Select user
3. Go to Roles section
4. Add or remove roles
5. Save

### Creating Custom Roles

1. Navigate to Admin > Roles
2. Click "Add Role"
3. Enter role code and name
4. Set level (hierarchy position)
5. Assign permissions
6. Save

---

## Permission Management

### Permission Structure

Permissions follow the format: `module.action`

Examples:
- `workorders.create`
- `workorders.approve`
- `sales.edit`
- `hr.approve_leave`

### Assigning Permissions to Roles

1. Navigate to Admin > Roles
2. Select role
3. Go to Permissions section
4. Check/uncheck permissions
5. Save

### Loading Default Permissions

```bash
python manage.py loaddata fixtures/permissions.json
python manage.py loaddata fixtures/role_permissions.json
```

---

## Department Configuration

### Creating Departments

1. Navigate to Admin > Organization > Departments
2. Click "Add Department"
3. Enter:
   - Department code
   - Name
   - Parent department (if applicable)
   - Manager
4. Save

### Department Hierarchy

Departments can be nested for organizational structure:
- Company
  - Operations
    - Manufacturing
    - Quality
  - Sales
  - Supply Chain

---

## System Settings

### General Settings

Access via Admin > System Settings:

- **Site Name**: Application title
- **Time Zone**: Default time zone
- **Date Format**: Display format
- **Pagination**: Items per page

### Email Configuration

Configure in `.env` file:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Security Settings

Production security checklist:

- [ ] DEBUG=False
- [ ] Unique SECRET_KEY
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS enabled
- [ ] Session cookies secure
- [ ] CSRF protection enabled

---

## Data Management

### Backup Procedures

**Database Backup:**
```bash
pg_dump -U ardt_user ardt_fms > backup.sql
```

**Restore:**
```bash
psql -U ardt_user ardt_fms < backup.sql
```

### Data Import/Export

**Export to CSV:**
```bash
python manage.py dumpdata app.Model --format=json > export.json
```

**Import:**
```bash
python manage.py loaddata export.json
```

---

## Audit & Logging

### Viewing Audit Logs

1. Navigate to Admin > Audit Logs
2. Filter by:
   - User
   - Action type
   - Date range
   - Module

### Log Retention

By default, logs are retained for 90 days. Configure in settings:

```python
AUDIT_LOG_RETENTION_DAYS = 90
```

---

## Troubleshooting

### Common Issues

**User cannot login:**
1. Check if user is active
2. Verify password
3. Check role assignments

**Permission denied errors:**
1. Verify user has required role
2. Check role permissions
3. Clear browser cache

**Slow performance:**
1. Check database connections
2. Review slow query log
3. Clear cache

### Maintenance Commands

```bash
# Clear expired sessions
python manage.py clearsessions

# Collect static files
python manage.py collectstatic

# Run database migrations
python manage.py migrate

# Check for issues
python manage.py check
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health/
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "version": "5.4.0"
}
```

### System Validation

```bash
python scripts/system_validation.py
```

---

**Version:** 5.4
**Last Updated:** December 2024
