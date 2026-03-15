# ── Stage 1: Build frontend ──────────────────────────────────────────
FROM node:20-slim AS frontend

WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY web/ ./
RUN npm run build

# ── Stage 2: Python runtime ─────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY bin /app/bin
COPY src /app/src
COPY config /app/config
COPY data /app/data

# Copy built frontend into the image
COPY --from=frontend /build/dist /app/web/dist

RUN chmod +x /app/bin/digest \
    && mkdir -p /app/logs /app/.runtime

ENTRYPOINT ["/app/bin/digest"]
CMD ["--sources", "config/sources.yaml", "--sources-overlay", "data/sources.local.yaml", "--profile", "config/profile.yaml", "--profile-overlay", "data/profile.local.yaml", "--db", "digest-live.db", "bot"]
