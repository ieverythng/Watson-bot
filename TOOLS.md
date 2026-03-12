# TOOLS.md - Local Runtime Notes

This file stores host-specific notes that help WatsonOW operate on the current machine.

## What Belongs Here

- local paths and mount points
- SSH aliases and host labels
- local model names and runner commands
- device names
- browser or editor notes
- deployment host facts that are useful operationally

## What Does Not Belong Here

- repo policy
- delegation rules
- memory summaries
- API keys, secrets, or raw credentials

If a fact is host-specific, prefer `TOOLS.md` or a runtime validation report under `reports/openclaw/` instead of hardcoding it into durable memory files.

## Suggested Structure

```md
## Host
- OS:
- Shell:
- GPU:

## Local Models
- Orchestrator:
- Embeddings:
- Review:

## Paths
- Repo root:
- Scratch dir:

## Integrations
- SSH:
- Browser:
- Editor:
```

## Common Command Patterns

Use simple, repeatable commands first:
- file listing: `rg --files`
- text search: `rg -n "pattern" path`
- file preview: `sed -n '1,200p' file`
- repo status: `git status --short`
- repo delta: `git diff --stat`
- recent history: `git log --oneline -n 5`

## Tool Failure Rule

If a command or tool fails:
- report the exact failure
- say what it blocked
- try one clear fallback only if it stays in scope
- otherwise delegate or stop

Do not claim success after a failed tool call.
