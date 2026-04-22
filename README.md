# Network Monitor MVP

Monitorizare rețea și detecție dispozitive mobile prin Mikrotik RouterOS API.

## Stack

- **Backend:** FastAPI + PostgreSQL
- **Scanner:** Mikrotik RouterOS API
- **Frontend:** React (schelet)
- **Deployment:** Docker Compose

## Quick Start

```bash
docker-compose up -d
```

> Backend-ul rulează cu `network_mode: host` pentru a putea accesa routerele MikroTik din rețeaua locală.

Backend: http://localhost:8000
Frontend: http://localhost:3000

## API Endpoints

### Devices
- `GET /api/devices` — Lista dispozitive (`phones_only=true` pentru doar mobile)
- `GET /api/devices/{id}` — Detalii dispozitiv
- `POST /api/devices/re-evaluate-phones` — Re-evaluează în masă flag-ul `is_phone`
- `POST /api/devices/scan` — Scan Mikrotik

### Health
- `GET /health` — Status sistem

## Structură

```
.
├── backend/          # FastAPI
├── frontend/         # React
├── docker-compose.yml
└── README.md
```

## Setup Mikrotik

1. Activează API pe Mikrotik (port 8728)
2. Creează user API cu permisiuni
3. Setează în `.env`: `ROUTER_IPS`, `ROUTER_USERNAME`, `ROUTER_PASSWORD`, `SCAN_INTERVAL_SECONDS`
