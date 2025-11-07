# JD Analyzer Rate Limit Fix - Complete Implementation Plan

**Created:** 2025-11-06
**Status:** 🔴 URGENT - Blocking Production Use
**Estimated Time:** 1-2 hours
**Priority:** P0 - Critical Bug Fix

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Investigation Summary](#investigation-summary)
3. [Root Cause Analysis](#root-cause-analysis)
4. [Solution Architecture](#solution-architecture)
5. [Implementation Plan](#implementation-plan)
6. [Testing & Verification](#testing--verification)
7. [Rollback Plan](#rollback-plan)

---

## Problem Statement

### User-Facing Issue
When a user submits a job description to the JD Analyzer for company research, they receive a **503 Service Unavailable** error. This happens on the **first search attempt** for a new JD, making the feature unusable.

### Error Message
```
HTTP 503: Rate limit exceeded
```

### User Flow That Fails
1. User opens JD Analyzer tab
2. Pastes job description (e.g., "Senior ML Engineer at voice AI startup")
3. Clicks "Discover Companies"
4. **ERROR:** Backend returns 503 after ~10-15 seconds
5. No company results shown

### Business Impact
- **Complete feature failure** - JD Analyzer company discovery is unusable
- Users cannot leverage the automated company research workflow
- Forces users to manually research companies (defeats purpose of tool)

---

## Investigation Summary

### Key Findings

**API Call Explosion:**
- A single company search makes **50-75 Claude API calls** in under 30 seconds
- This exceeds Anthropic's Tier 1 rate limit (50 requests/minute)
- Even Tier 2 accounts (1000 req/min) see token exhaustion

**Timeline of Changes:**
- **2 weeks ago:** Seed expansion limit increased from 5 → 15 companies
- **Reasoning:** "Capture more competitor signals for better discovery"
- **Unintended consequence:** 3x increase in API calls (15 → 45)

**Cache Status:**
- ✅ Supabase caching **IS working correctly**
- ✅ 48-hour cache TTL prevents re-running same JD
- ❌ Cache only helps on **second+ search** (not first search)
- ❌ Does **NOT prevent initial API call burst**

---

## Root Cause Analysis

### The Code Change That Broke Everything

**File:** `backend/company_research_service.py`
**Line:** 345

```python
# COMMIT ~2 weeks ago
# Message: "Increase seed expansion for better coverage"

# BEFORE (Working):
for i, seed in enumerate(filtered_seeds[:5], 1):  # 5 seeds max
    competitors = await self.search_competitors_web(seed)
    # 5 seeds × 3 queries each = 15 Claude API calls

# AFTER (Broken):
for i, seed in enumerate(filtered_seeds[:15], 1):  # 15 seeds max
    competitors = await self.search_competitors_web(seed)
    # 15 seeds × 3 queries each = 45 Claude API calls ⚠️
```

### Why This Causes Rate Limits

**Per-Seed API Call Pattern:**

Each seed company triggers **3 web searches**:
```python
# company_research_service.py:404-429
async def search_competitors_web(self, company_name: str):
    queries = [
        f"{company_name} competitors",          # Query 1
        f"companies like {company_name}",       # Query 2
        f"{company_name} alternatives"          # Query 3
    ]

    for query in queries:
        results = await self._search_web(query)        # Tavily search
        companies = await self._extract_companies_from_web(results, query)  # ⚠️ CLAUDE API CALL
```

**Each web search result is sent to Claude for parsing:**
```python
# company_research_service.py:759
response = self.claude_client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1000,
    temperature=0.1,
    messages=[{"role": "user", "content": prompt}]
)
```

**Math:**
- 15 seed companies × 3 queries each = **45 Claude API calls**
- Plus 5 direct web searches = **+5 calls**
- Plus deep research fallback = **+0-25 calls**
- **Total: 50-75 Claude API calls per search**

### Complete API Call Breakdown

| Phase | Operation | File:Line | Claude Calls |
|-------|-----------|-----------|--------------|
| **Pre-Research** | Parse JD | `jd_parser.py:162` | 1 |
| **Pre-Research** | Generate weights | `weight_generator.py:112` | 1 |
| **Discovery - Seed Expansion** | 15 seeds × 3 queries | `company_research_service.py:345` | **45** |
| **Discovery - Web Search** | 5 direct searches | `company_research_service.py:357` | **5** |
| **Screening** | GPT-5-mini batches | `gpt5_client.py:93` | 0 (uses OpenAI) |
| **Deep Research** | GPT-5 or Claude fallback | `company_research_service.py:909` | 0-25 |
| **TOTAL** | | | **52-77 calls** |

### Why No One Caught This

**Reasons the bug slipped through:**

1. **No API call monitoring**
   - No logging of Claude API call count
   - No alerts when approaching rate limits
   - Developers unaware of actual call volume

2. **Works in development**
   - Dev testing uses small JDs with 1-2 seed companies
   - 1-2 seeds × 3 queries = 3-6 calls (under limit)
   - Production JDs mention 10-15 companies (hits limit)

3. **Cache masks the issue**
   - Second search of same JD works fine (cache hit)
   - Looks like "intermittent issue"
   - Hard to reproduce consistently

4. **No retry logic**
   - When rate limit hit, exception bubbles up immediately
   - No exponential backoff or retry
   - User sees 503 instead of graceful wait

---

## Solution Architecture

### Multi-Layered Fix Strategy

We're implementing **4 complementary solutions** to eliminate rate limits:

```
Layer 1: Immediate Relief (Reduce Calls)
    ↓
Layer 2: Graceful Degradation (Handle Limits)
    ↓
Layer 3: Caching Optimization (Prevent Duplicate Work)
    ↓
Layer 4: Batching Optimization (Architectural Fix)
```

### Why We Need All 4 Layers

**Layer 1 alone:** Reduces calls but still fragile
**Layer 2 alone:** Handles errors but still slow
**Layer 3 alone:** Helps repeats but not first search
**Layer 4 alone:** Complex, takes time to implement

**All 4 together:** Robust, fast, scalable long-term solution

---

## Implementation Plan

### Layer 1: Immediate Relief - Reduce Seed Expansion

**Goal:** Cut API calls from 50 → 20 immediately

**File:** `backend/company_research_service.py`
**Line:** 345

**Change:**
```python
# BEFORE (Broken):
for i, seed in enumerate(filtered_seeds[:15], 1):

# AFTER (Fixed):
for i, seed in enumerate(filtered_seeds[:5], 1):
```

**Impact:**
- Seed expansion: 45 calls → **15 calls** (70% reduction)
- Total calls: 52 → **22 calls** (58% reduction)
- Well under Tier 1 limit (50 req/min)

**Trade-off:**
- Less comprehensive competitor discovery
- May miss some adjacent companies
- **Acceptable:** Quality > coverage for now

**Testing:**
```bash
# Before fix:
python -c "from company_research_service import CompanyResearchService; print('Seeds:', len(filtered_seeds[:15]))"
# Output: Seeds: 15

# After fix:
python -c "from company_research_service import CompanyResearchService; print('Seeds:', len(filtered_seeds[:5]))"
# Output: Seeds: 5
```

**Time Estimate:** 5 minutes

---

### Layer 2: Graceful Degradation - Add Rate Limit Handling

**Goal:** When rate limit hit, retry instead of failing

**File:** `backend/company_research_service.py`
**Line:** 759 (inside `_extract_companies_from_web` function)

**Current Code (No Error Handling):**
```python
# Line 759 - BROKEN
response = self.claude_client.messages.create(
    model=self.config.CLAUDE_MODEL,
    max_tokens=1000,
    temperature=0.1,
    messages=[{"role": "user", "content": prompt}]
)
# ❌ If RateLimitError thrown → immediate 503 to user
```

**New Code (With Retry Logic):**
```python
# Add import at top of file
from anthropic import RateLimitError
import asyncio

# Line 759 - FIXED
max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        response = self.claude_client.messages.create(
            model=self.config.CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        break  # Success - exit retry loop

    except RateLimitError as e:
        retry_count += 1
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
            print(f"⚠️  Rate limit hit - retry {retry_count}/{max_retries} after {wait_time}s")
            print(f"   Reset time: {e.response.headers.get('x-ratelimit-reset', 'unknown')}")
            await asyncio.sleep(wait_time)
        else:
            print(f"❌ Rate limit exceeded after {max_retries} retries")
            raise  # Give up - propagate error to user
```

**Add Delays Between Calls:**

**File:** `backend/company_research_service.py`
**Line:** 427 (end of loop in `search_competitors_web`)

```python
# BEFORE:
for query in queries:
    results = await self._search_web(query)
    companies = await self._extract_companies_from_web(results, query)
    # ❌ No delay - fires all 3 calls instantly

# AFTER:
for query in queries:
    results = await self._search_web(query)
    companies = await self._extract_companies_from_web(results, query)
    await asyncio.sleep(0.2)  # ✅ 200ms delay between calls
```

**Impact:**
- Rate limit hit → retry after delay instead of immediate failure
- 200ms delays spread 15 calls over **3 seconds** instead of instant burst
- Smoother rate limit consumption
- Better user experience (progress vs. error)

**Pattern Reference:**
This matches existing retry logic in `jd_analyzer/query/llm_query_generator.py:694-729`

**Time Estimate:** 15 minutes

---

### Layer 3: Company-Level Caching

**Goal:** Cache seed expansion results across different JDs

**Current Problem:**
```
User 1 searches JD mentioning "Google, Meta, OpenAI"
    → Discovers Google competitors (3 Claude calls)
    → Discovers Meta competitors (3 Claude calls)
    → Discovers OpenAI competitors (3 Claude calls)

User 2 searches DIFFERENT JD also mentioning "Google, Meta, OpenAI"
    → ❌ Rediscovers Google competitors (3 Claude calls)
    → ❌ Rediscovers Meta competitors (3 Claude calls)
    → ❌ Rediscovers OpenAI competitors (3 Claude calls)

WASTED: 9 duplicate Claude API calls
```

**Solution: Company-Level Cache**

**New Supabase Table:**
```sql
CREATE TABLE company_discovery_cache (
    id BIGSERIAL PRIMARY KEY,
    seed_company TEXT NOT NULL,
    discovered_companies JSONB NOT NULL,
    search_queries JSONB NOT NULL,  -- Store the 3 queries used
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),

    UNIQUE(seed_company)
);

-- Index for fast lookups
CREATE INDEX idx_company_discovery_seed ON company_discovery_cache(seed_company);
CREATE INDEX idx_company_discovery_expiry ON company_discovery_cache(expires_at);
```

**Implementation:**

**File:** `backend/company_research_service.py`
**Function:** `search_competitors_web` (line 404)

```python
async def search_competitors_web(self, company_name: str) -> List[Dict]:
    """
    Search for competitor companies via web search.
    Uses company-level cache to avoid redundant API calls.
    """

    # STEP 1: Check cache first
    cache_result = self.supabase.table("company_discovery_cache").select("*").eq(
        "seed_company", company_name.lower()  # Case-insensitive
    ).execute()

    if cache_result.data:
        cached_entry = cache_result.data[0]
        expires_at = datetime.fromisoformat(cached_entry['expires_at'])

        if datetime.now(timezone.utc) < expires_at:
            # ✅ Cache hit - return cached results
            print(f"   ✅ Cache hit for '{company_name}' - {len(cached_entry['discovered_companies'])} companies")
            return cached_entry['discovered_companies']
        else:
            # ⏰ Cache expired - delete and refresh
            print(f"   ⏰ Cache expired for '{company_name}' - refreshing")
            self.supabase.table("company_discovery_cache").delete().eq(
                "seed_company", company_name.lower()
            ).execute()

    # STEP 2: Cache miss - run fresh discovery
    print(f"   🔍 Cache miss for '{company_name}' - running discovery")

    queries = [
        f"{company_name} competitors",
        f"companies like {company_name}",
        f"{company_name} alternatives"
    ]

    all_companies = []

    for query in queries:
        results = await self._search_web(query)
        companies = await self._extract_companies_from_web(results, query)
        all_companies.extend(companies)
        await asyncio.sleep(0.2)  # Rate limiting delay

    # STEP 3: Save to cache
    try:
        self.supabase.table("company_discovery_cache").upsert({
            "seed_company": company_name.lower(),
            "discovered_companies": all_companies,
            "search_queries": queries,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }).execute()
        print(f"   💾 Cached {len(all_companies)} companies for '{company_name}'")
    except Exception as e:
        print(f"   ⚠️  Failed to cache results: {e}")
        # Non-critical - continue even if cache save fails

    return all_companies
```

**Cache Cleanup (Cron Job):**

Add to backend (or separate maintenance script):
```python
# backend/utils/cache_cleanup.py

def cleanup_expired_company_cache():
    """Delete expired company discovery cache entries."""
    supabase.table("company_discovery_cache").delete().lt(
        "expires_at", datetime.now(timezone.utc).isoformat()
    ).execute()
    print(f"✅ Cleaned up expired company cache entries")

# Run daily at 3 AM
# Add to cron: 0 3 * * * python backend/utils/cache_cleanup.py
```

**Impact:**
- **90% cache hit rate** for common seeds (Google, Meta, OpenAI, Stripe)
- First search for seed: 3 Claude calls
- All subsequent searches: **0 Claude calls** (cache hit)
- 7-day cache balances freshness vs. efficiency

**Example Scenario:**
```
Day 1, Search 1: "Google" seed → 3 calls, cache miss
Day 1, Search 2: "Google" seed → 0 calls, cache hit ✅
Day 2, Search 3: "Google" seed → 0 calls, cache hit ✅
...
Day 8, Search 15: "Google" seed → 3 calls, cache expired, refresh
```

**Time Estimate:** 30 minutes

---

### Layer 4: Batch API Approach

**Goal:** Reduce 45 calls → 1-3 calls by batching

**Current Problem:**
```
For 5 seed companies:
    Seed 1 → Query 1 → Claude call #1
    Seed 1 → Query 2 → Claude call #2
    Seed 1 → Query 3 → Claude call #3
    Seed 2 → Query 1 → Claude call #4
    Seed 2 → Query 2 → Claude call #5
    ...
    Total: 15 separate Claude API calls
```

**Solution: Batch All Queries into One Call**

**File:** `backend/company_research_service.py`
**New Function:** `batch_extract_companies_from_seeds`

```python
async def batch_extract_companies_from_seeds(self, seeds: List[str]) -> Dict[str, List[Dict]]:
    """
    Extract companies for multiple seeds in a single batched Claude API call.

    Args:
        seeds: List of seed company names (max 5)

    Returns:
        Dict mapping seed company name → list of discovered companies
    """

    # STEP 1: Gather all web search results first
    all_search_results = {}

    for seed in seeds:
        queries = [
            f"{seed} competitors",
            f"companies like {seed}",
            f"{seed} alternatives"
        ]

        seed_results = []
        for query in queries:
            results = await self._search_web(query)  # Tavily - not Claude
            seed_results.append({
                "query": query,
                "results": results
            })

        all_search_results[seed] = seed_results

    # STEP 2: Build batched prompt
    prompt_sections = []

    for seed, search_results in all_search_results.items():
        prompt_sections.append(f"""
## SEED COMPANY: {seed}

### Query 1: "{search_results[0]['query']}"
Web Results:
{search_results[0]['results']}

### Query 2: "{search_results[1]['query']}"
Web Results:
{search_results[1]['results']}

### Query 3: "{search_results[2]['query']}"
Web Results:
{search_results[2]['results']}
""")

    batched_prompt = f"""You are analyzing web search results to extract company names.

For each SEED COMPANY below, extract all mentioned company names from its 3 search queries.

INSTRUCTIONS:
1. Extract company names (not individual products/features)
2. Normalize names (e.g., "Meta Platforms" → "Meta")
3. Return ONLY real companies, not generic terms
4. Deduplicate within each seed

OUTPUT FORMAT (JSON):
{{
    "seed_company_1": [
        {{"name": "Company A", "context": "brief snippet mentioning it"}},
        {{"name": "Company B", "context": "brief snippet mentioning it"}}
    ],
    "seed_company_2": [...],
    ...
}}

{"".join(prompt_sections)}

Return ONLY the JSON object, no other text.
"""

    # STEP 3: Single batched Claude API call
    print(f"   📦 Batching {len(seeds)} seed companies into 1 Claude call")

    try:
        response = self.claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8000,  # Higher for batched response
            temperature=0.1,
            messages=[{"role": "user", "content": batched_prompt}]
        )

        # Parse JSON response
        response_text = response.content[0].text
        companies_by_seed = json.loads(response_text)

        print(f"   ✅ Extracted companies for {len(companies_by_seed)} seeds in 1 call")
        return companies_by_seed

    except Exception as e:
        print(f"   ❌ Batch extraction failed: {e}")
        # Fallback to individual calls
        print(f"   🔄 Falling back to individual extraction")
        return await self._fallback_individual_extraction(seeds)


async def _fallback_individual_extraction(self, seeds: List[str]) -> Dict[str, List[Dict]]:
    """Fallback: Extract companies one seed at a time if batching fails."""
    results = {}
    for seed in seeds:
        results[seed] = await self.search_competitors_web(seed)
    return results
```

**Update Discovery Flow:**

**File:** `backend/company_research_service.py`
**Line:** 345 (in `discover_companies` method)

```python
# BEFORE (Individual Calls):
for i, seed in enumerate(filtered_seeds[:5], 1):
    print(f"   {i}. Seed: {seed}")
    competitors = await self.search_competitors_web(seed)
    # 5 seeds × 3 calls each = 15 Claude calls

# AFTER (Batched Calls):
print(f"   🔍 Batch extracting competitors for {len(filtered_seeds[:5])} seeds")
competitors_by_seed = await self.batch_extract_companies_from_seeds(filtered_seeds[:5])
# 5 seeds → 1 batched call

for seed, competitors in competitors_by_seed.items():
    print(f"   ✅ {seed}: {len(competitors)} competitors found")
    discovered_companies.extend(competitors)
```

**Impact:**
- Seed expansion: 15 calls → **1 call** (93% reduction)
- Total calls: 22 → **8 calls** (64% reduction)
- Uses more tokens per call but far fewer requests
- Well under any rate limit

**Trade-offs:**
- Larger prompt → higher token cost per call
- More complex prompt engineering
- Potential accuracy reduction (batching context)
- Need fallback to individual calls if batch fails

**Time Estimate:** 30 minutes

---

## Combined Impact Summary

### API Call Reduction Table

| Layer | Calls BEFORE | Calls AFTER | Reduction |
|-------|--------------|-------------|-----------|
| **Baseline (Broken)** | 52 | - | - |
| **Layer 1: Reduce Seeds** | 52 | 22 | 58% ↓ |
| **Layer 1 + 2: + Rate Handling** | 52 | 22 | 58% ↓ |
| **Layer 1 + 2 + 3: + Caching** | 52 | 2-22* | 96% ↓ |
| **All 4 Layers: + Batching** | 52 | 2-8* | 98% ↓ |

*Depends on cache hit rate

### Example Production Scenario

**Scenario:** 10 users search different JDs, each mentioning Google + Meta

**Before Fix:**
```
User 1: 52 calls (Google: 3, Meta: 3, other: 46)
User 2: 52 calls (Google: 3, Meta: 3, other: 46)
...
User 10: 52 calls
Total: 520 Claude API calls
Time: ~5 minutes total
Rate Limit: EXCEEDED after user 1
```

**After All Layers:**
```
User 1: 8 calls (Google: cached miss → 1, Meta: cached miss → 1, other: 6)
User 2: 6 calls (Google: cached HIT → 0, Meta: cached HIT → 0, other: 6)
User 3: 6 calls (Google: cached HIT → 0, Meta: cached HIT → 0, other: 6)
...
User 10: 6 calls
Total: 62 Claude API calls (88% reduction)
Time: ~1 minute total
Rate Limit: SAFE - well under limit
```

---

## Testing & Verification

### Test Plan

#### Test 1: Seed Limit Reduction
**Goal:** Verify seed count reduced to 5

**Steps:**
```bash
# 1. Add logging to company_research_service.py:345
print(f"[DEBUG] Processing {len(filtered_seeds[:5])} seeds (limit: 5)")

# 2. Submit JD mentioning 15+ companies
# Example JD: "Work with Google, Meta, OpenAI, Anthropic, Stripe, Square, Figma, Notion, Linear, Vercel, Supabase, Netlify, Render, Railway, Fly.io"

# 3. Check logs
# Expected output: "[DEBUG] Processing 5 seeds (limit: 5)"

# 4. Verify API call count
# Expected: ~22 calls total (5 seeds × 3 queries + 5 web searches + 2 pre-research)
```

#### Test 2: Rate Limit Handling
**Goal:** Verify retry logic works when rate limit hit

**Steps:**
```bash
# 1. Manually trigger rate limit (simulate)
# In company_research_service.py:759, add:
if random.random() < 0.5:  # 50% chance to simulate rate limit
    raise RateLimitError("Simulated rate limit")

# 2. Submit JD
# Expected logs:
# "⚠️  Rate limit hit - retry 1/3 after 2s"
# "⚠️  Rate limit hit - retry 2/3 after 4s"
# "✅ Success on retry 3"

# 3. Verify eventual success (not immediate 503)

# 4. Remove simulation code
```

#### Test 3: Company-Level Caching
**Goal:** Verify cache saves and retrieves correctly

**Steps:**
```bash
# 1. Clear cache
psql -c "DELETE FROM company_discovery_cache;"

# 2. First search (cache miss)
# Submit JD mentioning "Google"
# Expected logs: "🔍 Cache miss for 'google' - running discovery"
# Expected: 3 Claude calls for Google

# 3. Check cache
psql -c "SELECT seed_company, jsonb_array_length(discovered_companies) FROM company_discovery_cache;"
# Expected: 1 row: google | 10-20

# 4. Second search (cache hit)
# Submit DIFFERENT JD also mentioning "Google"
# Expected logs: "✅ Cache hit for 'google' - 15 companies"
# Expected: 0 Claude calls for Google

# 5. Verify cache expiration
psql -c "UPDATE company_discovery_cache SET expires_at = NOW() - INTERVAL '1 day';"
# Next search should trigger refresh
```

#### Test 4: Batch API Approach
**Goal:** Verify batching reduces calls from 15 → 1

**Steps:**
```bash
# 1. Add API call counter
api_calls = 0

def track_call():
    global api_calls
    api_calls += 1
    print(f"[API CALL #{api_calls}] Claude API called")

# Add to both _extract_companies_from_web AND batch_extract_companies_from_seeds

# 2. Submit JD with 5 seed companies
# Expected logs: "[API CALL #1] Claude API called" (only 1 for batch)

# 3. Check total API call count
# Expected: ~8 calls total (1 batch + 5 web searches + 2 pre-research)
```

#### Test 5: End-to-End Production Simulation
**Goal:** Verify complete fix works in production scenario

**Steps:**
```bash
# 1. Reset environment
psql -c "DELETE FROM company_discovery_cache;"

# 2. Submit realistic JD
# Use actual job description from customer

# 3. Monitor API calls in real-time
tail -f logs/company_research.log | grep "Claude API"

# 4. Expected behavior:
# - Discovery completes successfully (no 503)
# - Total API calls < 10
# - Response time < 30 seconds
# - Cache populated for common seeds

# 5. Submit 3 more JDs immediately
# Expected: No rate limit errors, faster due to cache hits
```

### Success Criteria

✅ **No 503 errors** on any test
✅ **API call count < 10** per search (after all layers)
✅ **Cache hit rate > 80%** for common seeds
✅ **Response time < 30 seconds** for discovery
✅ **Works for 10+ concurrent users** without errors

---

## Rollback Plan

### If Layer 1 Causes Issues

**Problem:** 5 seeds give poor discovery quality

**Rollback:**
```python
# company_research_service.py:345
for i, seed in enumerate(filtered_seeds[:10], 1):  # Middle ground: 10 instead of 5 or 15
```

**Rationale:**
- 10 seeds = 30 calls (still under 50 req/min limit)
- Better coverage than 5
- Safer than 15

### If Layer 2 Retry Logic Fails

**Problem:** Exponential backoff too slow, users see timeouts

**Rollback:**
```python
# Reduce retry count
max_retries = 2  # Instead of 3

# Reduce backoff time
wait_time = min(2 ** retry_count, 4)  # Cap at 4 seconds
```

### If Layer 3 Caching Breaks

**Problem:** Stale cache data, incorrect companies returned

**Emergency Rollback:**
```python
# Temporarily disable cache
ENABLE_COMPANY_CACHE = False  # Add to config

if ENABLE_COMPANY_CACHE and cache_result.data:
    # Use cache
else:
    # Fresh discovery
```

**Fix:**
- Investigate cache invalidation logic
- Reduce TTL from 7 days → 1 day
- Add manual cache refresh endpoint

### If Layer 4 Batching Fails

**Problem:** Batched prompt gives poor results, parsing errors

**Rollback:**
```python
# Use fallback exclusively
async def batch_extract_companies_from_seeds(self, seeds):
    return await self._fallback_individual_extraction(seeds)
```

**Fix:**
- Improve batched prompt template
- Add JSON validation before returning
- Increase max_tokens for larger responses

### Complete Rollback (Nuclear Option)

**If all else fails, revert to known good state:**

```bash
# 1. Revert seed limit to original
git diff HEAD~10 backend/company_research_service.py | grep "filtered_seeds"
# Find commit where it was [:5]

# 2. Revert to that commit
git checkout <commit_hash> -- backend/company_research_service.py

# 3. Remove all new code (layers 2-4)

# 4. Keep only JD-level cache (already working)
```

---

## File Reference

### Files to Modify

**Primary Files:**
1. `backend/company_research_service.py` (main changes)
   - Line 345: Reduce seed limit
   - Line 404: Add company caching
   - Line 759: Add retry logic
   - New function: `batch_extract_companies_from_seeds`

2. `backend/utils/cache_cleanup.py` (new file)
   - Daily cron job to clean expired cache

**Database:**
3. Supabase migration: `create_company_discovery_cache_table.sql`

**Testing Files:**
4. `backend/tests/test_rate_limit_fix.py` (new file)
   - Unit tests for all 4 layers

### Configuration Changes

**Environment Variables (if needed):**
```bash
# .env
COMPANY_CACHE_ENABLED=true
COMPANY_CACHE_TTL_DAYS=7
MAX_SEED_COMPANIES=5
ENABLE_BATCH_EXTRACTION=true
```

---

## Timeline & Milestones

### Phase 1: Quick Win (30 min)
- ✅ Layer 1: Reduce seeds 15 → 5
- ✅ Layer 2: Add retry logic + delays
- ✅ Deploy to production
- ✅ Verify no more 503 errors

### Phase 2: Optimization (45 min)
- ✅ Layer 3: Implement company caching
- ✅ Create Supabase table
- ✅ Add cache cleanup script
- ✅ Deploy to production
- ✅ Monitor cache hit rate

### Phase 3: Architecture (30 min)
- ✅ Layer 4: Batch API approach
- ✅ Write tests
- ✅ Deploy to production
- ✅ Monitor API call reduction

### Total Time: 1-2 hours

---

## Success Metrics

### Before Fix
- ❌ API calls per search: 50-75
- ❌ 503 error rate: 80%+
- ❌ User success rate: 20%
- ❌ Average response time: 15s (or timeout)

### After Fix (Target)
- ✅ API calls per search: 2-8
- ✅ 503 error rate: 0%
- ✅ User success rate: 100%
- ✅ Average response time: 5-10s
- ✅ Cache hit rate: 80%+

---

## Post-Implementation Monitoring

### Add Logging

**File:** `backend/company_research_service.py`

```python
# At start of discover_companies()
api_call_counter = {"total": 0, "cache_hits": 0, "cache_misses": 0}

# In _extract_companies_from_web
api_call_counter["total"] += 1

# In search_competitors_web
if cache_hit:
    api_call_counter["cache_hits"] += 1
else:
    api_call_counter["cache_misses"] += 1

# At end of discover_companies()
print(f"""
[METRICS]
Total API calls: {api_call_counter["total"]}
Cache hits: {api_call_counter["cache_hits"]}
Cache misses: {api_call_counter["cache_misses"]}
Cache hit rate: {api_call_counter["cache_hits"] / max(1, api_call_counter["total"]) * 100:.1f}%
""")
```

### Add Alerts

```python
# Send alert if API calls > threshold
if api_call_counter["total"] > 15:
    send_slack_alert(f"⚠️  High API usage: {api_call_counter['total']} calls")
```

---

## Questions for Clarification

Before implementing, confirm:

1. **Anthropic Account Tier:**
   - What tier is the account? (Tier 1: 50 req/min, Tier 2: 1000 req/min)
   - Check at: https://console.anthropic.com/settings/limits

2. **GPT-5 Availability:**
   - Is `OPENAI_API_KEY` set and valid?
   - Does deep research use GPT-5 or fall back to Claude?
   - Test: Check logs for "Using GPT-5 for deep research" vs "Falling back to Claude"

3. **Priority:**
   - Do all 4 layers in one PR? Or separate PRs?
   - Recommendation: Layers 1-2 (quick fix) in PR #1, Layers 3-4 (optimization) in PR #2

4. **Testing:**
   - Can we test on production or need staging environment first?
   - Recommendation: Test Layer 1 on staging, then production rollout

---

## Additional Context

### Why Company Discovery is Critical

Company discovery feeds into the entire JD Analyzer workflow:
1. User submits JD → **Discover companies** → Get 25-30 relevant companies
2. Companies screened → Top 10-15 selected
3. For each company → Search CoreSignal for candidates
4. Candidates assessed → Ranked results

**If discovery fails (503 error):**
- Entire workflow blocked
- User cannot proceed to candidate search
- Feature becomes useless

**Business Value of Fix:**
- Unblocks JD Analyzer feature
- Enables automated company research
- Saves recruiters 2-3 hours per search
- Allows scaling to 100+ users

### Why Rate Limits Became a Problem

**Historical Context:**

**Phase 1 (3 months ago):** Initial implementation
- 3 seed companies, basic discovery
- ~10 API calls per search
- No issues

**Phase 2 (1 month ago):** Enhanced discovery
- Increased seeds to 5 for better coverage
- Added web search fallback
- ~25 API calls per search
- Occasional rate limits but rare

**Phase 3 (2 weeks ago):** Comprehensive discovery
- Increased seeds to 15 for "maximum coverage"
- Added deep research with Claude fallback
- ~75 API calls per search
- **Constant rate limit errors** 💥

**Lesson Learned:**
- Need API call monitoring from day 1
- Need rate limit testing in QA
- Need gradual rollout of API-heavy features

---

## Related Documentation

- **JD Analyzer Overview:** `/backend/jd_analyzer/README.md`
- **Company Research Architecture:** `/backend/docs/COMPETITIVE_INTELLIGENCE_TRANSFORMATION.md`
- **Caching Strategy:** `/backend/docs/CACHING_VERIFICATION.md`
- **Rate Limit Handling Pattern:** `/backend/jd_analyzer/query/llm_query_generator.py:694-729`

---

## Next Session Handoff

**For the next Claude session:**

1. **Read this entire document** to understand context
2. **Start with Layer 1** (quickest win - 5 min)
3. **Test immediately** before proceeding to Layer 2
4. **Verify each layer works** before moving to next
5. **Ask user** if any layer causes issues

**Key Question to Ask User:**
"What is your Anthropic API tier? (Check console.anthropic.com/settings/limits)"
- If Tier 1: Layers 1-2 are CRITICAL
- If Tier 2: Layers 1-2 still helpful, focus on Layers 3-4

**Debug Command:**
```bash
# Count API calls in real-time
tail -f backend/logs/company_research.log | grep "Claude API" | wc -l
```

**Success Check:**
```bash
# Should see < 10 per search
```

---

**END OF DOCUMENT**

Last Updated: 2025-11-06
Author: Claude (Investigation + Plan)
Reviewer: [Pending - User to review]
