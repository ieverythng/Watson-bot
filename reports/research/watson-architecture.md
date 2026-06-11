# WatsonOW / Watson-bot Architecture

## Purpose

This document describes the current WatsonOW architecture and the intended structure for consolidating it into the `Watson-bot` monorepo. It covers:

- the main Watson agent and its three Hermes profiles
- delegation and routing behavior
- the local and remote inference infrastructure
- end-to-end data flow between user, agents, providers, and model backends
- the provider chain for both local inference and ChatGPT-backed premium inference

This is written as a repository-level architecture reference for the Watson workspace.

---

## 1. System Summary

WatsonOW is a multi-agent Hermes-based system built around a **local-first primary assistant** with **premium delegated execution paths**.

At a high level:

- **Main Watson agent** runs on Hermes using `qwen36-turbo-hermes` via the `watson-llama` provider.
- **Delegation default** routes child/subagent work to `gpt-5.5` via `chatgpt-plus`.
- **Three named Hermes profiles** provide specialized operating modes:
  - `watson-dev` → `gpt-5.4-mini` via `openai-codex`
  - `watson-plus` → `gpt-5.5` via `chatgpt-plus`
  - `watson-codex` → `codex-auto-review` via `chatgpt-plus`
- **Local inference** is served by a Windows-hosted `llama.cpp` server exposed to WSL at `http://172.24.16.1:8080/v1`.
- **Premium ChatGPT inference** is exposed locally through **CLIProxyAPI** on `http://127.0.0.1:8317/v1`, which bridges Hermes calls to ChatGPT web/OAuth-backed access.
- **ZeroTier** is the private network layer intended to make the local LLM stack reachable across devices without exposing it publicly.

---

## 2. Architectural Principles

1. **Local-first orchestration**  
   The default Watson runtime should stay cheap, fast, and continuously available through the local LLM.

2. **Premium reasoning on demand**  
   Heavy reasoning, code review, and specialized work can be delegated to stronger hosted models.

3. **OpenAI-compatible interfaces everywhere possible**  
   Hermes, `llama.cpp`, CLIProxyAPI, and the ZeroTier proxy layer are all aligned around `/v1`-style HTTP APIs.

4. **Separation of concerns**  
   - Hermes handles orchestration, tools, memory, and delegation.
   - `llama.cpp` handles local token generation.
   - CLIProxyAPI handles ChatGPT session mediation.
   - ZeroTier handles private network reachability.

5. **Monorepo consolidation with infra adjacency**  
   `Watson-bot` should become the control plane repo, with related projects vendored, linked, or placed under `src/` where appropriate.

---

## 3. Current Runtime Components

## 3.1 Main Hermes agent

Authoritative root Hermes config: `~/.hermes/config.yaml`

Validated core settings (verified 2026-06-11):

- default model: `qwen36-turbo-hermes`
- default provider: `watson-llama`
- provider endpoint: `http://172.24.16.1:8080/v1`
- delegation model: `gpt-5.5`
- delegation provider: `chatgpt-plus`
- custom provider `chatgpt-plus`: `http://127.0.0.1:8317/v1`

Interpretation:

- the **main Watson session** runs locally against the Windows-hosted LLM server
- when Watson decides a task should be delegated, Hermes spawns child work using the `chatgpt-plus` provider by default

## 3.2 Specialized Hermes profiles

Profiles exist under `~/.hermes/profiles/`:

- `watson-dev`
- `watson-plus`
- `watson-codex`

**Status update (2026-06-11):** Profile configs have been cleaned — the line-number prefix issue has been resolved. All three profiles now contain valid YAML with clean config files.

### watson-dev

- default model: `gpt-5.4-mini`
- provider: `openai-codex` (Hermes built-in Codex OAuth)
- role: coding, implementation, debugging, tool-heavy execution
- gateway status: **stopped** (profile exists but not running as separate gateway instance)

### watson-plus

- default model: `gpt-5.5`
- provider: `chatgpt-plus` (via CLIProxyAPI on port 8317)
- role: premium reasoning, deeper synthesis, strategic planning
- gateway status: **stopped** (profile exists but not running as separate gateway instance)

