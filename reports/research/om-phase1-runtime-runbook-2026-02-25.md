# OM Phase 1 Runtime Runbook - 2026-02-25

## Goal

Unblock OpenClaw memory indexing on the main machine and verify recall against known memory facts.

## Current Validation State

Latest run:
- `reports/openclaw/mainpc-om-validation-2026-02-25T22-01-25Z.md`

Observed state:
- `openclaw` runtime and gateway are reachable.
- `openclaw memory index --force --verbose` returns success.
- Memory index remains `0 files / 0 chunks`.
- Root cause is explicit in CLI output:
  - `Skipping memory file sync in FTS-only mode (no embedding provider)`.

Implication:
- Memory indexing will remain empty until `agents.defaults.memorySearch.provider` is configured with working credentials or a working local model.

## Dependency Checklist

1. Choose embedding provider:
- Remote: `openai`, `gemini`, `voyage`, or `mistral`
- Local: `local` with `agents.defaults.memorySearch.local.modelPath`

2. Provide credentials/model access:
- Remote: set provider API key in env or config
- Local: ensure local embedding runtime is reachable and model path is valid

3. Rebuild index and validate recall:
- Index non-zero files/chunks
- Search queries return expected hits

4. Expand memory scope beyond default `MEMORY.md + memory/*.md`:
- Include reflective lanes in index:
  - `bank/`
  - `OBSERVATIONS.md`
  - `REFFLECTIONS.md`

## Path A: Remote Provider (OpenAI example)

```bash
openclaw config set agents.defaults.memorySearch.provider openai
openclaw config set agents.defaults.memorySearch.model text-embedding-3-small
openclaw config set agents.defaults.memorySearch.fallback none
openclaw config set agents.defaults.memorySearch.extraPaths '["bank","OBSERVATIONS.md","REFFLECTIONS.md"]'

# Option 1: env var (preferred for secrets)
export OPENAI_API_KEY='***'

# Option 2: config key (if needed)
# openclaw config set agents.defaults.memorySearch.remote.apiKey '***'

openclaw memory index --force --verbose
openclaw memory status --deep
openclaw memory search --json --query "Juan Bendek"
openclaw memory search --json --query "staged workflow"
openclaw memory search --json --query "Observational Memory"
```

Expected:
- provider is no longer `none`
- indexed files/chunks are greater than zero
- known-query search returns matching entries

## Path B: Local Provider

```bash
openclaw config set agents.defaults.memorySearch.provider local
openclaw config set agents.defaults.memorySearch.local.modelPath 'hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf'
openclaw config set agents.defaults.memorySearch.fallback none
openclaw config set agents.defaults.memorySearch.extraPaths '["bank","OBSERVATIONS.md","REFFLECTIONS.md"]'

openclaw memory index --force --verbose
openclaw memory status --deep
```

Notes:
- Use a model path supported by your local embedding stack.
- On WSL, you may see Vulkan incompatibility warnings and CPU fallback from `node-llama-cpp`; this is expected unless GPU backend support is configured.
- If local runtime is unavailable, this path will still fail.

## Validation Command

Run:

```bash
REPO_DIR=/home/juanbeck/Watson scripts/openclaw/mainpc-om-validation.sh
```

Exit codes:
- `0`: success
- `1`: command failures encountered
- `2`: `openclaw` missing
- `3`: blocker detected (for example missing embedding provider)

## Security Notes

- Ensure credential directory is private:
  - `chmod 700 ~/.openclaw/credentials`
- If gateway auth tokens were exposed during debugging, rotate them:
  - `openclaw gateway token rotate`
- If local small-model fallbacks remain enabled, harden sandbox/tool policy:
  - `openclaw config set agents.defaults.sandbox.mode all`
  - `openclaw config set tools.deny '["group:web","browser"]'`
