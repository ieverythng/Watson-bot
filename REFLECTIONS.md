# REFLECTIONS.md

Reflective summaries derived from observations and episodic logs.
This file is periodic and curated, not turn-by-turn.

## Reflection Format

- `id`: `R-YYYY-MM-DD-NN`
- `window`: date range covered
- `themes`: 2-5 high-level themes
- `durable_updates`: what should be promoted into `MEMORY.md` or `bank/*`
- `conflicts`: contradictions to resolve
- `actions`: concrete follow-up tasks
- `evidence`: source files and dates

## Entries

- `id`: R-2026-02-25-01
  - `window`: 2026-02-23 to 2026-02-25
  - `themes`:
    - Build OM memory architecture in staged, testable phases.
    - Keep markdown canonical and compression auditable.
  - `durable_updates`:
    - Earlier stage-first workflow note was later superseded by the 2026-03-11 auto-commit override.
  - `conflicts`:
    - None identified yet.
  - `actions`:
    - Implement bank scaffolding and retrieval/truncation policy docs.
  - `evidence`:
    - `memory/2026-02-24.md`
    - `reports/research/memory-architecture-review-2026-02-24.md`

- `id`: R-2026-03-09-01
  - `window`: 2026-03-09
  - `themes`:
    - WatsonOW bootstrap should proceed brick-by-brick with installation tasks first.
    - Keep Codex as primary installation model tier; defer local Qwen runtime switch until core system pieces are in place.
    - Enforce auditable operations via memory, observations, reflections, and recipe/skills artifacts.
  - `durable_updates`:
    - Canonical reflections file standardized as `REFLECTIONS.md`.
  - `conflicts`:
    - Historical notes still mention `REFFLECTIONS.md`, but the live repo now uses `REFLECTIONS.md` only.
  - `actions`:
    - Complete installation checklist artifacts under `reports/recipes/`, `reports/expenditure/`, and `skills/*`.
    - Keep a per-day expenditure ledger when installation blocks are executed.
  - `evidence`:
    - `reports/recipes/00-watsonow-operating-system.md`
    - active user instructions (2026-03-09)

- `id`: R-2026-03-10-01
  - `window`: 2026-03-10
  - `themes`:
    - WatsonOW should operate as a strict repo harness, not a general personal-assistant workspace.
    - Core skills need a shared authoring standard plus deterministic inputs, outputs, and failure handling.
    - Delegation can now plug into clearer roles, review gates, and budget-aware routing rules.
  - `durable_updates`:
    - Baseline git flow for this repo was defined as staged-first with typed commit subjects and short multiline bodies, then superseded operationally by Juan's 2026-03-11 auto-commit override.
    - Host-specific runtime facts should live in `TOOLS.md` or runtime reports, not in durable shared memory by default.
  - `conflicts`:
    - None identified in the current harness rewrite.
  - `actions`:
    - Test the updated skills and harness behavior on the main PC runtime.
    - Implement delegation contracts and role execution flow next, using the hardened `AGENTS.md` as the control layer.
  - `evidence`:
    - `AGENTS.md`
    - `HEARTBEAT.md`
    - `TOOLS.md`
    - `reports/recipes/00-watsonow-operating-system.md`
    - `reports/recipes/03-skills-authoring.md`
    - `skills/memory-observer/SKILL.md`
    - `skills/memory-reflector/SKILL.md`
    - `skills/expenditure-tracker/SKILL.md`

- `id`: R-2026-03-11-02
  - `window`: 2026-03-11
  - `themes`:
    - The new WatsonOW harness is stricter about repo boundaries, output routing, and role discipline.
    - Repo-wide defaults and active user overrides must both be represented clearly to avoid policy drift.
    - Auto-commit can be an active operating mode without deleting the staged-first baseline from the harness.
  - `durable_updates`:
    - Treat staged-first as the baseline repo policy, but honor Juan's active auto-commit override for Watson-made changes unless he requests staging-only.
  - `conflicts`:
    - Historical observations and earlier reflections still mention staged-first as the live workflow; they should now be read as prior state or baseline policy.
  - `actions`:
    - Keep `AGENTS.md` and `MEMORY.md` aligned whenever Juan changes operational mode.
    - Consider whether to create a dedicated live branch for continuous Watson commits.
  - `evidence`:
    - `AGENTS.md`
    - `MEMORY.md`
    - `memory/2026-03-11.md`
    - direct user instructions on 2026-03-11

- `id`: R-2026-03-12-01
  - `window`: 2026-03-12
  - `themes`:
    - OM only works reliably when retrieval order, write ownership, and promotion gates are explicit.
    - Qwen should read memory broadly enough to route work, but durable memory writes should stay with the memory role.
    - Review is valuable as recipe-ground-truth QA for both delegation and memory hygiene.
  - `durable_updates`:
    - `WatsonOW-Memory` owns durable memory writes by default.
    - Long transcripts and test dumps should live in reports, not active operational memory lanes.
  - `conflicts`:
    - Qwen tool reliability remains uneven; command guidance may help, but runtime/toolchain behavior still needs empirical testing.
  - `actions`:
    - Run fresh Qwen delegation tests against the hardened OM loop and contract fields.
    - Decide whether to add a dedicated memory-QA or review skill once the updated loop is exercised.
  - `evidence`:
    - `reports/recipes/01-om-loop.md`
    - `reports/recipes/02-delegation-contracts.md`
    - `AGENTS.md`
    - `TOOLS.md`
    - active user instructions on 2026-03-12
