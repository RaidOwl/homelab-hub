import secrets
from functools import wraps

from flask import request, jsonify

_valid_tokens = set()


def generate_token():
    token = secrets.token_urlsafe(32)
    _valid_tokens.add(token)
    return token


def invalidate_token(token):
    _valid_tokens.discard(token)


def is_valid_token(token):
    return token in _valid_tokens


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if is_valid_token(token):
                return f(*args, **kwargs)
        return jsonify(error="Unauthorized"), 401
    return decorated
