# OBSERVATIONS.md

Append-only observation log.
Each observation should be compact, evidence-backed, and optionally expirable.

## Observation Format

- `id`: `O-YYYY-MM-DD-NN`
- `timestamp`: ISO-8601 UTC
- `scope`: `user|project|infra|process`
- `confidence`: `0.00-1.00`
- `observation`: single durable statement
- `evidence`: source links to local files/lines
- `expires`: optional date when likely stale

## Entries

- `id`: O-2026-02-25-01
  - `timestamp`: 2026-02-25T00:00:00Z
  - `scope`: process
  - `confidence`: 0.95
  - `observation`: User requires staged diffs before any commit.
  - `evidence`: active thread instruction (Codex)
  - `expires`: 2026-03-11

- `id`: O-2026-02-25-02
  - `timestamp`: 2026-02-25T22:01:25Z
  - `scope`: infra
  - `confidence`: 0.98
  - `observation`: OpenClaw memory indexing stays empty until a memory embedding provider is configured.
  - `evidence`: `reports/openclaw/mainpc-om-validation-2026-02-25T22-01-25Z.md`
  - `expires`: none

- `id`: O-2026-03-09-01
  - `timestamp`: 2026-03-09T21:58:00Z
  - `scope`: process
  - `confidence`: 0.96
  - `observation`: WatsonOW installation tasks were initiated and core bootstrap artifacts were created in recipes/skills/expenditure paths under workspace constraints.
  - `evidence`: `reports/recipes/00-watsonow-operating-system.md`, `reports/recipes/01-om-loop.md`, `reports/recipes/02-delegation-contracts.md`, `reports/recipes/03-skills-authoring.md`, `skills/memory-observer/SKILL.md`, `skills/memory-reflector/SKILL.md`, `skills/expenditure-tracker/SKILL.md`
  - `expires`: none

