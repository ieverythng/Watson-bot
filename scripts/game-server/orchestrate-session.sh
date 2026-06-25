#!/usr/bin/env bash
# orchestrate-session.sh — VRAM-aware gaming session orchestrator.
#
# Adaptive model routing based on game + VRAM state:
#   - No game / idle     → 27B full model (all VRAM available)
#   - Big game running   → GPT-5.4-mini via gateway (zero local VRAM)
#   - Mid game           → LFM2-8B lightweight model (shares VRAM)
#   - Game exiting       → kill tiny → load 27B full restore
#
# Flow:
#   1. KILL full inference stack (frees VRAM for game)
#   2. Switch Hermes gateway to remote GPT-5.4-mini (no VRAM cost)
#   3. LAUNCH game via Sunshine
#   4. MONITOR game process + VRAM — adaptive model decisions
#   5. GAME EXITS → kill lightweight → REVIVE full 27B stack
#
# Usage:
#   bash scripts/game-server/orchestrate-session.sh [game_name] [--no-resume] [--no-lightweight] [--auto-close-after SECONDS]
#
# Default: adaptive mode tries LFM2-8B when VRAM headroom is sufficient.
# Use --no-lightweight for a clean remote-only gameplay run.
# Use --auto-close-after for bounded tests that close the game automatically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"
ROOT="$(dirname "$SCRIPT_DIR")/.."
LAZARUS="$ROOT/scripts/lazarus.sh"
LOG_DIR="$ROOT/memory"
LOG="$LOG_DIR/orchestrate-$(date +%Y-%m-%d_%H%M%S).log"

# Model tiers
FULL_MODEL_ALIAS="qwen36-turbo-hermes"
FULL_PROFILE="hermes-qwen36-64k"
LIGHTWEIGHT_MODEL="/mnt/d/MODELS/LFM2-8B-A1B-Q4_K_M.gguf"
LIGHTWEIGHT_ALIAS="lfm2-8b-lightweight"

# Game config
GAME_NAME="${1:-mina_the_hollower}"
NO_RESUME=0
NO_LIGHTWEIGHT=0
AUTO_CLOSE_AFTER=0
shift 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-resume) NO_RESUME=1; shift ;;
        --no-lightweight) NO_LIGHTWEIGHT=1; shift ;;
        --auto-close-after=*) AUTO_CLOSE_AFTER="${1#*=}"; shift ;;
        --auto-close-after) AUTO_CLOSE_AFTER="${2:?missing seconds}"; shift 2 ;;
        mina_the_hollower|equinox_homecoming) GAME_NAME="$1"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

mkdir -p "$LOG_DIR"
ts() { echo "[$(date -u '+%H:%M:%S UTC')] $*"; }
log() { ts "$@" | tee -a "$LOG"; }

# ─── Helpers ──────────────────────────────────────────────────────

get_vram_mb() {
    local vram
    vram=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        try {
            \$v = nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>\$null;
            if (\$v) { Write-Host \$v.Trim() } else { Write-Host '0' }
        } catch { Write-Host '0' }
    " 2>/dev/null | tr -d '\r')
    echo "${vram:-0}"
}

get_vram_total_mb() {
    local total
    total=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        try {
            \$v = nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>\$null;
            if (\$v) { Write-Host \$v.Trim() } else { Write-Host '0' }
        } catch { Write-Host '0' }
    " 2>/dev/null | tr -d '\r')
    echo "${total:-0}"
}

read_config_field() {
    python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
g = c['games']['$GAME_NAME']
v = g.get('$1', '$2')
# Normalize JSON null / Python None / empty-ish values so bash does not treat
# them as real launch targets (bug: steam_appid null became string 'None').
if v is None or v == 'None' or v == 'null':
    v = '$2'
print(v)
" 2>/dev/null || echo "$2"
}

wait_http() {
    local url="$1" name="$2" tries="${3:-60}" sleep_s="${4:-2}"
    for ((i=1; i<=tries; i++)); do
        local status
        status=$(curl -sS --connect-timeout 3 --max-time 10 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo "000")
        if [[ "$status" == "200" ]]; then
            log "  ✓ $name reachable: $url"
            return 0
        fi
        if (( i % 15 == 0 )); then
            log "  ⏳ Waiting for $name ($i/$tries)"
        fi
        sleep "$sleep_s"
    done
    log "  ✗ $name did not respond after $tries attempts"
    return 1
}

