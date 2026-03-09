# OM Phase 2 Observer Automation - 2026-02-25

## What Was Implemented

Observer worker CLI:
- `scripts/om/observer-worker.sh`

Commands:
1. `capture`
- Records a raw event in `memory/YYYY-MM-DD.md` under `## Raw Events`.
- Increments observer counters (`turns`, `tokens`, `events`).
- Auto-promotes an observation when thresholds are reached.

2. `tick`
- Increments counters without writing event content.
- Useful when turn/token accounting is handled elsewhere.

3. `observe`
- Writes an observation directly to:
  - `OBSERVATIONS.md`
  - `memory/YYYY-MM-DD.md` under `## Retain (Observer Output)`
- Optionally resets counters (default: yes).

State file:
- `memory/observer-state.env`

Default thresholds:
- `OM_OBSERVER_TURN_THRESHOLD=10`
- `OM_OBSERVER_TOKEN_THRESHOLD=5000`

## Why This Matches Phase 2

Phase 2 required:
- threshold-triggered observer automation
- compact structured writes into observation sections

This worker does both deterministically, with no external API dependency.

## Data Flow

1. Runtime emits event -> `capture`.
2. Event goes to daily `Raw Events`.
3. Counters accumulate in `memory/observer-state.env`.
4. On threshold hit, a compact observation is promoted to:
- global lane (`OBSERVATIONS.md`)
- daily retain lane (`memory/YYYY-MM-DD.md`)

## Quick Usage

Single event capture:

```bash
scripts/om/observer-worker.sh capture \
  --scope process \
  --event "User asked to keep staged-first workflow." \
  --context "Git workflow policy for this repo." \
  --source "active thread instruction"
```

Manual observe write:

```bash
scripts/om/observer-worker.sh observe \
  --scope infra \
  --observation "Local memory embeddings are active and index is healthy." \
  --confidence 0.95 \
  --evidence "openclaw memory status --deep"
```

Counter-only tick:

```bash
scripts/om/observer-worker.sh tick --turns 1 --tokens 650
```

## Low-Cost Test Plan

Use low thresholds for fast validation:

```bash
OM_OBSERVER_TURN_THRESHOLD=2 OM_OBSERVER_TOKEN_THRESHOLD=200 \
  scripts/om/observer-worker.sh capture \
  --scope process \
  --event "Observer test event one." \
  --source "manual-test"

OM_OBSERVER_TURN_THRESHOLD=2 OM_OBSERVER_TOKEN_THRESHOLD=200 \
  scripts/om/observer-worker.sh capture \
  --scope process \
  --event "Observer test event two (should trigger promotion)." \
  --source "manual-test"
```

Expected:
- first call: `observer_trigger=false`
- second call: `observer_trigger=true` and `observation_id=O-...`

Then verify:
- `OBSERVATIONS.md` got a new entry
- today’s `memory/YYYY-MM-DD.md` got:
  - one or more `Raw Events`
  - one `Retain (Observer Output)` observation

## Retrieval Isolation Checks (Context vs Index)

Goal:
- ensure recall comes from memory index, not current chat context window

Checklist:
1. Start a fresh OpenClaw session.
2. Ask for a paraphrased query not present verbatim in recent chat.
3. Confirm answer cites indexed files from memory lanes.
4. Cross-check with CLI retrieval:

```bash
openclaw memory search --json --query "staged review policy"
openclaw memory search --json --query "observational compression phases"
```

Interpretation:
- If CLI finds relevant chunks and fresh session answers align with those sources, retrieval is likely index-backed.
- If results appear only when the same wording was used in immediate chat turns, treat as possible context-window leakage and rerun from a clean session.

## Notes

- Token counting is approximate (`~chars/4`) by design for deterministic triggers.
- This phase focuses on deterministic compression mechanics, not semantic summarization quality.
- Reflective promotion quality tuning belongs to Phase 3 (reflector jobs and conflict handling).
