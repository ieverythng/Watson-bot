#!/usr/bin/env python3
"""Inventory local GGUF models for WatsonOW routing plans.

Scans mounted Windows model directories (default: /mnt/d/MODELS) and emits
compact Markdown or JSON. Read-only and safe while llama.cpp/Hermes are active.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

KEYWORDS = ("vibe", "vibecoder", "gemma", "qwen", "qwopus", "dflash", "llama", "lfm")


def gib(n: int) -> float:
    return round(n / (1024**3), 3)


def quant_from_name(name: str) -> str:
    upper = name.upper()
    for token in ("IQ4_XS", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "F16", "BF16"):
        if token in upper:
            return token
    return "unknown"


def windows_guess(p: Path) -> str | None:
    s = str(p)
    if s.startswith("/mnt/d/"):
        return s.replace("/mnt/d/", "D:/").replace("/", "\\")
    if s.startswith("/mnt/c/"):
        return s.replace("/mnt/c/", "C:/").replace("/", "\\")
    return None


def scan(paths: list[Path]) -> dict:
    models = []
    missing_roots = []
    for root in paths:
        if not root.exists():
            missing_roots.append(str(root))
            continue
        for p in sorted(root.rglob("*.gguf")):
            lower = p.name.lower()
            models.append(
                {
                    "path": str(p),
                    "windows_path_guess": windows_guess(p),
                    "name": p.name,
                    "size_gib": gib(p.stat().st_size),
                    "quant": quant_from_name(p.name),
                    "is_projector": lower.startswith("mmproj"),
                    "matched_keywords": [k for k in KEYWORDS if k in lower],
                }
            )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roots": [str(p) for p in paths],
        "missing_roots": missing_roots,
        "models": models,
    }


def markdown(data: dict) -> str:
    lines = [
        "# Local Model Inventory",
        "",
        f"Generated: `{data['generated_at']}`",
        "",
        "Read-only inventory of GGUF files visible from WSL for local supervisor/subagent routing plans.",
        "",
    ]
    if data["missing_roots"]:
        lines += ["## Missing scan roots", ""] + [f"- `{p}`" for p in data["missing_roots"]] + [""]
    lines += ["## GGUF models", "", "| Model | Size GiB | Quant | Role hint | Path |", "|---|---:|---|---|---|"]
    for m in data["models"]:
        role = "projector" if m["is_projector"] else ("draft/spec" if "dflash" in m["name"].lower() else "main/candidate")
        path = m["windows_path_guess"] or m["path"]
        lines.append(f"| `{m['name']}` | {m['size_gib']} | `{m['quant']}` | {role} | `{path}` |")
    if not data["models"]:
        lines.append("| _none found_ | | | | |")
    lines += [
        "",
        "## Immediate routing notes",
        "",
        "- `Qwen3.6-27B-Q3_K_M.gguf` remains the safest supervisor/front model candidate.",
        "- `Qwen3.6-27B-DFlash-IQ4_XS.gguf` is a draft/speculative model, not an independent coding subagent model.",
        "- `Qwopus3.6-27B-v2-Q3_K_M.gguf` is a vision-capable 27B candidate when paired with its `mmproj` file.",
        "- If Vibecoder/Gemma do not appear above, they were not visible in the scanned roots; rerun with `--root` pointing to their location.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", help="Model root to scan; repeatable. Default: /mnt/d/MODELS")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    ap.add_argument("--out", help="Write output to file as well as stdout")
    args = ap.parse_args()
    roots = args.root or ["/mnt/d/MODELS"]
    data = scan([Path(p) for p in roots])
    text = json.dumps(data, indent=2) + "\n" if args.json else markdown(data)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
