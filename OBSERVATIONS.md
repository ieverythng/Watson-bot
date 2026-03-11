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
  - `expires`: none

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
  - `observation`: WatsonOW harness files were tightened around workspace boundaries, staged-first git control, budget-aware model routing, and reusable skill conventions.
  - `evidence`: `AGENTS.md`, `HEARTBEAT.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `reports/recipes/00-watsonow-operating-system.md`, `reports/recipes/03-skills-authoring.md`, `skills/memory-observer/SKILL.md`, `skills/memory-reflector/SKILL.md`, `skills/expenditure-tracker/SKILL.md`
  - `expires`: none

- `id`: O-2026-03-11-01
  - `timestamp`: 2026-03-11T01:42:00Z
  - `scope`: infra
  - `confidence`: 0.93
  - `observation`: OpenClaw model fallbacks were updated to include `ollama/qwen3.5:9b` as a configured local option for upcoming delegated passthrough roles, without switching the default model.
  - `evidence`: `openclaw models fallbacks list`, `openclaw models list` (2026-03-11)
  - `expires`: none
