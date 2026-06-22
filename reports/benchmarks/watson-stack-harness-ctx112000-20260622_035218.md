# Watson Stack Harness Report — ctx112000

Generated: `2026-06-22T01:52:18.488672+00:00`
Base URL: `http://172.24.16.1:8080/v1`
Model: `qwen36-turbo-hermes`
Git: `feat/Foundations_OM_Skills` @ `fe08e55`

## Endpoint checks

| Check | Status | Elapsed s | OK |
|---|---:|---:|---|
| models | 200 | 0.003 | True |
| headroom | 200 | 2.466 | True |

## Context / throughput

| Target ctx | Status | Elapsed s | Est completion tok/s | Alpha | Omega |
|---:|---:|---:|---:|---|---|
| 3360 | 200 | 88.522 | 0.497 | True | True |

## Tool fidelity

| Test | JSON valid | Tool correct | Elapsed s |
|---|---|---|---:|
| select_read_file | True | True | 9.886 |

## Acceptance

- Result: **PASS** for all executed rows.
- Decode speed median across context rows: `0.497` est tok/s.
