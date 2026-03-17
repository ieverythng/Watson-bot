#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path('/home/juanbeck/Watson')
OPENCLAW_HOME = Path.home() / '.openclaw'
CODEX_AUTH = Path.home() / '.codex' / 'auth.json'
AGENTS_DIR = OPENCLAW_HOME / 'agents'
SUBAGENT_RUNS = OPENCLAW_HOME / 'subagents' / 'runs.json'
EXP_DIR = ROOT / 'reports' / 'expenditure'
HOURLY_CACHE_DIR = EXP_DIR / 'hourly'
DEFAULT_WEEKLY_SHARE = 0.30
PARIS_TZ = dt.timezone(dt.timedelta(hours=1))
TITLE_PREFIX = '# Expenditure Ledger - '
SUMMARY_START = '<!-- codex-usage-summary:start -->'
SUMMARY_END = '<!-- codex-usage-summary:end -->'
DEFAULT_USAGE_URL = os.environ.get('OPENAI_USAGE_URL', 'https://api.openai.com/v1/organization/usage/completions')
DEFAULT_COST_URL = os.environ.get('OPENAI_COST_URL', 'https://api.openai.com/v1/organization/costs')


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def iso_utc(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_ts(value: Any) -> dt.datetime | None:
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, tz=dt.timezone.utc)
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except Exception:
            return None
    return None


def date_bounds(target: str) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime.strptime(target, '%Y-%m-%d').replace(tzinfo=dt.timezone.utc)
    return start, start + dt.timedelta(days=1)