### watson-codex

- default model: `codex-auto-review`
- provider: `chatgpt-plus` (via CLIProxyAPI on port 8317)
- role: automated review, critique, and code-audit style passes
- gateway status: **stopped** (profile exists but not running as separate gateway instance)

**Note on profiles:** Profiles are configuration templates — they define model/provider pairs for specialized sessions. They are not independently running services. To use a profile, launch `hermes chat --profile watson-plus` or delegate with the profile specified. The "stopped" status in `hermes profile list` means no separate gateway instance is bound to that profile; it runs on-demand when invoked.

---

## 4. Complete Agent Architecture

```text
                                      +----------------------+
                                      |        User          |
                                      | Discord / CLI / App  |
                                      +----------+-----------+
                                                 |
                                                 v
                                 +---------------+----------------+
                                 |      Watson Main Agent         |
                                 | Hermes primary session         |
                                 | model: qwen36-turbo-hermes     |
                                 | provider: watson-llama         |
                                 +---------------+----------------+
                                                 |
                            +--------------------+--------------------+
                            |                                         |
                            | local-first response path               | delegated path
                            v                                         v
              +-------------+-------------+           +---------------+----------------+
              | Local provider route      |           | Hermes delegation router       |
              | watson-llama              |           | default child model: gpt-5.5   |
              | 172.24.16.1:8080/v1       |           | default provider: chatgpt-plus |
              +-------------+-------------+           +---------------+----------------+
                            |                                         |
                            v                                         v
                 +----------+-----------+               +-------------+-----------------------------+
                 | Windows llama.cpp    |               | Specialized profiles / delegated modes   |
                 | qwen36-turbo-hermes  |               |                                         |
                 +----------------------+               | 1. watson-dev                            |
                                                        |    gpt-5.4-mini via openai-codex        |
                                                        |                                         |
                                                        | 2. watson-plus                           |
                                                        |    gpt-5.5 via chatgpt-plus             |
                                                        |                                         |
                                                        | 3. watson-codex                          |
                                                        |    codex-auto-review via chatgpt-plus   |
                                                        +-------------------+---------------------+
                                                                            |
                                                                            v
                                                           +----------------+----------------+
                                                           | Provider backends / tool paths  |
                                                           | local LLM or ChatGPT web        |
                                                           +---------------------------------+
```

### 4.1 Main agent responsibilities

The main agent is the user-facing orchestrator. Its responsibilities are:

- receive user requests
- decide whether a task can be answered locally
- decide whether premium delegation is required
- invoke tools
- manage memory and workspace context
- aggregate delegated outputs into a final answer or artifact

### 4.2 Delegation routing model

Delegation should be understood in two layers:

1. **Default delegation policy in root Hermes config**  
   Hermes child tasks route to:
   - model: `gpt-5.5`
   - provider: `chatgpt-plus`

2. **Profile-specific operating modes**  
   When Watson is intentionally run through a named profile, it adopts that profile's model/provider pair.

### 4.3 Practical routing intent

A sensible routing interpretation for WatsonOW is:

- **Main chat / general orchestration** → local `qwen36-turbo-hermes`
- **Complex reasoning / long-form synthesis** → `watson-plus`
- **Implementation / code execution / repo changes** → `watson-dev`
- **Review / audit / critique / PR-style feedback** → `watson-codex`

---

## 5. Infrastructure Layer

## 5.1 Local LLM server

The local provider `watson-llama` points to:

- `http://172.24.16.1:8080/v1`

This is a Windows-hosted `llama.cpp` server exposed to WSL. Supporting evidence in local scripts shows:

- model served from Windows
- host binding `0.0.0.0`
- port `8080`
- OpenAI-compatible `/v1` path expected by Hermes

Representative runtime path:

```text
Hermes in WSL
  -> http://172.24.16.1:8080/v1
  -> Windows llama-server.exe
  -> local GGUF model
  -> response returned to Hermes
```

This is the primary, low-cost inference plane for Watson.

## 5.2 CLIProxyAPI

CLIProxyAPI lives at:

