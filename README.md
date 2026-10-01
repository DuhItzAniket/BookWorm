# BookWorm

BookWorm is a document question-answering application built around a PDF ingestion pipeline, retrieval layer, and pretrained BERT extractive QA model. The project follows the academic architecture required for a document QA system: extract text from a PDF, split it into chunks, retrieve the most relevant passages, and run BERT to answer the question using only evidence from the uploaded document.

## Overview

The system allows a user to:

- upload a PDF document
- wait while the document is processed
- inspect processing progress
- ask questions in natural language
- receive grounded answers with source page and evidence
- view question history for the active document
- upload a new document and begin a new session

## Problem Statement

Large books and documents cannot be passed directly into a BERT model as one long context. A practical solution is to retrieve the most relevant passages and then ask BERT to extract an answer span from those passages. This creates a retrieval + extractive QA system that is explainable, document-grounded, and suitable for academic evaluation.

## Architecture Summary

- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI + Python
- ML layer: Hugging Face Transformers, PyTorch, scikit-learn
- Persistence: SQLAlchemy with SQLite in development
- PDF processing: PyMuPDF / pypdf-compatible extraction pipeline
- Retrieval: TF-IDF + cosine similarity
- QA model: BERT-family extractive QA model

## Core ML Pipeline

1. Upload a PDF
2. Extract text while preserving page boundaries
3. Clean and normalize extracted text
4. Chunk the document with token-aware limits and overlap
5. Build a TF-IDF index over document chunks
6. Retrieve the top-k related passages for a question
7. Run a pretrained BERT QA model on each candidate passage
8. Rank candidates and return the strongest grounded answer
9. Show the answer, confidence, page, and evidence snippet

## BERT QA Explanation

BERT is retained as the core answering model. The retrieval layer exists only to make the document manageable for BERT. This follows the academic requirement for a SQuAD-style extractive QA system: the model does not invent answers, and it operates on retrieved evidence from the uploaded document.

## Project Status

This repository is being developed in phases. The current baseline establishes the repository, the architecture, the decision log, and the implementation roadmap.

## Repository Layout

```text
BookWorm/
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
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
└── ...
```

## Local Setup

See the development guide in the docs folder for the project workflow and environment setup.

## Testing

Backend tests will be added incrementally by phase. The project will use pytest for Python verification.

## Deployment

The frontend is intended for Vercel deployment, while the Python ML backend is designed to run in a suitable Python hosting environment where BERT and PyTorch inference are supported reliably.

## Limitations

- The initial phase is a clean project baseline and implementation plan, not a full end-to-end app
- OCR for scanned PDFs is deferred until the core PDF + retrieval + QA pipeline is working reliably
- Full production deployment will depend on cloud credentials and hosting decisions later in the project

## Academic Relevance

This project is designed to demonstrate a practical question-answering system using retriever + BERT extractive QA, with clear source attribution and evidence grounded in the uploaded document.
