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

RUN chmod +x /app/bin/digest \
    && mkdir -p /app/logs /app/.runtime

ENTRYPOINT ["/app/bin/digest"]
CMD ["--sources", "config/sources.yaml", "--sources-overlay", "data/sources.local.yaml", "--profile", "config/profile.yaml", "--db", "digest-live.db", "bot"]