# Model state tracking
LIGHTWEIGHT_LLAMA_PID=""
LIGHTWEIGHT_LITELLM_PID=""
CURRENT_TIER="full"  # full | remote | lightweight | none

switch_tier() {
    local target="$1"
    [[ "$target" == "$CURRENT_TIER" ]] && { log "  ℹ Already at tier: $target"; return 0; }

    log "  → Switching model tier: $CURRENT_TIER → $target"

    case "$target" in
        remote)
            # Kill any local models, Hermes uses gateway → GPT-5.4-mini (no VRAM)
            if [[ -n "$LIGHTWEIGHT_LLAMA_PID" ]]; then
                kill "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
                kill "${LIGHTWEIGHT_LITELLM_PID:-}" 2>/dev/null || true
                sleep 1
                log "  ✓ Killed lightweight model"
                LIGHTWEIGHT_LLAMA_PID=""
                LIGHTWEIGHT_LITELLM_PID=""
            fi
            # Hermes gateway already routes to openai-codex/gpt-5.4-mini — no local action needed
            ;;
        lightweight)
            # Kill full stack if still running, launch lightweight model
            if [[ "$CURRENT_TIER" == "full" ]]; then
                kill_litellm_wsl
                kill_llama_windows
                sleep 2
            fi
            # Kill existing lightweight if switching from remote
            if [[ -n "$LIGHTWEIGHT_LLAMA_PID" ]]; then
                kill "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
                kill "${LIGHTWEIGHT_LITELLM_PID:-}" 2>/dev/null || true
                sleep 1
            fi
            launch_lightweight
            ;;
        full)
            # Kill lightweight, run Lazarus to restore full stack
            if [[ -n "$LIGHTWEIGHT_LLAMA_PID" ]]; then
                kill "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
                kill "${LIGHTWEIGHT_LITELLM_PID:-}" 2>/dev/null || true
                sleep 1
                log "  ✓ Killed lightweight model"
                LIGHTWEIGHT_LLAMA_PID=""
                LIGHTWEIGHT_LITELLM_PID=""
            fi
            ;;
    esac
    CURRENT_TIER="$target"
}

kill_litellm_wsl() {
    if pgrep -f "litellm" >/dev/null 2>&1; then
        pkill -f 'litellm' || true
        sleep 1
        log "  ✓ Killed WSL LiteLLM"
    else
        log "  ℹ No WSL LiteLLM running"
    fi
}

kill_llama_windows() {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        \$procs = Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue;
        if (\$procs) {
            \$procs | Stop-Process -Force;
            Write-Host '✓ Killed llama.cpp'
        } else {
            Write-Host 'ℹ No llama.cpp running'
        }
    " 2>&1 | sed 's/^/  /'
}

launch_lightweight() {
    log "  Launching lightweight model: $LIGHTWEIGHT_MODEL"

    if [[ ! -f "$LIGHTWEIGHT_MODEL" ]]; then
        log "  ⚠ Model not found — falling back to remote tier"
        CURRENT_TIER="remote"
        return 1
    fi

    # Launch LFM2 on the canonical llama.cpp port (8080), replacing the full
    # Qwen backend in-place. LiteLLM/Hermes already route to 4000 → 8080, so
    # this proves the same session path can dynamically swap the loaded model
    # without needing the blocked 8081 firewall path.
    WINDOWS_MODEL='D:\\MODELS\\LFM2-8B-A1B-Q4_K_M.gguf'
    WINDOWS_LAUNCHER='C:\\Users\\Admin\\PROJECTS\\llama-cpp-server\\scripts\\start_turbo_hermes.ps1'

    # Keep this PowerShell command on one line. Backticks inside a Bash
    # double-quoted string are command substitution, so PowerShell line
    # continuations become Bash commands like '-Port: command not found'.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "\$ErrorActionPreference = 'Stop'; \$launcher = '$WINDOWS_LAUNCHER'; if (-not (Test-Path \$launcher)) { throw \"Launcher not found: \$launcher\" }; & \$launcher -Port 8080 -ContextSize 8192 -Profile hermes-qwen36-64k -ModelPath '$WINDOWS_MODEL' -BatchSize 1024 -UBatchSize 256" > "$LOG_DIR/lightweight-llama.log" 2>&1 &
    LIGHTWEIGHT_LLAMA_PID=$!
    log "  Windows launcher PID: $LIGHTWEIGHT_LLAMA_PID"

    # Do not gate on raw WSL → Windows:8080 reachability here. The real Hermes
    # path is WSL → LiteLLM:4000, and LiteLLM runs on Windows so it reaches
    # llama.cpp via Windows localhost:8080. Smoke that exact path instead.
    log "  Waiting for LiteLLM→LFM2 path on canonical backend port..."
    for ((i=1; i<=60; i++)); do
        if python3 - <<'PY' >> "$LOG" 2>&1
import json, urllib.request, sys
payload={"model":"qwen36-turbo-hermes","messages":[{"role":"user","content":"Reply with exactly LFM2_OK"}],"max_tokens":12,"temperature":0}
req=urllib.request.Request("http://172.24.16.1:4000/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json","Authorization":"Bearer ***"})
with urllib.request.urlopen(req, timeout=120) as r:
    body=r.read().decode()
