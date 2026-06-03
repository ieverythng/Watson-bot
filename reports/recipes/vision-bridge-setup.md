# Vision Bridge Setup — Image Support for Codex CLI

**Domain:** Infrastructure  
**Status:** Active  
**Last Updated:** 2026-06-03

## Overview

The Vision Bridge is a FastAPI proxy that enables image support for Codex CLI when using llama.cpp (which does not natively support images). It intercepts `/v1/responses` requests, describes any attached images via gpt-5.4-mini (Codex OAuth), replaces image content with text descriptions, and forwards the cleaned request to LiteLLM → llama.cpp.

## Architecture

```
Codex CLI → Vision Bridge :8002 (Linux) → LiteLLM :4000 (Windows) → llama.cpp :8080
```

## Prerequisites

- Hermes venv at `~/.hermes/hermes-agent/venv`
- Codex OAuth token configured in Hermes (`hermes auth codex`)
- LiteLLM proxy running on Windows PC at `10.88.140.94:4000`
- llama.cpp server running on Windows PC at `localhost:8080`

## Setup Steps

### 1. Start the Vision Bridge

```bash
cd /home/juanbeck/.hermes/hermes-agent \
  && source venv/bin/activate \
  && HERMES_HOME=/home/juanbeck/.hermes \
     python3 /home/juanbeck/Watson/scripts/vision-bridge/vision_bridge.py
```

The bridge listens on `0.0.0.0:8002`.

### 2. Verify Health

```bash
curl -s http://localhost:8002/health | python3 -m json.tool
```

Expected output:
```json
{
  "status": "ok",
  "upstream": "http://10.88.140.94:4000/v1",
  "local_model": "qwen36-turbo-hermes",
  "vision_model": "gpt-5.4-mini"
}
```

### 3. Point Codex CLI at the Vision Bridge

**Critical:** Update `~/.codex/config.toml` to point at port `8002`, NOT directly at LiteLLM or llama.cpp:

```toml
# ~/.codex/config.toml
openai_base_url = "http://127.0.0.1:8002/v1"
model = "qwen36-turbo-hermes"
```

⚠️ If Codex points directly to llama.cpp (`172.24.16.1:8080`) or LiteLLM (`10.88.140.94:4000`), images will fail with "image input not supported" and Codex will disconnect/reconnect.

### 4. Test with an Image

In Codex CLI, send a message with an attached image. The bridge should describe it via gpt-5.4-mini and forward to llama.cpp. You should see the model respond normally instead of disconnecting.

## Keeping It Running

The vision bridge is a long-running server. Options:

1. **Background process** — run in tmux/screen or via Hermes background terminal
2. **Systemd service** — create a unit file for auto-start
3. **Hermes cronjob** — schedule periodic restarts if it crashes

Quick tmux approach:
```bash
tmux new -s vision-bridge 'cd /home/juanbeck/.hermes/hermes-agent && source venv/bin/activate && HERMES_HOME=/home/juanbeck/.hermes python3 /home/juanbeck/Watson/scripts/vision-bridge/vision_bridge.py'
```

## Troubleshooting

### Port 8002 already in use

Kill the old process first:
```bash
lsof -i :8002 | grep LISTEN | awk '{print $2}' | xargs -r kill -9
```

### No Codex OAuth token

The bridge needs a valid Codex OAuth token to call gpt-5.4-mini. Ensure Hermes auth is configured: `hermes auth codex`

### Upstream unreachable

If LiteLLM at `10.88.140.94:4000` is down, the bridge will fail to forward requests. Verify with:
```bash
curl http://10.88.140.94:4000/v1/models
```

### Bridge crashes (SIGKILL/137)

The bridge has been known to crash. Monitor and restart. Consider a watchdog script or systemd service for reliability.

### 400 Bad Request from upstream

Occasional 400 errors from LiteLLM on `/v1/responses` calls. Usually transient — the bridge retries automatically. If persistent, check LiteLLM logs on Windows PC.

## Known Issues

- `on_event` deprecation warning in FastAPI (cosmetic, does not affect functionality)
- Bridge crashes (SIGKILL/137) — monitor and restart as needed
- Occasional 400 from upstream LiteLLM proxy
