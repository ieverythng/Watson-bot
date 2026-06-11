# nao-ros4hri-bridge dependency matrix

Source inspected:
- `/home/juanbeck/Watson/repos/nao-ros4hri-bridge/docker/Dockerfile.full`
- all `package.xml` files under `/home/juanbeck/Watson/repos/nao-ros4hri-bridge/src`

## 1) Authoritative external packages from `docker/Dockerfile.full`

### Standard ROS 2 / Ubuntu apt
- ROS base image: `ros:jazzy-ros-base`
- ROS apt packages: `ros-jazzy-cv-bridge`, `ros-jazzy-gscam`, `ros-jazzy-image-transport-plugins`, `ros-jazzy-rosbridge-server`, `ros-jazzy-naoqi-libqi`, `ros-jazzy-rqt`, `ros-jazzy-rqt-console`, `ros-jazzy-rqt-gui`, `ros-jazzy-rqt-gui-py`, `ros-jazzy-rqt-image-view`, `ros-jazzy-rqt-reconfigure`
- Ubuntu/system apt packages: `curl`, `gnupg`, `gstreamer1.0-alsa`, `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good`, `gstreamer1.0-pulseaudio`, `gstreamer1.0-tools`, `git`, `python3-gi`, `python3-colcon-common-extensions`, `python3-cpuinfo`, `python3-matplotlib`, `python3-opencv`, `python3-pil`, `python3-pip`, `python3-psutil`, `python3-requests`, `python3-scipy`, `python3-tqdm`, `python3-yaml`

### SocialMinds apt packages
- `socialminds-ros-jazzy-audio-common`
- `socialminds-ros-jazzy-std-skills`
- `socialminds-ros-jazzy-chatbot-msgs`
- `socialminds-ros-jazzy-hri-actions-msgs`
- `socialminds-ros-jazzy-hri-face-detect-yunet`
- `socialminds-ros-jazzy-kb-msgs`
- `socialminds-ros-jazzy-knowledge-core`
- `socialminds-ros-jazzy-hri-msgs`
- `socialminds-ros-jazzy-hri-emotion-models`
- `socialminds-ros-jazzy-hri-emotion-recognizer`
- `socialminds-ros-jazzy-hri-person-manager`
- `socialminds-ros-jazzy-hri-visualization`
- `socialminds-ros-jazzy-expressive-face`
- `socialminds-ros-jazzy-interaction-sim`
- `socialminds-ros-jazzy-naoqi-bridge-msgs`
- `socialminds-ros-jazzy-naoqi-driver`
- `socialminds-ros-jazzy-launch-tui`
- `socialminds-ros-jazzy-oro`
- `socialminds-ros-jazzy-pyhri`
- `socialminds-ros-jazzy-tts-msgs`
- `socialminds-ros-jazzy-rqt-chat`
- `socialminds-ros-jazzy-rqt-human-radar`
- `socialminds-ros-jazzy-ros-qml-plugin`
- `socialminds-ros-jazzy-ui-msgs`
- `socialminds-ros-jazzy-ui-server`

### Python packages installed with pip
- `vosk`
- `pyasyncore`
- `pyasynchat`
- `torch`
- `torchvision`
- `ultralytics`
- `ultralytics-thop`
- `textual>=0.50,<1`

## 2) Packages explicitly rebuilt from source in Docker
`Dockerfile.full` explicitly rebuilds:
- `kb_skills`
- `dialogue_manager`
- `asr_vosk`
- `chatbot_llm`
- `planner_common`
- `planner_llm`
- `fake_skills`
- `nao_say_skill`
- `nao_replay_motion`
- `nao_look_at`
- `nao_orchestrator`
- `interaction_trace_viewer`
- `nao_scene_grounding`
- `nao_chatbot`
- `simple_audio_capture`

Because `colcon build --packages-up-to` is used, source dependencies in the workspace are also built as needed, including the local stub/interface packages present in `src/`.

## 3) Package-by-package matrix

Legend:
- **Std ROS2** = standard ROS/Ubuntu dependency
- **SM apt** = SocialMinds apt dependency
- **Source** = built from this workspace
- **Robot** = robot/NAO-specific dependency
- **Gap** = referenced in package.xml but not explicitly installed in Dockerfile.full

