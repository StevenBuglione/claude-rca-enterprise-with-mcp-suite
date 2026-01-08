from __future__ import annotations

import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from claude_agent_sdk import tool, create_sdk_mcp_server

from app.evidence.store import EvidenceStore

class AddArgs(BaseModel):
    run_id: str
    source: str
    locator: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RefArgs(BaseModel):
    run_id: str
    evidence_id: str

class SearchArgs(BaseModel):
    run_id: str
    query: str
    limit: int = 20

def build_evidence_mcp_server(store: EvidenceStore):
    @tool("add", "Add an evidence excerpt and return a stable evidence_id for citations.", AddArgs)
    async def add(args: AddArgs):
        item = store.add(
            run_id=args.run_id,
            source=args.source,
            locator=args.locator,
            content=args.content,
            metadata=args.metadata,
        )
        payload = {
            "evidence_id": item.evidence_id,
            "source": item.source,
            "locator": item.locator,
            "quote": item.content[:280],
            "content_sha256": item.content_sha256,
        }
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}

    @tool("get", "Get a previously stored evidence item by evidence_id.", RefArgs)
    async def get(args: RefArgs):
        item = store.get(run_id=args.run_id, evidence_id=args.evidence_id)
        payload = item.model_dump()
        payload["created_at"] = item.created_at.isoformat()
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}

    @tool("list", "List evidence items for a run_id.", {"run_id": str})
    async def list_items(args: Dict[str, Any]):
        run_id = args["run_id"]
        items = store.list(run_id=run_id)
        payload = [
            {
                "evidence_id": i.evidence_id,
                "source": i.source,
                "locator": i.locator,
                "quote": i.content[:200],
                "content_sha256": i.content_sha256,
            }
            for i in items
        ]
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}

    @tool("search", "Search evidence by substring match across content and locator.", SearchArgs)
    async def search(args: SearchArgs):
        items = store.search(run_id=args.run_id, query=args.query, limit=args.limit)
        payload = [
            {
                "evidence_id": i.evidence_id,
                "source": i.source,
                "locator": i.locator,
                "quote": i.content[:200],
            }
            for i in items
        ]
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}

    return create_sdk_mcp_server(
        name="evidence",
        version="1.0.0",
        tools=[add, get, list_items, search],
    )
