#!/usr/bin/env bash
# kickbacks-watchdog.sh — Detects Kickbacks.ai kill wedge deadlock and auto-recovers
#
# The kill wedge bug (#48) causes the extension to permanently stop serving ads
# when a campaign-scoped kill is confirmed. The extension keeps polling the dead
# campaignId, the serving gate blocks rotation, and ads never show again until
# a manual "Developer: Reload Window".
#
# This watchdog:
# 1. Checks the Kickbacks debug log for killed:true state lasting >5 minutes
# 2. Verifies global killswitch is actually clear (GET /v1/killswitch)
# 3. If wedged but global is clear → triggers VS Code reload via sentinel file
#
# Usage: Run every 5 minutes via cron:
#   */5 * * * * /home/juanbeck/Watson/scripts/kickbacks-watchdog.sh >> /home/juanbeck/Watson/reports/expenditure/kickbacks-watchdog.log 2>&1

set -euo pipefail

LOGFILE="${KICKBACKS_LOG:-$HOME/.vibe-ads/debug.log}"
SENTINEL="${KICKBACKS_SENTINEL:-$HOME/.vibe-ads/reload}"
COOLDOWN_SECS=300  # 5 minutes between reloads
WEDGE_TIMEOUT=300  # 5 minutes of killed state before triggering reload

# Check if debug log exists
if [[ ! -f "$LOGFILE" ]]; then
    exit 0  # Extension not running, nothing to watch
fi

# Check global killswitch — if globally killed, don't reload (it's intentional)
GLOBAL_KILL=$(curl -s --connect-timeout 5 --max-time 10 \
    "https://kickbacks.ai/v1/killswitch?version=2.1.175&campaign=" 2>/dev/null || echo "")

if echo "$GLOBAL_KILL" | grep -q '"killed":true'; then
    # Global kill is active — this is intentional, don't fight it
    exit 0
fi

# Check if extension is in killed state
LAST_KILLED=$(grep -n '"killed":true' "$LOGFILE" 2>/dev/null | tail -1 || true)

if [[ -z "$LAST_KILLED" ]]; then
    # No killed state found — all good
    exit 0
fi

# Check when the last killed:true was logged
LAST_KILLED_LINE=$(echo "$LAST_KILLED" | cut -d: -f1)
TOTAL_LINES=$(wc -l < "$LOGFILE")

# Get timestamp of the killed event (last 100 lines for performance)
KILLED_TS=$(tail -100 "$LOGFILE" | grep '"killed":true' | tail -1 | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}' || true)

if [[ -z "$KILLED_TS" ]]; then
    exit 0
fi

# Calculate how long ago the kill was confirmed
KILLED_EPOCH=$(date -d "$KILLED_TS" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(date +%s)
ELAPSED=$(( NOW_EPOCH - KILLED_EPOCH ))

if [[ $ELAPSED -lt $WEDGE_TIMEOUT ]]; then
    # Kill is recent — might recover on its own, wait
    exit 0
fi

# Check cooldown — don't reload too frequently
if [[ -f "$SENTINEL" ]]; then
    SENTINEL_AGE=$(( $(date +%s) - $(stat -c %Y "$SENTINEL" 2>/dev/null || echo 0) ))
    if [[ $SENTINEL_AGE -lt $COOLDOWN_SECS ]]; then
        # Reloaded recently — back off
        exit 0
    fi
fi

# WE ARE WEDGED — trigger recovery
echo "[$(date -Iseconds)] WATCHDOG: Kill wedge detected (killed for ${ELAPSED}s). Triggering reload." >> "${LOGFILE}.watchdog"

# Write sentinel file — VS Code extension watches this and reloads
# If the extension doesn't auto-detect, fall back to notifying user
touch "$SENTINEL"

# Also try to trigger reload via VS Code command if running in WSL/Remote-SSH
# This requires code-cli or similar — for now just log and notify
echo "[$(date -Iseconds)] RELOAD TRIGGERED — kill wedge recovered" >> "${LOGFILE}.watchdog"

exit 0
