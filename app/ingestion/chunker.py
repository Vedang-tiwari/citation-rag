"""Intelligent sentence- and paragraph-aware text chunking with metadata preservation."""

import re
from typing import List, Optional
from app.core.config import settings
from app.core.exceptions import InvalidChunkingConfigError
from app.core.logging import get_logger
from app.models.schemas import ChunkMetadata, PageContent

logger = get_logger(__name__)


class TextChunker:
    """
    Splits document text into overlapping chunks while preserving:
    1. Paragraph boundaries where possible.
    2. Sentence boundaries (avoiding cutting mid-sentence).
    3. Exact original document page numbers.
    4. Unique chunk IDs and sequential indices.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        min_chunk_size: Optional[int] = None,
    ) -> None:
        self.chunk_size = chunk_size if chunk_size is not None else settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.DEFAULT_CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size if min_chunk_size is not None else settings.MIN_CHUNK_SIZE

        self._validate_config()

    def _validate_config(self) -> None:
        """Validate chunk size and overlap constraints."""
        if not isinstance(self.chunk_size, int) or self.chunk_size <= 0:
            raise InvalidChunkingConfigError(f"chunk_size must be a positive integer, got {self.chunk_size}.")
        if not isinstance(self.chunk_overlap, int) or self.chunk_overlap < 0:
            raise InvalidChunkingConfigError(
                f"chunk_overlap cannot be negative, got {self.chunk_overlap}."
            )
        if self.chunk_overlap >= self.chunk_size:
            raise InvalidChunkingConfigError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly less than chunk_size ({self.chunk_size})."
            )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using punctuation boundaries."""
        # Split on sentence endings followed by whitespace
        sentence_pattern = r"(?<=[.!?])\s+"
        raw_sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in raw_sentences if s.strip()]

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs by double newlines."""
        raw_paras = re.split(r"\n\s*\n", text)
        return [p.strip() for p in raw_paras if p.strip()]

    def _chunk_text_unit(self, text: str) -> List[str]:
        """
        Chunk a single coherent block of text respecting sentence boundaries and overlap.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text]

        # Break text down into atomic sentence units
        sentences = self._split_into_sentences(text)
        if not sentences:
            sentences = [text]

        chunks: List[str] = []
        current_sentences: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If a single sentence exceeds chunk_size, split by words
            if sentence_len > self.chunk_size:
                # Flush any accumulated sentences first
                if current_sentences:
                    chunk_str = " ".join(current_sentences).strip()
                    if chunk_str:
                        chunks.append(chunk_str)
                    current_sentences = []
                    current_len = 0

                words = sentence.split()
                sub_chunk: List[str] = []
                sub_len = 0
                for word in words:
                    added_len = len(word) + (1 if sub_len > 0 else 0)
                    if sub_len + added_len > self.chunk_size and sub_chunk:
                        chunks.append(" ".join(sub_chunk).strip())
                        # Overlap: keep last few words up to chunk_overlap
                        overlap_words: List[str] = []
                        overlap_chars = 0
                        for w in reversed(sub_chunk):
                            if overlap_chars + len(w) + 1 <= self.chunk_overlap:
                                overlap_words.insert(0, w)
                                overlap_chars += len(w) + 1
                            else:
                                break
                        sub_chunk = overlap_words
                        sub_len = sum(len(w) for w in sub_chunk) + max(0, len(sub_chunk) - 1)

                    sub_chunk.append(word)
                    sub_len += len(word) + (1 if len(sub_chunk) > 1 else 0)

                if sub_chunk:
                    chunks.append(" ".join(sub_chunk).strip())
                continue

            # Standard accumulation of sentences
            added_len = sentence_len + (1 if current_len > 0 else 0)
            if current_len + added_len > self.chunk_size and current_sentences:
                chunk_str = " ".join(current_sentences).strip()
                if chunk_str:
                    chunks.append(chunk_str)

                # Overlap: take trailing sentences that fit within chunk_overlap
                overlap_sentences: List[str] = []
                overlap_chars = 0
                for s in reversed(current_sentences):
                    if overlap_chars + len(s) + 1 <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_chars += len(s) + 1
                    else:
                        break

                current_sentences = overlap_sentences
                current_len = sum(len(s) for s in current_sentences) + max(0, len(current_sentences) - 1)

            current_sentences.append(sentence)
            current_len += sentence_len + (1 if len(current_sentences) > 1 else 0)

        if current_sentences:
            chunk_str = " ".join(current_sentences).strip()
            # Avoid duplicate trailing chunk if identical to last
            if chunk_str and (not chunks or chunks[-1] != chunk_str):
                chunks.append(chunk_str)

        return chunks

    def chunk_pages(
        self,
        pages: List[PageContent],
        document_id: str,
        document_name: str,
        source_type: str,
    ) -> List[ChunkMetadata]:
        """
        Produce ChunkMetadata objects for each page in the document.
        Preserves original document page numbers and maintains sequential chunk_index.
        """
        all_chunks: List[ChunkMetadata] = []
        global_chunk_index = 0

        for page in pages:
            if not page.text or not page.text.strip():
                continue

            page_chunks = self._chunk_text_unit(page.text)

            for text_chunk in page_chunks:
                clean_text = text_chunk.strip()
                if not clean_text:
                    continue

                chunk_id = f"chunk_{document_id}_{global_chunk_index:04d}"
                chunk_meta = ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page.page_number,
                    chunk_index=global_chunk_index,
                    text=clean_text,
                    source_type=source_type,
                    char_count=len(clean_text),
                )
                all_chunks.append(chunk_meta)
                global_chunk_index += 1

        logger.info(
            f"Chunked document '{document_name}' ({document_id}): "
            f"{len(pages)} pages -> {len(all_chunks)} chunks."
        )
        return all_chunks
