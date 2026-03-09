# Main PC OM Validation - 2026-02-25T21-51-56Z

Repo: /home/juanbeck/Watson
Branch: feat/Foundations_OM_Skills
Commit: a96214d

## Host Snapshot
- uname: Linux ULTIMATE-MACHINE 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
- gpu: NVIDIA GeForce RTX 5070 Ti, 16303 MiB
- ram: 7.7Gi

## $ openclaw --version
```
2026.2.24
```
exit_code: 0

## $ openclaw status
```
[agents/model-providers] Failed to discover Ollama models: TypeError: fetch failed
[agents/model-providers] Failed to discover Ollama models: TypeError: fetch failed
[openclaw] Failed to start CLI: SystemError [ERR_SYSTEM_ERROR]: A system error occurred: uv_interface_addresses returned Unknown system error 1 (Unknown system error 1)
    at Object.networkInterfaces (node:os:217:16)
    at listTailnetAddresses (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/tailnet-BOWO-AaH.js:16:20)
    at pickPrimaryTailnetIPv4 (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/tailnet-BOWO-AaH.js:33:9)
    at resolveControlUiLinks (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/onboard-helpers-DOdss3HD.js:368:22)
    at file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/status-akosBtzI.js:1733:10
    at statusCommand (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/status-akosBtzI.js:1739:4)
    at async Object.run (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/run-main-BUdbv390.js:150:3)
    at async runCli (file:///home/juanbeck/.npm-global/lib/node_modules/openclaw/dist/run-main-BUdbv390.js:393:6)
