# ARDT Floor Management System
# Server & Hosting Requirements Document
**Version:** 1.0
**Date:** February 24, 2026
**Prepared for:** IT Manager / Infrastructure Team

---

## 1. System Overview

The **ARDT Floor Management System** is a comprehensive enterprise web application for drill bit manufacturing and repair operations. It is NOT a simple website — it is a full ERP-style platform with 23 production modules.

### What the System Does

| Module | Function |
|--------|----------|
| **Inventory Management** | Track 323+ PDC cutter items, 850+ variants, stock levels, GRNs |
| **Work Orders / Job Cards** | Manufacturing & repair workflows, 30+ active work orders |
| **Drill Bit Lifecycle** | From receipt to deployment to repair, 45+ registered bits |
| **Designs & BOMs** | L3/L4 designs, L5 Bills of Materials with cutter assignments |
| **ERP Browser Automation** | Automated D365 ERP data entry via Playwright/Chromium |
| **QR Code Scanning** | Router sheet step tracking, item identification, station scanning |
| **PDF Processing** | Halliburton PDF extraction + BOM PDF/PPT generation |
| **Excel Import/Export** | Job card parsing, inventory export, report generation |
| **Supply Chain** | Purchase orders, vendors, email notifications |
| **Quality & Compliance** | Inspections, evaluations (9 types), decision tracking |
| **Document Management** | Versioning, access control, approval workflows |
| **Notifications** | Multi-channel: in-app, email, SMS-ready, push-ready |
| **Dashboards & Reports** | Custom dashboards, saved reports, export logs |
| **Audit Trail** | Complete activity logging with change diffs |
| **Planning** | Agile sprints, Kanban boards, wiki with versioning |
| **Maintenance** | Equipment maintenance and calibration tracking |

### How Users Access It

- Users open a **web browser** on any PC/laptop/tablet/phone on the company network
- They navigate to the server's IP address (e.g., `http://192.168.1.100:8001`)
- The system is fully responsive — works on desktop, tablet, and mobile screens
- QR scanning works via mobile phone cameras through the web interface
- ERP automation browser runs ON the server (not on user PCs)

---

## 2. Server Hardware Requirements

### Recommended Specifications

| Resource | Minimum | Recommended | Ideal (Future-Proof) |
|----------|---------|-------------|---------------------|
| **CPU** | 4 cores | **8 cores** | 12-16 cores |
| **RAM** | 8 GB | **16 GB** | 32 GB |
| **Storage** | 100 GB SSD | **256 GB SSD** | 512 GB NVMe SSD |
| **Network** | 100 Mbps | **1 Gbps** | 1 Gbps |
| **UPS** | Required | Required | Required |

### Why These Specs?

#### CPU (8 cores recommended)
| Consumer | Cores Used | Purpose |
|----------|-----------|---------|
| Web Server (Django/Gunicorn) | 2-4 cores | Serving 30 concurrent users |
| PostgreSQL Database | 1-2 cores | Query processing, indexing |
| Chromium Browser (Playwright) | 1-2 cores | ERP automation sessions |
| Redis Cache + Task Queue | 0.5 core | Caching, background jobs |
| OS + Services | 0.5-1 core | Windows/Linux overhead |

#### RAM (16 GB recommended)
| Component | Usage | Notes |
|-----------|-------|-------|
| Operating System | 2-3 GB | Windows Server base |
| Django Web App (4 workers) | 2-3 GB | Serving 30 users simultaneously |
| PostgreSQL Database | 2-3 GB | Query cache, connection pool |
| Chromium Browser (Playwright) | 2-3 GB | One active ERP automation session |
| Redis Cache | 0.5 GB | Sessions, task queue, caching |
| PDF/Excel Processing | 1-2 GB | Peak during batch operations |
| Headroom | 2-3 GB | Prevents swapping/slowdowns |
| **Total** | **~14 GB** | 16 GB is comfortable |

> **If running 2+ simultaneous ERP sessions or planning for growth: get 32 GB.**

