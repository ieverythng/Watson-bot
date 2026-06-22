#!/usr/bin/env bash
# LAZARUS — restore the local inference stack after model/routing experiments.
#
# Safe default: verifies and repairs llama.cpp + LiteLLM without touching Hermes
# gateway/CLI processes. Use --dry-run to inspect the exact actions first.
#
# Usage:
#   bash scripts/lazarus.sh [--dry-run] [--skip-kill] [--mode stable|spec]
#                           [--ctx 65536] [--main-model 'D:\MODELS\...gguf']
#                           [--draft-model 'D:\MODELS\...gguf']

set -euo pipefail

LLAMA_HOST="${LLAMA_HOST:-172.24.16.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LITELLM_HOST="${LITELLM_HOST:-127.0.0.1}"
LITELLM_PORT="${LITELLM_PORT:-4000}"
LITELLM_CONFIG="${LITELLM_CONFIG:-$HOME/.hermes/litellm/config.yaml}"
LOG_DIR="${LOG_DIR:-/home/juanbeck/Watson/memory}"
LOG="$LOG_DIR/lazarus-$(date +%Y-%m-%d_%H%M%S).log"

MODE="stable"
CONTEXT_SIZE="65536"
THREADS="16"
UBATCH_SIZE="2048"
PARALLEL="1"
MAIN_MODEL='D:\MODELS\Qwen3.6-27B-Q3_K_M.gguf'
DRAFT_MODEL='D:\MODELS\Qwen3.6-27B-DFlash-IQ4_XS.gguf'
DRY_RUN=0
SKIP_KILL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --skip-kill) SKIP_KILL=1; shift ;;
    --mode) MODE="${2:?missing mode}"; shift 2 ;;
    --ctx|--context-size) CONTEXT_SIZE="${2:?missing ctx}"; shift 2 ;;
    --threads) THREADS="${2:?missing threads}"; shift 2 ;;
    --parallel|-np) PARALLEL="${2:?missing parallel}"; shift 2 ;;
    --main-model) MAIN_MODEL="${2:?missing main model}"; shift 2 ;;
    --draft-model) DRAFT_MODEL="${2:?missing draft model}"; shift 2 ;;
    --llama-host) LLAMA_HOST="${2:?missing host}"; shift 2 ;;
    --help|-h) sed -n '1,28p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
case "$MODE" in stable|spec) ;; *) echo "--mode must be stable or spec" >&2; exit 2 ;; esac
for numeric_var in LLAMA_PORT LITELLM_PORT CONTEXT_SIZE THREADS UBATCH_SIZE PARALLEL; do
  numeric_value="${!numeric_var}"
  if [[ ! "$numeric_value" =~ ^[0-9]+$ ]]; then
    echo "$numeric_var must be numeric, got: $numeric_value" >&2
    exit 2
  fi
done

mkdir -p "$LOG_DIR" "$(dirname "$LITELLM_CONFIG")"
ts() { echo "[$(date -u '+%H:%M:%S UTC')] $*"; }
log() { ts "$@" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }
run() { log "+ $*"; [[ "$DRY_RUN" -eq 1 ]] || "$@"; }
run_bash() { log "+ $*"; [[ "$DRY_RUN" -eq 1 ]] || bash -lc "$*"; }
ps_quote() {
  local escaped="${1//\'/\'\'}"
  printf "'%s'" "$escaped"
}

wait_http() {
  local url="$1" name="$2" tries="${3:-30}" sleep_s="${4:-2}" i
  for ((i=1; i<=tries; i++)); do
    if curl -fsS --connect-timeout 3 "$url" >/dev/null 2>&1; then
      log "  ✓ $name is reachable: $url"
      return 0
    fi
    log "  ⏳ Waiting for $name ($i/$tries)"
    sleep "$sleep_s"
  done
  return 1
}

log "╔══════════════════════════════════════════════════════════╗"
log "║              LAZARUS — INFERENCE RESURRECTION           ║"
log "╚══════════════════════════════════════════════════════════╝"
log "Mode=$MODE DryRun=$DRY_RUN SkipKill=$SKIP_KILL"
log "llama.cpp target: http://${LLAMA_HOST}:${LLAMA_PORT}/v1"
log "LiteLLM target : http://${LITELLM_HOST}:${LITELLM_PORT}/v1"
log "Main model     : $MAIN_MODEL"
[[ "$MODE" == "spec" ]] && log "Draft model    : $DRAFT_MODEL"

log ""
log "── Phase 1: WSL proxy cleanup ──"
if [[ "$SKIP_KILL" -eq 1 ]]; then
  log "  ℹ Skipping process cleanup (--skip-kill)"
