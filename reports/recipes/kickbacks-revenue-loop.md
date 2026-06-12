# Kickbacks.ai Revenue Loop — Operating Procedure

**Recipe ID:** kickbacks-revenue-loop  
**Version:** 2.0  
**Created:** 2026-06-13  
**Domain:** revenue-optimization  

## Overview

Systematic procedure for generating passive revenue through kickbacks.ai — an ad marketplace that displays sponsored content during AI coding assistant wait states. Users earn 50% of ad revenue per impression (≥5 second view) and per click (50× impression value).

**Revenue rates:** ~$0.0125/impression, ~$0.625/click at current top bid ($25/1k).  
**Payout threshold:** $10 via Stripe Connect Express.  
**Realistic monthly income:** $50–$100 given known bugs.

## Prerequisites

- VS Code installed on Windows host with Kickbacks.ai extension
- Claude Code CLI ≥2.1.143 (you have v2.1.175 ✓)
- Google account for kickbacks.ai authentication
- Stripe Connect configured for payouts ($10 threshold)
- Watchdog script deployed: `scripts/kickbacks-watchdog.sh`

## Known Bugs & Mitigations

| Bug | Impact | Mitigation |
|-----|--------|------------|
| Kill wedge deadlock (#48) | 100% impression loss until reload | Watchdog auto-recovery + manual reload |
| Codex "target not found" (#55) | Codex panel surface broken | Use Claude Code surfaces only |
| Ads display, no credit (#52) | Unpredictable revenue loss | Monitor kickbacks.ai/me ledger daily |

## Procedure

### Phase 1: Setup (One-Time)

1. **Install Kickbacks extension** (Windows VS Code)
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

4. **Deploy watchdog**
   ```bash
   # Add to crontab (every 5 minutes):
   */5 * * * * /home/juanbeck/Watson/scripts/kickbacks-watchdog.sh >> /home/juanbeck/Watson/reports/expenditure/kickbacks-watchdog.log 2>&1
   ```

### Phase 2: Daily Revenue Loop

#### Morning Setup (10 min)

1. Launch VS Code with Kickbacks extension active
2. Open Claude Code panel → start a session
3. In WSL terminal: `claude` to start CLI session (secondary surface)
4. Verify ads render in both surfaces during thinking states
5. Check watchdog is running: `tail -f reports/expenditure/kickbacks-watchdog.log`

#### Session Execution (4-6 hours total)

**Session A — Primary Surface: Claude Code Panel (2-3 hours)**
1. Queue complex prompts that trigger extended AI thinking:
   - Multi-file refactors on iTrack-Supply-Chain
   - Documentation generation for existing codebases
   - Test suite creation for modules lacking coverage
2. Let each AI response complete fully — don't interrupt spinner before 5 seconds
3. Keep Claude Code panel visible and in focus
4. Expected: 15-30 impressions per hour

**Session B — Secondary Surface: Claude Code CLI (1-2 hours)**
1. Run Claude Code CLI for batch operations:
   ```bash
   claude --prompt "Generate comprehensive test suite for /path/to/module"
   claude --prompt "Write API documentation for /path/to/service"
   ```
2. Each CLI invocation generates status-bar + spinner verb impressions
3. Expected: 20-40 impressions per hour

**Session C — Feature Development (1-2 hours)**
1. Mix of VS Code panel and CLI work
2. Focus on multi-file operations that require extended AI processing
3. Expected: 30-50 impressions per session

#### End-of-Day Audit (15 min)

1. Check Kickbacks status bar for daily earnings
2. Copy today's data to `reports/expenditure/kickbacks-ledger-YYYY-MM-DD.md`
3. Note any flakiness in the "Flakiness Log" section
4. Check watchdog log: `tail reports/expenditure/kickbacks-watchdog.log`
5. Plan next day's high-impression tasks

### Phase 3: Weekly Review (30 min)

1. Calculate revenue per hour of AI thinking time
2. Identify best-performing prompt types (most impressions per minute)
3. Check kickbacks.ai/me for ledger reconciliation
4. Adjust strategy: double down on high-yield activities, drop low-yield ones
5. Update `reports/research/kickbacks-revenue-loop.html` with new data

## Quality Gates

- [ ] Claude Code panel surface rendering ads consistently
- [ ] Claude Code CLI spinner verb + status bar both active
- [ ] Watchdog running and detecting kill wedge events
- [ ] Daily ledger entry created before end of day
- [ ] No flakiness incidents unresolved for >24 hours
- [ ] Monthly reconciliation completed within 3 days of payout date

## Pitfalls

### Flakiness Causes (Documented)
- **Kill wedge deadlock (#48):** Extension permanently stops showing ads. Fix: `Developer: Reload Window` or wait for watchdog.
- **Codex panel broken (#55):** "target not found" — skip Codex surface entirely until patched.
- **Impression tracking failure (#52):** Ads show but no credit. Monitor kickbacks.ai/me daily.
- **Panel minimized:** Ads don't render if panel is hidden → keep panels visible.
- **Network interruptions:** Extension loses connection to backend → check "Kickbacks offline" status.

### Fraud Risks (DO NOT)
- ❌ Run scripted prompts solely to generate impressions
- ❌ Use headless VS Code or automated click scripts
- ❌ Create multiple accounts on the same machine
- ❌ Interrupt spinner before 5 seconds to "reset" impressions
- ❌ Click your own ads

### Safe Practices (DO)
- ✅ Generate impressions as a side effect of real coding work
- ✅ Run parallel sessions (panel + CLI) during natural workflows
- ✅ Click ads that are genuinely relevant
- ✅ Keep panels open and visible during AI thinking time
- ✅ Deploy watchdog to minimize kill wedge downtime

## Metrics to Track

| Metric | Target | Where Tracked |
|--------|--------|---------------|
| Impressions per session | 30-60 | Daily ledger |
| Revenue per hour | $2-10/hr | Weekly review |
| Click-through rate | 1-2% | kickbacks.ai/me |
| Kill wedge incidents | <2/week | Watchdog log |
| Monthly revenue | $50-100 | Monthly reconciliation |

## Related Documents

- Implementation plan: `reports/research/kickbacks-revenue-loop.html`
- Ledger template: `reports/expenditure/kickbucks-ledger-template.md`
- Watchdog script: `scripts/kickbacks-watchdog.sh`
- Platform docs: https://kickbacks.ai, https://github.com/andrewmccalip/kickbacks.ai
