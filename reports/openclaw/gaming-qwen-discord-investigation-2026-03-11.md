# Gaming, Qwen, and Discord Investigation

Date: 2026-03-11
Host: ULTIMATE-MACHINE / WSL2 side inspection + Windows host probes

## 1. Why the earlier run aborted

The earlier performance scan did **not** crash OpenClaw.
It failed because I launched broad filesystem scans across large Windows directories from WSL:
- `C:\Users\Admin`
- Steam library paths

One command timed out, another was SIGTERM-aborted, and OpenClaw inserted a transcript repair note because parallel tool history became inconsistent after the timeout.

Meaning:
- no data loss
- no broken runtime
- just an overly broad disk scan

## 2. Gaming bottleneck investigation

## Hardware / runtime facts confirmed
- CPU: AMD Ryzen 5 5500 (6 cores / 12 threads)
- RAM: 16 GB total
- GPU: NVIDIA GeForce RTX 5070 Ti 16 GB
- Driver: 595.71
- Power plan: **Ultimate Performance**
- Game Mode: enabled
- Game DVR: disabled
- HAGS (`HwSchMode`): 2 (enabled)

## High-confidence diagnosis
The most likely issue in modern competitive / live-service shooters like **Marathon** is:

1. **CPU bottleneck from the Ryzen 5 5500**
2. **Low system RAM headroom (16 GB)**
3. **C: drive critically crowded**
4. **background process noise / overlays**

### Important counterintuitive point
If you already set *everything* to Low, that can make the game **more CPU-bound**, not less.

When GPU load is reduced too far:
- the GPU finishes frames quickly
- the CPU becomes the limiting stage
- frame pacing can feel worse even though "settings are lower"

So for a CPU-limited game, the goal is **not** always "lowest settings possible".
The goal is to:
- reduce CPU-heavy settings
- keep some GPU-bound settings moderately on
- cap FPS to a stable ceiling

## Critical storage finding
- C: drive size: ~446 GB
- C: free space: **21.3 GB**
- This is roughly **95% full**

This is bad enough to materially hurt:
- Windows responsiveness
- shader/cache behavior
- patching/install behavior
- pagefile flexibility
- general frametime stability

### Storage hotspots found
- `C:\Program Files (x86)\Steam` → **119 GB**
- `C:\Program Files (x86)\Steam\steamapps\common\Marathon` → **19 GB**
- `C:\Users\Admin\Downloads` contains a visible `Qwen3.5-9B-Q4_K_M.gguf` file → **5.29 GB**
- `C:\Users\Admin\AppData\Local\Temp` has lots of junk folders

Also:
- you already have an `E:` drive with **286.6 GB free**
- Steam has a second library at `E:\SteamLibrary`

This strongly suggests the best purge path is **not** manual suffering in random folders.
It is:
- move games/libraries off C:
- clean obvious temp/download waste
- then only do deeper cleanup if needed

## Background-process findings
Some recurring desktop/background apps that are plausible gaming tax / clutter candidates:
- `iCUE`
- `Notion`
- `GitHubDesktop`
- multiple `Code` / `WindowsTerminal` instances
- `ollama`

These are not catastrophic individually, but on a 6-core CPU, they absolutely matter when a game is CPU-limited.

## Practical gaming action plan (ranked)

### Tier 1 — biggest wins, lowest pain
1. **Free 60-100 GB on C:**
   - move one or two large games from `C:` to `E:` in Steam
   - clear `Downloads`
   - clear `Temp`
2. **Close background CPU junk before gaming:**
   - VS Code
   - GitHub Desktop
   - Notion
   - Ollama
   - iCUE if safe / optional for your setup
3. **Set a stable FPS cap** instead of chasing max FPS
   - try 60, 72, 90, or 120 depending on your monitor and actual stability
   - stable frametimes beat erratic uncapped FPS
4. **Do not run every setting on Low blindly**
   - keep CPU-heavy settings low
   - allow some GPU-heavy settings to stay medium if needed

### Tier 2 — game-side tuning for CPU bottlenecks
In Marathon / similar shooters, reduce or disable first:
- view distance / crowd / world detail if present
- shadow quality / shadow distance
- effects density / volumetrics if they hit CPU pathing
- background simulation / animation detail if exposed

Keep or test upward slightly:
- texture quality (mostly VRAM, and you have 16 GB)
- anisotropic filtering
- some image-quality options that are GPU-heavy but not CPU-heavy

Use if available:
- NVIDIA Reflex / low-latency mode
- DLSS / upscaling if it helps maintain a stable base framerate
- Frame Generation only if the base framerate is already decent enough; it helps feel smoother but does not fix CPU-side input latency fundamentally

### Tier 3 — likely medium-term hardware truth
The RTX 5070 Ti is much stronger than the Ryzen 5 5500 for modern high-FPS gaming.
So for CPU-heavy titles, **the CPU is the long pole**.

The most meaningful hardware upgrades later would be:
- **32 GB RAM** first (very practical)
- then a stronger AM4 gaming CPU if your board supports it (e.g. X3D path if feasible)

