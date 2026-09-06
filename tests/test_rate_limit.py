import time

import pytest

from backend import rate_limit


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    # Module-level state shared across the whole test run - reset before
    # each test so one test's usage doesn't count against another's limit.
    rate_limit._limiters.clear()
    rate_limit._last_seen.clear()
    yield


async def test_allows_requests_up_to_the_limit_then_rejects():
    results = [await rate_limit.check_and_record("1.2.3.4") for _ in range(rate_limit._MAX_JOBS_PER_WINDOW + 2)]
    assert results == [True] * rate_limit._MAX_JOBS_PER_WINDOW + [False, False]


async def test_different_ips_have_independent_limits():
    for _ in range(rate_limit._MAX_JOBS_PER_WINDOW):
        assert await rate_limit.check_and_record("1.1.1.1")
    assert not await rate_limit.check_and_record("1.1.1.1")
    assert await rate_limit.check_and_record("2.2.2.2")


async def test_purge_stale_removes_old_entries_but_not_recent_ones():
    await rate_limit.check_and_record("old-ip")
    rate_limit._last_seen["old-ip"] = time.time() - 999
    await rate_limit.check_and_record("recent-ip")

    rate_limit.purge_stale(seconds=100)

    assert "old-ip" not in rate_limit._limiters
    assert "recent-ip" in rate_limit._limiters
