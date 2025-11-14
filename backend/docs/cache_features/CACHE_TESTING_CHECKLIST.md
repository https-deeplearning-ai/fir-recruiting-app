# Company Cache Testing Checklist

**Goal:** Verify the two-tier company caching system is working correctly after database schema fix.

**Estimated Time:** 15-20 minutes

---

## 📋 Pre-Test Setup

- [ ] Backend running on port 5001
- [ ] Frontend accessible
- [ ] Supabase SQL Editor open
- [ ] Terminal open for monitoring logs

**Log Monitoring Command:**
```bash
# Run this in a terminal to watch cache activity in real-time
tail -f /tmp/backend_test.log | grep -E "CACHE|Looking up|Cache Performance|💰"
```

---

## ✅ Phase 1: Pre-Flight Check (2 minutes)

### Step 1.1: Verify Database Schema Fix

**In Supabase SQL Editor, run:**
```sql
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'company_lookup_cache'
    AND column_name = 'website';
```

**Expected Result:**
```
column_name | is_nullable
website     | YES         ✅
```

- [ ] ✅ `is_nullable = 'YES'` (fix applied)
- [ ] ❌ `is_nullable = 'NO'` → **STOP! Apply fix first:**
  ```sql
  ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;
  ```

### Step 1.2: Check Baseline Cache State

**In Supabase SQL Editor, run:**
```sql
SELECT
    COUNT(*) as total_entries,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    MAX(created_at) as newest_entry
FROM company_lookup_cache;
```

**Record baseline:**
- [ ] Current total entries: ____________
- [ ] Current null_websites: ____________
- [ ] Newest entry timestamp: ____________

### Step 1.3: Clear Stuck Sessions

**In Supabase SQL Editor, run:**
```sql
UPDATE company_research_sessions
SET status = 'failed'
WHERE status IN ('running', 'in_progress')
    AND created_at < NOW() - INTERVAL '1 hour';
```

- [ ] Sessions cleared (or none stuck)

---

## 🧪 Phase 2: First Search - Cold Cache (5 minutes)

### Step 2.1: Start Search

**In UI, run company research with:**
```
Query: payment processing and payment gateway companies
```

- [ ] Search started (timestamp: ____________)
- [ ] Log monitoring active

### Step 2.2: Watch Backend Logs

**Look for these patterns:**

✅ **GOOD - Cache Saves Succeeding:**
```bash
   ⊗ [CACHE MISS] Stripe - executing 4-tier lookup...
      ✅ Found: ID=12345678 (tier 1, website)
   [CACHE] ✅ Saved Stripe → 12345678          ← LOOK FOR THIS!

   ⊗ [CACHE MISS] PayPal - executing 4-tier lookup...
      ✅ Found: ID=87654321 (tier 2, name)
   [CACHE] ✅ Saved PayPal → 87654321          ← LOOK FOR THIS!
```

- [ ] Seeing many `[CACHE] ✅ Saved` messages
- [ ] Minimal or zero `[CACHE] ❌ Failed` messages

❌ **BAD - The Bug Returns:**
```bash
   [CACHE] ❌ Failed to save Acme: 400 {"code":"23502"...}
```
- [ ] If seeing this → Schema fix not applied or reverted

### Step 2.3: Check Final Metrics

**At end of search, logs should show:**
```bash
💾 Cache Performance:
   Cache Hits: 0 (0.0% hit rate)              ← Expected for 1st search
   Cache Misses: 70                           ← ~70 companies discovered
   Cache Errors: 0                            ← MUST BE ZERO!
   💰 Credits Saved: 0 (~$0.00 at $0.10/credit)
```

- [ ] ✅ Cache Errors: 0
- [ ] ✅ Cache Misses: ~60-80 (varies by query)
- [ ] ✅ Cache Hits: 0 (expected for first search)
- [ ] Search completed (timestamp: ____________)
- [ ] Duration: ____________ (should be 2-3 minutes)

### Step 2.4: Verify Database Saves

**In Supabase SQL Editor, run:**
```sql
SELECT COUNT(*) as companies_added_recently
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
```

- [ ] Result: ____________ companies (should be ~70)

**Check for NULL websites (THE PROOF):**
```sql
SELECT
    company_name,
    company_id,
    website,
    lookup_successful,
    confidence
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC
LIMIT 10;
```

- [ ] ✅ Many rows have `website = NULL` (this is normal and proves fix works!)
- [ ] ✅ Most have `lookup_successful = true`
- [ ] ✅ Confidence scores typically 0.90-1.00

