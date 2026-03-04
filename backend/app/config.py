import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _get_database_uri():
    uri = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, '..', '..', 'data', 'homelab-hub.db')}"
    )
    # Heroku-style postgres:// → postgresql:// rewrite for SQLAlchemy 2.x
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


class Config:
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Allow larger request bodies for base64 image uploads (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    REQUIRE_AUTH = os.environ.get("REQUIRE_AUTH", "").lower() in ("true", "1", "yes")
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
