import logging
from logging.config import dictConfig
from contextvars import ContextVar

request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get() or "-"
        return True

def configure_logging(level: str = "INFO") -> None:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": "app.core.config.logging.RequestIdFilter"}},
        "formatters": {
            "default": {"format": "%(asctime)s | %(levelname)s | %(name)s | rid=%(request_id)s | %(message)s"},
            "uvicorn": {"format": "%(asctime)s | %(levelname)s | %(name)s | rid=%(request_id)s | %(message)s"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default", "filters": ["request_id"]},
            "uvicorn": {"class": "logging.StreamHandler", "formatter": "uvicorn", "filters": ["request_id"]},
        },
        "loggers": {
            "": {"handlers": ["console"], "level": level},
            "uvicorn": {"handlers": ["uvicorn"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["uvicorn"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["uvicorn"], "level": level, "propagate": False},
        },
    })

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
