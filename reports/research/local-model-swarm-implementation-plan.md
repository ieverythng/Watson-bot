# Local Model Swarm Stack — Implementation Plan

**Date:** 2026-06-22  
**Status:** First implementation pass committed to repo  
**Scope:** Higher-context local inference, Lazarus recovery hardening, and prep for small local coding-model subagents.

## What I checked

Relevant plan/report lane files reviewed:

- `reports/research/gpt5-oracle-migration.html` — webchat2api is useful for GPT-Oracle text/research but cannot provide real custom tool calling.
- `reports/research/webchat2api-integration-seams.md` — custom function schemas are not reliable through webchat2api; Hermes tool use should stay in Hermes/local routing.
- `reports/recipes/speculative-decoding-setup.md` — existing DFlash plan for Qwen3.6 speculative decoding through llama.cpp.
- `reports/research/qwopus-testing-plan.md` — Qwopus VL benchmark plan and the important “one llama.cpp model at a time” constraint.
- `reports/research/lucebox-implementation-guide.md` — experimental fast backend path, but not the first safe step.

## Current local model inventory

The WSL-visible `D:/MODELS` scan currently finds:

| Candidate | Path | Role |
|---|---|---|
| Qwen3.6 27B Q3_K_M | `D:\MODELS\Qwen3.6-27B-Q3_K_M.gguf` | safest supervisor/front model |
| Qwen3.6 27B MTP pi tune Q3_K_M | `D:\MODELS\Qwen3.6-27B-MTP-pi-tune-Q3_K_M.gguf` | benchmark candidate |
| Qwen3.6 DFlash IQ4_XS | `D:\MODELS\Qwen3.6-27B-DFlash-IQ4_XS.gguf` | speculative draft, not standalone subagent |
| Qwopus VL 27B Q3_K_M | `D:\MODELS\Qwopus-VL-3.6-27B-Q3_K_M\Qwopus3.6-27B-v2-Q3_K_M.gguf` | vision/coding benchmark candidate |
| LFM2 8B A1B Q4_K_M | `D:\MODELS\LFM2-8B-A1B-Q4_K_M.gguf` | small-model candidate |
| LocateAnything Q8_0 | `D:\MODELS\locate-anything-q8_0.gguf` | perception/robotics, not coding |

No `vibecoder` or `gemma` GGUF was visible in `/mnt/d/MODELS` during this pass. The new inventory script makes that check repeatable instead of relying on memory.

## First implementation shipped

### 1. Hardened Lazarus recovery script

Updated `scripts/lazarus.sh` from a one-off stack resurrector into a safer, parameterized recovery tool:

```bash
bash scripts/lazarus.sh --dry-run
bash scripts/lazarus.sh --mode stable
bash scripts/lazarus.sh --mode spec --ctx 65536
```

Key changes:

- Adds `--dry-run`, `--skip-kill`, `--mode stable|spec`, model/path/context overrides.
- Uses WSL `powershell.exe` first to launch Windows `llama-server.exe`; SSH is fallback, not the primary path.
- Keeps cleanup scoped to LiteLLM/WSL inference ports instead of touching Hermes gateway/CLI processes.
- Creates the LiteLLM config directory before writing.
- Writes a proper OpenAI-compatible LiteLLM config with `/v1` upstream paths.
- Verifies `/v1/models` and then performs a real chat completion through LiteLLM.
- Logs every run to `memory/lazarus-YYYY-MM-DD_HHMMSS.log`.

### 2. Added deterministic model inventory script

New file: `scripts/local-model-inventory.py`

Examples:

```bash
python3 scripts/local-model-inventory.py
python3 scripts/local-model-inventory.py --json
python3 scripts/local-model-inventory.py --root /mnt/d/MODELS --out reports/research/local-model-inventory.md
```

This is the safe first primitive for a future local swarm: before spawning any local subagents, Watson can prove which GGUFs are actually available and which are draft/projector files.

## Recommended swarm architecture

Start boring and reliable:

```text
Hermes supervisor (Qwen3.6 27B or Gemma 14B if later present)
  ├─ worker-a: small coding GGUF on port 8081
  ├─ worker-b: small coding GGUF on port 8082
  ├─ optional worker-c/d only after memory/VRAM tests pass
  └─ convergence: supervisor summarizes/reconciles worker outputs
```

Important constraint: the current single llama.cpp server only runs one model at a time. A true four-worker local swarm needs either:

1. multiple `llama-server` processes on separate ports with small enough models to fit RAM/VRAM, or
2. serialized “virtual workers” where the same endpoint is prompted as different roles, or
3. a router/proxy that queues requests across multiple backends.

Given 16 GB RAM + 16 GB VRAM, option 2 is the safest immediate path. Option 1 becomes realistic if the Vibecoder/Gemma models are genuinely ~3B–4B quantized files.

## Next implementation step

Add `scripts/local-swarm-smoke.sh` that:

1. reads `scripts/local-model-inventory.py --json`,
2. selects up to two small candidate GGUFs under a size threshold,
3. starts them on `8081`/`8082` only in `--dry-run` first,
4. verifies `/v1/models`,
5. sends the same coding prompt to both,
6. sends both answers to the supervisor endpoint for convergence.

I would not jump straight to four workers until two-worker startup, memory pressure, and convergence are measured.
