#!/usr/bin/env bash
# orchestrate-game.sh — Full gaming session from WSL.
# Pauses Watson inference, launches game via Windows PowerShell, monitors, then Lazarus restores.
#
# Usage:
#   bash scripts/game-server/orchestrate-game.sh [game_name] [--no-resume]
#
# Games are defined in config.json. Default: mina_the_hollower

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"
ROOT="$(dirname "$SCRIPT_DIR")/.."  # Watson root
LAZARUS="$ROOT/scripts/lazarus.sh"

GAME_NAME="${1:-mina_the_hollower}"
NO_RESUME=0

# Parse args
for arg in "$@"; do
  case "$arg" in
    --no-resume) NO_RESUME=1 ;;
    mina_the_hollower|equinox_homecoming) GAME_NAME="$arg" ;;
  esac
done

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║         GAMING SESSION ORCHESTRATOR         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Game: $GAME_NAME"
echo ""

# Phase 1: Pause Watson — kill llama.cpp on Windows + WSL LiteLLM
echo "── Phase 1: Pausing Watson ──"

# Kill WSL-side LiteLLM proxies
if pgrep -f "litellm" >/dev/null 2>&1; then
    pkill -f 'litellm' || true
    echo "  ✓ Killed WSL LiteLLM"
else
    echo "  ℹ No WSL LiteLLM running"
fi

# Kill llama.cpp on Windows via PowerShell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
    \$procs = Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue;
    if (\$procs) {
        \$procs | Stop-Process -Force;
        Write-Host '✓ llama.cpp stopped';
    } else {
        Write-Host 'ℹ llama.cpp not running';
    };
    try {
        \$vram = nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounim 2>\$null;
        if (\$vram) { Write-Host ('VRAM: ' + \$vram.Trim() + ' MB') }
    } catch {}
" 2>&1 | sed 's/^/  /'

echo ""
sleep 2

# Phase 2: Launch game via PowerShell
echo "── Phase 2: Launching Game ──"

GAME_EXE=$(python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
g = c['games']['$GAME_NAME']
print(g.get('exe', ''))
")

GAME_WORKING_DIR=$(python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
g = c['games']['$GAME_NAME']
print(g.get('working_dir', ''))
")

GAME_PROCESS=$(python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
g = c['games']['$GAME_NAME']
print(g.get('process_name', ''))
")

STEAM_APPID=$(python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
g = c['games']['$GAME_NAME']
appid = g.get('steam_appid')
print(appid if appid else '')
")

if [[ -n "$STEAM_APPID" ]]; then
    echo "  Launching Steam game (APPID: $STEAM_APPID)..."
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        Start-Process 'C:\\Program Files (x86)\\Steam\\steam.exe' '-applaunch $STEAM_APPID';
        Write-Host '✓ Game launched via Steam';
    " 2>&1 | sed 's/^/  /'
elif [[ -n "$GAME_EXE" ]]; then
    echo "  Executable: $GAME_EXE"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        Start-Process -FilePath '$GAME_EXE' -WorkingDirectory '$GAME_WORKING_DIR';
        Write-Host '✓ Game launched';
    " 2>&1 | sed 's/^/  /'
else
    echo "  ⚠ No launch method configured for $GAME_NAME"
    exit 1
fi

echo ""
sleep 3

# Phase 3: Monitor game process
if [[ -n "$GAME_PROCESS" ]]; then
    echo "── Phase 3: Monitoring Game ($GAME_PROCESS) ──"
    echo "Waiting for game to exit..."
    
    while true; do
        if ! pgrep -af "$GAME_PROCESS" >/dev/null 2>&1; then
            # Also check Windows side
            WIN_CHECK=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
                \$p = Get-Process -Name '$GAME_PROCESS' -ErrorAction SilentlyContinue;
                if (\$p) { 'RUNNING' } else { 'EXITED' }
            " 2>/dev/null)
            if [[ "$WIN_CHECK" == *"EXITED"* ]]; then
                echo ""
                echo "  ✓ Game process exited!"
                break
            fi
        fi
        sleep 5
    done
else
    echo "── Phase 3: No auto-monitoring (no process name) ──"
    echo "Game launched. Press Enter when done playing..."
    read -r
fi

# Phase 4: Resume Watson via Lazarus
if [[ "$NO_RESUME" -eq 0 ]]; then
    echo ""
    echo "── Phase 4: Restoring Watson (Lazarus) ──"
    if [[ -f "$LAZARUS" ]]; then
        bash "$LAZARUS" --skip-kill
    else
        echo "  ⚠ Lazarus script not found at $LAZARUS"
        echo "  Run manually: bash $LAZARUS"
    fi
else
    echo ""
    echo "── Skipping resume (--no-resume) ──"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║          SESSION COMPLETE — ENJOY!           ║"
echo "╚══════════════════════════════════════════════╝"
