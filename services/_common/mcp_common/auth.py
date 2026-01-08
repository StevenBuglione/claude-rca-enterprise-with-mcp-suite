from __future__ import annotations

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class BearerAuthMiddleware(BaseHTTPMiddleware):
    """
    Protects /mcp* routes using a shared secret:
      Authorization: Bearer <MCP_AUTH_TOKEN>

    Health + metrics remain unauthenticated by default.
    """
    def __init__(self, app, env_name: str = "MCP_AUTH_TOKEN"):
        super().__init__(app)
        self._token = os.getenv(env_name, "")

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            if not self._token:
                return JSONResponse({"error": "server_misconfigured", "message": "MCP_AUTH_TOKEN not set"}, status_code=500)

            auth = request.headers.get("authorization", "")
            if auth != f"Bearer {self._token}":
                return JSONResponse({"error": "unauthorized"}, status_code=401)

        return await call_next(request)