#### Storage (256 GB SSD mandatory)
| Item | Current | 1-Year Estimate | 3-Year Estimate |
|------|---------|-----------------|-----------------|
| OS + Software | 40 GB | 45 GB | 50 GB |
| Application Code | 50 MB | 100 MB | 200 MB |
| Database | 15 MB | 1 GB | 3-5 GB |
| Backups (30-day retention) | 0 | 5 GB | 15 GB |
| User Uploads (PDFs, Excel, Photos) | 0 | 2-5 GB | 10-20 GB |
| Logs | 0 | 5 GB | 15 GB |
| ERP Screenshots/Videos | 0 | 5 GB | 10 GB |
| **Total** | ~40 GB | ~65 GB | ~115 GB |

> **SSD is MANDATORY** — the system does heavy database queries and PDF processing. An HDD will make the system noticeably slow.

---

## 3. Operating System

### Recommended: Windows Server 2022 Standard

| Option | Recommendation | Why |
|--------|---------------|-----|
| **Windows Server 2022** | **Best Choice** | Matches development environment exactly, Playwright runs natively with visible browser, easy RDP for maintenance, Active Directory integration possible |
| Windows 11 Pro | Acceptable | Cheaper, works for <30 users, but not designed for server workloads |
| Ubuntu 22.04 LTS | Advanced Option | Free OS, lighter, Docker-native, but Playwright needs extra display setup and is different from dev environment |

### Windows Server Features Needed
- **Desktop Experience** — required for Playwright visible browser
- **Remote Desktop (RDP)** — for server maintenance
- **.NET Framework** — for some Python dependencies
- **Windows Defender** — basic security
- **Windows Server Backup** — for automated backups

---

## 4. Software Stack (All Installed on Server)

### Core Software

| Software | Version | Purpose | Free? |
|----------|---------|---------|-------|
| **Python** | 3.11+ | Application runtime | Yes |
| **PostgreSQL** | 16.x | Production database | Yes |
| **Redis** | 7.x (Memurai on Windows) | Cache + task queue | Memurai: $$ / Linux: Free |
| **Git** | Latest | Code deployment & updates | Yes |
| **Chromium** | Auto-installed by Playwright | ERP browser automation | Yes |

### Alternative to Redis on Windows
Redis does not officially support Windows. Options:
- **Memurai** — Windows Redis alternative ($$ for production license)
- **WSL2 + Redis** — Run Redis inside Windows Subsystem for Linux (free)
- **Docker Desktop + Redis** — Run Redis in a container (free)

### Optional Software

