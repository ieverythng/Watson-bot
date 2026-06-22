# Watson Stack Phase 1/2 Validation — Harness + Context Sweep

**Date:** 2026-06-22  
**Scope:** Phase 1 benchmark harness, Lazarus live validation, and Phase 2 context sweep using current Q3 model before any Q2 experiment.  
**Model:** `D:\MODELS\Qwen3.6-27B-Q3_K_M.gguf`  
**Endpoint tested:** `http://172.24.16.1:8080/v1`  
**Headroom health:** `http://172.24.16.1:8787/health`

## Source roadmap grounding

The roadmap HTML screenshot called for:

- **Phase 1:** repeatable tests for throughput, context, Headroom, tool calls, and Discord end-to-end completion.
- **Phase 2:** test **80k / 96k / 112k / 128k** with current Q3 before trying Q2; accept only if tool fidelity and latency remain usable.
- **Lazarus:** validate mode-based recovery before larger swarms.

I also checked the ZeroTier/local-inference docs and scripts already in the repo, especially:

- `reports/recipes/speculative-decoding-setup.md`
- `reports/research/qwopus-testing-plan.md`
- `scripts/start-speculative-server.ps1`
- `scripts/start-lucebox-stack.ps1`
- `scripts/llama_benchmark_suite.py`
- `scripts/benchmark-runner.py`
- `scripts/lazarus.sh`

## Implemented artifacts

### Phase 1 harness

New script:

```bash
python3 scripts/watson-stack-harness.py \
  --base-url http://172.24.16.1:8080/v1 \
  --headroom-url http://172.24.16.1:8787/health \
  --contexts 0,2048,8192 \
  --label baseline-65k-reasoning-off
```

Checks performed:

- `/v1/models` endpoint health
- Headroom `/health`
- synthetic context runs with marker retention checks
- tool-fidelity prompt that must select `read_file` as strict JSON
- JSON + Markdown report output under `reports/benchmarks/`

### Phase 2 sweep wrapper

New script:

```bash
bash scripts/context-sweep-lazarus.sh --live \
  --contexts 80000,96000,112000,128000 \
  --fraction 0.03 \
  --max-tokens 64
```

The wrapper restarts via Lazarus for each configured context, confirms the model comes up, then runs the harness.

## Lazarus live test result

`bash scripts/lazarus.sh --mode stable --ctx 65536` initially exposed two real issues:

1. 65k startup often returns `503 Loading model` for longer than the original wait window.
2. `litellm` is not installed in WSL, so WSL-side LiteLLM launch cannot succeed here.

Fixes applied:

- Lazarus now treats `503 Loading model` as a loading state and waits longer.
- Lazarus now defaults to the known BeeLlama server path: `C:\Users\Admin\PROJECTS\beellama-server\llama-server.exe`.
- Lazarus now starts llama.cpp with `--reasoning off`; without this, Qwen burned output tokens as hidden reasoning and produced empty visible replies.
- If WSL `litellm` is missing, Lazarus now reports the proxy gap but still verifies direct llama.cpp chat completion instead of falsely failing the whole recovery.

Final live Lazarus result:

- llama.cpp restored successfully.
- Direct chat completion verified successfully.
- Current active context after sweep: `128000` confirmed from `/v1/models`.

## Baseline harness result at 65k

Report:

- `reports/benchmarks/watson-stack-harness-baseline-65k-reasoning-off-20260622_033712.md`

| Check | Result |
|---|---|
| `/v1/models` | pass |
| Headroom `/health` | pass |
| 0-token context | pass, 5.777s elapsed |
| 2k context | pass, markers retained, 40.977s elapsed |
| 8k context | pass, markers retained, 162.279s elapsed |
| Tool fidelity | pass, strict JSON selected `read_file` |

The earlier pre-fix baseline failed because `--reasoning off` was missing. After adding it, tool fidelity passed.

## Phase 2 configured-context sweep

Sweep summary:

- `reports/benchmarks/context-sweep-20260622_034109/summary.md`

| Configured context | `/v1/models` confirmed | Harness target | Result | Harness report |
|---:|---:|---:|---|---|
| 80,000 | yes | 2,400 | pass | `reports/benchmarks/watson-stack-harness-ctx80000-20260622_034348.md` |
| 96,000 | yes | 2,880 | pass | `reports/benchmarks/watson-stack-harness-ctx96000-20260622_034800.md` |
| 112,000 | yes | 3,360 | pass | `reports/benchmarks/watson-stack-harness-ctx112000-20260622_035218.md` |
| 128,000 | yes | 3,840 | pass | `reports/benchmarks/watson-stack-harness-ctx128000-20260622_035622.md` |

All four configured contexts came up with Lazarus and passed endpoint, Headroom, marker-retention, and tool-fidelity checks.

## Decode/latency observations

Raw sweep rows used a 3% prompt fraction so each larger configured context also received a slightly larger prompt. That means elapsed times are not pure apples-to-apples decode-speed comparisons, but they do validate usability under increasing prompt loads.

| Configured context | Harness target | Elapsed | Est visible completion tok/s | Tool fidelity |
|---:|---:|---:|---:|---|
| 80k | 2,400 | 51.410s | 0.856 | pass |
| 96k | 2,880 | 67.089s | 0.656 | pass |
| 112k | 3,360 | 88.522s | 0.497 | pass |
| 128k | 3,840 | 94.614s | 0.465 | pass |

Additional fixed-target check at active 128k:

- `reports/benchmarks/watson-stack-harness-ctx128000-fixed2400-20260622_040114.md`
- 128k configured context, 2,400-token harness target: **20.971s**, estimated **2.098 visible completion tok/s**, tool fidelity pass.

This suggests the 128k configuration is viable once warmed, and the raw sweep slowdown was partly prompt-size/warmup related rather than context configuration alone.

## Recommendation

**Keep the stack at 128k Q3 for now** if Juan wants maximum working context today. It passed the full configured-context sweep and is currently active at `n_ctx=128000`.

Caveats:

- WSL LiteLLM is missing (`litellm` command not found). Direct llama.cpp works; proxy recovery needs either WSL LiteLLM installed or Lazarus updated to restart the Windows-side ZeroTier LiteLLM proxy instead.
- The 80k/96k/112k/128k sweep used modest prompt fills. Before relying on 128k for giant single prompts, run a heavier overnight sweep at 25%, 50%, and 75% fill.
- Do **not** move to Q2 yet. Current Q3 at 128k is working; Q2 should only be tested if VRAM/RAM pressure forces it.

## Next best step

Build Phase 3 dashboard around the harness outputs:

- llama.cpp `n_ctx` from `/v1/models`
- Headroom `/health`
- Lazarus last-run status
- recent benchmark markdown/json report links
- Windows process/VRAM/RAM snapshot
- true Hermes/gateway state
