---
name: memory-observer
description: Use this skill after meaningful work blocks, tool runs, or repo/policy changes to write compact operational observations into OBSERVATIONS.md and the current daily memory log.
---

# Memory Observer

## When to Use
- After a meaningful tool run or implementation block
- After repo, config, harness, or policy changes
- After a review that found important risk or scope information
- When a threshold-triggered observer flow needs a manual write

## Inputs
- `date`: target day for `memory/YYYY-MM-DD.md`
- `scope`: `user|project|infra|process`
- `change`: what happened
- `evidence`: file path, command, or artifact proving it
- `confidence`: `0.00-1.00`
- `risk_or_uncertainty`: optional caveat
- `next_step`: optional follow-up

## Steps
1. Open `OBSERVATIONS.md` and `memory/YYYY-MM-DD.md`. Create the daily file from `memory/templates/daily-memory-template.md` if missing.
2. Check the latest observation entries to avoid writing the same signal twice.
3. Add a short raw log line to the daily memory file describing the work block and affected artifacts.
4. If the signal is operationally useful beyond the single session, append one observation entry to `OBSERVATIONS.md` using the repo schema:
   - `id`
   - `timestamp`
   - `scope`
   - `confidence`
   - `observation`
   - `evidence`
   - `expires`
5. If the observation suggests a durable policy or belief, note that as a reflection candidate in the daily file. Do not update `MEMORY.md` directly from this skill.

## Outputs
- One daily audit entry in `memory/YYYY-MM-DD.md`
- Zero or one new observation in `OBSERVATIONS.md`
- Optional reflection candidate note in the daily file

## Failure Handling
- If evidence is weak or incomplete, still log the event in the daily file but lower confidence and state the gap explicitly.
- If two facts conflict, write the conflict as uncertainty instead of asserting a durable observation.
- If the event is trivial or duplicate, keep it in the daily file only and skip `OBSERVATIONS.md`.

## Examples
- Daily log line:
  - `- Hardened AGENTS.md and HEARTBEAT.md for WatsonOW harness discipline; see reports/recipes/03-skills-authoring.md and AGENTS.md.`
- Observation entry:
  - `observation`: `Harness files now enforce workspace-bound outputs, staged-first git flow, and explicit model routing.`
  - `evidence`: `AGENTS.md`, `HEARTBEAT.md`, `reports/recipes/03-skills-authoring.md`
