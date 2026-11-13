"""Metadata persistence and repository for documents and chunks."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError
from app.core.logging import get_logger
from app.models.schemas import ChunkMetadata, DocumentMetadata

logger = get_logger(__name__)


class MetadataStore:
    """
    Persistent store for document metadata and chunk records.
    Persists data in the configured processed directory as structured JSON files.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = (
            storage_dir
            if storage_dir
            else (
                settings.PROCESSED_DIR
                if settings.PROCESSED_DIR.is_absolute()
                else settings.BASE_DIR / settings.PROCESSED_DIR
            )
        )
        self._lock = Lock()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_doc_path(self, document_id: str) -> Path:
        return self.storage_dir / f"{document_id}.json"

    def save(
        self,
        document: DocumentMetadata,
        chunks: List[ChunkMetadata],
    ) -> None:
        """Save or update document metadata and its associated chunks."""
        with self._lock:
            self._ensure_storage()
            data = {
                "document": document.model_dump(mode="json"),
                "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
            }
            doc_path = self._get_doc_path(document.document_id)
            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Persisted metadata for document ID '{document.document_id}' to {doc_path}")

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve document metadata by document ID."""
        doc_path = self._get_doc_path(document_id)
        if not doc_path.exists():
            return None

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DocumentMetadata.model_validate(data["document"])
        except Exception as exc:
            logger.error(f"Failed to read metadata for document '{document_id}': {exc}")
            return None

    def get_chunks(self, document_id: str) -> List[ChunkMetadata]:
        """Retrieve chunks for a given document ID."""
        doc_path = self._get_doc_path(document_id)
        if not doc_path.exists():
            raise DocumentNotFoundError(document_id=document_id)

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ChunkMetadata.model_validate(c) for c in data.get("chunks", [])]
        except Exception as exc:
            logger.error(f"Failed to load chunks for document '{document_id}': {exc}")
            return []

    def list_all(self) -> List[DocumentMetadata]:
        """List all documents currently registered in the store."""
        with self._lock:
            documents: List[DocumentMetadata] = []
            for file_path in self.storage_dir.glob("*.json"):
                if file_path.name == ".gitkeep":
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "document" in data:
                        documents.append(DocumentMetadata.model_validate(data["document"]))
                except Exception as exc:
                    logger.warning(f"Error parsing metadata file {file_path}: {exc}")
            # Sort newest first
            documents.sort(key=lambda d: d.upload_timestamp, reverse=True)
            return documents

    def find_by_hash(self, file_hash: str) -> Optional[DocumentMetadata]:
        """Find an existing document by its SHA-256 content hash."""
        all_docs = self.list_all()
        for doc in all_docs:
            if doc.file_hash == file_hash:
                return doc
        return None

    def delete(self, document_id: str) -> bool:
        """Delete document metadata and its chunks from store."""
        with self._lock:
            doc_path = self._get_doc_path(document_id)
            if doc_path.exists():
                doc_path.unlink()
                logger.info(f"Deleted metadata file for document ID '{document_id}'")
                return True
            return False


metadata_store = MetadataStore()

