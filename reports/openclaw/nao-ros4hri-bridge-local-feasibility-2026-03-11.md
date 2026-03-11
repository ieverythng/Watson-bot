# NAO ROS4HRI Bridge - Local Feasibility Report

Date: 2026-03-11
Repo: `ieverythng/nao-ros4hri-bridge`
Branch inspected: `refactor/modularise-nodes-to-ROS4HRI-standard`
Local clone: `/home/juanbeck/Watson/repos/nao-ros4hri-bridge`

## Executive Summary

This repo is structurally in good shape for future NAO-ROS2 ablations, but it is **not runnable on this machine yet without host/runtime prep**.

The good news:
- the repo cloned cleanly
- the target branch is available and checked out
- the SocialMinds apt repository is reachable
- local Ollama is reachable from this machine
- `/dev/snd` exists, so audio passthrough is plausible
- `Dockerfile.full` can bootstrap from a public ROS Jazzy base image

The blockers today:
- no Docker or Podman installed
- no ROS 2 Jazzy installed on host
- no `colcon`
- no `pip`
- no sudo available in this session
- the launch defaults assume a NAO IP (`172.26.112.62`) that is not reachable from the current WSL network context

## What The Repo Actually Is

This is a **ROS 2 Jazzy workspace** for:
- NAO execution via `naoqi_driver` / `naoqi_libqi`
- ROS4HRI skill interfaces and messages
- local Vosk ASR
- audio capture via GStreamer
- Ollama-backed chat orchestration

Main local packages in `src/`:
- `asr_vosk`
- `communication_skills`
- `dialogue_manager`
- `nao_chatbot`
- `nao_skill_servers`
- `nao_skills`
- `simple_audio_capture`

## Key Dependency Surface

From package manifests and Dockerfiles, the practical dependency stack is:

### ROS / robot stack
- ROS 2 Jazzy
- `naoqi_libqi`
- `naoqi_driver`
- `naoqi_bridge_msgs`
- `hri_msgs`
- `chatbot_msgs`
- `tts_msgs`
- `std_skills`
- `communication_skills`
- `audio_common_msgs`

### Audio / ASR
- `gstreamer1.0-alsa`
- `gstreamer1.0-plugins-base`
- `gstreamer1.0-plugins-good`
- `gstreamer1.0-pulseaudio`
- `gstreamer1.0-tools`
- `python3-gi`
- `vosk`
- Vosk model mounted at `/models/...`

### Build / dev
- `python3-colcon-common-extensions`
- `python3-pip`
- `git`
- test/dev extras from `requirements-dev.txt`:
  - `pre-commit`
  - `pytest`
  - `ruff`

## Dockerfile Interpretation

### `docker/Dockerfile.full`
This is the correct **first build target** on a fresh machine.

It:
- starts from `ros:jazzy-ros-base`
- adds the SocialMinds apt repo
- installs ROS4HRI + NAO-related binary packages
- installs Vosk via pip
- copies this repo `src/`
- clones `rqt_chat`
- runs `colcon build`

Implication:
- this file is intended to bootstrap a mostly self-contained runtime from scratch

### `docker/Dockerfile`
This is an **overlay image**, not the best first entry point here.

It:
- starts from `ARG BASE_IMAGE=iiia:nao`
- assumes a validated pre-existing image already contains the broader base runtime
- overlays only this repo's `src/`
- rebuilds selected packages

Implication:
- on this machine, `Dockerfile.full` is the realistic starting point
- `Dockerfile` becomes useful only after we have a known-good base image strategy

## Local Machine Findings

### Confirmed
- OS: `Ubuntu 24.04.3 LTS` in WSL2
- network interface: `eth0` on `172.24.31.12/20`
- local Ollama binary exists: `/usr/local/bin/ollama`
- local Ollama API reachable on `172.24.16.1:11434`
- `/dev/snd` exists
- GitHub access works for repo cloning
- SocialMinds apt repo reachable over HTTPS

