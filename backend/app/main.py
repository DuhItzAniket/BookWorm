from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.security import require_access
from app.api.routes_questions import router as questions_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.core.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment == "production" and not settings.demo_access_token:
        raise RuntimeError("Production requires DEMO_ACCESS_TOKEN for this single-library demo.")
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="BookWorm backend foundation for document question answering.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(documents_router, dependencies=[Depends(require_access)])
app.include_router(questions_router, dependencies=[Depends(require_access)])


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
