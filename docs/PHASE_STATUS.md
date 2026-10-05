# Phase status

Updated 2026-10-05. The earlier notes incorrectly described this repository as empty after ingestion code had already landed. The revised plan supersedes those notes.

| Phase | Status | Evidence |
|---|---|---|
| 0: Analysis and revised plan | Complete | Existing upload/frontend code inspected; Vercel official function limits retrieved; scope and gates in IMPLEMENTATION_PLAN.md |
| 1: Backend vertical slice | In verification | 17 offline tests passed; actual BERT model verification underway |
| 2: Reading-room interface | In verification | Responsive interface implemented; production build and browser checks pending |
| 3: Reproducibility and release | In progress | Evaluation and deployment documentation pending |

## Phase 0 SDLC record

Requirements: document chatbot, required SQuAD-style BERT, optional internet search, Vercel frontend, polished interface, reproducible academic project.

Analysis: existing ingestion and UI were present; retrieval and QA were missing. Chunk overlap was configured but not implemented. EPUB paths used OS separators, and archive entry order ignored the spine. Global Python dependencies were inconsistent; the existing project virtual environment is usable. NVIDIA RTX 4050 is present; installed PyTorch is CPU-only.

Design: protected shared-library demo; exact-span BERT reader; separate document/web modes; Vercel frontend plus persistent Python backend. Official Vercel documentation currently lists a 500 MB uncompressed Python bundle limit and 4.5 MB function payload limit. Direct backend uploads avoid that frontend limit.

Validation: repository inspection and official documentation retrieval completed. No deployed system is claimed.

Risks: real model download/startup, search-provider credentials, hosting costs and persistent disk availability. Test these explicitly and retain honest limitations.
