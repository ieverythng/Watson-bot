# Recipe 03 - Skills Authoring Standard

## Purpose
Create lean, reusable skills that are easy to trigger, audit, and extend.

## Folder Convention
Use one folder per skill:

`skills/<skill-name>/SKILL.md`

Do not create extra README or changelog files for a skill unless the skill truly needs scripts or references.

## Required File Format
Each `SKILL.md` must start with YAML frontmatter:

```yaml
---
name: skill-name
description: Clear trigger description that says when the skill should be used.
---
```

## Required Sections
Each skill must include these sections in this order:
- `When to Use`
- `Inputs`
- `Steps`
- `Outputs`
- `Failure Handling`
- `Examples`

## Writing Rules
- Keep the description specific enough to trigger correctly.
- Keep steps deterministic and tied to repo paths.
- Prefer explicit schemas and short examples over long prose.
- Default to the current workspace only.
- State what the skill must not do when that boundary matters.
- If exact values are often unavailable, specify the fallback estimate format.

## Optional Extensions
Add extra files only when they reduce repeat work:
- `scripts/` for deterministic helpers
- `references/` for material too large for `SKILL.md`

## Standard Template

```md
---
name: example-skill
description: Use this skill when ...
---

# Example Skill

## When to Use
- ...

## Inputs
- ...

## Steps
1. ...

## Outputs
- ...

## Failure Handling
- ...

## Examples
- ...
```