print(body)
if "LFM2_OK" not in body:
    sys.exit(2)
PY
        then
            log "  ✓ LiteLLM→LFM2 smoke passed (same 4000 endpoint)"
            CURRENT_TIER="lightweight"
            return 0
        fi
        if (( i % 10 == 0 )); then
            log "  ⏳ Waiting for LiteLLM→LFM2 smoke ($i/60)"
        fi
        sleep 5
    done

    log "  ⚠ LiteLLM→LFM2 smoke failed; disabling lightweight tier"
    kill "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
    kill_llama_windows
    LIGHTWEIGHT_LLAMA_PID=""
    CURRENT_TIER="remote"
    NO_LIGHTWEIGHT=1
    return 1
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 0: Banner
# ═══════════════════════════════════════════════════════════════════

log ""
log "╔══════════════════════════════════════════════════════════╗"
log "║     VRAM-AWARE GAMING ORCHESTRATOR (Kill→Monitor→Revive) ║"
log "╚══════════════════════════════════════════════════════════╝"
log ""

# Read game config
GAME_EXE=$(read_config_field "exe" "")
GAME_WORKING_DIR=$(read_config_field "working_dir" "")
GAME_PROCESS=$(read_config_field "process_name" "")
STEAM_APPID=$(read_config_field "steam_appid" "")

log "Game: $GAME_NAME"
log "Process: ${GAME_PROCESS:-<unknown>}"
log "Launch: ${STEAM_APPID:+Steam APPID:$STEAM_APPID}${STEAM_APPID:-$GAME_EXE}"
log ""

VRAM_TOTAL=$(get_vram_total_mb)
VRAM_BEFORE=$(get_vram_mb)
log "VRAM total: ${VRAM_TOTAL} MB, used before: ${VRAM_BEFORE} MB"
log ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: Kill Full Inference Stack → Switch to Remote (GPT-5.4-mini)
# ═══════════════════════════════════════════════════════════════════

log "── Phase 1: Killing Full Stack → Remote Tier ──"
log "  Freeing VRAM for game. Hermes stays online via GPT-5.4-mini (remote)."

kill_litellm_wsl
kill_llama_windows
sleep 2

VRAM_AFTER_KILL=$(get_vram_mb)
log "VRAM after kill: ${VRAM_AFTER_KILL} MB (freed $(( VRAM_BEFORE - VRAM_AFTER_KILL )) MB)"

CURRENT_TIER="remote"
log "  ✓ Model tier: remote (GPT-5.4-mini via gateway, zero VRAM cost)"
log ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: Launch Game
# ═══════════════════════════════════════════════════════════════════

log "── Phase 2: Launching Game ──"

if [[ -n "$STEAM_APPID" ]]; then
    log "  Launching Steam game (APPID: $STEAM_APPID)..."
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        Start-Process 'C:\\\\Program Files (x86)\\\\Steam\\\\steam.exe' '-applaunch $STEAM_APPID';
        Write-Host '✓ Game launched via Steam'
    " 2>&1 | sed 's/^/  /'
elif [[ -n "$GAME_EXE" ]]; then
    log "  Launching: $GAME_EXE"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        Start-Process -FilePath '$GAME_EXE' -WorkingDirectory '$GAME_WORKING_DIR';
        Write-Host '✓ Game launched'
    " 2>&1 | sed 's/^/  /'
