from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .exceptions import AppException
import logging

logger = logging.getLogger(__name__)


def setup_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "type": exc.__class__.__name__},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}", "type": "InternalError"},
        )
