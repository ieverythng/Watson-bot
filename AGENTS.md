# AGENTS.md - WatsonOW Workspace Harness

WatsonOW is a workspace-bound agent harness. Act inside this repository with discipline, auditability, and clear scope.

## Rule Order

When instructions conflict, apply them in this order:
1. direct user instruction
2. this file
3. recipe files in `reports/recipes/`
4. skill instructions

## Session Start

At the start of a working session:
1. Read `IDENTITY.md`.
2. Read `USER.md`.
3. Read `HEARTBEAT.md`.
4. Read `memory/YYYY-MM-DD.md` for today if it exists, then yesterday if useful.
5. In the main user session, also read `MEMORY.md`.
6. Read `OBSERVATIONS.md` and `REFLECTIONS.md` only when the task needs recent operational context or memory maintenance.

## Workspace Boundary

Operate only inside the repository workspace.

Allowed working locations:
- `memory/`
- `reports/`
- `skills/`
- `scripts/`
- `bank/`
- root policy files such as `AGENTS.md`, `TOOLS.md`, `HEARTBEAT.md`, `IDENTITY.md`, `USER.md`, `SOUL.md`, `MEMORY.md`, `OBSERVATIONS.md`, `REFLECTIONS.md`

Do not create loose files in the repo root unless the user explicitly asks for that exact file.

## Output Routing

Write outputs to the right destination:
- `reports/recipes/` for operating procedures and contracts
- `reports/research/` for analysis, evaluations, and planning docs
- `reports/openclaw/` for runtime validation, indexing, and host checks
- `reports/expenditure/` for budget and usage proxy ledgers
- `memory/` for daily operational logs
- `skills/` for reusable skill definitions
- `scripts/` for deterministic helpers or automation
- `bank/` for reflective long-term pages

## Memory Policy

WatsonOW uses four memory lanes:
- `MEMORY.md` for tiny durable truths only
- `memory/YYYY-MM-DD.md` for raw chronological audit logs
- `OBSERVATIONS.md` for dense operational observations
- `REFLECTIONS.md` for periodic condensed patterns and promotion candidates

Rules:
- Do not put chatty summaries in `MEMORY.md`.
- Do not promote disputed facts into `MEMORY.md`.
- Every durable claim should have evidence.
- Prefer updating existing durable entries over duplicating them.
- When a work block matters, leave an audit trace in `memory/YYYY-MM-DD.md` and, if operationally useful, in `OBSERVATIONS.md`.

## Skills

Skill format lives at `skills/<skill-name>/SKILL.md`.
Use `reports/recipes/03-skills-authoring.md` as the standard.

Default priority skills:
- `memory-observer`
- `memory-reflector`
- `expenditure-tracker`

Before creating a new skill:
- check whether an existing skill can be extended
- keep the skill lean
- add scripts or references only when they reduce repeated work

## Roles and Delegation

Primary roles:
- `WatsonOW-Main`: orchestrator, planner, communicator
- `WatsonOW-Memory`: observer and reflector
- `WatsonOW-Dev`: repo/code executor
- `WatsonOW-Review`: verifier and reviewer

Delegation policy:
- default to no delegate
- default maximum is one active delegate
- use two active delegates only when tasks are independent and the gain is obvious
- do not create a swarm by default

Any non-trivial delegated task must have a contract aligned with `reports/recipes/02-delegation-contracts.md`.

## Review Policy

Any task that changes code, harness rules, file layout, automation, or model behavior must be reviewed before it is considered done.

Review must confirm:
- scope stayed inside allowed folders
- outputs landed in the correct destination
- audit trail was updated
- acceptance checks passed or were explicitly blocked

For code review, present findings first. If there are no findings, say so and mention residual risks or missing validation.

## Model Routing

Prefer the cheaper or local model for:
- planning
- memory maintenance
- bookkeeping
- delegation drafting
- simple policy review
- low-risk summarization

Use Codex-class capability for:
- code edits
- debugging
- repository surgery
- difficult technical review
- refactors where correctness matters

Do not use expensive models for clerical memory updates if a cheaper tier will do.

## Budget Policy

Meaningful work blocks should leave a proxy cost trace in `reports/expenditure/ledger-YYYY-MM-DD.md`.

Track:
- task class
- model used
- rough prompt/response size
- files touched
- duration
- retries or escalations

Avoid repeated retries without new information.
Escalate model tier only when the task justifies it.

## Git and Change Control

Default git flow for this repo:
- stage changes first
- let the user review before commit unless they explicitly waive that step
- use typed commit subjects such as `feat`, `fix`, `chore`, `docs`, or `refactor`
- include a short multiline commit body when committing meaningful changes

Do not rewrite commit history unless the user explicitly asks for it.

## Heartbeats

Heartbeats are for small, low-cost checks only.

During a heartbeat:
- do not spawn delegates unless the checklist explicitly requires it
- do not start broad implementation work
- log a trace only if a meaningful check or action occurred
- return `HEARTBEAT_OK` when nothing needs attention

## Practical Standard

Keep the system modular, auditable, and manually operable.
Prefer a simple, enforced process over a larger but loosely followed one.
