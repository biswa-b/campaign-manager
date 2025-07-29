"""
Error handling middleware for the Campaign Manager API.
"""

import logging
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from celery.exceptions import CeleryError

from ..exceptions import (
    CampaignManagerException,
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
    NotificationError,
    CampaignError,
    RecipientError,
    GroupError,
    ConfigurationError,
    ExternalServiceError,
)

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to catch and handle all exceptions.

    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint function

    Returns:
        JSONResponse: Formatted error response
    """
    try:
        return await call_next(request)
    except Exception as exc:
        return await handle_exception(request, exc)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle different types of exceptions and return appropriate responses.

    Args:
        request: FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse: Formatted error response
    """
    # Log the exception
    logger.error(
        f"Exception occurred: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
    )

    # Handle custom exceptions
    if isinstance(exc, CampaignManagerException):
        return handle_custom_exception(exc)

    # Handle FastAPI validation errors
    elif isinstance(exc, RequestValidationError):
        return handle_validation_error(exc)

    # Handle SQLAlchemy errors
    elif isinstance(exc, SQLAlchemyError):
        return handle_database_error(exc)

    # Handle Celery errors
    elif isinstance(exc, CeleryError):
        return handle_celery_error(exc)

    # Handle generic exceptions
    else:
        return handle_generic_error(exc)


def handle_custom_exception(exc: CampaignManagerException) -> JSONResponse:
    """Handle custom application exceptions."""
    status_code = get_status_code_for_exception(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": type(exc).__name__,
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


def handle_validation_error(exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


def handle_database_error(exc: SQLAlchemyError) -> JSONResponse:
    """Handle database-related errors."""
    logger.error(f"Database error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "DatabaseError",
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": {"operation": "database_operation"},
            }
        },
    )


def handle_celery_error(exc: CeleryError) -> JSONResponse:
    """Handle Celery-related errors."""
    logger.error(f"Celery error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "CeleryError",
                "code": "CELERY_ERROR",
                "message": "Background task operation failed",
                "details": {"operation": "background_task"},
            }
        },
    )


def handle_generic_error(exc: Exception) -> JSONResponse:
    """Handle generic/unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


def get_status_code_for_exception(exc: CampaignManagerException) -> int:
    """Get appropriate HTTP status code for custom exceptions."""
    if isinstance(exc, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    elif isinstance(exc, DuplicateError):
        return status.HTTP_409_CONFLICT
    elif isinstance(
        exc,
        (
            DatabaseError,
            NotificationError,
            CampaignError,
            RecipientError,
            GroupError,
            ConfigurationError,
            ExternalServiceError,
        ),
    ):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