else
    log "  ⚠ No launch method configured"
    exit 1
fi

sleep 3
VRAM_GAME=$(get_vram_mb)
log "VRAM after launch attempt: ${VRAM_GAME} MB"

# Confirm the game process actually appeared before entering the monitor loop.
# Without this, a bad launch path can look like an immediate clean exit and
# Lazarus will revive the full stack while the user thinks the game is starting.
if [[ -n "$GAME_PROCESS" ]]; then
    log "  Waiting for game process to appear: $GAME_PROCESS"
    GAME_STARTED=0
    for ((i=1; i<=24; i++)); do
        WIN_CHECK=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            \$p = Get-Process -Name '$GAME_PROCESS' -ErrorAction SilentlyContinue;
            if (\$p) { 'RUNNING' } else { 'MISSING' }
        " 2>/dev/null | tr -d '\r')
        if [[ "$WIN_CHECK" == *"RUNNING"* ]]; then
            GAME_STARTED=1
            log "  ✓ Game process detected ($GAME_PROCESS)"
            break
        fi
        sleep 5
    done
    if [[ "$GAME_STARTED" -ne 1 ]]; then
        log "  ✗ Game process did not appear after 120s. Launch likely failed."
        if [[ "$NO_RESUME" -eq 0 && -f "$LAZARUS" ]]; then
            log "  Restoring full inference stack because launch failed..."
            bash "$LAZARUS" --skip-kill
        fi
        exit 1
    fi
fi
log ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: Monitor Game + Adaptive VRAM Routing
# ═══════════════════════════════════════════════════════════════════

log "── Phase 3: Monitoring Game + Adaptive Model Routing ──"
log "Polling every 5s. Model tier adapts to available VRAM."
log ""

# Thresholds (tunable)
VRAM_HEADROOM_LIGHTWEIGHT=10240  # MB free needed to load LFM2-8B (~5-6GB VRAM)
VRAM_HEADROOM_FULL=13312          # MB free needed for 27B (~13GB VRAM, <0.5GB other usage)

TICK=0
GAME_EXITED=0

while [[ "$GAME_EXITED" -eq 0 ]]; do
    sleep 5
    TICK=$((TICK + 1))
    ELAPSED=$((TICK * 5))

    if [[ "$AUTO_CLOSE_AFTER" =~ ^[0-9]+$ && "$AUTO_CLOSE_AFTER" -gt 0 && "$ELAPSED" -ge "$AUTO_CLOSE_AFTER" && -n "$GAME_PROCESS" ]]; then
        log "  ⏱ Auto-close threshold reached (${ELAPSED}s >= ${AUTO_CLOSE_AFTER}s); closing $GAME_PROCESS"
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            \$p = Get-Process -Name '$GAME_PROCESS' -ErrorAction SilentlyContinue;
            if (\$p) { \$p | Stop-Process -Force; Write-Host '✓ Game process stopped by auto-close' }
        " 2>&1 | sed 's/^/  /'
        AUTO_CLOSE_AFTER=0
        sleep 2
    fi

    # Check if game is still running
    if [[ -n "$GAME_PROCESS" ]]; then
        WIN_CHECK=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            \$p = Get-Process -Name '$GAME_PROCESS' -ErrorAction SilentlyContinue;
            if (\$p) { 'RUNNING' } else { 'EXITED' }
        " 2>/dev/null | tr -d '\r')

        if [[ "$WIN_CHECK" == *"EXITED"* ]]; then
            log ""
            log "  ✓ Game process exited! (tick $TICK, ~$((TICK * 5 / 60))m)"
            GAME_EXITED=1
            continue
        fi
    fi

    # Report every 12 ticks (~1 minute)
    if (( TICK % 12 == 0 )); then
        VRAM_NOW=$(get_vram_mb)
        VRAM_FREE=$(( VRAM_TOTAL - VRAM_NOW ))
        log "  ⏳ Tick $TICK | Game running | Tier: $CURRENT_TIER | VRAM: ${VRAM_NOW}/${VRAM_TOTAL} MB (${VRAM_FREE} free)"

        # Adaptive decision: if game VRAM dropped enough, try lightweight
        if [[ "$NO_LIGHTWEIGHT" -eq 0 && "$CURRENT_TIER" == "remote" && "$VRAM_FREE" -ge "$VRAM_HEADROOM_LIGHTWEIGHT" ]]; then
            log "  → VRAM headroom sufficient (${VRAM_FREE} MB ≥ ${VRAM_HEADROOM_LIGHTWEIGHT} MB)"
            log "  → Trying lightweight model for better local responses..."
            launch_lightweight && log "  ✓ Switched to lightweight tier" || log "  ℹ Stayed on remote tier"
        elif [[ "$NO_LIGHTWEIGHT" -eq 1 && "$CURRENT_TIER" == "remote" ]]; then
            log "  ℹ Lightweight tier disabled (--no-lightweight); staying remote"
        fi
    fi
