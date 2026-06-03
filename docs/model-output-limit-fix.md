# Model Output Token Limit Fix

## Problem
Hermes Agent was hitting model output token limits during long autonomous runs or file generations. The issue was that `max_tokens` (output limit) was not being configured for local llama.cpp/Qwen models, causing the API to use default limits that were too restrictive.

## Root Cause
- Anthropic models have hardcoded output limits in `agent/anthropic_adapter.py`
- Local/custom models (like qwen3.5-27b via llama.cpp) had no configured limit
- When `max_tokens=None`, the API uses its own default (often 8192 or lower)
- This caused truncation during long code generation, file operations, or complex tasks

## Solution

### 1. Configured Output Limit in config.yaml
Added `max_tokens: 16384` to the model configuration:

```yaml
model:
  default: qwen35-27b-q3km
  provider: watson-llama
  base_url: http://172.24.16.1:8080/v1
  max_tokens: 16384  # Qwen3.5-27B can output up to ~16K tokens
```

**Why 16384?**
- Qwen3.5-27B has a 32K context window
- Typical safe output limit is 50% of context = 16K
- Can be adjusted based on your needs (8192, 16384, 32768)

### 2. Updated CLI Agent Initialization
Modified `cli.py` to read `max_tokens` from config and pass it to AIAgent:

```python
# Read max_tokens from config.yaml model section if not explicitly set
max_tokens = getattr(self, 'max_tokens', None)
if max_tokens is None and hasattr(self, '_config') and isinstance(self._config, dict):
    model_cfg = self._config.get("model", {})
    if isinstance(model_cfg, dict):
        max_tokens = model_cfg.get("max_tokens")
```

### 3. Updated Gateway (Discord/Telegram) Agent Initialization
Modified `gateway/run.py` to read config and pass `max_tokens`:

```python
# Read max_tokens from config.yaml model section
max_tokens = None
try:
    from hermes_cli.config import load_config
    _cfg = load_config()
    model_cfg = _cfg.get("model", {})
    if isinstance(model_cfg, dict):
        max_tokens = model_cfg.get("max_tokens")
except Exception:
    pass

agent = AIAgent(
    model=turn_route["model"],
    **turn_route["runtime"],
    max_tokens=max_tokens,  # Added
    ...
)
```

### 4. Updated Cron Job Agent Initialization
Modified `cron/scheduler.py` to read `max_tokens` from config:

```python
agent = AIAgent(
    model=turn_route["model"],
    ...
    max_tokens=_cfg.get("model", {}).get("max_tokens") if isinstance(_cfg.get("model"), dict) else None,
    ...
)
```

## Files Modified
1. `/home/juanbeck/.hermes/config.yaml` - Added `max_tokens: 16384`
2. `/home/juanbeck/.hermes/hermes-agent/cli.py` - Read config and pass to AIAgent
3. `/home/juanbeck/.hermes/hermes-agent/gateway/run.py` - Read config and pass to AIAgent
4. `/home/juanbeck/.hermes/hermes-agent/cron/scheduler.py` - Read config and pass to AIAgent

## Testing
To verify the fix works:

```bash
# Test with a long code generation task
cd /home/juanbeck/Watson
python3 scripts/test_output_limit.py

# Or run a complex file operation
hermes "Generate a comprehensive Python script that implements a REST API with authentication, database models, and documentation"
```

## Adjusting the Limit

If you need to change the output limit:

1. Edit `/home/juanbeck/.hermes/config.yaml`:
   ```yaml
   model:
     max_tokens: 32768  # Change to desired value
   ```

2. Restart any running Hermes sessions

## Notes
- The limit applies to **output tokens only** (model's response)
- Input context window is separate (Qwen3.5-27B supports 32K input)
- If you're still hitting limits, increase the value or check llama.cpp server settings on Windows
