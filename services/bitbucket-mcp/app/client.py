from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from mcp_common.http import join_url, request_json, request_text, with_retries

class BitbucketClient:
    def __init__(self, base_url: str, api_prefix: str, auth_mode: str, user: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix.strip("/")
        self.auth_mode = auth_mode.lower()
        self.user = user
        self.token = token
        self.verify_ssl = verify_ssl

    def _headers(self) -> Dict[str, str]:
        if self.auth_mode == "bearer":
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _auth(self):
        if self.auth_mode == "basic":
            return (self.user, self.token)
        return None

    def _url(self, path: str) -> str:
        return join_url(self.base_url, f"{self.api_prefix}/{path.lstrip('/')}")

    async def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self._auth(), timeout=30.0, headers=self._headers()) as client:
            return await with_retries(lambda: request_json(client, "GET", self._url(path), params=params), 2)

    async def get_text(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self._auth(), timeout=60.0, headers=self._headers()) as client:
            text, _ = await with_retries(lambda: request_text(client, "GET", self._url(path), params=params), 2)
            return text
