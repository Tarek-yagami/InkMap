"""FastAPI app: wraps the existing src/ pipeline as an HTTP API, and (once
built) serves the React frontend from the same origin so the browser never
needs CORS in production."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import dev_cors_origin
from backend.routers import jobs, providers

load_dotenv()

app = FastAPI(title="InkMap API")

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
