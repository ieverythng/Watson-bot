---
name: memory-reflector
description: Use this skill at milestones, session boundaries, or when observations become noisy to condense recent signals into REFLECTIONS.md and promote only durable truths into MEMORY.md or bank pages.
---

# Memory Reflector

## When to Use
- At the end of a meaningful session or milestone
- When `OBSERVATIONS.md` has accumulated repeated signals
- When repo direction, workflow, or policy changed
- Before promoting anything new into `MEMORY.md`

## Inputs
- `window`: dates or entries under review
- `candidate_signals`: repeated or durable observations
- `evidence`: source files, commands, or artifacts
- `conflicts`: unresolved contradictions, if any
- `promotion_targets`: optional `MEMORY.md` or `bank/*` destinations

## Steps
1. Read the relevant window from `OBSERVATIONS.md`, recent `memory/YYYY-MM-DD.md` files, current `REFLECTIONS.md`, and any existing target memory pages.
2. Separate session noise from repeated patterns, durable workflow changes, and unresolved conflicts.
3. Append or update a compact reflection entry in `REFLECTIONS.md` using the repo schema:
   - `id`
   - `window`
   - `themes`
   - `durable_updates`
   - `conflicts`
   - `actions`
   - `evidence`
4. Promote only stable, evidence-backed truths:
   - `MEMORY.md` for tiny durable truths
   - `bank/world.md` for environment or platform facts
   - `bank/experience.md` for learned patterns
   - `bank/opinions.md` for preferences with confidence
   - `bank/entities/*` for entity-specific facts
5. Leave disputed or weakly supported items in `REFLECTIONS.md` until resolved.

## Outputs
- One reflection entry in `REFLECTIONS.md`
- Optional small promotion to `MEMORY.md` or `bank/*`
- Clear unresolved conflicts if promotion was deferred

## Failure Handling
- If evidence is weak, keep the result in `REFLECTIONS.md` only.
- If multiple sources disagree, record the conflict and do not promote.
- If there is no durable signal, make no promotion and keep the daily log as the only audit trail.

## Examples
- Reflection theme:
  - `WatsonOW harness should stay workspace-bound, staged-first, and budget-aware.`
- Durable update:
  - `Use typed commit subjects with short multiline bodies when commits are requested.`
