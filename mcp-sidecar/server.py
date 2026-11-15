"""Read-only configuration + run execution MCP bridge for btaira/ai-router.
Runs over stdio; no listening port or Docker socket.
"""
import os
import time
import httpx
from mcp.server.fastmcp import FastMCP

BASE = os.environ.get("AI_ROUTER_URL", "http://host.docker.internal:8000").rstrip("/")
TIMEOUT = float(os.environ.get("AI_ROUTER_TIMEOUT", "180"))
POLL = 1.0
mcp = FastMCP("ai-router")

def api(method, path, **kwargs):
    with httpx.Client(timeout=15, trust_env=False) as client:
        response = client.request(method, BASE + path, **kwargs)
        response.raise_for_status()
        return response.json()

@mcp.tool()
def list_models() -> dict:
    """List router providers and selected models; excludes credentials."""
    cfg = api("GET", "/api/config")
    return {"providers": [
        {"key": p["key"], "model": p["model"], "enabled": p["enabled"], "local": p["local"]}
        for p in cfg["providers"]
    ]}

@mcp.tool()
def get_run(run_id: str) -> dict:
    """Retrieve a run's result, fact checks, citations, and cost breakdown."""
    return api("GET", f"/api/runs/{run_id}")

@mcp.tool()
def list_runs(limit: int = 10) -> dict:
    """List recent runs without modifying router settings."""
    return {"runs": api("GET", "/api/runs", params={"limit": max(1, min(limit, 50))})}

@mcp.tool()
def consensus_research(prompt: str, skip_fact_check: bool = False) -> dict:
    """Launch router consensus research and wait for completion. Incurs model API charges.
    Caller must approve spending before invoking this tool.
    """
    if not prompt.strip() or len(prompt) > 30000:
        raise ValueError("Prompt must contain 1–30000 characters")
    created = api("POST", "/api/runs", json={"prompt": prompt, "skip_stage2": skip_fact_check})
    run_id = created["run_id"]
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        data = api("GET", f"/api/runs/{run_id}")
        status = str(data.get("run", {}).get("status", "")).lower()
        if status in {"completed", "complete", "failed", "cancelled", "canceled"}:
            return data
        time.sleep(POLL)
    return {"run_id": run_id, "status": "still_running", "message": "Poll with get_run; run was not cancelled."}

if __name__ == "__main__":
    mcp.run(transport="stdio")
