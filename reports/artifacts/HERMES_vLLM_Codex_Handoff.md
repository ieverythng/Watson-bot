# Handoff: Migrate Hermes/Watson and iTrader proposer serving to vLLM

## Status
This handoff is for the next Codex pass.

The decision is to move the primary local inference-serving layer from `llama.cpp` to **vLLM** for Hermes/Watson first, while keeping the codebase provider-agnostic and preserving any currently working local paths until parity is confirmed.

This is an **inference-serving migration**, not a model-training rewrite.

---

# 1. Objectives

## Primary objective
Adopt **vLLM** as the local serving layer for Hermes/Watson so the agent stack gets:
- better throughput under concurrent sessions,
- one shared local API surface,
- cleaner multi-role serving,
- easier structured tool-calling / JSON generation,
- easier future routing across roles such as `WatsonMain`, `WatsonMemory`, `WatsonReviewer`, and `WatsonDev`.

## Secondary objective
Allow iTrader proposer traffic to optionally use the same local vLLM server through the existing OpenAI-compatible backend path, without tightly coupling iTrader to a single runtime.

## Non-goals
- Do not rewrite Hermes agent logic unnecessarily.
- Do not remove `llama.cpp` immediately if it is the current stable fallback.
- Do not change training algorithms in iTrader as part of this migration.
- Do not assume long-context slowdown is “solved” purely by switching engines.

---

# 2. Why vLLM

## Rationale
The move is primarily for:
- **high throughput**, especially under multiple simultaneous or overlapping requests,
- **multi-session handling**, where multiple Watson roles can share one loaded model,
- **OpenAI-compatible serving**, which simplifies integration and future provider swapping,
- better operational fit for agentic orchestration than direct per-process local runners.

## Important note
This migration is **not** based on the assumption that vLLM makes every single request dramatically faster.
The expected main gains are:
- server-side scheduling,
- shared model process,
- improved concurrency,
- simpler agent integration.

Long contexts will still be expensive. The serving change should be paired with tighter context discipline and stronger retrieval/memory usage.

---

# 3. Known repo alignment

The current iTrader repo already documents an OpenAI-compatible task-generation path for **vLLM or SGLang** on `:8000`, invoked through:
- `--backend vllm`
- `--api_base_url http://localhost:8000/v1`
- `--api_model <model>`

This means iTrader is already architecturally close to provider-agnostic HTTP inference for proposer generation.

Codex should preserve and extend that pattern rather than building a bespoke vLLM-only path.

---

# 4. Target serving topology

## 4.1 Core topology

```text
Hermes / Watson roles
  -> unified model client adapter
  -> local OpenAI-compatible endpoint
  -> vLLM server
  -> loaded model(s)

Optional:
iTrader proposer / MarketFramer
  -> same OpenAI-compatible endpoint
  -> same or separate vLLM server
```

## 4.2 Preferred rollout

### Phase 1
Use vLLM as the main serving layer for:
- `WatsonMain`
- `WatsonMemory`
- `WatsonReviewer`
- `WatsonDev` (if/when present)

### Phase 2
Point iTrader proposer / MarketFramer traffic to the same local endpoint **only if**:
- request patterns are compatible,
- model selection is appropriate,
- the combined workload does not destabilize latency.

### Phase 3
If needed, split into:
- one vLLM instance for Hermes/Watson,
- one vLLM instance for iTrader proposer workloads.

---

# 5. Architectural rule

## Hard rule
Hermes/Watson must not depend directly on `llama.cpp`-specific assumptions or flags.
All model interaction should go through a **provider adapter layer**.

## Desired interface
Introduce or formalize a model client abstraction that supports:
- `provider = llama_cpp | vllm | ollama | openai_compatible`
- same request contract for:
  - chat/completions,
  - structured JSON generation,
  - tool-call-oriented prompting,
  - streaming if already supported,
  - timeout / retries / cancellation,
  - system/user/tool message formatting.

This adapter should be the only layer Hermes uses.

---

# 6. Required implementation work

## Workstream A — provider abstraction hardening

### Goal
Make Hermes inference provider-agnostic.

### Tasks
1. Identify all places where Hermes/Watson currently assumes `llama.cpp` process semantics, flags, paths, or prompt formatting.
2. Centralize model invocation behind a single adapter.
3. Ensure the adapter can target an OpenAI-compatible base URL.
4. Preserve current `llama.cpp` path as fallback while vLLM is being validated.

### Acceptance criteria
- Hermes roles can switch providers via config only.
- No role-specific code directly shells into `llama.cpp` unless through a provider adapter.
- Structured JSON requests still work.

---

