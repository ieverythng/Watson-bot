# OM Orchestration Metrics Spec - 2026-02-25

## Objective

Measure whether the OM rollout improves recall quality and operational reliability without unacceptable latency or cost growth.

## Scope

Workers in scope:
1. Orchestrator
2. Retriever/reranker
3. Observer
4. Reflector (scheduled)

## Required Metrics

## Reliability

- `turn_success_rate`: successful assistant turns / total turns
  - Target: `>= 99.0%`
- `retrieval_success_rate`: retrieval pipeline success / retrieval attempts
  - Target: `>= 99.5%`
- `index_freshness_minutes_p95`: p95 time from file update to searchable
  - Target: `<= 10 min`

## Retrieval Quality

- `known_fact_recall_at_3`: recall@3 on fixed probe set
  - Target: `>= 0.90`
- `citation_coverage`: answers with explicit evidence references / answers requiring memory
  - Target: `>= 0.95`
- `conflict_detection_rate`: detected contradictions / seeded contradictions
  - Target: `>= 0.90`

## Latency

- `orchestrator_latency_ms_p95`
  - Target: `<= 7000 ms` (cloud-first baseline)
- `retrieval_latency_ms_p95`
  - Target: `<= 1200 ms`
- `observer_latency_ms_p95`
  - Target: `<= 3000 ms`

## Cost

- `orchestrator_tokens_per_turn` (input/output)
- `observer_tokens_per_turn`
- `reflector_tokens_per_run`
- `monthly_memory_cost_usd_estimate`
  - Guardrail: remain within phase budget envelope from rollout plan

## Logging Contract

Write one NDJSON record per event:
- File: `reports/openclaw/metrics/om-metrics-YYYY-MM-DD.ndjson`

Schema:

```json
{
  "ts": "2026-02-25T22:10:00Z",
  "session_id": "agent:main:main",
  "turn_id": "T-2026-02-25-0123",
  "worker": "retriever",
  "event": "retrieval_complete",
  "ok": true,
  "latency_ms": 412,
  "tokens_in": 0,
  "tokens_out": 0,
  "cost_usd": 0.0000,
  "query": "staged workflow",
  "top_k": 5,
  "hits": 3,
  "hit_sources": ["MEMORY.md", "bank/entities/juan-bendek.md"],
  "notes": ""
}
```

## Retrieval Audit Artifacts

For each probe run, store command outputs:
- `reports/openclaw/retrieval/DATE/probe-*.json`

Mandatory probes:
1. `Juan Bendek`
2. `staged workflow`
3. `Observational Memory`
4. One intentionally conflicting fact pair (to test resolver behavior)

## Experiment Design

1. Baseline window (no OM retrieval):
- 2 days
- collect latency/cost/reliability only

2. OM enabled (Phase 1 retrieval):
- 2 days
- collect full metric set

3. Compare baseline vs OM:
- `delta_recall_at_3`
- `delta_orchestrator_latency_p95`
- `delta_monthly_cost_projection`

Go/No-Go:
- Go if recall improves and reliability targets hold, with no more than `+20%` orchestrator p95 latency increase.

## Weekly Review Template

1. Summary of metric deltas
2. New failure modes
3. Cost drift vs budget
4. Policy adjustments (token budgets, top-k, thresholds)
5. Action items and owner
