"""
Custom Exception Classes

Domain-specific exceptions for the SyncFlow service.
"""


class SyncFlowBaseException(Exception):
    """Base exception for all SyncFlow errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConnectionError(SyncFlowBaseException):
    """Raised when external service connection fails (APISmith, ScheduleHub)."""

    pass


class NormalizationError(SyncFlowBaseException):
    """Raised when data normalization fails."""

    pass


class TypeCoercionError(SyncFlowBaseException):
    """Raised when type coercion fails."""

    pass


class ValidationError(SyncFlowBaseException):
    """Raised when validation fails."""

    pass


class DeltaDetectionError(SyncFlowBaseException):
    """Raised when delta detection fails."""

    pass


class IdentityGenerationError(SyncFlowBaseException):
    """Raised when identity (BK_HASH, DATA_HASH) generation fails."""

    pass


class ParentChildResolutionError(SyncFlowBaseException):
    """Raised when parent-child dependency resolution fails."""

    pass


class SyncExecutionError(SyncFlowBaseException):
    """Raised when sync batch execution fails."""

    pass


class AlreadyExistsError(SyncFlowBaseException):
    """Raised when a resource already exists."""

    pass


class NotFoundError(SyncFlowBaseException):
    """Raised when a resource is not found."""

    pass


class AuthenticationError(SyncFlowBaseException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(SyncFlowBaseException):
    """Raised when authorization fails."""

    pass


class ConfigurationError(SyncFlowBaseException):
    """Raised when entity configuration is invalid or missing."""

    pass
