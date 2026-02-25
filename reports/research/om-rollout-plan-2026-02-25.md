# Watson-Openclaw OM Rollout Plan - 2026-02-25

## Scope

This plan evaluates the recommended target architecture (points 1-4), maps it to current repo reality, and defines a staged implementation path that can start now.

## Current Baseline

- Core memory files already exist: `SOUL.md`, `USER.md`, `MEMORY.md`, `memory/*.md`.
- Research recommendation already captured:
  - `reports/research/memory-architecture-review-2026-02-24.md`
- Host runtime facts must be verified on the deployment machine before applying provider/index steps.

## Architecture Strengths (Points 1-4)

### 1) Four Memory Lanes

Strengths:
- Separates concerns cleanly (core identity, raw episodes, semantic index, reflective summaries).
- Improves retrieval precision by lane routing instead of full-history stuffing.
- Keeps memory auditable because canonical records stay in markdown.

Execution guardrails:
- Add provenance for every reflective claim (`source file + date`).
- Keep core lane small and curated to avoid prompt bloat.

### 2) `bank/` Reflective Layer

Strengths:
- Creates stable retrieval targets that are cheaper than replaying long logs.
- Natural home for entity memory and opinion confidence tracking.
- Helps avoid semantic drift by maintaining curated pages instead of only vectors.

Execution guardrails:
- Use explicit confidence + last-updated fields.
- Prefer updates over appending duplicate facts.

### 3) Observer + Reflector Loop

Strengths:
- Observer compresses raw event flow continuously (cost control).
- Reflector promotes only durable signals (quality control).
- Makes long-term memory updates systematic instead of ad hoc.

Execution guardrails:
- Observer must be deterministic and compact.
- Reflector should run on schedule with conflict checks.

### 4) Ordered Retrieval Policy

Strengths:
- Deterministic retrieval order reduces brittle misses.
- Blending recency + entities + semantic top-k keeps context relevant.
- Conflict resolver formalizes tie-breaking (newer + higher confidence + provenance).

Execution guardrails:
- Cap per-lane token budgets.
- Rerank before prompt packing to reduce noisy recalls.

## Infrastructure Map (Target)

1. Orchestrator (primary agent)
- Handles user-facing reasoning and tool orchestration.
- Default model: cloud (`gpt-4.1-mini` or `gpt-5-mini`).

2. Retriever service
- Pulls memory candidates from:
  - core files
  - `bank/entities/*`
  - recent episodic window
  - semantic index top-k
- Applies rerank + token packing.

3. Observer worker (asynchronous)
- Triggered every N turns or when episodic token threshold is exceeded.
- Writes structured records into `OBSERVATIONS.md` and episodic retain sections.

4. Reflector worker (scheduled)
- Daily pass: promote durable facts to `MEMORY.md` and `bank/*`.
- Weekly pass: deeper conflict resolution and confidence recalibration.

5. Storage/Index
- Canonical source: markdown files in repo.
- Retrieval index: sqlite/fts plus optional vector index.

## Agent Concurrency Recommendation

Using the previously shared target profile (`16 GB RAM + RTX 5070 Ti 16 GB VRAM`), pending host verification:

- Cloud-first mode (recommended now):
  - Simultaneous active workers: 3
    - 1x Orchestrator
    - 1x Observer (async, lightweight)
    - 1x Retriever/reranker
  - Reflector runs scheduled, not always-on.

- Local-first mode (optional):
  - Simultaneous generation workers: max 2
  - Prefer:
    - 1x 7B/8B quantized generation model
    - 1x embedding/reranker model
  - Avoid running two 14B generation models concurrently on 16 GB VRAM.

## Local Models: What to Run Where

Recommended split:

- Keep cloud for:
  - final orchestrator reasoning
  - conflict-heavy reflection jobs

- Use local for:
  - embeddings
  - first-pass observation compression
  - reranking

Rationale:
- This keeps API cost low while preserving quality where reasoning depth matters.

## Token/Cost Model (OpenAI)

Important billing note:
- ChatGPT Plus subscription does not include API token credits.
- OpenClaw/API-based calls are billed via API usage separately.

Reference pricing used (as of 2026-02-25):
- `gpt-4.1-mini`: input `$0.40 / 1M`, output `$1.60 / 1M`
- `gpt-4.1-nano`: input `$0.10 / 1M`, output `$0.40 / 1M`
- `text-embedding-3-small`: ~`$0.02 / 1M` tokens

### Monthly estimates (observer + reflector included)

Assumptions:
- Orchestrator per turn: 3k input, 900 output (`gpt-4.1-mini`)
- Observer every 8 turns: 1.2k input, 250 output (`gpt-4.1-nano`)
- Reflector daily: 18k input, 1.4k output (`gpt-4.1-mini`)
- Embedding volumes by usage tier:
  - 30 turns/day -> 1M embedding tokens/month
  - 100 turns/day -> 3M embedding tokens/month
  - 300 turns/day -> 10M embedding tokens/month

