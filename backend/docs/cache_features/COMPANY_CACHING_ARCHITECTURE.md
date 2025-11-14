# Company Caching Architecture

**Version:** 1.0
**Date:** November 13, 2025
**Status:** ✅ Production Ready

---

## Overview

The company caching system is a **two-tier architecture** designed to minimize CoreSignal API costs during the **Company Research Pipeline**. It caches company name→ID mappings separately from full company data, allowing fast lookups without expensive collect calls.

### Cost Savings

**Without caching:** $30+ per company search (100 companies × $0.10 ID + $0.20 data)
**With caching:** $2-4 per search (only uncached ID lookups)
**Savings:** ~90% reduction in API costs

---

## Architecture Components

### Tier 1: ID Mapping Cache (`company_lookup_cache`)

**Purpose:** Fast company name → CoreSignal ID resolution

**Schema:**
```sql
CREATE TABLE company_lookup_cache (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_id BIGINT,              -- NULL for failed searches
    website TEXT,
    lookup_successful BOOLEAN NOT NULL,
    confidence NUMERIC(3,2),
    employee_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW()
);
```

**Populated By:**
- Company discovery (4-tier ID lookup)
- Reverse enrichment (from collect calls)

**Cache Policy:**
- Failed searches cached for 7 days (prevents retry spam)
- Successful lookups cached indefinitely
- `last_used_at` updated on each access

**Cost Savings:** $0.10 per cache hit

---

### Tier 2: Full Data Cache (`stored_companies`)

**Purpose:** Complete company profiles from `/company_base/collect/` endpoint

**Schema:**
```sql
CREATE TABLE stored_companies (
    company_id BIGINT PRIMARY KEY,
    company_data JSONB NOT NULL,
    collection_method TEXT DEFAULT 'collect',  -- NEW
    collected_at TIMESTAMP,                    -- NEW
    data_source TEXT DEFAULT 'coresignal_company_base',  -- NEW
    last_fetched TIMESTAMP DEFAULT NOW(),
    user_verified BOOLEAN DEFAULT FALSE,
    verification_status TEXT,
    verified_by TEXT,
    verified_at TIMESTAMP
);
```

**Populated By:**
- Profile assessment (automatic during candidate evaluation)
- Manual company enrichment (future feature)

**Cache Policy:**
- Freshness: 30 days
- Stale data triggers fresh collect call

**Cost Savings:** $0.20 per cache hit

---

