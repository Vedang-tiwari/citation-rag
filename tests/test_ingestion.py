"""Tests for document parsing, loaders, security validation, and ingestion service."""

import pytest
from app.core.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsafePathError,
    UnsupportedFileTypeError,
)
from app.ingestion.loader import sanitize_filename, validate_upload
from app.ingestion.parser import DOCXParser, DocumentParser, PDFParser, TXTParser
from app.services.document_service import DocumentService


class TestDocumentParsing:
    """Tests for PDF, TXT, and DOCX parsers."""

    def test_pdf_extraction(self, temp_dir, sample_pdf_bytes):
        """Verify PyMuPDF extracts text page by page with correct page numbers."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(sample_pdf_bytes)

        parser = PDFParser()
        pages = parser.parse(file_path=pdf_path, document_name="test.pdf")

        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert "Retrieval-Augmented Generation" in pages[0].text
        assert not pages[0].has_error

        assert pages[1].page_number == 2
        assert "Page two of the evaluation document" in pages[1].text
        assert not pages[1].has_error

    def test_txt_extraction_with_pages(self, temp_dir, sample_txt_bytes):
        """Verify TXT parsing handles single and multi-page files (via form-feed)."""
        txt_path = temp_dir / "test.txt"
        txt_path.write_bytes(sample_txt_bytes)

        parser = TXTParser()
        pages = parser.parse(file_path=txt_path, document_name="test.txt")

        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert "This is page one" in pages[0].text
        assert pages[1].page_number == 2
        assert "This is page two" in pages[1].text

    def test_docx_extraction(self, temp_dir, sample_docx_bytes):
        """Verify python-docx extracts paragraphs and recognizes page breaks."""
        docx_path = temp_dir / "test.docx"
        docx_path.write_bytes(sample_docx_bytes)

        parser = DOCXParser()
        pages = parser.parse(file_path=docx_path, document_name="test.docx")

        assert len(pages) >= 2
        assert pages[0].page_number == 1
        assert "Introduction to Citation RAG" in pages[0].text
        assert pages[1].page_number == 2
        assert "Second page detailing chunking" in pages[1].text


class TestIngestionSecurityAndValidation:
    """Tests for input validation, security rules, and upload constraints."""

    def test_safe_path_sanitization(self):
        """Verify path traversal characters are sanitized or rejected."""
        # Simple traversal attempt
        assert sanitize_filename("safe_file.pdf") == "safe_file.pdf"
        assert sanitize_filename("../../secret.pdf") == "secret.pdf"

        # Traversal only
        with pytest.raises(UnsafePathError):
            sanitize_filename("..")
        with pytest.raises(UnsafePathError):
            sanitize_filename("")

    def test_unsupported_file_extension(self):
        """Verify uploading unsupported file extensions raises UnsupportedFileTypeError."""
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload(
                filename="script.py",
                content=b"print('hello')",
                content_type="text/x-python",
            )

        with pytest.raises(UnsupportedFileTypeError):
            validate_upload(
                filename="malicious.exe",
                content=b"binary_executable",
                content_type="application/octet-stream",
            )

    def test_empty_file_upload(self):
        """Verify empty (0 byte) file upload raises EmptyDocumentError."""
        with pytest.raises(EmptyDocumentError):
            validate_upload(
                filename="empty.txt",
                content=b"",
                content_type="text/plain",
            )

    def test_file_too_large(self):
        """Verify exceeding max upload size raises FileTooLargeError."""
        large_content = b"x" * 200
        with pytest.raises(FileTooLargeError):
            validate_upload(
                filename="large.txt",
                content=large_content,
                max_size_bytes=100,
            )


class TestDocumentServiceWorkflow:
    """Tests for the end-to-end ingestion service logic."""

    def test_successful_ingestion_and_metadata(
        self, isolated_document_service: DocumentService, sample_pdf_bytes
    ):
        """Verify end-to-end processing of a valid PDF document."""
        res = isolated_document_service.process_upload(
            filename="rag_paper.pdf",
            content=sample_pdf_bytes,
        )

        assert res.document_id.startswith("doc_")
        assert res.filename == "rag_paper.pdf"
        assert res.file_type == "pdf"
        assert res.total_pages == 2
        assert res.total_chunks >= 2

        # Check retrieval from store
        details = isolated_document_service.get_document(res.document_id)
        assert details.document.document_id == res.document_id
        assert len(details.chunks) == res.total_chunks
        assert details.chunks[0].document_name == "rag_paper.pdf"
        assert details.chunks[0].page_number in (1, 2)

    def test_duplicate_upload_rejection(
        self, isolated_document_service: DocumentService, sample_pdf_bytes
    ):
        """Verify that uploading the exact same document twice is detected and rejected."""
        # First upload succeeds
        res1 = isolated_document_service.process_upload(
            filename="document.pdf",
            content=sample_pdf_bytes,
        )
        assert res1.document_id is not None

        # Second upload with identical bytes must raise DocumentAlreadyExistsError
        with pytest.raises(DocumentAlreadyExistsError) as exc_info:
            isolated_document_service.process_upload(
                filename="document_copy.pdf",
                content=sample_pdf_bytes,
            )
        assert exc_info.value.details["document_id"] == res1.document_id

    def test_empty_content_document_handling(
        self, isolated_document_service: DocumentService
    ):
        """Verify document with no extractable text raises EmptyDocumentError."""
        with pytest.raises(EmptyDocumentError):
            isolated_document_service.process_upload(
                filename="blank.txt",
                content=b"   \n\n\t   ",
            )

    def test_document_deletion(
        self, isolated_document_service: DocumentService, sample_txt_bytes
    ):
        """Verify deleting a document removes its metadata and chunks."""
        res = isolated_document_service.process_upload(
            filename="notes.txt",
            content=sample_txt_bytes,
        )
        doc_id = res.document_id

        # Verify exists
        details = isolated_document_service.get_document(doc_id)
        assert details.document.document_id == doc_id

        # Delete
        del_res = isolated_document_service.delete_document(doc_id)
        assert del_res.deleted is True

        # Now fetching should raise DocumentNotFoundError
        with pytest.raises(DocumentNotFoundError):
            isolated_document_service.get_document(doc_id)

