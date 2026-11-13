# Citation RAG
## Agent Development Instructions

## 1. Project Overview

Build a production-oriented Citation-based Retrieval-Augmented Generation (RAG) system using Python, LLMs, embeddings, and a vector database.

The primary objective is to develop a RAG application that answers user questions using information retrieved from uploaded documents while providing accurate, traceable, and verifiable citations for every factual claim.

The system must not generate unsupported answers. If the retrieved context does not contain sufficient information to answer a question, the system must explicitly communicate that the information is unavailable.

### Core Philosophy

Every generated answer should be:
- Contextually grounded.
- Supported by retrieved document chunks.
- Accompanied by source citations.
- Traceable to the original document.
- Resistant to hallucinations.
- Evaluated for retrieval and generation quality.

### Primary Use Case

A user uploads multiple documents, asks questions about their contents, and receives answers with citations pointing to the exact source documents and relevant page numbers.

---

# 2. Technology Stack

Use the following technologies unless a technical limitation requires an alternative. Any proposed change must be explained before implementation.

| Component | Technology |
|---|---|
| Programming Language | Python 3.11+ |
| Backend Framework | FastAPI |
| Data Validation | Pydantic |
| LLM Framework | LangChain (optional abstraction layer) |
| Embedding Models | Sentence Transformers / Hugging Face |
| Vector Database | Qdrant |
| Metadata Database | PostgreSQL |
| ORM | SQLAlchemy |
| Document Processing | PyMuPDF |
| Text Splitting | Custom chunking / LangChain |
| LLM | Configurable API-based or local model |
| API Testing | Pytest |
| Containerization | Docker |
| Configuration | Environment Variables / Pydantic Settings |
| Logging | Python Logging |
| API Documentation | FastAPI Swagger UI |

### Architectural Principles

1. Keep business logic independent of API routes.
2. Separate document processing, retrieval, generation, and citation logic.
3. Use modular and reusable components.
4. Avoid unnecessary abstractions.
5. Keep LLM and embedding providers configurable.
6. Never hardcode API keys or credentials.
7. Implement proper exception handling.
8. Use asynchronous processing where appropriate.
9. Maintain type hints throughout the codebase.
10. Write testable and maintainable code.

---

# 3. System Architecture

The application should follow this high-level architecture:

```text
                  USER
                    |
                    v
              FastAPI Backend
                    |
          +---------+---------+
          |                   |
          v                   v
    Document Upload       Query API
          |                   |
          v                   v
    Document Parser      Query Processing
          |                   |
          v                   v
    Text Extraction      Query Embeddings
          |                   |
          v                   v
    Text Chunking        Vector Retrieval
          |                   |
          v                   v
    Metadata Mapping     Context Assembly
          |                   |
          v                   v
    Embedding Model      LLM Generation
          |                   |
          v                   v
    Qdrant Database      Citation Mapping
          |                   |
          +---------+---------+
                    |
                    v
              Final Response
                    |
          +---------+---------+
          |                   |
          v                   v
      Answer Text        Source Citations
```

---

# 4. Four-Phase Development Strategy

IMPORTANT: Development must happen in exactly four controlled phases.

The coding agent must follow these instructions:

- Implement only the phase explicitly requested by the user.
- Never automatically proceed to the next phase.
- Do not implement future-phase functionality prematurely.
- After completing a phase, stop.
- Provide an implementation summary.
- Report completed features and pending features.
- Report test results.
- Wait for explicit user approval.

The user will activate each phase using commands such as:

`Start Phase 1`

`Start Phase 2`

`Start Phase 3`

`Start Phase 4`

A request to inspect, explain, or review a phase does not authorize implementation.

---

# PHASE 1 — Foundation & Document Ingestion

## Objective

Build the foundational backend and document ingestion pipeline.

The system must accept documents, extract their content, split the extracted text into meaningful chunks, and preserve source metadata.

## 1. Project Initialization

Create a clean project structure.

Suggested structure:

```text
citation-rag/
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── documents.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── parser.py
│   │   ├── chunker.py
│   │   └── metadata.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   └── document_service.py
│   │
│   └── main.py
│
├── data/
│   ├── uploads/
│   └── processed/
│
├── tests/
│   ├── test_ingestion.py
│   └── test_chunking.py
│
├── scripts/
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── instruction.md
```

## 2. Document Upload

Implement document upload functionality.

Supported initial formats:

