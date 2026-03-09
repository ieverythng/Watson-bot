# Skill: memory-observer

## Purpose
Capture compact, evidence-backed operational observations after meaningful work blocks.

## When to Use
- After tool runs with meaningful outcomes
- After config/repo changes
- After completing a task block

## Required Inputs
- Context summary
- Change performed
- Evidence path(s)
- Risk/uncertainty
- Next step

## Steps
1. Read latest `memory/YYYY-MM-DD.md` and `OBSERVATIONS.md`.
2. Draft one compact observation entry.
3. Append observation to `OBSERVATIONS.md`.
4. Add corresponding audit line in daily memory file.

## Expected Output
- New observation entry in `OBSERVATIONS.md`
- Audit trail in `memory/YYYY-MM-DD.md`

## Failure Handling
- If evidence is missing, log uncertainty explicitly and mark confidence lower.

## Example
- Scope: infra
- Observation: "Local memory provider configured and index healthy."
- Evidence: `openclaw memory status --deep`