## Primary Use Case: Company Research Pipeline

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY (Web Search)                             │
│   Tavily + Claude → 100 companies discovered                │
│   Data: name, website, description                          │
│   Cost: $0 (web search is free with credits)                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: ID ENRICHMENT (company_lookup_cache)               │
│                                                              │
│   For each of 100 companies:                                │
│   ┌──────────────────────────────────────────┐              │
│   │ 1. Check company_lookup_cache            │              │
│   │    ├─ HIT: Use cached ID (FREE) ✅       │              │
│   │    └─ MISS: Execute 4-tier lookup        │              │
│   │                                           │              │
│   │ 2. 4-Tier Lookup (if cache miss):        │              │
│   │    Tier 1: Website exact ($0.10)         │              │
│   │    Tier 2: Name exact ($0.10)            │              │
│   │    Tier 3: Fuzzy match ($0.10)           │              │
│   │    Tier 4: company_clean fallback        │              │
│   │                                           │              │
│   │ 3. Save result to cache                  │              │
│   │    - Success: Store ID + metadata        │              │
│   │    - Failure: Store NULL (7-day retry)   │              │
│   └──────────────────────────────────────────┘              │
│                                                              │
│   Result: 80-90 companies with IDs                          │
│   Cost: ~$2-8 (20-80 cache misses × $0.10)                  │
│   Saved: ~$8-10 from cache hits!                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: EMPLOYEE SAMPLING (FREE Preview API)               │
│   Search employees by company_id                            │
│   Returns 5 sample employees per company                    │
│   Cost: $0.00 (preview endpoint is free!)                   │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: RETURN TO UI                                       │
│   Companies have:                                           │
│     - Name, website, description                            │
│     - CoreSignal ID                                         │
│     - Sample employees                                      │
│     - Relevance scores                                      │
│   ❌ NO full company data (saves $0.20 × 100 = $20!)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Secondary Use Case: Profile Assessment

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ USER ACTION: Assess Candidate Profile                       │
│   Input: LinkedIn URL                                       │
│   Fetch profile with work experiences                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ COMPANY ENRICHMENT (stored_companies)                       │
│                                                              │
│   For each job in experience[] where year >= 2020:          │
│   ┌──────────────────────────────────────────┐              │
│   │ 1. Check stored_companies cache          │              │
│   │    ├─ HIT: Use cached data (FREE) ✅     │              │
│   │    └─ MISS: Call collect API             │              │
│   │                                           │              │
│   │ 2. Collect Full Data (if cache miss):    │              │
│   │    API: /company_base/collect/{id}       │              │
│   │    Cost: $0.20                            │              │
│   │    Returns: 45+ fields                    │              │
│   │                                           │              │
│   │ 3. Save to stored_companies:              │              │
│   │    collection_method: "collect"           │              │
│   │    collected_at: NOW()                    │              │
│   │                                           │              │
│   │ 4. Reverse Enrichment (NEW!):             │              │
│   │    Extract company name from data         │              │
│   │    Save to company_lookup_cache           │              │
│   │    └─ Future ID lookups = instant! ✅     │              │
│   └──────────────────────────────────────────┘              │
│                                                              │
│   Result: Profile with rich company context                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Bidirectional Caching (Reverse Enrichment)

When full company data is collected, the system automatically caches the name→ID mapping:

```python
# Collect company data
company_data = fetch_from_api(company_id)

# Save full data to stored_companies
save_stored_company(company_id, company_data, collection_method="collect")

# NEW: Also cache name→ID mapping
company_name = company_data.get('name')
save_to_lookup_cache(company_name, company_id)  # Reverse enrichment
```

**Benefit:** Companies discovered via profile assessment become instantly searchable by name!

---

### 2. Failed Search Caching

When a company isn't found in CoreSignal, the system caches the failure:

```sql
INSERT INTO company_lookup_cache (
    company_name,
    company_id,
    lookup_successful,
    created_at
) VALUES (
    'Unknown Startup',
    NULL,
    FALSE,
    NOW()
);
```

**Benefit:** Prevents wasting $0.10 on repeated failed searches for the same company.

**Policy:** Failed searches aren't retried for 7 days.

---

### 3. 4-Tier ID Lookup Strategy

The system tries multiple methods to find CoreSignal IDs:

**Tier 1: Website Exact Match (90% success when available)**
```
Query: company_base/search WHERE website = "acme.com"
Cost: $0.10
```

**Tier 2: Name Exact Match (40-50% success)**
```
Query: company_base/search WHERE name = "Acme Corp"
Cost: $0.10
```

**Tier 3: Fuzzy Match (5-10% success)**
```
Query: company_base/search with fuzzy matching
Cost: $0.10
```

**Tier 4: company_clean Fallback (3-5% success)**
```
Query: company_clean/search (alternative endpoint)
Cost: $0.10
```

**Combined Success Rate:** 80-90% of companies get IDs

---

### 4. Collection Method Tracking

The system now tracks HOW company data was obtained:

```sql
collection_method:
  - "collect": Full data from /company_base/collect/ (45+ fields)
  - "lookup_only": Only ID cached, no full data yet (future use)
```

**Use Cases:**
- Distinguish ID-only cache from full data cache
- Enable on-demand enrichment (future feature)
- Track data freshness and collection history

---

## Cost Analysis

