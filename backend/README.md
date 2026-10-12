# BookWorm Backend

FastAPI document ingestion, retrieval, BERT QA and optional Glypharis adapter. See [development](../docs/DEVELOPMENT.md), [architecture](../docs/ARCHITECTURE.md), and [deployment](../docs/VERCEL_GUIDE.md) for the complete setup and limitations.

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.lock.txt
uvicorn app.main:app --reload
```
