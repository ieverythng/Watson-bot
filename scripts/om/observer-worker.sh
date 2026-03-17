#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

OBS_FILE="${OBS_FILE:-$REPO_DIR/OBSERVATIONS.md}"
MEM_DIR="${MEM_DIR:-$REPO_DIR/memory}"
TEMPLATE_FILE="${TEMPLATE_FILE:-$MEM_DIR/templates/daily-memory-template.md}"
STATE_FILE="${STATE_FILE:-$MEM_DIR/observer-state.env}"

TURN_THRESHOLD="${OM_OBSERVER_TURN_THRESHOLD:-10}"
TOKEN_THRESHOLD="${OM_OBSERVER_TOKEN_THRESHOLD:-5000}"
POST_CAPTURE_HOOK="${OM_POST_CAPTURE_HOOK:-}"
POST_CAPTURE_HOOK_STRICT="${OM_POST_CAPTURE_HOOK_STRICT:-0}"

usage() {
  cat <<'EOF'
Usage:
  observer-worker.sh tick [--turns N] [--tokens N]
  observer-worker.sh observe --scope S --observation TEXT --evidence TEXT
                         [--confidence 0.00-1.00] [--expires DATE|none]
                         [--timestamp ISO-8601] [--date YYYY-MM-DD] [--no-reset]
  observer-worker.sh capture --scope S --event TEXT --source TEXT
                         [--context TEXT] [--observation TEXT]
                         [--confidence 0.00-1.00] [--evidence TEXT]
                         [--expires DATE|none] [--tokens N]
                         [--timestamp ISO-8601] [--date YYYY-MM-DD]

Environment:
  OM_OBSERVER_TURN_THRESHOLD   Default: 10
  OM_OBSERVER_TOKEN_THRESHOLD  Default: 5000
  OM_POST_CAPTURE_HOOK         Optional shell command run after capture.
                               Receives OM_CAPTURE_* env vars.
  OM_POST_CAPTURE_HOOK_STRICT  Default: 0. If 1, capture exits non-zero when hook fails.
  OBS_FILE                     Default: OBSERVATIONS.md in repo root
  MEM_DIR                      Default: memory/ in repo root
  TEMPLATE_FILE                Default: memory/templates/daily-memory-template.md
  STATE_FILE                   Default: memory/observer-state.env
EOF
}

is_int() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

validate_thresholds() {
  if ! is_int "$TURN_THRESHOLD" || ! is_int "$TOKEN_THRESHOLD"; then
    echo "Thresholds must be non-negative integers." >&2
    exit 1
  fi
}

timestamp_utc_now() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

date_utc_today() {
  date -u +"%Y-%m-%d"
}

normalize_line() {
  echo "$1" | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//'
}