Estimated total:
- 30 turns/day: ~`$2.70`/month
- 100 turns/day: ~`$8.35`/month
- 300 turns/day: ~`$24.49`/month

Interpretation:
- With aggressive lane budgeting and local embeddings, OM memory costs stay modest.
- Cost spikes mostly come from large-output orchestrator calls, not embeddings.

## Retrieval Policy (SOTA-Aligned, Practical)

Policy for each important turn:

1. Always include core memory (`SOUL.md`, `USER.md`, `MEMORY.md`) with strict token cap.
2. Entity hit pass:
- detect entities from user message
- load matching `bank/entities/*` pages
3. Recency pass:
- include last 24-72h episodic window
4. Semantic pass:
- hybrid search (keyword + dense) over memory/index
- fetch top-k candidates
5. Rerank pass:
- rerank candidates with recency, confidence, and query relevance
6. Conflict pass:
- when contradictory facts appear, prefer newest + highest confidence + best provenance

## Truncation/Compression Policy

Token budgets (starting defaults):
- Core: 20%
- Entity: 20%
- Recent episodic: 30%
- Semantic/retrieved: 25%
- Scratch/system reserve: 5%

Compression triggers:
- Observer trigger:
  - every 10-12 user turns, or
  - when new episodic content > 5k tokens
- Reflector trigger:
  - daily scheduled pass
  - weekly deep merge pass

Never delete raw logs.
Only compress into:
- observation entries
- bank updates
- memory summaries with provenance

## External Ecosystem Signals (for retrieval policy)

Projects repeatedly referenced in active memory-system discussions and repos:

- `mastra-ai/mastra` (Observational Memory implementation + published benchmark write-up)
- `vectorize-io/hindsight` (long-context memory benchmark/performance project)
- `supermemoryai/supermemory` (open-source memory layer project)
- `mem0ai/mem0` (intelligent memory layer with extraction/update flow)
- `getzep/graphiti` + Zep docs (temporal + hybrid retrieval graph)
- `letta-ai/letta` (agent memory blocks + long-term memory abstractions)

These are useful reference points for policy patterns:
- extraction before storage
- hybrid retrieval over pure vectors
- explicit memory typing (core/entity/episodic/semantic)
- benchmark-driven evaluation

## Staged Implementation Plan

### Phase 0 (completed in this change set)

- Seed memory scaffolding:
  - `bank/*`
  - `OBSERVATIONS.md` template and first entry
  - `REFFLECTIONS.md` template and first entry
  - `memory/templates/daily-memory-template.md`
  - `MEMORY.md` durable structure

### Phase 1 (main machine)

- Configure embedding provider in OpenClaw.
- Run indexing and validate recall on known entities/decisions.
- Add retrieval logs for offline audit.

Exit criteria:
- recall tests return expected memory hits with evidence.

### Phase 2

- Implement observer automation (threshold-triggered).
- Write compact observations into structured sections.

Exit criteria:
- episodic growth rate slows; no key memory regressions.

### Phase 3

- Implement daily + weekly reflector jobs.
- Add confidence decay/reinforcement logic.

Exit criteria:
- conflicts are surfaced and resolved; bank remains concise.

## Risks and Mitigations

- Risk: confidence drift in reflective pages.
  - Mitigation: mandatory evidence links and periodic recalibration.

- Risk: retrieval noise from over-broad top-k.
  - Mitigation: rerank + strict token budget per lane.

- Risk: hidden API spend spikes.
  - Mitigation: per-worker usage counters and monthly budget guardrails.

## References Checked (2026-02-25)

- OpenAI API pricing:
  - https://openai.com/api/pricing
- OpenAI billing separation (ChatGPT vs API):
  - https://help.openai.com/en/articles/8156019-how-can-i-move-my-chatgpt-subscription-to-the-api
- OpenAI embeddings guide:
  - https://platform.openai.com/docs/guides/embeddings
- Mastra Observational Memory docs:
  - https://mastra.ai/docs/memory/observational-memory
- Mastra OM benchmark write-up:
  - https://mastra.ai/blog/benchmarking-observational-memory
- Hindsight repo:
  - https://github.com/vectorize-io/hindsight
- Supermemory repo:
  - https://github.com/supermemoryai/supermemory
- Mem0 repo and docs:
  - https://github.com/mem0ai/mem0
  - https://docs.mem0.ai
- Zep Graphiti and docs:
  - https://github.com/getzep/graphiti
  - https://help.getzep.com/graphiti/knowledge-graph-overview
- Letta docs and repo:
  - https://docs.letta.com/guides/agents/memory
  - https://github.com/letta-ai/letta
- LongMemEval benchmark repo:
  - https://github.com/SakanaAI/longmemeval

X/source-note:
- Direct unauthenticated X HTML snapshots in this repo are not reliably text-extractable.
- Local snapshot pointers still captured:
  - https://x.com/alexfinn/status/2024169334344679783
  - https://x.com/matthewberman/status/2023843493765157235
