"""Runs one extraction job to completion, reporting progress and the final
result (or error) into the job store.

Docling's extract_text is blocking/CPU-bound; it runs via asyncio.to_thread
so parsing one PDF doesn't stall every other client's SSE stream on this
single-worker process. build_graph's on_progress callback fires
synchronously from inside the same event loop it's awaited from, so pushing
into the job's queue from that callback needs no thread-safety bridging.
"""

import asyncio

from src.extraction.factory import create_extractor
from src.ingestion import extract_text
from src.pipeline import build_graph

from backend.jobs.store import store


async def run_job(job_id: str, *, text: str | None, file_bytes: bytes | None, filename: str | None, provider: str, model: str) -> None:
    try:
        resolved_text = text or ""
        if file_bytes is not None:
            resolved_text = await asyncio.to_thread(extract_text, file_bytes, filename or "upload")

        if not resolved_text.strip():
            store.mark_error(job_id, "No text found: upload a document or paste some text.")
            return

        extractor = create_extractor(provider, model)

        def on_progress(done: int, total: int) -> None:
            store.mark_progress(job_id, done, total)

        graph = await build_graph(resolved_text, extractor, on_progress=on_progress)
        store.mark_complete(job_id, graph)
    except Exception as exc:
        store.mark_error(job_id, str(exc))
