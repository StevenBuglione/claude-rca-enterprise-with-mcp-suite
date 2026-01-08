from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(:-([^}]*))?\}")

def _expand_env(value: str) -> str:
    def repl(m: re.Match) -> str:
        var = m.group(1)
        default = m.group(3)
        if var in os.environ:
            return os.environ[var]
        if default is not None:
            return default
        raise RuntimeError(f"Missing required environment variable for .mcp.json: {var}")
    return _ENV_PATTERN.sub(repl, value)

def _expand_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return _expand_env(obj)
    if isinstance(obj, list):
        return [_expand_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _expand_obj(v) for k, v in obj.items()}
    return obj

def load_project_mcp_servers(project_root: Path) -> Dict[str, Any]:
    path = project_root / ".mcp.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    return _expand_obj(servers)
