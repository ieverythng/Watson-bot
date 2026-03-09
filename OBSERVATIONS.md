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
