class TranslationError(Exception):
    """Base exception for all translation-related errors in the domain."""

    pass


class TranslationReadError(TranslationError):
    """Raised when a file cannot be read or parsed correctly."""

    pass


class FileError(TranslationError):
    """Base exception for file system operations."""

    pass


class FileNotExistsError(FileError):
    """Raised when a target file does not exist in the file system."""

    pass


class FileWriteError(FileError):
    """Raised when a target file can not be written to the file system."""

    pass

class LanguageToolError(TranslationError):
    """Base exception for LanguageTool client errors."""
    pass


class LanguageToolConnectionError(LanguageToolError):
    """Raised when the server drops connection, timeouts, or responds with 500/502/503."""
    pass


class LanguageToolResponseError(LanguageToolError):
    """Raised when the response payload is malformed or unexpected."""
    pass