def week_bounds(end: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    return end - dt.timedelta(days=7), end


def codex_auth_token() -> str | None:
    env_token = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_ACCESS_TOKEN')
    if env_token:
        return env_token.strip()
    payload = read_json(CODEX_AUTH, {}) or {}
    if payload.get('OPENAI_API_KEY'):
        return str(payload['OPENAI_API_KEY']).strip()
    tokens = payload.get('tokens') or {}
    for key in ('access_token', 'id_token'):
        if tokens.get(key):
            return str(tokens[key]).strip()
    return None


def metrics_request(url: str, params: dict[str, Any]) -> dict[str, Any]:
    token = codex_auth_token()
    if not token:
        return {'ok': False, 'error': 'missing OpenAI auth token'}
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
    req = urllib.request.Request(
        f'{url}?{query}',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode('utf-8')
        return {'ok': True, 'data': json.loads(body), 'fetchedAt': iso_utc(dt.datetime.now(dt.timezone.utc))}
    except Exception as exc:
        return {'ok': False, 'error': str(exc), 'fetchedAt': iso_utc(dt.datetime.now(dt.timezone.utc))}


def load_session_index() -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for agent_dir in AGENTS_DIR.iterdir() if AGENTS_DIR.exists() else []:
        sessions_file = agent_dir / 'sessions' / 'sessions.json'
        payload = read_json(sessions_file, {}) or {}
        if not isinstance(payload, dict):
            continue
        for key, meta in payload.items():
            if not isinstance(meta, dict):
                continue
            session_id = meta.get('sessionId')
            if not session_id:
                continue
            by_id[str(session_id)] = {
                'sessionKey': key,
                'agent': agent_dir.name,
                'label': meta.get('label') or '',
                'updatedAt': meta.get('updatedAt') or meta.get('lastUsageAt'),
                'model': meta.get('modelName') or meta.get('model') or '',
            }
    return by_id


def is_codex_message(message: dict[str, Any]) -> bool:
    provider = str(message.get('provider') or '').lower()
    model = str(message.get('model') or '').lower()
    return 'codex' in provider or provider.startswith('openai') or model.startswith('gpt-5')


def parse_usage(start: dt.datetime, end: dt.datetime) -> dict[str, Any]:
    session_index = load_session_index()
    sessions: dict[str, dict[str, Any]] = {}
    hourly: dict[str, dict[str, float]] = defaultdict(lambda: {'input': 0, 'output': 0, 'cached': 0, 'tokens': 0, 'cost': 0.0, 'turns': 0})
    totals = {'input': 0, 'output': 0, 'cached': 0, 'tokens': 0, 'cost': 0.0, 'turns': 0}

    for agent_dir in AGENTS_DIR.iterdir() if AGENTS_DIR.exists() else []:
        sess_dir = agent_dir / 'sessions'
        if not sess_dir.exists():
            continue
        for transcript in sess_dir.glob('*.jsonl'):
            session_id = transcript.stem
            meta = session_index.get(session_id, {})
            session_key = str(meta.get('sessionKey') or session_id)
            rec = sessions.setdefault(
                session_key,
                {
                    'sessionKey': session_key,
                    'sessionId': session_id,
                    'agent': meta.get('agent') or agent_dir.name,
                    'label': meta.get('label') or '',
                    'provider': set(),
                    'model': set(),
                    'input': 0,
                    'output': 0,
                    'cached': 0,
                    'tokens': 0,
                    'cost': 0.0,
                    'turns': 0,
                    'firstTs': None,
                    'lastTs': None,
                },
            )
            try:
                handle = transcript.open()
            except Exception:
                continue
            with handle:
                for line in handle:
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    if entry.get('type') != 'message':
                        continue
                    message = entry.get('message') or {}
                    if message.get('role') != 'assistant' or not is_codex_message(message):
                        continue
                    ts = parse_ts(message.get('timestamp') or entry.get('timestamp'))
                    if not ts or not (start <= ts < end):
                        continue
                    usage = message.get('usage') or {}
                    cost = usage.get('cost') or {}
                    input_tokens = int(usage.get('input') or 0)
                    output_tokens = int(usage.get('output') or 0)
                    cached_tokens = int(usage.get('cacheRead') or 0) + int(usage.get('cacheWrite') or 0)
                    total_tokens = input_tokens + output_tokens + cached_tokens
                    total_cost = float(cost.get('total') or 0.0)
                    hour_key = ts.strftime('%Y-%m-%d %H:00 UTC')
                    hourly[hour_key]['input'] += input_tokens
                    hourly[hour_key]['output'] += output_tokens
                    hourly[hour_key]['cached'] += cached_tokens
                    hourly[hour_key]['tokens'] += total_tokens
                    hourly[hour_key]['cost'] += total_cost
                    hourly[hour_key]['turns'] += 1
                    totals['input'] += input_tokens
                    totals['output'] += output_tokens
                    totals['cached'] += cached_tokens
                    totals['tokens'] += total_tokens
                    totals['cost'] += total_cost
                    totals['turns'] += 1
                    rec['input'] += input_tokens
                    rec['output'] += output_tokens
                    rec['cached'] += cached_tokens
                    rec['tokens'] += total_tokens
                    rec['cost'] += total_cost
                    rec['turns'] += 1
                    if message.get('provider'):
                        rec['provider'].add(str(message['provider']))
                    if message.get('model'):
                        rec['model'].add(str(message['model']))
                    rec['firstTs'] = ts if rec['firstTs'] is None or ts < rec['firstTs'] else rec['firstTs']
                    rec['lastTs'] = ts if rec['lastTs'] is None or ts > rec['lastTs'] else rec['lastTs']

    normalized_sessions = []
    for rec in sessions.values():
        if rec['turns'] <= 0:
            continue
        rec['provider'] = ', '.join(sorted(rec['provider']))
        rec['model'] = ', '.join(sorted(rec['model']))
        normalized_sessions.append(rec)

    normalized_sessions.sort(key=lambda item: item['cost'], reverse=True)
    normalized_hours = [
        {'hour': hour, **vals} for hour, vals in sorted(hourly.items(), key=lambda pair: pair[0])
    ]
    return {'totals': totals, 'sessions': normalized_sessions, 'hours': normalized_hours}


def active_subagents() -> dict[str, Any]:
    payload = read_json(SUBAGENT_RUNS, {}) or {}
    runs = payload.get('runs') or {}
    active = []
    finished = []
    for run in runs.values() if isinstance(runs, dict) else []:
        if not isinstance(run, dict):
            continue
        record = {
            'runId': run.get('runId'),
            'label': run.get('label') or '',
            'childSessionKey': run.get('childSessionKey') or '',
            'model': run.get('model') or '',
            'createdAt': run.get('createdAt'),
            'startedAt': run.get('startedAt'),
            'endedAt': run.get('endedAt'),
            'status': ((run.get('outcome') or {}).get('status') if isinstance(run.get('outcome'), dict) else None) or ('running' if not run.get('endedAt') else 'ended'),
        }
        (finished if run.get('endedAt') else active).append(record)
    active.sort(key=lambda item: item.get('startedAt') or 0, reverse=True)
    finished.sort(key=lambda item: item.get('endedAt') or 0, reverse=True)
    return {'active': active, 'recentFinished': finished[:5], 'activeCount': len(active), 'totalTracked': len(active) + len(finished)}


def stale_memory_candidates() -> list[dict[str, Any]]:
    mem_dir = ROOT / 'memory'
    candidates = []
    if not mem_dir.exists():
        return candidates
    for path in sorted(mem_dir.glob('*.md')):
        try:
            line_count = sum(1 for _ in path.open())
        except Exception:
            continue
        reason = None
        if line_count > 200:
            reason = 'file exceeds 200 lines; likely transcript/status dump'
        elif path.stem.count('-') != 2:
            reason = 'non-canonical daily-memory filename; check whether it belongs in reports/openclaw/'
        if reason:
            candidates.append({'path': str(path.relative_to(ROOT)), 'lines': line_count, 'reason': reason})
    return candidates


def memory_status() -> dict[str, Any]:
    memory_file = ROOT / 'MEMORY.md'
    lines = sum(1 for _ in memory_file.open()) if memory_file.exists() else 0
    return {'path': str(memory_file.relative_to(ROOT)), 'lines': lines, 'compactEnough': lines <= 60}


def hourly_cache_path(now: dt.datetime) -> Path:
    HOURLY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return HOURLY_CACHE_DIR / f"hourly-{now.strftime('%Y-%m-%d-%H')}.json"


def fetch_metrics_snapshot(now: dt.datetime, force: bool = False) -> dict[str, Any]:
    cache_path = hourly_cache_path(now)
    if cache_path.exists() and not force:
        cached = read_json(cache_path, {}) or {}
        cached['cachePath'] = str(cache_path.relative_to(ROOT))
        return cached

    end = now.replace(minute=0, second=0, microsecond=0)
    start = end - dt.timedelta(hours=24)
    params = {
        'start_time': int(start.timestamp()),
        'end_time': int(end.timestamp()),
        'bucket_width': '1h',
        'group_by': ['model'],
    }
    usage = metrics_request(DEFAULT_USAGE_URL, params)
    costs = metrics_request(DEFAULT_COST_URL, params)
    payload = {
        'fetchedAt': iso_utc(now),
        'start': iso_utc(start),
        'end': iso_utc(end),
        'usage': usage,
        'costs': costs,
    }
    cache_path.write_text(json.dumps(payload, indent=2) + '\n')
    payload['cachePath'] = str(cache_path.relative_to(ROOT))
    return payload


def format_int(value: int) -> str:
    return f'{value:,}'


def format_money(value: float) -> str:
    return f'${value:,.4f}'


def projection(week_cost: float, today_cost: float, now: dt.datetime, weekly_share: float = DEFAULT_WEEKLY_SHARE) -> dict[str, Any]:
    local_now = now.astimezone(PARIS_TZ)
    end_local = dt.datetime(2026, 3, 18, 23, 59, 59, tzinfo=PARIS_TZ)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_hours = max((local_now - start_local).total_seconds() / 3600.0, 1.0)
    remaining_hours = max((end_local - local_now).total_seconds() / 3600.0, 0.0)
    observed_daily_average = week_cost / 7.0 if week_cost > 0 else 0.0
    projected_extra_smoothed = observed_daily_average * (remaining_hours / 24.0)
    projected_extra_spike = today_cost * (remaining_hours / elapsed_hours)
    implied_weekly_budget = (week_cost / weekly_share) if weekly_share > 0 and week_cost > 0 else None
    projected_share_smoothed = ((week_cost + projected_extra_smoothed) / implied_weekly_budget) if implied_weekly_budget else None
    projected_share_spike = ((week_cost + projected_extra_spike) / implied_weekly_budget) if implied_weekly_budget else None
    return {
        'currentWeekCost': week_cost,
        'currentWeekShare': weekly_share,
        'impliedWeeklyBudget': implied_weekly_budget,
        'remainingHoursTo18th': remaining_hours,
        'observedDailyAverage': observed_daily_average,
        'projectedAdditionalCostTo18thSmoothed': projected_extra_smoothed,
        'projectedWeekCloseCostSmoothed': week_cost + projected_extra_smoothed,
        'projectedWeekCloseShareSmoothed': projected_share_smoothed,
        'projectedAdditionalCostTo18thSpike': projected_extra_spike,
        'projectedWeekCloseCostSpike': week_cost + projected_extra_spike,
        'projectedWeekCloseShareSpike': projected_share_spike,
    }


def summary_markdown(target_date: str, today_usage: dict[str, Any], week_usage: dict[str, Any], metrics: dict[str, Any], runs: dict[str, Any], mem: dict[str, Any], stale: list[dict[str, Any]], proj: dict[str, Any], generated_at: dt.datetime) -> str:
    totals = today_usage['totals']
    week_totals = week_usage['totals']
    lines = [
        SUMMARY_START,
        f'## Codex Usage Summary ({target_date})',
        '',
        f'- Generated: {iso_utc(generated_at)}',
        f"- Daily Codex turns: {totals['turns']}",
        f"- Daily Codex input tokens: {format_int(totals['input'])}",
        f"- Daily Codex output tokens: {format_int(totals['output'])}",
        f"- Daily Codex cached tokens: {format_int(totals['cached'])}",
        f"- Daily Codex cost: {format_money(totals['cost'])}",
        f"- 7-day observed Codex cost: {format_money(week_totals['cost'])}",
        f"- Active subagents right now: {runs['activeCount']}",
        f"- MEMORY.md line count: {mem['lines']} ({'within target' if mem['compactEnough'] else 'over 60; compact on next sweep'})",
        f"- OpenAI metrics cache: {metrics.get('cachePath', 'not written')}",
        f"- OpenAI metrics status: usage={'ok' if (metrics.get('usage') or {}).get('ok') else 'fallback'}, costs={'ok' if (metrics.get('costs') or {}).get('ok') else 'fallback'}",
        '',
        '### Token Breakdown by Session',
        '',
        '| Session | Agent | Turns | Input | Output | Cached | Cost |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for rec in today_usage['sessions'][:10]:
        label = rec['label'] or rec['sessionKey'].split(':')[-1]
        lines.append(
            f"| {label} | {rec['agent']} | {rec['turns']} | {format_int(rec['input'])} | {format_int(rec['output'])} | {format_int(rec['cached'])} | {format_money(rec['cost'])} |"
        )
    lines += [
        '',
        '### Hourly Codex Cost (local observed)',
        '',
        '| Hour | Turns | Tokens | Cost |',
        '|---|---:|---:|---:|',
    ]
    for hour in today_usage['hours']:
        lines.append(f"| {hour['hour']} | {hour['turns']} | {format_int(int(hour['tokens']))} | {format_money(hour['cost'])} |")
    lines += [
        '',
        '### Projection to 18th',
        '',
        f"- Current weekly spend position: ~{proj['currentWeekShare'] * 100:.0f}% of weekly budget (user-provided planning baseline).",
        f"- Remaining time to 18th close (Europe/Paris): {proj['remainingHoursTo18th']:.1f}h.",
        f"- Trailing 7-day observed daily average: {format_money(proj['observedDailyAverage'])}/day.",
        f"- Smoothed projected additional cost to 18th: {format_money(proj['projectedAdditionalCostTo18thSmoothed'])}.",
        f"- Smoothed projected week-close cost: {format_money(proj['projectedWeekCloseCostSmoothed'])}.",
        f"- Spike-risk projected additional cost if the current implementation burst continued unchanged: {format_money(proj['projectedAdditionalCostTo18thSpike'])}.",
    ]
    if proj['impliedWeeklyBudget']:
        lines.append(f"- Implied weekly budget from the 30% baseline: {format_money(proj['impliedWeeklyBudget'])}.")
    if proj['projectedWeekCloseShareSmoothed'] is not None:
        lines.append(f"- Smoothed projected week-close share: ~{proj['projectedWeekCloseShareSmoothed'] * 100:.1f}%.")
    if proj['projectedWeekCloseShareSpike'] is not None:
        lines.append(f"- Spike-risk week-close share if current burst persisted: ~{proj['projectedWeekCloseShareSpike'] * 100:.1f}%.")
    lines += [
        '',
        '### Active Subagent Snapshot',
        '',
        '| Label | Session | Model | Status |',
        '|---|---|---|---|',
    ]
    for run in runs['active'][:10]:
        lines.append(f"| {run['label'] or '-'} | {run['childSessionKey'] or '-'} | {run['model'] or '-'} | {run['status']} |")
    if not runs['active']:
        lines.append('| - | - | - | no active subagents |')
    lines += ['', '### Memory Sweep Flags', '']
    if stale:
        lines += ['| Path | Lines | Reason |', '|---|---:|---|']
        for item in stale:
            lines.append(f"| {item['path']} | {item['lines']} | {item['reason']} |")
    else:
        lines.append('- No stale transcript candidates detected in `memory/` during this sweep.')
    lines += ['', SUMMARY_END, '']
    return '\n'.join(lines)


def ensure_ledger_file(target_date: str) -> Path:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    path = EXP_DIR / f'ledger-{target_date}.md'
    if not path.exists():
        path.write_text(f'{TITLE_PREFIX}{target_date}\n\n')
    return path


def merge_summary(path: Path, summary: str, target_date: str) -> None:
    text = path.read_text() if path.exists() else f'{TITLE_PREFIX}{target_date}\n\n'
    if not text.startswith(TITLE_PREFIX):
        text = f'{TITLE_PREFIX}{target_date}\n\n' + text
    start = text.find(SUMMARY_START)
    end = text.find(SUMMARY_END)
    if start != -1 and end != -1 and end > start:
        end += len(SUMMARY_END)
        new_text = text[:start].rstrip() + '\n\n' + summary.strip() + '\n\n' + text[end:].lstrip('\n')
    else:
        first_break = text.find('\n')
        if first_break == -1:
            new_text = text.rstrip() + '\n\n' + summary.strip() + '\n'
        else:
            new_text = text[: first_break + 1] + '\n' + summary.strip() + '\n\n' + text[first_break + 1 :].lstrip('\n')
    path.write_text(new_text)


def build_snapshot(target_date: str, force_metrics: bool = False) -> dict[str, Any]:
    generated_at = dt.datetime.now(dt.timezone.utc)
    day_start, day_end = date_bounds(target_date)
    week_start, week_end = week_bounds(generated_at)
    today_usage = parse_usage(day_start, day_end)
    week_usage = parse_usage(week_start, week_end)
    metrics = fetch_metrics_snapshot(generated_at, force=force_metrics)
    runs = active_subagents()
    mem = memory_status()
    stale = stale_memory_candidates()
    proj = projection(week_usage['totals']['cost'], today_usage['totals']['cost'], generated_at)
    return {
        'generatedAt': iso_utc(generated_at),
        'date': target_date,
        'today': today_usage,
        'week': week_usage,
        'metrics': metrics,
        'runs': runs,
        'memory': mem,
        'staleCandidates': stale,
        'projectionTo18th': proj,
    }


def cmd_status(args: argparse.Namespace) -> int:
    snap = build_snapshot(args.date, force_metrics=args.force_metrics)
    print(f"Codex status for {snap['date']}")
    print(f"  Daily turns: {snap['today']['totals']['turns']}")
    print(f"  Daily input/output/cached: {format_int(snap['today']['totals']['input'])} / {format_int(snap['today']['totals']['output'])} / {format_int(snap['today']['totals']['cached'])}")
    print(f"  Daily cost: {format_money(snap['today']['totals']['cost'])}")
    print(f"  Active subagents: {snap['runs']['activeCount']}")
    print(f"  MEMORY.md lines: {snap['memory']['lines']}")
    print(f"  Stale memory candidates: {len(snap['staleCandidates'])}")
    if snap['runs']['active']:
        print('\nActive runs:')
        for run in snap['runs']['active'][:10]:
            print(f"  - {run['label'] or '-'} :: {run['childSessionKey']} :: {run['model'] or '-'}")
    print('\nTop Codex sessions:')
    for rec in snap['today']['sessions'][:10]:
        label = rec['label'] or rec['sessionKey'].split(':')[-1]
        print(f"  - {label} [{rec['agent']}] turns={rec['turns']} tokens={format_int(rec['tokens'])} cost={format_money(rec['cost'])}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    snap = build_snapshot(args.date, force_metrics=args.force_metrics)
    summary = summary_markdown(
        args.date,
        snap['today'],
        snap['week'],
        snap['metrics'],
        snap['runs'],
        snap['memory'],
        snap['staleCandidates'],
        snap['projectionTo18th'],
        dt.datetime.now(dt.timezone.utc),
    )
    if args.write:
        ledger = ensure_ledger_file(args.date)
        merge_summary(ledger, summary, args.date)
        print(str(ledger.relative_to(ROOT)))
    else:
        print(summary)
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    snap = build_snapshot(args.date, force_metrics=args.force_metrics)
    print(json.dumps(snap, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    today = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    parser = argparse.ArgumentParser(description='Codex-only token tracker and expenditure reporter for WatsonOW.')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'report', 'snapshot'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--date', default=today, help='UTC date in YYYY-MM-DD format')
        cmd.add_argument('--force-metrics', action='store_true', help='Bypass hourly cache and retry OpenAI metrics fetch')
        if name == 'report':
            cmd.add_argument('--write', action='store_true', help='Update reports/expenditure/ledger-YYYY-MM-DD.md in place')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == 'status':
        return cmd_status(args)
    if args.command == 'report':
        return cmd_report(args)
    if args.command == 'snapshot':
        return cmd_snapshot(args)
    parser.error('unknown command')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
