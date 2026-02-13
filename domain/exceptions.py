"""Custom exceptions for the application."""

class AppError(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DatabaseError(AppError):
    """Raised when a database operation fails."""
    pass


class AuthenticationError(AppError):
    """Raised when authentication fails."""
    pass


class ResourceNotFoundError(AppError):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(AppError):
    """Raised when data validation fails."""
    pass


class ExternalServiceError(AppError):
    """Raised when an external API (like Groq) fails."""
    pass
