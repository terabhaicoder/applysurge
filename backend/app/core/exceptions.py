"""
Custom exception classes and FastAPI exception handlers.
"""

from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class JobPilotException(Exception):
    """Base exception for all JobPilot application errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AuthenticationError(JobPilotException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationError(JobPilotException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundError(JobPilotException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", detail: Optional[Any] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ConflictError(JobPilotException):
    """Raised when there is a resource conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Resource already exists", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class ValidationError(JobPilotException):
    """Raised for custom validation errors beyond Pydantic."""

    def __init__(self, message: str = "Validation failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class RateLimitError(JobPilotException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"retry_after": retry_after} if retry_after else None,
        )
        self.retry_after = retry_after


class ExternalServiceError(JobPilotException):
    """Raised when an external service call fails."""

    def __init__(self, service: str, message: str = "External service error", detail: Optional[Any] = None):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )


class AgentError(JobPilotException):
    """Raised when the automation agent encounters an error."""

    def __init__(self, message: str = "Agent error occurred", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class PaymentError(JobPilotException):
    """Raised when a payment-related operation fails."""

    def __init__(self, message: str = "Payment processing failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
        )


class QuotaExceededError(JobPilotException):
    """Raised when a user exceeds their plan quota."""

    def __init__(self, message: str = "Quota exceeded", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


async def jobpilot_exception_handler(request: Request, exc: JobPilotException) -> JSONResponse:
    """Handle all JobPilot custom exceptions."""
    response_body = {
        "error": True,
        "message": exc.message,
        "status_code": exc.status_code,
    }
    if exc.detail is not None:
        response_body["detail"] = exc.detail

    headers = {}
    if isinstance(exc, RateLimitError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=headers if headers else None,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a generic error response."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An internal server error occurred",
            "status_code": 500,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(JobPilotException, jobpilot_exception_handler)
    app.add_exception_handler(AuthenticationError, jobpilot_exception_handler)
    app.add_exception_handler(AuthorizationError, jobpilot_exception_handler)
    app.add_exception_handler(NotFoundError, jobpilot_exception_handler)
    app.add_exception_handler(ConflictError, jobpilot_exception_handler)
    app.add_exception_handler(ValidationError, jobpilot_exception_handler)
    app.add_exception_handler(RateLimitError, jobpilot_exception_handler)
    app.add_exception_handler(ExternalServiceError, jobpilot_exception_handler)
    app.add_exception_handler(AgentError, jobpilot_exception_handler)
    app.add_exception_handler(PaymentError, jobpilot_exception_handler)
    app.add_exception_handler(QuotaExceededError, jobpilot_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
