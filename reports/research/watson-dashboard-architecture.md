# Watson Ecosystem Dashboard — Architecture Plan

## Overview

A web-based monitoring dashboard accessible via ZeroTier network, providing real-time visibility into the entire Watson ecosystem: GPU metrics, agent status, LLM server health, proxy stats, and project tracking.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ZERO TIER NETWORK (3b19b3a7)                    │
│                                                                     │
│  ┌──────────────────┐         ┌──────────────────┐                  │
│  │   Windows PC     │         │    WSL/Linux VM   │                  │
│  │  (10.88.140.94)  │◄───────►│  (10.88.140.135) │                  │
│  │                  │         │                  │                  │
│  │ ┌────────────┐   │         │ ┌────────────┐   │                  │
│  │ │ llama.cpp  │   │         │ │ Dashboard  │   │                  │
│  │ │ :8080/v1   │   │         │ │ :3000      │   │                  │
│  │ └────────────┘   │         │ └────────────┘   │                  │
│  │                  │         │                  │                  │
│  │ ┌────────────┐   │         │ ┌────────────┐   │                  │
│  │ │ LiteLLM    │   │         │ │ Hermes     │   │                  │
│  │ │ :4000      │───┼────────►│ │ Gateway    │   │                  │
│  │ │ (llm proxy)│   │         │ │ :8001      │   │                  │
│  │ └────────────┘   │         │ └────────────┘   │                  │
│  │                  │         │                  │                  │
│  │ ┌────────────┐   │         │ ┌────────────┐   │                  │
│  │ │ CLIProxyAPI│   │         │ │ WatsonOW   │   │                  │
│  │ │ :8317      │───┼────────►│ │ Workspace  │   │                  │
│  │ │ (ChatGPT+) │   │         │ └────────────┘   │                  │
│  │ └────────────┘   │         │                  │                  │
│  └──────────────────┘         └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
- **Framework:** React + Vite (lightweight, fast HMR)
- **UI Library:** Tailwind CSS + shadcn/ui components
- **Charts:** Recharts or lightweight SVG charts for GPU metrics
- **Real-time:** Server-Sent Events (SSE) or WebSocket for live updates
- **Icons:** Lucide React

### Backend
- **Runtime:** Python FastAPI (async, lightweight, native SSE support)
- **Data Collection:** Custom collectors per component
- **State:** In-memory with optional SQLite persistence for history
- **Auth:** Simple API key or ZeroTier IP-based trust

### Deployment
- **Host:** WSL/Linux VM (same machine as Hermes)
- **Port:** 3000 (frontend), 8000 (FastAPI backend)
- **Access:** ZeroTier network only (10.88.x.x subnet)
- **Process:** systemd service or s6-supervised

---

## Dashboard Panels

### 1. GPU Metrics Panel
```
┌──────────────────────────────────────────────┐
│  NVIDIA GPU STATUS                           │
├──────────────────────────────────────────────┤
│  GPU: NVIDIA GeForce RTX XXXX                │
│  ┌─────────────┐ ┌─────────────┐            │
│  │ Temperature │ │ Utilization │            │
│  │    62°C     │ │    78%      │ [bar]     │
│  └─────────────┘ └─────────────┘            │
│  Memory: 6.2 / 8.0 GB ████████░░ 77%        │
│  Power: 145W / 170W                          │
│  Fans: 1800 RPM                              │
│  ─────────────────────────────────────────── │
│  Recent activity (last hour):                │
│  [sparkline chart showing GPU utilization]   │
└──────────────────────────────────────────────┘
```

**Data source:** `nvidia-smi` via subprocess, polled every 5s
**Collector script:** Python script calling `nvidia-smi --query-gpu=... --format=csv`

