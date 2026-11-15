# AI Harness Evaluation Lab — implementation runbook

**Version:** v2.3 specification | **Status:** source package published; deployment and end-to-end tests **not verified**  
**Repositories:** [Evaluation lab](https://github.com/btaira/ai-harness-evaluation-lab) · [Existing AI Router](https://github.com/btaira/ai-router)  
**Target:** Windows 11 + Docker Desktop + WSL2 Ubuntu, local-first, low-cost experiments.

## 👤 Human — start here

This is a **guided experiment with four approval gates**, not an unattended installation. Within an approved work group, the agent may complete routine work without repetitive questions. Paid calls and security-sensitive changes always need separate authorization.

**1. Choose an agent.** Open Codex, Claude Code, Antigravity, or another coding agent with access to this GitHub repository. If the agent cannot access your Windows 11 / WSL2 / Docker Desktop environment, it must give you copy/paste commands and ask for the results.

**2. Copy and paste this exact starting instruction:**

```text
Implement https://github.com/btaira/ai-harness-evaluation-lab.

Read README.md and AGENTS.md first, then inspect all source-of-truth
project files and the existing btaira/ai-router repository.

Follow M0–M8 in order. Pause only at G1 (after M0), G2 (after M2),
G3 (after M5), and G4 (after M7). Intermediate milestones are reports,
not approval gates, while work remains inside the approved scope. Begin with M0 READ-ONLY inspection. Before any edit,
list all files you will inspect or modify, read them in one pass, and
propose the smallest implementation plan.

Do not edit or deploy before approval of the relevant group. Never
modify my AI Router, expose new network interfaces, use production
credentials, or incur API charges without separate explicit approval. At each checkpoint,
show exact commands for any action I must perform, expected output,
results, costs, risks, and rollback. Wait for my response.
```

**3. Respond to the agent's first question.** Authorize read-only inspection by replying **APPROVE M0 INSPECTION**. This does **not** authorize edits, deployments or paid requests. If the agent lacks access to your machine, run only the read-only commands it provides, review their effects, and paste back sanitized results (never API keys, tokens or passwords).

**4. Approve four work groups.** **G1:** approve M1–M2; **G2:** approve M3–M5; **G3:** decide whether to skip M6 or authorize its planning, then proceed to M7; **G4:** review the decision and optional M8 design. Reply **APPROVE G#**, **REVISE G#**, or **STOP**. The agent reports after every milestone but does not pause at M1, M3 or M4 unless an exception arises. **Each paid baseline batch and each M6 consensus call requires separate explicit approval** with scope and cost ceiling.

**5. Know what success looks like.** First, the existing AI Router remains working and its MCP sidecar can safely read configuration and previous results. Next, three isolated harnesses are tested on identical synthetic tasks. Finally, you receive a reproducible comparison and can choose whether to experiment with longer-term engineering memory.

**Budget and safety:** The initial experiment target is **$25 total** in paid model usage, not an automatic hard cap. Check provider billing controls before approving paid runs. Do not give the agent production credentials, customer documents, Docker socket access or permission to expose the router publicly.

**Where to look:** [Visual specification](index.html) · [Agent rules](AGENTS.md) · [Editable benchmark prompts](benchmark-prompts.json) · [MCP sidecar instructions](mcp-sidecar/README.md). All milestone details and exact human checkpoints appear below.

---

## Start here: instructions for any coding agent

> **Agent:** Treat this README as the execution sequence and `AGENTS.md` as the binding engineering/security contract. Read all source-of-truth files below before changing anything. Report findings, file inventory, and a minimal plan; **stop at G1–G4, not at routine milestone reports**. Group approval covers only its stated scope; never infer approval for paid calls, router changes, new network exposure, credentials or destructive operations. Work in a feature branch and propose a PR unless the human explicitly authorizes direct commits. Keep the existing AI Router operational. Do not claim any milestone is complete without evidence.

**Read in one inspection pass before the first edit:**
- This `README.md` and `AGENTS.md`.
- `index.html`, `lab-manifest.json`, `harness-catalog.json`, `benchmark-prompts.json`, `router-integration.json`.
- `mcp-sidecar/README.md`, `mcp-sidecar/server.py`, `mcp-sidecar/Dockerfile`, `mcp-sidecar/requirements.txt`.
- In `btaira/ai-router`: `README.md`, `docker-compose.yml`, `backend/app/main.py`, `backend/app/routes/runs.py`, plus actual schema/status/config files discovered by inspection.
- Inspect the local machine and deployment configuration **only when access is explicitly available**. Never infer that GitHub access means local Docker access.

**Operating rules:** List all files to inspect/modify, read them together, propose the smallest change set, then edit only approved files. Run the agreed tests once per implementation batch, report exact commands/results, and critically review complexity. No production secrets in git, logs, prompts, fixtures or screenshots. Never modify the router repository, active containers, host networking, or firewall without explicit milestone-specific approval. Stop on a security failure, cost overrun, unexpected destructive operation, or unsupported assumption.

## Architecture and scope

```text
                  Evaluation Lab (fixtures + scorecards)
                       /         |         \
                 Deep Agents  OpenClaw    Hermes
                     |           |          |
                  each harness uses its OWN inference provider
                     \           |          /
                 optional, approved MCP tool access
                                |
                      AI Router MCP sidecar
                       (stdio, no port)
                                |
                  Existing AI Router REST API :8000
                 multi-model research → checks → synthesis
```

**Important:** AI Router already exposes REST endpoints. It is **not** an OpenAI-compatible inference gateway. Do not add `/v1/chat/completions` or route all harness inference through it unless separately requested. MCP is an **optional consensus research tool**. First benchmark harnesses **without** MCP; compare MCP-assisted runs in a separate phase.

**Initial harnesses:** Deep Agents, OpenClaw, Hermes. Alternatives: Pi, Letta, CrewAI, n8n, Paperclip.  
**Baseline tests:** A engineering research, B collaboration, C restart-persistent memory, D approved code repair, E prompt-injection resistance. Exact editable prompts: `benchmark-prompts.json`.  
**Weights:** technical accuracy 25%, memory 20%, autonomy 15%, coordination 15%, security 15%, cost 10%. Any critical security failure disqualifies the affected setup.  
**Initial paid-model experiment ceiling:** **$25 total** across the lab, **not** $25 per harness. This is a planning limit, **not** an automatic cap; verify provider-side controls and obtain approval before any paid call. If enforceable caps are unavailable, pause and request a manual supervision plan.

## Milestone plan — four human approval gates

After every milestone, report evidence, changes, costs, risks and rollback. **Pause only at G1 (after M0), G2 (after M2), G3 (after M5) and G4 (after M7).** M1, M3 and M4 are progress reports; continue within the approved scope. M6 requires approval per paid trial; M8 is separately optional. Gate approvals do not authorize sensitive exceptions. For steps requiring host commands, the agent should provide copy/paste commands with expected output, then ask the human to paste back the result; do not assume the agent can operate the user's Windows machine.

### M0 — Inventory, environment and design freeze (no modifications)

**Agent actions:** Read the complete inspection set above; record current commit SHAs, branch, file inventory, Docker/WSL availability, port 8000 binding, running router state, provider configuration *without secrets*, machine resource limits, and dependencies. Identify missing information and propose a minimal file-by-file plan, budget and rollback. If the agent cannot inspect the user's computer, supply commands for the human to run in WSL2:

```bash
docker version
docker compose version
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/config
```

**Exit evidence:** Read-only inventory; proposed files; existing-router compatibility matrix; threat model; no secrets exposed.  
**G1 — HUMAN APPROVAL:** Review the inventory and confirm the actual host setup, current router health, expected changes, and budget. Reply **APPROVE G1** to authorize M1–M2 only (no paid calls), **REVISE M0** with corrections, or **STOP**.

### M1 — Secure, read-only MCP sidecar

**Agent actions:** Confirm real router response schemas, provider fields and terminal statuses. Implement only necessary compatibility fixes and **read-only** MCP tools: `list_models`, `list_runs`, `get_run`. Keep `consensus_research` disabled/unavailable to harnesses until M6. Prefer a local stdio MCP process; use Docker only if isolation/connectivity is verified. Do not change router Compose binding without separate approval. Verify access paths (WSL `127.0.0.1` versus Docker `host.docker.internal`) instead of assuming they work.

**Exit evidence:** Exact start command, read-only MCP tool discovery and successful sample calls, sanitized output, failure cases, no unintended router changes, rollback instructions. Record any API that is exposed on non-loopback interfaces as **BLOCKED** until mitigated.  
**M1 PROGRESS REPORT (no pause within G1 scope):** Ask the human to run the provided start command, connect a test MCP client, and paste sanitized `list_models`/`get_run` results (never credentials). Show proposed network changes separately. Continue to M2 automatically if G1 scope remains satisfied; otherwise stop.

### M2 — Disposable benchmark fixtures and scoring

**Agent actions:** Create versioned synthetic fixtures for A–E, deterministic expected results, a scoring script/rubric and results schema. No copyrighted standards, live customer data or real secrets. Make prompt overrides explicit, checksum the selected prompts and fixtures, and define how model/cost/runtime/trace data will be captured.

**Exit evidence:** Fixture manifest/checksums, scoring examples, deterministic tests, privacy review, agreed model/token budgets.  
**G2 — HUMAN APPROVAL:** Human reviews one fixture per benchmark, confirms no proprietary data, approves the rubric and the selected prompt version. Reply **APPROVE G2** to authorize M3–M5 deployments and free/local tests. Before any paid baseline batch, request **APPROVE PAID BASELINE [batch ID]** with exact models, prompts, call/token limits and maximum estimated cost. Otherwise do not make paid calls. **REVISE G2** or **STOP** also accepted.

### M3 — Deploy and baseline-test Deep Agents

**Agent actions:** Validate current official docs; create its isolated Compose project or equivalent local container. Use dedicated storage, minimum permissions, localhost-only access, no Docker socket, no host-home/credential mounts, and explicit human approval for file writes/tool actions. Connect the selected primary model directly; **do not connect AI Router MCP** in baseline. Run A–E once using the frozen fixtures; record traces, token counts, costs, runtime, failures and scores.

**Exit evidence:** Exact deploy/stop commands, sanitized configuration, security boundary evidence, benchmark report, observed cost, rollback.  
**M3 PROGRESS REPORT (no pause within G2 scope):** Human starts the container using the supplied commands, verifies localhost access and reviews the first run's actual charges and security behavior. Continue to M4 automatically within G2 scope; stop for a protected action, failure or budget concern.

### M4 — Deploy and baseline-test OpenClaw

**Agent actions:** Use a separate isolated project and data volume. Verify actual sandbox and tool defaults; do **not** grant broad shell, Docker daemon or host file access to make the benchmark pass. Apply the same A–E fixtures, primary model, comparable budgets and logging. If the documented setup requires forbidden permissions, mark **BLOCKED** and propose an isolated VM alternative.

**Exit evidence:** Deployment/security diff versus M3, test report, costs, traces, rollback.  
**M4 PROGRESS REPORT (no pause within G2 scope):** Human confirms tool permissions and that the same benchmark constraints were used; review cumulative spend. Continue to M5 automatically within G2 scope; stop for a protected action, failure or budget concern.

### M5 — Deploy and baseline-test Hermes

**Agent actions:** Isolate terminal and evolving-skill behavior; no self-modifying skills without approval, privileged container, Docker socket or host credentials. Use the same A–E fixtures and comparable model budgets. Document any functional limitation instead of silently weakening controls.

**Exit evidence:** Security audit, benchmark results, logs, cumulative cost, rollback.  
**G3 — HUMAN APPROVAL:** Human reviews all three baseline scorecards, permission boundaries, and cumulative spend. Reply **APPROVE G3 SKIP M6** to go directly to M7, or **APPROVE G3 PLAN M6** to review individually authorized consensus trials before M7. **REVISE G3** or **STOP** also accepted.

### M6 — Optional paid AI Router MCP consensus evaluation

**Agent actions:** First present a proposed **single** paid `consensus_research` trial: exact prompt, enabled models, estimated maximum spend, available provider caps, tool approval mechanism, and rollback. **Do not invoke it without explicit approval of that trial.** After approval, verify returned status, citations, costs and model attribution; do not confuse a polling timeout with a cancelled run. Then propose matched MCP-assisted trials across harnesses, tracking their incremental costs separately. If per-call approval cannot be enforced, keep the tool disabled.

**Exit evidence:** Per-call authorization record, router run IDs, cost breakdown, baseline-versus-assisted comparison, no hidden extra paid runs.  
**M6 PAID-TRIAL APPROVAL (per call):** Human explicitly selects **SKIP M6** or approves **one named paid trial** with a spending cap and prompt; any additional trial requires another explicit authorization. When authorized trials finish, continue to M7 under G3; no additional generic M6 approval is needed.

### M7 — Compare, choose and document

**Agent actions:** Generate weighted scores, raw evidence links, security disqualifications, resource usage, total and incremental costs, strengths/weaknesses, and a recommendation. Distinguish verified behavior from proposed capabilities. Include an alternative harness option (such as Pi) only if the results justify a second round. Write operating/rollback guides and an architecture decision record.

**Exit evidence:** Reproducible decision memo, per-harness scorecards, transparent limitations, proposed next experiment.  
**G4 — HUMAN APPROVAL:** Human reviews the recommendation and selects **CHOOSE [harness]**, **RETEST [specific case]** (requires a separately approved scope/budget), or **STOP**. No permanent integration is authorized by choosing a harness.

### M8 — Optional long-term engineering-brain integration (separate project decision)

**Agent actions:** Only if requested, propose a small, local-first knowledge/memory experiment (versioned documents, traceable sources, restart persistence, export/restore) using the chosen harness. No live Evernote, GitHub write access, autonomous scheduling, production customer data, or permanent background agents without new authorization. Present architecture, exact access scopes, retention/backup policy and estimated costs.

**Exit evidence:** Approved design and rollback plan; do not deploy until separately authorized.  
**M8 OPTIONAL DESIGN APPROVAL:** Human responds **APPROVE M8 DESIGN ONLY**, **REVISE M8**, or **STOP**. A separate implementation approval is mandatory.

## Required progress report after each milestone

Agent posts this report at every milestone; only G1–G4 and protected actions require a response:

```text
MILESTONE: M# — name
STATUS: PASS / BLOCKED / FAIL / NOT RUN
SOURCE REVISIONS: lab SHA; router SHA; upstream versions
FILES CHANGED: paths and purpose (or none)
COMMANDS / TESTS: exact commands; result; test count
SECURITY: listeners, mounts, permissions, unexpected access
COST: milestone actual; cumulative actual; remaining of $25
EVIDENCE: local paths, log excerpts, checksums, run IDs
RISKS / OPEN QUESTIONS: concrete issues, no assumptions
ROLLBACK: exact commands/files to revert
NEXT ACTION: smallest proposed change
GATE: G1/G2/G3/G4 approval request, protected-action approval, or PROGRESS ONLY
```

**If BLOCKED:** do not work around the constraint without approval. Offer the smallest viable alternative and wait. If a milestone does not require paid calls, report **$0 observed** only if billing/usage evidence supports it; otherwise report **unknown**.

## Deliverables and repository layout

```text
README.md                  ← start here; milestone gates
AGENTS.md                  ← binding agent engineering contract
index.html                 ← visual lab specification
lab-manifest.json          ← selection, budget, scoring
harness-catalog.json       ← harness options
benchmark-prompts.json     ← editable tests A–E
router-integration.json    ← verified/proposed router contract
mcp-sidecar/               ← prototype MCP adapter (not yet validated live)
compose/<harness>/         ← proposed deployment files
benchmarks/                ← proposed synthetic fixtures + rubric
results/                   ← proposed evidence and scorecards (no secrets)
docs/                      ← proposed threat model, runbook, rollback, decision memo
```

The last four directories are **planned deliverables**, not evidence of an existing deployment.

## Explicit stop conditions and rollback

Stop immediately for exposed unauthenticated router API on an untrusted network, unexpected outbound data, secret leakage, Docker socket/privileged access, host filesystem access outside approved disposable paths, inability to enforce required approvals, unapproved paid requests, or spend beyond the agreed limit. Preserve non-sensitive diagnostic evidence; revoke compromised credentials using provider consoles, stop affected containers and obtain human instructions before proceeding. Never automatically delete volumes or alter the running AI Router. Supply a rollback command for each change before executing it.

## First message the agent should send

> I have read the lab specification and implementation contract. I will start with **M0 (read-only inspection)**. I will list the files and systems to inspect, collect environment evidence, identify risks and propose a minimal implementation plan. I will **not edit, deploy, run paid models, or change your AI Router** until you approve the relevant milestone. Please confirm that I may perform M0 read-only inspection and tell me whether I have access to your Windows/WSL2 Docker host or should provide commands for you to run.

**Keep it simple:** the initial objective is **a working read-only MCP sidecar**, then **one isolated harness at a time**, then **fair baseline benchmarks**, then an **optional paid consensus comparison**. Resist adding a database, dashboard backend, orchestrator, or cloud services before evidence demonstrates a need.
