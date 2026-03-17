# Runtime Alignment Findings — 2026-03-12

## Gap: Missing Memory Search Paths in OpenClaw Config

### Observed behavior
- `openclaw.json` lacks a `memorySearch` or equivalent section that explicitly declares OM retrieval paths.
- OpenClaw relies on defaults, which currently do **not** include:
  - `OBSERVATIONS.md`
  - `REFLECTIONS.md`
  - `bank/`

### Impact
- Retrieval is incomplete for OM workflows; semantic expansion may miss key operational memory lanes.
- Matches Recipe 04’s requirement to “avoid treating reports/openclaw/test dumps as primary memory lanes.”

### Proposed fix
Add a `memorySearch` section under `tools` or a new top-level field that:
- Lists the canonical OM paths (`MEMORY.md`, `OBSERVATIONS.md`, `REFLECTIONS.md`, `bank/`)
- Prioritizes them before semantic expansion
- Excludes non-memory dump paths (e.g., `/reports/openclaw/`)

### Action items
1. Patch config with memory search paths
2. Log changes via `memory` agent (`sessions_spawn(agentId=memory)`)
3. Re-check retrieval indexing behavior after patch
4. Add an observation if this signal is reusable
