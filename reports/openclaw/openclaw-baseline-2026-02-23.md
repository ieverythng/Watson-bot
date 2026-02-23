# OpenClaw Baseline Test Sweep — 2026-02-23

## Scope
Quick baseline validation of a fresh OpenClaw implementation: CLI, gateway, health/security, memory indexing/search, channels, docs, skills, logs, and local runtime.

## Mindmap (works vs gaps)

- OpenClaw implementation
  - Core runtime
    - ✅ CLI installed and callable (`openclaw --version` => `2026.2.22-2`)
    - ✅ Node/npm present (`node v22.22.0`, `npm 10.9.4`)
    - ✅ Gateway running and reachable (`openclaw gateway status`, `openclaw gateway health`)
    - ✅ Service managed by systemd (enabled/running)
  - Control/observability
    - ✅ `openclaw status` returns complete system snapshot
    - ✅ `openclaw doctor` executes and reports actionable checks
    - ✅ Log access works (`openclaw logs --limit 40 --plain`)
    - ⚠️ `openclaw logs --lines` fails (invalid flag; use `--limit`)
  - Security posture
    - ⚠️ 1 critical + 2 warnings in `openclaw security audit`
      - CRITICAL: small-model fallback configured without enforced sandbox mode
      - WARN: credentials dir permissions too open (`~/.openclaw/credentials` = 755)
      - WARN: trusted proxies unset (relevant only if reverse-proxy exposure is added)
    - ℹ️ browser control and elevated tools enabled (increased attack surface; maybe acceptable for trusted local use)
  - Skills/tooling
    - ✅ Skills system works (`openclaw skills list`)
    - ✅ 4 skills ready (healthcheck, skill-creator, tmux, weather)
    - ⚠️ 47 bundled skills missing deps (normal on fresh setup)
  - Docs/help surface
    - ✅ `openclaw help` and `openclaw gateway --help` available
    - ✅ `openclaw docs "gateway"` search works
    - ✅ Local docs tree exists and is populated
  - Channels/messaging
    - ✅ Channel subsystem reachable (`openclaw channels status`)
    - ⚠️ No channels configured yet (expected; Discord/others pending)
  - Sessions
    - ✅ Session store healthy (`openclaw sessions` lists active main session)
  - Memory subsystem
    - ✅ Index command runs (`openclaw memory index`)
    - ⚠️ Semantic memory provider not configured (`openclaw doctor` warning)
    - ⚠️ Current index shows `0 chunks` and searches return no matches

## Pass/Fail summary
- Passed: 12
- Partial/Needs config: 8
- Hard failures: 0 (excluding intentional invalid-flag test)

## Recommended next fixes (priority order)
1. **Fix credentials permissions (fast security win)**
   - `chmod 700 ~/.openclaw/credentials`
2. **Decide sandbox policy for fallback small models**
   - Prefer: `agents.defaults.sandbox.mode="all"`
   - Keep web tools denied for small fallbacks
3. **Enable memory embeddings provider** (for actual semantic recall)
   - Configure OpenAI/Gemini/Voyage/Mistral key or local embedding provider
4. **Configure channels**
   - Start with Discord (as planned), then optional WhatsApp/Telegram
5. **Install only skills actually needed for your workflow**
   - Avoid installing all 47 blindly
6. **(If exposing behind reverse proxy later)** configure `gateway.trustedProxies`

## Notes
- Gateway is loopback-only right now (`127.0.0.1`), which is good default isolation.
- Security warnings are mostly configuration posture items, not runtime crashes.
