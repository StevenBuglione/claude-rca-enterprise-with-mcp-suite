from __future__ import annotations

import os
from starlette.responses import JSONResponse

def missing_env(*keys: str) -> list[str]:
    return [k for k in keys if not os.getenv(k)]

def _missing(*keys: str) -> list[str]:
    return missing_env(*keys)

async def live(_request):
    return JSONResponse({"ok": True})

async def ready(_request):
    # Each service adds its own env validation in addition to MCP_AUTH_TOKEN
    missing = _missing("MCP_AUTH_TOKEN")
    return JSONResponse({"ok": not missing, "missing": missing})
