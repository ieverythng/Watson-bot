# Local Model Inventory

Generated: `2026-06-22T00:56:34.621541+00:00`

Read-only inventory of GGUF files visible from WSL for local supervisor/subagent routing plans.

## GGUF models

| Model | Size GiB | Quant | Role hint | Path |
|---|---:|---|---|---|
| `LFM2-8B-A1B-Q4_K_M.gguf` | 4.698 | `Q4_K_M` | main/candidate | `D:\MODELS\LFM2-8B-A1B-Q4_K_M.gguf` |
| `Qwen3.6-27B-DFlash-IQ4_XS.gguf` | 0.87 | `IQ4_XS` | draft/spec | `D:\MODELS\Qwen3.6-27B-DFlash-IQ4_XS.gguf` |
| `Qwen3.6-27B-MTP-pi-tune-Q3_K_M.gguf` | 12.604 | `Q3_K_M` | main/candidate | `D:\MODELS\Qwen3.6-27B-MTP-pi-tune-Q3_K_M.gguf` |
| `Qwen3.6-27B-Q3_K_M.gguf` | 12.653 | `Q3_K_M` | main/candidate | `D:\MODELS\Qwen3.6-27B-Q3_K_M.gguf` |
| `Qwopus3.6-27B-v2-Q3_K_M.gguf` | 12.574 | `Q3_K_M` | main/candidate | `D:\MODELS\Qwopus-VL-3.6-27B-Q3_K_M\Qwopus3.6-27B-v2-Q3_K_M.gguf` |
| `mmproj-F32.gguf` | 0.867 | `unknown` | projector | `D:\MODELS\Qwopus-VL-3.6-27B-Q3_K_M\mmproj-F32.gguf` |
| `locate-anything-q8_0.gguf` | 5.83 | `Q8_0` | main/candidate | `D:\MODELS\locate-anything-q8_0.gguf` |

## Immediate routing notes

- `Qwen3.6-27B-Q3_K_M.gguf` remains the safest supervisor/front model candidate.
- `Qwen3.6-27B-DFlash-IQ4_XS.gguf` is a draft/speculative model, not an independent coding subagent model.
- `Qwopus3.6-27B-v2-Q3_K_M.gguf` is a vision-capable 27B candidate when paired with its `mmproj` file.
- If Vibecoder/Gemma do not appear above, they were not visible in the scanned roots; rerun with `--root` pointing to their location.
