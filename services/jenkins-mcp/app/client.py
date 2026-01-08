from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from mcp_common.http import join_url, request_json, request_text, with_retries

class JenkinsClient:
    def __init__(self, base_url: str, user: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.auth = (user, token)
        self.verify_ssl = verify_ssl

    def _job_path(self, job_full_name: str) -> str:
        # job_full_name like "folder1/folder2/jobname"
        parts = [p for p in job_full_name.strip("/").split("/") if p]
        path = ""
        for p in parts:
            path += f"/job/{p}"
        return path or ""

    def job_api(self, job_full_name: str) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + "/api/json")

    def build_api(self, job_full_name: str, build_number: int) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + f"/{build_number}/api/json")

    def config_xml(self, job_full_name: str) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + "/config.xml")

    def progressive_text(self, job_full_name: str, build_number: int) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + f"/{build_number}/logText/progressiveText")

    def test_report(self, job_full_name: str, build_number: int) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + f"/{build_number}/testReport/api/json")

    def wfapi(self, job_full_name: str, build_number: int, endpoint: str) -> str:
        return join_url(self.base_url, self._job_path(job_full_name) + f"/{build_number}/wfapi/{endpoint.lstrip('/')}")

    async def get_job(self, job_full_name: str, tree: Optional[str] = None, depth: Optional[int] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            params: Dict[str, Any] = {}
            if tree: params["tree"] = tree
            if depth is not None: params["depth"] = depth
            return await with_retries(lambda: request_json(client, "GET", self.job_api(job_full_name), params=params), 2)

    async def get_build(self, job_full_name: str, build_number: int, tree: Optional[str] = None, depth: Optional[int] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            params: Dict[str, Any] = {}
            if tree: params["tree"] = tree
            if depth is not None: params["depth"] = depth
            return await with_retries(lambda: request_json(client, "GET", self.build_api(job_full_name, build_number), params=params), 2)

    async def get_config_xml(self, job_full_name: str) -> str:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            text, _ = await with_retries(lambda: request_text(client, "GET", self.config_xml(job_full_name)), 2)
            return text

    async def get_console_chunk(self, job_full_name: str, build_number: int, start: int = 0) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=60.0) as client:
            async def _call():
                return await request_text(client, "GET", self.progressive_text(job_full_name, build_number), params={"start": str(start)})
            text, resp = await with_retries(_call, 2)
            # Jenkins progressiveText uses X-Text-Size and X-More-Data to page through logs.
            next_start = int(resp.headers.get("X-Text-Size", str(start)))
            has_more = resp.headers.get("X-More-Data", "false").lower() == "true"
            return {"text": text, "start": start, "next_start": next_start, "has_more": has_more}

    async def get_test_report(self, job_full_name: str, build_number: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=60.0) as client:
            return await with_retries(lambda: request_json(client, "GET", self.test_report(job_full_name, build_number)), 2)

    async def wfapi_describe(self, job_full_name: str, build_number: int, full_stages: bool = False) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            return await with_retries(
                lambda: request_json(client, "GET", self.wfapi(job_full_name, build_number, "describe"), params={"fullStages": str(full_stages).lower()}),
                2,
            )

    async def wfapi_changesets(self, job_full_name: str, build_number: int) -> Any:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            return await with_retries(lambda: request_json(client, "GET", self.wfapi(job_full_name, build_number, "changesets")), 2)

    async def wfapi_artifacts(self, job_full_name: str, build_number: int) -> Any:
        async with httpx.AsyncClient(verify=self.verify_ssl, auth=self.auth, timeout=30.0) as client:
            return await with_retries(lambda: request_json(client, "GET", self.wfapi(job_full_name, build_number, "artifacts")), 2)
