# BookWorm Development Guide

## Local Workflow

This project will be developed in explicit phases. The foundation phase establishes the repository, the architecture, and the project plan before implementation begins.

## Required Tools

- Python 3.11+
- Node.js 18+
- npm or pnpm
- Git
- pytest

## Repository Setup

```bash
git clone https://github.com/DuhItzAniket/BookWorm.git
cd BookWorm
git checkout -b feature/phase-01-foundation
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy the sample environment file and update values as needed:

```bash
cp .env.example .env
```

## Suggested Phase Sequence

1. Phase 0 — Repository baseline and architecture
2. Phase 1 — Project foundation
3. Phase 2 — PDF ingestion
4. Phase 3 — Text cleaning and chunking
5. Phase 4 — Retrieval
6. Phase 5 — BERT QA
7. Phase 6 — Retrieval + BERT orchestration
8. Phase 7 — FastAPI API
9. Phase 8 — Frontend UX
10. Phase 9 — Integration
11. Phase 10 — Quality and security
12. Phase 11 — Evaluation
13. Phase 12 — Deployment
14. Phase 13 — Final polish

## Testing Expectations

- Backend Python tests with pytest
- API smoke tests for health and document endpoints
- Unit tests for chunking, retrieval, and QA logic
- End-to-end validation of upload → process → ask → answer

## Git Rules

- Use a branch per implementation phase
- Run tests before committing a completed phase
- Update the phase status document after every completed phase
- Commit with meaningful prefixes like feat, fix, test, docs, refactor, chore

## Deployment Guidance

The frontend is planned for Vercel. The ML backend should be hosted on a Python environment suitable for PyTorch and the BERT inference pipeline, rather than forcing the whole AI workload into the frontend runtime.
