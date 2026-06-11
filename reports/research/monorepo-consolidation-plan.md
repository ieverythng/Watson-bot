# Watson Monorepo Consolidation Plan

## Executive recommendation

Use the **existing `ieverythng/Watson-bot` repo as the canonical monorepo** and evolve the current local `WatsonOW` workspace (`/home/juanbeck/Watson`) into that monorepo root.

Do **not** create a second new `Watson-bot` repo.

Reason: the current Watson workspace is already wired to `https://github.com/ieverythng/Watson-bot.git`, already contains the control-plane material (agent policy, memory, reports, scripts, skills, docs), and already matches the intended role of the monorepo root. Creating another repo would add naming confusion and force an unnecessary history split.

---

## What I checked

### Publicly discoverable GitHub repos for `ieverythng`
Using GitHub's public repo API for `ieverythng`, I found these visible repos:

- `asr_vosk`
- `CLIProxyAPI`
- `codex-desktop-linux`
- `dialogue_manager`
- `iChess-Sim`
- `nao-ros4hri-bridge`
- `nao_chatbot_llm`
- `vLLM-server`
- `Watson-bot`

### Watson repo status
- A repo named **`Watson-bot` already exists**: `https://github.com/ieverythng/Watson-bot`
- Public search for `user:ieverythng Watson` returned **only `Watson-bot`**
- I did **not** find a separate public `Watson` repo under `ieverythng`
- I did **not** find a public `WatsonOW` repo under `ieverythng`

### Current local Watson workspace
The local workspace at `/home/juanbeck/Watson` is already a git repo with:

- remote: `origin = https://github.com/ieverythng/Watson-bot.git`
- current branch: `feat/Foundations_OM_Skills`

So operationally, **WatsonOW is already the working tree for `Watson-bot`**.

### `zerotier-llm-proxy` status
- Public GitHub repo search did **not** return `ieverythng/zerotier-llm-proxy`
- Direct unauthenticated web/API checks returned `404`
- However, `git ls-remote https://github.com/ieverythng/zerotier-llm-proxy.git` succeeded from this machine
- Local clone exists at `/home/juanbeck/zerotier-llm-proxy`

Interpretation: `zerotier-llm-proxy` **exists**, but is **not publicly discoverable** from unauthenticated GitHub web/API queries. It is likely private or otherwise not web-visible.

### `iTrack-Supply-Chain` status
- Public GitHub repo search did **not** return `ieverythng/iTrack-Supply-Chain`
- Direct unauthenticated web/API checks returned `404`
- However, `git ls-remote https://github.com/ieverythng/iTrack-Supply-Chain.git` succeeded from this machine
- Local repo exists at `/home/juanbeck/iTrack-Supply-Chain`

Interpretation: `iTrack-Supply-Chain` **exists**, but is **not publicly discoverable** from unauthenticated GitHub web/API queries. It is likely private or otherwise not web-visible.

---

## What each repo appears to be

### `Watson-bot` / current `WatsonOW` workspace
This is the **control-plane repo**:

- Hermes/OpenClaw/Watson operating harness
- agent policy files (`AGENTS.md`, `IDENTITY.md`, `TOOLS.md`, etc.)
- memory and reporting structure
- scripts and skills
- architecture/planning docs

It is the natural **root monorepo** candidate.

### `CLIProxyAPI`
This is a substantial standalone product/service:

- Go codebase
- OpenAI/Gemini/Claude/Codex/Grok-compatible proxy API
- its own release/build/docs surface
- useful to Watson, but not Watson-specific

This should be included in the monorepo as a **service/infrastructure dependency**, while preserving its ability to build independently.

### `zerotier-llm-proxy`
Current local state suggests this is still early/minimal and closely tied to Watson infrastructure planning.

This fits best as a **Watson infrastructure service** inside the monorepo.

### `iChess-Sim`
This is a separate end-user application:

- Python desktop app
- chess training/simulation product
- separate domain from Watson core

It can live in the monorepo if Juan wants one umbrella repo, but it should remain **clearly isolated as a product/app**, not mixed into Watson core.

