"""FastAPI app: wraps the existing src/ pipeline as an HTTP API, and (once
built) serves the React frontend from the same origin so the browser never
needs CORS in production."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import rate_limit
from backend.config import dev_cors_origin
from backend.jobs.store import store
from backend.routers import jobs, providers

load_dotenv()

_CLEANUP_INTERVAL_SECONDS = 600  # 10 minutes
_STALE_AFTER_SECONDS = 3600  # 1 hour


async def _periodic_cleanup() -> None:
    # Both the job store and the rate limiter's per-IP entries grow
    # unbounded otherwise - this is the only thing that ever removes them.
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        store.purge_older_than(_STALE_AFTER_SECONDS)
        rate_limit.purge_stale(_STALE_AFTER_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    cleanup_task = asyncio.create_task(_periodic_cleanup())
    yield
    cleanup_task.cancel()


app = FastAPI(title="InkMap API", lifespan=lifespan)

dev_origin = dev_cors_origin()
if dev_origin:
    app.add_middleware(CORSMiddleware, allow_origins=[dev_origin], allow_methods=["*"], allow_headers=["*"])

app.include_router(providers.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