| Package | Build type | build_depend / depend / exec_depend | Robot-specific deps | SocialMinds-specific deps | Resolution notes |
|---|---|---|---|---|---|
| `asr_vosk` | `ament_python` | `ament_index_python`, `audio_common_msgs`, `diagnostic_msgs`, `hri_msgs`, `lifecycle_msgs`, `rcl_interfaces`, `rclpy`, `std_msgs`, `vosk` | none | `audio_common_msgs`, `hri_msgs` | `vosk` comes from pip; `audio_common_msgs` and `hri_msgs` are local source stubs shadowing SM apt packages |
| `audio_common_msgs` | msg pkg (no explicit export build_type in package.xml) | `std_msgs`, `builtin_interfaces`, `rosidl_default_generators`, `rosidl_default_runtime` | none | package itself corresponds to SM `audio-common` | local source stub; replaces `socialminds-ros-jazzy-audio-common` interfaces |
| `chatbot_llm` | `ament_python` | `rclpy`, `lifecycle_msgs`, `ament_index_python`, `launch`, `launch_ros`, `launch_pal`, `python3-requests`, `python3-yaml`, `python3-pydantic`, `hri_actions_msgs`, `i18n_msgs`, `chatbot_msgs`, `diagnostic_msgs`, `kb_skills`, `planner_common`, `skill_common` | none directly | `hri_actions_msgs`, `chatbot_msgs`, `i18n_msgs?`, `skill_common`, `launch_pal` | `requests`/`yaml` imports confirmed in code; `pydantic` import confirmed; **`python3-pydantic` not explicitly installed in Dockerfile.full** |
| `communication_skills` | `ament_cmake` | `ament_cmake_auto`, `rosidl_default_generators`, `action_msgs`, `builtin_interfaces`, `chatbot_msgs`, `std_skills`, `rosidl_default_runtime` | none | `chatbot_msgs`, `std_skills` | if not in workspace, expected from SM apt |
| `dialogue_manager` | `ament_python` | `rclpy`, `lifecycle_msgs`, `std_msgs`, `diagnostic_msgs`, `action_msgs`, `launch`, `launch_ros`, `launch_pal`, `communication_skills`, `chatbot_msgs`, `hri_msgs`, `hri_actions_msgs`, `planner_common` | none directly | `chatbot_msgs`, `hri_msgs`, `hri_actions_msgs`, `launch_pal` | `communication_skills` is source; chatbot/hri msgs expected from SM apt or local stubs |
| `rqt_dialogues` | `ament_python` | `rclpy`, `std_msgs`, `rqt_gui`, `rqt_gui_py`, `python3-pyside2.qtcore`, `python3-pyside2.qtgui`, `python3-pyside2.qtwidgets` | none | none | standard ROS/Ubuntu GUI tooling; **not explicitly installed in Dockerfile.full except generic `rqt`/`rqt_gui*`** |
| `fake_skills` | `ament_python` | `rclpy`, `rcl_interfaces`, `ament_index_python`, `nao_skills`, `std_msgs`, `skill_common`, `python3-yaml` | via `nao_skills` | `skill_common` | new package; source-built; depends on local `nao_skills` plus SM/shared skill registry stack |
| `hri_actions_msgs` | msg pkg (no explicit export build_type in package.xml) | `std_msgs`, `builtin_interfaces`, `rosidl_default_generators`, `rosidl_default_runtime` | none | package itself corresponds to SM apt | local source stub replacing `socialminds-ros-jazzy-hri-actions-msgs` |
| `hri_msgs` | msg pkg (no explicit export build_type in package.xml) | `std_msgs`, `rosidl_default_generators`, `rosidl_default_runtime` | none | package itself corresponds to SM apt | local source stub replacing `socialminds-ros-jazzy-hri-msgs` |
| `interaction_trace_viewer` | `ament_python` | `rclpy`, `std_msgs`, `hri_actions_msgs`, `rcl_interfaces`, `launch`, `launch_ros` | none | `hri_actions_msgs` | new package; source-built; otherwise standard ROS deps |
| `kb_skills` | `ament_python` | `rclpy`, `kb_msgs` | none | `kb_msgs` | new package; source-built; `kb_msgs` expected from `socialminds-ros-jazzy-kb-msgs` |
| `nao_chatbot` | `ament_python` | `rclpy`, `rcl_interfaces`, `std_msgs`, `hri_actions_msgs`, `asr_vosk`, `chatbot_llm`, `dialogue_manager`, `diagnostic_aggregator`, `knowledge_core`, `launch`, `launch_pal`, `launch_ros`, `lifecycle_msgs`, `hri_person_manager`, `hri_visualization`, `naoqi_driver`, `nao_robot`, `nao_look_at`, `nao_orchestrator`, `planner_llm`, `nao_replay_motion`, `nao_scene_grounding`, `nao_say_skill`, `rqt_chat`, `rqt_image_view`, `rviz2`, `python3-yaml`, `simple_audio_capture` | `naoqi_driver`, `nao_robot`, `nao_look_at`, `nao_orchestrator`, `nao_replay_motion`, `nao_scene_grounding`, `nao_say_skill` | `hri_actions_msgs`, `knowledge_core`, `hri_person_manager`, `hri_visualization`, `naoqi_driver`, `rqt_chat`, `launch_pal` | top-level integration package; strong robot coupling |
| `nao_look_at` | `ament_python` | `rclpy`, `lifecycle_msgs`, `diagnostic_msgs`, `launch`, `launch_ros`, `launch_pal`, `interaction_skills`, `std_skills`, `naoqi_bridge_msgs`, `tf2_ros` | `naoqi_bridge_msgs` | `interaction_skills`, `std_skills`, `naoqi_bridge_msgs`, `launch_pal` | source-built NAO skill; consumes SM skill interfaces and NAO bridge msgs |
| `nao_orchestrator` | `ament_python` | `rclpy`, `lifecycle_msgs`, `diagnostic_msgs`, `launch`, `launch_ros`, `launch_pal`, `std_msgs`, `geometry_msgs`, `hri_actions_msgs`, `hri_msgs`, `communication_skills`, `interaction_skills`, `kb_skills`, `nao_skills`, `naoqi_bridge_msgs`, `planner_common`, `skill_common` | `nao_skills`, `naoqi_bridge_msgs` | `hri_actions_msgs`, `hri_msgs`, `interaction_skills`, `skill_common`, `launch_pal` | new NAO execution core; source-built |
| `nao_replay_motion` | `ament_cmake` | `ament_cmake`, `ament_cmake_python`, `rclcpp`, `rclpy`, `action_msgs`, `std_msgs`, `sensor_msgs`, `std_skills`, `naoqi_libqi`, `naoqi_bridge_msgs`, `nao_skills` | **`naoqi_libqi`**, `naoqi_bridge_msgs`, `nao_skills` | `std_skills`, `naoqi_bridge_msgs` | robot-specific source build; `naoqi_libqi` comes from standard ROS apt, bridge msgs from SM/local stub |
| `nao_say_skill` | `ament_python` | `rclpy`, `lifecycle_msgs`, `diagnostic_msgs`, `action_msgs`, `launch`, `launch_ros`, `launch_pal`, `communication_skills`, `std_msgs`, `std_skills`, `tts_msgs` | via NAO speech role, but no direct NAO driver dep | `std_skills`, `tts_msgs`, `launch_pal` | source-built; `tts_msgs` currently provided by local stub replacing SM apt package |
| `nao_scene_grounding` | `ament_python` | `rclpy`, `std_msgs`, `kb_msgs` | none directly | `kb_msgs` | new package; source-built; bridges detector outputs to KnowledgeCore |
| `nao_skills` | `ament_cmake` | `ament_cmake`, `rosidl_default_generators`, `action_msgs`, `rosidl_default_runtime` | package defines NAO-specific action interfaces | none directly | source-built interface package; consumed by fake/orchestrator/motion packages |
| `naoqi_bridge_msgs` | msg pkg (no explicit export build_type in package.xml) | `std_msgs`, `rosidl_default_generators`, `rosidl_default_runtime` | yes: NAO bridge messages | package itself corresponds to SM apt | local source stub replacing `socialminds-ros-jazzy-naoqi-bridge-msgs` |
| `planner_common` | `ament_python` | `hri_actions_msgs`, `skill_common` | none | `hri_actions_msgs`, `skill_common` | new package; source-built; shared planner/orchestrator contract layer |
| `planner_llm` | `ament_python` | `rclpy`, `std_msgs`, `hri_actions_msgs`, `ament_index_python`, `planner_common`, `skill_common`, `python3-yaml` | none | `hri_actions_msgs`, `skill_common` | new package; source-built |
| `simple_audio_capture` | `ament_python` | `ament_python`, `rclpy`, `audio_common_msgs`, `python3-gi`, `gstreamer1.0-tools`, `gstreamer1.0-alsa`, `gstreamer1.0-pulseaudio`, `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good` | none | `audio_common_msgs` | source-built; system audio stack comes from Ubuntu apt |
| `tts_msgs` | msg pkg (no explicit export build_type in package.xml) | `std_msgs`, `rosidl_default_generators`, `rosidl_default_runtime` | none | package itself corresponds to SM apt | local source stub replacing `socialminds-ros-jazzy-tts-msgs` |

