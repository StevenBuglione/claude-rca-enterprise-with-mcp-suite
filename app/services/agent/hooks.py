from __future__ import annotations

from typing import Any, cast
from claude_agent_sdk import HookContext
from claude_agent_sdk.types import (
    HookInput,
    PostToolUseHookInput,
    PreToolUseHookInput,
    SyncHookJSONOutput,
)
from app.core.logging import get_logger

log = get_logger("agent.hooks")

async def log_pre_tool_use(input_data: HookInput, tool_use_id: str | None, context: HookContext) -> SyncHookJSONOutput:
    data = cast(PreToolUseHookInput, input_data)
    log.info(
        "tool.pre",
        tool_name=data.get("tool_name"),
        tool_use_id=tool_use_id,
        tool_input=data.get("tool_input"),
    )
    return {}

async def log_post_tool_use(input_data: HookInput, tool_use_id: str | None, context: HookContext) -> SyncHookJSONOutput:
    data = cast(PostToolUseHookInput, input_data)
    log.info(
        "tool.post",
        tool_name=data.get("tool_name"),
        tool_use_id=tool_use_id,
        tool_output=data.get("tool_response"),
    )
    return {}
