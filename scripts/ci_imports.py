from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENV_DEFAULTS = {
    "MCP_AUTH_TOKEN": "ci-token",
    "JENKINS_BASE_URL": "https://jenkins.example.com",
    "JENKINS_USER": "ci",
    "JENKINS_API_TOKEN": "ci",
    "BITBUCKET_BASE_URL": "https://bitbucket.example.com",
    "BITBUCKET_TOKEN": "ci",
    "BITBUCKET_AUTH_MODE": "bearer",
    "CONFLUENCE_BASE_URL": "https://confluence.example.com",
    "CONFLUENCE_TOKEN": "ci",
    "CONFLUENCE_AUTH_MODE": "bearer",
    "SOURCEBOT_MODE": "mock",
    "AWS_REGION": "us-east-1",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "ANTHROPIC_MODEL": "dummy",
    "EVIDENCE_STORE_URL": "postgresql://rca:rca@localhost:5432/rca",
}


def run_import(code: str, paths: list[Path], *, cwd: Path) -> None:
    env = os.environ.copy()
    env.update(ENV_DEFAULTS)
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in paths)
    subprocess.run([sys.executable, "-c", code], check=True, env=env, cwd=cwd)


def import_package(module: str, paths: list[Path], *, cwd: Path) -> None:
    run_import(f"import {module}", paths, cwd=cwd)


def import_file(path: Path, paths: list[Path], *, cwd: Path) -> None:
    code = (
        "import importlib.util, sys; "
        f"spec=importlib.util.spec_from_file_location('ci_module', {repr(str(path))}); "
        "mod=importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(mod)"
    )
    run_import(code, paths, cwd=cwd)


def main() -> None:
    import_package("app.main", [ROOT], cwd=ROOT)
    import_package("app.services.agent.runner", [ROOT], cwd=ROOT)
    import_package("app.services.mcp.evidence_server", [ROOT], cwd=ROOT)

    common = ROOT / "services" / "_common"
    service_roots = [
        ROOT / "services" / "jenkins-mcp",
        ROOT / "services" / "bitbucket-mcp",
        ROOT / "services" / "confluence-mcp",
        ROOT / "services" / "sourcebot-mcp",
    ]

    for service_root in service_roots:
        path = service_root / "app" / "server.py"
        import_file(path, [service_root, common], cwd=service_root)


if __name__ == "__main__":
    main()
