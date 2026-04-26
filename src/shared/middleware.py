from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
import logging
from .logging import request_id_var

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"
        return response


def setup_middleware(app):
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
