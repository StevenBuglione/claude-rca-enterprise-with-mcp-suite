#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall -q app services
python3 scripts/ci_imports.py

python3 -m mypy app

MYPYPATH="services/_common:services/jenkins-mcp" python3 -m mypy services/jenkins-mcp/app
MYPYPATH="services/_common:services/bitbucket-mcp" python3 -m mypy services/bitbucket-mcp/app
MYPYPATH="services/_common:services/confluence-mcp" python3 -m mypy services/confluence-mcp/app
MYPYPATH="services/_common:services/sourcebot-mcp" python3 -m mypy services/sourcebot-mcp/app