### `iTrack-Supply-Chain`
This is also a substantial standalone application/product:

- multi-package app layout
- frontend + API + shared packages
- separate business/domain identity

Like `iChess-Sim`, it belongs in the monorepo only as an **independent app subtree**.

---

## Recommendation: repo strategy

## Option A — Recommended
### Make the current Watson workspace become the real `Watson-bot` monorepo

This is the best path.

Why:

1. **The repo already exists** on GitHub as `Watson-bot`
2. **The local WatsonOW workspace already points to it**
3. **The current contents are monorepo-root material**, not subproject material
4. It avoids creating yet another repo and another rename/migration cycle
5. It preserves the Watson operating history where it already lives

### What this means concretely
- Keep `/home/juanbeck/Watson` as the main repo root
- Treat `WatsonOW` as the **workspace/runtime name**, not the GitHub repo name
- Treat `Watson-bot` as the **canonical repository name**
- Move/add other projects under a structured `src/` subtree

---

## Option B — Not recommended
### Create a brand-new `Watson-bot` repo and move WatsonOW into it

I do **not** recommend this unless Juan specifically wants a clean-history reset.

Downsides:

- duplicates what already exists
- creates confusion between existing `Watson-bot` and new `Watson-bot`
- forces remote/history migration for the current Watson workspace
- adds overhead without solving a technical problem

This only makes sense if the goal is a deliberate archival break from the current Watson history.

---

## Proposed monorepo structure

Because Juan explicitly wants other projects as `/src` subdirectories, the cleanest structure is:

```text
Watson-bot/
├── README.md
├── AGENTS.md
├── IDENTITY.md
├── USER.md
├── TOOLS.md
├── HEARTBEAT.md
├── MEMORY.md
├── OBSERVATIONS.md
├── REFLECTIONS.md
├── SOUL.md
├── docs/
├── reports/
├── memory/
├── skills/
├── scripts/
├── bank/
├── infra/
│   ├── compose/
│   ├── env/
│   ├── systemd/
│   └── zerotier/
├── src/
│   ├── CLIProxyAPI/
│   ├── zerotier-llm-proxy/
│   ├── iChess-Sim/
│   └── iTrack-Supply-Chain/
└── tools/
```

### Why this structure works

- **repo root** remains the Watson orchestration/control plane
- **`src/`** holds imported application/service repos
- **`infra/`** holds Watson-level deployment glue across projects
- each imported project can still retain its own internal layout and build system

---

## Where each project should go

### 1. `WatsonOW` / `Watson-bot`
**Role:** monorepo root and control plane

Keep at repo root:

- agent policy files
- memory
- reports
- scripts
- skills
- Watson architecture and orchestration docs
- cross-project integration docs
- top-level infra wiring

Do **not** move Watson core into `src/WatsonOW/` unless you want Watson to become just another app. Right now it is the umbrella system, so it should stay at root.

### 2. `CLIProxyAPI`
**Place:** `src/CLIProxyAPI/`

Reason:
- standalone service with its own release lifecycle
- Watson depends on it, but it is not the monorepo root
- easiest to preserve upstream structure as-is

### 3. `zerotier-llm-proxy`
**Place:** `src/zerotier-llm-proxy/`

Reason:
- belongs to networking/inference access layer
- tightly related to Watson distributed deployment
- still should remain isolated as its own service subtree

### 4. `iChess-Sim`
**Place:** `src/iChess-Sim/`

Reason:
- clearly a separate product/app
- should not be mixed into Watson infrastructure directories
- easiest future extraction path if needed

### 5. `iTrack-Supply-Chain`
**Place:** `src/iTrack-Supply-Chain/`

Reason:
- larger standalone app/product
- should preserve its app/package workspace intact
- keep independent CI/build instructions within its subtree

---

## Recommended import method

Use **`git subtree` or `git filter-repo`-based history import**, not manual file copying.

### Best practical order
1. stabilize `Watson-bot` root structure first
2. create `src/`
3. import `zerotier-llm-proxy`
4. import `CLIProxyAPI`
5. import `iChess-Sim`
6. import `iTrack-Supply-Chain`

