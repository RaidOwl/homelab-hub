from flask import g, jsonify, request


def init_auth(app):
    """Register Authentik forward-auth middleware."""
    require_auth = app.config.get("REQUIRE_AUTH", False)

    @app.before_request
    def extract_auth_headers():
        g.user = None
        username = request.headers.get("X-Authentik-Username")
        if username:
            g.user = {
                "username": username,
                "name": request.headers.get("X-Authentik-Name", ""),
                "email": request.headers.get("X-Authentik-Email", ""),
            }
        elif require_auth:
            # Allow health check without auth
            if request.path in ("/api/health",):
                return
            return jsonify(error="Authentication required"), 401

    @app.route("/api/auth/user")
    def auth_user():
        if g.user:
            return jsonify(g.user)
        return jsonify({"username": None, "name": None, "email": None})
