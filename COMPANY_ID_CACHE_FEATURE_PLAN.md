# Company ID Cache Feature Plan

**Feature:** CoreSignal Company ID Lookup Cache
**Status:** Infrastructure Complete, Integration Pending
**Last Updated:** November 12, 2025
**Owner:** Engineering Team

---

## Executive Summary

### Problem Statement
The company research pipeline currently performs redundant CoreSignal API searches for the same companies across multiple domain searches. Each 4-tier lookup costs ~1 search credit and takes 2-4 seconds. With 60-100 companies per search, this results in:
- **60-100 API credits** per domain search
- **2-7 minutes** in lookup latency
- **Repeated searches** for popular companies (e.g., "Deepgram" searched 10+ times)

### Solution
Implement a persistent company name → CoreSignal ID lookup cache that:
1. Checks cache before executing 4-tier lookup
2. Stores successful lookups indefinitely (IDs don't change)
3. Stores failed searches with 7-day retry window
4. Tracks cache hit count for ROI metrics

### Business Value
- **80%+ cache hit rate** after warm-up (based on company name distribution)
- **Save 48-80 API credits** per cached domain search (60-100 companies × 80% hit rate)
- **Reduce lookup time** from 2-4s to <10ms per cached company
- **Cost savings:** $30-40 per search with warm cache (at $0.50/credit)

### Current Status
✅ **Complete:**
- Database table `company_id_cache` created
- `CompanyIDCacheService` class implemented (backend/company_id_cache_service.py)
- Company name normalization logic built
- Hit count tracking for ROI metrics
- Last accessed timestamp for analytics

❌ **Pending:**
- Integration into `_enrich_companies()` method
- Cache statistics endpoint
- Monitoring dashboard

---

## Technical Architecture

### System Overview

```
Domain Search Request
    ↓
discover_companies() → 100 unique companies
    ↓
_enrich_companies() → Add CoreSignal IDs
    ↓
┌──────────────────────────────────────┐
│  FOR EACH COMPANY:                   │
│                                      │
│  1. Normalize company name           │
│  2. Check company_id_cache table ←───┼─── ✅ INTEGRATION POINT
│     ├─ Cache HIT → Return ID        │
│     └─ Cache MISS → Continue         │
│                                      │
│  3. Execute 4-tier lookup            │
│     ├─ Tier 1: Website match        │
│     ├─ Tier 2: Name exact match     │
│     ├─ Tier 3: Fuzzy match          │
│     └─ Tier 4: company_clean        │
│                                      │
│  4. Store result in cache ←──────────┼─── ✅ INTEGRATION POINT
│     ├─ Success: Save ID + metadata   │
│     └─ Failure: Save null + timestamp│
└──────────────────────────────────────┘
```

### Database Schema

**Table:** `company_id_cache` (already exists in Supabase)

**Schema:** `/backend/COMPANY_ID_CACHE_SCHEMA.sql`

```sql
CREATE TABLE company_id_cache (
    id BIGSERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_name_normalized TEXT NOT NULL,
    coresignal_id BIGINT,
    lookup_tier TEXT,
    website TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_company_name_normalized
ON company_id_cache(company_name_normalized);

CREATE INDEX idx_coresignal_id
ON company_id_cache(coresignal_id);

CREATE INDEX idx_last_accessed
ON company_id_cache(last_accessed_at);
```

**Key Fields:**
- `company_name`: Original name from discovery (preserves case)
- `company_name_normalized`: Lowercase, stripped suffixes, deduplicated (UNIQUE)
- `coresignal_id`: CoreSignal company ID (NULL if search failed)
- `lookup_tier`: Which tier found it (website, name_exact, fuzzy, company_clean, null)
- `metadata`: Industry, employee_count, location for verification
- `hit_count`: Incremented on each cache hit (ROI tracking)
- `last_accessed_at`: Updated on each access (for cache warmth analytics)

### Service Layer

**File:** `/backend/company_id_cache_service.py` (already implemented)

**Class:** `CompanyIDCacheService`

**Key Methods:**

```python
class CompanyIDCacheService:
    def __init__(self):
        self.supabase = get_supabase_client()

    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for cache key matching."""
        # Lowercase, remove suffixes (Inc, LLC, Corp, Ltd, etc.)
        # Remove punctuation except hyphens
        # Strip extra whitespace
        return normalized

    def get_cached_id(self, company_name: str) -> Optional[Dict]:
        """
        Check cache for company ID.

        Returns:
            {
                'coresignal_id': 12345,
                'lookup_tier': 'website',
                'hit_count': 42,
                'cached_at': '2025-11-01T...',
                'metadata': {...}
            }
            OR None if not cached
        """
        normalized = self.normalize_company_name(company_name)
        result = self.supabase.table('company_id_cache') \
            .select('*') \
            .eq('company_name_normalized', normalized) \
            .execute()

        if result.data:
            # Increment hit_count
            self._increment_hit_count(result.data[0]['id'])
            return result.data[0]

        return None

    def save_to_cache(
        self,
        company_name: str,
        coresignal_id: Optional[int],
        lookup_tier: Optional[str],
        website: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save lookup result to cache.

        Args:
            company_name: Original company name
            coresignal_id: CoreSignal ID (None if search failed)
            lookup_tier: Which tier found it (or None)
            website: Company website if available
            metadata: Additional company info (industry, size, etc.)

        Returns:
            True if saved successfully
        """
        normalized = self.normalize_company_name(company_name)

        data = {
            'company_name': company_name,
            'company_name_normalized': normalized,
            'coresignal_id': coresignal_id,
            'lookup_tier': lookup_tier,
            'website': website,
            'metadata': metadata or {},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # Upsert: Update if exists, insert if new
        result = self.supabase.table('company_id_cache') \
            .upsert(data, on_conflict='company_name_normalized') \
            .execute()

        return bool(result.data)

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        # Total entries
        # Cache hit distribution
        # Top cached companies
        # Recent activity
        return stats
```

---

## Integration Strategy

### Integration Point 1: Import Cache Service

**File:** `/backend/company_research_service.py`
**Location:** Top of file (after existing imports)

```python
from company_id_cache_service import CompanyIDCacheService
```

### Integration Point 2: Modify `_enrich_companies()` Method

**File:** `/backend/company_research_service.py`
**Location:** Lines 1177-1274 (existing method)

**Current Code (NO CACHING):**

```python
def _enrich_companies(self, companies: List[Dict]) -> List[Dict]:
    """Enrich discovered companies with CoreSignal IDs."""
    enriched = []
    company_lookup = CoreSignalCompanyLookup()

    for company in companies:
        company_name = company.get('name', company.get('company_name', ''))
        website = company.get('website')

        # ⚠️ NO CACHE CHECK - Calls 4-tier lookup directly
        match = company_lookup.lookup_with_fallback(
            company_name=company_name,
            website=website,
            confidence_threshold=0.75,
            use_company_clean_fallback=True
        )

        if match:
            company['coresignal_id'] = match['company_id']
            company['lookup_tier'] = match.get('tier', 'unknown')
            company['match_confidence'] = match.get('confidence', 1.0)
            enriched.append(company)

    return enriched
```

**New Code (WITH CACHING):**

```python
def _enrich_companies(self, companies: List[Dict]) -> List[Dict]:
    """Enrich discovered companies with CoreSignal IDs."""
    enriched = []
    company_lookup = CoreSignalCompanyLookup()
    cache_service = CompanyIDCacheService()  # ✅ NEW: Initialize cache

    cache_hits = 0
    cache_misses = 0

    for company in companies:
        company_name = company.get('name', company.get('company_name', ''))
        website = company.get('website')

        # ✅ NEW: Check cache first
        cached = cache_service.get_cached_id(company_name)

        if cached and cached.get('coresignal_id'):
            # ✅ Cache HIT with valid ID
            cache_hits += 1
            company['coresignal_id'] = cached['coresignal_id']
            company['lookup_tier'] = cached.get('lookup_tier', 'unknown')
            company['match_confidence'] = 1.0
            company['cache_hit'] = True
            enriched.append(company)

            print(f"  ✓ Cache HIT: {company_name} → ID {cached['coresignal_id']} "
                  f"(hit #{cached.get('hit_count', 0)})")
            continue

        elif cached and not cached.get('coresignal_id'):
            # ✅ Cache HIT with NULL (failed search)
            # Check if search is recent (within 7 days)
            cached_at = datetime.fromisoformat(cached['created_at'])
            days_old = (datetime.now(timezone.utc) - cached_at).days

            if days_old < 7:
                print(f"  ⊘ Cache HIT (failed search): {company_name} "
                      f"(searched {days_old} days ago, skipping retry)")
                continue  # Skip - failed recently, don't retry yet
            else:
                print(f"  ↻ Cache STALE (failed search): {company_name} "
                      f"(searched {days_old} days ago, retrying)")

        # ✅ Cache MISS or stale failed search - Execute 4-tier lookup
        cache_misses += 1
        print(f"  ⊗ Cache MISS: {company_name} (executing 4-tier lookup)")

        match = company_lookup.lookup_with_fallback(
            company_name=company_name,
            website=website,
            confidence_threshold=0.75,
            use_company_clean_fallback=True
        )

        # ✅ NEW: Save result to cache
        if match:
            company['coresignal_id'] = match['company_id']
            company['lookup_tier'] = match.get('tier', 'unknown')
            company['match_confidence'] = match.get('confidence', 1.0)
            company['cache_hit'] = False
            enriched.append(company)

            # Save successful lookup to cache
            cache_service.save_to_cache(
                company_name=company_name,
                coresignal_id=match['company_id'],
                lookup_tier=match.get('tier'),
                website=website,
                metadata={
                    'confidence': match.get('confidence', 1.0),
                    'industry': company.get('industry'),
                    'employee_count': company.get('employee_count')
                }
            )
            print(f"    → Saved to cache: {company_name} → ID {match['company_id']}")
        else:
            # Save failed lookup to cache (prevents retry for 7 days)
            cache_service.save_to_cache(
                company_name=company_name,
                coresignal_id=None,
                lookup_tier=None,
                website=website,
                metadata={'search_failed': True}
            )
            print(f"    → Saved failed search to cache: {company_name}")

    # ✅ NEW: Log cache performance
    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total * 100) if total > 0 else 0
    print(f"\n📊 Cache Performance: {cache_hits} hits, {cache_misses} misses "
          f"({hit_rate:.1f}% hit rate)")

    return enriched
```

**Key Changes:**
1. Initialize `CompanyIDCacheService` at start of method
2. Check cache before 4-tier lookup
3. Handle cache hits (valid ID, failed search, stale failed search)
4. Save successful lookups to cache
5. Save failed searches to cache (with NULL ID)
6. Log cache performance metrics

---

## Implementation Checklist

### Phase 1: Core Integration ✅ READY TO IMPLEMENT
- [x] Database table created (`company_id_cache`)
- [x] Cache service class implemented (`CompanyIDCacheService`)
- [x] Normalization logic built
- [x] Hit count tracking added
- [ ] **TODO:** Integrate cache checks into `_enrich_companies()` method
- [ ] **TODO:** Add logging for cache hits/misses
- [ ] **TODO:** Add cache performance metrics to API response

### Phase 2: Testing
- [ ] Unit tests for `CompanyIDCacheService`
  - [ ] Test normalization logic
  - [ ] Test cache hit/miss flows
  - [ ] Test failed search retry logic (7-day window)
  - [ ] Test hit count increment
- [ ] Integration tests for `_enrich_companies()`
  - [ ] Cold cache (0% hit rate)
  - [ ] Warm cache (80%+ hit rate)
  - [ ] Mixed cache (some hits, some misses)
  - [ ] Failed searches (NULL IDs)
- [ ] Performance tests
  - [ ] Measure cache lookup latency (<10ms target)
  - [ ] Measure API credit savings
  - [ ] Verify no false positives

### Phase 3: Monitoring & Analytics
- [ ] Create `/api/cache/stats` endpoint
  - [ ] Total cache entries
  - [ ] Cache hit rate (last 24h, 7d, 30d)
  - [ ] Top 20 most cached companies
  - [ ] Recent cache activity
  - [ ] Failed searches awaiting retry
- [ ] Add cache metrics to domain search response
  - [ ] `cache_hits`, `cache_misses`, `cache_hit_rate`
  - [ ] `api_credits_saved`
- [ ] Create monitoring dashboard (optional)
  - [ ] Real-time cache hit rate
  - [ ] Credit savings over time
  - [ ] Cache warmth distribution

### Phase 4: Optimization (Future)
- [ ] Preload cache with known companies
  - [ ] Top 1000 AI/ML companies
  - [ ] YC companies
  - [ ] Fortune 500
- [ ] Add cache invalidation logic
  - [ ] Manual refresh for specific companies
  - [ ] Bulk refresh for stale entries
- [ ] Add cache export/import
  - [ ] Backup cache periodically
  - [ ] Share cache between environments

---

## Testing Plan

### Unit Tests (`test_company_id_cache_service.py`)

```python
def test_normalize_company_name():
    """Test company name normalization."""
    service = CompanyIDCacheService()

    assert service.normalize_company_name("Deepgram, Inc.") == "deepgram"
    assert service.normalize_company_name("Google LLC") == "google"
    assert service.normalize_company_name("Meta Platforms Inc.") == "meta platforms"
    assert service.normalize_company_name("  OpenAI  ") == "openai"

def test_cache_hit():
    """Test cache hit flow."""
    service = CompanyIDCacheService()

    # Save to cache
    service.save_to_cache(
        company_name="Deepgram, Inc.",
        coresignal_id=3829471,
        lookup_tier="website",
        website="deepgram.com"
    )

    # Retrieve from cache
    cached = service.get_cached_id("Deepgram Inc")  # Different format
    assert cached is not None
    assert cached['coresignal_id'] == 3829471
    assert cached['lookup_tier'] == 'website'
    assert cached['hit_count'] == 1

def test_cache_miss():
    """Test cache miss flow."""
    service = CompanyIDCacheService()

    cached = service.get_cached_id("NonexistentCompany12345")
    assert cached is None

def test_failed_search_caching():
    """Test caching of failed searches."""
    service = CompanyIDCacheService()

    # Save failed search
    service.save_to_cache(
        company_name="UnknownStartup",
        coresignal_id=None,
        lookup_tier=None
    )

    # Retrieve failed search
    cached = service.get_cached_id("UnknownStartup")
    assert cached is not None
    assert cached['coresignal_id'] is None

    # Check if retry is allowed (should be False if < 7 days)
    cached_at = datetime.fromisoformat(cached['created_at'])
    days_old = (datetime.now(timezone.utc) - cached_at).days
    assert days_old < 7  # Fresh failed search, don't retry

def test_hit_count_increment():
    """Test hit count increments on each access."""
    service = CompanyIDCacheService()

    service.save_to_cache("TestCompany", 12345, "name_exact")

    # Access 5 times
    for i in range(5):
        cached = service.get_cached_id("TestCompany")
        assert cached['hit_count'] == i + 1
```

### Integration Tests (`test_company_enrichment_with_cache.py`)

```python
def test_enrich_with_cold_cache():
    """Test enrichment with empty cache (0% hit rate)."""
    service = CompanyResearchService(...)

    companies = [
        {'name': 'Deepgram', 'website': 'deepgram.com'},
        {'name': 'AssemblyAI', 'website': 'assemblyai.com'},
        {'name': 'Otter.ai', 'website': 'otter.ai'}
    ]

    enriched = service._enrich_companies(companies)

    # All should be cache misses
    assert all(not c.get('cache_hit') for c in enriched)
    assert len(enriched) == 3

    # Verify all have CoreSignal IDs
    assert all(c.get('coresignal_id') for c in enriched)

def test_enrich_with_warm_cache():
    """Test enrichment with warm cache (100% hit rate)."""
    service = CompanyResearchService(...)
    cache_service = CompanyIDCacheService()

    # Preload cache
    cache_service.save_to_cache("Deepgram", 3829471, "website")
    cache_service.save_to_cache("AssemblyAI", 9876543, "name_exact")
    cache_service.save_to_cache("Otter.ai", 1234567, "website")

    companies = [
        {'name': 'Deepgram'},
        {'name': 'AssemblyAI'},
        {'name': 'Otter.ai'}
    ]

    enriched = service._enrich_companies(companies)

    # All should be cache hits
    assert all(c.get('cache_hit') for c in enriched)
    assert enriched[0]['coresignal_id'] == 3829471
    assert enriched[1]['coresignal_id'] == 9876543
    assert enriched[2]['coresignal_id'] == 1234567

def test_enrich_with_mixed_cache():
    """Test enrichment with partial cache (50% hit rate)."""
    service = CompanyResearchService(...)
    cache_service = CompanyIDCacheService()

    # Preload 2 out of 4
    cache_service.save_to_cache("Company A", 111, "website")
    cache_service.save_to_cache("Company B", 222, "name_exact")

    companies = [
        {'name': 'Company A'},
        {'name': 'Company B'},
        {'name': 'Company C'},
        {'name': 'Company D'}
    ]

    enriched = service._enrich_companies(companies)

    # Check hit/miss distribution
    cache_hits = [c for c in enriched if c.get('cache_hit')]
    cache_misses = [c for c in enriched if not c.get('cache_hit')]

    assert len(cache_hits) == 2
    assert len(cache_misses) == 2

def test_failed_search_retry_logic():
    """Test 7-day retry window for failed searches."""
    service = CompanyResearchService(...)
    cache_service = CompanyIDCacheService()

    # Save failed search (recent)
    cache_service.save_to_cache("RecentFail", None, None)

    # Save failed search (8 days ago) - requires DB manipulation
    # ... (test setup)

    companies = [
        {'name': 'RecentFail'},
        {'name': 'StaleFail'}
    ]

    enriched = service._enrich_companies(companies)

    # RecentFail: Skipped (cached NULL, < 7 days)
    # StaleFail: Retried (cached NULL, > 7 days)
    assert 'RecentFail' not in [c['name'] for c in enriched]
    # StaleFail may or may not be in enriched (depends on if retry succeeds)
```

---

## Rollout Plan

### Phase 1: Staging Deployment (Week 1)
**Goal:** Validate cache functionality in staging environment

**Steps:**
1. Deploy cache integration to staging
2. Run domain searches for 10-20 common domains
3. Monitor cache hit rates
4. Verify no false positives (wrong IDs)
5. Check API credit usage (should decrease on repeat searches)

**Success Criteria:**
- ✅ Cache hit rate increases from 0% to 60%+ after 10 searches
- ✅ No false positives (manual verification of 20 cached IDs)
- ✅ API credit usage drops by 50%+ on cached searches
- ✅ Cache lookup latency < 50ms (p99)

### Phase 2: Canary Rollout (Week 2)
**Goal:** Test with real production traffic (10%)

**Steps:**
1. Enable cache for 10% of production traffic (feature flag)
2. Monitor cache hit rates for 7 days
3. Compare API credit usage vs. control group
4. Check for any errors or timeouts

**Success Criteria:**
- ✅ Cache hit rate reaches 70%+ after 7 days
- ✅ API credit savings of 40%+ vs. control group
- ✅ No increase in error rate or latency
- ✅ Zero false positives in manual sample checks

### Phase 3: Full Rollout (Week 3)
**Goal:** Enable cache for 100% of production traffic

**Steps:**
1. Gradually increase cache rollout: 25% → 50% → 75% → 100%
2. Monitor cache performance metrics
3. Set up alerts for cache errors or low hit rates
4. Document cache statistics for stakeholders

**Success Criteria:**
- ✅ Cache hit rate stabilizes at 80%+
- ✅ API credit savings of 50%+ overall
- ✅ Cache lookup latency < 20ms (p95)
- ✅ Hit count distribution shows cache warmth

### Phase 4: Analytics & Optimization (Week 4+)
**Goal:** Maximize cache efficiency and ROI

**Steps:**
1. Create cache statistics dashboard
2. Identify most frequently cached companies
3. Preload cache with top 1000 companies
4. Set up weekly cache performance reports
5. Monitor failed searches for retry optimization

**Success Criteria:**
- ✅ Cache hit rate increases to 90%+
- ✅ API credit savings of 60%+ with preloaded cache
- ✅ Failed search retry rate < 5%
- ✅ Clear ROI metrics (credits saved, $ savings)

---

## Success Metrics

### Primary Metrics

**1. Cache Hit Rate**
- **Formula:** `(cache_hits / (cache_hits + cache_misses)) × 100%`
- **Targets:**
  - Week 1: 40-60% (cold cache warming up)
  - Week 2: 60-80% (cache maturing)
  - Week 4+: 80-90% (mature cache with preloading)
- **Measurement:** Track per domain search, aggregate daily/weekly

**2. API Credit Savings**
- **Formula:** `cache_hits × 1 credit = credits_saved`
- **Targets:**
  - 40-80 credits saved per domain search (100 companies × 80% hit rate)
  - 500+ credits saved per week (10 domain searches)
  - 2000+ credits saved per month
- **Measurement:** Track cumulative savings, compare to baseline

**3. Lookup Latency Reduction**
- **Baseline:** 2-4s per company (4-tier API lookup)
- **Target:** <10ms per company (cache lookup)
- **Formula:** `(baseline_latency - cache_latency) / baseline_latency × 100%`
- **Expected:** 99.5%+ latency reduction for cache hits

### Secondary Metrics

**4. False Positive Rate**
- **Formula:** `(incorrect_ids / total_cache_hits) × 100%`
- **Target:** 0% (zero tolerance for wrong IDs)
- **Measurement:** Manual spot checks + user feedback

**5. Cache Warmth**
- **Metric:** Distribution of hit counts across cached companies
- **Target:**
  - Top 20 companies: 50+ hits each
  - Top 100 companies: 10+ hits each
  - Long tail: 1-5 hits
- **Measurement:** Query `hit_count` distribution weekly

**6. Failed Search Retry Rate**
- **Formula:** `(retried_searches / total_failed_searches) × 100%`
- **Target:** < 10% (most failed searches stay failed)
- **Measurement:** Track NULL ID cache entries retried after 7 days

### ROI Calculation

**Cost Savings:**
```
Assumptions:
- 10 domain searches per week
- 100 companies per search
- 80% cache hit rate after warm-up
- $0.50 per API credit (CoreSignal search)

Weekly Savings:
= 10 searches × 100 companies × 80% hit rate × $0.50
= 10 × 100 × 0.8 × 0.5
= $400/week

Monthly Savings:
= $400 × 4 weeks
= $1,600/month

Annual Savings:
= $1,600 × 12 months
= $19,200/year
```

**Time Savings:**
```
Assumptions:
- 2.5s average API lookup time
- <10ms average cache lookup time
- 80% cache hit rate

Time Saved per Domain Search:
= 100 companies × 80% × (2.5s - 0.01s)
= 80 × 2.49s
= 199.2s (~3.3 minutes)

Weekly Time Savings:
= 10 searches × 3.3 minutes
= 33 minutes/week

Monthly Time Savings:
= 33 × 4 weeks
= 132 minutes (~2.2 hours/month)
```

---

## Monitoring & Alerts

### Cache Performance Dashboard

**Metrics to Display:**
1. **Real-time Hit Rate:** Last 1 hour, 24 hours, 7 days
2. **Cache Size:** Total entries, growth rate
3. **Top Cached Companies:** Top 20 by hit count
4. **Recent Activity:** Last 100 cache accesses
5. **Failed Searches:** Count, retry schedule
6. **Credits Saved:** Daily, weekly, monthly totals
7. **Latency Distribution:** Cache hits vs. API lookups

### Alert Thresholds

**Critical Alerts (PagerDuty):**
- Cache hit rate drops below 50% (after warm-up period)
- Cache lookup latency > 100ms (p95)
- False positive detected (manual report)
- Cache service unavailable (5+ consecutive errors)

**Warning Alerts (Slack):**
- Cache hit rate drops below 70% (after warm-up period)
- Failed search retry rate > 15%
- Cache size exceeds 10,000 entries (review for duplicates)
- Hit count distribution shows poor cache warmth

---

## Appendix

### A. Code References

**Database Schema:**
- File: `/backend/COMPANY_ID_CACHE_SCHEMA.sql`
- Table: `company_id_cache`

**Cache Service:**
- File: `/backend/company_id_cache_service.py`
- Class: `CompanyIDCacheService`
- Methods: `get_cached_id()`, `save_to_cache()`, `normalize_company_name()`

**Integration Point:**
- File: `/backend/company_research_service.py`
- Method: `_enrich_companies()` (lines 1177-1274)
- Current: No caching
- Target: Add cache checks before 4-tier lookup

**4-Tier Lookup:**
- File: `/backend/coresignal_company_lookup.py`
- Method: `lookup_with_fallback()` (lines 334-422)
- Tiers: Website (90%) → Name (40-50%) → Fuzzy (5-10%) → company_clean (3-5%)

### B. Related Documentation

**Existing Cache Systems:**
- Profile cache: `stored_profiles` table (3-90 day TTL)
- Company data cache: `stored_companies` table (30 day TTL)
- Competitor discovery cache: `company_discovery_cache` table (7 day TTL)

**Normalization Logic:**
- Lowercase conversion
- Suffix removal: Inc, LLC, Corp, Ltd, GmbH, AG, SA, AB, NV, BV, Plc, Pty, Srl, SpA
- Punctuation removal (except hyphens)
- Whitespace stripping

**Similar Features:**
- See `backend/utils/supabase_storage.py` for cache patterns
- See `backend/company_research_service.py:_deduplicate_companies()` for name matching

### C. Example Cache Scenarios

**Scenario 1: Cold Cache (First Domain Search)**
```
Domain: "Voice AI"
Companies: Deepgram, AssemblyAI, Otter.ai, ... (100 total)

Cache State Before: 0 entries
Cache Hits: 0
Cache Misses: 100
API Calls: 100 × 4-tier lookup = 100 credits
Latency: 100 × 2.5s = 250s (~4 minutes)

Cache State After: 100 entries (60 with IDs, 40 failed)
```

**Scenario 2: Warm Cache (Second Domain Search)**
```
Domain: "Voice AI" (repeated)
Companies: Deepgram, AssemblyAI, Otter.ai, ... (same 100)

Cache State Before: 100 entries
Cache Hits: 100 (all cached)
Cache Misses: 0
API Calls: 0 credits
Latency: 100 × 0.01s = 1s

Credits Saved: 100 credits (~$50)
Time Saved: 249s (~4 minutes)
```

**Scenario 3: Partial Overlap (Related Domain)**
```
Domain: "Conversational AI"
Companies: 60 from previous search, 40 new

Cache State Before: 100 entries
Cache Hits: 60
Cache Misses: 40
API Calls: 40 × 4-tier lookup = 40 credits
Latency: (60 × 0.01s) + (40 × 2.5s) = 100.6s (~1.7 minutes)

Credits Saved: 60 credits (~$30)
Time Saved: 150s (~2.5 minutes)
```

---

## Next Steps

1. **Immediate (Week 1):**
   - [ ] Integrate cache into `_enrich_companies()` method (2-3 hours)
   - [ ] Add cache performance logging (1 hour)
   - [ ] Write unit tests for cache service (2-3 hours)
   - [ ] Deploy to staging for testing

2. **Short-term (Week 2-3):**
   - [ ] Create cache statistics endpoint (2 hours)
   - [ ] Add cache metrics to domain search API response (1 hour)
   - [ ] Run canary rollout with 10% traffic (1 week monitoring)
   - [ ] Full production rollout

3. **Medium-term (Week 4+):**
   - [ ] Build cache performance dashboard (1 day)
   - [ ] Preload cache with top 1000 companies (2 hours)
   - [ ] Set up monitoring alerts (1 hour)
   - [ ] Document ROI metrics for stakeholders

4. **Long-term (Future):**
   - [ ] Add manual cache invalidation UI
   - [ ] Implement cache export/import for backups
   - [ ] Add cache warming jobs (scheduled preloading)
   - [ ] Explore multi-region cache replication

---

**Status:** Ready for implementation ✅
**Estimated Effort:** 1-2 days for core integration + testing
**Expected ROI:** $1,600/month in API credit savings

**Questions? Contact:** Engineering team or see `/backend/company_id_cache_service.py` for implementation details.
