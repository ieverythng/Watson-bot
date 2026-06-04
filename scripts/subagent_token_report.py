#!/usr/bin/env python3
"""Post-subagent token usage report.

Usage:
  python3 subagent_token_report.py [parent_session_id]

If parent_session_id is omitted, uses the most recent non-archived session as parent.
Prints a compact footer showing child session token usage with budget context.
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "state.db"

# ChatGPT Plus soft limits (adjust based on actual plan)
FIVE_HOUR_LIMIT = 200_000_000  # ~200M tokens rolling 5hr window (generous estimate)
WEEKLY_LIMIT = 1_000_000_000   # ~1B tokens weekly (generous estimate)


def main():
    parent_id = sys.argv[1] if len(sys.argv) > 1 else None

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    now = datetime.now()
    five_hours_ago = now - timedelta(hours=5)
    week_ago = now - timedelta(days=7)

    # If no parent_id given, find the most recent active session
    if not parent_id:
        cur = db.execute(
            "SELECT id FROM sessions WHERE archived=0 ORDER BY started_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        parent_id = row["id"] if row else None

    if not parent_id:
        print("⚠️ No active session found")
        db.close()
        return

    # --- Child sessions (subagents) ---
    children = db.execute(
        """SELECT model, input_tokens, output_tokens, billing_provider,
                   estimated_cost_usd, actual_cost_usd, cost_status
           FROM sessions WHERE parent_session_id=? AND archived=0""",
        (parent_id,),
    ).fetchall()

    # --- 5-hour window totals for paid models ---
    five_hr = db.execute(
        """SELECT COALESCE(SUM(input_tokens),0) as inp,
                  COALESCE(SUM(output_tokens),0) as outp
           FROM sessions
           WHERE started_at > ? AND archived=0
             AND billing_provider IN ('openai-codex','openai')""",
        (five_hours_ago.timestamp(),),
    ).fetchone()

    # --- Weekly totals for paid models ---
    weekly = db.execute(
        """SELECT COALESCE(SUM(input_tokens),0) as inp,
                  COALESCE(SUM(output_tokens),0) as outp
           FROM sessions
           WHERE started_at > ? AND archived=0
             AND billing_provider IN ('openai-codex','openai')""",
        (week_ago.timestamp(),),
    ).fetchone()

    # Print report
    print("📊 Token Usage Report")
    print("=" * 40)

    if children:
        print("\n🤖 Subagent sessions:")
        total_child_in = 0
        total_child_out = 0
        for c in children:
            cost = c["actual_cost_usd"] or c["estimated_cost_usd"] or 0.0
            status = c["cost_status"] or "?"
            print(
                f"  {c['model']:20s} | in={c['input_tokens']:>10,} "
                f"out={c['output_tokens']:>10,} | ${cost:.4f} [{status}]"
            )
            total_child_in += c["input_tokens"]
            total_child_out += c["output_tokens"]

        print(
            f"  {'TOTAL':20s} | in={total_child_in:>10,} "
            f"out={total_child_out:>10,}"
        )
    else:
        print("\n  No subagent sessions found")

    # Budget context
    five_total = five_hr["inp"] + five_hr["outp"]
    week_total = weekly["inp"] + weekly["outp"]

    five_pct = (five_total / FIVE_HOUR_LIMIT) * 100 if FIVE_HOUR_LIMIT else 0
    week_pct = (week_total / WEEKLY_LIMIT) * 100 if WEEKLY_LIMIT else 0

    print(f"\n💰 Budget (paid models only):")
    print(f"  5hr window: {five_total:>12,} / {FIVE_HOUR_LIMIT:,} tokens ({five_pct:.1f}%)")
    print(f"  Weekly:     {week_total:>12,} / {WEEKLY_LIMIT:,} tokens ({week_pct:.1f}%)")

    # Warning if close to limits
    if five_pct > 80:
        print(f"\n  ⚠️  5hr window at {five_pct:.0f}% — consider reducing subagent usage!")
    if week_pct > 80:
        print(f"\n  ⚠️  Weekly at {week_pct:.0f}% — conserve tokens!")

    db.close()


if __name__ == "__main__":
    main()
