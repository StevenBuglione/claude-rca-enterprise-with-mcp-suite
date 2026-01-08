from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk.types import ResultMessage, AssistantMessage, ToolUseBlock, ToolResultBlock, TextBlock, ThinkingBlock

from app.core.logging import get_logger
from app.core.config import settings
from app.evidence.store import build_evidence_store
from app.services.mcp.evidence_server import build_evidence_mcp_server
from app.services.agent.mcp_config import load_project_mcp_servers
from app.services.agent.schema import RCA_JSON_SCHEMA
from app.services.agent.hooks import log_pre_tool_use, log_post_tool_use
from app.services.agent.permissions import can_use_tool

log = get_logger("agent.runner")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RCA_SEMAPHORE = asyncio.Semaphore(settings.max_concurrent_rca)

def _build_prompt(*, run_id: str, pipeline_ref: str, question: str, skill: str) -> str:
    return f"""Use the **{skill}** Skill.

You are performing Root Cause Analysis (RCA) for a failed Jenkins pipeline using MCP tools.

run_id: {run_id}
pipeline_ref:
{pipeline_ref}

question:
{question}

Hard requirements:
- Use MCP tools to gather evidence; do not guess.
- Every factual claim must have a citation that references an evidence_id created via mcp__evidence__add(run_id=...).
- Store minimal excerpts as evidence (targeted log windows, diff hunks, runbook paragraphs).
- Include recommended remediation_steps with concrete actions and validation steps.
- Output MUST match the host JSON schema (no markdown).
"""

def build_options() -> ClaudeAgentOptions:
    # Load external MCP servers from .mcp.json (with env expansion)
    external_mcp = load_project_mcp_servers(PROJECT_ROOT)

    # In-process evidence registry (Postgres-backed)
    store_url = settings.evidence_store_url
    evidence_store = build_evidence_store(store_url)
    evidence_server = build_evidence_mcp_server(evidence_store)

    mcp_servers: Dict[str, Any] = dict(external_mcp)
    mcp_servers["evidence"] = evidence_server

    return ClaudeAgentOptions(
        # Load Claude Code system prompt + project skills/instructions
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["project"],
        # MCP servers: external + in-process evidence server
        mcp_servers=mcp_servers,
        # Structured output for stable API response.
        output_format={"type": "json_schema", "schema": RCA_JSON_SCHEMA},
        # Enterprise posture: bypass interactive prompts but enforce policy in can_use_tool + hooks.
        permission_mode="bypassPermissions",
        can_use_tool=can_use_tool,
        # Disable dangerous built-ins even if model tries (belt + suspenders).
        disallowed_tools=[
            "Bash", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch", "TodoWrite"
        ],
        hooks={
            "PreToolUse": [HookMatcher(hooks=[log_pre_tool_use])],
            "PostToolUse": [HookMatcher(hooks=[log_post_tool_use])],
        },
        cwd=str(PROJECT_ROOT),
    )

async def run_rca(*, pipeline_ref: str, question: str, skill: str, run_id: Optional[str] = None, max_turns: int = 18) -> Tuple[str, ResultMessage, Dict[str, Any] | None]:
    rid = run_id or str(uuid.uuid4())
    prompt = _build_prompt(run_id=rid, pipeline_ref=pipeline_ref, question=question, skill=skill)

    options = build_options()
    options.max_turns = max_turns

    # One request == one isolated session/client. This keeps the service stateless and horizontally scalable.
    async with _RCA_SEMAPHORE:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            structured: Dict[str, Any] | None = None
            result_msg: ResultMessage | None = None

            async for message in client.receive_messages():
                # Log high-level progress for debugging
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            log.info("agent.tool_use", run_id=rid, tool=block.name, tool_use_id=block.id)
                        elif isinstance(block, ToolResultBlock):
                            log.info("agent.tool_result", run_id=rid, tool_use_id=block.tool_use_id, is_error=block.is_error)
                        elif isinstance(block, ThinkingBlock):
                            # Do not log raw thinking in enterprise logs by default.
                            pass
                        elif isinstance(block, TextBlock):
                            # Avoid logging full text output; can be sensitive and large.
                            pass

                if isinstance(message, ResultMessage):
                    result_msg = message
                    structured = message.structured_output if hasattr(message, "structured_output") else None
                    break

            if result_msg is None:
                raise RuntimeError("Claude SDK client did not produce a ResultMessage.")

            return rid, result_msg, structured

    raise RuntimeError("RCA execution did not return a result.")
