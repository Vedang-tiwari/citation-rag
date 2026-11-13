"""Document loader: file validation, path sanitization, hashing, and storage."""

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Set
from app.core.config import settings
from app.core.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsafePathError,
    UnsupportedFileTypeError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def generate_document_id() -> str:
    """Generate a clean, collision-resistant document ID."""
    return f"doc_{uuid.uuid4().hex[:12]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent directory traversal and path injection attacks.
    Removes leading/trailing whitespace, path separators, and null bytes.
    """
    if not filename or not filename.strip():
        raise UnsafePathError(filename="<empty>")

    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        # Check specifically if malicious traversal was intended
        clean_name = os.path.basename(filename.replace("\\", "/"))
        if not clean_name or clean_name == "." or clean_name == "..":
            raise UnsafePathError(filename=filename)
    else:
        clean_name = filename.strip()

    # Normalize safe alphanumeric characters, underscores, hyphens, dots
    base = re.sub(r"[^\w\s\.-]", "_", clean_name).strip()
    if not base or base.startswith("."):
        # Prevent hidden files or purely dotted names
        base = f"doc_{base}" if base else "uploaded_document"

    return base


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash for byte content."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension including dot."""
    ext = Path(filename).suffix.lower()
    return ext


def validate_upload(
    filename: str,
    content: bytes,
    content_type: Optional[str] = None,
    allowed_extensions: Optional[Set[str]] = None,
    allowed_mime_types: Optional[Set[str]] = None,
    max_size_bytes: Optional[int] = None,
) -> str:
    """
    Validate upload filename, extension, MIME type, and size.
    Returns the sanitized filename.
    """
    allowed_exts = allowed_extensions or settings.ALLOWED_EXTENSIONS
    allowed_mimes = allowed_mime_types or settings.ALLOWED_MIME_TYPES
    max_size = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES

    # Check empty content
    file_size = len(content)
    if file_size == 0:
        raise EmptyDocumentError(filename=filename, message=f"Uploaded file '{filename}' is empty (0 bytes).")

    # Check file size limit
    if file_size > max_size:
        raise FileTooLargeError(filename=filename, file_size=file_size, max_size=max_size)

    # Sanitize and validate path safety
    safe_name = sanitize_filename(filename)

    # Check extension
    extension = get_file_extension(safe_name)
    if extension not in allowed_exts:
        raise UnsupportedFileTypeError(filename=safe_name, extension=extension, mime_type=content_type)

    # Check MIME type if provided and not generic
    if content_type:
        clean_mime = content_type.lower().split(";")[0].strip()
        # If MIME type is specified, check against allowed or generic fallback
        if clean_mime not in allowed_mimes and clean_mime != "application/octet-stream":
            logger.warning(
                f"MIME type '{clean_mime}' for '{safe_name}' not in strict allowed list, verifying extension."
            )

    return safe_name


def save_uploaded_file(document_id: str, filename: str, content: bytes) -> Path:
    """
    Safely persist uploaded file to the configured upload directory.
    Stores the file under `{document_id}_{safe_filename}` to guarantee uniqueness on disk.
    """
    settings.ensure_directories()
    safe_name = sanitize_filename(filename)
    storage_filename = f"{document_id}_{safe_name}"

    upload_dir = (
        settings.UPLOAD_DIR
        if settings.UPLOAD_DIR.is_absolute()
        else settings.BASE_DIR / settings.UPLOAD_DIR
    )
    dest_path = upload_dir / storage_filename

    # Ensure resolved path is strictly inside upload_dir
    dest_path = dest_path.resolve()
    if not str(dest_path).startswith(str(upload_dir.resolve())):
        raise UnsafePathError(filename=filename)

    with open(dest_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved uploaded file to {dest_path} ({len(content)} bytes)")
    return dest_path

