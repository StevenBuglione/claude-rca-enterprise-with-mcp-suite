from __future__ import annotations

import contextlib
from typing import Any, Dict

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from prometheus_client import make_asgi_app

from mcp.server.fastmcp import FastMCP

from mcp_common.auth import BearerAuthMiddleware
from mcp_common.health import live, missing_env
from mcp_common.logging import configure_logging
from mcp_common.result import json_result, text_result

from app.config import settings
from app.client import BitbucketClient

configure_logging(settings.log_level)
mcp = FastMCP("bitbucket", json_response=True)

client = BitbucketClient(
    base_url=settings.base_url,
    api_prefix=settings.api_prefix,
    auth_mode=settings.auth_mode,
    user=settings.user,
    token=settings.token,
    verify_ssl=settings.verify_ssl,
)

async def ready(_request):
    required = ["MCP_AUTH_TOKEN", "BITBUCKET_BASE_URL", "BITBUCKET_TOKEN"]
    if settings.auth_mode.lower() == "basic":
        required.append("BITBUCKET_USER")
    missing = missing_env(*required)
    return JSONResponse({"ok": not missing, "missing": missing})

def repo_base(project_key: str, repo_slug: str) -> str:
    return f"projects/{project_key}/repos/{repo_slug}"

@mcp.tool()
async def bitbucket_get_repo(project_key: str, repo_slug: str):
    return json_result(await client.get_json(repo_base(project_key, repo_slug)))

@mcp.tool()
async def bitbucket_list_commits(project_key: str, repo_slug: str, limit: int = 50, start: int = 0, since: str | None = None, until: str | None = None):
    params: Dict[str, Any] = {"limit": limit, "start": start}
    if since: params["since"] = since
    if until: params["until"] = until
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/commits", params=params))

@mcp.tool()
async def bitbucket_get_commit(project_key: str, repo_slug: str, commit_id: str):
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/commits/{commit_id}"))

@mcp.tool()
async def bitbucket_get_commit_diff(project_key: str, repo_slug: str, commit_id: str, limit: int = 1000):
    # /commits/{commitId}/diff returns unified diff text
    return text_result(await client.get_text(f"{repo_base(project_key, repo_slug)}/commits/{commit_id}/diff", params={"limit": limit}))

@mcp.tool()
async def bitbucket_list_pull_requests(project_key: str, repo_slug: str, state: str = "OPEN", limit: int = 50, start: int = 0):
    params: Dict[str, Any] = {"state": state, "limit": limit, "start": start}
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/pull-requests", params=params))

@mcp.tool()
async def bitbucket_get_pull_request(project_key: str, repo_slug: str, pr_id: int):
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/pull-requests/{pr_id}"))

@mcp.tool()
async def bitbucket_get_pull_request_commits(project_key: str, repo_slug: str, pr_id: int, limit: int = 100, start: int = 0):
    params: Dict[str, Any] = {"limit": limit, "start": start}
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/pull-requests/{pr_id}/commits", params=params))

@mcp.tool()
async def bitbucket_get_pull_request_diff(project_key: str, repo_slug: str, pr_id: int, context_lines: int = 3):
    return text_result(await client.get_text(f"{repo_base(project_key, repo_slug)}/pull-requests/{pr_id}/diff", params={"contextLines": context_lines}))

@mcp.tool()
async def bitbucket_get_file_raw(project_key: str, repo_slug: str, file_path: str, at: str | None = None):
    # Bitbucket DC raw endpoint: /raw/{path}?at=<ref>
    params: Dict[str, Any] = {}
    if at: params["at"] = at
    return text_result(await client.get_text(f"{repo_base(project_key, repo_slug)}/raw/{file_path.lstrip('/')}", params=params))

@mcp.tool()
async def bitbucket_list_branches(project_key: str, repo_slug: str, limit: int = 50, start: int = 0, filter_text: str | None = None):
    params: Dict[str, Any] = {"limit": limit, "start": start}
    if filter_text: params["filterText"] = filter_text
    return json_result(await client.get_json(f"{repo_base(project_key, repo_slug)}/branches", params=params))

@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield

metrics_app = make_asgi_app()
app = Starlette(
    routes=[
        Route("/health/live", live, methods=["GET"]),
        Route("/health/ready", ready, methods=["GET"]),
        Mount("/metrics", app=metrics_app),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    middleware=[Middleware(BearerAuthMiddleware)],
    lifespan=lifespan,
)

def main():
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())

if __name__ == "__main__":
    main()
