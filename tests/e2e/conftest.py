import os
import time

import httpx
import pytest

BASE_URL = os.environ.get("SDL_GATEWAY_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def http():
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        yield client


def eventually(fn, timeout: float = 30, interval: float = 0.5):
    """Retry an assertion until it passes — for eventually-consistent flows (replicas, streams, caches)."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return fn()
        except AssertionError:
            if time.monotonic() > deadline:
                raise
            time.sleep(interval)
