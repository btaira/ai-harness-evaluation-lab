# AI Router MCP sidecar (prototype)

Targets existing `btaira/ai-router` endpoints without editing the router.

## Interface
- `list_models` — read-only
- `list_runs` — read-only
- `get_run` — read-only
- `consensus_research` — creates a paid multi-model run; requires human approval.

This **does not** turn the router into an OpenAI-compatible inference endpoint. It exposes consensus research as an MCP tool; harnesses still need their own model provider.

## Install (WSL2, local stdio)
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
AI_ROUTER_URL=http://127.0.0.1:8000 .venv/bin/python server.py
```
The process communicates through MCP stdio. Configure the client to launch this command; it is not an interactive CLI.

## Docker option
```bash
docker build -t ai-router-mcp:local .
docker run --rm -i --read-only --cap-drop=ALL --security-opt=no-new-privileges \\
  --pids-limit=64 --memory=256m --cpus=0.5 \\
  -e AI_ROUTER_URL=http://host.docker.internal:8000 ai-router-mcp:local
```
Client must launch the container with stdin connected. Do not publish ports or mount Docker socket.

## Limitations / review before deployment
- Router's existing API has no authentication; keep it bound to localhost and prevent untrusted containers from reaching it.
- Current router compose publishes `8000:8000` on all interfaces. Change to `127.0.0.1:8000:8000` only after approval and checking existing consumers.
- MCP tool execution incurs real provider costs; no enforceable dollar cap exists in this sidecar.
- Long-running runs return an ID on timeout; retrieve with `get_run`.
- The exact terminal status string and CreateRunRequest schema should be verified against the deployed revision.
- Do not give this tool to untrusted agents until per-tool human approval is enabled.
- This package has not been connected to a running router.
