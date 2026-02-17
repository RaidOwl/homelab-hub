# ---- Stage 1: Build frontend ----
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Production image ----
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copy built frontend into Flask static directory
COPY --from=frontend-build /build/dist/ /app/static/

RUN mkdir -p /data

ENV DATABASE_URL=sqlite:////data/homelab-hub.db
ENV FLASK_ENV=production

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "wsgi:app"]