### Step 2.5: Calculate Save Success Rate

**In Supabase SQL Editor, run:**
```sql
SELECT
    COUNT(*) as total_attempts,
    SUM(CASE WHEN lookup_successful IS NOT NULL THEN 1 ELSE 0 END) as successful_saves,
    ROUND((SUM(CASE WHEN lookup_successful IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as save_success_rate
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
```

- [ ] Save success rate: ____________% (should be > 95%)

**✅ Phase 2 PASSED if:**
- Save success rate > 95%
- Cache Errors = 0
- ~70 companies saved with many NULL websites

---

## 🔥 Phase 3: Second Search - Warm Cache (3 minutes)

### Step 3.1: Run Same Search Again

**IMPORTANT: Use EXACT SAME query:**
```
Query: payment processing and payment gateway companies
```

- [ ] Search started (timestamp: ____________)
- [ ] Log monitoring active

### Step 3.2: Watch Backend Logs - THE PROOF!

**Look for these patterns:**

✅ **PERFECT - Cache Hits:**
```bash
🔍 Looking up CoreSignal company IDs for ~70 companies...

   ✅ [CACHE HIT] Stripe: ID=12345678 (confidence: 1.0)
   ✅ [CACHE HIT] PayPal: ID=87654321 (confidence: 1.0)
   ✅ [CACHE HIT] Square: ID=99999999 (confidence: 1.0)
   ✅ [CACHE HIT] Adyen: ID=11111111 (confidence: 1.0)
   # ... all companies should be cache hits!
```

- [ ] ✅ Seeing many `✅ [CACHE HIT]` messages
- [ ] ✅ NO `⊗ [CACHE MISS]` messages (or very few)

### Step 3.3: Check Final Metrics - THE MONEY SHOT!

**At end of search, logs should show:**
```bash
💾 Cache Performance:
   Cache Hits: 70 (100.0% hit rate)           ← 🎉 PERFECT!
   Cache Misses: 0                            ← No new lookups!
   Cache Errors: 0
   💰 Credits Saved: 70 (~$7.00 at $0.10/credit)  ← COST SAVINGS!
```

- [ ] ✅ Cache Hits: ~70 (should match companies discovered)
- [ ] ✅ Cache Hit Rate: 100.0% or very close (95%+)
- [ ] ✅ Cache Misses: 0 or very few (<5)
- [ ] ✅ Credits Saved: ~$7.00
- [ ] Search completed (timestamp: ____________)
- [ ] Duration: ____________ (should be < 30 seconds!)

### Step 3.4: Performance Comparison

**Calculate speedup:**
- First search duration: ____________
- Second search duration: ____________
- Speedup: ____________x (should be ~10x)

- [ ] ✅ Second search at least 5x faster than first

**✅ Phase 3 PASSED if:**
- Cache hit rate = 100% (or >95%)
- Cost savings = ~$7
- Search completed in < 30 seconds (10x faster)

---

## 🔬 Phase 4: Quality Verification (5 minutes)

### Step 4.1: Overall Cache Health

**In Supabase SQL Editor, run:**
```sql
SELECT
    COUNT(*) as total_entries,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN lookup_successful = false THEN 1 ELSE 0 END) as failed,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as success_rate,
    ROUND(AVG(CASE WHEN lookup_successful = true THEN confidence::numeric END), 2) as avg_confidence,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    ROUND((SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as null_website_pct
FROM company_lookup_cache;
```

**Record results:**
- [ ] Total entries: ____________
- [ ] Success rate: ____________% (should be ~92%)
- [ ] Avg confidence: ____________ (should be > 0.90)
- [ ] NULL website %: ____________% (should be ~90%)

