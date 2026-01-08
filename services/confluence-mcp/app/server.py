from __future__ import annotations

import contextlib

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from prometheus_client import make_asgi_app

from mcp.server.fastmcp import FastMCP

from mcp_common.auth import BearerAuthMiddleware
from mcp_common.health import live, missing_env
from mcp_common.logging import configure_logging
from mcp_common.result import json_result

from app.config import settings
from app.client import ConfluenceClient

configure_logging(settings.log_level)
mcp = FastMCP("confluence", json_response=True)

client = ConfluenceClient(
    base_url=settings.base_url,
    api_prefix=settings.api_prefix,
    auth_mode=settings.auth_mode,
    user=settings.user,
    token=settings.token,
    verify_ssl=settings.verify_ssl,
)

async def ready(_request):
    required = ["MCP_AUTH_TOKEN", "CONFLUENCE_BASE_URL", "CONFLUENCE_TOKEN"]
    if settings.auth_mode.lower() == "basic":
        required.append("CONFLUENCE_USER")
    missing = missing_env(*required)
    return JSONResponse({"ok": not missing, "missing": missing})

@mcp.tool()
async def confluence_get_content(content_id: str, expand: str = "body.storage,version,space,history"):
    return json_result(await client.get_json(f"content/{content_id}", params={"expand": expand}))

@mcp.tool()
async def confluence_get_space(space_key: str, expand: str = "description"):
    return json_result(await client.get_json(f"space/{space_key}", params={"expand": expand}))

@mcp.tool()
async def confluence_list_content(space_key: str | None = None, title: str | None = None, type: str = "page", limit: int = 25, start: int = 0, expand: str = "space,version"):
    params = {"type": type, "limit": limit, "start": start, "expand": expand}
    if space_key: params["spaceKey"] = space_key
    if title: params["title"] = title
    return json_result(await client.get_json("content", params=params))

@mcp.tool()
async def confluence_search_content_cql(cql: str, limit: int = 25, start: int = 0, expand: str = "space,history,version,body.storage"):
    # /rest/api/content/search?cql=...
    params = {"cql": cql, "limit": limit, "start": start, "expand": expand}
    return json_result(await client.get_json("content/search", params=params))

@mcp.tool()
async def confluence_search_cql(cql: str, limit: int = 25, start: int = 0, expand: str = "content.space,space.homepage"):
    # /rest/api/search?cql=...
    params = {"cql": cql, "limit": limit, "start": start, "expand": expand}
    return json_result(await client.get_json("search", params=params))

@mcp.tool()
async def confluence_get_children(content_id: str, type: str = "page", limit: int = 25, start: int = 0):
    params = {"limit": limit, "start": start}
    return json_result(await client.get_json(f"content/{content_id}/child/{type}", params=params))

@mcp.tool()
async def confluence_list_attachments(content_id: str, limit: int = 25, start: int = 0, expand: str = "version,metadata,extensions"):
    params = {"limit": limit, "start": start, "expand": expand}
    return json_result(await client.get_json(f"content/{content_id}/child/attachment", params=params))

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
