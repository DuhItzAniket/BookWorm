# Deploy BookWorm with Vercel

Verified against official documentation on 2026-10-09. This is a deployment recipe; no cloud resources have been provisioned or live deployment verified in this session.

## Recommended topology

- **Vercel:** Next.js frontend, rooted at `frontend/`.
- **Persistent Python host:** FastAPI, CPU PyTorch/BERT, SQLite, uploads and model cache. Use one instance and one worker.
- **Optional Brave Search API:** your own server-side key enables the web-search button.

The browser sends uploads and questions directly to the backend's public HTTPS URL. It does not proxy them through a Vercel Function. Your laptop is not a production backend: `localhost` in a deployed browser means the visitor's own machine.

Vercel can host Python and offers larger-function options. Current standard Python bundles are limited to 500 MB, large functions offer up to 5 GB in beta, and function request bodies remain capped at 4.5 MB. BookWorm's supported 20 MB uploads and persistent local SQLite/files require a different design for an all-Vercel deployment. That alternative would need external database/object storage and direct-to-storage uploads; it is not implemented here. See [Vercel function limits](https://vercel.com/docs/functions/limitations).

## 1. Prepare the Python host

Choose a Linux Docker host with persistent disk and HTTPS. Render is one example; its persistent disks require an eligible paid service. Check the provider's current plans before creating anything. A starting estimate is 2 vCPU, 4 GB RAM, and 5–10 GB disk for a small class demo, then measure memory and latency with your own documents. This is an estimate, not a load-tested capacity guarantee.

For a Render Docker Web Service connected to this GitHub repository:

| Setting | Value |
|---|---|
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | Docker |
| Dockerfile path | `./Dockerfile` |
| Docker build context | `.` |
| Persistent disk mount | `/data` |
| Health check path | `/api/health` |
| Instances | 1 |

The container installs CPU PyTorch, runs as UID 10001, warms the pinned model, then starts Uvicorn on `$PORT`. The mounted disk must be writable by UID 10001. Model warmup needs outbound access to Hugging Face. Startup may take several minutes on an empty cache; allow for this in the host's startup timeout. Persistent disks are available only at runtime on Render, which is why warmup runs on startup. See [Render disks](https://render.com/docs/disks) and [Docker deployment](https://render.com/docs/docker).

Set these **backend** environment variables in the hosting dashboard:

| Variable | Value / purpose |
|---|---|
| `ENVIRONMENT` | `production` |
| `DEMO_ACCESS_TOKEN` | A new random token; required for production startup |
| `CORS_ORIGINS` | Exact Vercel/custom frontend origins, comma-separated, without trailing slashes |
| `DATABASE_URL` | `sqlite:////data/bookworm.db` |
| `UPLOAD_DIR` | `/data/uploads` |
| `HF_HOME` | `/data/huggingface` |
| `QA_DEVICE` | `cpu` |
| `QA_MODEL_NAME` | `deepset/bert-base-cased-squad2` |
| `QA_MODEL_REVISION` | `d378e310c8000d824954c1e76c943a0581b49f0c` |
| `QA_THRESHOLD` | `0.08` initially; tune using development data |
| `TOP_K` | `5` |
| `BRAVE_SEARCH_API_KEY` | Optional; omit or leave empty to disable web search |
| `OCR_PROVIDER` | `disabled` until the Glypharis release passes acceptance |

When Glypharis is released, follow [its integration gate](GLYPHARIS_INTEGRATION.md) before installing a pinned package and setting `GLYPHARIS_MODEL_PATH` plus `OCR_PROVIDER=glypharis`. Its model files belong on the Python host, never the Vercel frontend. CPU is the intended starting point; no GPU hosting or OCR quality is assumed.

Generate a token locally with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Store it privately in the host's secret settings. Users enter it in BookWorm's connection panel. Everyone with this token shares the library; there are no individual user accounts.

For a local Docker rehearsal, from the repository root:

```powershell
docker build -t bookworm-api ./backend
docker volume create bookworm-data
# Supply DEMO_ACCESS_TOKEN via a private backend/.env, not in Git.
docker run --rm -p 8000:8000 --env-file backend/.env -e ENVIRONMENT=production -e DATABASE_URL=sqlite:////data/bookworm.db -e UPLOAD_DIR=/data/uploads -e HF_HOME=/data/huggingface -v bookworm-data:/data bookworm-api
```

