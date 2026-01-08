from __future__ import annotations

import contextlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

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

configure_logging(settings.log_level)

mcp = FastMCP("sourcebot", json_response=True)


def _load_data(path: str) -> Dict[str, Any]:
    data_path = Path(path)
    if not data_path.is_file():
        return {"repos": [], "files": []}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _snippet(lines: List[str], line_index: int, context_lines: int = 2) -> str:
    start = max(line_index - context_lines, 0)
    end = min(line_index + context_lines + 1, len(lines))
    return "\n".join(lines[start:end])


_DATA = _load_data(settings.mock_data_path)
_REPOS = _DATA.get("repos", [])
_FILES = _DATA.get("files", [])
_REPO_LOOKUP = {repo.get("id"): repo for repo in _REPOS}


@mcp.tool()
async def list_repos():
    """List mock repositories indexed by Sourcebot."""
    return json_result({"repos": _REPOS})


@mcp.tool()
async def get_file_source(fileName: str, repoId: str):
    """Fetch the source code for a given file in a repository."""
    for entry in _FILES:
        if entry.get("repo_id") == repoId and entry.get("file_name") == fileName:
            repo = _REPO_LOOKUP.get(repoId, {})
            return json_result(
                {
                    "found": True,
                    "repoId": repoId,
                    "repoName": repo.get("name"),
                    "fileName": fileName,
                    "language": entry.get("language"),
                    "content": entry.get("content", ""),
                }
            )
    return json_result({"found": False, "repoId": repoId, "fileName": fileName, "content": ""})


@mcp.tool()
async def search_code(
    query: str,
    filterByRepoIds: List[str] | None = None,
    filterByLanguages: List[str] | None = None,
    caseSensitive: bool = False,
    includeCodeSnippets: bool = False,
    maxTokens: int | None = None,
):
    """Search mock code using a regex query string."""
    if not query:
        return json_result({"matches": []})

    flags = 0 if caseSensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags=flags)
    except re.error as exc:
        return json_result({"matches": [], "error": "invalid_regex", "message": str(exc)})
    repo_filter = set(filterByRepoIds or [])
    lang_filter = set(filterByLanguages or [])

    matches: List[Dict[str, Any]] = []
    for entry in _FILES:
        repo_id = entry.get("repo_id")
        if repo_filter and repo_id not in repo_filter:
            continue
        language = entry.get("language")
        if lang_filter and language not in lang_filter:
            continue

        content = entry.get("content", "")
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if not pattern.search(line):
                continue
            repo = _REPO_LOOKUP.get(repo_id, {})
            match = {
                "repoId": repo_id,
                "repoName": repo.get("name"),
                "repoUrl": repo.get("url"),
                "fileName": entry.get("file_name"),
                "language": language,
                "lineNumber": idx + 1,
                "line": line,
            }
            if includeCodeSnippets:
                match["snippet"] = _snippet(lines, idx)
            matches.append(match)

    return json_result({"matches": matches})


async def ready(_request):
    missing = missing_env("MCP_AUTH_TOKEN")
    if settings.mode.lower() == "mock":
        if not Path(settings.mock_data_path).is_file():
            missing.append("SOURCEBOT_MOCK_DATA")
    else:
        missing.extend(missing_env("SOURCEBOT_HOST", "SOURCEBOT_API_KEY"))
    return JSONResponse({"ok": not missing, "missing": missing})


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
