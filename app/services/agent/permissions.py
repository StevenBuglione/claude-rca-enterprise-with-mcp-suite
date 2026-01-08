from __future__ import annotations

from typing import Any, Dict
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

# Enterprise default: allow only MCP tool usage + Skill tool. Everything else is denied.
ALLOWED_PREFIXES = (
    "mcp__jenkins__",
    "mcp__bitbucket__",
    "mcp__confluence__",
    "mcp__sourcebot__",
    "mcp__evidence__",
)
ALLOWED_EXACT = {"Skill"}

async def can_use_tool(tool_name: str, input_data: Dict[str, Any], context: ToolPermissionContext):
    if tool_name in ALLOWED_EXACT or tool_name.startswith(ALLOWED_PREFIXES):
        return PermissionResultAllow(behavior="allow")

    return PermissionResultDeny(
        behavior="deny",
        message=f"Tool '{tool_name}' is not allowed by policy. Allowed: MCP tools (jenkins/bitbucket/confluence/sourcebot/evidence) + Skill."
    )
