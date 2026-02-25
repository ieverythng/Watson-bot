# Experience

Execution learnings that should inform future behavior.

## Learned Patterns

- Staged-review workflow improves trust and reduces accidental regressions.
  - Confidence: 0.95
  - Evidence: active thread request (2026-02-25)

- Keeping markdown as canonical memory reduces brittleness and improves debugging.
  - Confidence: 0.90
  - Evidence: `reports/research/memory-architecture-review-2026-02-24.md`

- Memory quality depends on retrieval policy and curation, not vector store alone.
  - Confidence: 0.88
  - Evidence: same report, section "Caution"

## To Validate

- Best local/cloud split for OM workloads on 16 GB RAM + 16 GB VRAM.
- Observer thresholds that minimize token spend without losing signal.
