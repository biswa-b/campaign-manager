"""
Custom exceptions for the Campaign Manager application.
"""

from typing import Optional, Any, Dict


class CampaignManagerException(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CampaignManagerException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})


class NotFoundError(CampaignManagerException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, "NOT_FOUND", {"resource_type": resource_type, "resource_id": resource_id})


class DuplicateError(CampaignManagerException):
    """Raised when trying to create a duplicate resource."""
    
    def __init__(self, resource_type: str, field: str, value: Any):
        message = f"{resource_type} with {field} '{value}' already exists"
        super().__init__(message, "DUPLICATE", {"resource_type": resource_type, "field": field, "value": value})


class DatabaseError(CampaignManagerException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation})


class NotificationError(CampaignManagerException):
    """Raised when notification sending fails."""
    
    def __init__(self, message: str, notification_type: Optional[str] = None, recipients: Optional[list] = None):
        super().__init__(message, "NOTIFICATION_ERROR", {
            "notification_type": notification_type,
            "recipients": recipients
        })


class CampaignError(CampaignManagerException):
    """Raised when campaign operations fail."""
    
    def __init__(self, message: str, campaign_id: Optional[int] = None, operation: Optional[str] = None):
        super().__init__(message, "CAMPAIGN_ERROR", {
            "campaign_id": campaign_id,
            "operation": operation
        })


class RecipientError(CampaignManagerException):
    """Raised when recipient operations fail."""
    
    def __init__(self, message: str, email: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "RECIPIENT_ERROR", {
            "email": email,
            "operation": operation
        })


class GroupError(CampaignManagerException):
    """Raised when group operations fail."""
    
    def __init__(self, message: str, group_id: Optional[int] = None, operation: Optional[str] = None):
        super().__init__(message, "GROUP_ERROR", {
            "group_id": group_id,
            "operation": operation
        })


class ConfigurationError(CampaignManagerException):
    """Raised when application configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})


class ExternalServiceError(CampaignManagerException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", {
            "service_name": service_name,
            "status_code": status_code
        }) 