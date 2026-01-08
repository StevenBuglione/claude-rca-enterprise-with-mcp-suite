from __future__ import annotations

import json
from typing import Any, Optional, Dict
from mcp.types import CallToolResult, TextContent

def json_result(payload: Any, *, meta: Optional[Dict[str, Any]] = None) -> CallToolResult:
    # Provide both human-readable text and structuredContent.
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
        structuredContent=payload,
        _meta=meta or {},
    )

def text_result(text: str, *, meta: Optional[Dict[str, Any]] = None) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        _meta=meta or {},
    )
