# Token Usage Report - 2026-06-04

## Scope
This report summarizes Hermes token usage for **today (2026-06-04)** and **this week (2026-06-01 through 2026-06-07)**, then proposes a lightweight **post-subagent token display** that can be auto-appended after each `delegate_task` run.

## Data sources and normalization notes
- Top-line daily and weekly totals below use the normalized figures supplied for this task.
- Per-model breakdown uses the live `~/.hermes/state.db` snapshot via `scripts/hermes_usage_report.py` schema, because the prompt included models-in-use but not exact per-model totals.
- Live DB counts were **47 sessions today / 136 this week**, versus the normalized **46 / 135** in the task brief. The difference appears to be zero-token or placeholder sessions (`gpt-5.5-low`, empty qwen entries, and one unknown row), so the normalized totals are used for the headline report.

## Executive summary
- **Today total:** ~31,164,476 tokens
- **Week total so far:** ~68,182,307 tokens
- **Today as share of week:** **45.7%**
- **Interpretation:** almost half of the week's token volume landed on a single day, indicating a concentrated usage spike rather than a smooth weekly burn.

## Assumed monitoring limits
No explicit daily/weekly token caps were provided in the task brief, so this report uses **recommended soft limits** for relative comparison:

- **Daily soft limit:** 35,000,000 total tokens
- **Weekly soft limit:** 120,000,000 total tokens

These are not enforced system limits; they are suggested operational thresholds for alerting and projection.

## Today - 2026-06-04

### Totals
| Metric | Value |
|---|---:|
| Sessions | 46 |
| Input tokens | 2,142,760 |
| Output tokens | 126,929 |
| Cached tokens | 28,885,750 |
| Reasoning tokens | 9,037 |
| **Total tokens** | **31,164,476** |

### Relative to daily limit
| Measure | Value |
|---|---:|
| Daily soft limit | 35,000,000 |
| Usage as % of daily limit | **89.0%** |
| Relative change vs limit | **-11.0%** |

Interpretation: today is already near a full daily soft-budget burn, but still remains just under the recommended threshold.

## This week - 2026-06-01 to 2026-06-07

### Totals so far
| Metric | Value |
|---|---:|
| Sessions | 135 |
| Input tokens | 4,452,258 |
| Output tokens | 284,770 |
| Cached tokens | 63,436,242 |
| Reasoning tokens | 9,037 |
| **Total tokens** | **68,182,307** |

### Relative to weekly limit
| Measure | Value |
|---|---:|
| Weekly soft limit | 120,000,000 |
| Usage as % of weekly limit | **56.8%** |
| Relative change vs limit | **-43.2%** |

### Today vs week
| Measure | Value |
|---|---:|
| Today share of weekly total | **45.7%** |
| Non-today share of weekly total | 54.3% |
| Avg daily burn so far (4 days elapsed) | 17,045,577 |
| Today vs current daily average | **+82.8%** |

Interpretation: usage is still under the weekly soft limit, but the intra-week distribution is highly uneven. Today is materially above the week-to-date daily average.

## Per-model breakdown

### Today (live `state.db` snapshot, grouped by active model/provider rows)
| Model | Sessions | Input | Output | Cached | Reasoning | Total | Share of today |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen36-turbo-hermes | 30 | 1,623,043 | 81,204 | 24,060,151 | 0 | 25,764,398 | 82.7% |
| gpt-5.4 | 7 | 549,328 | 47,976 | 4,942,336 | 9,273 | 5,548,913 | 17.8% |
| gpt-5.5-low | 8 | 0 | 0 | 0 | 0 | 0 | 0.0% |

Notes:
- `qwen36-turbo-hermes` is the dominant front-model lane and accounts for most daily volume.
- `gpt-5.4` carries the paid delegation/Codex lane; the ledger currently still shows **$0.0000**.
- `gpt-5.5-low` appears to be placeholder or failed sessions and contributes no measured tokens.

### Week so far (live `state.db` snapshot)
| Model | Sessions | Input | Output | Cached | Reasoning | Total | Share of week |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen36-turbo-hermes | 99 | 3,932,541 | 239,045 | 58,610,643 | 0 | 62,782,229 | 92.1% |
| gpt-5.4 | 7 | 549,328 | 47,976 | 4,942,336 | 9,273 | 5,548,913 | 8.1% |
| gpt-5.5-low | 17 | 0 | 0 | 0 | 0 | 0 | 0.0% |

## Projection to end of week
Two projections are useful:

### 1) Baseline projection: continue the week-to-date average
Formula: `week total so far / 4 elapsed days * 7 days`

- Current week-to-date average: **17,045,577 tokens/day**
- Projected week-end total: **119,319,037 tokens**
- Relative to weekly soft limit: **99.4% of limit**
- Relative change vs limit: **-0.6%**