- PDF
- TXT
- DOCX

Requirements:

- Validate file extensions.
- Validate MIME types.
- Implement configurable file size limits.
- Generate unique document IDs.
- Prevent unsafe file path handling.
- Handle duplicate uploads.
- Store document metadata.
- Provide upload status.

API:

`POST /api/v1/documents/upload`

`GET /api/v1/documents`

`GET /api/v1/documents/{document_id}`

`DELETE /api/v1/documents/{document_id}`

## 3. Document Parsing

Implement text extraction using PyMuPDF for PDFs.

Requirements:

- Extract text page by page.
- Preserve page numbers.
- Handle empty pages.
- Detect extraction failures.
- Support TXT and DOCX.
- Preserve document identity throughout processing.

Do not silently discard pages with extraction problems.

## 4. Intelligent Chunking

Implement configurable text chunking.

Requirements:

- Configurable chunk size.
- Configurable chunk overlap.
- Avoid splitting text unnecessarily in the middle of sentences.
- Preserve paragraph boundaries where possible.
- Generate unique chunk IDs.
- Maintain document-to-chunk relationships.

Each chunk must contain metadata:

```json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_001",
  "document_name": "research.pdf",
  "page_number": 5,
  "chunk_index": 0,
  "text": "Extracted document content...",
  "source_type": "pdf"
}
```

Page numbers must refer to the original document, not chunk positions.

## 5. Metadata Management

Create reusable metadata models.

Track:

- Document ID
- Original filename
- File type
- Upload timestamp
- Processing status
- Total pages
- Total chunks
- Chunk ID
- Page number
- Chunk index

## 6. Phase 1 Testing

Implement tests for:

- PDF extraction.
- TXT extraction.
- DOCX extraction.
- Empty document handling.
- Invalid file uploads.
- Chunk size.
- Chunk overlap.
- Page metadata preservation.
- Duplicate document handling.

## Phase 1 Completion Criteria

Phase 1 is complete when:

- FastAPI starts successfully.
- Documents can be uploaded.
- Supported formats are parsed.
- Text is extracted correctly.
- Chunks are generated.
- Page-level metadata is preserved.
- Document APIs work.
- Tests pass.

Do not implement embeddings, vector retrieval, or LLM generation in this phase.

STOP after Phase 1.

---

# PHASE 2 — Embeddings & Vector Database

## Objective

Implement semantic indexing and persistent vector storage.

The system should transform document chunks into embeddings and store them in Qdrant with their associated metadata.

## 1. Embedding Pipeline

Implement a dedicated embedding service.

Requirements:

- Use Sentence Transformers or Hugging Face embedding models.
- Keep embedding models configurable.
- Support batch embedding generation.
- Handle embedding failures.
- Avoid regenerating embeddings unnecessarily.
- Normalize vectors when required by the selected similarity metric.

Suggested interface:

```python
class EmbeddingService:

    def embed_documents(self, texts):
        pass

    def embed_query(self, query):
        pass
```

The query and document embedding paths must use compatible models and configurations.

## 2. Qdrant Integration

Configure Qdrant as the primary vector database.

Requirements:

- Create collections automatically.
- Configure vector dimensions correctly.
- Configure similarity metrics.
- Store chunk embeddings.
- Store chunk metadata as payload.
- Support persistent storage.
- Support deletion of vectors.
- Support document-level filtering.

Suggested payload:

```json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_001",
  "document_name": "research.pdf",
  "page_number": 5,
  "chunk_index": 0,
  "text": "Original chunk text"
}
```

## 3. Indexing Pipeline

Implement the following workflow:

```text
Document Upload
      |
      v
Text Extraction
      |
      v
Chunk Generation
      |
      v
Embedding Generation
      |
      v
Qdrant Indexing
      |
      v
Indexing Confirmation
```

Requirements:

- Generate embeddings in batches.
- Associate each vector with its chunk metadata.
- Handle partial indexing failures.
- Prevent duplicate indexing.
- Support document re-indexing.
- Support deleting all chunks associated with a document.
- Track indexing status.

## 4. Semantic Retrieval

Implement a retrieval service.

Suggested interface:

```python
class RetrievalService:

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids=None
    ):
        pass
```

Requirements:

- Convert queries into embeddings.
- Perform vector similarity search.
- Return top-K relevant chunks.
- Return similarity scores.
- Return original document metadata.
- Support document filters.
- Support configurable retrieval thresholds.

