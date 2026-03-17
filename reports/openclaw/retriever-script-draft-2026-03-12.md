# Retriever Worker Draft — 2026-03-12

## Intent
Create `scripts/om/retriever-worker.sh` as a deterministic-first OM retrieval helper that:
- loads memory in the fixed Recipe 01 order before any semantic work
- excludes `reports/openclaw/` validation/test dumps from retrieval sources
- uses local OpenClaw embeddings when they are actually available
- remains useful without embeddings via deterministic + lexical fallback
- exposes a `retrieve` CLI suitable for direct calls and `observer-worker.sh` post-capture hooks

## Recipe 04 Alignment Check

Required by `reports/recipes/04-openclaw-runtime-alignment.md`:
- deterministic file loading first ✅
- semantic/index retrieval second ✅
- retrieval coverage includes `MEMORY.md`, `OBSERVATIONS.md`, `REFLECTIONS.md`, `bank/`, and `memory/` ✅
- do **not** treat `reports/openclaw/` dumps as primary memory lanes ✅
- report semantic/tool blockers explicitly instead of silently pretending success ✅

Design choice:
- deterministic preload order is exactly: `IDENTITY.md`, `USER.md`, `AGENTS.md`, `HEARTBEAT.md`, optional task file, `MEMORY.md`, `OBSERVATIONS.md`, `REFLECTIONS.md`, then sorted `bank/**/*.md`
- daily memory under `memory/*.md` participates in expansion/fallback coverage instead of bloating the deterministic preload

## Proposed CLI

```bash
scripts/om/retriever-worker.sh retrieve \
  --query "auto-commit override" \
  --task-file reports/recipes/04-openclaw-runtime-alignment.md \
  --json
```

Optional observer hook form:

```bash
OM_POST_CAPTURE_HOOK='scripts/om/retriever-worker.sh retrieve --query "$OM_CAPTURE_QUERY" --out reports/openclaw/post-capture-retrieval.md' \
  scripts/om/observer-worker.sh capture ...
```

## Final Script Contents

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  retriever-worker.sh retrieve --query TEXT [options]

Options:
  --query TEXT              Query to retrieve against.
  --query-file PATH         Read query text from a file.
  --task-file PATH          Optional task/contract file inserted after HEARTBEAT.md.
  --semantic-k N            Max semantic hits to include. Default: 5
  --max-chars N             Max excerpt chars per deterministic item. Default: 2200
  --daily-limit N           Max recent daily memory files for lexical fallback. Default: 3
  --no-daily                Disable daily-memory fallback coverage.
  --no-semantic             Skip OpenClaw semantic expansion.
  --require-semantic        Exit non-zero if local semantic expansion is unavailable.
  --json                    Emit JSON instead of markdown/text.
  --out PATH                Write output to a file inside the repo instead of stdout.
  -h, --help                Show this help.

Environment:
  OM_RETRIEVER_SEMANTIC_K      Default semantic hit cap (5)
  OM_RETRIEVER_MAX_CHARS       Default excerpt cap (2200)
  OM_RETRIEVER_DAILY_LIMIT     Default recent-daily fallback window (3)

Notes:
  - Deterministic preload order follows Recipe 01 before any semantic expansion.
  - Semantic expansion is attempted only when OpenClaw reports a local embedding provider.
  - reports/openclaw/ dumps are explicitly excluded from retrieval sources.
EOF
}

is_int() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