| Software | Purpose | When Needed |
|----------|---------|-------------|
| **Nginx** | Reverse proxy, SSL, load balancing | If using HTTPS or custom domain |
| **Certbot** | Free SSL certificates (Let's Encrypt) | If HTTPS needed |
| **Docker Desktop** | Container management | If deploying via Docker |
| **7-Zip** | Backup compression | For automated backups |

---

## 5. Network Requirements

### LAN Configuration

| Requirement | Detail |
|-------------|--------|
| **Speed** | 1 Gbps recommended (users upload Excel/PDF files) |
| **IP Address** | **Static IP** on company LAN (e.g., `192.168.1.100`) |
| **DNS (optional)** | Map `ardt-fms` or `fms.ardt.local` to server IP for easy access |
| **Ports to Open (inbound, LAN only)** | |
| Port 8001 | Django web application (or 80/443 with Nginx) |
| Port 5432 | PostgreSQL (only if DB accessed from other servers) |
| Port 6379 | Redis (only if accessed from other servers) |

### Internet Access (REQUIRED)

| Purpose | Destination | Port |
|---------|-------------|------|
| **ERP Automation** | `ardt.operations.dynamics.com` | 443 (HTTPS) |
| **ADFS Login** | `*.microsoftonline.com` | 443 (HTTPS) |
| **Playwright Updates** | `playwright.azureedge.net` | 443 (HTTPS) |
| **Python Packages** | `pypi.org`, `files.pythonhosted.org` | 443 (HTTPS) |
| **GitHub (code updates)** | `github.com` | 443 (HTTPS) |

### Firewall Rules
- **ALLOW** inbound on port 8001 from company LAN only
- **BLOCK** inbound on port 8001 from internet/public
- **ALLOW** outbound HTTPS (443) to the destinations above
- **BLOCK** all other inbound from internet

---

## 6. Current Features & Their Server Impact

### Features Already Built

| Feature | Server Impact | Special Requirements |
|---------|--------------|---------------------|
| **Web Dashboard** (30 users) | Moderate CPU, 2-3 GB RAM | 4+ Gunicorn workers |
| **QR Code Generation** | Low — generates small PNGs | `qrcode` + `python-barcode` libraries |
| **QR Code Scanning** | None on server — camera runs on user's phone | Mobile browser access |
| **PDF Extraction** (PyMuPDF) | Moderate CPU burst, ~500 MB RAM peak | Per-file processing |
| **PDF Generation** (ReportLab) | Low-Moderate | Template rendering |
| **Excel Import/Export** (openpyxl, pandas) | Moderate RAM for large datasets | Pandas can use 1+ GB for big exports |
| **ERP Browser Automation** (Playwright) | **HIGH** — 2-3 GB RAM, 1-2 CPU cores | Chromium browser on server |
| **Email Notifications** | Minimal | SMTP server access needed |
| **In-App Notifications** | Low — database queries | Already built |
| **Audit Trail / Logging** | Low — write-only | Disk space for logs |
| **Document Management** | Low CPU, disk I/O for uploads | Storage for uploaded files |
| **Comment System** | Low | Database + optional file attachments |
| **Router Sheet QR Scan** | Low | Real-time via HTMX polling |

---

## 7. Future Features & Their Server Impact

These features are either partially built or commonly needed for manufacturing systems. The server should be sized to accommodate them.

### Mobile & Communication

| Feature | Description | Server Impact | Additional Software |
|---------|-------------|--------------|-------------------|
| **Mobile-Optimized Views** | Already responsive via Tailwind CSS | None — already works | None |
| **PWA (Progressive Web App)** | Install on phone home screen, offline access | Minimal — add service worker | None (code change only) |
| **Push Notifications** | Browser push to mobile/desktop | Low — WebPush protocol | `django-webpush` library |
| **WhatsApp Integration** | Send notifications via WhatsApp Business API | Low — API calls | WhatsApp Business API account ($) |
| **Microsoft Teams Integration** | Send alerts to Teams channels | Low — webhook calls | Teams Incoming Webhook (free) |
| **Outlook/Email Integration** | Send emails, calendar invites | Low — SMTP/Graph API | SMTP server or Microsoft 365 account |
| **SMS Notifications** | Send SMS alerts | Low — API calls | Twilio or similar SMS provider ($) |

### Photo & Video

| Feature | Description | Server Impact | Storage Impact |
|---------|-------------|--------------|---------------|
| **Photo Uploads** | Attach photos to work orders, evaluations, drill bits | Low CPU | 2-5 MB per photo, ~10-50 GB/year |
| **Video Uploads** | Record repair processes, inspections | Moderate disk I/O | 50-500 MB per video, needs large disk |
| **Photo Gallery** | Browse photos per work order | Low CPU, moderate RAM | Thumbnail generation (Pillow) |
| **Image Compression** | Auto-resize uploaded photos | Low CPU burst | Reduces storage by 60-80% |

> **If video uploads are planned:** Increase storage to **512 GB or 1 TB SSD**, or use a **NAS** for media files.

### Real-Time & Chat

| Feature | Description | Server Impact | Additional Software |
|---------|-------------|--------------|-------------------|
| **Real-Time Chat** | Internal messaging between staff | Moderate — WebSocket connections | `django-channels` + Redis |
| **Live Dashboard Updates** | Auto-refresh dashboards without page reload | Low-Moderate — WebSocket | `django-channels` + Redis |
| **Live Notification Bell** | Real-time notification counter | Low — WebSocket | `django-channels` + Redis |

> **For WebSocket features:** Redis is already in the stack. Only code changes needed.

### Advanced Features

| Feature | Description | Server Impact | Notes |
|---------|-------------|--------------|-------|
| **Barcode/QR Printing** | Print labels from the system | Minimal — sends to printer | Label printer (Zebra, Brother) on network |
| **Camera Scanning** | Use phone camera as barcode scanner | None on server | Already supported via web |
| **GPS/Location Tracking** | Track where drill bits are deployed | Low — store coordinates | Mobile browser geolocation API |
| **Digital Signatures** | Sign off on evaluations electronically | Low | Already partially built (signature field exists) |
| **Multi-Language** | Arabic/English interface | Low | Django i18n (code change only) |
| **Active Directory / LDAP** | Login with company Windows credentials | Low | `django-auth-ldap` library |
| **SSO (Single Sign-On)** | Login with Microsoft 365 account | Low | `django-allauth` + Azure AD |
| **REST API** | Mobile app backend, external integrations | Moderate | `djangorestframework` library |
| **Scheduled Reports** | Auto-email daily/weekly reports | Low | Celery Beat (already configured) |
| **Data Analytics** | Charts, trends, KPIs | Moderate | `plotly` or `chart.js` (code change only) |

---

## 8. Integration Compatibility

### Integrations That Work NOW (No Server Changes Needed)

| Integration | How | Status |
|-------------|-----|--------|
| **D365 ERP** | Playwright browser automation | Working |
| **Web Browsers** | Chrome, Firefox, Edge, Safari | Working |
| **Mobile Browsers** | iOS Safari, Android Chrome | Working |
| **QR Scanners** | Phone camera via web browser | Working |
| **Excel** | Import/Export via openpyxl + pandas | Working |
| **PDF** | Extract (PyMuPDF) + Generate (ReportLab) | Working |
| **PowerPoint** | Generate from BOM data (python-pptx) | Working |

### Integrations That Need Configuration (Server-Side)

| Integration | Requirement | Effort |
|-------------|-------------|--------|
| **Email (SMTP)** | SMTP server credentials (or Microsoft 365) | 1 hour setup |
| **WhatsApp Business** | API account + webhook endpoint | 1-2 days development |
| **Microsoft Teams** | Incoming Webhook URL per channel | 2-4 hours development |
| **Outlook Calendar** | Microsoft Graph API credentials | 1-2 days development |
| **Active Directory** | LDAP server connection details | 4-8 hours development |
| **SMS (Twilio/etc.)** | API account + phone number | 4-8 hours development |

### Integrations That Need Additional Software

| Integration | Additional Server Software | Notes |
|-------------|---------------------------|-------|
| **Real-Time Chat** | Django Channels (Python library) | Uses existing Redis |
| **REST API (Mobile App)** | Django REST Framework (Python library) | For building a mobile app |
| **Label Printing** | Network printer driver | Zebra ZPL or similar |
| **Document Scanning** | TWAIN driver (Windows) | For flatbed scanner integration |

---

## 9. Backup & Disaster Recovery

### Backup Strategy

| What | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| **Database** | Daily at 2 AM | 30 days rolling | `pg_dump` → compressed file |
| **User Uploads** | Daily at 3 AM | 30 days rolling | File copy to backup location |
| **Application Code** | On each update | Full Git history | Git repository on GitHub |
| **Full System Snapshot** | Weekly (Sunday) | 4 weeks | Windows Server Backup |
| **Off-Site Copy** | Weekly | 12 months | Copy to NAS, external drive, or cloud |

### Estimated Backup Storage
- Daily DB backup: ~10-50 MB (compressed)
- Daily media backup: ~100 MB-1 GB (incremental)
- Weekly full snapshot: ~20-50 GB
- **Total backup storage needed:** 100-200 GB (separate from main SSD)

### Disaster Recovery Options

| Scenario | Recovery Time | Method |
|----------|--------------|--------|
| Database corruption | 15-30 minutes | Restore from daily backup |
| Server hardware failure | 2-4 hours | Restore full snapshot on new server |
| File accidentally deleted | 5-10 minutes | Restore from daily file backup |
| Complete site disaster | 4-8 hours | Deploy from GitHub + restore DB backup |

---

## 10. Security Requirements

### Network Security
- Server should be on company LAN only (NOT exposed to public internet)
- Firewall rules: only port 8001 (or 80/443) open inbound from LAN
- If remote access needed: use VPN, not direct internet exposure
- RDP access: restrict to IT admin IPs only

### Application Security (Built-In)
- User authentication with role-based permissions
- CSRF protection on all forms
- Session timeout: 24 hours
- Audit trail on all actions (who did what, when)
- SSL/HTTPS ready (configure with Nginx + certificate)
- ERP credentials stored in memory only (not on disk)

### Data Security
- Database backups should be encrypted
- User uploads stored in server filesystem (access controlled by app)
- Logs contain IP addresses and user actions (privacy consideration)

---

## 11. Monitoring & Maintenance

### Recommended Monitoring

| What to Monitor | Tool | Alert When |
|----------------|------|------------|
| **Disk Space** | Windows Task Scheduler script | < 20% free |
| **RAM Usage** | Windows Performance Monitor | > 85% sustained |
| **CPU Usage** | Windows Performance Monitor | > 90% sustained |
| **Database Size** | Scheduled SQL query | > 5 GB |
| **Application Health** | Built-in `/health/` endpoint | HTTP != 200 |
| **Backup Success** | Windows Event Log | Backup fails |
| **Service Status** | Windows Services | Django/PostgreSQL/Redis stopped |

### Regular Maintenance Tasks

| Task | Frequency | Duration |
|------|-----------|----------|
| Windows Updates | Monthly | 30 min + restart |
| Database VACUUM/ANALYZE | Weekly (auto) | Automatic |
| Log rotation / cleanup | Monthly | 10 minutes |
| Backup verification (test restore) | Monthly | 30 minutes |
| Application update (`git pull`) | As needed | 15 minutes |
| SSL certificate renewal | Annually | 15 minutes |
| Disk space review | Monthly | 5 minutes |

---

## 12. Performance Expectations

| Operation | Expected Time | Notes |
|-----------|--------------|-------|
| Login page load | < 0.5 seconds | |
| Dashboard load | < 1 second | With 30 concurrent users |
| Inventory list (300+ items) | < 1 second | Client-side filtering |
| PDF extraction (Halliburton) | 2-5 seconds | Depends on PDF complexity |
| Excel export (full inventory) | 3-8 seconds | 300+ rows with formatting |
| BOM PDF generation | 2-4 seconds | Multi-page with images |
| QR code generation | < 0.5 seconds | Base64 PNG |
| QR scan + save | < 1 second | HTMX partial update |
| ERP automation (full chain) | 10-20 minutes | 13 workflows, 160+ steps |
| Job card Excel upload | 2-5 seconds | Parse + save |
| Photo upload (5 MB) | 1-3 seconds | Depends on network speed |

---

## 13. Scalability Path

### Current → Near Future → Growth

| Aspect | Now | 1 Year | 3 Years |
|--------|-----|--------|---------|
| **Users** | 15-30 | 30-50 | 50-100 |
| **Server** | Single server | Single server (larger) | Consider load balancer |
| **Database** | PostgreSQL on same server | Same | Consider dedicated DB server |
| **Storage** | 256 GB SSD | Add NAS for media | NAS + cloud backup |
| **RAM** | 16 GB | 32 GB upgrade | 32-64 GB |
| **ERP Sessions** | 1 at a time | 2-3 concurrent | Dedicated automation server |

### When to Upgrade

| Symptom | Solution |
|---------|----------|
| Pages load slowly (> 3 seconds) | Add RAM, check DB indexes |
| ERP automation fails/times out | Dedicated more RAM to Chromium |
| Disk > 80% full | Add storage or NAS |
| > 50 concurrent users, slowness | Add CPU cores, increase Gunicorn workers |
| Need 3+ concurrent ERP sessions | Separate ERP automation server |

---

## 14. Cost Estimates

### Option A: Physical Server (Recommended for ARDT)

| Item | Specification | Est. Cost (USD) |
|------|--------------|----------------|
| **Server Hardware** | Dell PowerEdge T350 or HP ProLiant ML350 | |
| | 8-core Intel Xeon E-2400 series | |
| | 32 GB DDR5 ECC RAM | |
| | 2x 480 GB SSD (RAID 1 for redundancy) | |
| | Redundant power supply | |
| | **Hardware Total** | **$3,000 - $5,000** |
| **Windows Server 2022 Standard** | 16-core license | $800 - $1,200 |
| **UPS** | APC 1500VA (30 min backup) | $300 - $500 |
| **NAS for Backups** (optional) | Synology 2-bay + 2x 2TB HDD | $400 - $600 |
| **Total (One-Time)** | | **$4,500 - $7,300** |
| **Annual Costs** | Electricity, maintenance | ~$200 - $500/year |

### Option B: Cloud VM (Alternative)

| Provider | Specification | Monthly Cost |
|----------|--------------|-------------|
| **Azure VM** | D4s v5 (4 vCPU, 16 GB) + 256 GB SSD | ~$200 - $300/mo |
| **AWS EC2** | m6i.xlarge (4 vCPU, 16 GB) + 256 GB EBS | ~$200 - $300/mo |
| **Hetzner** | CCX33 (8 vCPU, 32 GB) + 240 GB NVMe | ~$60 - $80/mo |
| | **Annual Cloud Cost** | **$720 - $3,600/year** |

> **Cloud note:** Playwright with visible browser is harder in cloud (needs VNC/RDP). Physical server is simpler for ARDT's use case.

### Option C: Refurbished Server (Budget)

| Item | Specification | Est. Cost |
|------|--------------|-----------|
| **Refurbished Server** | Dell PowerEdge R640/R740 | $800 - $1,500 |
| | 8-16 cores, 32 GB RAM | |
| | 2x 240 GB SSD | |
| **Windows Server 2022** | License | $800 - $1,200 |
| **Total** | | **$1,600 - $2,700** |

---

## 15. Summary for IT Manager

### Quick Reference Card

```
SYSTEM:         ARDT Floor Management System
TYPE:           Enterprise Web Application (Django/Python)
USERS:          15-30+ concurrent users via web browser
ACCESS:         Any device with a web browser on company LAN

SERVER SPECS:
  CPU:          8 cores (Intel Xeon or AMD EPYC)
  RAM:          16 GB minimum, 32 GB recommended
  Storage:      256 GB SSD (RAID 1 recommended)
  Network:      1 Gbps LAN, internet access required
  OS:           Windows Server 2022 Standard with Desktop Experience
  UPS:          Required (1500VA minimum)

SOFTWARE (all free except OS):
  Python 3.11, PostgreSQL 16, Redis 7, Chromium (auto-installed)

SPECIAL NOTES:
  - Chromium browser runs ON the server for ERP automation
  - Desktop Experience required (not Server Core)
  - SSD mandatory (not HDD)
  - Internet needed for D365 ERP access
  - Static IP on LAN recommended
  - Daily automated backups needed

ESTIMATED BUDGET:
  New server + license:      $4,500 - $7,300 (one-time)
  Refurbished + license:     $1,600 - $2,700 (one-time)
  Cloud alternative:         $720 - $3,600/year
```

---

## 16. Deployment Checklist

### Server Setup Steps

- [ ] Install Windows Server 2022 with Desktop Experience
- [ ] Configure static IP address on company LAN
- [ ] Enable RDP for remote management
- [ ] Install Python 3.11+
- [ ] Install PostgreSQL 16
- [ ] Install Redis (Memurai or WSL2)
- [ ] Install Git
- [ ] Clone application from GitHub
- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Install Playwright Chromium (`playwright install chromium`)
- [ ] Configure environment variables (SECRET_KEY, DATABASE_URL, etc.)
- [ ] Run database migrations (`python manage.py migrate`)
- [ ] Seed initial data (`python manage.py seed_all`)
- [ ] Create admin user (`python manage.py createsuperuser`)
- [ ] Start application server
- [ ] Configure Windows Firewall (open port 8001 from LAN)
- [ ] Test access from a user workstation
- [ ] Set up daily backup schedule
- [ ] Configure monitoring alerts (disk, RAM, services)

### Environment Variables Required
```
SECRET_KEY=<generate-random-50-char-string>
DEBUG=False
DATABASE_URL=postgres://ardt_user:password@localhost:5432/ardt_fms
ALLOWED_HOSTS=192.168.1.100,ardt-fms.local,localhost
```

---

*Document prepared based on analysis of the complete ARDT Floor Management System codebase
(23 Django apps, 90+ models, 42 Python packages, full Docker deployment configuration).*
