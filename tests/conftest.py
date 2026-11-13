"""Pytest fixtures and test document generators for Phase 1 test suite."""

import tempfile
from pathlib import Path
from typing import Generator
import pytest
import pymupdf as fitz
import docx

from app.core.config import settings
from app.ingestion.metadata import MetadataStore
from app.main import create_application
from app.services.document_service import DocumentService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory cleaned up after test execution."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def isolated_metadata_store(temp_dir: Path) -> MetadataStore:
    """Create an isolated metadata store operating in a temporary directory."""
    store_dir = temp_dir / "processed"
    store_dir.mkdir(parents=True, exist_ok=True)
    return MetadataStore(storage_dir=store_dir)


@pytest.fixture
def isolated_document_service(temp_dir: Path, isolated_metadata_store: MetadataStore) -> DocumentService:
    """Create a DocumentService operating in a sandbox directory."""
    # Override settings directories temporarily for tests
    upload_dir = temp_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR = upload_dir
    settings.PROCESSED_DIR = temp_dir / "processed"
    return DocumentService(store=isolated_metadata_store)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate a valid 2-page PDF in-memory using PyMuPDF."""
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Retrieval-Augmented Generation (RAG) is an AI architecture that enhances "
        "Large Language Models by grounding them with factual context retrieved from external documents. "
        "This prevents hallucinations and provides verifiable references for each claim.",
    )

    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "Page two of the evaluation document discusses vector databases and embeddings. "
        "Embeddings map high-dimensional text to dense vectors where semantic similarity correlates "
        "with proximity in the vector space.",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Generate a valid multi-page DOCX in-memory using python-docx."""
    doc = docx.Document()
    p1 = doc.add_paragraph(
        "Introduction to Citation RAG architectures. "
        "Every factual claim must have a corresponding citation pointing to the exact document and page."
    )
    doc.add_page_break()
    p2 = doc.add_paragraph(
        "Second page detailing chunking methodologies. Sentence-aware chunking preserves boundaries."
    )
    
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        doc.save(str(tmp_path))
        data = tmp_path.read_bytes()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return data


@pytest.fixture
def sample_txt_bytes() -> bytes:
    """Generate a multi-page TXT file using form feed characters."""
    content = (
        "This is page one of the plain text document.\n"
        "It contains foundational information about citation mapping.\n"
        "\x0c"
        "This is page two of the plain text document.\n"
        "It details chunking overlap and boundary preservation rules."
    )
    return content.encode("utf-8")
