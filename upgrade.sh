#!/usr/bin/env bash
set -euo pipefail

#
# Upgrade script for non-Docker homelab-hub deployments.
#
# Usage:
#   cd /path/to/homelab-hub
#   ./upgrade.sh [--branch main]
#
# Defaults to the 'main' branch. Override with --branch <name>.
# Assumes the repo was originally cloned via git and that
# backend/.venv exists with pip installed.
#

BRANCH="main"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
SERVICE_NAME="homelab-hub"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) BRANCH="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

info()  { echo -e "\033[1;34m==>\033[0m $*"; }
warn()  { echo -e "\033[1;33m==>\033[0m $*"; }
error() { echo -e "\033[1;31m==>\033[0m $*" >&2; }

cd "$APP_DIR"

info "Upgrading homelab-hub in $APP_DIR (branch: $BRANCH)"

# --- Pre-flight checks ---
for cmd in git python3 npm; do
    if ! command -v "$cmd" &>/dev/null; then
        error "Required command '$cmd' not found. Install it first."
        exit 1
    fi
done

if ! command -v nmap &>/dev/null; then
    warn "nmap not found — LAN/port scanning will not work."
    warn "Install it: sudo apt install nmap (Debian) / brew install nmap (macOS)"
fi

if [ ! -d "$BACKEND_DIR/.venv" ]; then
    error "Python venv not found at $BACKEND_DIR/.venv — run initial setup first."
    exit 1
fi

# --- Backup database ---
DATA_DIR="$APP_DIR/data"
if [ -d "$DATA_DIR" ]; then
    BACKUP_NAME="data-backup-$(date +%Y%m%d-%H%M%S)"
    info "Backing up $DATA_DIR → $APP_DIR/$BACKUP_NAME"
    cp -r "$DATA_DIR" "$APP_DIR/$BACKUP_NAME"
else
    warn "No data/ directory found — skipping backup."
fi

# --- Stop service if running under systemd ---
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    info "Stopping $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME"
    RESTART_SERVICE=1
else
    RESTART_SERVICE=0
    warn "Service '$SERVICE_NAME' not active — skipping stop (restart manually if needed)."
fi

# --- Pull latest code ---
info "Pulling latest code from origin/$BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# --- Update backend dependencies ---
info "Updating Python dependencies..."
source "$BACKEND_DIR/.venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q

# --- Run database migrations ---
info "Running database migrations..."
cd "$BACKEND_DIR"
alembic upgrade head

# --- Rebuild frontend ---
info "Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm ci --silent

info "Building frontend for production..."
npm run build

# --- Restart service ---
if [ "$RESTART_SERVICE" -eq 1 ]; then
    info "Restarting $SERVICE_NAME service..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        info "Service is running."
    else
        error "Service failed to start. Check: sudo journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
else
    warn "No systemd service was stopped — start the app manually if needed."
fi

info "Upgrade complete!"