### 2. Agent Status Panel
```
┌──────────────────────────────────────────────┐
│  AGENT FLEET                                  │
├──────────────────────────────────────────────┤
│  Watson Main    ● ONLINE  (qwen36-turbo)     │
│  WatsonDev      ● READY   (gpt-5.4-mini)     │
│  WatsonPlus     ● READY   (gpt-5.5)          │
│  WatsonCodex    ● READY   (codex-auto-review)│
├──────────────────────────────────────────────┤
│  Active delegations: 0                        │
│  Last activity: 2 min ago                     │
│  Total sessions today: 12                     │
└──────────────────────────────────────────────┘
```

**Data source:** Hermes gateway API + profile config inspection
**Polling:** Every 30s

### 3. LLM Server Health Panel
```
┌──────────────────────────────────────────────┐
│  LLM SERVERS                                  │
├──────────────────────────────────────────────┤
│  llama.cpp (Windows)    ● UP   :8080         │
│    Model: qwen3.6-27b                                    │
│    Prompt cache: 45% hit rate                        │
│    Avg latency: 120ms/token                              │
│                                                     │
│  LiteLLM Proxy        ● UP   :4000         │
│    Routing to: llama.cpp localhost:8080              │
│                                                     │
│  CLIProxyAPI          ● UP   :8317         │
│    Models: 6 (gpt-5.5, gpt-5.4, gpt-5.4-mini...) │
│    Auth: codex-general@yourgamma.com-plus.json     │
│    Requests today: 47                                    │
└──────────────────────────────────────────────┘
```

**Data sources:**
- llama.cpp: HTTP health check to `http://172.24.16.1:8080/v1/models`
- LiteLLM: Health check to `http://10.88.140.94:4000/v1/models`
- CLIProxyAPI: Health check to `http://127.0.0.1:8317/healthz`

### 4. ZeroTier Network Panel
```
┌──────────────────────────────────────────────┐
│  ZERO TIER NETWORK                            │
├──────────────────────────────────────────────┤
│  Network: my-first-network (3b19b3a7)        │
│  My IP: 10.88.140.135                        │
│  ─────────────────────────────────────────── │
│  Connected peers:                            │
│  Windows PC    10.88.140.94   ● ONLINE       │
│  [other devices as connected]                │
└──────────────────────────────────────────────┘
```

**Data source:** `zerotier-cli listpeers` + `zerotier-cli get /network/...`

### 5. Project Tracker Panel
```
┌──────────────────────────────────────────────┐
│  PROJECTS                                      │
├──────────────────────────────────────────────┤
│  iChess-Sim       ████████░░ 80%  Phase 1-2 done   │
│  iTrack Supply    ██████░░░░ 60%  Gamma insights   │
│  Watson-bot       ████░░░░░░ 40%  Foundations      │
└──────────────────────────────────────────────┘
```

**Data source:** Static config + git commit activity tracking

---

## Data Collection Architecture

### Collector Service (Python/FastAPI)

```python
# collectors/gpu.py
import subprocess
import asyncio

async def collect_gpu_metrics():
    result = await asyncio.create_subprocess_exec(
        "nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu,"
        "memory.used,memory.total,power.draw,fan.speed",
        "--format=csv,noheader,nounits",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await result.communicate()
    return parse_nvidia_smi(stdout.decode())

# collectors/llm_servers.py
import httpx

async def check_llm_server(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{url}/v1/models")
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                return {"status": "up", "models": len(models)}
            return {"status": "degraded", "code": resp.status_code}
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"status": "down"}

# collectors/zerotier.py
import subprocess

async def collect_zerotier_status():
    result = await asyncio.create_subprocess_exec(
        "zerotier-cli", "listpeers",
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await result.communicate()
    return parse_zerotier_peers(stdout.decode())
```

### SSE Endpoint for Real-time Updates

