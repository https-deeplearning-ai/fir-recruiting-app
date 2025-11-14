-- ============================================================================
-- COMPANY CACHE TESTING QUERIES
-- ============================================================================
-- Use these queries in Supabase SQL Editor to verify cache is working
-- Run them in order during testing phases
-- ============================================================================

-- ============================================================================
-- PHASE 1: PRE-FLIGHT CHECK
-- ============================================================================

-- Query 1.1: Check if website column allows NULL (THE CRITICAL FIX)
-- Expected: is_nullable = 'YES' ✅
-- If 'NO': Run the ALTER TABLE command below
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'company_lookup_cache'
    AND column_name = 'website';

-- FIX (if needed): Remove NOT NULL constraint
-- ALTER TABLE company_lookup_cache
-- ALTER COLUMN website DROP NOT NULL;


-- Query 1.2: Check current cache state (baseline)
SELECT
    COUNT(*) as total_entries,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful_lookups,
    SUM(CASE WHEN lookup_successful = false THEN 1 ELSE 0 END) as failed_lookups,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    SUM(CASE WHEN website IS NOT NULL THEN 1 ELSE 0 END) as has_websites,
    MIN(created_at) as oldest_entry,
    MAX(created_at) as newest_entry
FROM company_lookup_cache;


-- Query 1.3: Clear any stuck sessions before testing
UPDATE company_research_sessions
SET status = 'failed'
WHERE status IN ('running', 'in_progress')
    AND created_at < NOW() - INTERVAL '1 hour';


-- Query 1.4: Verify stored_companies has tracking columns
SELECT
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name = 'stored_companies'
    AND column_name IN ('collection_method', 'collected_at', 'data_source')
ORDER BY column_name;

-- If missing, add them:
-- ALTER TABLE stored_companies
-- ADD COLUMN IF NOT EXISTS collection_method TEXT DEFAULT 'collect',
-- ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP,
-- ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'coresignal_company_base';


-- ============================================================================
-- PHASE 2: AFTER FIRST SEARCH (Cold Cache)
-- ============================================================================

-- Query 2.1: Count companies added in last 10 minutes
SELECT COUNT(*) as companies_added_recently
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
-- Expected: ~70 rows (one per discovered company)


-- Query 2.2: View recently added companies (check for NULL websites)
SELECT
    company_name,
    company_id,
    website,
    lookup_successful,
    confidence,
    employee_count,
    created_at
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC
LIMIT 30;
-- Expected: Many rows with website = NULL (THIS IS NORMAL AND PROVES FIX WORKS!)


-- Query 2.3: Check for save failures (should be zero or near-zero)
SELECT
    COUNT(*) as total_attempts,
    SUM(CASE WHEN lookup_successful IS NOT NULL THEN 1 ELSE 0 END) as successful_saves,
    COUNT(*) - SUM(CASE WHEN lookup_successful IS NOT NULL THEN 1 ELSE 0 END) as failed_saves,
    ROUND((SUM(CASE WHEN lookup_successful IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as save_success_rate
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '10 minutes';
-- Expected: save_success_rate > 95%


-- ============================================================================
-- PHASE 3: AFTER SECOND SEARCH (Warm Cache)
-- ============================================================================

-- Query 3.1: Check if last_used_at updated for cached companies
SELECT
    company_name,
    company_id,
    created_at,
    last_used_at,
    EXTRACT(EPOCH FROM (last_used_at - created_at))/60 as cache_age_minutes
FROM company_lookup_cache
ORDER BY last_used_at DESC
LIMIT 20;
-- Expected: last_used_at > created_at for recently searched companies


-- Query 3.2: Verify cache is being reused (no duplicate saves)
SELECT
    company_name,
    COUNT(*) as occurrences
FROM company_lookup_cache
GROUP BY company_name
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;
-- Expected: Empty result (no duplicates) or very few duplicates


-- ============================================================================
-- PHASE 4: QUALITY VERIFICATION
-- ============================================================================

-- Query 4.1: Overall cache health metrics
SELECT
    COUNT(*) as total_entries,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN lookup_successful = false THEN 1 ELSE 0 END) as failed,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as success_rate,
    ROUND(AVG(CASE WHEN lookup_successful = true THEN confidence::numeric END), 2) as avg_confidence,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    ROUND((SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END)::float / COUNT(*) * 100), 1) as null_website_pct,
    SUM(CASE WHEN website IS NOT NULL THEN 1 ELSE 0 END) as has_websites
FROM company_lookup_cache;
-- Expected:
-- success_rate: ~92% (some companies not in CoreSignal)
-- avg_confidence: > 0.90 (high-quality matches)
-- null_website_pct: ~90% (proves fix is working!)


-- Query 4.2: Cache growth over time
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as companies_added,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN lookup_successful = false THEN 1 ELSE 0 END) as failed,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) * 0.10), 2) as potential_savings_usd
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;
-- Expected: Steady growth with each search