estimate_tokens() {
  local text="$1"
  local chars=${#text}
  echo $(((chars + 3) / 4))
}

ensure_state_file() {
  mkdir -p "$(dirname "$STATE_FILE")"
  if [[ ! -f "$STATE_FILE" ]]; then
    cat > "$STATE_FILE" <<'EOF'
turns_since_flush=0
tokens_since_flush=0
events_since_flush=0
last_flush_at=
last_observation_id=
EOF
  fi
}

load_state() {
  ensure_state_file
  # shellcheck disable=SC1090
  source "$STATE_FILE"
  turns_since_flush="${turns_since_flush:-0}"
  tokens_since_flush="${tokens_since_flush:-0}"
  events_since_flush="${events_since_flush:-0}"
  last_flush_at="${last_flush_at:-}"
  last_observation_id="${last_observation_id:-}"
}

save_state() {
  cat > "$STATE_FILE" <<EOF
turns_since_flush=$turns_since_flush
tokens_since_flush=$tokens_since_flush
events_since_flush=$events_since_flush
last_flush_at=$last_flush_at
last_observation_id=$last_observation_id
EOF
}

ensure_observations_file() {
  if [[ -f "$OBS_FILE" ]]; then
    return
  fi
  mkdir -p "$(dirname "$OBS_FILE")"
  cat > "$OBS_FILE" <<'EOF'
# OBSERVATIONS.md

Append-only observation log.
Each observation should be compact, evidence-backed, and optionally expirable.

## Observation Format

- `id`: `O-YYYY-MM-DD-NN`
- `timestamp`: ISO-8601 UTC
- `scope`: `user|project|infra|process`
- `confidence`: `0.00-1.00`
- `observation`: single durable statement
- `evidence`: source links to local files/lines
- `expires`: optional date when likely stale

## Entries
EOF
}

ensure_daily_file() {
  local date="$1"
  local file="$MEM_DIR/$date.md"

  mkdir -p "$MEM_DIR"
  if [[ -f "$file" ]]; then
    return
  fi

  if [[ -f "$TEMPLATE_FILE" ]]; then
    sed "1s/YYYY-MM-DD/$date/" "$TEMPLATE_FILE" > "$file"
    return
  fi

  cat > "$file" <<EOF
# $date

## Raw Events

## Retain (Observer Output)

## Reflection Candidates
EOF
}

insert_entry_before_header() {
  local file="$1"
  local header="$2"
  local entry="$3"
  local tmp_file
  local entry_file

  tmp_file="$(mktemp)"
  entry_file="$(mktemp)"
  printf "%s\n" "$entry" > "$entry_file"

  awk -v header="$header" -v entry_file="$entry_file" '
BEGIN {
  inserted = 0
  entry = ""
  while ((getline line < entry_file) > 0) {
    entry = entry line "\n"
  }
  close(entry_file)
}
$0 == header && inserted == 0 {
  printf "\n%s", entry
  inserted = 1
}
{
  print
}
END {
  if (inserted == 0) {
    printf "\n%s", entry
  }
}
' "$file" > "$tmp_file"

  mv "$tmp_file" "$file"
  rm -f "$entry_file"
}

threshold_reached() {
  if (( turns_since_flush >= TURN_THRESHOLD )); then
    return 0
  fi
  if (( tokens_since_flush >= TOKEN_THRESHOLD )); then
    return 0
  fi
  return 1
}

next_observation_id() {
  local date="$1"
  local max_seq=0
  local seq

  ensure_observations_file
  while IFS= read -r seq; do
    if is_int "$seq" && (( seq > max_seq )); then
      max_seq="$seq"
    fi
  done < <(
    grep -E "O-${date}-[0-9]{2}$" "$OBS_FILE" 2>/dev/null \
      | sed -E 's/.*O-[0-9]{4}-[0-9]{2}-[0-9]{2}-([0-9]{2})$/\1/' \
      || true
  )

  printf "O-%s-%02d" "$date" "$((max_seq + 1))"
}

append_observation_global() {
  local id="$1"
  local timestamp="$2"
  local scope="$3"
  local confidence="$4"
  local observation="$5"
  local evidence="$6"
  local expires="$7"

  ensure_observations_file
  {
    echo ""
    echo "- \`id\`: $id"
    echo "  - \`timestamp\`: $timestamp"
    echo "  - \`scope\`: $scope"
    echo "  - \`confidence\`: $confidence"
    echo "  - \`observation\`: $observation"
    echo "  - \`evidence\`: $evidence"
    echo "  - \`expires\`: $expires"
  } >> "$OBS_FILE"
}

append_raw_event_daily() {
  local date="$1"
  local timestamp="$2"
  local event="$3"
  local context="$4"
  local source="$5"
  local file="$MEM_DIR/$date.md"

  ensure_daily_file "$date"
  insert_entry_before_header "$file" "## Retain (Observer Output)" "- Timestamp: $timestamp
  - Event: $event
  - Context: $context
  - Source: $source"
}

append_retain_observation_daily() {
  local date="$1"
  local id="$2"
  local scope="$3"
  local observation="$4"
  local confidence="$5"
  local evidence="$6"
  local expires="$7"
  local file="$MEM_DIR/$date.md"

  ensure_daily_file "$date"
  insert_entry_before_header "$file" "## Reflection Candidates" "- $id:
  - Scope: $scope
  - Observation: $observation
  - Confidence: $confidence
  - Evidence: $evidence
  - Expiry: $expires"
}

write_observation() {
  local scope="$1"
  local observation="$2"
  local confidence="$3"
  local evidence="$4"
  local expires="$5"
  local timestamp="$6"
  local date="$7"
  local reset_counters="$8"
  local id

  scope="$(normalize_line "$scope")"
  observation="$(normalize_line "$observation")"
  confidence="$(normalize_line "$confidence")"
  evidence="$(normalize_line "$evidence")"
  expires="$(normalize_line "$expires")"

  id="$(next_observation_id "$date")"
  append_observation_global "$id" "$timestamp" "$scope" "$confidence" "$observation" "$evidence" "$expires"
  append_retain_observation_daily "$date" "$id" "$scope" "$observation" "$confidence" "$evidence" "$expires"

  if [[ "$reset_counters" == "true" ]]; then
    turns_since_flush=0
    tokens_since_flush=0
    events_since_flush=0
    last_flush_at="$timestamp"
    last_observation_id="$id"
    save_state
  fi

  echo "observation_id=$id"
  echo "observation_written=true"
}

run_post_capture_hook() {
  local scope="$1"
  local event="$2"
  local context="$3"
  local source="$4"
  local observation="$5"
  local timestamp="$6"
  local date="$7"
  local hook_query
  local rc

  if [[ -z "$POST_CAPTURE_HOOK" ]]; then
    return 0
  fi

  hook_query="$(normalize_line "$observation")"
  if [[ -z "$hook_query" || "$hook_query" == "none" ]]; then
    hook_query="$event"
    if [[ -n "$context" && "$context" != "none" ]]; then
      hook_query="$event $context"
    fi
  fi

  export OM_CAPTURE_SCOPE="$scope"
  export OM_CAPTURE_EVENT="$event"
  export OM_CAPTURE_CONTEXT="$context"
  export OM_CAPTURE_SOURCE="$source"
  export OM_CAPTURE_OBSERVATION="$(normalize_line "$observation")"
  export OM_CAPTURE_TIMESTAMP="$timestamp"
  export OM_CAPTURE_DATE="$date"
  export OM_CAPTURE_QUERY="$hook_query"

  if bash -lc "$POST_CAPTURE_HOOK"; then
    echo "post_capture_hook=true"
    echo "post_capture_hook_status=ok"
    return 0
  fi

  rc=$?
  echo "post_capture_hook=true"
  echo "post_capture_hook_status=failed"
  cat >&2 <<EOF
BLOCKED
- Tool: OM_POST_CAPTURE_HOOK
- Failure: exit code $rc
- Impact: optional post-capture hook did not complete after observer capture.
- Next action: fix OM_POST_CAPTURE_HOOK or unset it to keep capture-only flow.
EOF

  if [[ "$POST_CAPTURE_HOOK_STRICT" == "1" ]]; then
    exit "$rc"
  fi

  return 0
}

tick_command() {
  local turns=0
  local tokens=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --turns)
        turns="$2"
        shift 2
        ;;
      --tokens)
        tokens="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option for tick: $1" >&2
        exit 1
        ;;
    esac
  done

  if ! is_int "$turns" || ! is_int "$tokens"; then
    echo "--turns/--tokens must be integers." >&2
    exit 1
  fi

  load_state
  turns_since_flush=$((turns_since_flush + turns))
  tokens_since_flush=$((tokens_since_flush + tokens))
  events_since_flush=$((events_since_flush + turns))
  save_state

  echo "turns_since_flush=$turns_since_flush"
  echo "tokens_since_flush=$tokens_since_flush"
  echo "events_since_flush=$events_since_flush"
  if threshold_reached; then
    echo "observer_trigger=true"
  else
    echo "observer_trigger=false"
  fi
}

