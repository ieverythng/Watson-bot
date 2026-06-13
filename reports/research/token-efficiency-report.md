# Token Efficiency Report — Oracle Offload Analysis

**Date:** 2026-06-13  
**Period:** Last 24 hours (Jun 12–13)  

---

## Session Overview

| Metric | Value |
|--------|-------|
| Total sessions | 65 |
| Total messages | 1,032 |
| Total tool calls | 394 |
| Total tokens processed | ~29.4M |
| Active time | ~1 day |

## Model Breakdown

| Model | Sessions | Tokens | % of Total | Role |
|-------|----------|--------|------------|------|
| **qwen36-turbo-hermes** | 52 | 28,440,832 | **96.7%** | Front model (coordination) |
| **gpt-5-4-thinking** | 1 | 407,145 | 1.4% | Heavy reasoning task |
| **gpt-5-5-thinking** | 2 | 282,142 | 1.0% | Oracle consultations |
| **gpt-5.5** | 8 | 266,731 | 0.9% | Delegated expert tasks |
| **gpt-5.4-mini** | 1 | 20,455 | 0.1% | Vision/auxiliary |

## The Oracle Efficiency Pattern

### What Happened

The Kickbacks.ai research session used a **two-tier reasoning pattern**:

1. **Front model (qwen36-turbo-hermes)** handled:
   - Web research (search, extract, GitHub analysis)
   - File operations (read/write/patch)
   - Coordination and delegation
   - Context management

2. **Oracle (gpt-5-5-thinking)** handled:
   - Strategic revenue analysis (1 call, ~150K tokens)
   - Architecture decisions (1 call, ~130K tokens)

### Why This Is Efficient

**Without Oracle offload**, the front model would have needed to:
- Reason through all 6 strategic questions itself (~50K+ output tokens)
- Include that reasoning in context window for subsequent turns
- Trigger context compression sooner due to bloat
- Lose detail during compression

**With Oracle offload:**
- Front model sends concise prompt (~4K input tokens)
- Oracle returns synthesized answer (~150K tokens, but NOT in front context)
- Front model gets a **compact summary** to work with
- Context stays clean, fewer compressions triggered

### Token Savings Estimate

```
Without Oracle:  ~50K output tokens + compression overhead = ~75K effective tokens
With Oracle:     ~4K prompt + ~2K summary in context = ~6K effective tokens
Savings:         ~69K tokens saved in front model context (~92% reduction)
```

The Oracle costs ~150K tokens on its own pipeline, but those don't bloat the front model's context. The net effect is **cleaner reasoning and fewer compressions**.

## Compression Frequency

Looking at the session data:
- 65 sessions in 24 hours
- Longest session: 9h 18m (likely triggered multiple compressions)
- Average session: ~32 minutes (likely no compression needed)

**Pattern:** Short, focused sessions with Oracle offload = minimal compression. Long sessions without offload = frequent compression and detail loss.

## Recommendations for Token Efficiency

1. **Offload heavy reasoning to Oracle** — architecture decisions, strategic analysis, complex tradeoffs
2. **Keep front model lean** — use it for coordination, file ops, and acting on Oracle advice
3. **Short sessions > long sessions** — break work into focused blocks that don't trigger compression
4. **Track with `hermes insights`** — monitor token distribution across models weekly

## Top Tools Used (Efficiency Indicators)

| Tool | Calls | % | What It Means |
|------|-------|---|---------------|
| terminal | 257 | 65.2% | Heavy scripting/automation (good) |
| read_file | 25 | 6.3% | Context gathering (normal) |
| write_file | 20 | 5.1% | Document generation (normal) |
| web_search | 19 | 4.8% | Research (healthy) |
| delegate_task | 3 | 0.8% | Subagent delegation (low — could use more) |

**Insight:** Low delegation count (3) suggests the front model does most work itself. Increasing delegation to Oracle or subagents would further reduce context bloat.
