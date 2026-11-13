"""Pydantic schemas and data models for document ingestion and metadata."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Supported document source types."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"


class ProcessingStatus(str, Enum):
    """Document processing pipeline status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PageContent(BaseModel):
    """Extracted text content for a single page of a document."""
    page_number: int = Field(..., ge=1, description="1-indexed physical page number")
    text: str = Field(..., description="Raw text extracted from this page")
    has_error: bool = Field(default=False, description="Whether an extraction error occurred on this page")
    error_message: Optional[str] = Field(default=None, description="Error details if extraction failed")


class ChunkMetadata(BaseModel):
    """Metadata and content for a single text chunk, traceable to document and page."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    document_name: str = Field(..., description="Original filename of the parent document")
    page_number: int = Field(..., ge=1, description="Original document page number where this chunk originates")
    chunk_index: int = Field(..., ge=0, description="Sequential index of chunk within the document")
    text: str = Field(..., description="Extracted document content for this chunk")
    source_type: str = Field(..., description="File source type: pdf, txt, or docx")
    char_count: Optional[int] = Field(default=None, description="Character count of the chunk text")


class DocumentMetadata(BaseModel):
    """Complete metadata for an ingested document."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original uploaded filename")
    file_type: str = Field(..., description="Document source type (pdf, txt, docx)")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of the uploaded file content")
    upload_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of upload"
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING, description="Current processing status"
    )
    total_pages: int = Field(default=0, ge=0, description="Total number of pages in document")
    total_chunks: int = Field(default=0, ge=0, description="Total number of chunks produced")
    error_message: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )


class DocumentUploadResponse(BaseModel):
    """API response model after document upload and processing."""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: ProcessingStatus
    total_pages: int
    total_chunks: int
    message: str


class DocumentDetailResponse(BaseModel):
    """API response model with document metadata and its chunks."""
    document: DocumentMetadata
    chunks: List[ChunkMetadata]


class DocumentListResponse(BaseModel):
    """API response model for listing all uploaded documents."""
    documents: List[DocumentMetadata]
    total: int


class DeleteDocumentResponse(BaseModel):
    """API response model when deleting a document."""
    document_id: str
    message: str
    deleted: bool
