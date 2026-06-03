# OM Scripts vs Hermes Memory Audit
Date: 2026-03-28
Scope: `/home/juanbeck/Watson/scripts/om/*` and Hermes native memory/recall

## Executive Summary
The Watson OM scripts are partly worth keeping.

Keep:
- `scripts/om/observer-worker.sh` as a repo-bound structured logging helper
- the deterministic-first retrieval philosophy from `scripts/om/retriever-worker.sh`
- the lane separation in the Watson repo (`memory/`, `OBSERVATIONS.md`, `REFLECTIONS.md`, `MEMORY.md`, `bank/`)

Do not keep unchanged:
- the OpenClaw semantic search coupling in `retriever-worker.sh`
- any assumption that OpenClaw memory indexing remains available or healthy
- placeholder-heavy daily-memory template content that pollutes retrieval

Hermes already gives strong built-in memory/recall primitives:
- bounded durable memory (`~/.hermes/memories/MEMORY.md` and `USER.md`)
- automatic memory flush before compression/reset/exit
- session recall through `session_search`
- full session persistence in `~/.hermes/state.db`
- subagent delegation and cron jobs

Conclusion:
Use OM as a repo-bound external memory hygiene layer, not as a replacement for Hermes native memory.

## What Was Verified

### `scripts/om/observer-worker.sh`
Validated:
- shell syntax passes `bash -n`
- direct observation mode works in sandbox
- capture mode writes raw events correctly
- state tracking works through `memory/observer-state.env`

Validated behaviors:
- `capture` appends raw events to `memory/YYYY-MM-DD.md`
- `observe` appends durable observation entries to `OBSERVATIONS.md`
- threshold counters gate whether a capture auto-promotes into observation output
- optional post-capture hook exists and reports blocker state clearly on failure

Caveat discovered during sandbox validation:
- the old daily template injected placeholder example entries into every new day file, which is bad for retrieval quality
- this was cleaned up by simplifying `memory/templates/daily-memory-template.md`

Assessment:
- salvageable and useful
- best used as a deterministic structured writer for the external Watson repo
- should not be allowed to promote into Hermes native memory automatically

### `scripts/om/retriever-worker.sh`
Validated:
- shell syntax passes `bash -n`
- deterministic retrieval packet generation works
- fixed-order hydration of key files works
- lexical fallback logic is reasonable

Original weakness:
- semantic expansion was tightly coupled to `openclaw memory status/search`
- in current validation, semantic mode was blocked due to unusable OpenClaw status output
- this made the semantic portion brittle and unsuitable as a continuing dependency

Hermes-era change applied:
- OpenClaw semantic expansion was removed as an active dependency
- the retriever now intentionally reports semantic mode as deprecated/disabled
- deterministic retrieval and lexical fallback remain intact

What is still good:
- deterministic file ordering
- exclusion of `reports/openclaw/` dumps from primary retrieval
- lexical fallback over current/recent daily memory files
- output packet format

Assessment:
- keep deterministic and lexical parts
- keep semantic flags only as compatibility no-ops for old callers
- use Hermes-native recall (`session_search`) plus repo file retrieval instead of OpenClaw semantic search

## Hermes Native Memory/Recall Capabilities Relevant to OM

## 1. Durable bounded memory
Hermes has built-in file-backed durable memory in:
- `~/.hermes/memories/MEMORY.md`
- `~/.hermes/memories/USER.md`

Important properties:
- injected into the system prompt at session start
- bounded by character limits
- intended for compact durable facts only
- protected against obvious prompt-injection payloads
- writes persist immediately but do not mutate the active session prefix cache mid-session

This overlaps with the top lane of OM:
- Hermes `MEMORY.md`/`USER.md` ~= your tiny durable truths / user profile layer

## 2. Session recall via `session_search`
Hermes persists sessions into:
- `~/.hermes/state.db`

Those sessions are searchable via:
- `session_search`

This overlaps with OM's purpose of recovering cross-session context, but it works at conversation history/session level rather than curated markdown lane level.

This means Hermes already has a native answer for:
- "what were we working on before?"
- "how did we solve that last time?"
- "what happened in that previous session?"

## 3. Automatic memory flush
Hermes has a `flush_memories()` path that runs before:
- compression
- reset/new session
- CLI exit
- some gateway lifecycle events

What it does:
- gives the model one focused chance to call the `memory` tool before context is lost
- prioritizes durable user preferences and recurring patterns over task junk

This overlaps with the "observer/reflection before losing context" instinct behind OM, but only for the bounded native memory lane.

## 4. Project-context loading
Hermes automatically loads project context files like:
- `.hermes.md` / `HERMES.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.cursorrules`

This means some routing/policy context you were trying to force through OM retrieval can already be loaded at session start if the working directory is appropriate.

## 5. Delegation + cron
Hermes already has native primitives for:
- subagents (`delegate_task`)
- scheduled autonomous work (`cronjob`)

This overlaps with the orchestration role around OM sweeps and review lanes.

## Where Hermes Does NOT Replace OM
Hermes does not natively provide the exact same thing as your repo-bound OM lanes.

What Hermes does not give you out of the box:
- a curated external markdown knowledge base with explicit promotion gates
- an append-only operational observation file like `OBSERVATIONS.md`
- a reflective consolidation layer like `REFLECTIONS.md`
- your `bank/*` durable structured pages
- deterministic project-specific retrieval packets over those repo files

So if you care about preserving a human-auditable, markdown-canonical Watson memory repo, OM still has value.

## Best Integration Strategy

### Keep in Hermes native memory
Only keep:
- user preferences
- durable workflow rules
- stable environment facts
- a few repeatedly useful project truths

### Keep in Watson OM repo
Keep:
- `memory/YYYY-MM-DD.md`
- `OBSERVATIONS.md`
- `REFLECTIONS.md`
- `bank/*`
- repo-bound research/process memory

### Use Hermes tools for cross-session recall
Use:
- `session_search` for previous Hermes conversations
- `memory` for compact durable facts

### Use OM only for external curation/hygiene
Use OM scripts for:
- structured audit trails
- curated observation capture
- reflection candidate staging
- deterministic repo-bound retrieval packets

Do not use OM for:
- replacing Hermes durable memory
- recreating a second general-purpose recall system for everything
- storing every session artifact in primary retrieval lanes

## Recommendation by Script

### `observer-worker.sh`
Recommendation: KEEP, with narrow scope

Best Hermes-era use:
- cron-driven or manually invoked repo hygiene helper
- writes to Watson repo only
- no direct write path into Hermes native memory
- trigger after meaningful repo/workflow blocks, not every tiny event

### `retriever-worker.sh`
Recommendation: PARTIAL KEEP / REFACTOR

Keep:
- deterministic order
- lexical fallback
- packet rendering
- path filtering

Replace:
- OpenClaw semantic search dependency

Future Hermes-era behavior should be one of:
- deterministic + lexical only
- deterministic + lexical + optional `session_search` summary note

## Minimal Hermes-Era OM Design
The lean version should be:

1. Hermes built-ins handle:
- durable memory
- user profile
- prior-session recall
- subagents
- cron

2. Watson OM handles:
- external markdown audit and curation
- reflection/promotion candidates
- project-local structured knowledge

3. Integration rule:
- Hermes consults Watson OM when task domain needs it
- Watson OM does not try to duplicate Hermes native memory features

## Practical Bottom Line
You do not need to recreate the full OM stack inside Hermes.
You only need the parts OM does better than Hermes already:
- repo-bound, auditable markdown curation
- explicit promotion lanes
- deterministic project-specific retrieval over those files

Everything else should stay Hermes-native.