- repo: `/home/juanbeck/CLIProxyAPI` (forked from upstream, public at `ieverythng/CLIProxyAPI`)
- bind host: `127.0.0.1`
- port: `8317`
- API key for Hermes: `watson-chatgpt-key`
- auth directory: `~/.cli-proxy-api`

**Status (verified 2026-06-11):** Service is **RUNNING**. PID 3319, health check returns `{"status":"ok"}`. Six models available via `/v1/models`:

| Model ID | Role |
|---|---|
| `codex-auto-review` | Code review (watson-codex profile) |
| `gpt-image-2` | Image generation |
| `gpt-5.3-codex-spark` | Codex lightweight |
| `gpt-5.4` | General purpose / vision auxiliary |
| `gpt-5.4-mini` | Lightweight (watson-dev profile) |
| `gpt-5.5` | Premium reasoning (default delegation, watson-plus profile) |

Its role in the system is to expose an OpenAI-compatible local endpoint that Hermes can call while the proxy itself uses OAuth-backed ChatGPT/Codex access behind the scenes.

In WatsonOW, this is the bridge that turns **ChatGPT web/subscription access** into a **local API endpoint** usable by Hermes.

## 5.3 ZeroTier network

ZeroTier is the private networking layer for remote/local-hybrid inference.

Observed/related config and docs show:

- private mesh networking is part of the intended architecture
- a referenced ZeroTier network ID exists: `3b19b3a716937e29`
- the ZeroTier LLM proxy concept is based on a LiteLLM + `llama.cpp` front door that can be reached from other devices over the mesh

Its purpose is:

- avoid exposing local inference publicly
- make the local model reachable across machines
- support Watson clients or related tools running outside the host machine

## 5.4 ZeroTier LLM proxy role

The referenced `zerotier-llm-proxy` component should be understood as an optional network-facing wrapper around local inference.

Conceptually:

- `llama.cpp` remains the generator
- LiteLLM or another OpenAI-compatible proxy normalizes the upstream interface
- ZeroTier provides secure/private transport between nodes

This is complementary to the direct local `watson-llama` path. It matters most when Watson consumers are not on the same host or same localhost boundary.

---

## 6. Infrastructure Topology

```text
                         WatsonOW Infrastructure Topology

   WSL / Hermes side                                      Windows / external side
   ------------------                                     -----------------------

   +------------------------------+
   | Hermes Agent Runtime         |
   | ~/.hermes/config.yaml        |
   | main model: watson-llama     |
   | delegation: chatgpt-plus     |
   +---------------+--------------+
                   |                                +------------------------------+
                   | local network to host          | Windows llama.cpp server     |
                   +------------------------------->| 0.0.0.0:8080                |
                   |                                | model: qwen36-turbo-hermes   |
                   |                                +--------------+---------------+
                   |                                               |
                   |                                               v
                   |                                +------------------------------+
                   |                                | Local GGUF model / GPU        |
                   |                                +------------------------------+
                   |
                   | localhost
                   v
   +------------------------------+
   | CLIProxyAPI                  |
   | 127.0.0.1:8317/v1            |
   | OpenAI-compatible proxy      |
   +---------------+--------------+
                   |
                   | OAuth-backed web/session bridge
                   v
   +------------------------------+
   | ChatGPT web / Codex backend  |
   | premium hosted inference     |
   +------------------------------+

                   Optional remote reachability layer
                   ----------------------------------

   +------------------------------+        ZeroTier mesh        +------------------------------+
   | Remote Watson client         | <-------------------------> | ZeroTier LLM Proxy / Gateway |
   | laptop / service / tool      |                             | LiteLLM + local inference     |
   +------------------------------+                             +------------------------------+
```

---

## 7. Provider Chain

## 7.1 Local provider chain

The local provider path is:

```text
watson-llama -> local llama.cpp OpenAI-compatible server -> qwen36-turbo-hermes
```

Expanded:

```text
Hermes request
  -> provider name: watson-llama
  -> base URL: http://172.24.16.1:8080/v1
  -> llama-server.exe on Windows host
  -> local GGUF model execution
  -> response back to Hermes
```

