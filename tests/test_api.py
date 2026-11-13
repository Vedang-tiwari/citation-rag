"""Tests for API routes: health, root, and document management endpoints."""

import io
import pytest
from fastapi import UploadFile
from app.api.routes import documents, health
from app.core.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    UnsupportedFileTypeError,
)
from app.main import create_application
from app.models.schemas import ProcessingStatus
from app.services.document_service import DocumentService


class TestAPIRoutes:
    """Direct route-level integration tests verifying API contracts and status responses."""

    def test_health_endpoint(self):
        """Verify /health returns service status and phase indicator."""
        res = health.health_check()
        assert res["status"] == "healthy"
        assert res["phase"] == 1
        assert "service" in res

    def test_root_endpoint(self):
        """Verify root route provides app name and status."""
        app = create_application()
        root_handler = None
        for route in app.routes:
            if getattr(route, "path", None) == "/" and "GET" in getattr(route, "methods", set()):
                root_handler = route.endpoint
                break

        assert root_handler is not None
        data = root_handler()
        assert data["status"] == "online"
        assert data["phase"] == 1
        assert data["docs_url"] == "/docs"

    def test_upload_pdf_route(
        self, isolated_document_service: DocumentService, sample_pdf_bytes: bytes
    ):
        """Verify uploading a PDF file through the route handler."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            upload_file = UploadFile(
                filename="quantum_rag.pdf",
                file=io.BytesIO(sample_pdf_bytes),
                headers={"content-type": "application/pdf"},
            )
            response = documents.upload_document(file=upload_file)

            assert response.document_id.startswith("doc_")
            assert response.filename == "quantum_rag.pdf"
            assert response.file_type == "pdf"
            assert response.total_pages == 2
            assert response.total_chunks >= 2
            assert response.status == ProcessingStatus.COMPLETED
        finally:
            documents.document_service = original_service

    def test_upload_txt_route(
        self, isolated_document_service: DocumentService, sample_txt_bytes: bytes
    ):
        """Verify uploading a TXT document through the route handler."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            upload_file = UploadFile(
                filename="manual.txt",
                file=io.BytesIO(sample_txt_bytes),
                headers={"content-type": "text/plain"},
            )
            response = documents.upload_document(file=upload_file)

            assert response.filename == "manual.txt"
            assert response.file_type == "txt"
            assert response.total_pages == 2
            assert response.total_chunks >= 2
        finally:
            documents.document_service = original_service

    def test_upload_docx_route(
        self, isolated_document_service: DocumentService, sample_docx_bytes: bytes
    ):
        """Verify uploading a DOCX file through the route handler."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            upload_file = UploadFile(
                filename="spec.docx",
                file=io.BytesIO(sample_docx_bytes),
                headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            )
            response = documents.upload_document(file=upload_file)

            assert response.filename == "spec.docx"
            assert response.file_type == "docx"
            assert response.total_pages >= 2
            assert response.total_chunks >= 2
        finally:
            documents.document_service = original_service

    def test_upload_duplicate_rejection(
        self, isolated_document_service: DocumentService, sample_pdf_bytes: bytes
    ):
        """Verify uploading duplicate document raises DocumentAlreadyExistsError."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            f1 = UploadFile(
                filename="first.pdf",
                file=io.BytesIO(sample_pdf_bytes),
            )
            documents.upload_document(file=f1)

            # Duplicate upload
            f2 = UploadFile(
                filename="second.pdf",
                file=io.BytesIO(sample_pdf_bytes),
            )
            with pytest.raises(DocumentAlreadyExistsError) as exc_info:
                documents.upload_document(file=f2)
            assert "already exists" in str(exc_info.value)
        finally:
            documents.document_service = original_service

    def test_upload_invalid_type_rejection(
        self, isolated_document_service: DocumentService
    ):
        """Verify uploading unsupported file raises UnsupportedFileTypeError."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            f = UploadFile(
                filename="exploit.exe",
                file=io.BytesIO(b"executable_binary_content"),
            )
            with pytest.raises(UnsupportedFileTypeError):
                documents.upload_document(file=f)
        finally:
            documents.document_service = original_service

    def test_list_and_get_document_routes(
        self, isolated_document_service: DocumentService, sample_txt_bytes: bytes
    ):
        """Verify listing documents and retrieving specific document details via routes."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            f = UploadFile(
                filename="listing_test.txt",
                file=io.BytesIO(sample_txt_bytes),
            )
            upload_res = documents.upload_document(file=f)
            doc_id = upload_res.document_id

            # List
            list_res = documents.list_documents()
            assert list_res.total >= 1
            assert any(d.document_id == doc_id for d in list_res.documents)

            # Get
            detail_res = documents.get_document(document_id=doc_id)
            assert detail_res.document.document_id == doc_id
            assert len(detail_res.chunks) == upload_res.total_chunks
            assert detail_res.chunks[0].document_name == "listing_test.txt"
        finally:
            documents.document_service = original_service

    def test_get_nonexistent_document_raises_404(
        self, isolated_document_service: DocumentService
    ):
        """Verify retrieving non-existent document ID raises DocumentNotFoundError."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            with pytest.raises(DocumentNotFoundError):
                documents.get_document(document_id="doc_missing_404")
        finally:
            documents.document_service = original_service

    def test_delete_document_route(
        self, isolated_document_service: DocumentService, sample_txt_bytes: bytes
    ):
        """Verify deleting a document removes it from storage and metadata."""
        original_service = documents.document_service
        try:
            documents.document_service = isolated_document_service
            f = UploadFile(
                filename="to_delete.txt",
                file=io.BytesIO(sample_txt_bytes),
            )
            upload_res = documents.upload_document(file=f)
            doc_id = upload_res.document_id

            # Delete
            del_res = documents.delete_document(document_id=doc_id)
            assert del_res.deleted is True
            assert del_res.document_id == doc_id

            # Subsequent fetch should raise 404
            with pytest.raises(DocumentNotFoundError):
                documents.get_document(document_id=doc_id)
        finally:
            documents.document_service = original_service
