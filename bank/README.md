# Bank Layer

The `bank/` directory stores reflective, durable memory pages.
It is derived from episodic logs and observations, not a raw transcript dump.

## Layout

- `world.md`: stable facts about environment, systems, and constraints.
- `experience.md`: lessons learned from execution and outcomes.
- `opinions.md`: preferences and beliefs with confidence and evidence.
- `entities/`: per-entity pages with profile, preferences, and timeline.

## Writing Rules

- Keep entries short and explicit.
- Add evidence pointers for every durable claim.
- Prefer updates over duplication.
- Mark uncertainty with confidence.
