import json
import os
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from ..models import *
from ..models.base import db

bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")

EXPORTS_DIR = "/data/exports"


def _check_webhook_auth():
    """Validate webhook secret from Authorization header or X-Webhook-Secret."""
    secret = current_app.config.get("WEBHOOK_SECRET", "")
    if not secret:
        return jsonify(error="WEBHOOK_SECRET not configured"), 500

    auth = request.headers.get("Authorization", "")
    header_secret = request.headers.get("X-Webhook-Secret", "")

    if auth.startswith("Bearer "):
        token = auth[7:]
        if token == secret:
            return None
    if header_secret == secret:
        return None

    return jsonify(error="Unauthorized"), 401


@bp.route("/export-trigger", methods=["POST"])
def export_trigger():
    """Trigger a database export (for use by N8N or other webhook callers)."""
    auth_error = _check_webhook_auth()
    if auth_error:
        return auth_error

    try:
        data = {
            "hardware": [h.to_dict() for h in Hardware.query.all()],
            "vms": [vm.to_dict() for vm in VM.query.all()],
            "apps": [app.to_dict() for app in AppService.query.all()],
            "storage": [s.to_dict() for s in Storage.query.all()],
            "networks": [n.to_dict() for n in Network.query.all()],
            "misc": [m.to_dict() for m in Misc.query.all()],
            "documents": [d.to_dict() for d in Document.query.all()],
        }

        os.makedirs(EXPORTS_DIR, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.json"
        filepath = os.path.join(EXPORTS_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return jsonify(
            status="ok",
            filename=filename,
            download_url=f"/api/webhooks/exports/{filename}",
        )
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route("/exports/<filename>", methods=["GET"])
def download_export(filename):
    """Download a previously generated export file."""
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        return jsonify(error="Invalid filename"), 400
    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True)
