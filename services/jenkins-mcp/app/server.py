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
from mcp_common.result import json_result, text_result

from app.config import settings
from app.client import JenkinsClient

configure_logging(settings.log_level)

mcp = FastMCP("jenkins", json_response=True)

client = JenkinsClient(
    base_url=settings.base_url,
    user=settings.user,
    token=settings.api_token,
    verify_ssl=settings.verify_ssl,
)

async def ready(_request):
    missing = missing_env("MCP_AUTH_TOKEN", "JENKINS_BASE_URL", "JENKINS_USER", "JENKINS_API_TOKEN")
    return JSONResponse({"ok": not missing, "missing": missing})

@mcp.tool()
async def jenkins_get_job(job_full_name: str, tree: str | None = None, depth: int | None = None):
    """Get Jenkins job metadata (Remote Access API /api/json)."""
    return json_result(await client.get_job(job_full_name, tree=tree, depth=depth))

@mcp.tool()
async def jenkins_get_build(job_full_name: str, build_number: int, tree: str | None = None, depth: int | None = None):
    """Get Jenkins build metadata (Remote Access API /api/json)."""
    return json_result(await client.get_build(job_full_name, build_number, tree=tree, depth=depth))

@mcp.tool()
async def jenkins_get_console_chunk(job_full_name: str, build_number: int, start: int = 0):
    """Get paged console output via /logText/progressiveText?start=..."""
    return json_result(await client.get_console_chunk(job_full_name, build_number, start=start))

@mcp.tool()
async def jenkins_get_job_config_xml(job_full_name: str):
    """Get job config.xml (read-only)."""
    return text_result(await client.get_config_xml(job_full_name))

@mcp.tool()
async def jenkins_get_test_report(job_full_name: str, build_number: int):
    """Get JUnit test report JSON (if available) via /testReport/api/json."""
    return json_result(await client.get_test_report(job_full_name, build_number))

@mcp.tool()
async def jenkins_wfapi_describe(job_full_name: str, build_number: int, full_stages: bool = False):
    """Get Pipeline stage graph info via /wfapi/describe (requires Pipeline: REST API plugin)."""
    return json_result(await client.wfapi_describe(job_full_name, build_number, full_stages=full_stages))

@mcp.tool()
async def jenkins_wfapi_changesets(job_full_name: str, build_number: int):
    """Get Pipeline changesets via /wfapi/changesets (requires Pipeline: REST API plugin)."""
    return json_result(await client.wfapi_changesets(job_full_name, build_number))

@mcp.tool()
async def jenkins_wfapi_artifacts(job_full_name: str, build_number: int):
    """Get Pipeline artifacts via /wfapi/artifacts (requires Pipeline: REST API plugin)."""
    return json_result(await client.wfapi_artifacts(job_full_name, build_number))

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
