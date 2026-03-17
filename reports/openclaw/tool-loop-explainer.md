# 🔄 Tool Loop / Automatic Retry Explainer

## What It Is

OpenClaw's subagent system includes built-in **automatic retry logic** with exponential backoff. This prevents silent failures and ensures tasks complete when possible.

## How It Works

1. **Attempt 1**: Task runs normally
2. **If failure occurs**: System automatically retries (usually 3-5 attempts depending on error type)
3. **Timeout enforcement**: Each subagent has a `runTimeoutSeconds` limit (currently 20 min for dev subagents, 60 min archive default)
4. **Error reporting**: You always see:
   - What failed
   - How many retries occurred
   - The final error message
   - Whether it succeeded on retry

## Where It Applies

- ✅ All `sessions_spawn` calls with `runtime: subagent`
- ✅ Agent roles (`dev`, `review`, `memory`)
- ✅ Cron job payloads
- ❌ **NOT** direct tool calls (like `read`, `write`, `message`) - those have no retry by design

## Configuration

Current settings in your config:

```json
"agents": {
  "defaults": {
    "subagents": {
      "runTimeoutSeconds": 1200,  // 20 minutes
      "archiveAfterMinutes": 60   // Archive old subagents after 60 min
    }
  }
}
```

## Dashboard Visibility

From the OpenClaw TUI dashboard you can:

1. **Monitor active subagents**: See running tasks with progress indicators
2. **Check completion status**: Green checkmarks for success, red X for failures
3. **View errors**: Click into failed tasks to see retry history and error logs
4. **Manual intervention**: Right-click to kill stalled tasks or send steer messages

## Why No Silent Failures?

The system is designed to be **transparent about failures**:
- Every tool call with a hard timeout reports immediately
- Retry attempts are logged
- Final results (success/failure) always surface to you
- Error context helps diagnose what went wrong

---

**TL;DR**: You're protected from silent failures. OpenClaw will retry tasks automatically and tell you exactly what happened!
