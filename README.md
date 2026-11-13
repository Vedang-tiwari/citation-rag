# Citation RAG

A production-oriented Citation-based Retrieval-Augmented Generation (RAG) system built with FastAPI, PyMuPDF, Pydantic, and modular clean architecture.

The core objective is to answer user questions using information retrieved from uploaded documents while providing accurate, traceable, and verifiable citations for every factual claim.

---

## Current Status: Phase 1 (Foundation & Document Ingestion)

This repository currently implements **Phase 1** of the 4-phase development roadmap.

### Phase 1 Implemented Features

1. **Multi-Format Document Parsing**
   - **PDF**: Page-by-page text extraction using `PyMuPDF` (`fitz`), preserving 1-indexed physical page numbers, gracefully handling empty pages, and recording page-level extraction issues without silent discarding.
   - **TXT**: Text ingestion supporting UTF-8 and fallback encodings (`latin-1`, `cp1252`) with form-feed (`\x0c`) multi-page boundary detection.
   - **DOCX**: Word document parsing via `python-docx` extracting paragraphs, tables, and physical page breaks.

2. **Intelligent Text Chunking**
   - Configurable chunk size and chunk overlap.
   - Sentence-aware and paragraph-aware boundary preservation (avoids splitting mid-sentence or mid-word).
   - Generates unique chunk IDs (`chunk_{doc_id}_{index:04d}`).
   - Strictly preserves source document identity and original page numbers on every chunk.

3. **Security, Validation & Duplicate Handling**
   - File extension and MIME type validation.
   - Configurable file size limits (default 10MB).
   - Directory traversal sanitization and safe file storage.
   - SHA-256 content hashing for duplicate upload prevention (HTTP 409 Conflict).
   - Empty document detection.

4. **REST API Endpoints**
   - `GET /health` & `GET /api/v1/health` - Backend health check.
   - `POST /api/v1/documents/upload` - Multipart file upload, parsing, chunking, and persistence.
   - `GET /api/v1/documents` - List all ingested documents.
   - `GET /api/v1/documents/{document_id}` - Retrieve metadata and page-traceable chunks for a document.
   - `DELETE /api/v1/documents/{document_id}` - Remove document files, chunks, and metadata.

5. **Containerization & Tooling**
   - Production-ready `Dockerfile` and `docker-compose.yml`.
   - Comprehensive test suite covering PDF/TXT/DOCX extraction, chunking, overlap, metadata preservation, duplicate detection, and API routes.

---

## Project Structure

```text
citation-rag/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── documents.py      # Document CRUD and upload routes
│   │       └── health.py         # Healthcheck endpoints
│   ├── core/
│   │   ├── config.py             # Pydantic Settings and environment config
│   │   ├── exceptions.py         # Custom application exceptions and handlers
│   │   └── logging.py            # Logging setup
│   ├── ingestion/
│   │   ├── chunker.py            # Sentence-aware chunking engine
│   │   ├── loader.py             # File validation, sanitization, hashing
│   │   ├── metadata.py           # Metadata repository and persistence
│   │   └── parser.py             # PDF, TXT, DOCX parsers
│   ├── models/
│   │   └── schemas.py            # Pydantic schemas for documents & chunks
│   ├── services/
│   │   └── document_service.py   # Business logic coordination
│   └── main.py                   # FastAPI entrypoint and lifespan management
├── data/
│   ├── uploads/                  # Raw uploaded files
│   └── processed/                # Chunk records and metadata JSON
├── tests/
│   ├── conftest.py               # Shared test fixtures and generators
│   ├── test_api.py               # API endpoint integration tests
│   ├── test_chunking.py          # Chunking and boundary tests
│   └── test_ingestion.py         # Ingestion, parsing, and security tests
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── instruction.md
├── README.md
└── requirements.txt
```

---

## Quickstart

### 1. Local Environment Setup

Ensure Python 3.11+ is installed.

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Swagger UI documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Docker Deployment

```bash
docker compose up --build
```

---

## Running Tests

Execute the full pytest suite:

```bash
pytest -v
```

---

## Upcoming Phases (Per Roadmap)

- **Phase 2**: Embeddings & Persistent Vector Database (Sentence Transformers & Qdrant).
- **Phase 3**: RAG Generation & Citation Engine (Context Assembly, LLM Grounding & Citation Mapping).
- **Phase 4**: Evaluation, Reliability & Production Readiness (Faithfulness, Citation Correctness & PostgreSQL).

