# Troubleshooting Guide
## ARDT Floor Management System

---

## Common Issues

### Authentication Issues

#### Cannot Login

**Symptoms:**
- Login form rejects valid credentials
- "Invalid username or password" message

**Solutions:**
1. Verify username is correct (case-sensitive)
2. Reset password via admin
3. Check if user account is active:
   ```sql
   SELECT username, is_active FROM users WHERE username = 'user';
   ```
4. Clear browser cache and cookies

#### Session Expired

**Symptoms:**
- Logged out unexpectedly
- "Session expired" message

**Solutions:**
1. Login again
2. Check session cookie settings
3. Verify Redis is running (if using Redis sessions)

---

### Permission Issues

#### "Permission Denied" Error

**Symptoms:**
- 403 Forbidden error
- "You don't have permission" message

**Solutions:**
1. Verify user has required role:
   ```python
   user = User.objects.get(username='user')
   print(user.role_codes)
   ```

2. Check role permissions:
   ```python
   from apps.accounts.models import Role
   role = Role.objects.get(code='PLANNER')
   print(list(role.permissions.values_list('code', flat=True)))
   ```

3. Assign missing role:
   ```python
   from apps.accounts.models import UserRole
   UserRole.objects.create(user=user, role=role)
   ```

#### Admin Access Denied

**Symptoms:**
- Cannot access /admin/
- Redirected to admin login

**Solutions:**
1. Verify user is_staff = True:
   ```python
   user.is_staff = True
   user.save()
   ```

2. For superuser access:
   ```python
   user.is_superuser = True
   user.save()
   ```

---

### Database Issues

#### Connection Refused

**Symptoms:**
```
psycopg.OperationalError: connection failed: Connection refused
```

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. Verify connection settings in .env:
   ```bash
   DATABASE_URL=postgres://user:pass@localhost:5432/ardt_fms
   ```

3. Test connection:
   ```bash
   psql -U ardt_user -h localhost -d ardt_fms
   ```

#### Migration Errors

**Symptoms:**
- "relation does not exist" errors
- Migration conflicts

**Solutions:**
1. Check migration status:
   ```bash
   python manage.py showmigrations
   ```

2. Apply pending migrations:
   ```bash
   python manage.py migrate
   ```

3. For conflicts, fake initial migration:
   ```bash
   python manage.py migrate app_name --fake-initial
   ```

4. **Nuclear option** (development only):
   ```bash
   # Reset database
   dropdb ardt_fms
   createdb ardt_fms
   python manage.py migrate
   ```

---

### Performance Issues

#### Slow Page Load

**Symptoms:**
- Pages take >3 seconds to load
- Browser timeout errors

**Solutions:**
1. Check for N+1 queries:
   - Enable Django Debug Toolbar
   - Look for excessive SQL queries

2. Add select_related/prefetch_related:
   ```python
   WorkOrder.objects.select_related('customer', 'assigned_to')
   ```

3. Check database indexes:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM work_orders WHERE customer_id = 1;
   ```

4. Monitor with Django Debug Toolbar

#### High Memory Usage

**Symptoms:**
- Server running out of memory
- Worker processes killed

**Solutions:**
1. Reduce Gunicorn workers:
   ```bash
   gunicorn --workers 2 ...
   ```

2. Add query limits:
   ```python
   Model.objects.all()[:100]  # Limit results
   ```

3. Use pagination for large lists

---

### Static Files Issues

#### CSS/JS Not Loading

**Symptoms:**
- Unstyled pages
- Missing images
- 404 errors for static files

**Solutions:**
1. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. Check STATIC_ROOT in settings:
   ```python
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   ```

3. Verify Nginx static configuration:
   ```nginx
   location /static/ {
       alias /app/staticfiles/;
   }
   ```

#### File Upload Errors

**Symptoms:**
- "Upload failed" errors
- File too large errors

**Solutions:**
1. Check file size limits:
   ```python
   # settings.py
   DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
   ```

2. Check Nginx client max body size:
   ```nginx
   client_max_body_size 50M;
   ```

3. Verify MEDIA_ROOT is writable:
   ```bash
   sudo chown -R www-data:www-data /app/media/
   ```

---

### Email Issues

#### Emails Not Sending

**Symptoms:**
- No notification emails
- Email errors in logs

**Solutions:**
1. Verify email settings:
   ```python
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   ```

2. Test email configuration:
   ```bash
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
   ```

3. Check spam folder

4. For Gmail, use App Password (not regular password)

---

### Docker Issues

#### Container Won't Start

**Symptoms:**
- Container exits immediately
- "Exited (1)" status

**Solutions:**
1. Check container logs:
   ```bash
   docker-compose logs web
   ```

2. Verify environment variables:
   ```bash
   docker-compose config
   ```

3. Check database is ready:
   ```bash
   docker-compose exec db pg_isready
   ```

#### Database Connection in Docker

**Symptoms:**
- "Connection refused" in Docker
- Cannot connect to db service

**Solutions:**
1. Use service name, not localhost:
   ```
   DATABASE_URL=postgres://user:pass@db:5432/ardt_fms
   ```

2. Wait for database:
   ```bash
   docker-compose exec web python manage.py wait_for_db
   ```

---

### Redis/Celery Issues

#### Celery Tasks Not Running

**Symptoms:**
- Background tasks not executing
- Tasks stuck in queue

**Solutions:**
1. Check Celery is running:
   ```bash
   celery -A ardt_fms status
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   ```

3. View queued tasks:
   ```bash
   celery -A ardt_fms inspect active
   ```

4. Restart Celery worker:
   ```bash
   supervisorctl restart celery
   ```

---

## Diagnostic Commands

### System Validation

```bash
python scripts/system_validation.py
```

### Production Checks

```bash
python manage.py check --deploy
```

### Health Check

```bash
curl http://localhost:8000/health/
```

### Database Check

```bash
python manage.py dbshell
\dt  # List tables
SELECT COUNT(*) FROM users;
```

### Log Inspection

```bash
# Application logs
tail -f /var/log/ardt-fms/django.log

# Nginx logs
tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f web
```

---

## Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `IntegrityError: duplicate key` | Unique constraint violated | Check for existing record |
| `OperationalError: disk full` | No disk space | Free up disk space |
| `ValidationError: This field is required` | Missing required field | Provide required data |
| `DoesNotExist` | Record not found | Verify ID exists |
| `MultipleObjectsReturned` | Query returned multiple results | Add more filters |

---

## Getting Help

1. **Check Logs**: Always check application and server logs first
2. **Search Documentation**: Review docs/guides/
3. **Run Diagnostics**: Use validation scripts
4. **Contact Support**: support@ardt.com

---

**Version:** 5.4
**Last Updated:** December 2024