observe_command() {
  local scope=""
  local observation=""
  local confidence="0.80"
  local evidence=""
  local expires="none"
  local timestamp=""
  local date=""
  local reset_counters="true"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scope)
        scope="$2"
        shift 2
        ;;
      --observation)
        observation="$2"
        shift 2
        ;;
      --confidence)
        confidence="$2"
        shift 2
        ;;
      --evidence)
        evidence="$2"
        shift 2
        ;;
      --expires)
        expires="$2"
        shift 2
        ;;
      --timestamp)
        timestamp="$2"
        shift 2
        ;;
      --date)
        date="$2"
        shift 2
        ;;
      --no-reset)
        reset_counters="false"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option for observe: $1" >&2
        exit 1
        ;;
    esac
  done

  if [[ -z "$scope" || -z "$observation" || -z "$evidence" ]]; then
    echo "observe requires --scope, --observation, and --evidence." >&2
    exit 1
  fi

  if [[ -z "$timestamp" ]]; then
    timestamp="$(timestamp_utc_now)"
  fi
  if [[ -z "$date" ]]; then
    date="${timestamp:0:10}"
  fi

  load_state
  ensure_daily_file "$date"
  write_observation "$scope" "$observation" "$confidence" "$evidence" "$expires" "$timestamp" "$date" "$reset_counters"
}

