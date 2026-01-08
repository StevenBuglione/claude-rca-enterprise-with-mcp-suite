from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import httpx

@dataclass(frozen=True)
class HttpConfig:
    base_url: str
    verify_ssl: bool = True
    timeout_s: float = 30.0
    max_retries: int = 2

def join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")

async def with_retries(fn, max_retries: int = 2):
    last = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
            last = e
            if attempt >= max_retries:
                raise
            await asyncio.sleep(0.4 * (2 ** attempt))
    if last is None:  # pragma: no cover
        raise RuntimeError("Retry loop failed without an exception.")
    raise last  # pragma: no cover

async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    resp = await client.request(method, url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()

async def request_text(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[str, httpx.Response]:
    resp = await client.request(method, url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.text, resp