This is the default chain for the main agent.

## 7.2 Premium provider chain

The premium provider path is:

```text
chatgpt-plus -> CLIProxyAPI -> ChatGPT web / Codex OAuth session
```

Expanded:

```text
Hermes request
  -> provider name: chatgpt-plus
  -> base URL: http://127.0.0.1:8317/v1
  -> CLIProxyAPI validates local API key
  -> CLIProxyAPI maps requested model alias
  -> CLIProxyAPI uses stored OAuth-backed ChatGPT/Codex session
  -> ChatGPT web/backend performs inference
  -> response returns through CLIProxyAPI to Hermes
```

This is the default chain for delegated premium work and for the `watson-plus` / `watson-codex` profiles.

## 7.3 OpenAI-Codex path

A separate direct path also exists for `watson-dev`:

```text
openai-codex -> OpenAI/Codex authenticated backend
```

In WatsonOW terms, this is the development-oriented execution lane.

---

## 8. End-to-End Data Flows

## 8.1 Standard local request flow

```text
User
  -> Watson main agent
  -> Hermes tool/memory/context assembly
  -> watson-llama provider
  -> local llama.cpp server
  -> generated response
  -> Watson main agent finalizes answer
  -> User
```

Use this path when:

- the task is straightforward
- low latency matters
- privacy/locality is preferred
- premium delegation is not necessary

## 8.2 Delegated premium reasoning flow

```text
User
  -> Watson main agent
  -> task judged too complex or high-value for local model alone
  -> Hermes delegation
  -> chatgpt-plus provider
  -> CLIProxyAPI
  -> ChatGPT web backend
  -> delegated result returned
  -> Watson main agent synthesizes final output
  -> User
```

Use this path when:

- stronger reasoning is needed
- long-form planning or synthesis is needed
- review/critique quality matters more than local cost

## 8.3 Profile-driven execution flow

```text
User / automation
  -> explicit Watson profile selection
  -> Hermes loads selected profile defaults
  -> provider/model determined by profile
  -> backend inference path executes
  -> output returned directly or via parent Watson session
```

This matters when a workflow wants a stable specialist identity rather than ad hoc delegation.

## 8.4 Remote inference over ZeroTier

```text
Remote client
  -> ZeroTier private IP
  -> ZeroTier LLM proxy / gateway
  -> local inference server (llama.cpp or compatible backend)
  -> result returns over ZeroTier mesh
```

This is the path that turns the private Watson inference stack into a multi-device service.

---

## 9. Data Ownership and Boundaries

## 9.1 Hermes layer

Hermes owns:

- conversation state
- tool execution
- delegation spawning
- profile selection
- memory and workspace orchestration
- final answer composition

## 9.2 Local inference layer

`llama.cpp` owns:

- model loading
- token generation
- context-window execution
- GPU/CPU inference runtime

## 9.3 ChatGPT proxy layer

CLIProxyAPI owns:

- translating local API calls into provider-specific web/session calls
- model alias mapping
- OAuth/session reuse
- local API key gatekeeping for callers like Hermes

## 9.4 Network layer

ZeroTier owns:

- private connectivity between machines
- non-public exposure of the inference plane
- stable remote addressing for distributed Watson access

---

## 10. Monorepo Consolidation Target

The desired future state is for **Watson-bot** to become the monorepo control plane, with WatsonOW as the main workspace and related projects colocated as subdirectories or linked repositories.

Relevant projects:

- main workspace: `/home/juanbeck/Watson`
- CLI proxy service: `/home/juanbeck/CLIProxyAPI`
- ZeroTier LLM proxy: `https://github.com/ieverythng/zerotier-llm-proxy`
- chess simulation project: `/home/juanbeck/iChess-Sim`
- supply chain project: `/home/juanbeck/iTrack-Supply-Chain`

A practical target layout would be:

