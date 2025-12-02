"""
Custom exception classes for Career Copilot application
Provides specific exception types for different error scenarios
"""


class CareerCopilotError(Exception):
    """Base exception class for all Career Copilot errors"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self):
        """Convert exception to dictionary for logging/API responses"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


# Database Exceptions
class DatabaseError(CareerCopilotError):
    """Base class for database-related errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class DocumentNotFoundError(DatabaseError):
    """Raised when a document is not found in the database"""
    pass


class DuplicateDocumentError(DatabaseError):
    """Raised when attempting to create a document that already exists"""
    pass


class ChunkStorageError(DatabaseError):
    """Raised when chunk storage operation fails"""
    pass


# Processing Exceptions
class ProcessingError(CareerCopilotError):
    """Base class for processing-related errors"""
    pass


class ResumeParsingError(ProcessingError):
    """Raised when resume parsing fails"""
    pass


class JDParsingError(ProcessingError):
    """Raised when job description parsing fails"""
    pass


class InvalidFormatError(ProcessingError):
    """Raised when input format is invalid"""
    pass


class PDFExtractionError(ProcessingError):
    """Raised when PDF text extraction fails"""
    pass


class LLMError(ProcessingError):
    """Raised when LLM API call fails"""
    pass


# Matching Exceptions
class MatchingError(CareerCopilotError):
    """Base class for matching-related errors"""
    pass


class InsufficientDataError(MatchingError):
    """Raised when there's insufficient data for matching"""
    pass


class MatchingTimeoutError(MatchingError):
    """Raised when matching operation times out"""
    pass


# Validation Exceptions
class ValidationError(CareerCopilotError):
    """Base class for validation errors"""
    pass


class InvalidInputError(ValidationError):
    """Raised when input validation fails"""
    pass


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing"""
    pass


class InvalidFileTypeError(ValidationError):
    """Raised when uploaded file type is not supported"""
    pass


# Cache Exceptions
class CacheError(CareerCopilotError):
    """Base class for cache-related errors"""
    pass


class CacheReadError(CacheError):
    """Raised when reading from cache fails"""
    pass


class CacheWriteError(CacheError):
    """Raised when writing to cache fails"""
    pass


# Configuration Exceptions
class ConfigurationError(CareerCopilotError):
    """Base class for configuration errors"""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid"""
    pass


# Example usage and error handler
def handle_exception(exception: Exception, logger=None):
    """
    Centralized exception handler that logs and formats exceptions

    Args:
        exception: The exception to handle
        logger: Logger instance (optional)

    Returns:
        Dictionary with error information
    """
    if isinstance(exception, CareerCopilotError):
        error_dict = exception.to_dict()
    else:
        error_dict = {
            'error_type': exception.__class__.__name__,
            'message': str(exception),
            'details': {}
        }

    if logger:
        logger.error(
            f"{error_dict['error_type']}: {error_dict['message']}",
            extra=error_dict['details'],
            exc_info=True
        )

    return error_dict
