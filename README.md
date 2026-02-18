# Home Lab Hub

A self-hosted web application for managing and visualizing home lab infrastructure. Track hardware, virtual machines, applications, storage, networks, and more — all in one place.

![Home Lab Hub Screenshot](docs/screenshot.png)

## Features

- **Inventory Management** — Full CRUD for hardware, VMs, apps/services, storage, networks, shares, and miscellaneous items
- **Shares Management** — Track network shares (NFS, SMB, iSCSI, FTP, SFTP, WebDAV) under storage devices with auto-population of connection details
- **Export/Import** — Backup and restore your entire inventory with one-click JSON export/import
- **Network Visualization** — Interactive graph map with depth-first layout showing relationships between infrastructure components (powered by Cytoscape.js)
- **Tree View** — Hierarchical view of your infrastructure with collapsible nodes
- **Documentation** — Hierarchical markdown-based docs with live preview and auto-save
- **Sortable Tables** — Click column headers to sort inventory data ascending or descending
- **Cross-Entity Search** — Filter and search across all inventory types from a single interface
- **Modal Dialogs** — Clean, accessible modal forms for creating and editing entities
- **Relationship Tracking** — Automatic and manual relationship mapping between entities

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Svelte 4, Vite 5, Cytoscape.js, ByteMD, Pico CSS |
| Backend | Python 3.14, Flask 3, SQLAlchemy 2, Alembic |
| Database | SQLite (default, configurable) |
| Deployment | Docker, Docker Compose, Gunicorn || Platforms | Linux (x86_64, ARM64), macOS, Windows |
## Requirements

- **Node.js 24+** (for frontend development)
- **Python 3.14+** (for backend development)
- **Docker** (optional, for containerized deployment)

**Supported Platforms:**
- Linux (x86_64, ARM64) — including Raspberry Pi 4+, Orange Pi, etc.
- macOS (Intel & Apple Silicon)
- Windows (native or WSL2)

## Quick Start (Docker)

Works on x86_64, ARM64, and other supported platforms. Docker will automatically pull the correct image for your system.

```bash
docker run -d \
  --name homelab-hub \
  -p 8000:8000 \
  -v ./data:/data \
  --restart unless-stopped \
  raidowl/homelab-hub:latest
```

Or with Docker Compose — create a `docker-compose.yml`:

```yaml
services:
  homelab-hub:
    image: raidowl/homelab-hub:latest
    container_name: homelab-hub
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    restart: unless-stopped
```

```bash
docker compose up -d
```

The application will be available at `http://localhost:8000`.

Data is persisted in the `./data/` directory.

## Non-Docker Deployment

Deploy Home Lab Hub directly on your system without Docker containers.

### Prerequisites

- **Python 3.14+**
- **Node.js 24+** 
- **pip** (Python package manager)
- **npm** (Node package manager)
- A web server (Nginx/Apache, optional for reverse proxy)

### Step 1: Clone/Download the Repository

```bash
git clone https://github.com/raidowl/homelab-hub.git
cd homelab-hub
```

### Step 2: Backend Setup

```bash
cd backend

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Frontend Setup & Build

```bash
cd ../frontend

# Install Node dependencies
npm install