## 5. Retrieval Results

Expected response:

```json
{
  "query": "What is retrieval augmented generation?",
  "results": [
    {
      "chunk_id": "chunk_001",
      "document_id": "doc_001",
      "document_name": "research.pdf",
      "page_number": 5,
      "text": "RAG combines retrieval systems with generative models...",
      "score": 0.89
    }
  ]
}
```

## 6. Phase 2 Testing

Test:

- Embedding generation.
- Embedding dimensions.
- Vector insertion.
- Vector persistence.
- Similarity search.
- Top-K retrieval.
- Document filtering.
- Document deletion.
- Duplicate indexing.
- Retrieval metadata integrity.

## Phase 2 Completion Criteria

- Documents are converted into embeddings.
- Vectors are stored in Qdrant.
- Semantic retrieval works.
- Metadata remains attached to vectors.
- Document filtering works.
- Tests pass.

Do not implement LLM answer generation or final citation generation yet.

STOP after Phase 2.

---

# PHASE 3 — RAG Generation & Citation Engine

## Objective

Build the core Citation RAG functionality.

The application must retrieve relevant document chunks, construct context, generate grounded answers, and attach citations that map back to the original documents.

This is the most important phase of the project.

## 1. Query Processing

Implement a query processing service.

Responsibilities:

- Validate incoming questions.
- Generate query embeddings.
- Retrieve relevant chunks.
- Apply retrieval thresholds.
- Prepare context for generation.

## 2. Context Assembly

Implement a dedicated context builder.

Requirements:

- Assemble retrieved chunks.
- Preserve document identifiers.
- Preserve page numbers.
- Preserve chunk identifiers.
- Remove redundant context where appropriate.
- Respect configurable context limits.
- Prevent source metadata from being lost.

Each context passage should have an explicit source identifier.

Example:

```text
[SOURCE: S1]
Document: research.pdf
Page: 5
Chunk ID: chunk_001

Content:
RAG combines retrieval systems with generative models.
```

## 3. LLM Integration

Create a provider-independent LLM service.

Requirements:

- Support configurable LLM providers.
- Support local and API-based models.
- Use environment variables for credentials.
- Configure temperature and token limits.
- Handle timeouts.
- Handle rate limits.
- Handle provider errors.

Suggested interface:

```python
class GenerationService:

    def generate_answer(
        self,
        query: str,
        context: str
    ):
        pass
```

## 4. Citation-Aware Prompt Engineering

Create a dedicated prompt template.

The model must follow these rules:

1. Answer only using the supplied context.
2. Never invent sources.
3. Never invent page numbers.
4. Every factual claim must have supporting citations.
5. Cite using source identifiers such as `[S1]`.
6. If multiple sources support a claim, cite all relevant sources.
7. If context is insufficient, explicitly say so.
8. Distinguish direct evidence from reasonable inference.
9. Never cite a document that was not retrieved.
10. Do not produce fabricated quotations.

Example prompt:

```text
You are a citation-grounded AI assistant.

Answer the user's question using ONLY the provided context.

STRICT RULES:

- Every factual claim must include a citation.
- Use citations in the format [S1], [S2].
- Only cite sources provided in the context.
- Never invent document names or page numbers.
- If evidence is insufficient, say so.
- If sources disagree, explain the disagreement.
- Do not present unsupported assumptions as facts.

QUESTION:
{question}

CONTEXT:
{context}

Generate a concise, evidence-supported answer.
```

## 5. Citation Mapping Engine

Do not rely exclusively on the LLM to generate citation metadata.

Implement a separate citation mapping service.

The LLM should return source identifiers.

The backend must resolve those identifiers against the actual retrieved source metadata.

Example:

LLM response:

```text
RAG combines information retrieval with generative models [S1].
```

Backend citation resolution:

```json
{
  "source_id": "S1",
  "document_id": "doc_001",
  "document_name": "research.pdf",
  "page_number": 5,
  "chunk_id": "chunk_001"
}
```

Requirements:

- Validate every cited source ID.
- Reject unknown source identifiers.
- Map citations to original documents.
- Preserve page numbers.
- Prevent citations to unretrieved documents.
- Detect uncited factual claims where feasible.
- Support multiple citations per answer.
- Maintain source traceability.

Important: Citation presence does not automatically prove citation correctness. Implement an independent validation layer to check whether cited source passages actually support their associated claims.

