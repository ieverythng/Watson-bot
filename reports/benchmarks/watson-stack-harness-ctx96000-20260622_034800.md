# Watson Stack Harness Report — ctx96000

Generated: `2026-06-22T01:48:00.785349+00:00`
Base URL: `http://172.24.16.1:8080/v1`
Model: `qwen36-turbo-hermes`
Git: `feat/Foundations_OM_Skills` @ `fe08e55`

## Endpoint checks

| Check | Status | Elapsed s | OK |
|---|---:|---:|---|
| models | 200 | 0.004 | True |
| headroom | 200 | 0.752 | True |

## Context / throughput

| Target ctx | Status | Elapsed s | Est completion tok/s | Alpha | Omega |
|---:|---:|---:|---:|---|---|
| 2880 | 200 | 67.089 | 0.656 | True | True |

## Tool fidelity

| Test | JSON valid | Tool correct | Elapsed s |
|---|---|---|---:|
| select_read_file | True | True | 9.615 |

## Acceptance

- Result: **PASS** for all executed rows.
- Decode speed median across context rows: `0.656` est tok/s.