```text
Watson-bot/
├── README.md
├── docs/
│   └── architecture/
├── reports/
├── infra/
│   ├── hermes/
│   ├── cliproxyapi/
│   ├── zerotier-llm-proxy/
│   └── local-llm/
├── src/
│   ├── watson-core/              # current WatsonOW workspace logic
│   ├── cliproxyapi/              # vendored or linked service
│   ├── zerotier-llm-proxy/       # vendored or linked network proxy
│   ├── iChess-Sim/
│   └── iTrack-Supply-Chain/
└── scripts/
```

Recommended consolidation rule:

- keep Watson orchestration/docs as the root concern
- treat infrastructure services as first-class subprojects
- keep external services loosely coupled through config and scripts, not hardcoded path assumptions

---

## 11. Recommended Mental Model

The simplest correct mental model for WatsonOW is:

```text
Watson = Hermes orchestration brain
       + local llama.cpp everyday inference
       + ChatGPT-backed premium delegation
       + ZeroTier private network reachability
```

Or, in one sentence:

> WatsonOW is a Hermes-orchestrated multi-profile assistant whose default brain is local, whose premium reasoning rides through CLIProxyAPI to ChatGPT, and whose distributed reach is enabled by ZeroTier.

---

## 12. Key Configuration Facts

### Root Hermes config

- path: `~/.hermes/config.yaml`
- valid YAML: yes
- default model: `qwen36-turbo-hermes`
- default provider: `watson-llama`
- delegation model: `gpt-5.5`
- delegation provider: `chatgpt-plus`
- custom provider URL for `chatgpt-plus`: `http://127.0.0.1:8317/v1`

### Hermes profiles

- path root: `~/.hermes/profiles/`
- profiles present: `watson-dev`, `watson-plus`, `watson-codex`
- issue: profile configs are malformed due to embedded line-number prefixes

### CLIProxyAPI

- repo: `/home/juanbeck/CLIProxyAPI`
- host: `127.0.0.1`
- port: `8317`
- auth dir: `~/.cli-proxy-api`
- local API key: `watson-chatgpt-key`

### Local LLM server

- provider name: `watson-llama`
- endpoint: `http://172.24.16.1:8080/v1`
- implementation: Windows `llama.cpp` server exposed to WSL

### ZeroTier

- related network ID seen in local docs/config: `3b19b3a716937e29`
- role: private connectivity for remote access to inference services

---

## 13. Risks and Current Gaps

1. **Profile configs cleaned** ~~(RESOLVED 2026-06-11)~~  
   The `watson-dev`, `watson-plus`, and `watson-codex` profile YAML files have been regenerated with clean, valid YAML. No more line-number prefixes.

2. **Split-source architecture**  
   Watson currently spans multiple adjacent repos and service directories rather than a single monorepo root. The monorepo consolidation plan exists but has not been executed yet.

3. **Provider dependency asymmetry**  
   Local inference is self-hosted, but premium inference depends on a working CLIProxyAPI auth/session chain. CLIProxyAPI is currently running (PID 3319) but lacks persistent service management (systemd/s6 supervision).

4. **Network topology drift risk**  
   ZeroTier, direct localhost access, WSL host bridging, and optional proxy layers can diverge unless documented and scripted consistently.

5. **CLIProxyAPI upstream repo down**  
   The original `g13y/CLIProxyAPI` returns 404. Watson uses the fork at `ieverythng/CLIProxyAPI`. No releases available — only the pre-built binary in the repo works.

---

## 14. Bottom Line

WatsonOW is a **hybrid local + premium agent architecture**:

- **primary orchestrator:** Hermes main agent
- **default runtime brain:** `qwen36-turbo-hermes` via `watson-llama`
- **default delegated premium brain:** `gpt-5.5` via `chatgpt-plus`
- **specialist profiles:** `watson-dev`, `watson-plus`, `watson-codex`
- **local model transport:** Windows-hosted `llama.cpp` on `172.24.16.1:8080`
- **premium provider transport:** CLIProxyAPI on `127.0.0.1:8317`
- **distributed private networking:** ZeroTier and the planned ZeroTier LLM proxy layer

That combination gives Watson a practical operating model:

- cheap local default behavior
- stronger premium delegation when needed
- a path to cross-device/private network deployment
- a clean basis for consolidation into a `Watson-bot` monorepo