## 6. Citation Response Format

Expected API response:

```json
{
  "question": "What is RAG?",
  "answer": "RAG combines information retrieval with generative models [S1].",
  "citations": [
    {
      "citation_id": "S1",
      "document_id": "doc_001",
      "document_name": "research.pdf",
      "page_number": 5,
      "chunk_id": "chunk_001",
      "quoted_text": "RAG combines retrieval systems with generative models."
    }
  ],
  "retrieval_metadata": {
    "retrieved_chunks": 5,
    "used_chunks": 2
  },
  "grounded": true
}
```

The `grounded` field must not simply mean that citations exist. It should reflect the result of the implemented grounding checks.

## 7. Hallucination Prevention

Implement:

- No-context detection.
- Low-relevance retrieval detection.
- Insufficient-evidence responses.
- Citation validation.
- Source consistency checks.
- Unsupported claim detection where feasible.

Never force the LLM to generate an answer when retrieval confidence is insufficient.

## 8. Query API

Implement:

`POST /api/v1/query`

Example request:

```json
{
  "question": "What is RAG?",
  "top_k": 5,
  "document_ids": ["doc_001"]
}
```

Implement proper response validation and error handling.

## 9. Phase 3 Testing

Test:

- End-to-end RAG workflow.
- Context assembly.
- Citation source mapping.
- Invalid citation IDs.
- Multiple citations.
- Missing citations.
- Unsupported answers.
- Empty retrieval results.
- Low-relevance results.
- Conflicting sources.
- Page number correctness.
- Citation-to-chunk traceability.

## Phase 3 Completion Criteria

- Users can ask questions.
- Relevant chunks are retrieved.
- LLM generates context-grounded answers.
- Answers include citations.
- Citations resolve to original documents and pages.
- Invalid citations are rejected.
- Insufficient evidence is handled correctly.
- Tests pass.

STOP after Phase 3.

---

# PHASE 4 — Evaluation, Reliability & Production Readiness

## Objective

Improve the system's reliability and evaluate whether its answers and citations are genuinely accurate.

A Citation RAG system is not production-ready simply because it generates answers with clickable sources.

It must demonstrate retrieval quality, answer quality, and citation correctness.

## 1. RAG Evaluation Framework

Implement an evaluation module.

Evaluate:

### Retrieval Metrics

- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Hit Rate@K
- Normalized Discounted Cumulative Gain (NDCG)

### Generation Metrics

- Faithfulness
- Answer Relevance
- Context Relevance
- Answer Correctness

### Citation Metrics

- Citation Precision
- Citation Recall
- Citation Coverage
- Citation Correctness
- Citation Completeness

Do not treat citation coverage as equivalent to citation correctness.

## 2. Evaluation Dataset

Create a structured evaluation dataset.

Example:

```json
{
  "question": "What is RAG?",
  "expected_answer": "RAG combines retrieval and generation.",
  "expected_sources": [
    {
      "document_id": "doc_001",
      "page_number": 5
    }
  ]
}
```

Support:

- Custom evaluation questions.
- Expected answers.
- Expected source documents.
- Expected page numbers.
- Automated evaluation reports.

## 3. Citation Verification

Build a citation verification pipeline.

Check:

- Whether cited sources exist.
- Whether citations point to retrieved chunks.
- Whether cited passages support the associated claims.
- Whether factual claims are missing citations.
- Whether the citation points to the correct page.
- Whether irrelevant citations are attached.

Use deterministic checks wherever possible and an LLM-based evaluator for semantic support verification.

Do not treat an LLM evaluator as absolute ground truth.

## 4. Reliability & Performance

Implement:

- Structured logging.
- Request validation.
- API error handling.
- Retrieval latency tracking.
- Generation latency tracking.
- Embedding latency tracking.
- Configurable timeouts.
- Retry policies.
- Database health checks.
- Graceful shutdown.
- Request-level correlation IDs.

## 5. Persistence & Data Management

Use PostgreSQL for application metadata.

Persist:

- Document information.
- Upload history.
- Indexing status.
- Query history.
- Citation records.
- Evaluation results.

Qdrant remains responsible for vector storage and similarity search.

Ensure document deletion also removes associated vectors and metadata.

## 6. Dockerization

Provide:

- Application Dockerfile.
- Docker Compose configuration.
- Qdrant service.
- PostgreSQL service.
- Persistent database volumes.
- Environment configuration.
- Health checks.

