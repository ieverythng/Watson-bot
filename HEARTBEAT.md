# HEARTBEAT.md

Default heartbeat behavior for WatsonOW:

- If no active checklist exists below, reply `HEARTBEAT_OK`.
- Keep heartbeat work low-cost and workspace-bound.
- Do not spawn delegates from a heartbeat unless the checklist explicitly requires it.
- Do not start broad implementation work from a heartbeat.
- If a heartbeat performs a meaningful check, leave a short audit line in `memory/YYYY-MM-DD.md`.
- If a heartbeat reveals a real issue, report it clearly and stop unless the checklist already authorizes the next step.

## Active Checklist

Add temporary heartbeat tasks here when needed.
