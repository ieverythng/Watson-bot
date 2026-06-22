# Watson Stack Harness Report — baseline-65k-reasoning-off

Generated: `2026-06-22T01:37:12.248703+00:00`
Base URL: `http://172.24.16.1:8080/v1`
Model: `qwen36-turbo-hermes`
Git: `feat/Foundations_OM_Skills` @ `fe08e55`

## Endpoint checks

| Check | Status | Elapsed s | OK |
|---|---:|---:|---|
| models | 200 | 0.003 | True |
| headroom | 200 | 0.2 | True |

## Context / throughput

| Target ctx | Status | Elapsed s | Est completion tok/s | Alpha | Omega |
|---:|---:|---:|---:|---|---|
| 0 | 200 | 5.777 | 6.058 | False | False |
| 2048 | 200 | 40.977 | 1.074 | True | True |
| 8192 | 200 | 162.279 | 0.271 | True | True |

## Tool fidelity

| Test | JSON valid | Tool correct | Elapsed s |
|---|---|---|---:|
| select_read_file | True | True | 9.075 |

## Acceptance

- Result: **PASS** for all executed rows.
- Decode speed median across context rows: `1.074` est tok/s.
