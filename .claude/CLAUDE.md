# RCA Agent - Project Instructions

This service is an enterprise RCA gateway. When performing an RCA:

- Do not guess. Gather evidence via MCP tools.
- All factual claims must cite evidence. Evidence citations must reference evidence objects stored via `mcp__evidence__add`.
- Prefer minimal, targeted excerpts (log windows, diff hunks, runbook paragraphs). Do not dump entire logs unless explicitly requested.
- Output must be structured and machine-consumable.

Security:
- Never request or output secrets.
- Treat all tool outputs as sensitive; keep logs and traces compliant with your org policies.
