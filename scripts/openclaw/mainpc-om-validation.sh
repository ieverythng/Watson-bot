#!/usr/bin/env bash
set -u -o pipefail

REPO_DIR="${REPO_DIR:-$PWD}"
cd "$REPO_DIR"

if [[ ! -d .git ]]; then
  echo "Run from repo root (Watson-bot)."
  exit 1
fi

mkdir -p reports/openclaw
TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPORT="reports/openclaw/mainpc-om-validation-${TS}.md"

HAS_FAILURE=0
HAS_BLOCKER=0

run() {
  local cmd="$*"
  local ec=0
  local had_errexit=0
  [[ $- == *e* ]] && had_errexit=1
  {
    echo ""
    echo "## \$ $cmd"
    echo '```'
    set +e
    bash -lc "$cmd"
    ec=$?
    [[ "$had_errexit" -eq 1 ]] && set -e
    echo '```'
    echo "exit_code: $ec"
  } >> "$REPORT" 2>&1
  return "$ec"
}

write_blocker() {
  local message="$1"
  {
    echo ""
    echo "## Blocker"
    echo "$message"
  } >> "$REPORT"
  HAS_BLOCKER=1
}

{
  echo "# Main PC OM Validation - ${TS}"
  echo ""
  echo "Repo: $(pwd)"
  echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "Commit: $(git rev-parse --short HEAD)"
  echo ""
  echo "## Host Snapshot"
  echo "- uname: $(uname -a)"
  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "- gpu: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n1)"
  else
    echo "- gpu: nvidia-smi not found"
  fi
  if command -v free >/dev/null 2>&1; then
    echo "- ram: $(free -h | awk '/Mem:/ {print $2}')"
  fi
  echo "- home: $HOME"
} > "$REPORT"

if ! command -v openclaw >/dev/null 2>&1; then
  write_blocker "`openclaw` not found on PATH. Install/fix PATH, then rerun."
  echo "Report: $REPORT"
  exit 2
fi

if ! run "openclaw --version"; then HAS_FAILURE=1; fi
if ! run "openclaw status"; then HAS_FAILURE=1; fi
if ! run "openclaw doctor"; then HAS_FAILURE=1; fi
if ! run "openclaw gateway status"; then HAS_FAILURE=1; fi
if ! run "openclaw memory status --deep"; then HAS_FAILURE=1; fi

MEM_STATUS="$(openclaw memory status 2>&1 || true)"
if echo "$MEM_STATUS" | grep -Eiq "not configured|provider.*none|no provider|missing|no api key found"; then
  write_blocker "Embedding provider appears unconfigured."
  {
    echo ""
    echo "### Next actions"
    echo "1. Configure an embedding provider in OpenClaw."
    echo "2. Re-run this script."
  } >> "$REPORT"
fi

if ! run "openclaw memory index --force --verbose"; then HAS_FAILURE=1; fi
if ! run "openclaw memory status --json"; then HAS_FAILURE=1; fi

MEM_HELP="$(openclaw memory --help 2>&1 || true)"
if echo "$MEM_HELP" | grep -Eq "\\bsearch\\b"; then
  if ! run "openclaw memory search --json --query \"Juan Bendek\""; then HAS_FAILURE=1; fi
  if ! run "openclaw memory search --json --query \"staged workflow\""; then HAS_FAILURE=1; fi
  if ! run "openclaw memory search --json --query \"Observational Memory\""; then HAS_FAILURE=1; fi
elif echo "$MEM_HELP" | grep -Eq "\\bquery\\b"; then
  if ! run "openclaw memory query \"Juan Bendek\""; then HAS_FAILURE=1; fi
  if ! run "openclaw memory query \"staged workflow\""; then HAS_FAILURE=1; fi
  if ! run "openclaw memory query \"Observational Memory\""; then HAS_FAILURE=1; fi
else
  {
    echo ""
    echo "## Manual Recall Check Needed"
    echo "Could not detect memory query subcommand from \`openclaw memory --help\`."
  } >> "$REPORT"
fi

if [[ -d "$HOME/.openclaw/credentials" ]]; then
  chmod 700 "$HOME/.openclaw/credentials" || true
fi

{
  echo ""
  echo "## Workspace Sanity"
  echo "- bank files:"
  ls -1 bank 2>/dev/null | sed 's/^/  - /'
  echo "- memory files:"
  ls -1 memory 2>/dev/null | sed 's/^/  - /'
} >> "$REPORT"

if [[ "$HAS_BLOCKER" -eq 1 ]]; then
  echo "OM validation completed with blockers. Report: $REPORT"
  exit 3
fi

if [[ "$HAS_FAILURE" -eq 1 ]]; then
  echo "OM validation completed with failures. Report: $REPORT"
  exit 1
fi

echo "OM validation complete. Report: $REPORT"