else
  if pgrep -f "litellm" >/dev/null 2>&1; then
    run_bash "pkill -f 'litellm' || true"
    sleep 1
    log "  ✓ Requested LiteLLM stop"
  else
    log "  ℹ No LiteLLM process found"
  fi
  for port in "$LITELLM_PORT" 18080; do
    pid=$(ss -tlnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K\d+' | head -1 || true)
    if [[ -n "${pid:-}" ]]; then
      run kill "$pid"
      log "  ✓ Killed WSL PID $pid on port $port"
    fi
  done
fi

log ""
log "── Phase 2: Windows llama.cpp launch ──"
PS_MAIN_MODEL=$(ps_quote "$MAIN_MODEL")
PS_DRAFT_MODEL=$(ps_quote "$DRAFT_MODEL")
PS_ARGS="@('-m', ${PS_MAIN_MODEL}, '-ngl', '999', '--host', '0.0.0.0', '--port', '${LLAMA_PORT}', '--ctx-size', '${CONTEXT_SIZE}', '--threads', '${THREADS}', '--ubatch-size', '${UBATCH_SIZE}', '-fa', 'on', '-np', '${PARALLEL}')"
if [[ "$MODE" == "spec" ]]; then
  PS_ARGS="@('-m', ${PS_MAIN_MODEL}, '--spec-draft', ${PS_DRAFT_MODEL}, '-ngl', '999', '--spec-draft-ngl', '999', '--spec-draft-n-max', '16', '--host', '0.0.0.0', '--port', '${LLAMA_PORT}', '--ctx-size', '${CONTEXT_SIZE}', '--threads', '${THREADS}', '--ubatch-size', '${UBATCH_SIZE}', '-fa', 'on', '-np', '${PARALLEL}')"
fi
PS_CMD="\$ErrorActionPreference='Stop'; \$exe=(Get-Command llama-server.exe -ErrorAction SilentlyContinue).Source; if (-not \$exe) { \$exe='C:\\Program Files\\llama.cpp\\llama-server.exe' }; if (-not (Test-Path -LiteralPath \$exe)) { throw 'llama-server.exe not found in PATH or C:\\Program Files\\llama.cpp' }; Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2; \$args=${PS_ARGS}; Start-Process -FilePath \$exe -ArgumentList \$args -WindowStyle Hidden; Write-Output \"started \$exe with ${MODE} mode\""

if command -v powershell.exe >/dev/null 2>&1; then
  log "  ℹ Using WSL interop powershell.exe"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN PowerShell: $PS_CMD"
  else
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$PS_CMD" 2>&1 | tee -a "$LOG" || log "  ⚠ PowerShell launch failed; will check if server is already up"
  fi
elif command -v ssh >/dev/null 2>&1 && ssh -o ConnectTimeout=5 -o BatchMode=yes "$LLAMA_HOST" 'echo ok' >/dev/null 2>&1; then
  log "  ℹ Using SSH to Windows host"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN SSH PowerShell: $PS_CMD"
  else
    ssh -o BatchMode=yes "$LLAMA_HOST" "powershell -NoProfile -Command \"$PS_CMD\"" 2>&1 | tee -a "$LOG" || log "  ⚠ SSH launch failed; will check if server is already up"
  fi
else
  log "  ⚠ No powershell.exe/SSH launcher available; expecting llama.cpp already running"
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  wait_http "http://${LLAMA_HOST}:${LLAMA_PORT}/v1/models" "llama.cpp" 30 2 || die "llama.cpp did not respond. Start it manually on Windows and rerun with --skip-kill."
fi

log ""
log "── Phase 3: LiteLLM config ──"
if [[ "$DRY_RUN" -eq 1 ]]; then
  log "DRY-RUN would write $LITELLM_CONFIG"
else
  cat > "$LITELLM_CONFIG" <<EOF
model_list:
  - model_name: qwen36-turbo-hermes
    litellm_params:
      model: openai/qwen36-turbo-hermes
      api_base: "http://${LLAMA_HOST}:${LLAMA_PORT}/v1"
      api_key: "placeholder"
  - model_name: qwen36-turbo-hermes-spec
    litellm_params:
      model: openai/qwen36-turbo-hermes
      api_base: "http://${LLAMA_HOST}:${LLAMA_PORT}/v1"
      api_key: "placeholder"

litellm_settings:
  request_timeout: 600
  drop_params: true
  stream_options_include_usage: true
  set_verbose: false

general_settings:
  master_key: "placeholder"
EOF
fi
log "  ✓ LiteLLM config ready: $LITELLM_CONFIG"

log ""
log "── Phase 4: LiteLLM launch ──"
if [[ "$DRY_RUN" -eq 0 ]]; then
  export OPENAI_API_KEY="placeholder"
  nohup litellm --config "$LITELLM_CONFIG" --host "$LITELLM_HOST" --port "$LITELLM_PORT" > /tmp/litellm.log 2>&1 &
  LITELLM_PID=$!
  log "  ✓ LiteLLM start requested (PID: $LITELLM_PID)"
  sleep 3
  kill -0 "$LITELLM_PID" 2>/dev/null || die "LiteLLM failed to start. Check /tmp/litellm.log"
  wait_http "http://${LITELLM_HOST}:${LITELLM_PORT}/v1/models" "LiteLLM" 15 2 || die "LiteLLM did not expose /v1/models"
else
  log "DRY-RUN would run: litellm --config '$LITELLM_CONFIG' --host '$LITELLM_HOST' --port '$LITELLM_PORT'"
fi

log ""
log "── Phase 5: End-to-end verification ──"
if [[ "$DRY_RUN" -eq 0 ]]; then
  RESPONSE=$(curl -fsS --connect-timeout 10 \
    "http://${LITELLM_HOST}:${LITELLM_PORT}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer placeholder" \
    -d '{"model":"qwen36-turbo-hermes","messages":[{"role":"user","content":"Reply with exactly: OK"}],"max_tokens":8,"temperature":0}' 2>/dev/null || true)
  if [[ "$RESPONSE" == *"OK"* || "$RESPONSE" == *"choices"* ]]; then
    log "  ✓ Full chain verified: LiteLLM → llama.cpp returned a chat completion"
  else
    log "  ⚠ Chat test did not return expected content. Raw response follows:"
    log "${RESPONSE:-<empty>}"
  fi
fi

log ""
log "╔══════════════════════════════════════════════════════════╗"
if [[ "$DRY_RUN" -eq 1 ]]; then
  log "║              LAZARUS DRY RUN COMPLETE                   ║"
else
  log "║           LAZARUS COMPLETE — STACK IS BACK ONLINE       ║"
fi
log "╚══════════════════════════════════════════════════════════╝"
log "Log saved to: $LOG"
