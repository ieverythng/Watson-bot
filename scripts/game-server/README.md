# Game Server Scripts

Remote gaming orchestration: pause Watson inference → launch game → monitor → restore.

## Architecture

```
WSL (orchestrate-game.sh)  →  Windows PowerShell scripts  →  Lazarus restore
       │                           │                              │
       │  Phase 1: Kill proxies   │  Phase 2: Launch game        │  Phase 4: Lazarus
       │  Phase 3: Monitor        │  via Sunshine + Moonlight    │  resurrect stack
```

## Files

| Script | Purpose |
|--------|---------|
| `config.json` | Game library, paths, inference settings |
| `install-sunshine.ps1` | One-time Sunshine installer (download from GitHub) |
| `pause-watson.ps1` | Kill llama.cpp + LiteLLM to free VRAM |
| `launch-game.ps1` | Launch game by name or direct path |
| `monitor-game.ps1` | Watch game process, auto-resume on exit |
| `full-session.ps1` | Full Windows-side session (pause → play → resume) |
| `orchestrate-game.sh` | WSL orchestrator (calls PS scripts + Lazarus) |

## Quick Start

### 1. Install Sunshine (one-time)
```bash
pwsh -File /mnt/c/Users/Admin/Watson/scripts/game-server/install-sunshine.ps1
```

Then open https://localhost:47990 and configure apps.

### 2. Connect Moonlight
- **iPad:** App Store → "Moonlight"
- **Laptop:** https://moonlight-stream.org/downloads/
- Pair with PIN from Sunshine web UI

### 3. Play a game
```bash
# From WSL:
bash /home/juanbeck/Watson/scripts/game-server/orchestrate-game.sh mina_the_hollower

# Or Windows PowerShell:
pwsh -File /home/juanbeck/Watson/scripts/game-server/full-session.ps1 -GameName mina_the_hollower
```

### 4. Manual control
```bash
# Pause Watson only:
pwsh -File pause-watson.ps1

# Launch game only:
pwsh -File launch-game.ps1 -GameName mina_the_hollower

# Resume Watson (via Lazarus):
bash /home/juanbeck/Watson/scripts/lazarus.sh --skip-kill
```

## Network

**ZeroTier** is used for remote access (network: `3b19b3a716937e29`).
- Add Zsani's iPad/laptop to the ZeroTier network
- Moonlight connects via ZeroTier IP (e.g., `10.88.140.94`)
- No port forwarding needed

## Games Library

Add games to `config.json` → `games` section:
```json
"my_game": {
  "name": "My Game",
  "exe": "D:\\path\\to\\game.exe",
  "working_dir": "D:\\path\\to\\game",
  "process_name": "GameProcess",
  "steam_appid": null
}
```

For Steam games, use `steam_appid` instead of `exe`.
