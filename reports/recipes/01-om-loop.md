# Recipe 01 - OM Loop (Observer/Reflector)
Date: 2026-03-12

## Purpose
Run a deterministic Observational Memory loop so WatsonOW can:
- capture meaningful work consistently
- keep memory lanes small and useful
- route memory ownership by role
- avoid silent failures when tools or retrieval break

## 1. Memory Lanes and Owners

- `memory/YYYY-MM-DD.md`
  - purpose: raw operational timeline
  - owner: any active role may append its own work block
- `OBSERVATIONS.md`
  - purpose: compact reusable operational facts
  - owner: `WatsonOW-Memory`
- `REFLECTIONS.md`
  - purpose: condensed patterns, conflicts, and promotion candidates
  - owner: `WatsonOW-Memory`
- `MEMORY.md`
  - purpose: tiny durable truths only
  - owner: `WatsonOW-Memory`
- `bank/*`
  - purpose: structured reflective pages
  - owner: `WatsonOW-Memory`

Rule:
- `WatsonOW-Main` may propose promotions.
- `WatsonOW-Dev` may append daily audit notes only.
- `WatsonOW-Review` may QA memory changes and write review artifacts, but does not directly update durable memory unless explicitly assigned.

## 2. Deterministic Retrieval Order

Always load in this order before any semantic expansion:
1. `IDENTITY.md`
2. `USER.md`
3. `AGENTS.md`
4. `HEARTBEAT.md`
5. current contract or task brief

Then load by role:

### WatsonOW-Main
1. `memory/YYYY-MM-DD.md` for today
2. yesterday’s daily memory only if the task spans days
3. `MEMORY.md`
4. relevant sections of `OBSERVATIONS.md` and `REFLECTIONS.md` only when needed
5. semantic/index retrieval only as a fallback or expansion step

### WatsonOW-Dev
1. current contract
2. target files
3. only the memory inputs explicitly listed in the contract

Do not load all memory lanes by default for Dev work.

### WatsonOW-Memory
1. recent daily memory window
2. `OBSERVATIONS.md`
3. `REFLECTIONS.md`
4. `MEMORY.md`
5. relevant `bank/*` pages

### WatsonOW-Review
1. current contract
2. changed files
3. this recipe
4. `reports/recipes/02-delegation-contracts.md`
5. proposed memory outputs if memory changed

## 3. Write Triggers

### Daily memory (`memory/YYYY-MM-DD.md`)
Write after:
- any meaningful work block
- delegation start or completion
- config, runtime, or repo changes
- test or validation runs
- tool failure that changed the task outcome

### Observations (`OBSERVATIONS.md`)
Write only when one of these is true:
- the fact is reusable beyond the current session
- the same signal appeared at least twice
- a tool or retrieval failure exposed an operational rule
- a workflow or routing rule changed
- a role boundary or contract rule changed

### Reflections (`REFLECTIONS.md`)
Write when:
- a milestone is reached
- `OBSERVATIONS.md` gets noisy or repetitive
- three or more linked observations should be merged
- policy drift or conflict needs consolidation

### Durable memory (`MEMORY.md` or `bank/*`)
Promote only when:
- the user explicitly asked to remember it
- the fact is stable and evidence-backed
- the rule survived at least one reuse or revalidation
- the statement is unlikely to churn rapidly

## 4. Promotion and Pruning Rules

### Promotion
- raw daily note -> observation:
  - if it is operationally reusable
- observation -> reflection:
  - if repeated, clustered, or conflict-prone
- reflection -> `MEMORY.md`:
  - if tiny, durable, and high confidence
- reflection -> `bank/*`:
  - if structured context is useful but too detailed for `MEMORY.md`

### Pruning
- Keep daily logs as canonical raw history, but move long transcripts and test dumps to `reports/openclaw/` or `reports/artifacts/` and leave a short pointer in daily memory.
- Rewrite reflections in place when the same theme repeats.
- Remove or overwrite superseded statements in `bank/*`.
- Keep `MEMORY.md` small enough for routine hydration. If an entry is obsolete, remove or mark it superseded.
- Remove observations only when their evidence is preserved elsewhere and the observation is no longer operationally useful.

## 5. Automatic OM Path

Use `scripts/om/observer-worker.sh` for deterministic observer writes.

### Typical capture flow

```bash
scripts/om/observer-worker.sh capture \
  --scope process \
  --event "Delegation contract executed for harness update." \
  --context "WatsonOW-Main -> WatsonOW-Dev" \
  --source "reports/openclaw/agentic-workflow-2026-03-11T18-27-44Z.md"
```

### Direct observation write

```bash
scripts/om/observer-worker.sh observe \
  --scope infra \
  --observation "Tool access failed for Qwen main; task must be delegated or explicitly blocked." \
  --confidence 0.95 \
  --evidence "runtime failure log"
```

### Counter tick

```bash
scripts/om/observer-worker.sh tick --turns 1 --tokens 600
```

## 6. Post-Task OM Flow

1. `WatsonOW-Main`
   - drafts the contract
   - lists memory inputs required
   - lists expected memory outputs
2. `WatsonOW-Dev`
   - executes only within contract scope
   - writes daily audit trace
   - returns evidence and promotion candidates
3. `WatsonOW-Memory`
   - decides observation/reflection/durable writes
   - rejects weak or disputed promotions
4. `WatsonOW-Review`
   - checks recipe compliance
   - checks memory ownership was respected
   - checks pruning and promotion rules were followed
5. `expenditure-tracker`
   - logs the work block if spend was meaningful

## 7. Tool Failure Policy

If a required tool is unavailable, denied, or fails:
- report the exact tool and failure
- say what the failure blocks
- try one reasonable fallback only if it stays inside scope
- otherwise delegate or stop

Do not silently continue after tool failure.
Do not claim a memory update or validation happened if the required tool did not run.

## 8. Role Boundaries

- `WatsonOW-Main`
  - may read all lanes
  - may write daily notes and contracts
  - may propose, but not directly own, durable promotions
- `WatsonOW-Dev`
  - may write only task-local/daily audit memory
  - does not update `OBSERVATIONS.md`, `REFLECTIONS.md`, `MEMORY.md`, or `bank/*`
- `WatsonOW-Memory`
  - owns cross-lane promotion, pruning, and durable updates
- `WatsonOW-Review`
  - verifies that role boundaries and recipes were respected

## 9. Minimal Checklist

Before closing a non-trivial task, confirm:
- daily audit trace exists
- any reusable signal was either promoted or explicitly rejected
- durable memory was updated only by the memory role
- reviewer checked recipe compliance if scope was meaningful
- expenditure was logged if the session consumed notable model budget