### Scenario 1: First Company Search (Cold Cache)

```
100 companies discovered
├─ 80 found in CoreSignal (80% success rate)
│  ├─ 0 cache hits (cold cache)
│  └─ 80 API calls × $0.10 = $8.00
├─ 20 not found
│  └─ 20 API calls × $0.10 = $2.00
└─ Total: $10.00 (vs $30 without caching architecture)
```

---

### Scenario 2: Second Search (Warm Cache)

```
100 companies discovered (same companies)
├─ 80 found in CoreSignal
│  ├─ 80 cache hits × $0.00 = $0.00 ✅
│  └─ 0 API calls
├─ 20 not found (cached failures)
│  └─ 0 API calls (failures cached for 7 days)
└─ Total: $0.00 (100% cache hit rate!)
```

**Savings:** $10.00 per search after warm-up!

---

### Scenario 3: Profile Assessment

```
Assess 10 candidates with experiences at discovered companies
├─ First assessment per company:
│  └─ 10 collect calls × $0.20 = $2.00
├─ Subsequent assessments (same companies):
│  └─ 10 cache hits × $0.00 = $0.00 ✅
└─ Total: $2.00 (vs $4.00 without caching)
```

**Savings:** $2.00 per duplicate company!

---

### Monthly Cost Projection

**Assumptions:**
- 50 company searches per month
- 200 profile assessments per month
- 80% cache hit rate after warm-up

**Without Caching:**
```
Company searches: 50 × $10 = $500
Profile assessments: 200 × $2 = $400
Total: $900/month
```

**With Caching:**
```
Company searches: 50 × $2 = $100 (80% cache hit)
Profile assessments: 200 × $0.80 = $160 (60% cache hit)
Total: $260/month
```

**Monthly Savings:** $640 (71% reduction!)

---

## Implementation Details

### Service: CompanyIDCacheService

**Location:** `backend/company_id_cache_service.py`

**Key Methods:**

```python
async def get_cached_id(company_name: str) -> Optional[Dict]:
    """
    Get cached CoreSignal ID for a company.

    Returns:
        {
            'coresignal_id': int,
            'lookup_successful': bool,
            'confidence': float,
            'employee_count': int,
            'created_at': datetime,
            'last_used_at': datetime,
            'from_cache': True
        }
    """

async def save_to_cache(
    company_name: str,
    coresignal_id: Optional[int],
    lookup_tier: str,
    website: Optional[str],
    metadata: Dict
) -> bool:
    """
    Save company ID lookup result to cache.

    Args:
        company_name: Original company name
        coresignal_id: CoreSignal ID (None for failed searches)
        lookup_tier: 'website' | 'name_exact' | 'fuzzy' | 'company_clean'
        website: Company website URL
        metadata: {confidence, employee_count, industry}
    """
```

---

### Storage Functions

**Location:** `backend/utils/supabase_storage.py`

```python
def save_stored_company(
    company_id: int,
    company_data: Dict[str, Any],
    collected_at: Optional[float] = None,
    collection_method: str = "collect"
) -> bool:
    """
    Save full company data to stored_companies table.

    Args:
        company_id: CoreSignal ID
        company_data: Full 45+ field profile
        collected_at: Timestamp when data was collected
        collection_method: "collect" | "lookup_only"

    Features:
        - Uses merge-duplicates (upsert on company_id)
        - Tracks collection method and timestamp
        - Stores complete raw data in JSONB
    """

def get_stored_company(
    company_id: int,
    freshness_days: int = 30
) -> Optional[Dict]:
    """
    Get cached company data if fresh.

    Returns None if:
        - Company not cached
        - Data older than freshness_days
        - Stale data needs refresh
    """
```

---

## Testing Guide

### Test 1: Company Research Cache (Primary)

