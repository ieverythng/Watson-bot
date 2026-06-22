# Watson Stack Harness Report — ctx128000-fixed2400

Generated: `2026-06-22T02:01:14.251829+00:00`
Base URL: `http://172.24.16.1:8080/v1`
Model: `qwen36-turbo-hermes`
Git: `feat/Foundations_OM_Skills` @ `fe08e55`

## Endpoint checks

| Check | Status | Elapsed s | OK |
|---|---:|---:|---|
| models | 200 | 0.005 | True |
| headroom | 200 | 0.203 | True |

## Context / throughput

| Target ctx | Status | Elapsed s | Est completion tok/s | Alpha | Omega |
|---:|---:|---:|---:|---|---|
| 2400 | 200 | 20.971 | 2.098 | True | True |

## Tool fidelity

| Test | JSON valid | Tool correct | Elapsed s |
|---|---|---|---:|
| select_read_file | True | True | 8.818 |

## Acceptance

- Result: **PASS** for all executed rows.
- Decode speed median across context rows: `2.098` est tok/s.