The Linux image was built and tested locally on 2026-10-12. All 24 backend tests passed in it, and the protected API passed health/auth/upload/real-BERT/evidence checks. A named `/data` volume retained the uploaded document after container restart. That run mounted the existing Hugging Face cache read-only with offline mode, so a fresh host's first network download remains a deployment acceptance check. Model warmup verifies/downloads the cache in a separate process; the server still loads weights into memory on its first question.

## 2. Import the frontend into Vercel

1. Sign in to Vercel and import `DuhItzAniket/BookWorm` from GitHub.
2. Set **Root Directory** to `frontend` and **Framework Preset** to Next.js.
3. Select Node.js **22.x** (or another supported version that you test). Use `npm ci` for install and `npm run build` for build. Leave the output directory at the Next.js default.
4. Add `NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-HOST` for the Production environment. It is a public URL, with no `/api` suffix or trailing slash. Add a preview-specific URL if you want previews connected.
5. Deploy. Copy the stable production origin, for example `https://your-bookworm.vercel.app`.
6. Update the backend's `CORS_ORIGINS` to include that exact origin and restart/redeploy the backend.
7. Open the website, enter the demo token in **Connect to server**, and run the smoke checks below.

`NEXT_PUBLIC_API_URL` is baked into the browser bundle at build time. Changing it requires a new frontend deployment. Never put the demo token, Brave key, or database credentials in a `NEXT_PUBLIC_*` variable. Official reference: [Next.js on Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs).

Preview URLs have different origins. Explicitly allow a stable preview origin or each intended preview; do not open the backend to every `*.vercel.app` site. Both frontend and backend must use HTTPS on the internet. Add any custom domain as an additional exact CORS origin.

## 3. Enable web search

Create a Brave Search API subscription/key, check its current price and quota, and set `BRAVE_SEARCH_API_KEY` only on the backend. Restart it, then reconnect/reload the frontend so `/capabilities` reflects the change. The web button should become available.

Only the question is sent to Brave. BERT reads returned search snippets; it does not browse entire pages. Live integration has not been tested without a user-supplied key. Validate the provider account with a real query before the project presentation. See [Brave API getting started](https://api-dashboard.search.brave.com/app/documentation/web-search/get-started).

## 4. Deployment acceptance checks

- Open `https://YOUR-BACKEND-HOST/api/health`: expect `status: ok`. This endpoint is liveness, not proof that QA works.
- Request `/documents` without a token: expect HTTP 401.
- Connect through the deployed frontend. Upload a small text PDF containing a fact you know.
- Ask a specific question; verify the answer is highlighted within the correct source and PDF page.
- Ask an unanswerable question. Verify that abstention is possible; no model can guarantee perfect abstention on every example.
- Upload a file above 4.5 MB but below 20 MB. Confirm the browser request goes directly to the backend.
- Restart the backend. Reconnect and verify the uploaded document still exists and is answerable.
- Test phone width, invalid upload, and (if configured) web mode with a source link.
- Check logs and billing dashboards. A CORS error, timeout, or search-provider failure must not be mistaken for a successful deployment.

## Troubleshooting and operations

| Symptom | Check |
|---|---|
| Cannot reach server | Public HTTPS backend URL, network access, exact CORS origin, rebuilt frontend env |
| HTTP 401 | Correct shared token in connection panel; no accidental whitespace |
| HTTP 503 on first question | Backend logs, model download/cache, available RAM, supported PyTorch device |
| Web button disabled | Backend Brave key and refreshed capabilities |
| Provider rate limit | Brave quota/subscription; backend logs show upstream failure |
| Upload disappears after restart | `/data` is not persistent, or database/upload paths point elsewhere |
| Permission denied | Disk ownership/writability for UID 10001 |
| HTTP 413 | Backend proxy upload limit, or accidental Vercel proxying |
| Long first request | Prewarm model; persistent cache; browser timeout is three minutes |

Use one worker/instance with SQLite. Each extra process loads a model copy, and separate instances cannot share this local library safely. Back up the database using SQLite's backup API plus the uploads directory; do not copy an actively written database without a consistent snapshot. Model cache can be downloaded again.

Vercel's frontend firewall does not protect a separately exposed backend. Before opening this to a large audience, add backend request rate limits, a proxy body-size cap, real accounts/document ownership, retention/deletion and monitoring. Current uploaded data is retained until the operator removes it.

## Rollback

The Git commits are the phase checkpoints. To roll back the frontend, redeploy a known-good commit in Vercel. For the backend, redeploy its corresponding commit while preserving `/data`; back up before any future schema or tokenizer migration. This release creates tables automatically but does not include a schema migration system. Document every deploy's commit, URL, date, smoke results and config changes without recording secrets.
