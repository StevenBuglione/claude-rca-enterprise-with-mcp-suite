# Enterprise Claude Code RCA API + MCP Suite (All-in-One)

This repo combines:
- **Enterprise Claude Code RCA API** (FastAPI + Claude Agent SDK + Bedrock + Evidence Registry)
- **Read-only MCP services** for Jenkins, Bitbucket Data Center, Confluence Data Center, and Sourcebot (mock)

Run everything locally with one command:
```bash
cp .env.example .env
docker compose up --build
```

Service URLs:
- RCA API: http://localhost:8000
- Jenkins MCP: http://localhost:18080/mcp
- Bitbucket MCP: http://localhost:18081/mcp
- Confluence MCP: http://localhost:18082/mcp
- Sourcebot MCP: http://localhost:18083/mcp
- Postgres: localhost:15432 (db `rca`)

Sourcebot runs in mock mode by default using the bundled `services/sourcebot-mcp/app/mock_data.json`.

The RCA API is preconfigured to call these services via `.mcp.json` using `MCP_AUTH_TOKEN`.


# Enterprise Claude Code RCA API (Starter)
FastAPI facade that runs a **Claude Code agent** through the **Claude Agent SDK**, with:
- **AWS Bedrock** as the LLM backend (Opus 4.5 modelId)
- **Claude Code Skills** in `.claude/skills/`
- External **MCP servers** configured via `.mcp.json` (Jenkins/Bitbucket/Confluence/SourceBot)
- An **in-process Evidence Registry MCP server** (SDK MCP tools) that guarantees citations reference persisted evidence objects
- Production-grade **observability**: structured JSON logs, OpenTelemetry traces, Prometheus metrics

## Quickstart
1) Configure environment:
```bash
cp .env.example .env
# fill AWS credentials (or use ~/.aws + AWS_PROFILE), and your Bedrock modelId
```

2) Start the API:
```bash
docker compose up --build
```

3) Open API docs:
- http://localhost:8000/docs

4) Run an RCA:
```bash
curl -s http://localhost:8000/v1/rca \
  -H 'content-type: application/json' \
  -d '{
    "pipeline_ref": "job=my-pipeline build=123",
    "question": "Why did it fail? Provide root cause and fixes with citations.",
    "skill": "rca"
  }' | jq
```

## Add Skills
Create a new skill scaffold:
```bash
python scripts/new_skill.py --name my-skill --description "Describe when to use this skill"
```

Skills live under:
`.claude/skills/<skill-name>/SKILL.md`

## Add/Configure MCP Servers
Edit `.mcp.json`. Example (HTTP transport):
```json
{
  "mcpServers": {
    "jenkins": {
      "type": "http",
      "url": "http://jenkins-mcp:8080/mcp",
      "headers": { "Authorization": "Bearer ${JENKINS_TOKEN}" }
    }
  }
}
```

## Observability (local)
Enable the optional observability stack (OTel Collector + Jaeger + Prometheus):
```bash
docker compose --profile obs up --build
```

- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Metrics endpoint: http://localhost:8000/metrics

## CI / Type checks
Install dev deps and run the checks locally:
```bash
pip install -r requirements.txt -r requirements-dev.txt
./scripts/ci_check.sh
```

## Production guidance (ECS)
- Use an ECS task role with `bedrock:InvokeModel` (and related actions) rather than static keys.
- Keep `permission_mode=bypassPermissions` but enforce a strict tool allowlist via hooks/permissions.
- Persist Evidence Registry to a durable store (Postgres/DynamoDB). The interface is abstracted.
# claude-rca-enterprise-with-mcp-suite
