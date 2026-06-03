# Delegation Contract — Subagent Infrastructure Test
Date: 2026-04-23
Scope: WatsonOW repository inspection

## Contract Fields

- **Objective:** Inspect WatsonOW repository structure and generate a comprehensive summary report of files, folders, and key configurations.

- **Reason for delegation:** Demonstrate subagent infrastructure deployment with full audit trail compliance per AGENTS.md and delegation contract recipe.

- **Delegate role:** WatsonOW-Dev

- **Delegation mode:** single

- **Model tier:** codex (gpt-5.4-mini via OpenAI)

- **Scope:** Read-only inspection of /home/juanbeck/Watson repository structure, key config files, and reports/recipes/ directory.

- **Allowed folders:** 
  - /home/juanbeck/Watson (read-only)
  - /home/juanbeck/Watson/reports/recipes/
  - /home/juanbeck/Watson/reports/expenditure/

- **Allowed tools:** read, terminal (for ls/tree commands), write (for report output only)

- **Forbidden actions:** 
  - No file edits to existing WatsonOW files
  - No commits
  - No credential changes
  - No edits outside allowed folders
  - No writes except to reports/reports/inspection/ subdirectory

- **Memory inputs required:** none (task is self-contained)

- **Memory outputs required:** daily audit line in memory/2026-04-23.md

- **Promotion candidates:** Any discovered repository patterns or conventions worth noting for future sessions.

- **Audit obligation:** 
  - Entry in OBSERVATIONS.md
  - Entry in memory/2026-04-23.md
  - Entry in reports/expenditure/ledger-2026-04-23.md

- **Deliverables:** 
  - Report file at /home/juanbeck/Watson/reports/research/subagent-test-report-2026-04-23.md
  - Summary of repository structure
  - List of key configuration files and their purposes
  - Token usage estimate

- **Acceptance checks:** 
  - Only the report file was created (no other edits)
  - Report includes complete folder tree
  - Report lists all .md policy files found
  - Audit entries exist in all three required locations
  - Expenditure ledger entry created with task details

- **Budget expectation:** One subagent task, ~10-15 turns, gpt-5.4-mini tier

- **Token cap:** 2000 tokens (warning-only for this test)

- **Cost-aware routing note:** Using gpt-5.4-mini (codex-tier but cost-effective) for structured report generation and file system analysis task that benefits from stronger reasoning than local model provides.

- **Exception handling:** None expected; if token cap at risk, stop and report.

- **Rollback plan:** Delete /home/juanbeck/Watson/reports/research/subagent-test-report-2026-04-23.md if needed.

- **Escalation triggers:** 
  - If more files need to be edited than expected
  - If required tools unavailable
  - If token usage exceeds 80% of cap before completion

- **Audit destination:** OBSERVATIONS.md, memory/2026-04-23.md, reports/expenditure/ledger-2026-04-23.md

---

## Execution Instructions for WatsonOW-Dev

1. Use `tree` or `find` commands to map repository structure
2. Read key policy files: AGENTS.md, IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md
3. List all files in reports/recipes/ directory
4. Generate comprehensive markdown report with findings
5. Create expenditure ledger entry for today
6. Write audit trail to memory/YYYY-MM-DD.md and OBSERVATIONS.md
7. Return summary to WatsonOW-Main
