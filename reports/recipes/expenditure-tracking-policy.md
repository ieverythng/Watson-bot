# 💰 Expenditure Tracking Policy (WatsonOW)

## Purpose

Track token usage for Codex-based subagents while respecting local model costs. Provide visibility into spending without flooding with constant noise.

---

## 📊 Tracking Scope

### Track:
- ✅ **Codex model delegations** (`openai-codex/gpt-5.4`, `gpt-5.3`)
- ✅ **Session tokens** (input + output)
- ✅ **Hourly usage** via OpenAI API metrics endpoint
- ✅ **Weekly spend projections** to budget close

### Exclude:
- ❌ Local models (`ollama/qwen3.5:9b`, etc.) - already free
- ❌ Direct tool calls (read/write/edit/message) - no retry needed, instant cost
- ❌ Gateway overhead (minimal, not tracked)

---

## 🔄 Frequency

| Report Type | Schedule | Content |
|-------------|----------|-----------||
| **Token ledger** | Every subagent run | Session tokens used, model type |
| **Daily expenditure** | End of day (cron) | Summary + projections |
| **Hourly usage check** | Every 60 min (cron) | API-based metrics snapshot |
| **Weekly report** | Sunday noon | Full breakdown + budget status |

---

## 🎯 Budget Controls

### Enforced on Codex Delegations:
1. **Default max**: 2,000 tokens per subagent unless approved
2. **High-priority tasks**: May use up to 5k tokens with note in contract
3. **Escalation trigger**: >80% of remaining weekly budget → warning

### Contract Requirement (Codex-only):
```markdown
Budget expectation: One Codex task, no more than N follow-up revisions  
Token cap: 2000 tokens unless escalation approved  
Model tier: codex  
Reason for delegation: Speed/specialization justifies cost  
```

---

## 📈 Visibility Tools

### Daily Report Format:
```markdown
# 💰 Expenditure Report - 2026-03-17
## Summary
- **Hourly Spend **(Today) $N
- **Weekly Spend**: 30% (to close of week)
- **Model Used**: openai-codex

## Token Usage
| Time | Subagent | Tokens | Cost |
|------|-------|-------||-------||
| 02:15 | nao-ros-check | ~4,500 | $N.NN |
```

### CLI Dashboard (Future):
```bash
$ watson-expenditure status --model codex --since today
Hourly spend: $N.NN  
Weekly remaining: N%  
Budget alert: ⚠️ Warning at 80% threshold
```

---

## 📁 Output Locations

- Daily ledger: `reports/expenditure/ledger-YYYY-MM-DD.md`
- Hourly snapshots: `reports/expenditure/hourly-N.json`
- Weekly reports: `reports/research/watson-expenditure-week-N.md`

---

## 🔗 Delegation Contract Enforcement

All Codex-based delegation contracts must include:

```markdown
Budget expectation: One Codex task, no more than N follow-up revisions
Token cap: 2000 tokens unless escalation approved
Model tier: codex
Escalation triggers: If token usage exceeds budget or acceptance fails
```

---

## 🚀 Implementation Status

- ✅ Cron job: Hourly sweep + expenditure updates
- ✅ Daily ledger generator: Creates reports in correct format
- ✅ Token tracking script: Placeholder for API calls
- ⏳ Delegation contract enforcement: Updates pending
- ⏳ CLI dashboard: Future enhancement

---

*Policy last updated: 2026-03-17*  
*Author: WatsonOW-Memory*
