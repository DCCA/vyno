from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOGGER_NAME = "digest"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "run_id": getattr(record, "run_id", ""),
            "stage": getattr(record, "stage", ""),
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


class RunLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        merged = dict(self.extra)
        event_extra = kwargs.get("extra")
        if isinstance(event_extra, dict):
            merged.update(event_extra)
        kwargs["extra"] = merged
        return msg, kwargs


def setup_logging(*, force: bool = False) -> logging.Logger:
    log_path = os.getenv("DIGEST_LOG_PATH", "logs/digest.log").strip() or "logs/digest.log"
    log_level = os.getenv("DIGEST_LOG_LEVEL", "INFO").strip().upper() or "INFO"
    max_bytes = int(os.getenv("DIGEST_LOG_MAX_BYTES", "5000000"))
    backup_count = int(os.getenv("DIGEST_LOG_BACKUP_COUNT", "5"))

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.propagate = False

    if force:
        for h in list(logger.handlers):
            logger.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    if logger.handlers:
        return logger

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger


def get_run_logger(run_id: str) -> RunLoggerAdapter:
    base = logging.getLogger(LOGGER_NAME)
    return RunLoggerAdapter(base, {"run_id": run_id})


def log_event(logger: logging.Logger | logging.LoggerAdapter, level: str, stage: str, message: str, **fields: Any) -> None:
    fn = getattr(logger, level.lower(), logger.info)
    fn(message, extra={"stage": stage, "extra_fields": fields})