### Why subtree-style import is better
- preserves commit history
- keeps everything in one repo after migration
- avoids nested `.git` repos in the final state
- makes later blame/history archaeology possible

If Juan wants the source repos to continue living independently on GitHub for public distribution, then:
- keep them as standalone repos too, and
- mirror selected changes between standalone repos and monorepo

But if the goal is true consolidation, subtree import is the cleaner long-term answer.

---

## Suggested governance model after consolidation

### Root-level ownership
The root repo should own:

- Watson orchestration
- cross-project docs
- deployment wiring
- environment bootstrap
- shared automation scripts
- shared CI entrypoints

### Project-level ownership
Each imported project should own its own:

- app code
- package/dependency files
- project README
- tests
- local build scripts

### Cross-project rules
At the monorepo root, add:

- a top-level `README.md` explaining the ecosystem
- a `src/README.md` describing each imported project
- monorepo contribution rules
- root CI that can run targeted project jobs
- path-based automation so changes in `src/iChess-Sim` do not trigger all projects unnecessarily

---

## Specific recommendation on naming

### Keep these concepts separate
- **Watson-bot** = GitHub repository / monorepo name
- **WatsonOW** = local workspace/operational harness identity
- **CLIProxyAPI / iChess-Sim / iTrack-Supply-Chain / zerotier-llm-proxy** = subprojects inside the monorepo

This removes the current ambiguity where "Watson" sometimes means:
- the assistant runtime
- the workspace
- the repo
- the broader ecosystem

---

## Minimal migration plan

### Phase 1 — Normalize the root
- confirm `Watson-bot` is the canonical repo name
- add/update top-level `README.md`
- document monorepo intent clearly
- clean root so only Watson control-plane material stays there

### Phase 2 — Prepare structure
- create `src/`
- create `infra/`
- create root docs for contribution/build conventions

### Phase 3 — Import repos
- import `zerotier-llm-proxy` into `src/zerotier-llm-proxy/`
- import `CLIProxyAPI` into `src/CLIProxyAPI/`
- import `iChess-Sim` into `src/iChess-Sim/`
- import `iTrack-Supply-Chain` into `src/iTrack-Supply-Chain/`

### Phase 4 — Add integration glue
- top-level scripts for starting Watson dependencies
- root docs for local/dev/prod flows
- optional root task runner / makefile / justfile
- path-aware CI

### Phase 5 — Decide repo visibility strategy
For each imported project, decide whether it should remain:
- standalone + mirrored, or
- monorepo-only

---

## Bottom line

### Final answer to the main question
**Yes: WatsonOW should become the `Watson-bot` monorepo in practice, because it already is the working tree for that repo.**

Do **not** create a separate fresh `Watson-bot` repo unless Juan explicitly wants to abandon or archive current Watson history.

### Final placement recommendation
- current Watson workspace/control plane → **repo root**
- `CLIProxyAPI` → `src/CLIProxyAPI/`
- `zerotier-llm-proxy` → `src/zerotier-llm-proxy/`
- `iChess-Sim` → `src/iChess-Sim/`
- `iTrack-Supply-Chain` → `src/iTrack-Supply-Chain/`

### Public visibility finding
- `Watson-bot`, `CLIProxyAPI`, and `iChess-Sim` are publicly visible
- `zerotier-llm-proxy` and `iTrack-Supply-Chain` appear to exist but are **not publicly discoverable** from unauthenticated GitHub web/API queries

---

## Evidence summary

Key live checks performed:

- GitHub public user repo listing for `ieverythng`
- GitHub repository search queries for `Watson`, `Watson-bot`, `zerotier-llm-proxy`, `iTrack`
- direct URL checks against GitHub repo pages
- local git remotes for:
  - `/home/juanbeck/Watson`
  - `/home/juanbeck/CLIProxyAPI`
  - `/home/juanbeck/iChess-Sim`
  - `/home/juanbeck/iTrack-Supply-Chain`
  - `/home/juanbeck/zerotier-llm-proxy`
- authenticated network existence checks with `git ls-remote`
