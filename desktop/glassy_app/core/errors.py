"""Application specific exceptions."""


class AppError(Exception):
    """Base class for errors that are safe to show to the user."""


class ValidationError(AppError):
    """User supplied data failed validation."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


class NotFoundError(AppError):
    """A requested record does not exist."""


class ConflictError(AppError):
    """An operation would violate a uniqueness or integrity rule."""
