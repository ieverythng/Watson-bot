#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

HERMES_HOME = Path.home() / ".hermes"
STATE_DB = HERMES_HOME / "state.db"
ROOT = Path("/home/juanbeck/Watson")
EXP_DIR = ROOT / "reports" / "expenditure"
HOURLY_DIR = EXP_DIR / "hourly"
TZ = ZoneInfo("Europe/Madrid")
SUMMARY_START = "<!-- hermes-usage-summary:start -->"
SUMMARY_END = "<!-- hermes-usage-summary:end -->"
TITLE_PREFIX = "# Expenditure Ledger - "


@dataclass
class SessionRow:
    session_id: str
    source: str | None
    model: str | None
    message_count: int
    tool_call_count: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    billing_provider: str | None
    billing_base_url: str | None
    billing_mode: str | None
    estimated_cost_usd: float | None
    actual_cost_usd: float | None
    cost_status: str | None
    cost_source: str | None
    started_at: float
    ended_at: float | None
    title: str | None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Hermes usage reporting for the Watson workspace.")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--date", default=dt.datetime.now(TZ).date().isoformat(), help="Target date in Europe/Madrid timezone (YYYY-MM-DD).")
    common.add_argument("--db", default=str(STATE_DB), help="Path to Hermes state.db")

    status = sub.add_parser("status", parents=[common], help="Print usage summary")
    status.add_argument("--json", action="store_true", help="Emit JSON")

    report = sub.add_parser("report", parents=[common], help="Generate markdown report")
    report.add_argument("--write", action="store_true", help="Write report into reports/expenditure/ledger-YYYY-MM-DD.md")

    return p.parse_args()


def local_day_bounds(target: str) -> tuple[dt.datetime, dt.datetime]:
    day = dt.date.fromisoformat(target)
    start = dt.datetime.combine(day, dt.time.min, tzinfo=TZ)
    end = start + dt.timedelta(days=1)
    return start, end


