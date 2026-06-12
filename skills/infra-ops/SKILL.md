# Infrastructure Operations

Manage and troubleshoot the WatsonOW inference infrastructure: CLIProxyAPI (ChatGPT Plus proxy), ZeroTier LLM proxy (LiteLLM → llama.cpp), and local model serving.

## Triggers

- "CLIProxyAPI not running" / "restart CLIProxyAPI" / "cliproxyapi down"
- "ZeroTier proxy" / "LiteLLM" / "llama.cpp not responding"
- "Infrastructure health check" / "check inference stack"
- "Model routing" / "delegation failing" / "subagent routing"
- "Vision bridge" / "port 8002"

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Hermes Agent (Watson)                     │
│                                                               │
│  Front model: qwen36-turbo-hermes via watson-llama provider  │
│    → http://172.24.16.1:8080/v1  (llama.cpp on Windows PC)   │
│                                                               │
│  Delegation: gpt-5.5 via chatgpt-plus provider               │
│    → http://127.0.0.1:8317/v1  (CLIProxyAPI on WSL)          │
│                                                               │
│  Vision: gpt-5.4-mini via openai-codex provider              │
│    → OpenAI Codex OAuth (built-in Hermes)                     │
│                                                               │
│  ZeroTier route: qwen36-turbo-hermes via LiteLLM proxy       │
│    → http://10.88.140.94:4000/v1  (LiteLLM on Windows PC)   │
│    → http://127.0.0.1:8080/v1  (llama.cpp on Windows PC)     │
└─────────────────────────────────────────────────────────────┘
```

## Key Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| llama.cpp | `http://172.24.16.1:8080/v1` | Local inference (Windows PC) |
| CLIProxyAPI | `http://127.0.0.1:8317/v1` | ChatGPT Plus proxy (WSL) |
| LiteLLM proxy | `http://10.88.140.94:4000/v1` | ZeroTier cross-device access |
| Vision Bridge | `http://127.0.0.1:8002/v1` | Image → text descriptions |

## CLIProxyAPI

### Location & Config

- **Repo:** `/home/juanbeck/CLIProxyAPI/`
- **Binary (repo):** `/home/juanbeck/CLIProxyAPI/cli-proxy-api`
- **Binary (PATH):** `~/.local/bin/cliproxyapi`
- **Config:** `/home/juanbeck/CLIProxyAPI/config.yaml`
- **Auth dir:** `~/.cli-proxy-api/`
- **Port:** 8317

### Start/Stop/Check

```bash
# Check if running
curl -s http://127.0.0.1:8317/v1/models | python3 -m json.tool

# List available models (requires auth)
curl -s -H "Authorization: Bearer watson-chatgpt-key" \
  http://127.0.0.1:8317/v1/models | python3 -m json.tool

# Start (from repo directory)
cd /home/juanbeck/CLIProxyAPI && ./cli-proxy-api --config config.yaml &

# Or via PATH binary
cliproxyapi serve --config /home/juanbeck/CLIProxyAPI/config.yaml &

# Check process
ps aux | grep cli-proxy-api | grep -v grep

# Stop
pkill -f "cli-proxy-api"
```

### Available Models (via CLIProxyAPI)

- `gpt-5.5` — premium reasoning (default delegation model)
- `gpt-5.4` — general purpose
- `gpt-5.4-mini` — lightweight
- `gpt-5.3-codex-spark` — Codex lightweight
- `codex-auto-review` — code review
- `gpt-image-2` — image generation

### Config Model Mappings

The config.yaml codex.models section maps Hermes model names to ChatGPT models:

```yaml
codex:
  models:
    - name: "chatgpt-4o"
      alias: "gpt-4o"
    - name: "chatgpt-o3-pro"
      alias: "o3-pro"
    - name: "chatgpt-o4"
      alias: "o4"
    - name: "chatgpt-gpt-5.5"
      alias: "gpt-5.5"
```

To add a new model, append to the models list. The `alias` is what Hermes requests; the `name` is what CLIProxyAPI maps to internally.

