# BookWorm Architecture

## Project Goal

BookWorm is a document question-answering web application that lets a user upload a PDF, retrieve relevant content, and ask natural-language questions whose answers are grounded in the uploaded document. The system must keep BERT as the core answer-generation model while using a retrieval layer to handle large documents.

## High-Level Design

```text
User
  │
  ▼
Frontend (Next.js)
  │
  ▼
API Layer (FastAPI)
  │
  ▼
Document pipeline
  ├── PDF validation and storage
  ├── text extraction
  ├── cleaning and normalization
  ├── chunking
  ├── retrieval index
  └── BERT QA service
  │
  ▼
Answer + source metadata
```

## Architectural Principles

1. Keep the ML layer independent from the HTTP layer.
2. Preserve page boundaries throughout extraction and chunking.
3. Do not allow answers to be invented when evidence is weak or missing.
4. Use a retrieval layer to reduce context size before QA.
5. Keep the backend portable and deployable on a Python runtime suitable for PyTorch inference.
6. Keep the frontend separate from the ML backend for operational clarity.

## Proposed Repository Structure

```text
BookWorm/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── ml/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── alembic/ (optional later)
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── public/
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── DECISIONS.md
│   ├── PHASE_STATUS.md
│   └── evaluation/
├── .env.example
├── .gitignore
├── README.md
└── .github/workflows/
```

## Pipeline Details

### 1. PDF Ingestion

- Validate file extension and MIME type
- Validate PDF magic bytes
- Enforce file size and page count limits
- Save the file to a safe storage directory or object store
- Store a document record with status metadata

### 2. PDF Extraction

- Extract raw text page-by-page
- Preserve page numbers
- Detect extraction failure or low-text-image PDFs
- Store raw and cleaned page text separately

### 3. Cleaning and Normalization

- Remove duplicated whitespace
- Fix hyphenation and broken wrapping
- Drop empty or irrelevant repeated lines
- Keep the original document meaning intact

### 4. Chunking

- Split text into paragraph-aware chunks
- Keep chunk lengths under a configured token budget
- Include overlap between chunks
- Preserve range metadata for page start and end

### 5. Retrieval

- Build a TF-IDF vector space for text chunks
- Retrieve the top-k chunks for a question
- Produce metadata such as chunk id, page range, and retrieval score

### 6. BERT QA

- Load the pretrained question-answering model once
- Run the model on each retrieved chunk
- Gather candidate answers and confidence values
- Rank the strongest answer while enforcing no-answer behavior when confidence is insufficient

### 7. Response Construction

- Return answer text
- Return confidence score
- Return page and evidence
- Return chunk metadata when useful for debugging

## Academic Requirement

This project must clearly demonstrate the distinction between:

- retrieval: locating the most relevant document passages
- BERT QA: extracting the answer span from the selected passage

The final explanation must be understandable in a viva and must not misrepresent the system as a generic chatbot.

## Deployment Considerations

- Frontend should be deployable to Vercel
- Backend should be deployed to a Python runtime capable of PyTorch + Transformers inference
- For production, object storage should be used rather than direct browser-to-API file transfer for large PDFs
- Secrets must remain in environment variables and never be committed to source control

## Current Baseline State

This repository is currently empty. The first milestone is to establish the project baseline, architecture docs, and a phased implementation plan before starting the actual foundation implementation.
