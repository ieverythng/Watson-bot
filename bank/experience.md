# Experience

Execution learnings that should inform future behavior.

## Learned Patterns

- Explicit git workflow declarations improve trust and reduce accidental regressions.
  - Confidence: 0.95
  - Evidence: user workflow instructions across 2026-02-25 and 2026-03-11

- Keeping markdown as canonical memory reduces brittleness and improves debugging.
  - Confidence: 0.90
  - Evidence: `reports/research/memory-architecture-review-2026-02-24.md`

- Memory quality depends on retrieval policy and curation, not vector store alone.
  - Confidence: 0.88
  - Evidence: same report, section "Caution"

## To Validate

- Best local/cloud split for OM workloads on 16 GB RAM + 16 GB VRAM.
- Observer thresholds that minimize token spend without losing signal.
