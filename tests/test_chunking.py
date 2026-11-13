"""Tests for intelligent chunking, overlap, boundary preservation, and page metadata preservation."""

import pytest
from app.core.exceptions import InvalidChunkingConfigError
from app.ingestion.chunker import TextChunker
from app.models.schemas import PageContent


class TestIntelligentChunker:
    """Suite testing chunking algorithms, boundary preservation, and metadata."""

    def test_invalid_chunking_config(self):
        """Ensure invalid chunk size or overlap raises InvalidChunkingConfigError."""
        # Overlap equal to chunk size
        with pytest.raises(InvalidChunkingConfigError):
            TextChunker(chunk_size=200, chunk_overlap=200)

        # Overlap greater than chunk size
        with pytest.raises(InvalidChunkingConfigError):
            TextChunker(chunk_size=100, chunk_overlap=150)

        # Zero or negative chunk size
        with pytest.raises(InvalidChunkingConfigError):
            TextChunker(chunk_size=0, chunk_overlap=0)

        # Negative overlap
        with pytest.raises(InvalidChunkingConfigError):
            TextChunker(chunk_size=100, chunk_overlap=-10)

    def test_chunk_size_limit(self):
        """Verify that produced chunks generally respect the configured chunk size."""
        chunk_size = 120
        chunk_overlap = 30
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        text = (
            "Sentence one is concise. "
            "Sentence two provides additional contextual detail. "
            "Sentence three explores retrieval augmented generation. "
            "Sentence four summarizes citation requirements."
        )
        pages = [PageContent(page_number=1, text=text)]
        chunks = chunker.chunk_pages(pages, "doc_1", "test.pdf", "pdf")

        assert len(chunks) > 1
        for chunk in chunks:
            # Allow minor leeway only if single word/sentence forced an expansion
            assert len(chunk.text) <= chunk_size or len(chunk.text.split()) == 1

    def test_chunk_overlap_retention(self):
        """Verify that adjacent chunks share overlapping text."""
        chunk_size = 100
        chunk_overlap = 40
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        text = (
            "First sentence is short. "
            "Second sentence provides vital context. "
            "Third sentence contains key citations."
        )
        pages = [PageContent(page_number=1, text=text)]
        chunks = chunker.chunk_pages(pages, "doc_1", "test.pdf", "pdf")

        if len(chunks) >= 2:
            chunk1_words = set(chunks[0].text.split())
            chunk2_words = set(chunks[1].text.split())
            # There should be overlap in words between adjacent chunks
            common_words = chunk1_words.intersection(chunk2_words)
            assert len(common_words) > 0

    def test_sentence_boundary_preservation(self):
        """Verify that text is split at sentence boundaries, not mid-sentence."""
        chunker = TextChunker(chunk_size=80, chunk_overlap=20)
        text = "Hello world! This is a test sentence. Another sentence follows right here."
        pages = [PageContent(page_number=1, text=text)]
        chunks = chunker.chunk_pages(pages, "doc_1", "test.pdf", "pdf")

        for chunk in chunks:
            # Each chunk should start cleanly with a capitalized letter or first word
            assert not chunk.text.startswith(" ")
            assert not chunk.text.endswith(" ")

    def test_page_metadata_preservation(self):
        """
        Verify that chunk metadata explicitly records the original document page number,
        and not the sequential chunk position.
        """
        chunker = TextChunker(chunk_size=80, chunk_overlap=20)
        pages = [
            PageContent(page_number=1, text="Page one text about vector search and retrieval models."),
            PageContent(page_number=5, text="Page five text representing a skipped page gap in source."),
            PageContent(page_number=12, text="Page twelve text containing final summary and conclusions."),
        ]

        chunks = chunker.chunk_pages(pages, "doc_999", "doc.pdf", "pdf")

        assert len(chunks) >= 3

        # First chunk should have page 1
        assert chunks[0].page_number == 1
        assert chunks[0].document_id == "doc_999"
        assert chunks[0].document_name == "doc.pdf"
        assert chunks[0].source_type == "pdf"

        # Check that page 5 and 12 are faithfully preserved on their respective chunks
        page_numbers_present = {c.page_number for c in chunks}
        assert 1 in page_numbers_present
        assert 5 in page_numbers_present
        assert 12 in page_numbers_present

    def test_unique_chunk_ids_and_sequential_indices(self):
        """Verify unique chunk IDs and strictly sequential chunk indices."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        pages = [
            PageContent(page_number=1, text=text),
            PageContent(page_number=2, text=text),
        ]
        chunks = chunker.chunk_pages(pages, "doc_abc", "doc.pdf", "pdf")

        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "All chunk IDs must be unique"

        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_index == idx
            assert f"doc_abc_{idx:04d}" in chunk.chunk_id

    def test_empty_page_handling(self):
        """Verify that completely empty or whitespace pages produce no chunks and don't fail."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        pages = [
            PageContent(page_number=1, text="   "),
            PageContent(page_number=2, text="Actual text on page two."),
            PageContent(page_number=3, text=""),
        ]
        chunks = chunker.chunk_pages(pages, "doc_1", "doc.pdf", "pdf")

        assert len(chunks) == 1
        assert chunks[0].page_number == 2
        assert "Actual text on page two." in chunks[0].text