### Missing / blocking
- Docker runtime: missing
- Podman runtime: missing
- ROS Jazzy host install: missing (`/opt/ros/jazzy` absent)
- `colcon`: missing
- `pip`: missing
- elevated package install path: unavailable from current session (`sudo -n` fails)

### Network caveat
Launch defaults in `nao_chatbot_skills.launch.py` include:
- `start_naoqi_driver:=true`
- `nao_ip:=172.26.112.62`
- `network_interface:=eth0`

From this current WSL environment, the default NAO IP was **not reachable**.

Implication:
- for local smoke tests, disable the driver
- for real NAO runs, pass the robot's current reachable IP explicitly and validate network routing from the runtime environment

## Smartest Setup Path

## Recommendation: Docker-first, then robot connectivity

Why this is the sane path:
- host is missing the full ROS toolchain
- repo already includes a strong container story
- the branch is clearly organized around launch profiles and packaged runtime behavior
- this lets us validate most of the stack before fighting NAO networking

### Phase 1 - make the machine container-capable
Install one of:
- Docker Engine / Docker Desktop with WSL integration, or
- Podman

Docker is the easier path here because the repo already speaks Docker natively.

### Phase 2 - build the full image
From repo root:

```bash
docker build -f docker/Dockerfile.full -t nao-ros4hri-bridge:full .
```

### Phase 3 - run smoke tests without NAO first
Use the skills-only profile with the robot driver disabled:

```bash
docker run --rm -it \
  --network host \
  nao-ros4hri-bridge:full \
  bash
```

Then inside:

```bash
ros2 launch nao_chatbot nao_chatbot_skills.launch.py \
  start_naoqi_driver:=false \
  start_rqt_chat:=false
```

This validates:
- package sourcing
- launch graph
- skill servers
- mission controller wiring
- Ollama chat path assumptions

## Why `--network host` matters
The code defaults to Ollama at `http://localhost:11434/api/chat`.
Inside a bridged container, `localhost` would point to the container itself, not the host.

So either:
- run with `--network host`, or
- override the Ollama URL to a host-reachable address

## Phase 4 - ASR validation
Mount a Vosk model and audio access:

```bash
docker run --rm -it \
  --network host \
  --device /dev/snd \
  -v /absolute/path/to/vosk-models:/models \
  nao-ros4hri-bridge:full \
  bash
```

Then:

```bash
ros2 launch nao_chatbot nao_chatbot_asr_only.launch.py \
  asr_vosk_model_path:=/models/vosk-model-small-en-us-0.15
```

This validates:
- audio capture
- ASR lifecycle node
- Vosk model loading
- ROS4HRI `LiveSpeech` publication

## Phase 5 - NAO integration
Only after the above works:

```bash
ros2 launch nao_chatbot nao_chatbot_skills.launch.py \
  start_naoqi_driver:=true \
  start_rqt_chat:=false \
  nao_ip:=<actual-nao-ip> \
  network_interface:=<correct-interface>
```

At that stage, verify:
- robot IP reachability
- camera topics
- `/joint_angles`
- posture skill server path
- head motion path

## What I Would Do Next On This Machine

1. Install Docker in the host/WSL setup.
2. Build `docker/Dockerfile.full`.
3. Smoke test `nao_chatbot_skills.launch.py` with `start_naoqi_driver:=false`.
4. Add Vosk model mount and run `nao_chatbot_asr_only.launch.py`.
5. Only then attempt real NAO connectivity.

## Practical Notes For Future Ablations

For NAO-ROS2 ablations, this repo is well-positioned because it already separates:
- ASR-only path
- skills-only path
- full stack path
- optional robot driver path

That means ablations can cleanly isolate:
- ASR quality vs dialogue behavior
- Ollama backend behavior vs rules mode
- robot execution vs non-robot orchestration
- head-motion/posture effects independently

## Bottom Line

**Can this work here eventually?** Yes.

**Can I fully set it up right now from this session alone?** No, because the machine lacks the container/runtime/toolchain prerequisites and I do not currently have elevated install rights.

**Best next move:** make this machine Docker-capable and use `Dockerfile.full` as the first reproducible runtime path.