**✅ Quality checks:**
- [ ] Success rate 85-95% (some companies won't be in CoreSignal)
- [ ] Avg confidence > 0.90 (high-quality matches)
- [ ] NULL website % > 80% (proves fix is working!)

### Step 4.2: Cache Growth Verification

**In Supabase SQL Editor, run:**
```sql
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as companies_added
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '2 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;
```

- [ ] ✅ Cache grew with first search (~70 companies)
- [ ] ✅ Cache did NOT grow with second search (no new entries, just hits)

### Step 4.3: Cost Savings Analysis

**In Supabase SQL Editor, run:**
```sql
SELECT
    COUNT(*) as total_cached_companies,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful_lookups,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) * 0.10), 2) as total_potential_savings_usd
FROM company_lookup_cache;
```

**Record results:**
- [ ] Total cached: ____________ companies
- [ ] Successful: ____________ lookups
- [ ] Potential savings: $____________

**Future projection:**
- Monthly searches: ~50
- Companies per search: ~70
- **Without cache:** 50 × 70 × $0.10 = **$350/month**
- **With cache (after warm-up):** ~$10-20/month
- **Estimated savings:** **$330-340/month (94-97% reduction)**

---

## 📊 Final Results Summary

### Cache System Performance

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Cache Save Success Rate** | > 95% | ______% | ☐ Pass ☐ Fail |
| **Cache Hit Rate (2nd search)** | 100% | ______% | ☐ Pass ☐ Fail |
| **Cache Errors** | 0 | ______ | ☐ Pass ☐ Fail |
| **NULL Websites Allowed** | ~90% | ______% | ☐ Pass ☐ Fail |
| **Avg Confidence** | > 0.90 | ______ | ☐ Pass ☐ Fail |
| **Cost Savings (repeat search)** | ~$7 | $______ | ☐ Pass ☐ Fail |
| **Speed Improvement** | 10x | ______x | ☐ Pass ☐ Fail |

### Overall Assessment

- [ ] ✅ **PASS** - Cache system working perfectly
- [ ] ⚠️ **PARTIAL** - Some issues but functional
- [ ] ❌ **FAIL** - Critical issues, needs fixing

**Notes/Issues:**
```
(Add any observations, warnings, or issues encountered)




```

---

## 🐛 Troubleshooting

### Issue 1: High Save Failure Rate (> 10%)

**Symptoms:**
- Many `[CACHE] ❌ Failed to save` errors with "23502" code
- Low save success rate (< 90%)

**Fix:**
```sql
-- Verify website column allows NULL
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'company_lookup_cache'
    AND column_name = 'website';

-- If is_nullable = 'NO', run:
ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;
```

### Issue 2: Zero Cache Hits on Second Search

**Symptoms:**
- Second search shows 0% cache hit rate
- All companies are cache misses again

**Possible causes:**
1. **Cache not saving properly** → Check Phase 2.4 database verification
2. **Different search query** → Ensure using EXACT same query
3. **Cache cleared between searches** → Check if someone ran cleanup queries

**Debug:**
```sql
-- Check if companies from first search exist in cache
SELECT company_name, company_id, created_at
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 10;
```

### Issue 3: High Cache Errors

**Symptoms:**
- `Cache Errors: 10+` in logs

**Possible causes:**
1. **Supabase connection issues** → Check Supabase status
2. **Invalid credentials** → Verify `SUPABASE_URL` and `SUPABASE_KEY`
3. **Schema mismatch** → Verify table structure

**Debug:**
```sql
-- Check table structure
\d company_lookup_cache
```

### Issue 4: Session Stuck as "Running"

**Symptoms:**
- "Research already in progress for this JD" error
- Can't start new searches

**Fix:**
```sql
-- Clear stuck sessions
UPDATE company_research_sessions
SET status = 'failed'
WHERE status = 'running'
    AND created_at < NOW() - INTERVAL '1 hour';
```

---

## 📝 Next Steps After Testing

### If All Tests Pass ✅

1. **Monitor in production** - Watch cache hit rates over next week
2. **Set up weekly health check** - Run SQL query from `CACHE_TESTING_QUERIES.sql` (Query 7.1)
3. **Track cost savings** - Monitor monthly Supabase logs for actual savings
4. **Delete handoff document** - `HANDOFF_COMPANY_CACHING.md` no longer needed

### If Tests Fail ❌

1. **Document failures** in "Notes/Issues" section above
2. **Check troubleshooting** section for common fixes
3. **Review backend logs** for detailed error messages
4. **Verify database schema** matches expectations
5. **Contact support** if persistent issues

---

## 📚 Reference Files

- **SQL Queries:** `backend/CACHE_TESTING_QUERIES.sql`
- **Architecture Doc:** `backend/COMPANY_CACHING_ARCHITECTURE.md`
- **Handoff Doc:** `backend/HANDOFF_COMPANY_CACHING.md`
- **Code:**
  - `backend/company_id_cache_service.py` (Tier 1 cache)
  - `backend/company_research_service.py` (Research pipeline)
  - `backend/utils/supabase_storage.py` (Storage layer)

---

**Testing Completed By:** ________________
**Date:** ________________
**Time:** ________________
**Result:** ☐ Pass ☐ Fail ☐ Partial
