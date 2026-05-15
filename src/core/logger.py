import logging
import sys
from contextvars import ContextVar

# Context var for request ID tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="system")

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | [%(request_id)s] | %(name)s | %(message)s")
        )
        # Custom filter to inject request_id into records
        class RequestIDFilter(logging.Filter):
            def filter(self, record):
                record.request_id = request_id_var.get()
                return True

        logger.addFilter(RequestIDFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
