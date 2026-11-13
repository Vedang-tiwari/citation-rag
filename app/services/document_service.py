"""Document service coordinating ingestion, parsing, chunking, and persistence."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    EmptyDocumentError,
)
from app.core.logging import get_logger
from app.ingestion.chunker import TextChunker
from app.ingestion.loader import (
    compute_sha256,
    generate_document_id,
    get_file_extension,
    save_uploaded_file,
    validate_upload,
)
from app.ingestion.metadata import MetadataStore, metadata_store
from app.ingestion.parser import DocumentParser
from app.models.schemas import (
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
    ProcessingStatus,
    SourceType,
)

logger = get_logger(__name__)


class DocumentService:
    """Service encapsulating all document ingestion and lifecycle business logic."""

    def __init__(
        self,
        store: Optional[MetadataStore] = None,
        parser: Optional[DocumentParser] = None,
    ) -> None:
        self.store = store or metadata_store
        self.parser = parser or DocumentParser()

    def process_upload(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> DocumentUploadResponse:
        """
        Validate, ingest, parse, chunk, and persist an uploaded document.
        """
        # 1. Validate security, extension, MIME, size
        safe_filename = validate_upload(
            filename=filename,
            content=content,
            content_type=content_type,
        )

        # 2. Check for duplicate upload via content hash
        file_hash = compute_sha256(content)
        existing_doc = self.store.find_by_hash(file_hash)
        if existing_doc:
            logger.warning(
                f"Duplicate upload detected: '{safe_filename}' matches existing document ID '{existing_doc.document_id}'"
            )
            raise DocumentAlreadyExistsError(
                document_id=existing_doc.document_id,
                filename=existing_doc.filename,
                file_hash=file_hash,
            )

        # 3. Generate unique document ID and save raw file
        doc_id = generate_document_id()
        saved_path = save_uploaded_file(
            document_id=doc_id,
            filename=safe_filename,
            content=content,
        )

        # 4. Determine file type
        ext = get_file_extension(safe_filename)
        file_type = ext.lstrip(".").lower()

        try:
            # 5. Parse document page by page
            pages = self.parser.parse_document(file_path=saved_path, filename=safe_filename)

            # Check if all pages are completely empty
            total_extracted_text = "".join(p.text for p in pages if p.text).strip()
            if not total_extracted_text and not any(p.has_error for p in pages):
                # Document has 0 extractable content
                logger.warning(f"Uploaded document '{safe_filename}' contains no readable text.")
                # We still create the metadata or raise empty error depending on strictness
                # Per spec: "Empty document handling" test requirement
                raise EmptyDocumentError(
                    filename=safe_filename,
                    message=f"Document '{safe_filename}' has {len(pages)} page(s) but contains no extractable text.",
                )

            # 6. Chunk text intelligently
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.chunk_pages(
                pages=pages,
                document_id=doc_id,
                document_name=safe_filename,
                source_type=file_type,
            )

            # 7. Build metadata record
            doc_metadata = DocumentMetadata(
                document_id=doc_id,
                filename=safe_filename,
                file_type=file_type,
                file_size=len(content),
                file_hash=file_hash,
                upload_timestamp=datetime.now(timezone.utc),
                processing_status=ProcessingStatus.COMPLETED,
                total_pages=len(pages),
                total_chunks=len(chunks),
                error_message=None,
            )

            # 8. Save metadata and chunks
            self.store.save(document=doc_metadata, chunks=chunks)

            return DocumentUploadResponse(
                document_id=doc_id,
                filename=safe_filename,
                file_type=file_type,
                file_size=len(content),
                status=ProcessingStatus.COMPLETED,
                total_pages=len(pages),
                total_chunks=len(chunks),
                message=f"Document '{safe_filename}' processed successfully: {len(pages)} page(s), {len(chunks)} chunk(s).",
            )

        except Exception as exc:
            # Clean up saved raw file if ingestion fails
            if saved_path.exists():
                try:
                    saved_path.unlink()
                except Exception:
                    pass
            raise exc

    def get_document(self, document_id: str) -> DocumentDetailResponse:
        """Fetch metadata and chunks for a specific document."""
        doc = self.store.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id=document_id)
        chunks = self.store.get_chunks(document_id)
        return DocumentDetailResponse(document=doc, chunks=chunks)

    def list_documents(self) -> DocumentListResponse:
        """List all registered documents."""
        docs = self.store.list_all()
        return DocumentListResponse(documents=docs, total=len(docs))

    def delete_document(self, document_id: str) -> DeleteDocumentResponse:
        """Delete document raw files, chunks, and metadata."""
        doc = self.store.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id=document_id)

        # Delete raw files matching doc_id in UPLOAD_DIR
        upload_dir = (
            settings.UPLOAD_DIR
            if settings.UPLOAD_DIR.is_absolute()
            else settings.BASE_DIR / settings.UPLOAD_DIR
        )
        if upload_dir.exists():
            for matching_file in upload_dir.glob(f"{document_id}_*"):
                try:
                    matching_file.unlink()
                    logger.info(f"Removed raw file {matching_file}")
                except Exception as e:
                    logger.warning(f"Could not delete raw file {matching_file}: {e}")

        # Delete metadata
        self.store.delete(document_id)

        return DeleteDocumentResponse(
            document_id=document_id,
            message=f"Document '{doc.filename}' ({document_id}) and all associated chunks were successfully deleted.",
            deleted=True,
        )


document_service = DocumentService()