def load_sessions(db_path: Path, start: dt.datetime, end: dt.datetime) -> list[SessionRow]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT id AS session_id, source, model, message_count, tool_call_count, input_tokens, output_tokens,
               cache_read_tokens, cache_write_tokens, reasoning_tokens,
               billing_provider, billing_base_url, billing_mode,
               estimated_cost_usd, actual_cost_usd, cost_status, cost_source,
               started_at, ended_at, title
        FROM sessions
        WHERE started_at >= ? AND started_at < ?
        ORDER BY started_at ASC
        """,
        (start.astimezone(dt.timezone.utc).timestamp(), end.astimezone(dt.timezone.utc).timestamp()),
    ).fetchall()
    conn.close()
    return [SessionRow(**dict(row)) for row in rows]


def session_kind(row: SessionRow) -> str:
    provider = (row.billing_provider or "").lower()
    base_url = (row.billing_base_url or "").lower()
    model = (row.model or "").lower()
    if provider == "openai-codex" or "chatgpt.com/backend-api/codex" in base_url:
        return "codex"
    if provider in {"custom", "local"} or "172.24.16.1:11434" in base_url or "127.0.0.1:11434" in base_url:
        return "local"
    if model.startswith("qwen") or model.startswith("gpt-oss"):
        return "local"
    return "other"


def cost_value(row: SessionRow) -> float:
    if row.actual_cost_usd is not None:
        return float(row.actual_cost_usd)
    if row.estimated_cost_usd is not None:
        return float(row.estimated_cost_usd)
    return 0.0


def summarize(rows: list[SessionRow], target_date: str) -> dict:
    buckets = {
        "codex": {"sessions": [], "input": 0, "output": 0, "cached": 0, "reasoning": 0, "cost": 0.0, "messages": 0, "tools": 0},
        "local": {"sessions": [], "input": 0, "output": 0, "cached": 0, "reasoning": 0, "cost": 0.0, "messages": 0, "tools": 0},
        "other": {"sessions": [], "input": 0, "output": 0, "cached": 0, "reasoning": 0, "cost": 0.0, "messages": 0, "tools": 0},
    }
    hourly: dict[str, dict[str, float | int]] = {}

    for row in rows:
        kind = session_kind(row)
        bucket = buckets[kind]
        bucket["sessions"].append(row)
        bucket["input"] += row.input_tokens or 0
        bucket["output"] += row.output_tokens or 0
        bucket["cached"] += (row.cache_read_tokens or 0) + (row.cache_write_tokens or 0)
        bucket["reasoning"] += row.reasoning_tokens or 0
        bucket["cost"] += cost_value(row)
        bucket["messages"] += row.message_count or 0
        bucket["tools"] += row.tool_call_count or 0

        started = dt.datetime.fromtimestamp(row.started_at, tz=dt.timezone.utc).astimezone(TZ)
        hour_key = started.strftime("%Y-%m-%d %H:00 %Z")
        entry = hourly.setdefault(hour_key, {"sessions": 0, "input": 0, "output": 0, "cached": 0, "cost": 0.0})
        entry["sessions"] += 1
        entry["input"] += row.input_tokens or 0
        entry["output"] += row.output_tokens or 0
        entry["cached"] += (row.cache_read_tokens or 0) + (row.cache_write_tokens or 0)
        entry["cost"] += cost_value(row)

    return {
        "date": target_date,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "rows": rows,
        "buckets": buckets,
        "hourly": hourly,
    }


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}"


def fmt_cost(value: float) -> str:
    return f"${value:,.4f}"


def render_markdown(summary: dict) -> str:
    rows: list[SessionRow] = summary["rows"]
    buckets = summary["buckets"]
    hourly = summary["hourly"]
    lines: list[str] = []
    lines.append(SUMMARY_START)
    lines.append(f"## Hermes Usage Summary ({summary['date']})")
    lines.append("")
    lines.append(f"- Generated: {summary['generated_at']}")
    lines.append(f"- Sessions tracked: {len(rows)}")
    lines.append(f"- Codex sessions: {len(buckets['codex']['sessions'])}")
    lines.append(f"- Local sessions: {len(buckets['local']['sessions'])}")
    lines.append(f"- Other sessions: {len(buckets['other']['sessions'])}")
    lines.append(f"- Codex estimated cost: {fmt_cost(buckets['codex']['cost'])}")
    lines.append(f"- Local estimated cost: {fmt_cost(buckets['local']['cost'])}")
    lines.append("")

    lines.append("### Session Breakdown")
    lines.append("")
    lines.append("| Session | Kind | Model | Input | Output | Cached | Reasoning | Cost | Msgs | Tools |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    if rows:
        for row in rows:
            kind = session_kind(row)
            label = row.title or row.session_id
            lines.append(
                f"| {label} | {kind} | {(row.model or '-')} | {fmt_int(row.input_tokens)} | {fmt_int(row.output_tokens)} | {fmt_int((row.cache_read_tokens or 0) + (row.cache_write_tokens or 0))} | {fmt_int(row.reasoning_tokens)} | {fmt_cost(cost_value(row))} | {fmt_int(row.message_count)} | {fmt_int(row.tool_call_count)} |"
            )
    else:
        lines.append("| - | - | - | 0 | 0 | 0 | 0 | $0.0000 | 0 | 0 |")
    lines.append("")

    lines.append("### Bucket Totals")
    lines.append("")
    lines.append("| Kind | Sessions | Input | Output | Cached | Reasoning | Cost |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for kind in ("codex", "local", "other"):
        bucket = buckets[kind]
        lines.append(
            f"| {kind} | {len(bucket['sessions'])} | {fmt_int(bucket['input'])} | {fmt_int(bucket['output'])} | {fmt_int(bucket['cached'])} | {fmt_int(bucket['reasoning'])} | {fmt_cost(bucket['cost'])} |"
        )
    lines.append("")

    lines.append("### Hourly Activity")
    lines.append("")
    lines.append("| Hour | Sessions | Input | Output | Cached | Cost |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    if hourly:
        for hour, vals in sorted(hourly.items()):
            lines.append(
                f"| {hour} | {vals['sessions']} | {fmt_int(vals['input'])} | {fmt_int(vals['output'])} | {fmt_int(vals['cached'])} | {fmt_cost(float(vals['cost']))} |"
            )
    else:
        lines.append("| - | 0 | 0 | 0 | 0 | $0.0000 |")
    lines.append("")
    lines.append(SUMMARY_END)
    lines.append("")
    return "\n".join(lines)


def ensure_ledger_file(target_date: str) -> Path:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    path = EXP_DIR / f"ledger-{target_date}.md"
    if not path.exists():
        path.write_text(f"{TITLE_PREFIX}{target_date}\n\n")
    return path


def replace_or_append_section(existing: str, section: str) -> str:
    if SUMMARY_START in existing and SUMMARY_END in existing:
        start = existing.index(SUMMARY_START)
        end = existing.index(SUMMARY_END) + len(SUMMARY_END)
        prefix = existing[:start].rstrip()
        suffix = existing[end:].lstrip("\n")
        body = section.strip()
        parts = [p for p in [prefix, body, suffix] if p]
        return "\n\n".join(parts) + "\n"
    return existing.rstrip() + "\n\n" + section.strip() + "\n"


def write_outputs(summary: dict) -> dict:
    target_date = summary["date"]
    ledger_path = ensure_ledger_file(target_date)
    section = render_markdown(summary)
    ledger_path.write_text(replace_or_append_section(ledger_path.read_text(), section))

    HOURLY_DIR.mkdir(parents=True, exist_ok=True)
    generated = dt.datetime.now(TZ)
    hourly_path = HOURLY_DIR / f"hermes-usage-{generated.strftime('%Y-%m-%d-%H')}.json"
    hourly_payload = {
        "date": summary["date"],
        "generated_at": summary["generated_at"],
        "hourly": summary["hourly"],
        "bucket_totals": {
            kind: {
                "sessions": len(data["sessions"]),
                "input": data["input"],
                "output": data["output"],
                "cached": data["cached"],
                "reasoning": data["reasoning"],
                "cost": data["cost"],
            }
            for kind, data in summary["buckets"].items()
        },
    }
    hourly_path.write_text(json.dumps(hourly_payload, indent=2))
    return {"ledger": str(ledger_path), "hourly": str(hourly_path)}


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"state.db not found: {db_path}")

    start, end = local_day_bounds(args.date)
    rows = load_sessions(db_path, start, end)
    summary = summarize(rows, args.date)

    if args.cmd == "status":
        payload = {
            "date": summary["date"],
            "generated_at": summary["generated_at"],
            "session_count": len(rows),
            "bucket_totals": {
                kind: {
                    "sessions": len(data["sessions"]),
                    "input": data["input"],
                    "output": data["output"],
                    "cached": data["cached"],
                    "reasoning": data["reasoning"],
                    "cost": data["cost"],
                }
                for kind, data in summary["buckets"].items()
            },
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Hermes usage for {summary['date']}")
            for kind in ("codex", "local", "other"):
                data = payload["bucket_totals"][kind]
                print(
                    f"- {kind}: sessions={data['sessions']} input={fmt_int(data['input'])} output={fmt_int(data['output'])} cached={fmt_int(data['cached'])} reasoning={fmt_int(data['reasoning'])} cost={fmt_cost(data['cost'])}"
                )
        return 0

    section = render_markdown(summary)
    if args.write:
        outputs = write_outputs(summary)
        print(json.dumps({"status": "written", "outputs": outputs}, indent=2))
    else:
        print(section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