done

# If game process name is unknown, fall back to manual
if [[ -z "$GAME_PROCESS" ]]; then
    log "No process to monitor. Press Enter when done playing..."
    read -r
    GAME_EXITED=1
fi

log ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: Cleanup Lightweight Model
# ═══════════════════════════════════════════════════════════════════

if [[ -n "$LIGHTWEIGHT_LLAMA_PID" ]]; then
    log "── Phase 4: Cleaning Up Lightweight Model ──"
    kill "${LIGHTWEIGHT_LITELLM_PID:-}" 2>/dev/null || true
    kill "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$LIGHTWEIGHT_LLAMA_PID" 2>/dev/null || true
    kill -9 "${LIGHTWEIGHT_LITELLM_PID:-}" 2>/dev/null || true

    # The lightweight model is launched by Windows PowerShell, so the real
    # llama-server process may not be a WSL child PID. Kill the Windows
    # llama-server explicitly before Lazarus restores the full stack.
    kill_llama_windows

    # Kill stragglers on WSL port 8081 if any exist.
    STRAGGLER=$(ss -tlnp 'sport = :8081' 2>/dev/null | grep -oP 'pid=\K\d+' | head -1 || true)
    [[ -n "$STRAGGLER" ]] && kill "$STRAGGLER" 2>/dev/null || true

    sleep 1
    log "  ✓ Lightweight model cleaned up"
    VRAM_CLEAN=$(get_vram_mb)
    log "  VRAM after cleanup: ${VRAM_CLEAN} MB"
    log ""
fi

# ═══════════════════════════════════════════════════════════════════
# PHASE 5: Revive Full Stack (Lazarus)
# ═══════════════════════════════════════════════════════════════════

if [[ "$NO_RESUME" -eq 0 ]]; then
    log "── Phase 5: Reviving Full Inference Stack ──"
    if [[ -f "$LAZARUS" ]]; then
        # Lazarus sometimes leaves the PowerShell wrapper attached after the
        # stack is already healthy. Bound it, then verify the real endpoint.
        timeout 420 bash "$LAZARUS" --skip-kill || log "  ⚠ Lazarus command timed out or returned non-zero; checking endpoint health anyway"
        log "  Verifying restored Qwen endpoint through LiteLLM..."
        for ((i=1; i<=60; i++)); do
            if python3 - <<'PY' >> "$LOG" 2>&1
import json, urllib.request, sys
payload={"model":"qwen36-turbo-hermes","messages":[{"role":"user","content":"Reply with exactly QWEN_RESTORED"}],"max_tokens":16,"temperature":0}
req=urllib.request.Request("http://172.24.16.1:4000/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json","Authorization":"Bearer ***"})
with urllib.request.urlopen(req, timeout=120) as r:
    body=r.read().decode()
print(body)
if "QWEN_RESTORED" not in body:
    sys.exit(2)
PY
            then
                log "  ✓ Qwen restore smoke passed through LiteLLM"
                CURRENT_TIER="full"
                break
            fi
            log "  ⏳ Waiting for Qwen restore smoke ($i/60)"
            sleep 5
        done
        if [[ "$CURRENT_TIER" != "full" ]]; then
            log "  ⚠ Qwen restore smoke did not pass within timeout"
        fi
    else
        log "  ⚠ Lazarus not found — run manually: bash $LAZARUS"
    fi
else
    log "── Skipping revive (--no-resume) ──"
fi

log ""
log "╔══════════════════════════════════════════════════════════╗"
log "║     SESSION COMPLETE — WATSON BACK ON FULL MODEL       ║"
log "╚══════════════════════════════════════════════════════════╝"
log "Final tier: $CURRENT_TIER | Log: $LOG"