retrieve_command() {
  local query=""
  local query_file=""
  local task_file=""
  local semantic_k="${OM_RETRIEVER_SEMANTIC_K:-5}"
  local max_chars="${OM_RETRIEVER_MAX_CHARS:-2200}"
  local daily_limit="${OM_RETRIEVER_DAILY_LIMIT:-3}"
  local include_daily="true"
  local no_semantic="false"
  local require_semantic="false"
  local output_format="text"
  local out_file=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --query)
        query="$2"
        shift 2
        ;;
      --query-file)
        query_file="$2"
        shift 2
        ;;
      --task-file)
        task_file="$2"
        shift 2
        ;;
      --semantic-k)
        semantic_k="$2"
        shift 2
        ;;
      --max-chars)
        max_chars="$2"
        shift 2
        ;;
      --daily-limit)
        daily_limit="$2"
        shift 2
        ;;
      --no-daily)
        include_daily="false"
        shift
        ;;
      --no-semantic)
        no_semantic="true"
        shift
        ;;
      --require-semantic)
        require_semantic="true"
        shift
        ;;
      --json)
        output_format="json"
        shift
        ;;
      --out)
        out_file="$2"
        shift 2
        ;;
      -h|--help|help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option for retrieve: $1" >&2
        exit 1
        ;;
    esac
  done

  if [[ -n "$query_file" ]]; then
    if [[ ! -f "$query_file" ]]; then
      echo "Query file not found: $query_file" >&2
      exit 1
    fi
    query="$(cat "$query_file")"
  fi

  if [[ -z "$query" ]]; then
    echo "retrieve requires --query or --query-file." >&2
    exit 1
  fi

  if ! is_int "$semantic_k" || ! is_int "$max_chars" || ! is_int "$daily_limit"; then
    echo "--semantic-k, --max-chars, and --daily-limit must be non-negative integers." >&2
    exit 1
  fi

  python3 - "$REPO_DIR" "$query" "$task_file" "$output_format" "$max_chars" "$semantic_k" "$include_daily" "$daily_limit" "$no_semantic" "$require_semantic" "$out_file" <<'PY'
import json
import os
import re
import subprocess
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1]).resolve()
query = sys.argv[2]
task_file_arg = sys.argv[3]
output_format = sys.argv[4]
max_chars = int(sys.argv[5])
semantic_k = int(sys.argv[6])
include_daily = sys.argv[7] == "true"
daily_limit = int(sys.argv[8])
no_semantic = sys.argv[9] == "true"
require_semantic = sys.argv[10] == "true"
out_file_arg = sys.argv[11]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "have",
    "will", "about", "after", "before", "then", "only", "when", "what", "where",
    "which", "while", "were", "been", "being", "them", "they", "their", "there",
    "here", "than", "under", "over", "uses", "using", "into", "onto", "also",
    "just", "does", "did", "done", "path", "file", "files", "lane", "lanes",
}


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def ensure_inside_repo(path_value: Path, label: str) -> Path:
    path_value = path_value.resolve()
    if path_value == repo_dir or repo_dir in path_value.parents:
        return path_value
    fail(f"{label} must stay inside the repo: {path_value}")


def resolve_optional_repo_path(raw: str, label: str) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_dir / candidate
    candidate = ensure_inside_repo(candidate, label)
    if not candidate.exists():
        fail(f"{label} not found: {candidate}")
    return candidate


def normalize_rel(path_value: Path | str) -> str:
    try:
        return Path(path_value).resolve().relative_to(repo_dir).as_posix()
    except Exception:
        return Path(path_value).as_posix()


def read_text(path_value: Path) -> str:
    return path_value.read_text(encoding="utf-8", errors="replace")


def query_terms(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9._:-]+", text.lower())
    terms = []
    for word in words:
        if len(word) < 3 or word in STOPWORDS:
            continue
        if word not in terms:
            terms.append(word)
    if not terms and text.strip():
        return [text.strip().lower()]
    return terms


def score_line(line: str, terms: list[str], phrase: str) -> int:
    lowered = line.lower()
    score = sum(lowered.count(term) for term in terms)
    if phrase and phrase in lowered:
        score += 3
    return score


def excerpt_from_text(text: str, terms: list[str], max_len: int) -> tuple[str, int, int, str]:
    lines = text.splitlines()
    if not lines:
        return "", 1, 1, "empty"

    if len(text) <= max_len:
        return text.rstrip(), 1, len(lines), "full"

    phrase = query.lower().strip()
    best_index = 0
    best_score = -1
    for idx, line in enumerate(lines):
        current = score_line(line, terms, phrase)
        if current > best_score:
            best_score = current
            best_index = idx

    if best_score > 0:
        start = max(0, best_index - 12)
        end = min(len(lines), best_index + 13)
        snippet_lines = lines[start:end]
        while len("\n".join(snippet_lines)) > max_len and end - start > 4:
            if best_index - start > end - best_index - 1:
                start += 1
            else:
                end -= 1
            snippet_lines = lines[start:end]
        excerpt = "\n".join(snippet_lines).rstrip()
        if end < len(lines):
            excerpt += "\n...[truncated]"
        return excerpt, start + 1, end, "query-window"

    clipped = text[:max_len]
    if "\n" in clipped:
        clipped = clipped.rsplit("\n", 1)[0]
    clipped = clipped.rstrip() + "\n...[truncated]"
    end_line = clipped.count("\n") + 1
    return clipped, 1, end_line, "head"


