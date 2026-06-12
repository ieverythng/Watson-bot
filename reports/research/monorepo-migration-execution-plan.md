# Monorepo Migration Execution Plan

_GPT-Oracle reviewed and approved. Ready for execution._

## Current State

- Watson workspace at `/home/juanbeck/Watson` is already the working tree for `ieverythng/Watson-bot`
- Branch: `feat/Foundations_OM_Skills`
- No `src/` directory exists yet
- 4 repos to import: zerotier-llm-proxy, CLIProxyAPI, iChess-Sim, iTrack-Supply-Chain

## Target Structure

```
Watson-bot/
├── AGENTS.md, IDENTITY.md, etc.    ← Watson control plane (root)
├── reports/, memory/, skills/, scripts/, bank/
├── src/
│   ├── zerotier-llm-proxy/
│   ├── CLIProxyAPI/
│   ├── iChess-Sim/
│   └── iTrack-Supply-Chain/
└── infra/                          ← deployment glue
```

## Import Commands (with --squash)

### 1. zerotier-llm-proxy
```bash
cd /home/juanbeck/Watson
git remote add -f zerotier-llm-proxy ../zerotier-llm-proxy
git subtree add --prefix=src/zerotier-llm-proxy zerotier-llm-proxy master --squash
```

### 2. CLIProxyAPI
```bash
git remote add -f cli-proxy-api ../CLIProxyAPI
git subtree add --prefix=src/CLIProxyAPI cli-proxy-api main --squash
```

### 3. iChess-Sim
```bash
git remote add -f icess-sim ../iChess-Sim
git subtree add --prefix=src/iChess-Sim iess-sim main --squash
```

### 4. iTrack-Supply-Chain
```bash
git remote add -f itrack ../iTrack-Supply-Chain
git subtree add --prefix=src/iTrack-Supply-Chain itrack feat/Gamma-insights-v0 --squash
```

## .gitignore Strategy

Root `.gitignore` covers global patterns:
```
node_modules/
dist/
__pycache__/
*.pyc
venv/
*.log
.DS_Store
Thumbs.db
```

Each subproject keeps its own `.gitignore` within `src/<repo>/`.

## Tagging Convention

- Imported repo tags: `<repo>-v<semver>` (e.g., `zerotier-v1.0.0`)
- Monorepo releases: `monorepo-<semver>` (e.g., `monorepo-1.0.0`)

## CI/CD Path Triggers (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    paths:
      - 'src/zerotier-llm-proxy/**'
      - 'src/CLIProxyAPI/**'
      - 'src/iChess-Sim/**'
      - 'src/iTrack-Supply-Chain/**'
```

## Oracle Recommendations (from GPT-5-5-Thinking)

1. **Use --squash** to avoid history bloat from importing full commit histories
2. **Watch for merge conflicts** when syncing upstream repos later via `git subtree pull`
3. **Path-based CI triggers** to avoid building all 5 projects on every commit
4. **Consider keeping truly independent apps (iChess-Sim, iTrack) in separate repos** if they don't share code with Watson — but consolidate if the goal is true monorepo

## Remaining Decisions

- [ ] Should iChess-Sim and iTrack stay as separate repos or join monorepo?
- [ ] Branch names for each repo (main vs master vs feat/*)?
- [ ] CI/CD pipeline per project or unified?
- [ ] Repo visibility strategy (public vs private) post-consolidation?