# Build for production
npm run build
```

The built frontend will be in the `frontend/dist/` directory.

Next, copy the built files to the backend's static directory.

**On Linux/macOS:**
```bash
mkdir -p ../backend/static
cp -r dist/* ../backend/static/
```

**On Windows:**
```powershell
mkdir ..\backend\static
xcopy dist\* ..\backend\static /E /I /Y
```

### Step 4: Database Initialization

From the `backend/` directory (with virtual environment activated):

```bash
# Apply any pending migrations
alembic upgrade head
```

The application will automatically create the SQLite database at `data/homelab-hub.db` on first run.

### Step 5: Run the Application

#### Option A: Development (Single Process)

From the `backend/` directory:

```bash
python wsgi.py
```

Access the application at `http://localhost:5001` (the built frontend files are served automatically).

#### Option B: Production (Gunicorn + Reverse Proxy)

From the `backend/` directory, run Gunicorn:

```bash
gunicorn -w 4 -b 127.0.0.1:5001 wsgi:app
```

- `-w 4`: Number of worker processes (adjust based on CPU cores)
- `-b 127.0.0.1:5001`: Bind to localhost on port 5001

Then set up a reverse proxy (Nginx recommended):

**Nginx Configuration** (`/etc/nginx/sites-available/homelab-hub`):

```nginx
server {
    listen 8000;
    server_name localhost;  # Or your domain name
    client_max_body_size 10M;

    # Serve static frontend files
    location / {
        alias /path/to/homelab-hub/frontend/dist/;
        try_files $uri /index.html;
    }

    # Proxy API requests to Gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/homelab-hub /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### Step 6 (Optional): Auto-Start with Systemd

Create a systemd service file for auto-start on boot.

**Create `/etc/systemd/system/homelab-hub.service`:**

```ini
[Unit]
Description=Home Lab Hub
After=network.target

[Service]
Type=simple
User=homelab
WorkingDirectory=/path/to/homelab-hub/backend
Environment="FLASK_ENV=production"
Environment="DATABASE_URL=sqlite:////path/to/homelab-hub/data/homelab-hub.db"
ExecStart=/path/to/homelab-hub/backend/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 wsgi:app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `/path/to/homelab-hub` with your actual installation path.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable homelab-hub
sudo systemctl start homelab-hub
```

Check status:

```bash
sudo systemctl status homelab-hub
```

### Configuration

Set environment variables as needed:

```bash
export FLASK_ENV=production
export DATABASE_URL=sqlite:////data/homelab-hub/homelab-hub.db
```

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///data/homelab-hub.db` | SQLAlchemy database URI |
| `FLASK_ENV` | `production` | Flask environment (`production` or `development`) |

### Data Backup

Export your data regularly:

```bash
curl -X GET http://localhost:8000/api/inventory/export -o homelab-export-$(date +%Y%m%d).json
```

Keep backups safe to restore in case of data loss.

## Development Setup

### Backend

```bash
cd backend
python3 -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python wsgi.py
```

The API server runs on `http://localhost:5001`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:3000` (or next available port) with hot reload.

### Database Migrations

Migrations are managed with Alembic. From the `backend/` directory:

```bash
# Apply migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description of changes"
```

Note: The app also calls `db.create_all()` on startup as a fallback for fresh databases.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///data/homelab-hub.db` | SQLAlchemy database URI |
| `FLASK_ENV` | `production` | Flask environment |

## Export & Import

Backup and restore your entire inventory data including hardware, VMs, apps, storage, networks, misc items, and documents.

### Using the UI (Recommended)

Use the Export/Import buttons in the application header:

- **Export**: Click the "Export Data" button to download a `homelab-export.json` file with all your data
- **Import**: Click the "Import Data" button, select a JSON file, and upload it to replace all existing data

**Warning**: Importing will clear all existing data before restoring from the file. Always keep a backup export before performing an import.

### Using the API/CLI

You can also use the API endpoints directly:

**Export:**
```bash
curl -X GET http://localhost:5001/inventory/export -o export.json
```

**Import:**
```bash
curl -X POST http://localhost:5001/inventory/import \
     -H "Content-Type: application/json" \
     -d @export.json
```

**Using with Docker:**
```bash
# Export from running container
docker exec -it <container_name> curl -X GET http://localhost:5001/inventory/export -o export.json

# Import to a new container
docker cp export.json <container_name>:/app/export.json
docker exec -it <container_name> curl -X POST http://localhost:5001/inventory/import \
     -H "Content-Type: application/json" \
     -d @/app/export.json
```

## Project Structure

```
homelab-hub/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   └── routes/       # Flask API blueprints
│   ├── migrations/       # Alembic migrations
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   ├── src/
│   │   ├── components/   # Svelte components
│   │   ├── pages/        # Page-level components
│   │   └── lib/          # API client, stores
│   └── package.json
├── data/                 # SQLite database (gitignored)
├── Dockerfile
└── docker-compose.yml
```

## API

All endpoints are prefixed with `/api/`.

| Resource | Endpoints |
|----------|-----------|
| Health | `GET /api/health` |
| Hardware | `GET/POST /api/hardware`, `GET/PUT/DELETE /api/hardware/:id` |
| VMs | `GET/POST /api/vms`, `GET/PUT/DELETE /api/vms/:id` |
| Apps | `GET/POST /api/apps`, `GET/PUT/DELETE /api/apps/:id` |
| Storage | `GET/POST /api/storage`, `GET/PUT/DELETE /api/storage/:id` |
| Shares | `GET/POST /api/shares`, `GET/PUT/DELETE /api/shares/:id` |
| Networks | `GET/POST /api/networks`, `GET/PUT/DELETE /api/networks/:id` |
| Misc | `GET/POST /api/misc`, `GET/PUT/DELETE /api/misc/:id` |
| Documents | `GET/POST /api/docs`, `GET/PUT/DELETE /api/docs/:id`, `PATCH /api/docs/:id/move` |
| Inventory | `GET /api/inventory`, `GET /api/inventory/search?q=`, `GET /api/inventory/export`, `POST /api/inventory/import` |
| Map | `GET /api/map/graph`, `GET/PUT /api/map/layout`, `POST/DELETE /api/map/edges` |

## License

MIT
