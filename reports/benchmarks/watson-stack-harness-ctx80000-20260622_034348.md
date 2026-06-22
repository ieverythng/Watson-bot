# Watson Stack Harness Report — ctx80000

Generated: `2026-06-22T01:43:48.767610+00:00`
Base URL: `http://172.24.16.1:8080/v1`
Model: `qwen36-turbo-hermes`
Git: `feat/Foundations_OM_Skills` @ `fe08e55`

## Endpoint checks

| Check | Status | Elapsed s | OK |
|---|---:|---:|---|
| models | 200 | 0.002 | True |
| headroom | 200 | 0.232 | True |

## Context / throughput

| Target ctx | Status | Elapsed s | Est completion tok/s | Alpha | Omega |
|---:|---:|---:|---:|---|---|
| 2400 | 200 | 51.41 | 0.856 | True | True |

## Tool fidelity

| Test | JSON valid | Tool correct | Elapsed s |
|---|---|---|---:|
| select_read_file | True | True | 9.478 |

## Acceptance

- Result: **PASS** for all executed rows.
- Decode speed median across context rows: `0.856` est tok/s.
