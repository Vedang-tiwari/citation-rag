"""Document management API endpoints."""

from typing import Annotated, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from app.core.exceptions import CitationRAGException
from app.core.logging import get_logger
from app.models.schemas import (
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.document_service import document_service

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
)
def upload_document(
    file: Annotated[UploadFile, File(description="Document file to upload (PDF, TXT, DOCX)")],
    chunk_size: Annotated[
        Optional[int],
        Query(ge=50, le=10000, description="Optional custom chunk size in characters"),
    ] = None,
    chunk_overlap: Annotated[
        Optional[int],
        Query(ge=0, le=5000, description="Optional custom chunk overlap in characters"),
    ] = None,
) -> DocumentUploadResponse:
    """
    Upload a document (PDF, TXT, DOCX), validate its type and security,
    extract page-level text, intelligently chunk the content, and preserve citation metadata.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or empty.",
        )

    try:
        content = file.file.read()
        return document_service.process_upload(
            filename=file.filename,
            content=content,
            content_type=file.content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    finally:
        file.file.close()


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
)
def list_documents() -> DocumentListResponse:
    """Retrieve metadata for all ingested documents in the system."""
    return document_service.list_documents()


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and chunks",
)
def get_document(document_id: str) -> DocumentDetailResponse:
    """Retrieve complete metadata and chunks for a specific document ID."""
    return document_service.get_document(document_id=document_id)


@router.delete(
    "/{document_id}",
    response_model=DeleteDocumentResponse,
    summary="Delete a document",
)
def delete_document(document_id: str) -> DeleteDocumentResponse:
    """Delete a document, removing its stored raw files, chunk metadata, and citations."""
    return document_service.delete_document(document_id=document_id)
