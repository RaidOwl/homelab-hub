# Contributing to Homelab Hub

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- (Optional) Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with SQLite (default)
flask --app app run --port 5001

# Or with PostgreSQL
export DATABASE_URL=postgresql://homelab:homelab@localhost:5432/homelab_hub
flask --app app run --port 5001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies API requests to `http://localhost:5001`.

### Database Migrations

```bash
cd backend
alembic upgrade head        # Apply all migrations
alembic revision -m "desc"  # Create new migration
```

SQLite and PostgreSQL are both supported. Alembic uses batch mode automatically for SQLite.

## Features

### PostgreSQL Support
Set `DATABASE_URL` to a PostgreSQL connection string. The app handles `postgres://` → `postgresql://` rewriting automatically. Docker Compose includes a `postgres:16-alpine` service.

### Authentik Forward Auth
Set `REQUIRE_AUTH=true` to enforce authentication. The app reads `X-Authentik-Username`, `X-Authentik-Name`, and `X-Authentik-Email` headers set by Authentik's forward auth outpost. See `docs/Caddyfile` for an example Caddy configuration.

### Webhook Export
Set `WEBHOOK_SECRET` and call:
```bash
curl -X POST -H "Authorization: Bearer <secret>" http://localhost:8000/api/webhooks/export-trigger
```
Exports are saved to `/data/exports/` and can be downloaded via `GET /api/webhooks/exports/<filename>`.

### Proxmox Entities
**Clusters** and **Nodes** are first-class entity types. VMs can belong to either a Hardware or a Node. VMs have a `vm_type` field (`vm` or `lxc`). Apps and Storage can also be parented to Nodes.

## Docker

```bash
docker compose up -d
```

The compose file starts PostgreSQL and the app on an internal network. To expose the app directly (without Caddy), add a ports mapping:

```yaml
# docker-compose.override.yml
services:
  homelab-hub:
    ports:
      - "8000:8000"
```
