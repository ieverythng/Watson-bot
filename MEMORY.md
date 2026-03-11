# MEMORY.md

Curated long-term memory for Watson.
This file is not append-only. Keep it short, stable, and evidence-backed.

## Core Profile

- `owner.name`: Juan Bendek
- `owner.timezone`: Europe/Madrid
- `assistant.name`: Watson
- `assistant.role`: research and engineering co-pilot

## Durable Decisions

- `D-2026-02-25-01`: Use staged workflow for repo changes.
  - Decision: Stage changes first for review in Cursor; commit only after explicit go-ahead.
  - Status: superseded
  - Evidence: earlier thread instruction

- `D-2026-03-11-02`: Default Watson repo workflow is auto-commit.
  - Decision: Automatically commit changes Watson makes in this workspace unless Juan explicitly asks for review/staging-only.
  - Status: active
  - Evidence: direct user instruction on 2026-03-11

## Current Priorities

- Build Watson-Openclaw Observational Memory (OM) pipeline with:
  - hybrid memory lanes
  - auditable retrieval policy
  - scalable truncation/compression policy

## Operating Constraints

- Keep human-auditable markdown as canonical truth.
- Keep core memory small enough for routine prompt hydration.
- Prefer deterministic retrieval order over opaque full-history stuffing.

## Entity Index

- [Juan Bendek](bank/entities/juan-bendek.md)
- [Zsanett Jung](bank/entities/zsanett-jung.md)
