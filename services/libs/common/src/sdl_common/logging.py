import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str, pod: str):
        super().__init__()
        self.service = service
        self.pod = pod

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "pod": self.pod,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in getattr(record, "extra_fields", {}).items():
            entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(service: str, pod: str, level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service, pod))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # uvicorn's access log duplicates the request log emitted by the app middleware
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers[:] = []
        logging.getLogger(name).propagate = True
