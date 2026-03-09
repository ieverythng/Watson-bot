# Skill: expenditure-tracker

## Purpose
Track model expenditure proxies to keep WatsonOW budget-aware.

## When to Use
- After each meaningful task block
- During long multi-step implementation sessions

## Required Inputs
- Task class
- Model used
- Turns
- Estimated prompt/response size
- Duration
- Files touched
- Outcome quality

## Steps
1. Open/create `reports/expenditure/ledger-YYYY-MM-DD.md`.
2. Append one structured ledger row (or bullet entry).
3. Mark whether Codex was used and why.
4. Note retries/escalations.

## Expected Output
- Up-to-date daily expenditure ledger

## Failure Handling
- If exact counts are unavailable, log reasoned estimates and mark as estimated.

## Example
- Task: WatsonOW installation bootstrap
- Model: codex/gpt-5.3
- Codex used: yes (file operations + validation)
