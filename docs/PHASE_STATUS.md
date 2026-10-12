# Phase status

Updated 2026-10-12. The earlier notes incorrectly described this repository as empty after ingestion code had already landed. The revised plan supersedes those notes.

| Phase | Status | Evidence |
|---|---|---|
| 0: Analysis and revised plan | Complete | Existing upload/frontend code inspected; Vercel official function limits retrieved; scope and gates in IMPLEMENTATION_PLAN.md |
| 1: Backend vertical slice | Complete | 17 offline tests passed; actual pretrained BERT extracted the correct school from the supplied sample |
| 1B: Glypharis integration preparation | Complete, real-model integration pending upstream | 24 offline tests passed; optional adapter, PDF routing, provenance and integration contract |
| 2: Reading-room interface | Complete | Lint/build pass; real upload-to-BERT answer, abstention, desktop/mobile inspection |
| 3: Reproducibility and release | Complete locally; cloud acceptance remains user-operated | Docker build/API/persistence and 24 Linux tests pass; frontend lint/build pass; CI and guides packaged |

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

## Phase 2 SDLC record (2026-10-12)

Requirements: a tailored reading-room interface with document library, chat, evidence, separate web mode and responsive design.

Implementation: warm paper/green palette, serif reading typography, custom book illustration, library selection, bounded upload, per-document in-memory conversation, exact-span evidence highlighting, no-answer state, loading/error states, shared-token connection panel and OCR provenance notice. Next.js upgraded to 16.3.8/React 19.3.0; unused Tailwind configuration removed. Connection loading has effect cleanup and handles invalid server responses. No external fonts or generated illustration assets are required.

Validation: `npm run lint` and `npm run build` passed. Playwright uploaded the sample through the actual UI and obtained “Hogwarts School of Witchcraft and Wizardry” from the real BERT API with highlighted evidence. An unanswerable library question returned no answer. Desktop 1440×1000 and mobile 390×844 screenshots inspected; mobile document width equals viewport width. Browser console reported zero errors/warnings. Web button is disabled without a provider key. Production dependency audit: zero vulnerabilities.

Limitations: real Brave requests need a key; history lasts only in the current tab; the library is shared by token holders. Full dependency audit still reports five dev-only findings in the Next ESLint plugin's glob/braces chain; production dependencies are unaffected. These are disclosed, not suppressed by a forced framework downgrade.

## Phase 3 SDLC record (2026-10-12)

Requirements: reproducible setup, honest academic evaluation, deployment feasibility and detailed Vercel guide, regression checks and release checkpoints.

Implementation: pinned direct/complete Python requirements, CPU Docker image with non-root user and persistent disk paths, model cache warmup, lightweight CI requirements, GitHub Actions backend/frontend checks, real API smoke command, BERT evaluation harness/results, revised README/development/architecture/decisions, and step-by-step Vercel guide. The evaluation now records model revision, dataset hash, environment and timestamp. Frontend evidence highlighting accounts for Python Unicode code-point offsets, including non-BMP characters. Environment override files are ignored to prevent accidental secret commits.

Validation: Windows tests: 24 passed; Linux Docker tests: 24 passed; pip dependency checks pass. Docker image builds successfully, loads the pinned BERT on CPU from a read-only offline cache, rejects unauthenticated library access, accepts an upload, and answers with correct source offsets. A restart retains the document on the named disk. Frontend lint, TypeScript and final production build pass. Real BERT sanity evaluation: 6/6 normalized EM and F1, explicitly not a benchmark. Desktop/mobile browser flow verified in Phase 2. Production npm audit has zero findings; five development-only transitive findings remain documented above.

Operational limits: no paid service provisioned; no public cloud deployment asserted; fresh-host model download and real Brave queries still require deployment acceptance. Glypharis's trained engine and licence are pending upstream. Authentication is a shared library token, not individual accounts. Synchronous OCR is capped at five pages and has no hard inference cancellation. See [Vercel guide](VERCEL_GUIDE.md), [OCR gate](GLYPHARIS_INTEGRATION.md) and [evaluation plan](evaluation/README.md).

Checkpoint history: plan `b785bb2`, backend `6013219`, OCR preparation `21d0885`, interface `0d497a0`. The release commit that contains this record is the next checkpoint; Git history is authoritative.
