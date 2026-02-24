# Memory Architecture Review (OpenClaw repo) — 2026-02-24

## Inputs reviewed
- X posts (alexfinn, matthewberman): links accessible, but direct tweet text was not reliably extractable from unauthenticated HTML snapshots.
- Anthropic PDF: downloaded, but local PDF text extraction tools are unavailable in this runtime.
- Mastra docs: **Observational Memory** (Observer + Reflector, thresholds, buffering).
- arXiv 2602.11865: **Intelligent AI Delegation** (adaptive delegation, explicit roles/boundaries/accountability).
- Local OpenClaw docs: `docs/experiments/research/memory.md` (offline-first memory design for Clawd-style workspaces).

## Current repo state (important)
- You already have strong human-auditable memory primitives:
  - `memory/YYYY-MM-DD.md` (daily logs)
  - `MEMORY.md` (curated long-term)
  - context files (`SOUL.md`, `USER.md`, etc.)
- OpenClaw memory search exists, but semantic recall is currently weak because embedding provider is not configured.

## What to keep (do not throw away)
1. **Markdown as source of truth** (excellent for trust/debugging).
2. **Two-layer memory**
   - Raw episodic logs (`memory/YYYY-MM-DD.md`)
   - Curated semantic layer (`MEMORY.md` + future entity/opinion pages)
3. **Session startup hydration** from small stable files only (avoid giant context injection).

## Recommended target architecture (non-brittle)

### 1) Four memory lanes (hybrid, practical)
- **Core memory (always loaded):**
  - identity, user profile, mission constraints, active principles.
  - files: `SOUL.md`, `USER.md`, `MEMORY.md` (small, curated).
- **Episodic memory (append-only):**
  - daily timeline facts and events.
  - files: `memory/YYYY-MM-DD.md`.
- **Semantic memory (retrieval index):**
  - derived from markdown; optimized for recall.
  - store: sqlite/fts (+ optional vectors).
- **Reflective memory (compressed beliefs):**
  - distilled preferences, stable decisions, entity profiles.
  - files: `bank/` style pages (below).

### 2) Add a `bank/` layer (from OpenClaw research doc)
Suggested structure:
- `bank/world.md`
- `bank/experience.md`
- `bank/opinions.md` (with confidence)
- `bank/entities/<name>.md`

Why: this gives you "dynamic but stable" memory — logs can grow forever while retrieval hits compact, maintained summaries.

### 3) Observer + Reflector loop (Mastra-style idea, OpenClaw-compatible)
- **Observer (frequent):** turns recent raw logs into compact observations when token/size thresholds are hit.
- **Reflector (slower):** merges observations into durable summaries and updates confidence in opinions/preferences.

Equivalent in your repo:
- Observer output => `memory/YYYY-MM-DD.md` retain blocks + semantic index entries.
- Reflector output => updates to `MEMORY.md` and `bank/*`.

### 4) Retrieval policy (to avoid brittle memory)
On each important turn, retrieve in this order:
1. Core memory (always in prompt)
2. Entity memory (if user/task mentions entities)
3. Recent episodic window (last 24–72h)
4. Semantic top-k from index
5. Conflict resolver (prefer newest + highest confidence, keep provenance)

### 5) Truncation/compression policy
- Hard cap raw episodic context in prompt (recent-only).
- Older raw logs are never deleted; they are compressed into:
  - observation summaries
  - entity pages
  - opinion/confidence entries
- Keep citations (source file + date), so compressed memory stays auditable.

## Concrete implementation plan for this repo

### Phase A (today): make retrieval work
1. Configure memory embeddings provider (`openclaw memory status` currently shows none).
2. Reindex memory.
3. Validate recall queries (names, projects, decisions).

### Phase B (this week): add structure
1. Create `bank/` files and seed them from existing memory.
2. Add a lightweight "Retain" section template for daily logs.
3. Define confidence format for opinions (e.g., `O(c=0.85)`).

### Phase C (next): automate reflection
1. Add scheduled reflection pass (heartbeat or cron):
   - promote durable facts to `MEMORY.md`
   - update entity pages
   - revise opinion confidence with evidence links
2. Add memory hygiene checks:
   - stale/conflicting facts report
   - orphan entities
   - oversized core memory guardrails

## Suggested defaults (starting point)
- Core memory target size: <= 1,500–2,500 tokens.
- Episodic retrieval window: last 2 days by default.
- Semantic recall top-k: 8–20 depending on task complexity.
- Reflection cadence: daily + weekly deeper pass.
- Confidence decay: slight decay over time without reinforcing evidence.

## Where this aligns with your goal
This architecture is:
- **solid** (not brittle): because raw history remains canonical and compressed layers are derived.
- **dynamic**: reflection updates beliefs/preferences over time.
- **precise**: retrieval is targeted by entity/time/task, not full-history dumps.
- **auditable**: every belief can point back to source events.

## Caution
Do not rely on a single vector store as "memory". Use vectors as an accelerator, not as canonical truth.
Markdown + curated summaries + indexed retrieval is the safer backbone.
