# backend/app/core/exceptions.py
from typing import Any, Dict, Optional, List
from fastapi import HTTPException
from datetime import datetime

class PollySystemException(Exception):
    """Base exception for PollySystem"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.error_code or self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

class PluginError(PollySystemException):
    """Raised when there's an error with plugin operations"""
    def __init__(
        self,
        message: str,
        plugin_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"plugin_name": plugin_name, **(details or {})},
            error_code="PLUGIN_ERROR"
        )
        self.plugin_name = plugin_name

class MachineConnectionError(PollySystemException):
    """Raised when there's an error connecting to a machine"""
    def __init__(
        self,
        message: str,
        machine_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"machine_id": machine_id, **(details or {})},
            error_code="MACHINE_CONNECTION_ERROR"
        )
        self.machine_id = machine_id

class DockerError(PollySystemException):
    """Raised when there's an error with Docker operations"""
    def __init__(
        self,
        message: str,
        container_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"container_id": container_id, **(details or {})},
            error_code="DOCKER_ERROR"
        )
        self.container_id = container_id

class MonitoringError(PollySystemException):
    """Raised when there's an error with monitoring operations"""
    def __init__(
        self,
        message: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"resource_id": resource_id, **(details or {})},
            error_code="MONITORING_ERROR"
        )
        self.resource_id = resource_id

class ValidationError(PollySystemException):
    """Raised when there's a validation error"""
    def __init__(
        self,
        message: str,
        errors: List[Dict[str, Any]]
    ):
        super().__init__(
            message=message,
            details={"errors": errors},
            error_code="VALIDATION_ERROR"
        )
        self.errors = errors

class ConfigurationError(PollySystemException):
    """Raised when there's a configuration error"""
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"config_key": config_key, **(details or {})},
            error_code="CONFIGURATION_ERROR"
        )
        self.config_key = config_key

class AuthenticationError(PollySystemException):
    """Raised when there's an authentication error"""
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(PollySystemException):
    """Raised when there's an authorization error"""
    def __init__(
        self,
        message: str = "Not authorized",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={
                "resource": resource,
                "action": action,
                **(details or {})
            },
            error_code="AUTHORIZATION_ERROR"
        )
        self.resource = resource
        self.action = action

class APIError(HTTPException):
    """Custom API error with additional data"""
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code or f"HTTP_{status_code}"
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": self.error_code,
                "message": message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            },
            headers=headers
        )