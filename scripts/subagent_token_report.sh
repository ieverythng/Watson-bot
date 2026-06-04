#!/usr/bin/env bash
# Quick post-subagent token report — call after delegate_task
# Usage: ./subagent_token_report.sh [parent_session_id]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/subagent_token_report.py" "$@"
