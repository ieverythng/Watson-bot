# Hermes Migration Blueprint
Date: 2026-03-28
Scope: Watson workspace + Hermes install
Status: phase 1 and part of phase 2 completed

## Goal
Migrate Watson from the legacy OpenClaw-centered harness into Hermes Agent without polluting Hermes memory, recreating brittle OpenClaw complexity, or losing the valuable parts of the Watson workspace.

## Core Decision
Do not bulk-import `/home/juanbeck/Watson` into Hermes memory.

Use a 3-layer model instead:
1. Hermes native memory for tiny durable facts and user preferences
2. `/home/juanbeck/Watson` as the canonical external Watson knowledge/workspace repo
3. A migration bridge made of docs, scripts, cron jobs, and skills describing what to consult, what to promote, and what to ignore

## Current Validated State

### Legacy Watson workspace
Validated path:
- `/home/juanbeck/Watson`

Key files inspected:
- `AGENTS.md`
- `TOOLS.md`
- `MEMORY.md`
- `USER.md`
- `SOUL.md`
- `HEARTBEAT.md`
- `reports/recipes/01-om-loop.md`
- `reports/recipes/04-openclaw-runtime-alignment.md`
- `cron/memory-sweep-job.json`
- `cron/immediate-memory-sweep.json`
- `scripts/token_tracker.py`
- `scripts/om/observer-worker.sh`
- `scripts/om/retriever-worker.sh`
- `skills/memory-observer/SKILL.md`
- `skills/memory-reflector/SKILL.md`

Useful abstractions worth preserving:
- memory lanes
- deterministic retrieval first, deeper retrieval second
- role-owned durable memory writes
- transcript garbage kept out of core memory
- cheap router / strong executor split
- auditability and cost awareness

### Hermes install
Validated paths:
- config: `/home/juanbeck/.hermes/config.yaml`
- memories: `/home/juanbeck/.hermes/memories/`
- repo: `/home/juanbeck/.hermes/hermes-agent`
- git remote: `https://github.com/NousResearch/hermes-agent.git`

Validated capabilities:
- memory
- session_search
- delegate_task
- cronjob
- browser
- terminal
- file tools
- code execution
- todo
- TTS/STT

## Model Routing Decision

### Validated Ollama endpoints
Observed from this environment:
- `http://127.0.0.1:11434` -> `gpt-oss:20b-cloud`
- `http://172.24.16.1:11434` -> `qwen3.5:9b`, `gpt-oss:20b`

Conclusion:
- Windows Ollama is the correct endpoint for the intended local orchestrator model.
- The local-main strategy should target the Windows endpoint, not the WSL-local Ollama daemon.

### Hermes config change applied
Hermes default model was switched to:
- model: `qwen3.5:9b`
- provider: `custom`
- base_url: `http://172.24.16.1:11434/v1`

Hermes delegation defaults were set to:
- model: `gpt-5.4`
- provider: `openai-codex`
- base_url: `https://chatgpt.com/backend-api/codex`

Why:
- local model handles main routing/planning cheaply
- delegated subagents stay strong for coding/review/heavy execution

Validation performed:
- `hermes chat -q "Reply with exactly LOCAL_OK." -m qwen3.5:9b`
- result: success

## Hermes-Era Watson Role Mapping

### WatsonMain
Implementation in Hermes:
- primary Hermes session
- default model: local Windows Ollama (`qwen3.5:9b` for now)
- responsibilities:
  - user-facing orchestration
  - planning
  - deciding whether delegation is needed
  - deciding how many delegates to spawn
  - lightweight retrieval from Hermes memory and Watson repo

### WatsonDev
Implementation in Hermes:
- `delegate_task` subagent
- model override: `gpt-5.4` via delegation defaults or explicit override
- responsibilities:
  - heavy coding
  - repo surgery
  - debugging
  - difficult technical implementation

### WatsonMemory
Implementation in Hermes:
- either a focused `delegate_task` run or a future custom skill/cron workflow
- responsibilities:
  - OM sweeps
  - curation proposals
  - controlled promotion into Hermes memory and Watson repo memory lanes

### WatsonReviewer
Implementation in Hermes:
- focused `delegate_task` reviewer lane
- cheap local review by default for scope/process checks
- stronger model only when hard technical review is needed

