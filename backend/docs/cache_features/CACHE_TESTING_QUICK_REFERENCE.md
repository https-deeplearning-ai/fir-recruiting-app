# Company Cache Testing - Quick Reference Card

**Goal:** Test company caching system in 10 minutes

---

## 🚀 Quick Start (3 Commands)

### 1. Check Database Schema (in Supabase SQL Editor)
```sql
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'company_lookup_cache' AND column_name = 'website';
```
**Expected:** `is_nullable = 'YES'` ✅

**If NO:** Apply fix first:
```sql
ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;
```

### 2. Monitor Logs (in terminal)
```bash
cd backend
./monitor_cache.sh watch
```

### 3. Run Test Searches (in UI)
- **First search:** "payment processing and payment gateway companies"
- **Second search:** Same exact query immediately

---

## 📊 What to Look For

### ✅ SUCCESS Indicators

**In backend logs during first search:**
```bash
[CACHE] ✅ Saved Stripe → 12345678     # Many of these
[CACHE] ✅ Saved PayPal → 87654321     # Should see ~70

💾 Cache Performance:
   Cache Hits: 0 (0.0% hit rate)       # Expected for first
   Cache Errors: 0                      # MUST be zero!
```

**In backend logs during second search:**
```bash
✅ [CACHE HIT] Stripe: ID=12345678     # All companies
✅ [CACHE HIT] PayPal: ID=87654321     # Should be hits

💾 Cache Performance:
   Cache Hits: 70 (100.0% hit rate)    # 🎉 PERFECT!
   💰 Credits Saved: 70 (~$7.00)        # Cost savings!
```

**Performance:**
- First search: 2-3 minutes
- Second search: **< 30 seconds** (10x faster!)

### ❌ FAILURE Indicators

**The bug (constraint violation):**
```bash
[CACHE] ❌ Failed to save Acme: 400 {"code":"23502"...}
```
→ Schema fix not applied. Run ALTER TABLE command above.

**Zero cache hits on repeat search:**
```bash
💾 Cache Performance:
   Cache Hits: 0 (0.0% hit rate)    # Should be 100%!
```
→ Cache not saving. Check Phase 2 verification queries.

---

## 🔍 Verification Queries (in Supabase)

### After First Search - Check Saves
```sql
-- How many companies saved?
SELECT COUNT(*) FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
-- Expected: ~70

-- Are NULL websites allowed? (THE PROOF)
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    ROUND((SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as pct
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
-- Expected: ~90% NULL websites (proves fix works!)
```

### Overall Cache Health
```sql
SELECT
    COUNT(*) as total,
    ROUND(AVG(CASE WHEN lookup_successful THEN confidence::numeric END), 2) as avg_confidence,
    ROUND((SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as null_pct
FROM company_lookup_cache;
-- Expected: avg_confidence > 0.90, null_pct ~90%
```

---

## 🎯 Success Criteria Checklist

| Metric | Target | Pass? |
|--------|--------|-------|
| Cache save success rate | > 95% | ☐ |
| Cache hit rate (2nd search) | 100% | ☐ |
| Cache errors | 0 | ☐ |
| NULL websites in DB | ~90% | ☐ |
| Cost savings (2nd search) | ~$7 | ☐ |
| Speed improvement | 10x | ☐ |

**Overall:** ☐ Pass ☐ Fail

---

## 🛠️ Helper Scripts

### Monitor cache in real-time:
```bash
./monitor_cache.sh watch    # Live monitoring
./monitor_cache.sh summary  # Recent activity summary
./monitor_cache.sh test     # Quick test verification
```

### Manual log monitoring:
```bash
tail -f /tmp/backend_test.log | grep -E "CACHE|Cache Performance|💰"
```

---

## 📁 Reference Files

| File | Purpose |
|------|---------|
| `CACHE_TESTING_CHECKLIST.md` | Detailed step-by-step checklist |
| `CACHE_TESTING_QUERIES.sql` | All SQL verification queries |
| `monitor_cache.sh` | Log monitoring script |
| `HANDOFF_COMPANY_CACHING.md` | Complete implementation details |
| `COMPANY_CACHING_ARCHITECTURE.md` | System architecture docs |

---

## 🚨 Quick Troubleshooting

**Problem:** High save failures (> 10%)
```sql
-- Fix: Remove NOT NULL constraint
ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;
```

**Problem:** Session stuck as "running"
```sql
-- Fix: Clear stuck sessions
UPDATE company_research_sessions SET status = 'failed'
WHERE status = 'running' AND created_at < NOW() - INTERVAL '1 hour';
```

**Problem:** Zero cache hits on second search
1. Check if first search saved companies (run verification query above)
2. Ensure using EXACT same search query
3. Check backend logs for save errors

---

## 💡 Pro Tips

1. **Always run EXACT same query** for second search to test cache hits
2. **Watch the logs** during searches - immediate feedback
3. **Check NULL websites in DB** - proves schema fix is working
4. **Compare durations** - should see 10x speedup on second search
5. **Run `./monitor_cache.sh test`** - quick automated verification

---

## 📈 Expected Results Timeline

**First Search (Cold Cache):**
- ⏱️ Duration: 2-3 minutes
- 🔍 Cache hits: 0%
- 💾 Saves: ~70 companies
- 💰 Savings: $0

**Second Search (Warm Cache):**
- ⏱️ Duration: < 30 seconds ⚡
- 🔍 Cache hits: 100% 🎉
- 💾 Saves: 0 (all cached)
- 💰 Savings: ~$7 💸

**Monthly Projection:**
- Without cache: $350/month
- With cache: ~$10-20/month
- **Savings: $330-340/month (94-97% reduction)**

---

**Last Updated:** November 13, 2025
**Version:** 1.0