**Steps:**
```bash
# 1. Start backend
cd backend && python3 app.py

# 2. Watch logs
tail -f /tmp/backend_test.log

# 3. In UI: Navigate to Domain Search
# 4. Enter JD: "Experience at OpenAI, Anthropic, or similar AI companies"
# 5. Click "Research Companies"
```

**Expected Logs:**
```
🔍 Looking up CoreSignal company IDs for 100 companies...

# First search (cache misses):
   ⊗ [CACHE MISS] OpenAI - executing 4-tier lookup...
      ✅ Found: ID=12345678 (tier 1, website)
   [CACHE] ✅ Saved OpenAI → 12345678

# Repeat search (cache hits):
   ✅ [CACHE HIT] OpenAI: ID=12345678 (confidence: 1.0)

📊 Cache Performance:
   Cache hit rate: 100%
   Search credits saved: 1 ($0.10)
```

**Verify:**
```sql
SELECT company_name, company_id, confidence, created_at
FROM company_lookup_cache
WHERE company_name IN ('OpenAI', 'Anthropic')
ORDER BY created_at DESC;
```

---

### Test 2: Profile Assessment Cache (Secondary)

**Steps:**
```bash
# 1. In UI: Single Profile Assessment
# 2. Enter LinkedIn URL of someone who worked at OpenAI
# 3. Click "Assess Profile"
```

**Expected Logs:**
```
🏢 Fetching fresh company data from CoreSignal for ID: 12345678
✅ SUCCESS: Company data retrieved!
📦 Cached full company data for company_id 12345678
   💾 BONUS: Cached name→ID mapping: 'OpenAI' → 12345678
```

**Verify:**
```sql
SELECT
    company_id,
    collection_method,
    collected_at,
    jsonb_object_keys(company_data) as field_count
FROM stored_companies
WHERE company_id = 12345678;
```

**Expected:**
- `collection_method = 'collect'`
- `collected_at` = recent timestamp
- 45+ fields in company_data

---

### Test 3: Cache Hit on Second Profile

**Steps:**
```bash
# Assess another profile from OpenAI
```

**Expected Logs:**
```
✅ Using stored company 12345678 (age: 0 days) - SAVED 1 Collect credit!
```

---

## Troubleshooting

### Issue: "Column does not exist" errors

**Symptom:**
```
ERROR: column "collection_method" does not exist
```

**Cause:** Database schema not updated

**Fix:**
```sql
ALTER TABLE stored_companies
ADD COLUMN IF NOT EXISTS collection_method TEXT DEFAULT 'collect',
ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'coresignal_company_base';
```

---

### Issue: Low cache hit rate (<50%)

**Possible Causes:**
1. Cold cache (first few searches)
2. Unique companies each search
3. Company names not matching (normalization issue)

**Debug:**
```sql
-- Check cache contents
SELECT company_name, lookup_successful, created_at
FROM company_lookup_cache
ORDER BY created_at DESC
LIMIT 20;

-- Check for duplicates (normalization issues)
SELECT company_name, COUNT(*)
FROM company_lookup_cache
GROUP BY company_name
HAVING COUNT(*) > 1;
```

---

### Issue: Failed searches not cached

**Symptom:** Same company searched multiple times despite being not found

**Debug:**
```sql
-- Check failed searches
SELECT company_name, created_at
FROM company_lookup_cache
WHERE lookup_successful = FALSE
ORDER BY created_at DESC;
```

**Expected:** Failed searches should appear with `lookup_successful = FALSE`

---

## Monitoring Queries

### Cache Performance Metrics

```sql
-- Overall cache statistics
SELECT
    COUNT(*) as total_entries,
    COUNT(*) FILTER (WHERE lookup_successful = TRUE) as successful,
    COUNT(*) FILTER (WHERE lookup_successful = FALSE) as failed,
    ROUND(AVG(confidence::numeric), 2) as avg_confidence
FROM company_lookup_cache;
```

---

### Recent Cache Activity

