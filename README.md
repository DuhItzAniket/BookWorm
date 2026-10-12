# BookWorm

A reading room for your documents: upload a book or paper, ask a question, and inspect the passage behind the answer.

**Next.js frontend + FastAPI + pretrained BERT (SQuAD 2.0) + TF-IDF retrieval.** The interface supports a separate, optional web-search mode with source links. This is an academic, English-language, shared-library demo.

## What works

- PDF, DOCX, EPUB, TXT, Markdown, CSV and HTML ingestion, with size/text/archive limits.
- Overlapping token windows and TF-IDF passage retrieval for long documents.
- Genuine BERT extractive QA using `deepset/bert-base-cased-squad2`, pinned to a checkpoint revision.
- Exact answer spans, source excerpts, PDF page numbers, and no-answer behavior.
- Responsive library/chat UI, document-specific in-memory conversation history, upload/error/loading states.
- Optional Brave Search excerpts as open-domain evidence; uploaded content is not sent to the search provider.
- Protected demo access, offline API tests, real-model sanity evaluation, CI and a Docker deployment recipe.
- Optional Glypharis OCR integration boundary, with bounded PDF rendering and OCR provenance. Disabled until its trained release is validated.

## Run locally

Python 3.11 and Node.js 22+ are recommended. Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item .env.example backend/.env
cd backend
..\.venv\Scripts\python.exe -m scripts.warm_model
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

Open <http://localhost:3000>. The first model download needs internet and several hundred MB of model-cache storage. CPU inference is supported. For Linux/macOS and optional NVIDIA setup, see [Development](docs/DEVELOPMENT.md).

## Deploy on Vercel

**Yes: deploy the frontend to Vercel, and deploy the Python model service separately.** The complete app is not intended to run inside Vercel Functions. Follow the [Vercel deployment guide](docs/VERCEL_GUIDE.md), including backend storage, access token, CORS, environment variables, and smoke tests.

## Read the project

- [Implementation plan and SDLC](docs/IMPLEMENTATION_PLAN.md)
- [Architecture and API](docs/ARCHITECTURE.md)
- [Decisions and tradeoffs](docs/DECISIONS.md)
- [Phase checkpoints and validation](docs/PHASE_STATUS.md)
- [Evaluation method and actual sanity results](docs/evaluation/README.md)
- [Glypharis integration contract and release gate](docs/GLYPHARIS_INTEGRATION.md)

## Honest limitations

This is retrieval-augmented **extractive QA**, not a generative chatbot. It answers specific questions whose answers appear in the evidence; it does not summarize whole books or infer what “he” refers to from previous turns. Scores are uncalibrated, and even exact-span answers can be wrong. English is the supported model language.

Scanned PDFs need a validated Glypharis release; its prepared adapter is disabled by default. Legacy DOC/RTF must be converted. Non-PDF inputs use a text section rather than physical page numbering; tables are flattened. Web mode needs your own Brave Search API key and operates on search excerpts, not fully crawled pages. History lasts for the current tab session. Documents persist on the backend.

Everyone using the demo token shares the same library. Individual accounts, document ownership, rate limits, automatic retention, background job queues, and multi-worker scaling are future work. Do not host sensitive documents in a publicly shared demo. RoBERTa/ALBERT/T5 comparisons are planned experiments, not claimed implemented features.