def build_deterministic_paths(task_file: Path | None) -> list[Path]:
    ordered: list[Path] = []
    fixed = [
        repo_dir / "IDENTITY.md",
        repo_dir / "USER.md",
        repo_dir / "AGENTS.md",
        repo_dir / "HEARTBEAT.md",
    ]
    for item in fixed:
        if item.exists():
            ordered.append(item)
    if task_file is not None:
        ordered.append(task_file)
    for name in ["MEMORY.md", "OBSERVATIONS.md", "REFLECTIONS.md"]:
        path_value = repo_dir / name
        if path_value.exists():
            ordered.append(path_value)
    bank_dir = repo_dir / "bank"
    if bank_dir.exists():
        ordered.extend(sorted(p for p in bank_dir.rglob("*.md") if p.is_file()))
    return ordered


def build_daily_pool(limit: int) -> list[Path]:
    memory_dir = repo_dir / "memory"
    if not memory_dir.exists():
        return []
    daily = []
    for path_value in sorted(memory_dir.glob("*.md"), reverse=True):
        if path_value.name == "observer-state.env":
            continue
        daily.append(path_value)
    return daily[:limit]


def deterministic_payload(paths: list[Path], terms: list[str]) -> list[dict]:
    payload = []
    for path_value in paths:
        text = read_text(path_value)
        excerpt, start_line, end_line, mode = excerpt_from_text(text, terms, max_chars)
        payload.append(
            {
                "path": normalize_rel(path_value),
                "start_line": start_line,
                "end_line": end_line,
                "mode": mode,
                "excerpt": excerpt,
            }
        )
    return payload


def allowed_memory_path(path_text: str) -> bool:
    normalized = path_text.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith(str(repo_dir).replace("\\", "/")):
        normalized = normalize_rel(Path(normalized))
    if normalized.startswith("reports/openclaw/") or "/reports/openclaw/" in normalized:
        return False
    return (
        normalized == "MEMORY.md"
        or normalized == "OBSERVATIONS.md"
        or normalized == "REFLECTIONS.md"
        or normalized.startswith("bank/")
        or normalized.startswith("memory/")
    )


def extract_json(stdout_text: str):
    stripped = stdout_text.strip()
    if not stripped:
        raise ValueError("empty JSON output")
    for marker in ("[", "{"):
        idx = stripped.find(marker)
        if idx != -1:
            candidate = stripped[idx:]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
    return json.loads(stripped)