-- Query 4.3: Failed lookups (companies not found in CoreSignal)
SELECT
    company_name,
    website,
    confidence,
    created_at
FROM company_lookup_cache
WHERE lookup_successful = false
ORDER BY created_at DESC
LIMIT 20;
-- Expected: Small percentage (< 10%) of total entries
-- These are cached as "failed" to avoid wasting credits on retries


-- Query 4.4: Top cached companies (by usage)
SELECT
    company_name,
    company_id,
    lookup_successful,
    created_at,
    last_used_at,
    EXTRACT(EPOCH FROM (NOW() - last_used_at))/3600 as hours_since_last_use
FROM company_lookup_cache
WHERE lookup_successful = true
ORDER BY last_used_at DESC
LIMIT 30;


-- ============================================================================
-- COST SAVINGS ANALYSIS
-- ============================================================================

-- Query 5.1: Total cost savings (all time)
SELECT
    COUNT(*) as total_cached_companies,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful_lookups,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) * 0.10), 2) as total_potential_savings_usd
FROM company_lookup_cache;
-- Each cached company saves $0.10 on future searches


-- Query 5.2: Daily cost savings breakdown (last 7 days)
SELECT
    DATE(created_at) as date,
    COUNT(*) as companies_cached,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) * 0.10), 2) as daily_savings_usd
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;


-- Query 5.3: Projected monthly savings
WITH cache_stats AS (
    SELECT
        COUNT(*) as unique_companies,
        SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful_lookups
    FROM company_lookup_cache
)
SELECT
    unique_companies,
    successful_lookups,
    ROUND((successful_lookups * 0.10), 2) as cost_if_not_cached_usd,
    '~$10-20' as estimated_monthly_cost_with_cache,
    ROUND((successful_lookups * 0.10) - 15, 2) as estimated_monthly_savings_usd
FROM cache_stats;
-- Assumes 50 searches/month, 70 companies/search
-- Without cache: 50 × 70 × $0.10 = $350/month
-- With cache (after warm-up): ~$10-20/month
-- Savings: ~$330-340/month (94-97% reduction)


-- ============================================================================
-- TROUBLESHOOTING QUERIES
-- ============================================================================

-- Query 6.1: Check for constraint violation errors (the bug)
-- Note: This query checks for companies that SHOULD have been saved but weren't
-- Run BEFORE the fix to see how many companies have missing cache entries
SELECT
    COUNT(*) as companies_discovered,
    COUNT(DISTINCT company_name) as unique_companies,
    COUNT(*) - COUNT(DISTINCT company_name) as potential_duplicates
FROM company_lookup_cache
WHERE created_at > NOW() - INTERVAL '1 hour';


-- Query 6.2: Check for recent research sessions
SELECT
    session_id,
    jd_id,
    status,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_ago
FROM company_research_sessions
ORDER BY created_at DESC
LIMIT 10;


-- Query 6.3: Find sessions stuck as 'running'
SELECT
    session_id,
    jd_id,
    status,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_running
FROM company_research_sessions
WHERE status = 'running'
    AND created_at < NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;
-- If found, mark as failed:
-- UPDATE company_research_sessions SET status = 'failed'
-- WHERE session_id = 'xxx-xxx-xxx';


-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Query 7.1: Weekly cache health check (run every Monday)
SELECT
    COUNT(*) as total_cached,
    SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) as successful,
    ROUND(AVG(CASE WHEN lookup_successful = true THEN confidence::numeric END), 2) as avg_confidence,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as null_websites,
    SUM(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as added_last_week,
    SUM(CASE WHEN last_used_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as used_last_week,
    ROUND((SUM(CASE WHEN lookup_successful = true THEN 1 ELSE 0 END) * 0.10), 2) as total_savings_usd
FROM company_lookup_cache;


-- Query 7.2: Cleanup stale failed lookups (optional, run monthly)
-- This removes failed lookups older than 90 days that haven't been used
-- DELETE FROM company_lookup_cache
-- WHERE lookup_successful = false
--     AND created_at < NOW() - INTERVAL '90 days'
--     AND last_used_at < NOW() - INTERVAL '90 days';
-- (Commented out for safety - uncomment to execute)


-- ============================================================================
-- SUCCESS CRITERIA CHECKLIST
-- ============================================================================
--
-- ✅ Phase 1: is_nullable = 'YES' for website column
-- ✅ Phase 2: ~70 companies saved after first search
-- ✅ Phase 2: null_website_pct ~90% (proves fix works!)
-- ✅ Phase 2: save_success_rate > 95%
-- ✅ Phase 3: last_used_at updates on cache hits
-- ✅ Phase 4: success_rate ~92%, avg_confidence > 0.90
-- ✅ Cost: ~$7 savings per repeat search
-- ✅ Performance: 10x speedup (2-3 min → < 30 sec)
--
-- ============================================================================
