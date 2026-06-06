"""Global exception handlers for structured error responses."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound


class AppError(Exception):
    """Base application error with structured response."""

    def __init__(self, message: str, code: str = "internal_error", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="not_found", status_code=status.HTTP_404_NOT_FOUND)


class BadRequestError(AppError):
    """Bad request."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message, code="bad_request", status_code=status.HTTP_400_BAD_REQUEST)


class ConflictError(AppError):
    """Resource conflict."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, code="conflict", status_code=status.HTTP_409_CONFLICT)


def _error_response(message: str, code: str, status_code: int, details: dict | list | None = None) -> JSONResponse:
    """Build a structured JSON error response."""
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.message, exc.code, exc.status_code)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        from fastapi import HTTPException
        he = exc  # type: ignore[assignment]
        assert isinstance(he, HTTPException)
        return _error_response(
            str(he.detail),
            code="http_error",
            status_code=he.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            "Request validation failed",
            code="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=[{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()],
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(
            "Data validation failed",
            code="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=[{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()],
        )

    @app.exception_handler(NoResultFound)
    async def no_result_found_handler(_request: Request, _exc: NoResultFound) -> JSONResponse:
        return _error_response("Resource not found", "not_found", status.HTTP_404_NOT_FOUND)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
        return _error_response(
            f"Database integrity error: {str(exc.orig)}" if exc.orig else "Database integrity error",
            "conflict",
            status.HTTP_409_CONFLICT,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            "An unexpected error occurred",
            "internal_error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"type": type(exc).__name__, "message": str(exc)},
        )
