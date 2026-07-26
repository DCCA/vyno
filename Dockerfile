FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
RUN pip install --no-cache-dir ".[runtime,llm]"

COPY bin /app/bin
COPY config /app/config
COPY data /app/data

RUN chmod +x /app/bin/digest \
    && mkdir -p /app/logs /app/.runtime

ENTRYPOINT ["/app/bin/digest"]
CMD ["--sources", "config/sources.yaml", "--sources-overlay", "data/sources.local.yaml", "--profile", "config/profile.yaml", "--profile-overlay", "data/profile.local.yaml", "--db", "digest-live.db", "bot"]
