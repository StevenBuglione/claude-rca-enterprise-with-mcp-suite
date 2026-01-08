from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
from datetime import datetime

class EvidenceItem(BaseModel):
    run_id: str
    evidence_id: str
    source: str
    locator: str
    content: str
    content_sha256: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
