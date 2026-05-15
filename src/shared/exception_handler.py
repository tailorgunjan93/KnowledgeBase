from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.logger import get_logger
from .exceptions import AppException

logger = get_logger(__name__)


def setup_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "type": exc.__class__.__name__},
        )

    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        if isinstance(exc, RequestValidationError):
            return JSONResponse(status_code=422, content={"detail": exc.errors()})

        logger.exception("Unhandled exception")
        import traceback
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {repr(exc)}\n{tb}", "type": "InternalError"},
        )
