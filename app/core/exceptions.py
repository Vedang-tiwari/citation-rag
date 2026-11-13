"""Custom application exceptions and FastAPI exception handlers."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class CitationRAGException(Exception):
    """Base exception for all Citation RAG errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class DocumentNotFoundError(CitationRAGException):
    """Raised when a requested document does not exist."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with ID '{document_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id},
        )


class DocumentAlreadyExistsError(CitationRAGException):
    """Raised when an identical document has already been uploaded."""

    def __init__(self, document_id: str, filename: str, file_hash: str):
        super().__init__(
            message=f"Document '{filename}' already exists with ID '{document_id}'.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DOCUMENT_ALREADY_EXISTS",
            details={
                "document_id": document_id,
                "filename": filename,
                "file_hash": file_hash,
            },
        )


class UnsupportedFileTypeError(CitationRAGException):
    """Raised when an uploaded file type is not supported."""

    def __init__(self, filename: str, extension: str, mime_type: Optional[str] = None):
        super().__init__(
            message=f"Unsupported file type '{extension}' for file '{filename}'. Supported types: PDF, TXT, DOCX.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="UNSUPPORTED_FILE_TYPE",
            details={"filename": filename, "extension": extension, "mime_type": mime_type},
        )


class FileTooLargeError(CitationRAGException):
    """Raised when uploaded file exceeds the configured size limit."""

    def __init__(self, filename: str, file_size: int, max_size: int):
        super().__init__(
            message=f"File '{filename}' ({file_size} bytes) exceeds maximum limit of {max_size} bytes.",
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            error_code="FILE_TOO_LARGE",
            details={"filename": filename, "file_size": file_size, "max_size": max_size},
        )


class UnsafePathError(CitationRAGException):
    """Raised when a filename contains directory traversal or unsafe path characters."""

    def __init__(self, filename: str):
        super().__init__(
            message=f"Unsafe filename detected: '{filename}'. Directory traversal is prohibited.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="UNSAFE_PATH_DETECTED",
            details={"filename": filename},
        )


class EmptyDocumentError(CitationRAGException):
    """Raised when an uploaded document has 0 bytes or no extractable text."""

    def __init__(self, filename: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Document '{filename}' is empty or contains no extractable content.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMPTY_DOCUMENT",
            details={"filename": filename},
        )


class DocumentParsingError(CitationRAGException):
    """Raised when document parsing fails due to corruption or format issues."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to parse document '{filename}': {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DOCUMENT_PARSING_FAILED",
            details={"filename": filename, "reason": reason},
        )


class InvalidChunkingConfigError(CitationRAGException):
    """Raised when chunking parameters are invalid (e.g. overlap >= chunk_size)."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid chunking configuration: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_CHUNKING_CONFIG",
            details={"reason": reason},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application."""

    @app.exception_handler(CitationRAGException)
    async def citation_rag_exception_handler(
        request: Request, exc: CitationRAGException
    ) -> JSONResponse:
        logger.warning(
            f"Handled application exception: [{exc.error_code}] {exc.message} (Path: {request.url.path})"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            f"Unhandled exception on {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": {},
                }
            },
        )
