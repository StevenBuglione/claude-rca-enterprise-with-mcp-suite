from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class RcaRequest(BaseModel):
    pipeline_ref: str = Field(..., description="Jenkins job/build reference, URL, or logical identifier.")
    question: str = Field(..., description="What you want the RCA agent to answer.")
    skill: str = Field(default="rca", description="Claude Code Skill name under .claude/skills/")
    max_turns: int = Field(default=18, ge=1, le=50)

class Citation(BaseModel):
    evidence_id: str
    source: str
    locator: str
    quote: str

class RcaResponse(BaseModel):
    status: str
    run_id: str
    session_id: Optional[str] = None
    rca: Optional[Dict[str, Any]] = None
    citations: List[Citation] = Field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None