## Workstream B — vLLM server profile

### Goal
Create a reproducible local vLLM server setup.

### Tasks
1. Add a documented launch profile for vLLM.
2. Support one or more model profiles, including a practical default.
3. Add environment/config variables for:
   - base URL,
   - model name,
   - API key/token,
   - max context,
   - timeout,
   - generation defaults.
4. Ensure the client layer supports OpenAI-style calls to `http://localhost:8000/v1`.
5. Explicitly decide whether model-side defaults should be overridden or inherited.

### Important note
vLLM applies `generation_config.json` from the Hugging Face model repo by default if one exists. Provide an explicit configuration decision around this rather than leaving it implicit.

### Acceptance criteria
- One command or script starts the local vLLM server.
- Hermes can hit it successfully.
- Base URL and model are configurable.

---

## Workstream C — Hermes role migration

### Goal
Move Watson roles from local-runner-specific behavior to shared-server inference.

### Tasks
1. Migrate `WatsonMain` first.
2. Then migrate `WatsonMemory` and `WatsonReviewer`.
3. Add per-role model config support if needed.
4. Ensure simultaneous requests do not break role behavior.
5. Add logging around:
   - request start/end,
   - time to first token if measurable,
   - total latency,
   - token counts if available,
   - JSON/tool-call success/failure.

### Acceptance criteria
- Multiple roles can call one vLLM server.
- Tool usage and structured outputs remain stable or improve.
- No regression in standard Watson workflows.

---

## Workstream D — iTrader proposer compatibility

### Goal
Make sure iTrader can optionally reuse the same vLLM server cleanly.

### Tasks
1. Preserve current proposer backend pattern that already supports `vllm` / OpenAI-compatible serving.
2. Ensure config can point proposer traffic to the local vLLM endpoint.
3. Validate task generation parity versus current serving path.
4. Keep fallback backends intact.

### Acceptance criteria
- Existing iTrader task-generation commands still work.
- vLLM-backed proposer generation works through config, not code forks.

---

## Workstream E — benchmarking and validation

### Goal
Measure actual practical gains.

### Metrics to capture
For Hermes:
- total latency,
- concurrency behavior,
- stability under multiple sessions,
- JSON reliability,
- tool-call reliability,
- throughput under overlapping role requests.

For iTrader proposer:
- task generation latency,
- JSON validity rate,
- validation/clamping failure rate,
- behavior under repeated batch generation.

### Important note
Do not judge the migration on raw tok/s alone.
Include:
- time to first useful response,
- end-to-end task completion time,
- multi-session degradation,
- memory pressure,
- long-context slowdown.

### Acceptance criteria
- Benchmark artifact or markdown summary exists.
- We can compare `llama.cpp` and `vLLM` on real workloads.

---

# 7. Recommended configuration strategy

## 7.1 Config shape
Introduce or extend config so the provider can be swapped without code edits.

Illustrative shape:

```yaml
inference:
  provider: vllm
  base_url: http://localhost:8000/v1
  api_key_env: VLLM_API_KEY
  model: Qwen/Qwen3.5-9B
  timeout_s: 120
  max_context: 16384
  structured_json_mode: true
  retries: 2
  backoff_s: 1.5
```

## 7.2 Model routing
If Hermes uses multiple roles, allow config like:

```yaml
roles:
  WatsonMain:
    model: <default>
  WatsonMemory:
    model: <same-or-smaller>
  WatsonReviewer:
    model: <same-or-other>
  WatsonDev:
    model: <optional>
```

This routing should be optional; simplest first version can use one shared model.

---

# 8. Context policy

## Hard recommendation
Do not rely on very large live contexts by default.

### Preferred pattern
- shorter active context,
- retrieval/memory summaries,
- explicit compression of old sessions,
- large contexts only when necessary.

### Reason
The current known behavior strongly suggests that long-context cost is a major bottleneck regardless of serving layer.

Codex should not try to “solve” long-context degradation only by changing engines.
Context budgeting must remain part of the system design.

---

# 9. Coding harness integration inside Hermes

## Goal
Enable Hermes to use an external coding harness reliably for repo work.

## Key decision
Do **not** make Hermes spawn a fully interactive coding CLI in an ad hoc way and hope it behaves well.
That is brittle.

## Recommended pattern
Treat the coding harness as a **supervised tool adapter** with:
- a working directory,
- a prompt file or prompt string,
- a timeout,
- a mode flag,
- captured stdout/stderr,
- structured result parsing,
- optional git worktree isolation.

### In other words
Instead of:
- “Hermes tries to open an interactive sub-agent shell and improvise”

