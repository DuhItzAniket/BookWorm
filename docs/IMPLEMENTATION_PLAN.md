# Implementation plan and SDLC

## Requirements and scope

BookWorm is an academic, English-language question-answering application. The mandatory baseline is a pretrained **BERT** reader fine-tuned on SQuAD 2.0, operating on retrieved document passages. The website runs on Vercel; inference and persistent storage run on an external Python service. A web-search switch implements an optional open-domain retrieval path. This release is a protected, shared-library demo, not a multi-tenant SaaS.

Supported inputs: text PDFs, DOCX, EPUB, TXT, Markdown, CSV and HTML. Legacy DOC/RTF require conversion. Images and scanned PDFs require external OCR. Never promise arbitrary file support.

## Design decisions

- Default reader: `deepset/bert-base-cased-squad2`, genuine BERT with a no-answer objective. Retain exact text offsets and show supporting passages.
- TF-IDF baseline, token-window overlap, top-five retrieval. These are interpretable and affordable; dense retrieval is an evaluated extension, not a prerequisite.
- Describe this accurately as retrieval-augmented **extractive QA**. It is not a generative RAG system and does not summarize a whole book or resolve conversational references.
- Web mode uses Brave Search excerpts and URLs, then the same reader. It never silently combines uploaded text and web results. Only the question leaves for the search provider.
- Vercel serves Next.js. Browser uploads directly to FastAPI over HTTPS, bypassing Vercel function payload limits. Use persistent disk plus SQLite for a single process demo.
- One shared demo token protects all library operations. Public multi-user use requires user authentication, per-document ownership, quotas and storage redesign.
- RoBERTa and ALBERT are future controlled extractive-reader comparisons; T5 is a future generative baseline. GPT-2 is not instruction-tuned QA, and GPT-3 is a hosted model family, not a free local checkpoint. Do not add model switches with untested implementations.

## Delivery checkpoints

Each completed phase must include requirements/design notes, implementation, verification, limitations, and a separate Git commit pushed to the existing GitHub branch. No fabricated test results or automatic paid provisioning.

| Phase | Deliverable | Acceptance gate |
|---|---|---|
| 0. Analysis and revised design | This plan; deployment feasibility; corrected scope | Existing source/docs inspected, official Vercel limits checked |
| 1. Backend vertical slice | Ingestion fixes, overlapping chunks, retrieval, BERT, web adapter, access guard | Offline regression/API tests; real-model smoke test separately |
| 2. Reading-room interface | Responsive library, uploader, chat history, source excerpts, web mode, errors | Production build, type checks, browser interaction and responsive inspection |
| 3. Reproducibility and release | SDLC records, evaluation harness, Docker, CI, setup and Vercel guide | Full test/build gates, real QA evaluation recorded, dependency/security checks |

## Validation strategy

Offline tests use an explicit test-only reader/tokenizer so CI neither downloads a large model nor claims to evaluate BERT. A separate real-model smoke/evaluation runs the actual checkpoint, with exact-match/F1 and abstention results clearly identified as a tiny synthetic sanity set. Document upload, negative inputs, source offsets, retrieval, authentication and web provider failure are testable independently. UI checks cover desktop/mobile, empty/error states and the complete upload-to-answer flow.

## Remaining research / production work

1. Build a held-out, legally usable question set with answerable and unanswerable examples; measure retrieval recall@k, EM/F1, abstention and latency. Tune thresholds only on development data.
2. Compare TF-IDF with a sentence-transformer retriever on that same split, before introducing a vector database.
3. Compare BERT with QA-fine-tuned RoBERTa/ALBERT under identical retrieval conditions. Evaluate T5 generation separately for grounding and factual errors.
4. For many users: authentication/ownership, per-user rate limits, object storage, PostgreSQL, queue/worker ingestion, retention/deletion and observability.
5. OCR and sophisticated table/layout extraction need separate acceptance tests.

## Change management

A checkpoint commit records a tested state; Git history is the authoritative version record. Deployment remains a user-operated step documented in the Vercel guide. A successful local build is not proof of a live deployment. Never mark external-service verification complete without credentials and a successful request.