- `id`: O-2026-03-10-01
  - `timestamp`: 2026-03-09T23:12:47Z
  - `scope`: process
  - `confidence`: 0.98
  - `observation`: WatsonOW harness files were tightened around workspace boundaries, git change control, budget-aware model routing, and reusable skill conventions.
  - `evidence`: `AGENTS.md`, `HEARTBEAT.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `reports/recipes/00-watsonow-operating-system.md`, `reports/recipes/03-skills-authoring.md`, `skills/memory-observer/SKILL.md`, `skills/memory-reflector/SKILL.md`, `skills/expenditure-tracker/SKILL.md`
  - `expires`: 2026-03-11

- `id`: O-2026-03-11-01
  - `timestamp`: 2026-03-11T01:42:00Z
  - `scope`: infra
  - `confidence`: 0.93
  - `observation`: OpenClaw model fallbacks were updated to include `ollama/qwen3.5:9b` as a configured local option for upcoming delegated passthrough roles, without switching the default model.
  - `evidence`: `openclaw models fallbacks list`, `openclaw models list` (2026-03-11)
  - `expires`: none

- `id`: O-2026-03-11-02
  - `timestamp`: 2026-03-11T18:40:00Z
  - `scope`: process
  - `confidence`: 0.97
  - `observation`: The repo harness was updated upstream to a stricter WatsonOW control layer, and the active git workflow was reconciled so Juan's direct auto-commit override remains live on top of the staged-first baseline policy.
  - `evidence`: `AGENTS.md`, `MEMORY.md`, `REFLECTIONS.md`, `memory/2026-03-11.md`, upstream commit `334ab93`
  - `expires`: none

- `id`: O-2026-03-11-03
  - `timestamp`: 2026-03-11T23:02:41Z
  - `scope`: infra
  - `confidence`: 0.98
  - `observation`: In the current WSL/OpenClaw runtime, Ollama is reachable on `127.0.0.1:11434`, while the configured `172.24.16.1:11434/v1` endpoint is stale and causes a false appearance that `qwen3.5:9b` is available even though local Ollama currently exposes only `gpt-oss:20b-cloud`.
  - `evidence`: `~/.openclaw/openclaw.json`, `~/.openclaw/agents/main/agent/models.json`, `openclaw status`, `openclaw models list`, `ollama list`, localhost `/api/tags` probe
  - `expires`: 2026-03-18

- `id`: O-2026-03-11-04
  - `timestamp`: 2026-03-11T23:06:50Z
  - `scope`: infra
  - `confidence`: 0.99
  - `observation`: This machine currently has two active Ollama installations: a WSL/Linux `0.15.4` daemon on `127.0.0.1:11434` and a Windows `0.17.7` installation reachable from WSL at `172.24.16.1:11434`; the Windows side holds the real `qwen3.5:9b` model.
  - `evidence`: `/usr/local/bin/ollama`, `/etc/systemd/system/ollama.service`, `/mnt/c/Users/Admin/AppData/Local/Programs/Ollama/ollama.exe`, `/mnt/c/Users/Admin/.ollama/models/manifests/registry.ollama.ai/library/qwen3.5/9b`, `/api/version` and `/api/tags` probes
  - `expires`: 2026-03-18

- `id`: O-2026-03-11-05
  - `timestamp`: 2026-03-11T23:28:36Z
  - `scope`: infra
  - `confidence`: 0.98
  - `observation`: After switching OpenClaw to the native Windows Ollama endpoint, `qwen3.5:9b` performs real tool calls in-session; session clutter can be reduced by using named session keys and patched labels instead of `/new`-minted `tui-*` sessions.
  - `evidence`: `openclaw gateway call sessions.patch --params '{"key":"agent:main:test-2","model":"ollama/qwen3.5:9b"}' --json`, `openclaw agent --session-id e5d12c68-d66b-4582-bf2f-ed103b0993cf ... --json`, `/home/juanbeck/.openclaw/agents/main/sessions/e5d12c68-d66b-4582-bf2f-ed103b0993cf.jsonl`, `openclaw gateway call sessions.patch --params '{"key":"agent:main:test-2","label":"Qwen tool test"}' --json`
  - `expires`: 2026-03-18

- `id`: O-2026-03-12-01
  - `timestamp`: 2026-03-12T00:05:00Z
  - `scope`: infra
  - `confidence`: 0.96
  - `observation`: OpenClaw now has a non-default `router` agent pinned to `ollama/qwen3.5:9b`, with Qwen restricted to read/write/session tools while spawned subagents default to `openai-codex/gpt-5.4`; this keeps the Codex execution lane intact while testing the orchestrator pattern safely.
  - `evidence`: `~/.openclaw/openclaw.json`, `openclaw status`, `openclaw agents list`
  - `expires`: 2026-03-19

- `id`: O-2026-03-12-02
  - `timestamp`: 2026-03-12T00:56:00Z
  - `scope`: process
  - `confidence`: 0.95
  - `observation`: OM review confirms the current operating stack is: OM pipeline build as the top repo priority, staged-first as the baseline harness policy with Juan's auto-commit override active, and Qwen-router/Codex-executor as the live delegation pattern.
  - `evidence`: `MEMORY.md`, `REFLECTIONS.md`, `OBSERVATIONS.md`, `memory/2026-03-12.md`
  - `expires`: 2026-03-19

- `id`: O-2026-03-12-03
  - `timestamp`: 2026-03-12T01:36:20Z
  - `scope`: process
  - `confidence`: 0.98
  - `observation`: OM control logic now defines deterministic retrieval order, role-owned durable memory writes, explicit promotion/pruning rules, and required reporting of tool failures instead of silent no-ops.
  - `evidence`: `reports/recipes/01-om-loop.md`, `reports/recipes/02-delegation-contracts.md`, `AGENTS.md`, `TOOLS.md`, `skills/memory-observer/SKILL.md`, `skills/memory-reflector/SKILL.md`, `MEMORY.md`
  - `expires`: none

- `id`: O-2026-03-12-04
  - `timestamp`: 2026-03-12T02:11:00Z
  - `scope`: infra
  - `confidence`: 0.94
  - `observation`: OpenClaw config lacks explicit memory search paths for OM retrieval; patching now.
  - `evidence`: subagent runtime-alignment task (2026-03-12), `memory/2026-03-12.md`
  - `expires`: 2026-03-19

- `id`: O-2026-03-17-01
  - `timestamp`: 2026-03-17T01:24:00Z
  - `scope`: process
  - `confidence`: 0.95
  - `observation`: OM lane audit shows recent repo operations such as the `nao-ros4hri-bridge` fast-forward are staying in daily memory, while transcript-sized artifacts can still leak into `memory/`; transcript routing is the main current hygiene gap.
  - `evidence`: `memory/2026-03-17.md`, `memory/2026-03-11.md`, `memory/2026-03-11-repo-memory-status.md`, `MEMORY.md`, `reports/recipes/01-om-loop.md`
  - `expires`: 2026-03-24

- `id`: O-2026-03-17-02
  - `timestamp`: 2026-03-17T02:48:00Z
  - `scope`: infra
  - `confidence`: 0.97
  - `observation`: OM automation now uses isolated `memory`-agent cron jobs plus local OpenClaw session/transcript parsing to track Codex spend and stale memory artifacts without repeated external API polling.
  - `evidence`: `cron/memory-sweep-job.json`, `cron/immediate-memory-sweep.json`, `scripts/token_tracker.py`, `scripts/token-tracker.sh`, `reports/expenditure/ledger-2026-03-17.md`, `openclaw cron list --all --json`
  - `expires`: 2026-03-24

- `id`: O-2026-03-17-03
  - `timestamp`: 2026-03-17T03:01:00Z
  - `scope`: process
  - `confidence`: 0.96
  - `observation`: Relocated oversized transcript to compliance by moving the 2026-03-11 status dump out of `memory/` and into `reports/openclaw/transcripts/`.
  - `evidence`: `reports/openclaw/transcripts/2026-03-11-repo-memory-status.md`, `memory/2026-03-17.md`
  - `expires`: 2026-03-24

- `id`: O-2026-03-17-04
  - `timestamp`: 2026-03-17T03:43:00Z
  - `scope`: process
  - `confidence`: 0.93
  - `observation`: Current OM sweep stale-memory alerts are now mainly being triggered by non-canonical filenames, so the flag should be interpreted as a naming-hygiene check unless a file also shows transcript-like content or excessive line count.
  - `evidence`: `reports/expenditure/ledger-2026-03-17.md`, `memory/2026-02-23-2227.md`, `memory/2026-03-12-delegation-test.md`
  - `expires`: 2026-03-24

- `id`: O-2026-03-28-01
  - `timestamp`: 2026-03-28T19:43:00Z
  - `scope`: process
  - `confidence`: 0.95
  - `observation`: Current OM sweep stale-memory alerts still mostly indicate filename-hygiene drift; treat them as relocation candidates only when a flagged file is also transcript-shaped or exceeds the memory-size threshold.
  - `evidence`: `reports/expenditure/ledger-2026-03-28.md`, `memory/2026-02-23-2227.md`, `memory/2026-03-12-delegation-test.md`, `memory/2026-03-28.md`
  - `expires`: 2026-04-04

- `id`: O-2026-04-01-01
  - `timestamp`: 2026-04-01T01:12:40Z
  - `scope`: process
  - `confidence`: 0.92
  - `observation`: Current Watson-repo OM hygiene is in a clean-state regime: remaining sweep drift is minor template-format residue rather than durable-memory growth or transcript bloat.
  - `evidence`: MEMORY.md; memory/2026-04-01.md; reports/expenditure/ledger-2026-04-01.md
  - `expires`: 2026-04-08

- `id`: O-2026-05-21-01
  - `timestamp`: 2026-05-21T03:55:31Z
  - `scope`: process
  - `confidence`: 0.97
  - `observation`: OM sweep cycle is executing but OBSERVATIONS.md and REFLECTIONS.md have not been updated since early April and mid-March respectively; the OM writing loop has gone dormant despite active repo work including Hermes migration, Codex harness integration, and expenditure tracking infrastructure.
  - `evidence`: OBSERVATIONS.md (last: O-2026-04-01-01), REFLECTIONS.md (last: R-2026-03-17-01), memory/2026-05-07.md, reports/expenditure/ledger-2026-05-21.md
  - `expires`: none

- `id`: O-2026-05-30-01
  - `timestamp`: 2026-05-30T15:46:49Z
  - `scope`: process
  - `confidence`: 0.96
  - `observation`: OM writing loop dormancy confirmed persistent: 9+ days since last OBSERVATIONS.md update and 7+ weeks since last REFLECTIONS.md entry, despite sustained daily activity (21 sessions on 2026-05-30 alone). The OM sweep cron jobs execute but do not produce new observations or reflections — the loop captures events to daily memory but does not flush to durable lanes.
  - `evidence`: memory/2026-05-30.md, OBSERVATIONS.md (last: O-2026-05-21-01), REFLECTIONS.md (last: R-2026-03-17-01), reports/expenditure/ledger-2026-05-30.md
  - `expires`: none