## Specific recommendation for your setup
If you want the highest-value sequence, do this:
1. reclaim 60+ GB on C:
2. close background apps before gaming
3. cap Marathon to a realistic stable target
4. re-test with a mix of low + medium settings instead of all-low
5. if still ugly, plan RAM upgrade to 32 GB

## 3. Qwen3.5 local model unreliability

## Smoking gun found
Your OpenClaw Ollama provider is configured like this in `models.json`:
- `baseUrl: "http://172.24.16.1:11434/v1"`
- `api: "ollama"`

OpenClaw docs explicitly warn:
- **Do not use `/v1` with Ollama for tool calling**
- OpenAI-compatible mode can cause the model to emit raw tool JSON as plain text
- use the native Ollama base URL instead:
  - `http://host:11434`
  - no `/v1`

This exactly matches the historical failure mode found in session logs:
- Qwen/Ollama often printed fake tool JSON or bash snippets
- it did **not** reliably enter true `toolUse`

So the main problem is probably **not just Qwen being flaky by nature**.
It is also that the runtime path is currently configured in a way OpenClaw documents as unreliable for tools.

## Additional inconsistency found
- OpenClaw config manually defines `qwen3.5:9b`
- the plain `ollama list` command from this environment did **not** show that model in the local CLI inventory

That suggests the runtime may be seeing models through a remote/alternate host path that is not perfectly mirrored in local CLI behavior.
This increases confusion and makes debugging harder.

## Best operating model for cost control
Yes — using Qwen as a **planner/orchestrator** is a very sensible idea.
But with one refinement:

### Best pattern
Use Qwen in a **read-mostly / no-danger** lane:
- allowed: `read`, maybe memory tools, maybe session listing
- denied: `write`, `exec`, heavy runtime tools

Then use Codex for:
- writes
- shell commands
- git operations
- non-trivial code edits

### Why this is good
It gives you:
- low-cost planning and summarization
- local contract drafting
- workspace awareness
- much less risk of malformed tool calling causing damage

### Important answer to your question
> if it doesn't execute tools, can it still read the workspace?

Only if it keeps **read access**.

If you remove all tools entirely, it cannot inspect arbitrary local files beyond whatever is already injected into prompt context.

So the clean pattern is **not** "no tools".
It is:
- Qwen gets **file read tools only** (or a very narrow allowlist)
- Codex gets runtime and write tools

## OpenClaw mechanism for this
OpenClaw supports provider/model-specific tool restrictions via:
- `tools.byProvider`

And tool groups include:
- `group:fs` = `read`, `write`, `edit`, `apply_patch`
- `group:runtime` = `exec`, `bash`, `process`

So the right shape is probably a model-specific narrow allowlist such as:
- allow only `read` and maybe memory/session tools for `ollama/qwen3.5:9b`
- deny `group:runtime`
- deny `write` / edit paths unless explicitly wanted later

## Recommended Qwen plan
### Phase A — fix the root runtime path
Change Ollama base URL from:
- `http://172.24.16.1:11434/v1`

to:
- `http://172.24.16.1:11434`

Keep:
- `api: "ollama"`

This should restore native `/api/chat` behavior.

### Phase B — use Qwen conservatively
Put Qwen into a limited role:
- contract drafting
- repo reading
- summary / review
- triage / routing
- memory maintenance

### Phase C — Codex handles execution
Codex remains the execution tier for:
- git
- shell
- code edits
- file writes
- riskier multi-step ops

## 4. Discord setup path

Discord setup in OpenClaw looks straightforward and sane.

## Recommended rollout
### Step 1 — make a private Discord server
Use it as a controlled testbed first.

### Step 2 — create a bot in Discord Developer Portal
Enable:
- Message Content Intent (**required**)
- Server Members Intent (recommended)
- Presence Intent (optional)

### Step 3 — invite the bot with minimum useful permissions
At least:
- View Channels
- Send Messages
- Read Message History
- Embed Links
- Attach Files

### Step 4 — set token locally
Do **not** send the token in chat.
Use config on the machine directly.

### Step 5 — pair via DM first
This is the safest first route.
Once DMs work, expand to your private guild.

### Step 6 — guild allowlist
For a private server:
- add your server ID to allowlist
- initially keep `requireMention: true`
- only later switch to `requireMention: false`

### Step 7 — structure channels by function
Suggested channels:
- `#watson-main`
- `#research`
- `#coding`
- `#ops`
- `#memory-lab`

This works nicely because each Discord channel gets its own isolated session context.

## My recommendation
When you come back, do Discord in this order:
1. bot + token
2. DM pairing
3. private guild allowlist
4. mention-required guild mode
5. then loosen behavior once we trust it

## 5. Bottom line

## Gaming
Your biggest practical issue right now is **not just raw CPU horsepower**.
It is the combination of:
- 6-core Ryzen CPU ceiling
- only 16 GB RAM
- **C: drive at 95% full**
- background app noise

If you fix only one thing immediately:
- **free a lot of space on C:** and move game weight to E:

## Qwen
Your current Qwen/Ollama tool instability is very likely made worse by a **bad provider path choice** (`/v1` on Ollama).
Best strategy:
- fix Ollama base URL
- use Qwen in a read-only / planning lane
- keep Codex as executor

## Discord
Very doable.
Start with DM pairing, then private guild, then structured channels.
