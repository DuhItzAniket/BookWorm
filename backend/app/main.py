from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.core.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
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
app.include_router(documents_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
