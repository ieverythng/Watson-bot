# Performance Investigation Contract
- timestamp_utc: 2026-03-11T19-09-09Z
- repo: /home/juanbeck/Watson

## Delegation Contract
- Objective: Investigate likely CPU bottlenecks affecting gaming performance on Juan's machine, assess storage pressure/cleanup opportunities, and produce an actionable optimization plan plus a Discord setup plan.
- Reason for delegation: Multi-source system analysis across CPU, GPU, memory, storage, drivers, and workflow recommendations.
- Delegate role: WatsonOW-Dev
- Model tier: codex
- Scope: local system inspection and workspace report generation only.
- Allowed folders: /home/juanbeck/Watson/**
- Allowed tools: read, write, exec
- Forbidden actions: no destructive cleanup, no package installs, no registry edits, no driver changes, no process killing without explicit user approval.
- Deliverables:
  1. system bottleneck investigation report
  2. storage/purge recommendations
  3. prioritized action list for Marathon and similar games
  4. Discord onboarding plan for Watson
- Acceptance checks:
  1. CPU/GPU/storage state inspected with commands
  2. recommendations distinguish low-risk tweaks from later invasive steps
  3. report saved under reports/openclaw/
- Budget expectation: single-pass investigation with local inspection and synthesis
- Rollback plan: none needed; read-only investigation plus report write only
- Escalation triggers: missing runtime commands, unclear hardware visibility, or need for destructive cleanup decisions
- Audit destination: this report + memory/2026-03-11.md + expenditure ledger
