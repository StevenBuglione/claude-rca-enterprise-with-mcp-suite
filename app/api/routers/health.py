from __future__ import annotations

import os
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def live():
    return {"ok": True}

@router.get("/ready")
async def ready():
    # Lightweight readiness checks: ensure Bedrock mode env is present.
    # For deeper checks, add a startup probe that runs a minimal claude query.
    required = ["AWS_REGION", "CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_MODEL"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        return {"ok": False, "missing": missing}
    return {"ok": True}
