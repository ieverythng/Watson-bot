# Delegation Contracts — WatsonOW Recipe
Date: 2026-03-11
Scope: repository root

## Purpose
Use delegation contracts so any non-trivial delegated task is:
- scoped
- auditable
- reversible
- reviewable
- budget-aware

A delegation contract is required whenever a task changes code, configuration, file layout, runtime behavior, or model behavior.

---

## 1. Roles

### WatsonOW-Main
- planner
- task decomposer
- contract author
- final decision-maker

### WatsonOW-Dev
- executor
- may edit files and run commands only within contract scope

### WatsonOW-Review
- verifies scope compliance
- verifies deliverables and acceptance checks
- escalates hard technical review when needed

### WatsonOW-Memory
- records the delegation event in OBSERVATIONS.md
- updates REFLECTIONS.md or MEMORY.md only when appropriate

---

## 2. When a delegation contract is required
Create a contract before delegating if any of the following is true:
- more than one file may change
- code/config/runtime behavior will change
- commands/tests/builds will run
- the task may consume meaningful model budget
- the task may need rollback
- the task is not trivially reversible

No contract is needed for:
- simple read-only inspection
- tiny formatting edits explicitly requested by the user
- adding one observation/reflection entry
- other minimal, non-destructive, single-step tasks

---

## 3. Delegation Contract Template
Every delegated task must contain:

- Objective:
- Reason for delegation:
- Delegate role:
- Delegation mode:
- Model tier:
- Scope:
- Allowed folders:
- Allowed tools:
- Forbidden actions:
- Memory inputs required:
- Memory outputs required:
- Promotion candidates:
- Audit obligation:
- Deliverables:
- Acceptance checks:
- Budget expectation:
- Rollback plan:
- Escalation triggers:
- Audit destination:

---

## 4. Contract field rules

### Objective
One sentence, concrete, outcome-based.

### Reason for delegation
Why this should be delegated now:
- speed
- specialization
- lower cost
- stronger coding ability
- isolation of review/execution

### Delegate role
One of:
- WatsonOW-Dev
- WatsonOW-Review
- WatsonOW-Memory

### Delegation mode
Choose one:
- single
- parallel

Rule:
- default to `single`
- use `parallel` only when tasks are clearly independent
- if `parallel`, assign one merge owner and avoid shared file ownership

### Model tier
Choose explicitly:
- local-cheap
- local-reasoning
- codex

Rule:
- default cheap/local first
- Codex for repo surgery, debugging, non-trivial code edits, or difficult technical review

### Scope
State exactly what part of the repo or system is in scope.

### Allowed folders
Default:
- current repository workspace only

Prefer narrower paths whenever possible.

### Allowed tools
Pick only what is needed:
- read
- write
- exec
- git status / diff / add if explicitly allowed

If a required tool is missing or fails:
- report the exact failure
- do not silently continue
- either use one explicit fallback or escalate

### Forbidden actions
Always list explicit negatives, such as:
- no commits
- no branch deletion
- no credential changes
- no repo-root loose files
- no edits outside allowed folders

### Memory inputs required
State the exact memory lanes or files the delegate is allowed to read.

Examples:
- `none`
- `memory/2026-03-12.md only`
- `MEMORY.md + current contract only`

### Memory outputs required
State the exact memory outputs expected from the delegate.

Examples:
- `daily audit line only`
- `promotion candidates returned to WatsonOW-Memory`
- `none`

### Promotion candidates
List any facts the delegate thinks may deserve observation, reflection, or durable promotion.
These are suggestions, not durable writes.

### Audit obligation
State the minimum audit artifacts required.

Examples:
- `memory/YYYY-MM-DD.md`
- `reports/openclaw/<report>.md + daily memory`
- `daily memory + expenditure ledger`

### Deliverables
Concrete outputs only:
- files created/edited
- reports produced
- tests run
- summaries returned

### Acceptance checks
Must be testable.
Examples:
- “Only the listed files changed.”
- “All three skills follow the same structure and include examples.”
- “OM files were updated with an audit entry.”

### Budget expectation
Required when model choice matters.
Record:
- expected model
- expected turns
- whether Codex is justified

### Rollback plan
Always specify:
- git restore paths
- revert file list
- restore old config values

### Escalation triggers
Delegate must stop and ask Juan if:
- scope expands unexpectedly
- credentials or secrets are touched
- model config changes affect unrelated providers
- more than N files change unexpectedly
- tests fail in a way not directly tied to the task
- a required tool is unavailable and no approved fallback exists

### Audit destination
At minimum:
- add one OBSERVATIONS entry
Optionally:
- append to memory/YYYY-MM-DD.md
- update expenditure ledger if Codex or multiple turns were used

---

## 5. Execution flow

### Step 1 — Draft
WatsonOW-Main writes the contract before execution.

### Step 2 — Sanity-check
Review the contract for:
- clear scope
- enough acceptance checks
- rollback present
- budget logic present

### Step 3 — Execute
Delegate performs only the work defined in the contract.
If tools fail, the delegate must report the blocker and stop or fall back explicitly.

### Step 4 — Review
WatsonOW-Review checks:
- deliverables complete
- no scope drift
- acceptance checks passed
- no forbidden actions occurred
- memory ownership was respected
- claimed tool usage actually happened

### Step 5 — Audit
WatsonOW-Memory records:
- what was delegated
- why
- outcome
- next step
- whether any promotion candidates were accepted or rejected

---

## 6. Review policy

### Use local/Qwen review for:
- scope compliance
- process compliance
- folder discipline
- output completeness
- audit trail completeness

### Use Codex review for:
- non-trivial code correctness
- refactors
- subtle bug fixes
- framework-specific technical validation

---

## 7. Spawn policy
Default:
- one delegate

Allowed without explicit user approval:
- maximum two concurrent delegates if tasks are clearly independent

Do not spawn swarms by default.

Stop delegation if:
- outputs conflict
- budget grows too quickly
- acceptance criteria are weak
- uncertainty rises materially

If multiple Dev delegates are used:
- each delegate gets its own contract
- each delegate owns a disjoint file set
- one role is assigned as merge owner
- Review must check cross-contract consistency before completion

---

## 8. Minimal contract example

- Objective: Harden AGENTS.md, TOOLS.md, and HEARTBEAT.md to enforce workspace boundaries and audit discipline.
- Reason for delegation: Non-trivial repo editing with policy consequences.
- Delegate role: WatsonOW-Dev
- Delegation mode: single
- Model tier: codex
- Scope: AGENTS.md, TOOLS.md, HEARTBEAT.md
- Allowed folders: current repository workspace
- Allowed tools: read, write, exec, git status, git diff
- Forbidden actions: no commits, no edits outside listed files, no credential changes
- Memory inputs required: memory/2026-03-11.md only if needed for active policy context
- Memory outputs required: daily audit line only
- Promotion candidates: any workflow rule that should be reviewed by WatsonOW-Memory
- Audit obligation: OBSERVATIONS.md and memory/YYYY-MM-DD.md
- Deliverables: edited policy files and concise change summary
- Acceptance checks: only listed files changed; policy covers output locations, audit trail, model routing, spawn policy
- Budget expectation: one Codex task, no more than one follow-up revision
- Rollback plan: git restore AGENTS.md TOOLS.md HEARTBEAT.md
- Escalation triggers: if more files need edits or current policy files are inconsistent
- Audit destination: OBSERVATIONS.md and memory/YYYY-MM-DD.md

---

## 9. Rule of thumb
If a delegated task would be annoying to review after the fact, the contract is too weak.
If a delegate could technically complete the task while still surprising you, the contract is too weak.