def openclaw_semantic(query_text: str) -> dict:
    status_cmd = ["openclaw", "memory", "status", "--json"]
    try:
        status_run = subprocess.run(status_cmd, capture_output=True, text=True, timeout=25, check=False)
    except FileNotFoundError:
        return {
            "mode": "disabled",
            "blocked": {
                "tool": "openclaw",
                "failure": "command not found",
                "impact": "local semantic expansion unavailable",
                "next_action": "install/configure OpenClaw or rerun with --no-semantic",
            },
            "results": [],
        }

    if status_run.returncode != 0:
        return {
            "mode": "disabled",
            "blocked": {
                "tool": "openclaw memory status --json",
                "failure": (status_run.stderr or status_run.stdout).strip() or f"exit {status_run.returncode}",
                "impact": "could not verify local memory embeddings",
                "next_action": "fix OpenClaw memory status or rerun with --no-semantic",
            },
            "results": [],
        }

    try:
        status_json = extract_json(status_run.stdout)
    except Exception as exc:
        return {
            "mode": "disabled",
            "blocked": {
                "tool": "openclaw memory status --json",
                "failure": f"unparseable JSON: {exc}",
                "impact": "could not verify local memory embeddings",
                "next_action": "inspect OpenClaw memory status output",
            },
            "results": [],
        }

    if not isinstance(status_json, list):
        status_json = [status_json]

    active_status = None
    for entry in status_json:
        status = entry.get("status", {}) if isinstance(entry, dict) else {}
        provider = status.get("provider") or entry.get("provider")
        requested = status.get("requestedProvider") or entry.get("requestedProvider")
        if provider == "local" or requested == "local":
            active_status = status
            break

    if active_status is None:
        return {
            "mode": "disabled",
            "blocked": {
                "tool": "openclaw memory status --json",
                "failure": "local embedding provider not active",
                "impact": "semantic expansion unavailable; deterministic retrieval still works",
                "next_action": "configure a local memorySearch provider or rerun with --no-semantic",
            },
            "results": [],
        }

    search_cmd = ["openclaw", "memory", "search", "--json", "--query", query_text]
    search_run = subprocess.run(search_cmd, capture_output=True, text=True, timeout=40, check=False)
    if search_run.returncode != 0:
        return {
            "mode": "disabled",
            "provider": active_status.get("provider") or active_status.get("requestedProvider") or "local",
            "model": active_status.get("model"),
            "blocked": {
                "tool": "openclaw memory search --json",
                "failure": (search_run.stderr or search_run.stdout).strip() or f"exit {search_run.returncode}",
                "impact": "semantic expansion unavailable; deterministic retrieval still works",
                "next_action": "repair memory indexing/provider or rerun with --no-semantic",
            },
            "results": [],
        }

    try:
        result_json = extract_json(search_run.stdout)
    except Exception as exc:
        return {
            "mode": "disabled",
            "provider": active_status.get("provider") or active_status.get("requestedProvider") or "local",
            "model": active_status.get("model"),
            "blocked": {
                "tool": "openclaw memory search --json",
                "failure": f"unparseable JSON: {exc}",
                "impact": "semantic expansion unavailable; deterministic retrieval still works",
                "next_action": "inspect OpenClaw memory search output",
            },
            "results": [],
        }

    if isinstance(result_json, dict):
        results = result_json.get("results", [])
    else:
        results = result_json

    filtered = []
    seen = set()
    for hit in results:
        if not isinstance(hit, dict):
            continue
        raw_path = hit.get("path", "")
        if not raw_path:
            continue
        normalized = normalize_rel(repo_dir / raw_path) if not os.path.isabs(raw_path) else normalize_rel(Path(raw_path))
        if not allowed_memory_path(normalized):
            continue
        key = (normalized, hit.get("startLine"), hit.get("endLine"), hit.get("snippet"))
        if key in seen:
            continue
        seen.add(key)
        filtered.append(
            {
                "path": normalized,
                "score": hit.get("score"),
                "start_line": hit.get("startLine"),
                "end_line": hit.get("endLine"),
                "snippet": (hit.get("snippet") or "").rstrip(),
                "source": hit.get("source"),
            }
        )
        if len(filtered) >= semantic_k:
            break

    return {
        "mode": "openclaw-local",
        "provider": active_status.get("provider") or active_status.get("requestedProvider") or "local",
        "model": active_status.get("model"),
        "results": filtered,
    }


def lexical_fallback(paths: list[Path], terms: list[str]) -> dict:
    if not paths:
        return {"mode": "none", "results": []}

    phrase = query.lower().strip()
    scored = []
    for path_value in paths:
        text = read_text(path_value)
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if phrase and phrase in lowered:
            score += 3
        if score <= 0:
            continue
        excerpt, start_line, end_line, mode = excerpt_from_text(text, terms, max_chars)
        scored.append(
            {
                "path": normalize_rel(path_value),
                "score": score,
                "start_line": start_line,
                "end_line": end_line,
                "snippet": excerpt,
                "source": "lexical-fallback",
                "mode": mode,
            }
        )

    scored.sort(key=lambda item: (-item["score"], item["path"]))
    return {"mode": "lexical-fallback", "results": scored[:semantic_k]}