## 4) Focused findings for the NEW branch packages

### `fake_skills`
- Build type: `ament_python`
- Direct deps: `rclpy`, `rcl_interfaces`, `ament_index_python`, `nao_skills`, `std_msgs`, `skill_common`, `python3-yaml`
- Category: **source-built**, with a **NAO-facing contract dependency** through local `nao_skills`
- SocialMinds dependency surface: `skill_common` (not in workspace)

### `planner_common`
- Build type: `ament_python`
- Direct deps: `hri_actions_msgs`, `skill_common`
- Category: **source-built**, no robot-specific deps
- SocialMinds dependency surface: `hri_actions_msgs` (currently local stub), `skill_common`

### `planner_llm`
- Build type: `ament_python`
- Direct deps: `rclpy`, `std_msgs`, `hri_actions_msgs`, `ament_index_python`, `planner_common`, `skill_common`, `python3-yaml`
- Category: **source-built**, no robot-specific deps
- SocialMinds dependency surface: `hri_actions_msgs`, `skill_common`

### `kb_skills`
- Build type: `ament_python`
- Direct deps: `rclpy`, `kb_msgs`
- Category: **source-built**, no robot-specific deps
- SocialMinds dependency surface: `kb_msgs`

### `nao_scene_grounding`
- Build type: `ament_python`
- Direct deps: `rclpy`, `std_msgs`, `kb_msgs`
- Category: **source-built**, not inherently robot-driver-specific but semantically tied to NAO integration pipeline
- SocialMinds dependency surface: `kb_msgs`