## Memory Integration Policy

### Hermes memory should store only
- user identity and preferences
- durable workflow preferences
- machine/runtime facts reused often
- a few stable project truths

### Watson repo should continue storing
- `MEMORY.md`
- `memory/YYYY-MM-DD.md`
- `OBSERVATIONS.md`
- `REFLECTIONS.md`
- `bank/*`
- `reports/*`
- automation scripts and recipes

### Promotion path
Use this flow:
- reports/transcripts/runtime dumps
- -> observations if reusable
- -> reflections if repeated or clustered
- -> Watson durable memory if stable
- -> Hermes memory only if truly session-independent and repeatedly useful

## Migration Phases

### Phase 1 - Preserve, do not merge
Status: done
- left `/home/juanbeck/Watson` intact
- avoided bulk import into Hermes memory
- validated the role/memory/OM structure before changing anything

### Phase 2 - Validate runtime reality
Status: mostly done
- validated the correct Windows Ollama endpoint
- validated Hermes local-model call path
- validated Hermes repo, config, and core tool availability

Remaining check:
- run a practical multi-step tool-use test on the local model after more sessions accumulate

### Phase 3 - Replace OpenClaw-specific spend tracking with Hermes-native tracking
Status: started
Implemented:
- `scripts/hermes_usage_report.py`

Purpose:
- query `~/.hermes/state.db`
- separate Codex sessions from local sessions
- write Hermes usage summaries into `reports/expenditure/ledger-YYYY-MM-DD.md`
- emit hourly JSON snapshots under `reports/expenditure/hourly/`

Reason:
- old `scripts/token_tracker.py` is tightly coupled to OpenClaw session formats and metrics assumptions
- Hermes already stores session usage in `state.db`, so Hermes-native reporting is cleaner and more reliable

### Phase 4 - Re-express OM automation with Hermes primitives
Status: pending
Target:
- keep the Watson OM lane design
- drive it with Hermes cron + repo scripts instead of OpenClaw cron JSONs

Planned approach:
- preserve `scripts/om/observer-worker.sh`
- preserve `scripts/om/retriever-worker.sh`
- create Hermes cron jobs that run self-contained prompts invoking these scripts via terminal
- keep durable-memory promotion conservative

### Phase 5 - Skill-ify the durable workflows
Status: pending
Likely skill candidates:
- Watson repo retrieval contract
- Watson memory sweep / OM observer flow
- Hermes usage reporting
- review lane conventions

## What Not to Migrate Blindly
- OpenClaw session internals
- stale endpoint assumptions
- transcript dumps as primary retrieval sources
- brittle model/tool expectations from old Qwen tests
- large raw memory blobs into Hermes native memory

## New Operational Defaults
1. Hermes is the runtime brain.
2. `/home/juanbeck/Watson` is the canonical Watson external memory/workspace.
3. Windows Ollama is the local-model endpoint.
4. Main runs local-first.
5. Delegation defaults to strong Codex execution.
6. Memory promotion remains explicit and curated.
7. Spend tracking should use Hermes `state.db`, not OpenClaw session files.

## Immediate Next Steps
1. Create a Hermes cron job for `scripts/hermes_usage_report.py report --write`
2. Create a Hermes cron job for OM hygiene sweeps using `scripts/om/observer-worker.sh`
3. Add a lightweight Watson migration skill so new Hermes sessions know when and how to consult the Watson repo
4. Run a local-model capability test for a realistic multi-step planning + delegation workflow
5. If Qwen 27B via llama.cpp becomes the new main local stack, keep the same role split and swap only the endpoint/model config

## Commands

### Hermes config / runtime
```bash
hermes config
hermes doctor
hermes cron list
```

### Local model smoke test
```bash
hermes chat -q "Reply with exactly LOCAL_OK." -m qwen3.5:9b
```

### Hermes usage reporting
```bash
python3 scripts/hermes_usage_report.py status --date 2026-03-28
python3 scripts/hermes_usage_report.py report --date 2026-03-28 --write
```

## Bottom Line
The migration should preserve the good Watson abstractions while letting Hermes remain Hermes.
The right move is not to port OpenClaw literally.
The right move is to port the logic that made Watson useful.