Use:
- “Hermes calls a deterministic wrapper script that launches the coding harness in a controlled way.”

---

# 10. Recommended harness choice

## Best choice: Codex CLI
This is the preferred first integration target.

### Why
- It is available through OpenAI’s current Codex ecosystem.
- It supports local terminal usage.
- It has approval modes.
- It can be accessed through ChatGPT-linked sign-in flows rather than forcing a separate Anthropic account.
- It is the most natural fit for your existing setup.

## Not preferred first
### Claude Code
Not the best first option here because you do not currently have an Anthropic API key and Anthropic documents Claude Code as using Anthropic’s API by default.

### Cursor CLI
Possible, but less attractive as the first automation harness if the goal is low-friction “already available” integration.
It supports browser auth and API-key auth, but it is better treated as an optional secondary harness, not the first one to operationalize.

---

# 11. Harness integration standard

## 11.1 Introduce a `DevHarnessAdapter`
Codex should add a thin abstraction for coding tools.

Supported target harnesses should ideally be:
- `codex_cli`
- `cursor_cli` (optional later)
- `claude_code` (optional later)

## 11.2 Unified invocation contract
Illustrative interface:

```python
run_dev_harness(
    harness: str,
    repo_path: str,
    prompt: str,
    mode: str = "suggest",
    timeout_s: int = 900,
    allow_write: bool = False,
    allow_shell: bool = False,
    worktree: str | None = None,
) -> HarnessRunResult
```

## 11.3 Result object should capture
- exit status,
- stdout,
- stderr,
- changed files if detectable,
- diff path or patch output if produced,
- runtime,
- timeout flag.

## 11.4 First implementation target
Implement `codex_cli` first.

### Suggested modes mapping
- `suggest`
- `auto_edit`
- `full_auto` only with explicit guardrails and sandbox awareness

## 11.5 Guardrails
- always run in a specified repo/worktree,
- default to no network unless intentionally needed,
- enforce timeouts,
- capture logs,
- require git status before and after,
- do not allow silent background hangs.

---

# 12. Best practical way to integrate Codex CLI into Hermes

## Recommended architecture

```text
Hermes / WatsonDev
  -> DevHarnessAdapter
  -> codex_wrapper.sh / python wrapper
  -> Codex CLI in controlled mode
  -> output parsed back into Hermes
```

## Why this is best
- avoids fragile interactive nesting,
- makes runs reproducible,
- gives Hermes deterministic inputs/outputs,
- makes timeout/retry handling possible,
- supports later replacement with Cursor CLI if desired.

## Do not do this first
- direct interactive shell nesting,
- pseudo-terminal improvisation without structure,
- allowing Hermes to spawn arbitrary coding CLIs without wrapper constraints.

---

# 13. Proposed implementation order

1. formalize Hermes inference adapter
2. add vLLM server profile and config
3. migrate `WatsonMain` to vLLM
4. migrate other Watson roles
5. benchmark concurrency / latency / structured JSON quality
6. confirm iTrader proposer can reuse the same endpoint cleanly
7. add `DevHarnessAdapter`
8. integrate `codex_cli` through a wrapper
9. optionally add Cursor CLI later
10. only consider Claude Code later if Anthropic access becomes available

---

# 14. Deliverables expected from Codex

## Deliverable A
A markdown doc under `docs/` describing:
- vLLM serving topology,
- environment variables,
- launch commands,
- migration notes,
- rollback path to `llama.cpp`.

## Deliverable B
A provider adapter or equivalent abstraction for Hermes inference.

## Deliverable C
A reproducible local vLLM launch script or command profile.

## Deliverable D
A benchmark script or benchmark notes comparing old and new serving paths on real Hermes workloads.

## Deliverable E
A `DevHarnessAdapter` with `codex_cli` support and a controlled wrapper script.

---

# 15. Definition of done

This migration pass is complete when:

1. Hermes/Watson can use vLLM through a shared local OpenAI-compatible endpoint.
2. Multiple Watson roles can hit the same serving layer reliably.
3. Tool-calling / structured JSON is at least as stable as before.
4. iTrader proposer can optionally use the same endpoint without bespoke branching.
5. A controlled Codex CLI wrapper exists for Hermes-driven coding tasks.
6. There is a documented fallback path to `llama.cpp` if needed.
7. Benchmark notes exist for real usage, not just raw tok/s.

---

# 16. Important final instruction to Codex

Preserve working behavior first.
This should be implemented as a clean serving and tooling evolution, not as a disruptive rewrite.

Focus on:
- shared API serving,
- concurrency robustness,
- provider abstraction,
- controlled coding-harness integration,
- replayable and debuggable behavior.

