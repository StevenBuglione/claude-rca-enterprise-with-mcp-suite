from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.models import RcaRequest, RcaResponse, Citation
from app.core.logging import get_logger
from app.services.agent.runner import run_rca

router = APIRouter(prefix="/v1", tags=["rca"])
log = get_logger("api.rca")

@router.post("/rca", response_model=RcaResponse)
async def rca(req: RcaRequest):
    try:
        run_id, result_msg, structured = await run_rca(
            pipeline_ref=req.pipeline_ref,
            question=req.question,
            skill=req.skill,
            max_turns=req.max_turns,
        )
    except Exception as e:
        log.exception("rca.failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"RCA execution failed: {e}") from e

    status = "error" if result_msg.is_error else "ok"

    citations = []
    if isinstance(structured, dict):
        for c in structured.get("citations", []) or []:
            try:
                citations.append(Citation(**c))
            except Exception:
                # Don't fail entire response due to one malformed citation
                continue

    return RcaResponse(
        status=status,
        run_id=run_id,
        session_id=getattr(result_msg, "session_id", None),
        rca=structured if isinstance(structured, dict) else None,
        citations=citations,
        usage=getattr(result_msg, "usage", None),
        cost_usd=getattr(result_msg, "total_cost_usd", None),
        error=getattr(result_msg, "result", None) if result_msg.is_error else None,
    )
