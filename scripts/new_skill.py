from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

TEMPLATE = '''---
name: {name}
description: {description}
---

# Skill: {name}

Define:
- When to use this skill (trigger patterns)
- Which MCP tools are permitted
- Evidence/citation discipline
- Output requirements (schema constraints)

Notes:
- Keep tool usage deterministic.
- Prefer evidence excerpts over large dumps.
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    skill_dir = root / ".claude" / "skills" / args.name
    skill_dir.mkdir(parents=True, exist_ok=True)

    p = skill_dir / "SKILL.md"
    if p.exists():
        raise SystemExit(f"Skill already exists: {p}")

    p.write_text(TEMPLATE.format(name=args.name, description=args.description), encoding="utf-8")
    print(f"Created: {p}")

if __name__ == "__main__":
    main()
