from flask import Blueprint, request, jsonify, current_app

from ..auth import generate_token, invalidate_token, is_valid_token

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "password" not in data:
        return jsonify(error="Password required"), 400
    admin_password = current_app.config.get("ADMIN_PASSWORD", "admin")
    if data["password"] == admin_password:
        token = generate_token()
        return jsonify(token=token)
    return jsonify(error="Invalid credentials"), 401


@bp.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        invalidate_token(token)
    return jsonify(message="Logged out")


@bp.route("/status", methods=["GET"])
def status():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if is_valid_token(token):
            return jsonify(authenticated=True)
    return jsonify(authenticated=False)
