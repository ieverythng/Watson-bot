# Kickbacks.ai Revenue Loop — Operating Procedure

**Recipe ID:** kickbacks-revenue-loop  
**Version:** 1.0  
**Created:** 2026-06-13  
**Domain:** revenue-optimization  

## Overview

Systematic procedure for generating passive revenue through kickbacks.ai — an ad marketplace that displays sponsored content during AI coding assistant wait states. Users earn 50% of ad revenue per impression (≥5 second view) and per click (50× impression value).

## Prerequisites

- VS Code installed on Windows host with Kickbacks.ai extension
- Claude Code CLI ≥2.1.143 (`npm update -g @anthropic-ai/claude-code`)
- Codex CLI installed (`npm install -g @openai/codex`)
- Google account for kickbacks.ai authentication
- Stripe Connect configured for payouts ($10 threshold)

## Procedure

### Phase 1: Setup (One-Time)

1. **Install Kickbacks extension**
   ```
   VS Code → Extensions → Search "Kickbacks" → Install
   ```

2. **Authenticate**
   - Click "Kickbacks: Sign in" in VS Code status bar
   - Complete Google OAuth flow
   - Verify account at https://kickbacks.ai/me

3. **Verify surfaces**
   - Status bar shows: `Kickbacks ($0.00 today · $0.00)`
   - NOT "Kickbacks incompatible" or "Kickbacks offline"
   - Open debug log: status bar → "Open Debug Log"

4. **Create revenue workspace**
   - Dedicated VS Code profile to minimize extension conflicts
   - Install Claude Code and Codex VS Code extensions
   - Keep Kickbacks as the only ad-related extension

### Phase 2: Daily Revenue Loop

#### Morning Setup (10 min)

1. Launch VS Code with revenue workspace
2. Open Claude Code panel → start a session
3. Open Codex panel → start a session (optional, doubles surfaces)
4. In WSL terminal: `claude` to start CLI session
5. Verify all 3 surfaces show Kickbacks ads during thinking states

#### Session Execution (4-6 hours total)

**Session A — High-Value Work (2-3 hours)**
1. Queue complex prompts that trigger extended AI thinking:
   - Multi-file refactors on iTrack-Supply-Chain
   - Documentation generation for existing codebases
   - Test suite creation for modules lacking coverage
2. Let each AI response complete fully — don't interrupt spinner
3. Review output → submit next prompt → repeat
4. Expected: 40-80 impressions per session

**Session B — CLI Batch Tasks (1-2 hours)**
1. Run Claude Code CLI for batch operations:
   ```bash
   claude --prompt "Generate comprehensive test suite for /path/to/module"
   claude --prompt "Write API documentation for /path/to/service"
   ```
2. Each CLI invocation generates status-bar + spinner verb impressions
3. Expected: 20-40 impressions per session

**Session C — Feature Development (1-2 hours)**
1. Mix of VS Code panel and CLI work
2. Focus on multi-file operations that require extended AI processing
3. Expected: 30-50 impressions per session

#### End-of-Day Audit (15 min)

1. Check Kickbacks status bar for daily earnings
2. Copy today's data to `reports/expenditure/kickbucks-ledger-YYYY-MM-DD.md`
3. Note any flakiness in the "Flakiness Log" section
4. Plan next day's high-impression tasks

### Phase 3: Weekly Review (30 min)

1. Calculate revenue per hour of AI thinking time
2. Identify best-performing prompt types (most impressions per minute)
3. Check kickbacks.ai/me for ledger reconciliation
4. Adjust strategy: double down on high-yield activities, drop low-yield ones
5. Update `reports/research/kickbacks-revenue-loop.html` with new data

## Quality Gates

- [ ] All 3 surfaces (panel, CLI status bar, CLI spinner) rendering ads
- [ ] Daily ledger entry created before end of day
- [ ] No flakiness incidents unresolved for >24 hours
- [ ] Monthly reconciliation completed within 3 days of payout date
- [ ] Revenue per hour trending stable or improving

## Pitfalls

### Flakiness Causes
- **VS Code panel minimized:** Ads don't render if panel is hidden → keep panels visible
- **Network interruptions:** Extension loses connection to kickbacks.ai backend → check "Kickbacks offline" status
- **Claude Code version too old:** Spinner verb ads require ≥2.1.143 → update regularly
- **Extension conflicts:** Other extensions modifying the same UI elements → use dedicated workspace

### Fraud Risks (DO NOT)
- ❌ Run scripted prompts solely to generate impressions
- ❌ Use headless VS Code or automated click scripts
- ❌ Create multiple accounts on the same machine
- ❌ Interrupt spinner before 5 seconds to "reset" impressions

### Safe Practices (DO)
- ✅ Generate impressions as a side effect of real coding work
- ✅ Run parallel sessions on different machines under one account
- ✅ Click ads that are genuinely relevant
- ✅ Keep panels open and visible during AI thinking time

## Metrics to Track

| Metric | Target | Where Tracked |
|--------|--------|---------------|
| Impressions per session | 30-60 | Daily ledger |
| Revenue per hour | $5-15/hr | Weekly review |
| Click-through rate | 1-2% | kickbacks.ai/me |
| Flakiness incidents | <2/week | Daily ledger |
| Monthly revenue | $35-75 | Monthly reconciliation |

## Related Documents

- Implementation plan: `reports/research/kickbacks-revenue-loop.html`
- Ledger template: `reports/expenditure/kickbucks-ledger-template.md`
- Platform docs: https://kickbacks.ai/terms, https://github.com/andrewmccalip/kickbacks.ai
