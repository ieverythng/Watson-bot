---
name: expenditure-tracker
description: Use this skill after meaningful work blocks, reviews, or delegate runs to append a budget-aware ledger entry under reports/expenditure and record proxy model usage signals.
---

# Expenditure Tracker

## When to Use
- After a meaningful implementation or debugging block
- After review or validation runs
- After delegate execution or retry loops
- After any Codex-heavy task that should leave a cost proxy trail

## Inputs
- `time`
- `task_class`
- `model_used`
- `turns`
- `estimated_prompt_size`
- `estimated_response_size`
- `codex_used`
- `duration`
- `files_touched`
- `outcome_quality`
- `retries_or_escalations`

## Steps
1. Open or create `reports/expenditure/ledger-YYYY-MM-DD.md`.
2. Append one structured entry using the current repo format:
   - `Time`
   - `Task class`
   - `Model used`
   - `Turns`
   - `Estimated prompt size`
   - `Estimated response size`
   - `Codex used`
   - `Duration`
   - `Files touched`
   - `Outcome quality`
   - `Retries/escalations`
3. If multiple models or delegates were involved, record the primary model in `Model used` and mention delegates in the task description or retries field.
4. Use coarse estimates like `low|medium|high` when exact counts are unavailable.
5. Cross-link major artifacts or reports when they explain why the spend was justified.

## Outputs
- One appended entry in `reports/expenditure/ledger-YYYY-MM-DD.md`

## Failure Handling
- If exact usage metrics are unavailable, log estimates and mark them as estimated instead of skipping the ledger.
- If the task aborted, still log the partial work block and the reason it stopped.
- If no meaningful work happened, do not create noise by logging a trivial entry.

## Examples
- `Task class`: `WatsonOW harness hardening`
- `Model used`: `openai-codex/gpt-5.3-codex`
- `Estimated prompt size`: `medium`
- `Estimated response size`: `medium`
- `Outcome quality`: `pass`
