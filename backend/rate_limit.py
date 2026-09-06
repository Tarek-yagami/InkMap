"""Per-IP rate limiting for job creation, reusing aiolimiter (already a
dependency for pacing outgoing LLM calls) rather than adding a new library
for this.

aiolimiter's own `acquire()` waits until capacity frees up - correct for
pacing our own outgoing requests, wrong here: an abusive client should be
rejected immediately (429), not queued. `has_capacity()` is a read-only
check, so it's paired with `acquire()` (confirmed non-blocking immediately
after) to both check and actually consume capacity - calling only
`has_capacity()` would never register any usage, making the limit a no-op.

The module-level dicts persist AsyncLimiter instances for the process's
lifetime, which is only safe bound to one asyncio event loop throughout -
already required anyway (see backend/jobs/store.py) since the job store is
an in-memory dict too, correct only with a single uvicorn worker. Tests
using a sync TestClient can trigger aiolimiter's "reused across loops"
warning since each call may run its own throwaway loop; that's a test-
harness artifact; verified directly (reusing one AsyncLimiter across two
real asyncio.run() calls reproduces the same warning), not a bug reachable
under the single persistent event loop the real deployed server runs on.
"""

import time

from aiolimiter import AsyncLimiter

_MAX_JOBS_PER_WINDOW = 5
_WINDOW_SECONDS = 300  # 5 minutes - generous for real use, restrictive for a script

_limiters: dict[str, AsyncLimiter] = {}
_last_seen: dict[str, float] = {}


async def check_and_record(client_ip: str) -> bool:
    """Returns True if this request is allowed, False if client_ip is over
    its job-creation limit right now."""
    limiter = _limiters.setdefault(client_ip, AsyncLimiter(_MAX_JOBS_PER_WINDOW, _WINDOW_SECONDS))
    _last_seen[client_ip] = time.time()
    if not limiter.has_capacity():
        return False
    await limiter.acquire()
    return True


def purge_stale(seconds: float) -> None:
    cutoff = time.time() - seconds
    stale = [ip for ip, last in _last_seen.items() if last < cutoff]
    for ip in stale:
        _limiters.pop(ip, None)
        _last_seen.pop(ip, None)
