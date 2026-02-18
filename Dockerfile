# ---- Stage 1: Build frontend ----
FROM node:24-alpine AS frontend-build
WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Production image ----
FROM python:3.14-alpine
WORKDIR /app

COPY backend/requirements.txt .
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install --system --compile-bytecode --no-cache-dir -r requirements.txt
# bytecode compilation makes startup faster but the image bigger, see: https://docs.astral.sh/uv/pip/compatibility/#bytecode-compilation

COPY backend/ .

# Copy built frontend into Flask static directory
COPY --from=frontend-build /build/dist/ /app/static/

RUN mkdir -p /data

ENV DATABASE_URL=sqlite:////data/homelab-hub.db
ENV FLASK_ENV=production

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "wsgi:app"]
