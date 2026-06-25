# Remote Gaming Architecture — WatsonOW Game Server

## Overview

Turn Juan's PC (Ryzen 7 5800X / RTX 5070 Ti 16GB VRAM / 16GB RAM) into a personal game streaming server. Zsani connects from her laptop or iPad over the internet, plays Steam games remotely, with Watson orchestrating the entire pipeline.

## Phase 1: Equinox: Homecoming (Priority Game)

### Game Profile (VERIFIED via Steam API)
- **Steam APPID:** `3258290`
- **Price:** €14.79 EUR
- **Genre:** Horse mystery MMO / Multi-player adventure
- **Description:** "Saddle up with friends and investigate a dark mystery, where each trail leads to wonder and intrigue."
- **Min specs:** i9-9900K 3.6 GHz, 8GB RAM, RTX 2070, 20GB storage
- **Controller support:** ✅ Full controller support (Steam category ID 28)
- **Typical VRAM:** 4-8GB depending on settings
- **Typical RAM:** 8-12GB during gameplay

### Resource Conflict Analysis

| Component | VRAM | System RAM |
|-----------|------|------------|
| Equinox: Homecoming | 4-8 GB | 8-12 GB |
| llama.cpp 27B (Q3) | 11-13 GB | ~2 GB |
| Windows + WSL overhead | ~1 GB | 2-4 GB |
| **Total** | **16-22 GB** ❌ | **12-18 GB** ⚠️ |

**Verdict:** Cannot run game + 27B LLM simultaneously on 16GB/16GB hardware.

### Solution: Watson Auto-Pause System

```
┌─────────────────────────────────────────────┐
│           GAME SESSION FLOW                 │
├─────────────────────────────────────────────┤
│                                              │
│  1. Zsani requests game via Discord         │
│  2. Watson pauses llama.cpp (stops GPU)     │
│  3. Sunshine host is already running         │
│  4. Watson launches Equinox via Steam        │
│  5. Zsani connects via Moonlight client      │
│  6. [GAMEPLAY — Watson dormant]             │
│  7. Game exits → Watson detects process end  │
│  8. Watson restarts llama.cpp + resumes      │
│  9. Discord notification: "Watson back"     │
│                                              │
└─────────────────────────────────────────────┘
```

## Phase 2: Streaming Platform — Moonlight + Sunshine (VERIFIED)

### Comparison Matrix (Research-Verified)

| Solution | iPad App | Controller Passthrough | Internet Latency | Setup Complexity | Host Overhead | Status |
|----------|----------|------------------------|------------------|------------------|---------------|--------|
| **Moonlight + Sunshine** | ✅ Native app, strong support | ✅ Full (XInput, DS4, HID) — BT controller on iPad relayed to host | ⭐⭐⭐⭐⭐ Best | Moderate (~100MB RAM) | Active dev |
| Steam Remote Play | ✅ iOS app active (NOT deprecated) | ✅ Good | ⭐⭐⭐⭐ Good | Easy (~200-400MB RAM) | Active |
| Parsec | ❌ No iPad/iOS client | ✅ Excellent on desktop | ⭐⭐⭐⭐ Good | Easy (~150-350MB RAM) | Active |
| NVIDIA GameStream | ❌ Deprecated 2021 | N/A | N/A | N/A | Dead |
| RustDesk gaming | ✅ iOS app exists | ⚠️ Limited for gaming | ⭐⭐ Fair | Easy (~100-250MB RAM) | Active, not gaming-first |

### Why Moonlight + Sunshine Wins
1. **Best latency** — NVENC hardware encoding on RTX 5070 Ti, P1/P2 preset for lowest encode delay
2. **Native iPad app** with full controller support — Parsec has no iOS client
3. **Bluetooth controllers paired to iPad** → input relayed through Moonlight → Sunshine presents as virtual Xbox controller on Windows host
4. **Open source, self-hosted, no subscription**
5. **Lowest host overhead** (~100-300MB RAM, ~100-300MB VRAM for encoder surfaces)