```sql
SELECT
    company_name,
    company_id,
    lookup_successful,
    confidence,
    created_at,
    last_used_at,
    EXTRACT(DAY FROM NOW() - last_used_at) as days_since_use
FROM company_lookup_cache
ORDER BY last_used_at DESC
LIMIT 20;
```

---

### Cost Savings Estimation

```sql
-- Estimate API cost savings
WITH cache_stats AS (
    SELECT
        COUNT(*) as total_lookups,
        COUNT(*) FILTER (WHERE last_used_at > created_at) as cache_hits
    FROM company_lookup_cache
    WHERE lookup_successful = TRUE
)
SELECT
    total_lookups,
    cache_hits,
    ROUND(cache_hits::numeric / NULLIF(total_lookups, 0) * 100, 1) as hit_rate_pct,
    cache_hits * 0.10 as search_credits_saved,
    CONCAT('$', cache_hits * 0.10) as cost_saved
FROM cache_stats;
```

---

## Future Enhancements

### 1. On-Demand Company Enrichment

**Feature:** Allow users to request full company data from UI

**Implementation:**
```python
@app.route('/api/company/<int:company_id>/enrich', methods=['POST'])
def enrich_company(company_id):
    """Fetch full company data on demand"""
    company_data = fetch_company_data(company_id)
    save_stored_company(company_id, company_data, collection_method="collect")
    return jsonify(company_data)
```

---

### 2. Bulk Company Enrichment

**Feature:** Enrich top N companies from research results

**Use Case:** User wants full data for top 25 companies (cost: $5.00)

---

### 3. Cache Invalidation API

**Feature:** Manual cache refresh for specific companies

**Use Case:** Company just raised funding, need fresh data

---

### 4. Cache Analytics Dashboard

**Feature:** Visualize cache performance over time

**Metrics:**
- Hit rate trends
- Cost savings per day/month
- Most searched companies
- Cache size growth

---

## Maintenance

### Periodic Cleanup (Monthly)

```sql
-- Remove old failed searches (>30 days)
DELETE FROM company_lookup_cache
WHERE lookup_successful = FALSE
  AND created_at < NOW() - INTERVAL '30 days';

-- Archive stale company data (>90 days)
-- (Keep IDs, remove full data to save space)
UPDATE stored_companies
SET company_data = '{}'::jsonb
WHERE last_fetched < NOW() - INTERVAL '90 days';
```

---

### Backup Strategy

**Critical Data:**
- `company_lookup_cache` (67 entries, ~10KB)
- `stored_companies` (286 entries, ~5MB)

**Backup Frequency:** Daily (automatic via Supabase)

**Restore Priority:** High (cache miss = $$ lost)

---

## Support

### Common Questions

**Q: Why are discovered companies not in stored_companies?**
A: By design! This saves $20 per search by not collecting full data unnecessarily.

**Q: When does full data get collected?**
A: During profile assessment or manual enrichment requests.

**Q: How long is data cached?**
A: IDs: indefinitely. Full data: 30 days.

**Q: What's the expected cache hit rate?**
A: 80%+ after warm-up period (first few searches).

---

## Changelog

### v1.0 (November 13, 2025)
- ✅ Initial two-tier caching architecture
- ✅ 4-tier ID lookup strategy
- ✅ Failed search caching (7-day retry delay)
- ✅ Reverse enrichment (name→ID from collect)
- ✅ Collection method tracking
- ✅ Timestamp tracking for collected_at
- ✅ 30-day freshness policy for full data

---

## References

- **CoreSignal API Pricing:** Search $0.10/credit, Collect $0.20/credit
- **Supabase Schema:** `SUPABASE_SCHEMA.sql`
- **Service Implementation:** `company_id_cache_service.py`
- **Storage Utilities:** `utils/supabase_storage.py`
- **Company Research:** `company_research_service.py`

---

**Status:** ✅ Production Ready
**Last Updated:** November 13, 2025
**Next Review:** December 2025
