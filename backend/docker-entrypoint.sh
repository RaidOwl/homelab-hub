#!/bin/sh
set -e
echo "Waiting for PostgreSQL..."
until python -c "import psycopg2,os,sys; psycopg2.connect(os.environ['DATABASE_URL']); sys.exit(0)" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL ready."
cd /app
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
alembic stamp head 2>/dev/null || true
exec gunicorn --bind 0.0.0.0:8000 --workers 2 wsgi:app
