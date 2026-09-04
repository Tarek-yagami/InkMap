"""In-memory job store for tracking async extraction jobs.

Single-process only: the job dict lives in this process's memory, so the
server must run with exactly one uvicorn worker (the default, and the only
option - never add --workers without adding a shared store first, since
each worker would otherwise have its own empty dict and every job lookup
from a different worker would 404).
"""

import time
import uuid
from asyncio import Queue
from dataclasses import dataclass, field

from src.schema import KnowledgeGraph

# Queue items: ("progress", done, total) | ("complete", None, None) | ("error", None, None)
QueueEvent = tuple[str, int | None, int | None]


@dataclass
class Job:
    id: str
    status: str = "running"  # "running" | "complete" | "error"
    done: int = 0
    total: int = 0
    result: KnowledgeGraph | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    queue: "Queue[QueueEvent]" = field(default_factory=Queue)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self) -> Job:
        job = Job(id=str(uuid.uuid4()))
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def mark_progress(self, job_id: str, done: int, total: int) -> None:
        job = self._jobs[job_id]
        job.done, job.total = done, total
        job.queue.put_nowait(("progress", done, total))

    def mark_complete(self, job_id: str, result: KnowledgeGraph) -> None:
        job = self._jobs[job_id]
        job.status, job.result = "complete", result
        job.queue.put_nowait(("complete", None, None))

    def mark_error(self, job_id: str, message: str) -> None:
        job = self._jobs[job_id]
        job.status, job.error = "error", message
        job.queue.put_nowait(("error", None, None))

    def purge_older_than(self, seconds: float) -> None:
        cutoff = time.time() - seconds
        stale = [job_id for job_id, job in self._jobs.items() if job.created_at < cutoff]
        for job_id in stale:
            del self._jobs[job_id]


store = JobStore()
