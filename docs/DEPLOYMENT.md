# Deployment Guide
## ARDT Floor Management System - Production Deployment

---

## Overview

This guide covers deploying the ARDT FMS to a production environment using:
- Ubuntu 22.04+ server
- Nginx as reverse proxy
- Gunicorn as WSGI server
- PostgreSQL 16 database
- Redis for caching/Celery
- Supervisor for process management

---

## Server Preparation

### 1. System Updates

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx supervisor redis-server
```

### 2. Create Application User

```bash
sudo adduser --system --group ardt
sudo mkdir -p /var/www/ardt-fms
sudo chown ardt:ardt /var/www/ardt-fms
```

---

## Application Setup

### 1. Deploy Code

```bash
cd /var/www/ardt-fms
sudo -u ardt git clone <repository-url> .
```

### 2. Virtual Environment

```bash
sudo -u ardt python3 -m venv venv
sudo -u ardt ./venv/bin/pip install --upgrade pip
sudo -u ardt ./venv/bin/pip install -r requirements.txt
sudo -u ardt ./venv/bin/pip install gunicorn
```

### 3. Environment Configuration

```bash
sudo -u ardt nano .env
```

**Production Environment Variables:**

```bash
# Security
DEBUG=False
SECRET_KEY=<generate-64-char-random-string>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgres://ardt_user:secure_password@localhost:5432/ardt_fms

# Redis
REDIS_URL=redis://localhost:6379/0

# Static files
STATIC_ROOT=/var/www/ardt-fms/staticfiles

# Security headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 4. Database & Static Files

```bash
sudo -u ardt ./venv/bin/python manage.py migrate
sudo -u ardt ./venv/bin/python manage.py collectstatic --noinput
sudo -u ardt ./venv/bin/python manage.py createsuperuser
```

---

## Gunicorn Configuration

### Create Service File

```bash
sudo nano /etc/supervisor/conf.d/ardt-fms.conf
```

```ini
[program:ardt-fms]
command=/var/www/ardt-fms/venv/bin/gunicorn ardt_fms.wsgi:application --workers 3 --bind unix:/var/www/ardt-fms/gunicorn.sock
directory=/var/www/ardt-fms
user=ardt
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ardt-fms/gunicorn.log

[program:ardt-celery]
command=/var/www/ardt-fms/venv/bin/celery -A ardt_fms worker -l info
directory=/var/www/ardt-fms
user=ardt
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ardt-fms/celery.log

[program:ardt-celery-beat]
command=/var/www/ardt-fms/venv/bin/celery -A ardt_fms beat -l info
directory=/var/www/ardt-fms
user=ardt
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ardt-fms/celery-beat.log
```

### Create Log Directory

```bash
sudo mkdir -p /var/log/ardt-fms
sudo chown ardt:ardt /var/log/ardt-fms
```

### Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

---

## Nginx Configuration

### Create Site Configuration

```bash
sudo nano /etc/nginx/sites-available/ardt-fms
```

```nginx
upstream ardt_fms {
    server unix:/var/www/ardt-fms/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/ardt-fms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/ardt-fms/media/;
        expires 7d;
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://ardt_fms;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/ardt-fms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## Database Backup

### Automated Backup Script

```bash
sudo nano /usr/local/bin/backup-ardt-fms.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ardt-fms"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U ardt_user ardt_fms | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/ardt-fms/media/

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-ardt-fms.sh
```

### Cron Job

```bash
sudo crontab -e
# Add:
0 2 * * * /usr/local/bin/backup-ardt-fms.sh
```

---

## Monitoring

### Health Check Endpoint

Add to your Django urls.py:

```python
def health_check(request):
    return JsonResponse({'status': 'healthy'})

urlpatterns += [
    path('health/', health_check),
]
```

### Supervisor Status

```bash
sudo supervisorctl status
```

### Log Monitoring

```bash
# Application logs
tail -f /var/log/ardt-fms/gunicorn.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Backup current database
- [ ] Test migrations on staging
- [ ] Verify all tests pass
- [ ] Review security settings

### Deployment

- [ ] Pull latest code
- [ ] Install new dependencies
- [ ] Run migrations
- [ ] Collect static files
- [ ] Restart services

### Post-Deployment

- [ ] Verify application is running
- [ ] Check error logs
- [ ] Test critical workflows
- [ ] Monitor performance

---

## Update Procedure

```bash
cd /var/www/ardt-fms
sudo -u ardt git pull origin main
sudo -u ardt ./venv/bin/pip install -r requirements.txt
sudo -u ardt ./venv/bin/python manage.py migrate
sudo -u ardt ./venv/bin/python manage.py collectstatic --noinput
sudo supervisorctl restart all
```

---

## Security Recommendations

1. **Firewall**: Only allow ports 22, 80, 443
2. **SSH**: Use key-based authentication
3. **Database**: Use strong passwords, limit access
4. **Backups**: Test restore procedures regularly
5. **Updates**: Keep system packages updated
6. **Monitoring**: Set up uptime monitoring
7. **Logging**: Centralize and monitor logs

---

**Version:** 1.0
**Last Updated:** December 2024