capture_command() {
  local scope=""
  local event=""
  local context=""
  local source=""
  local observation=""
  local confidence="0.80"
  local evidence=""
  local expires="none"
  local tokens=""
  local timestamp=""
  local date=""
  local normalized_event
  local normalized_context
  local token_estimate

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scope)
        scope="$2"
        shift 2
        ;;
      --event)
        event="$2"
        shift 2
        ;;
      --context)
        context="$2"
        shift 2
        ;;
      --source)
        source="$2"
        shift 2
        ;;
      --observation)
        observation="$2"
        shift 2
        ;;
      --confidence)
        confidence="$2"
        shift 2
        ;;
      --evidence)
        evidence="$2"
        shift 2
        ;;
      --expires)
        expires="$2"
        shift 2
        ;;
      --tokens)
        tokens="$2"
        shift 2
        ;;
      --timestamp)
        timestamp="$2"
        shift 2
        ;;
      --date)
        date="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option for capture: $1" >&2
        exit 1
        ;;
    esac
  done

  if [[ -z "$scope" || -z "$event" || -z "$source" ]]; then
    echo "capture requires --scope, --event, and --source." >&2
    exit 1
  fi

  if [[ -z "$timestamp" ]]; then
    timestamp="$(timestamp_utc_now)"
  fi
  if [[ -z "$date" ]]; then
    date="${timestamp:0:10}"
  fi

  normalized_event="$(normalize_line "$event")"
  normalized_context="$(normalize_line "$context")"
  if [[ -z "$normalized_context" ]]; then
    normalized_context="none"
  fi

  if [[ -z "$observation" ]]; then
    observation="$normalized_event"
  fi

  if [[ -z "$evidence" ]]; then
    evidence="$source"
  fi

  if [[ -z "$tokens" ]]; then
    token_estimate="$(estimate_tokens "$normalized_event $normalized_context")"
  else
    token_estimate="$tokens"
  fi

  if ! is_int "$token_estimate"; then
    echo "--tokens must be an integer." >&2
    exit 1
  fi

  ensure_daily_file "$date"
  append_raw_event_daily "$date" "$timestamp" "$normalized_event" "$normalized_context" "$(normalize_line "$source")"

  load_state
  turns_since_flush=$((turns_since_flush + 1))
  tokens_since_flush=$((tokens_since_flush + token_estimate))
  events_since_flush=$((events_since_flush + 1))

  echo "turns_since_flush=$turns_since_flush"
  echo "tokens_since_flush=$tokens_since_flush"
  echo "events_since_flush=$events_since_flush"

  if threshold_reached; then
    write_observation "$scope" "$observation" "$confidence" "$evidence" "$expires" "$timestamp" "$date" "true"
    echo "observer_trigger=true"
  else
    save_state
    echo "observer_trigger=false"
  fi

  run_post_capture_hook "$scope" "$normalized_event" "$normalized_context" "$(normalize_line "$source")" "$observation" "$timestamp" "$date"
}

main() {
  validate_thresholds
  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    usage
    exit 1
  fi
  shift || true

  case "$cmd" in
    tick)
      tick_command "$@"
      ;;
    observe)
      observe_command "$@"
      ;;
    capture)
      capture_command "$@"
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
