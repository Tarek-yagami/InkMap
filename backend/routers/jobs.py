"""Job lifecycle: start an extraction, stream its progress, or poll its
status. The task returned by asyncio.create_task is kept in a module-level
set with a done_callback that discards it - an unreferenced fire-and-forget
task can otherwise be garbage-collected mid-run ("Task was destroyed but it
is pending")."""

import asyncio
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.jobs.runner import run_job
from backend.jobs.store import store
from backend.schemas import JobStatusResponse

router = APIRouter()

_background_tasks: set[asyncio.Task] = set()


@router.post("/jobs", status_code=202)
async def start_job(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    provider: str = Form(...),
    model: str = Form(...),
) -> dict[str, str]:
    if file is None and not (text or "").strip():
        raise HTTPException(400, "Upload a document or paste some text first.")

    file_bytes = await file.read() if file is not None else None
    filename = file.filename if file is not None else None

    job = store.create()
    task = asyncio.create_task(
        run_job(job.id, text=text, file_bytes=file_bytes, filename=filename, provider=provider, model=model)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"job_id": job.id}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> JobStatusResponse:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(404, "Unknown job id.")
    return JobStatusResponse(
        id=job.id,
        status=job.status,
        done=job.done,
        total=job.total,
        result=job.result.model_dump() if job.result else None,
        error=job.error,
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str) -> StreamingResponse:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(404, "Unknown job id.")

    async def event_stream():
        if job.status == "complete":
            yield f"event: complete\ndata: {job.result.model_dump_json()}\n\n"
            return
        if job.status == "error":
            yield f"event: error\ndata: {json.dumps({'message': job.error})}\n\n"
            return

        # No separate "current state" snapshot here: the queue already holds
        # every progress event since job creation (nothing drains it until a
        # stream connects), so replaying it from the start is already
        # complete and in order. Emitting a snapshot too would duplicate
        # whatever's still queued, making the bar jump forward then backward.
        while True:
            try:
                kind, done, total = await asyncio.wait_for(job.queue.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
                continue

            if kind == "progress":
                yield f"event: progress\ndata: {json.dumps({'done': done, 'total': total})}\n\n"
            elif kind == "complete":
                yield f"event: complete\ndata: {job.result.model_dump_json()}\n\n"
                return
            elif kind == "error":
                yield f"event: error\ndata: {json.dumps({'message': job.error})}\n\n"
                return

    return StreamingResponse(event_stream(), media_type="text/event-stream")