Interpretation: if the remaining days normalize back toward the earlier average, the week likely finishes almost exactly on the proposed soft limit.

### 2) Spike projection: repeat today for the remaining 3 days
Formula: `current week total + (today total * 3)`

- Spike-case projected week-end total: **161,675,735 tokens**
- Relative to weekly soft limit: **134.7% of limit**
- Relative change vs limit: **+34.7%**

Interpretation: if today's pace persists through Sunday, the week will overshoot the recommended weekly threshold by roughly one-third.

## Risk readout
- **Daily risk:** elevated but not yet over threshold.
- **Weekly risk:** acceptable at present, but highly sensitive to whether today was an anomaly or the new pace.
- **Primary driver:** local qwen cached-token volume dominates both the day and the week.
- **Cost visibility issue:** `gpt-5.4` appears paid in routing terms but still reports `$0.0000`; token visibility is present, monetary visibility is not.

## Proposed post-subagent token display

### Goal
After every `delegate_task` run, append a compact footer showing what that specific subagent consumed, without requiring the caller to inspect a full ledger.

### Available fields
The delegated result already includes:
- `tokens.input`
- `tokens.output`
- `api_calls`
- `duration_seconds`
- `model`

That means the **cleanest solution is to append the footer directly from the delegate result**, not to re-query the DB unless needed for fallback or auditing.

### Recommended footer format
Compact single-line version:

```text
— subagent: gpt-5.4 · 5,492 in · 811 out · 2 api · 48s
```

Slightly richer version with total:

```text
— subagent: gpt-5.4 · 6,303 tok (5,492 in / 811 out) · 2 api · 48s
```

### Why this format works
- short enough to live at the bottom of every delegated reply
- preserves the key operational metrics
- makes expensive or unusually long subagents immediately visible
- avoids clutter from cached/reasoning/cost fields when they are unavailable or noisy

## How to make it automatic

### Preferred option: modify the delegation workflow
Append the footer in the parent workflow immediately after `delegate_task` returns.

Pseudo-implementation:

```python
result = delegate_task(...)

footer = (
    f"\n\n— subagent: {result.model}"
    f" · {result.tokens.input:,} in"
    f" · {result.tokens.output:,} out"
    f" · {result.api_calls} api"
    f" · {int(result.duration_seconds)}s"
)

final_text = result.output_text.rstrip() + footer
return final_text
```

Recommended behavior:
- always append for successful delegated runs
- append even on partial failures if token fields are present
- omit the footer only if token metadata is absent

### Fallback option: small script/snippet against `state.db`
Use a small script when the delegation layer cannot yet expose or append the metadata cleanly.

Important caveat:
- querying the **last session row** only works reliably if each subagent creates a distinct session.
- if a subagent can reuse an existing session, the correct method is **before/after snapshot delta** for that session ID.

#### Simplest last-session query
```sql
SELECT
  id,
  model,
  input_tokens,
  output_tokens,
  cache_read_tokens + cache_write_tokens AS cached_tokens,
  reasoning_tokens,
  started_at,
  ended_at
FROM sessions
ORDER BY started_at DESC
LIMIT 1;
```

#### Better delta approach
1. Capture `session_id` or current totals before `delegate_task` starts.
2. Run the delegated task.
3. Re-read the same session row.
4. Compute deltas for input/output/cache/reasoning.
5. Append the compact footer from those deltas.

#### Minimal Python footer helper
```python
from pathlib import Path
import sqlite3

DB = Path.home() / ".hermes" / "state.db"

def latest_session_usage():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT id, model, input_tokens, output_tokens, tool_call_count,
               started_at, ended_at
        FROM sessions
        ORDER BY started_at DESC
        LIMIT 1
        """
    ).fetchone()
    conn.close()
    return dict(row) if row else None
```

## Recommendation
1. **Use the delegation-workflow append path first.** It is simpler, cheaper, and more accurate because the delegate result already contains the needed metadata.
2. Keep the `state.db` helper only as a fallback or audit tool.
3. Add alerting thresholds on the compact footer later if needed, for example:
   - `!` when total subagent tokens exceed 25k
   - `!!` when duration exceeds 120s

## Bottom line
- Today is a **high-usage spike day** at **31.16M** total tokens.
- Week-to-date usage is **68.18M** total tokens.
- Today alone is **45.7%** of the week's usage.
- Against suggested soft limits, today is **89.0%** of daily budget and the week is **56.8%** of weekly budget so far.
- If the current week reverts to average pace, it ends at **119.3M** tokens, effectively right on the weekly threshold.
- If today repeats through the rest of the week, usage projects to **161.7M** tokens, or **+34.7% over** the recommended weekly limit.
- The best post-subagent token display is a **one-line footer appended directly from the `delegate_task` result metadata**.