### Steam Link Clarification
Steam Link iOS app is **NOT deprecated** — it's still available and functional. The confusion stems from the discontinued Steam Link hardware box and Apple's 2018 initial rejection. Use as fallback if Sunshine setup proves too complex.

## Phase 3: Architecture Design

### System Components

```
┌──────────────────────┐     ┌──────────────────────┐
│   Zsani's Device     │     │   Juan's PC (Host)    │
│                      │     │                       │
│  Moonlight Client    │◄────│  Sunshine Host        │
│  (iPad / Laptop)     │ UDP │  (NVENC encoder)      │
│                      │────►│                       │
│  Bluetooth Controller│     │  Steam + Game         │
│  → input relayed ────┼────►│                       │
│                      │     │  WSL2                  │
│                      │     │   └─ Hermes Agent      │
│                      │     │   └─ llama.cpp (paused)│
└──────────────────────┘     └──────────────────────┘
         │                              │
         │    Internet                   │
         │    UDP: 47998, 47999,        │
         │    48000, 48010              │
         ▼                              ▼
┌──────────────────────┐     ┌──────────────────────┐
│   Discord Bot        │────►│   Watson Orchestrator │
│   (Zsani: "play      │     │                      │
│    Equinox")         │     │  1. Pause LLM        │
│                      │     │  2. Sunshine running  │
│                      │     │  3. Launch game       │
│                      │     │  4. Monitor process   │
│                      │     │  5. Resume on exit    │
└──────────────────────┘     └──────────────────────┘
```

### How Sunshine Sessions Work (Important)

Sunshine does NOT have a "start stream via API" command. Stream sessions are **client-driven**:
1. Moonlight client connects to Sunshine
2. Moonlight selects an advertised app/desktop
3. Sunshine launches the configured target app and starts streaming

**Automation pattern:** Watson pre-launches the game, Zsani connects via Moonlight selecting the game entry, or Watson uses Sunshine's "prep commands" to set up the environment before connection.

### Network Requirements

- **UDP ports:** 47998, 47999, 48000, 48010 (for direct internet access)
- **TCP ports:** 47984, 47989, 47990 (web UI), 48010
- **NAT traversal:** ZeroTier VPN (network `3b19b3a716937e29`) — already active, no port forwarding needed
- **ZeroTier IPs:** Windows PC = `10.88.140.94`, WSL = `10.88.140.135`
- **Client devices:** Add Zsani's iPad/laptop to ZeroTier network (up to 10 free)
- **Minimum bandwidth:** 15 Mbps upload on host, 25 Mbps download on client
- **Recommended:** Ethernet on host, 5GHz/6GHz Wi-Fi on client

### Controller Passthrough Flow

```
iPad Bluetooth Controller → Moonlight App (captures input) 
→ Encoded in stream → Sunshine Host → Virtual Xbox Controller → Game
```

The controller pairs to the iPad, NOT to Juan's PC. Moonlight captures gamepad input on iPad and sends it through the streaming protocol. Sunshine presents it as a virtual Xbox controller device on Windows. Core stick/button/trigger passthrough works reliably; rumble/gyro/touchpad may vary.

## Phase 4: NVENC Encoder Settings (RTX 5070 Ti)

| Setting | Value | Reason |
|---------|-------|--------|
| Encoder | NVENC | Hardware encoding, minimal CPU overhead |
| Codec | H.264 (safest) or HEVC (better quality/bitrate) | AV1 only if client decode verified |
| Preset | P1 or P2 | Lowest encode latency |
| Rate control | CBR | Stable bitrate for internet |
| Lookahead | Off | Reduce encode delay |
| B-frames | Disabled/Minimized | Lowest latency |
| Resolution | 1080p60 or 1440p60 | Sweet spot for latency vs quality |
| Bitrate (1080p) | 15-25 Mbps | Adjust based on uplink |
| Bitrate (1440p) | 25-40 Mbps | If network supports it |
| AQ/Psycho-visual | Conservative | Don't add encode delay |

## Phase 5: Implementation Plan

