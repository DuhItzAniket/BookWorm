# Development and verification

## Prerequisites

Python 3.11, Node.js 22+, npm and Git. The recorded local environment uses Windows and CPU PyTorch. A GPU is optional. Keep this environment separate from Glypharis's training environment.

From the repository root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item .env.example backend/.env
cd backend
..\.venv\Scripts\python.exe -m scripts.warm_model
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

On Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cp .env.example backend/.env
cd backend
../.venv/bin/python -m scripts.warm_model
../.venv/bin/python -m uvicorn app.main:app --reload
```

Run the backend from `backend/`: `.env` and relative database paths resolve from that working directory. The root template is not loaded automatically. The first warmup needs outbound Hugging Face access. `requirements.txt` lists direct pinned dependencies; `requirements.lock.txt` records the complete tested environment. The CPU Docker image has also been built and tested on Linux; see the deployment guide for the recorded scope and fresh-host checks.

In a separate terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

On Linux/macOS use `cp` and `npm`. Open <http://localhost:3000>; FastAPI docs are at <http://127.0.0.1:8000/docs>. Windows uses `npm.cmd` here because PowerShell may block the `npm.ps1` shim. No global execution-policy change is required.

## Configuration

See the [backend template](../.env.example) and [frontend template](../frontend/.env.example). Local demo auth is optional. Production requires a random `DEMO_ACCESS_TOKEN`; users enter it in the connection panel. It is not an individual-user login. Search requires a server-side Brave key. OCR stays disabled pending [Glypharis integration acceptance](GLYPHARIS_INTEGRATION.md).

`QA_MODEL_NAME` and `QA_MODEL_REVISION` must identify a compatible BERT SQuAD 2.0 checkpoint. They are not a supported arbitrary-model selector. Changing tokenizer/model requires rebuilding persisted chunks with a deliberate migration. Do not delete the existing user's database to achieve this.

## Validation

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests -q
..\.venv\Scripts\python.exe -m pip check
..\.venv\Scripts\python.exe -m scripts.evaluate
cd ../frontend
npm.cmd run lint
npm.cmd run build
npm.cmd audit --omit=dev
```

Offline tests isolate storage and substitute explicit fake reader/tokenizer/OCR dependencies. For a lightweight test environment, install `backend/requirements-test.txt`. The real-model evaluation is separate and downloads/loads the pinned BERT checkpoint. See [evaluation methodology](evaluation/README.md) before interpreting the numbers.

CI runs offline backend tests, frontend lint/build and a production-dependency audit on pushes and PRs. It does not run Glypharis training, a real search query, or BERT quality benchmarks. Browser verification should upload [demo.txt](evaluation/demo.txt), ask “Where does Harry Potter study?”, inspect the highlighted answer, switch documents, and check mobile/error states.

For a running protected backend, set `BOOKWORM_SMOKE_TOKEN` in your shell and run `python -m scripts.smoke_api --url https://YOUR-BACKEND` from `backend/`. This creates a small `bookworm-smoke.txt` document and verifies health, token enforcement, actual QA and evidence offsets. Use a staging library, and never commit the token. The command exits nonzero on failure.

## Optional GPU

The inspected laptop has an RTX 4050; the existing PyTorch install is CPU-only. CPU inference has been verified. To use CUDA later, create a separate environment and install the appropriate wheel using the current [PyTorch installation selector](https://pytorch.org/get-started/locally/), then verify `python -c "import torch; print(torch.cuda.is_available())"` before setting `QA_DEVICE=cuda`. Do not assume the driver version alone proves PyTorch GPU support. Leave BookWorm on CPU while Glypharis uses the laptop GPU for training.

## Git and release workflow

Use a tested checkpoint commit per completed phase, update [phase status](PHASE_STATUS.md), and push without rewriting earlier checkpoints. Avoid secrets, uploads, local databases, cached weights and generated build files in commits. Inspect both staged diff and test output. Frontend production builds must finish before starting `next start`; rebuilding while serving an older build can create misleading chunk-404 errors.

See the [Vercel guide](VERCEL_GUIDE.md) for hosted configuration, disk persistence, rollback and deployment acceptance checks.
