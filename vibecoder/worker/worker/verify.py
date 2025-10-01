from __future__ import annotations

import time
from typing import Sequence

import httpx

PATHS: Sequence[str] = ("/", "/api/health")


def run_smoke_tests(base_url: str, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        all_ok = True
        for path in PATHS:
            try:
                url = base_url.rstrip("/") + path
                resp = httpx.get(url, timeout=5.0)
                if resp.status_code != 200:
                    all_ok = False
            except Exception:
                all_ok = False
        if all_ok:
            return True
        time.sleep(2)
    return False
