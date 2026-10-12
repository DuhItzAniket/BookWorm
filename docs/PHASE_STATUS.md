# Phase status

Updated 2026-10-12. The earlier notes incorrectly described this repository as empty after ingestion code had already landed. The revised plan supersedes those notes.

| Phase | Status | Evidence |
|---|---|---|
| 0: Analysis and revised plan | Complete | Existing upload/frontend code inspected; Vercel official function limits retrieved; scope and gates in IMPLEMENTATION_PLAN.md |
| 1: Backend vertical slice | Complete | 17 offline tests passed; actual pretrained BERT extracted the correct school from the supplied sample |
| 1B: Glypharis integration preparation | Complete, real-model integration pending upstream | 24 offline tests passed; optional adapter, PDF routing, provenance and integration contract |
| 2: Reading-room interface | In verification | Responsive interface implemented; production build and browser checks pending |
| 3: Reproducibility and release | In progress | Evaluation and deployment documentation pending |

## Phase 0 SDLC record

Requirements: document chatbot, required SQuAD-style BERT, optional internet search, Vercel frontend, polished interface, reproducible academic project.

Analysis: existing ingestion and UI were present; retrieval and QA were missing. Chunk overlap was configured but not implemented. EPUB paths used OS separators, and archive entry order ignored the spine. Global Python dependencies were inconsistent; the existing project virtual environment is usable. NVIDIA RTX 4050 is present; installed PyTorch is CPU-only.

Design: protected shared-library demo; exact-span BERT reader; separate document/web modes; Vercel frontend plus persistent Python backend. Official Vercel documentation currently lists a 500 MB uncompressed Python bundle limit and 4.5 MB function payload limit. Direct backend uploads avoid that frontend limit.

Validation: repository inspection and official documentation retrieval completed. No deployed system is claimed.

Risks: real model download/startup, search-provider credentials, hosting costs and persistent disk availability. Test these explicitly and retain honest limitations.

## Phase 1 SDLC record

Requirements: genuine SQuAD-style BERT answering with sources, upload format validation, reliable failure behavior, and an explicit open-domain path.

Implementation: 320-token windows with 64-token overlap; TF-IDF bigram retrieval; top-five BERT passage reading; null-span rejection and minimum score threshold; exact-span output validation; evidence offsets and page metadata. Web mode reads Brave Search snippets with URLs. Ingestion rejects unreadable/scanned documents and oversized archive expansion, honors EPUB spine order and uses platform-independent archive paths. Database ingestion commits atomically. Production requires a shared demo token.

Verification: `python -m pytest tests -q` from backend: 17 passed. Tests isolate SQLite/storage and use clearly identified fake reader/tokenizer dependencies. Separately, the actual `deepset/bert-base-cased-squad2` model on CPU answered ?Where does Harry study?? with ?Hogwarts School of Witchcraft and Wizardry? and correct source offsets. Installed torch 2.14.1+cpu and transformers 5.18.0 were used. One test-client deprecation warning is non-failing.

Limitations: no live Brave key supplied, so external search has not been verified end to end. Non-PDF formats use one text section rather than physical page numbers. First QA request downloads/loads the model and builds persisted chunks. This is a single-library demo; the shared token does not isolate individual users. Model scores are uncalibrated and extracted answers may still be incorrect.

## Phase 1B SDLC record (2026-10-12)

Requirement change: prepare BookWorm for the owner's independent Glypharis OCR project while that project continues development.

Analysis: reviewed upstream commit `7cb784d471dabe0efcf495a3b397f9110429c8af`, including README, architecture, roadmap, integration phases, package exports and ADR-0008. It reports data audit, no trained model, a planned Python API, and CPU-first inference. No changes were made to Glypharis.

Design/implementation: optional lazy Python adapter behind an internal protocol; bounded image-page rendering; mixed-PDF detection; output validation; atomic OCR provenance in an additive table; exact PDF page attribution. BERT checkpoint revision is now pinned. Disabled by default, with clear failures when the planned package is unavailable. See [integration contract](GLYPHARIS_INTEGRATION.md).

Validation: 24 backend tests passed, including seven new contract/integration tests for mixed PDFs, disabled or missing OCR, invalid scores, pixel/page limits, temporary-image cleanup and OCR provenance in answers. These use fake OCR output, not a trained model. Existing native ingestion and QA regressions pass.

Release gate: actual Glypharis v0.1 installation, coordinate/API compatibility, performance/quality measurements and deployment acceptance remain pending its upstream release. No OCR accuracy or successful real-model integration is claimed.