def render_text(payload: dict) -> str:
    lines = []
    lines.append("# OM Retrieval Packet")
    lines.append("")
    lines.append(f"- query: {payload['query']}")
    lines.append(f"- deterministic_items: {len(payload['deterministic'])}")
    lines.append(f"- semantic_mode: {payload['semantic'].get('mode', 'none')}")
    lines.append(f"- semantic_results: {len(payload['semantic'].get('results', []))}")
    if payload.get("notes"):
        lines.append("- notes:")
        for note in payload["notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Deterministic Order")
    for index, item in enumerate(payload["deterministic"], start=1):
        lines.append(f"{index}. `{item['path']}`")
    lines.append("")
    lines.append("## Deterministic Hydration")
    for item in payload["deterministic"]:
        lines.append("")
        lines.append(f"### `{item['path']}`")
        lines.append(f"- lines: {item['start_line']}-{item['end_line']}")
        lines.append(f"- mode: {item['mode']}")
        lines.append("```md")
        lines.append(item["excerpt"])
        lines.append("```")
    lines.append("")
    lines.append("## Expansion")
    semantic = payload["semantic"]
    if semantic.get("blocked"):
        blocked = semantic["blocked"]
        lines.append("")
        lines.append("BLOCKED")
        lines.append(f"- Tool: {blocked['tool']}")
        lines.append(f"- Failure: {blocked['failure']}")
        lines.append(f"- Impact: {blocked['impact']}")
        lines.append(f"- Next action: {blocked['next_action']}")
    if semantic.get("results"):
        lines.append("")
        for index, hit in enumerate(semantic["results"], start=1):
            lines.append(f"### Hit {index}: `{hit['path']}`")
            if hit.get("score") is not None:
                lines.append(f"- score: {hit['score']}")
            if hit.get("start_line") is not None and hit.get("end_line") is not None:
                lines.append(f"- lines: {hit['start_line']}-{hit['end_line']}")
            if hit.get("source"):
                lines.append(f"- source: {hit['source']}")
            lines.append("```md")
            lines.append(hit.get("snippet", ""))
            lines.append("```")
            lines.append("")
    elif not semantic.get("blocked"):
        lines.append("")
        lines.append("No expansion hits.")
    return "\n".join(lines).rstrip() + "\n"


task_file = resolve_optional_repo_path(task_file_arg, "Task file")
out_file = resolve_optional_repo_path(out_file_arg, "Output file") if out_file_arg else None
terms = query_terms(query)
deterministic_paths = build_deterministic_paths(task_file)
deterministic = deterministic_payload(deterministic_paths, terms)

notes = [
    "Deterministic preload excludes reports/openclaw/ dumps by construction.",
    "Daily memory participates in expansion/fallback coverage, not primary preload order.",
]

if no_semantic:
    semantic = {"mode": "disabled", "results": []}
else:
    semantic = openclaw_semantic(query)

if not semantic.get("results") and include_daily:
    fallback = lexical_fallback(build_daily_pool(daily_limit), terms)
    if fallback.get("results"):
        if semantic.get("blocked"):
            notes.append("Used lexical fallback because local semantic expansion was blocked.")
        semantic = fallback

payload = {
    "query": query,
    "deterministic": deterministic,
    "semantic": semantic,
    "notes": notes,
}

if require_semantic and semantic.get("mode") != "openclaw-local":
    if output_format == "json":
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        rendered = render_text(payload)
    if out_file:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    raise SystemExit(3)

if output_format == "json":
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
else:
    rendered = render_text(payload)

if out_file:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(rendered, encoding="utf-8")
else:
    sys.stdout.write(rendered)
PY
}

main() {
  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    usage
    exit 1
  fi
  shift || true

  case "$cmd" in
    retrieve)
      retrieve_command "$@"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "Unknown command: $cmd" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
```

## Hook Wiring Needed in `observer-worker.sh`

Minimal follow-up patch:
- add `OM_POST_CAPTURE_HOOK` and `OM_POST_CAPTURE_HOOK_STRICT`
- export `OM_CAPTURE_QUERY`, `OM_CAPTURE_EVENT`, `OM_CAPTURE_CONTEXT`, `OM_CAPTURE_SOURCE`, etc. after `capture`
- run the hook after capture finishes
- if hook fails, print a Recipe 04-style blocker instead of pretending it ran

That keeps the retriever optional and auditable instead of baking in hidden coupling.
