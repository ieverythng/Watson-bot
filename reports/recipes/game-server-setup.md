# Game Server Setup — Operating Procedure

## Overview
Install and configure Sunshine + Moonlight remote gaming on Juan's PC, with Watson orchestration for automated game sessions.

## Prerequisites
- Windows 11 host with RTX 5070 Ti (16GB VRAM)
- Steam installed (optional — non-Steam games work too)
- WSL2 with Hermes agent running
- ZeroTier network `3b19b3a716937e29` (my-first-network) — already active

## Steps

### 1. Install Sunshine on Windows Host
```powershell
# Run in WSL:
pwsh -File /mnt/c/Users/Admin/Watson/scripts/game-server/install-sunshine.ps1
```
Or manually download from https://github.com/LizardByte/Sunshine/releases

### 2. Configure Sunshine Web UI
- Open https://localhost:47990
- Add Equinox: Homecoming as app entry:
  - Command: `C:\Program Files (x86)\Steam\steam.exe -applaunch APPID`
  - Working dir: `C:\Program Files (x86)\Steam`
- Configure encoder settings:
  - Encoder: NVENC
  - Codec: H.264 or HEVC
  - Preset: P1 or P2
  - Rate control: CBR
  - Bitrate: 15-25 Mbps (1080p)

### 3. Network Setup
**ZeroTier (already configured):**
- Network: `3b19b3a716937e29` (my-first-network)
- Windows PC ZT IP: `10.88.140.94`
- WSL ZT IP: `10.88.140.135`
- Add Zsani's iPad/laptop to the ZeroTier network (up to 10 devices free)
- Moonlight connects via ZeroTier IP — no port forwarding needed

**Alternative — Port Forwarding:**
- Forward UDP: 47998, 47999, 48000
- Forward TCP: 47984, 47989, 47990
- Use DDNS or static IP

### 4. Install Moonlight on Client Devices
- **iPad:** App Store → "Moonlight"
- **Laptop:** https://moonlight-stream.org/downloads/
- Pair with Sunshine PIN (shown in web UI)

### 5. Test Connection
1. Start a simple game via Sunshine web UI
2. Connect Moonlight client
3. Verify video stream, audio, and controller input
4. Measure latency

### 6. Configure Watson Orchestration
- Edit `scripts/game-server/config.json` with correct paths
- Look up Equinox: Homecoming Steam APPID
- Update `GAME_APPIDS` in `orchestrate-game.sh`
- Test full session: `./orchestrate-game.sh equinox_homecoming`

### 7. Discord Integration
- Watson listens for "play [game]" commands
- Looks up APPID from game registry
- Runs orchestrate-game.sh
- Notifies when ready and when session ends

## Verification Checklist
- [ ] Sunshine service running on Windows
- [ ] Moonlight paired and connected over LAN
- [ ] Moonlight connected over ZeroTier VPN (10.88.x.x)
- [ ] Controller passthrough working on iPad
- [ ] Watson pause/resume cycle tested
- [ ] Lazarus restore verified after gaming session
- [ ] Full session: Discord command → game launch → play → auto-resume

## Troubleshooting
- **Moonlight can't connect:** Check UDP ports, firewall, ZeroTier status (`zerotier-cli listnetworks`)
- **Black screen in Moonlight:** Sunshine may not have launched the app — check web UI logs
- **Controller not working:** Ensure controller is paired to iPad, not PC. Check Moonlight settings.
- **High latency:** Reduce bitrate, switch to H.264, use Ethernet on host, 5GHz Wi-Fi on client
- **Stuttering:** Lower resolution/bitrate, close background apps on host
- **Lazarus fails:** Check that stack script exists at `C:\Users\Admin\PROJECTS\zerotier-llm-proxy\scripts\windows\Start-Qwen36ZeroTierStack.ps1`