### Common Issues

**Usage limit reached:**
- Error: `"usage_limit_reached"` / `"All credentials for model gpt-5.5 are cooling down"`
- ChatGPT Plus has rate limits (~100 messages/3h on GPT-5). CLIProxyAPI does not bypass these.
- Fix: Wait for cooldown reset (error response includes `resets_in_seconds`).

**Connection refused:**
- CLIProxyAPI is not running. Start it per the commands above.
- Check `ps aux | grep cli-proxy-api` to confirm.

**502 Bad Gateway:**
- Hermes is routing a model that CLIProxyAPI doesn't serve (e.g., `qwen36-turbo-hermes`).
- Fix: Use an explicit CLIProxyAPI model (`-m gpt-5.5`) or switch provider to `watson-llama`.

## ZeroTier LLM Proxy

### Network Details

- **Network:** `my-first-network` (ID: `3b19b3a716937e29`)
- **Windows PC ZT IP:** `10.88.140.94`
- **Linux ZT IP:** `10.88.140.135`

### LiteLLM Proxy (Windows PC)

- Runs on Windows PC alongside llama.cpp
- Binds to `0.0.0.0:4000`, accessible via ZeroTier at `10.88.140.94:4000`
- Translates Chat Completions → llama.cpp
- Config: `~/.litellm/config.yaml` on Windows

### llama.cpp (Windows PC)

- Serves `qwen36-turbo-hermes` on localhost:8080
- Accessible via ZeroTier through LiteLLM at `10.88.140.94:4000`
- Stateless — each request is independent, no cross-contamination between clients

### Hermes Provider Config

```yaml
custom_providers:
  watson-llama:
    base_url: http://172.24.16.1:8080/v1
    api_key: placeholder
    api_mode: chat_completions
```

### Known Issues

- **Wire API must be `chat_completions`** — llama.cpp does not support Responses API
- **Vision not supported on local model** — text-only GGUF. Hermes uses auxiliary vision (gpt-5.4-mini via Codex OAuth)
- **LiteLLM timeout** — set `request_timeout: 600` for 65k context models
- **Logs:** `/mnt/c/Users/Admin/PROJECTS/zerotier-llm-proxy/litellm.err.log` and `.out.log`

## Vision Bridge

- **Port:** 8002
- **Purpose:** Describes images via gpt-5.4-mini, feeds text to local model
- **Health check:** `curl -s http://localhost:8002/health`
- **Known issue:** Crashes (SIGKILL/137) — OOM or external termination. Restart if down.

## Delegation Routing

Hermes delegation is configured in `~/.hermes/config.yaml`:

```yaml
delegation:
  model: gpt-5.5
  provider: chatgpt-plus
```

Subagents route through CLIProxyAPI → ChatGPT Plus backend. Verify routing by checking subagent error messages — they should reference "provider codex" (CLIProxyAPI's internal name), not the local llama.cpp endpoint.

## Health Check Script

```bash
# Full infrastructure check
echo "=== llama.cpp ===" && curl -s http://172.24.16.1:8080/v1/models | python3 -m json.tool
echo "=== CLIProxyAPI ===" && curl -s -H "Authorization: Bearer watson-chatgpt-key" http://127.0.0.1:8317/v1/models | python3 -m json.tool
echo "=== Vision Bridge ===" && curl -s http://localhost:8002/health
echo "=== ZeroTier ===" && ping -c 1 10.88.140.94
```

## Files

- CLIProxyAPI config: `/home/juanbeck/CLIProxyAPI/config.yaml`
- Hermes config: `~/.hermes/config.yaml`
- Status report: `Watson/reports/research/cliproxyapi-status-jun2026.html`
- ZeroTier bootstrap: `Watson/reports/research/zerotier-llm-bootstrap.html`
- ZeroTier architecture: `Watson/reports/research/zerotier-llm-architecture.html`
- GitHub fork: https://github.com/ieverythng/CLIProxyAPI
- GitHub zerotier repo: https://github.com/ieverythng/zerotier-llm-proxy
