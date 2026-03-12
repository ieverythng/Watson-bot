# Recipe 04 - OpenClaw Runtime Alignment
Date: 2026-03-12

## Purpose
Map WatsonOW repo policy into OpenClaw runtime behavior so the roles, tool boundaries, and OM loop behave the same way in live sessions.

Repo files alone are not enough.
OpenClaw must mirror the same control logic through agent prompts, model routing, tool permissions, and memory indexing.

## 1. Required Runtime Alignment

### WatsonOW-Main
Role:
- intake
- planning
- delegation
- lightweight retrieval
- user-facing communication

Runtime expectations:
- may read memory broadly enough to route work
- may write contracts and daily audit notes
- may not directly own durable memory writes
- must report tool failure explicitly
- should delegate execution-heavy work instead of improvising around missing tools

Recommended tools:
- read
- write
- limited exec
- no broad browser/web tools for small local models unless you have evidence they behave reliably

### WatsonOW-Dev
Role:
- repo execution
- file edits
- tests and validation

Runtime expectations:
- strong tool access
- narrow memory preload based on contract
- no durable memory writes

Recommended tools:
- read
- write
- exec
- git status/diff/add/commit when allowed by the current user instruction

### WatsonOW-Memory
Role:
- observer
- reflector
- memory hygiene

Runtime expectations:
- owns `OBSERVATIONS.md`, `REFLECTIONS.md`, `MEMORY.md`, and `bank/*`
- may use `scripts/om/observer-worker.sh`
- should not act as a general executor

Recommended tools:
- read
- write
- limited exec only for OM scripts or validation helpers

### WatsonOW-Review
Role:
- scope QA
- acceptance QA
- recipe QA
- memory hygiene QA

Runtime expectations:
- validates role boundaries
- checks claimed tool usage and outputs
- escalates hard technical review when needed

Recommended tools:
- read
- exec
- git diff/status
- write only for review artifacts or explicit audit outputs

## 2. Model Routing to Mirror in OpenClaw

Recommended mapping:
- `WatsonOW-Main`: local-cheap or local-reasoning
- `WatsonOW-Memory`: local-cheap or local-reasoning
- `WatsonOW-Review`: local-cheap by default, stronger model for difficult review
- `WatsonOW-Dev`: Codex-capable model for non-trivial edits and debugging

Rule:
- do not give `WatsonOW-Main` a larger execution surface than the model can reliably use
- if Qwen can route and write but not reliably execute tools, keep it in the routing lane and delegate execution

## 3. Tool-Reliability Policy

If a model is known to struggle with tool calls:
- reduce its tool surface
- keep commands simple
- require explicit blocker reporting
- route execution-heavy work to `WatsonOW-Dev`

Required runtime behavior:
- no silent failure
- no pretending a tool ran when it did not
- no empty completion after a blocked action

Preferred blocker format:

```text
BLOCKED
- Tool: <name>
- Failure: <exact message or reason>
- Impact: <what could not be completed>
- Next action: <fallback or delegate role needed>
```

## 4. Memory Indexing Alignment

Recommended memory search coverage:
- `MEMORY.md`
- `OBSERVATIONS.md`
- `REFLECTIONS.md`
- `bank/`
- `memory/`

Recommended retrieval behavior:
- deterministic file loading first
- semantic/index retrieval second

Avoid treating these as primary memory lanes:
- `reports/openclaw/` test transcripts
- large validation dumps
- one-off execution reports unless explicitly queried

Those should stay auditable, but they should not dominate routine retrieval.

## 5. Small-Model Safety

Based on existing OpenClaw validation artifacts in this repo, small local fallbacks should remain sandboxed and should not get broad web/browser capability by default.

Minimum runtime stance:
- sandbox on for small local models
- browser/web groups denied unless intentionally needed
- delegate external or fragile work to a better-suited agent/model

## 6. WatsonOW-Main Delegation Starter

Use this as a repo-side starter for live delegation:

```md
Delegation Contract

- Objective: <one concrete outcome>
- Reason for delegation: <why Main should delegate>
- Delegate role: WatsonOW-Dev | WatsonOW-Memory | WatsonOW-Review
- Delegation mode: single | parallel
- Model tier: local-cheap | local-reasoning | codex
- Scope: <exact task scope>
- Allowed folders: <narrow paths>
- Allowed tools: <exact tools>
- Forbidden actions: <clear negatives>
- Memory inputs required: <exact files or none>
- Memory outputs required: <daily audit only | promotion candidates | none>
- Promotion candidates: <optional>
- Audit obligation: <daily memory | observations | expenditure ledger>
- Deliverables: <files, reports, checks>
- Acceptance checks: <testable checks>
- Budget expectation: <expected spend/turns>
- Rollback plan: <how to undo>
- Escalation triggers: <when to stop and report>
- Audit destination: <where results are logged>
```

## 7. What to Change in OpenClaw

At minimum, reflect these repo assumptions in `openclaw.json` or equivalent runtime setup:
- distinct role prompts or agent profiles
- model routing by role
- tool permissions by role
- explicit blocker reporting for tool failure
- memory search paths aligned to the OM lanes above

If you share `openclaw.json`, the next pass should be a direct config audit against this recipe.
