import asyncio

import pytest

from app import cache
from app.cache import AsyncTTLCache, CallBudget
from app.errors import UpstreamRateLimited


# --- CallBudget (the upstream budget guard) ----------------------------------

def test_budget_refuses_over_the_limit_and_recovers_after_60_s(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: now[0])
    budget = CallBudget(per_minute=2)

    budget.take()
    budget.take()
    with pytest.raises(UpstreamRateLimited) as exc:
        budget.take()
    assert 1 <= exc.value.retry_after_s <= 61

    now[0] += 60  # the two earlier calls fall out of the window
    budget.take()


# --- AsyncTTLCache (in-flight dedup) -----------------------------------------

async def test_concurrent_callers_share_one_fetch():
    c = AsyncTTLCache(ttl_s=60, maxsize=10)
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return {"value": 1}

    a, b, d = await asyncio.gather(c.get("k", fetch), c.get("k", fetch), c.get("k", fetch))
    assert calls == 1
    assert a is b is d
    assert await c.get("k", fetch) is a  # now served from the cache
    assert calls == 1


async def test_failed_fetch_is_not_cached():
    c = AsyncTTLCache(ttl_s=60, maxsize=10)
    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise UpstreamRateLimited("busy", retry_after_s=5)
        return "ok"

    with pytest.raises(UpstreamRateLimited):
        await c.get("k", flaky)
    assert await c.get("k", flaky) == "ok"
    assert attempts == 2