```python
# main.py
from fastapi import FastAPI
from sse_starlette import EventSourceResponse

app = FastAPI()

@app.get("/api/stream")
async def metrics_stream():
    async def event_generator():
        while True:
            data = {
                "gpu": await collect_gpu_metrics(),
                "llm_servers": await check_all_servers(),
                "zerotier": await collect_zerotier_status(),
                "agents": await get_agent_status(),
            }
            yield {"event": "metrics", "data": json.dumps(data)}
            await asyncio.sleep(5)  # 5-second polling interval
    return EventSourceResponse(event_generator())
```

---

## File Structure

```
src/dashboard/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── collectors/
│   │   ├── gpu.py              # nvidia-smi collector
│   │   ├── llm_servers.py      # Health checks for all LLM endpoints
│   │   ├── zerotier.py          # ZeroTier network status
│   │   └── agents.py            # Hermes agent status
│   ├── templates/
│   │   └── index.html           # SPA shell (loads React build)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main dashboard layout
│   │   ├── components/
│   │   │   ├── GpuPanel.tsx     # GPU metrics panel
│   │   │   ├── AgentPanel.tsx   # Agent fleet status
│   │   │   ├── ServerPanel.tsx  # LLM server health
│   │   │   ├── NetworkPanel.tsx # ZeroTier network
│   │   │   └── ProjectPanel.tsx # Project tracker
│   │   ├── hooks/
│   │   │   └── useMetrics.ts    # SSE connection hook
│   │   └── utils/
│   │       └── format.ts        # Metric formatting helpers
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── Dockerfile                   # Optional containerized deploy
└── docker-compose.yml           # For local dev
```

---

## Deployment Options

### Option A: Direct Process (Simplest)
- Run FastAPI backend on port 8000 via systemd/s6
- Build React SPA, serve static files from FastAPI
- Access via `http://10.88.140.135:8000` from ZeroTier network

### Option B: Reverse Proxy (Production)
- Nginx/Caddy reverse proxy on WSL
- HTTPS via self-signed cert for ZeroTier network
- Single port access: `https://watson-dashboard.local:443`

### Option C: Containerized
- Docker Compose with backend + pre-built frontend
- Isolated, portable, easy restart
- Volume mounts for config/logs

**Recommendation:** Start with Option A for rapid development, migrate to B once stable.

---

## Implementation Phases

### Phase 1: MVP (1-2 hours)
- [x] Architecture doc ✓
- [ ] FastAPI backend skeleton with GPU collector
- [ ] Basic HTML dashboard (no React yet — just a clean template)
- [ ] SSE stream for live GPU metrics
- [ ] Deploy on WSL, test via ZeroTier

### Phase 2: Full Dashboard (3-4 hours)
- [ ] All 5 panels implemented
- [ ] React SPA with proper component architecture
- [ ] Historical sparklines for GPU metrics
- [ ] Agent status integration with Hermes

### Phase 3: Polish (2-3 hours)
- [ ] Dark theme matching WatsonOW aesthetic
- [ ] Alert thresholds (GPU temp > 80°C, server down)
- [ ] Project tracker with git activity integration
- [ ] Mobile-responsive layout

---

## Key Design Decisions

1. **Python backend over Node.js** — matches Hermes toolchain, easier GPU collection via subprocess
2. **SSE over WebSocket** — simpler implementation, unidirectional push is all we need
3. **No database for MVP** — in-memory state is sufficient; add SQLite later for history
4. **ZeroTier-only access** — no public exposure, trust the network boundary
5. **React SPA** — component-based architecture scales well as panels grow

---

## Integration with WatsonOW

The dashboard will live at `src/dashboard/` in the Watson-bot monorepo:

```
Watson-bot/
├── src/
│   ├── CLIProxyAPI/
│   ├── zerotier-llm-proxy/
│   ├── iChess-Sim/
│   ├── iTrack-Supply-Chain/
│   └── dashboard/          ← new addition
└── reports/research/watson-dashboard-architecture.md  ← this doc
```

The dashboard serves as the central observability layer for the entire Watson ecosystem — visible from any ZeroTier-connected device.
