# Server Specifications
# ARDT Floor Management System

**Date:** February 24, 2026
**Prepared for:** IT Department — Server Procurement

---

## 1. Server Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores / 8 threads (Intel Xeon E-2300 or equivalent) | 8 cores / 16 threads (Intel Xeon E-2400 or AMD EPYC 7002) |
| **RAM** | 16 GB DDR4 ECC | 32 GB DDR4 ECC |
| **Storage (OS + App)** | 256 GB SSD (SATA) | 512 GB NVMe SSD |
| **Storage (Data/Backups)** | 500 GB HDD | 1 TB HDD (separate drive) |
| **Network** | 1 Gbps Ethernet | 1 Gbps Ethernet (dual NIC recommended) |
| **RAID** | — | RAID 1 on OS drive (optional) |
| **Power** | Standard ATX | Redundant PSU (if rack-mounted) |

---

## 2. Operating System

| Option | Version |
|--------|---------|
| **Primary (Recommended)** | Windows Server 2022 Standard — Desktop Experience |
| **Alternative** | Ubuntu Server 22.04 LTS or 24.04 LTS |

> **Note:** Windows Server with Desktop Experience is recommended because the system includes browser automation (Chromium) that requires a GUI environment.

---

## 3. Software Stack (To Be Installed on Server)

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Application runtime |
| PostgreSQL | 16 | Production database |
| Redis | 7+ | Caching & background task queue |
| Nginx | Latest stable | Web server / reverse proxy |
| Chromium | Latest (via Playwright) | Browser automation module |
| Git | Latest | Version control & deployment |
| Node.js | 18+ LTS (optional) | Frontend build tools if needed |

---

## 4. Network & Connectivity

| Requirement | Details |
|-------------|---------|
| **LAN Access** | All users connect via company LAN (Wi-Fi or Ethernet) |
| **Static IP** | Server must have a fixed LAN IP address |
| **Internet Access** | Required for: ERP automation (D365 cloud), email notifications, package updates |
| **Firewall Ports** | Inbound: 80 (HTTP), 443 (HTTPS), 8001 (app — LAN only) |
| **DNS (Optional)** | Internal DNS name recommended (e.g., `fms.ardt.local`) |
| **SSL Certificate** | Self-signed for LAN, or internal CA certificate |

---

## 5. User Capacity

| Metric | Specification |
|--------|---------------|
| **Concurrent Users** | 15–30 |
| **Total User Accounts** | Up to 50 |
| **Access Method** | Web browser (Chrome, Edge, Firefox, Safari) |
| **Mobile Access** | Responsive web — works on phones & tablets via browser |

---

## 6. Storage Estimates

| Data Type | Estimated Size (Year 1) | Growth Rate |
|-----------|------------------------|-------------|
| Database | 2–5 GB | ~2 GB/year |
| File uploads (photos, PDFs, documents) | 5–20 GB | ~10 GB/year |
| Backups (daily, 30-day retention) | 10–30 GB | Proportional |
| Application code + dependencies | ~2 GB | Minimal |
| Logs | 1–3 GB | ~1 GB/year |
| **Total Year 1** | **~20–60 GB** | |
| **Projected 3 Years** | **~60–150 GB** | |

---

## 7. Backup Requirements

| Item | Specification |
|------|---------------|
| **Frequency** | Daily automated backup |
| **Retention** | Minimum 30 days |
| **What to Backup** | Database, uploaded files, application configuration |
| **Backup Location** | Separate drive or network share (not same disk as OS) |
| **Off-site (Recommended)** | Weekly copy to external storage or cloud (OneDrive, Google Drive, NAS) |

---

## 8. Security

| Requirement | Details |
|-------------|---------|
| **Windows Updates** | Automatic security updates enabled |
| **Antivirus** | Windows Defender or enterprise AV |
| **Firewall** | Block all inbound except ports 80, 443, 8001 (LAN only) |
| **User Authentication** | Application handles its own login (username + password) |
| **Remote Access** | RDP for admin only, restrict to IT team IPs |
| **Database Access** | Local connections only (no external DB access) |

---

## 9. Future-Ready Considerations

The system is designed to support the following features when enabled. No additional hardware is needed, but the recommended specs account for these:

- **Email notifications** (SMTP — via Outlook/Office 365 or local SMTP relay)
- **WhatsApp integration** (via API gateway — internet required)
- **Microsoft Teams integration** (via webhook or Graph API — internet required)
- **Push notifications** (browser-based — no extra infrastructure)
- **Photo & video uploads** (stored on server — accounted for in storage estimates)
- **QR code scanning** (phone camera → browser — no server-side hardware needed)
- **Mobile app / PWA** (served from same server — no additional resources)

---

## 10. Summary — Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│          SERVER SPECIFICATION SUMMARY             │
├──────────────────────────────────────────────────┤
│  CPU:        8 cores / 16 threads                │
│  RAM:        32 GB DDR4 ECC                      │
│  OS Disk:    512 GB NVMe SSD                     │
│  Data Disk:  1 TB HDD                            │
│  Network:    1 Gbps Ethernet                     │
│  OS:         Windows Server 2022 Standard        │
│              (Desktop Experience)                │
│  Users:      15–30 concurrent                    │
│  Internet:   Required                            │
│  Backup:     Daily, 30-day retention             │
├──────────────────────────────────────────────────┤
│  Estimated Budget:                               │
│  • New server:        $4,500 – $7,000 USD        │
│  • Refurbished:       $1,500 – $2,500 USD        │
│  • Cloud VM (monthly): $150 – $300 USD/month     │
│  • Windows Server license: ~$1,000 (Standard)    │
└──────────────────────────────────────────────────┘
```

---

## 11. Recommended Server Models (Reference)

| Option | Model Examples | Estimated Price |
|--------|---------------|-----------------|
| **Tower (Office)** | Dell PowerEdge T150, HPE ProLiant ML30 Gen11 | $2,000–$4,000 |
| **Rack (Data Center)** | Dell PowerEdge R350, HPE ProLiant DL20 Gen11 | $3,000–$6,000 |
| **Workstation (Budget)** | Dell Precision 3660, HP Z2 Tower G9 | $1,500–$3,000 |
| **Cloud VM** | Azure B4ms, AWS t3.xlarge, Hetzner AX41 | $150–$300/mo |

> Any server or workstation-class machine meeting the specs in Section 1 will work. Brand preference is flexible.