### `interaction_trace_viewer`
- Build type: `ament_python`
- Direct deps: `rclpy`, `std_msgs`, `hri_actions_msgs`, `rcl_interfaces`, `launch`, `launch_ros`
- Category: **source-built**, no robot-specific deps
- SocialMinds dependency surface: `hri_actions_msgs`

## 5) Cross-workspace dependency categorization

### Built from source in this workspace
Core new/modified source packages:
- `asr_vosk`
- `chatbot_llm`
- `communication_skills`
- `dialogue_manager`
- `rqt_dialogues`
- `fake_skills`
- `interaction_trace_viewer`
- `kb_skills`
- `nao_chatbot`
- `nao_look_at`
- `nao_orchestrator`
- `nao_replay_motion`
- `nao_say_skill`
- `nao_scene_grounding`
- `nao_skills`
- `planner_common`
- `planner_llm`
- `simple_audio_capture`

Local stub/interface source packages that replace SocialMinds apt artifacts:
- `audio_common_msgs`
- `hri_actions_msgs`
- `hri_msgs`
- `naoqi_bridge_msgs`
- `tts_msgs`

### SocialMinds apt dependencies not present as workspace packages
- `chatbot_msgs`
- `std_skills`
- `kb_msgs`
- `knowledge_core`
- `hri_person_manager`
- `hri_visualization`
- `naoqi_driver`
- `rqt_chat`
- likely `interaction_skills`, `skill_common`, `launch_pal`, `i18n_msgs`, `nao_robot` are external as well, but they are **not explicitly installed in Dockerfile.full under those exact names**; they may arrive transitively from other apt packages or from upstream repositories.

### Standard ROS 2 / Ubuntu dependencies used by workspace packages
Representative direct deps appearing in `package.xml` files:
- ROS/runtime: `rclpy`, `rclcpp`, `rcl_interfaces`, `lifecycle_msgs`, `std_msgs`, `diagnostic_msgs`, `geometry_msgs`, `sensor_msgs`, `action_msgs`, `tf2_ros`, `launch`, `launch_ros`, `rqt_gui`, `rqt_gui_py`, `rqt_image_view`, `rviz2`
- Message generation: `ament_cmake`, `ament_cmake_auto`, `ament_cmake_python`, `ament_python`, `rosidl_default_generators`, `rosidl_default_runtime`, `builtin_interfaces`
- Ubuntu/system: `python3-gi`, `python3-yaml`, `python3-requests`, `python3-pydantic`, `python3-pyside2.qtcore`, `python3-pyside2.qtgui`, `python3-pyside2.qtwidgets`, `gstreamer1.0-*`

### Python-only runtime deps observed
- Package XML / code confirmed: `vosk`, `requests`, `yaml` (PyYAML), `pydantic`
- Docker-only extra Python deps not referenced by current `package.xml` set: `torch`, `torchvision`, `ultralytics`, `ultralytics-thop`, `textual`, `pyasyncore`, `pyasynchat`
  - These appear to support optional CV/UI tooling in the image rather than the listed core packages.

## 6) Notable gaps / mismatches
- The user-provided package list mentioned `chatbot_msgs` and `std_skills` in `src/`, but they are **not present as source packages** in this checkout.
- Several local message packages are explicitly labeled as **stubs for local development because the SocialMinds apt repo was down**: `audio_common_msgs`, `hri_actions_msgs`, `hri_msgs`, `naoqi_bridge_msgs`, `tts_msgs`.
- `chatbot_llm` declares `python3-pydantic`, but `Dockerfile.full` does **not** explicitly install `python3-pydantic`.
- `launch_pal`, `interaction_skills`, `skill_common`, `i18n_msgs`, `nao_robot`, and `diagnostic_aggregator` are referenced by package manifests but are **not explicitly listed in Dockerfile.full** under those exact package names, so they are either transitive apt dependencies or unresolved requirements that should be verified in a live build environment.