### Step 1: Install Sunshine on Windows Host
- Download from GitHub (LizardByte/Sunshine)
- Configure NVENC encoder per settings above
- Set up user accounts and permissions
- Add Equinox: Homecoming as a Sunshine app entry (`steam.exe -applaunch APPID`)
- Test pairing with Moonlight on LAN first

### Step 2: Network Setup
- **ZeroTier VPN** (already configured) — network `3b19b3a716937e29`, no port forwarding needed
- Add client devices to ZeroTier network and connect Moonlight via ZT IP
- Test internet latency and adjust bitrate

### Step 3: Install Moonlight on Client Devices
- **iPad:** App Store → "Moonlight" app
- **Laptop:** Desktop client from moonlight-stream.org
- Pair with Sunshine PIN

### Step 4: Watson Orchestration Scripts

```
scripts/game-server/
├── config.json             # Game library, paths, inference settings
├── install-sunshine.ps1    # One-time Sunshine installer
├── pause-watson.ps1        # Stop llama.cpp, free VRAM (Windows)
├── resume-watson.ps1       # Restart llama.cpp after game ends
├── launch-game.ps1         # Launch game by name or direct path
├── monitor-game.ps1        # Watch process, detect exit, trigger resume
├── full-session.ps1        # Full Windows-side session pipeline
└── orchestrate-game.sh     # WSL orchestrator (calls PS scripts + Lazarus)
```

### Watson Auto-Pause + Lazarus Restore

The game session uses Lazarus (`scripts/lazarus.sh`) for the restore phase:
1. **Pause:** Kill llama.cpp on Windows + WSL LiteLLM proxies → frees 11-13GB VRAM
2. **Launch:** Game starts via Sunshine (Steam APPID or direct .exe)
3. **Monitor:** Watch game process, detect exit
4. **Restore:** Lazarus kills stale WSL proxies → launches canonical Windows stack via `Start-Qwen36ZeroTierStack.ps1` → verifies full chain

### Step 5: Discord Integration
- Watson listens for game requests in Discord
- Parses game name, looks up Steam APPID
- Executes full session pipeline via PowerShell on Windows host
- Notifies when ready to connect and when session ends

## Phase 6: Resource Budget

| Item | Cost |
|------|------|
| Sunshine | Free (open source) |
| Moonlight | Free (open source) |
| Equinox: Homecoming | ~€14.79 on Steam |
| Bluetooth controller for iPad | ~€30-50 (if needed) |
| ZeroTier | Free tier (up to 10 devices) |
| **Total** | **~€45-75** |

## Open Questions / Verification Needed

1. [x] Verify Equinox: Homecoming exact Steam APPID and controller support on Steam page — **APPID 3258290, full controller support confirmed**
2. [ ] Test Sunshine + Moonlight pairing over ZeroTier VPN — measure actual latency
3. [ ] Determine optimal bitrate for Juan's specific upload speed
4. [ ] Test Bluetooth controller passthrough on iPad specifically with a known game
5. [x] Implement Watson auto-pause/resume PowerShell scripts on Windows host — **scripts created in `scripts/game-server/`**
6. [ ] Add game library discovery (Steam API integration for APPID lookup)
7. [x] Decide: ZeroTier VPN vs port forwarding — **ZeroTier chosen (already active, network `3b19b3a716937e29`)**
8. [ ] Test full session pipeline with Mina: The Hollower as test game
9. [ ] Verify Lazarus restore after gaming session

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VRAM conflict: game + LLM | Certain if not paused | Critical — crashes | Auto-pause Watson before game |
| High latency over internet | Medium | High — unplayable | ZeroTier VPN, Ethernet host, bitrate tuning |
| Controller passthrough issues on iPad | Low-Medium | Medium | Test thoroughly with Moonlight iOS app |
| 16GB system RAM pressure | Medium | Medium — stuttering | Close background apps during game sessions |
| Sunshine/Moonlight pairing fails | Low | Medium | Steam Link as fallback |
| Lazarus restore fails after gaming | Low | High — Watson offline | Manual `bash scripts/lazarus.sh` fallback; stack script verified at `C:\Users\Admin\PROJECTS\zerotier-llm-proxy\scripts\windows\Start-Qwen36ZeroTierStack.ps1` |