The application should be runnable using:

```bash
docker compose up --build
```

## 7. Documentation

Update README.md with:

- Project overview.
- Problem statement.
- Solution.
- Architecture.
- Tech stack.
- Features.
- Installation instructions.
- Environment configuration.
- API documentation.
- Example requests and responses.
- Citation workflow.
- Evaluation methodology.
- Performance considerations.
- Limitations.
- Future improvements.

## 8. Final Testing

Run:

- Unit tests.
- Integration tests.
- API tests.
- Ingestion tests.
- Retrieval tests.
- Citation validation tests.
- End-to-end tests.
- Evaluation benchmarks.

## Phase 4 Completion Criteria

- Evaluation framework works.
- Retrieval and generation metrics are reported.
- Citation correctness is evaluated.
- Structured logging works.
- PostgreSQL persistence works.
- Docker Compose works.
- All critical tests pass.
- README is complete.

STOP after Phase 4.

---

# 5. Global Coding Agent Rules

These instructions apply throughout all four phases.

## Rule 1: Strict Phase Execution

Never implement multiple phases in one execution.

If the user says "Start Phase 1", implement Phase 1 only.

If the user says "Start Phase 2", first inspect the existing Phase 1 implementation and then implement Phase 2.

Do not assume permission to start subsequent phases.

## Rule 2: Inspect Before Coding

Before implementing a phase:

1. Inspect the existing repository.
2. Read existing source files.
3. Understand current architecture.
4. Identify completed functionality.
5. Identify missing functionality.
6. Avoid unnecessary rewrites.

Preserve working code unless changes are necessary.

## Rule 3: No Fake Implementations

Never:

- Use hardcoded fake retrieval results.
- Return fabricated citations.
- Mock core functionality in production code.
- Hide errors using empty responses.
- Generate random similarity scores.
- Pretend indexing succeeded when it failed.

Mocks are permitted only in appropriate tests.

## Rule 4: Code Quality

- Follow PEP 8.
- Use type hints.
- Use meaningful variable names.
- Implement modular functions.
- Avoid giant service classes.
- Use dependency injection where appropriate.
- Document complex logic.
- Handle exceptions explicitly.

## Rule 5: Testing

Every major feature must have tests.

Do not mark a feature complete merely because the code was written.

Run the relevant tests and report their results.

## Rule 6: Environment Management

- Never commit `.env`.
- Provide `.env.example`.
- Keep secrets outside source code.
- Make providers configurable.
- Document required environment variables.

## Rule 7: No Unnecessary Complexity

Do not introduce:

- Kubernetes.
- Microservices.
- Kafka.
- Redis.
- Distributed orchestration.
- Complex agent frameworks.

Unless they solve a demonstrated requirement.

Prioritize a well-engineered modular monolith.

---

# 6. Agent Completion Report

After finishing each phase, provide the following report:

```text
========================================
       CITATION RAG - PHASE REPORT
========================================

Phase: [Phase Number]

1. IMPLEMENTED FEATURES
- Feature 1
- Feature 2
- Feature 3

2. FILES CREATED
- List of new files

3. FILES MODIFIED
- List of modified files

4. TEST RESULTS
- Total tests:
- Passed:
- Failed:
- Skipped:

5. TECHNICAL DECISIONS
- Important implementation decisions

6. KNOWN ISSUES
- Remaining problems

7. PHASE STATUS
- COMPLETED / PARTIALLY COMPLETED

========================================
NEXT ACTION: WAIT FOR USER APPROVAL
========================================
```

After producing this report, stop execution.

Do not automatically start another phase.

---

# 7. Final Project Vision

At completion, Citation RAG should provide:

1. Document ingestion and parsing.
2. Page-aware text chunking.
3. Semantic embedding generation.
4. Persistent vector storage.
5. Metadata-aware retrieval.
6. Context-grounded LLM generation.
7. Claim-level source attribution.
8. Citation-to-document traceability.
9. Hallucination and unsupported-answer detection.
10. Citation verification.
11. RAG evaluation benchmarks.
12. Production-oriented API and Docker deployment.

The ultimate goal is to demonstrate that the system does not merely generate answers with references, but generates answers whose factual claims can be traced back to supporting evidence.

**Development Rule: One Phase at a Time. Never Proceed Without Explicit User Authorization.**