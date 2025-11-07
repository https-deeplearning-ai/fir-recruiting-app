# Beyond 100: Reaching 1000 Candidates Strategy

## The Challenge
CoreSignal's preview endpoint has a **hard limit of 5 pages** (100 results total per query). But we can work around this by running **multiple strategic queries**.

## Solution: Multi-Query Strategy to Reach 1000

### Core Concept: Query Variations
Instead of one query for 100 candidates, run 10+ queries with variations to get 1000 unique candidates.

```
┌──────────────────────────────────────────────────────────────┐
│                    QUERY VARIATION STRATEGY                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Base Query (100 candidates)                                 │
│    ↓                                                          │
│  10 Query Variations × 100 candidates each = 1000 total      │
│                                                               │
│  Variation Techniques:                                       │
│  1. Company Batching                                         │
│  2. Seniority Segmentation                                   │
│  3. Location Filtering                                       │
│  4. Time-Based Windows                                       │
│  5. Role Title Variations                                    │
│  6. Skill Combinations                                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Strategies

### Strategy 1: Company Batching (Most Effective)
```python
# If Stage 1 discovers 30 companies, split into batches
companies = [/* 30 companies from Stage 1 */]

batch_1 = companies[0:10]   # First 10 companies → 100 candidates
batch_2 = companies[10:20]  # Next 10 companies → 100 candidates
batch_3 = companies[20:30]  # Last 10 companies → 100 candidates

# Run 3 separate searches, get 300 unique candidates
```

### Strategy 2: Seniority Progression
```python
seniority_levels = [
    "junior",      # Query 1: 100 junior engineers
    "mid",         # Query 2: 100 mid-level engineers
    "senior",      # Query 3: 100 senior engineers
    "staff",       # Query 4: 100 staff engineers
    "principal",   # Query 5: 100 principal engineers
    "director",    # Query 6: 100 directors
    "vp",          # Query 7: 100 VPs
    "c-level"      # Query 8: 100 C-level execs
]

# 8 queries × 100 = 800 candidates across seniority spectrum
```

### Strategy 3: Geographic Expansion
```python
locations = [
    "San Francisco Bay Area",  # Query 1: 100 Bay Area
    "New York",                # Query 2: 100 NYC
    "Seattle",                 # Query 3: 100 Seattle
    "Austin",                  # Query 4: 100 Austin
    "Remote",                  # Query 5: 100 Remote
    "Los Angeles",             # Query 6: 100 LA
    "Boston",                  # Query 7: 100 Boston
    "Denver",                  # Query 8: 100 Denver
]

# 8 queries × 100 = 800 candidates across locations
```

### Strategy 4: Time-Based Windows
```python
time_windows = [
    {"joined_after": "2024-01", "joined_before": "2024-12"},  # Recent hires
    {"joined_after": "2023-01", "joined_before": "2023-12"},  # 2023 cohort
    {"joined_after": "2022-01", "joined_before": "2022-12"},  # 2022 cohort
    {"joined_after": "2020-01", "joined_before": "2021-12"},  # Pandemic era
    {"joined_after": "2018-01", "joined_before": "2019-12"},  # Pre-pandemic
]

# 5 queries × 100 = 500 candidates across time periods
```

### Strategy 5: Role Variation
```python
role_variations = [
    ["engineer", "developer"],           # Software roles
    ["ml", "ai", "machine learning"],    # AI/ML roles
    ["architect", "principal"],          # Senior technical
    ["manager", "lead"],                 # Leadership
    ["founder", "cto", "ceo"],          # Executives
    ["researcher", "scientist"],         # Research roles
]

# 6 queries × 100 = 600 candidates across role types
```

## Smart Combination Algorithm

```python
class ExtendedSearchStrategy:
    """
    Intelligently combines strategies to reach 1000 candidates
    while maintaining relevance and avoiding duplicates.
    """

    def generate_query_variations(self, base_query, target_count=1000):
        """
        Generate query variations to reach target candidate count.

        Returns list of queries that together should yield ~1000 unique candidates
        """
        variations = []

        # Phase 1: Company batching (most relevant)
        # Expected: 300 unique candidates
        company_batches = self.split_companies_into_batches(base_query.companies, batch_size=10)
        for batch in company_batches[:3]:
            variations.append({
                "type": "company_batch",
                "query": self.build_query(companies=batch, **base_query.other_params),
                "priority": 1,
                "expected_yield": 100
            })

        # Phase 2: Seniority variations (good diversity)
        # Expected: 400 more unique candidates
        for seniority in ["junior/mid", "senior/staff", "principal/director", "vp/c-level"]:
            variations.append({
                "type": "seniority",
                "query": self.build_query(seniority=seniority, **base_query.params),
                "priority": 2,
                "expected_yield": 100
            })

        # Phase 3: Location expansion (if remote-friendly)
        # Expected: 300 more unique candidates
        if base_query.allows_remote:
            for location in ["Bay Area", "NYC", "Seattle"]:
                variations.append({
                    "type": "location",
                    "query": self.build_query(location=location, **base_query.params),
                    "priority": 3,
                    "expected_yield": 100
                })

        return variations[:10]  # Cap at 10 variations (1000 candidates max)
```

## Progressive Loading UX

```
┌─────────────────────────────────────────────┐
│         PROGRESSIVE LOADING UI               │
├─────────────────────────────────────────────┤
│                                              │
│  Showing 100 of 100 (Basic Search)          │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │   🚀 EXTENDED SEARCH AVAILABLE     │     │
│  │                                    │     │
│  │   Find up to 900 more candidates   │     │
│  │   using advanced search variations │     │
│  │                                    │     │
│  │   Strategies available:            │     │
│  │   ☑️ Company batching (+300)       │     │
│  │   ☑️ Seniority levels (+400)       │     │
│  │   ☑️ Geographic expansion (+300)   │     │
│  │                                    │     │
│  │   Estimated cost: $10-20           │     │
│  │   Time: 2-3 minutes                │     │
│  │                                    │     │
│  │   [Start Extended Search]          │     │
│  └────────────────────────────────────┘     │
│                                              │
└──────────────────────────────────────────────┘
```

## Implementation Code

```python
async def extended_search_to_1000(
    session_id: str,
    base_query: Dict,
    target_count: int = 1000
) -> Dict[str, Any]:
    """
    Extend search beyond 100 to reach up to 1000 candidates.

    Uses multiple query variations to bypass CoreSignal's 100-result limit.
    """
    all_candidates = []
    all_employee_ids = set()  # For deduplication
    queries_executed = 0
    credits_used = 0

    # Generate query variations
    strategy = ExtendedSearchStrategy()
    variations = strategy.generate_query_variations(base_query, target_count)

    print(f"📊 Extended Search Plan:")
    print(f"   Target: {target_count} candidates")
    print(f"   Strategies: {len(variations)} query variations")
    print(f"   Estimated credits: {len(variations) * 5}")

    # Execute variations in priority order
    for i, variation in enumerate(sorted(variations, key=lambda x: x['priority'])):
        if len(all_candidates) >= target_count:
            break

        print(f"\n🔍 Variation {i+1}/{len(variations)}: {variation['type']}")

        # Rate limit protection
        if i > 0:
            await asyncio.sleep(5)  # 5s between variation searches

        # Execute search (up to 100 results)
        result = await search_with_pagination(
            variation['query'],
            max_results=100,
            endpoint="employee_clean"
        )

        if result['success']:
            new_candidates = result['candidates']

            # Deduplicate
            unique_new = []
            for candidate in new_candidates:
                emp_id = candidate.get('employee_id') or candidate.get('id')
                if emp_id and emp_id not in all_employee_ids:
                    all_employee_ids.add(emp_id)
                    unique_new.append(candidate)

            all_candidates.extend(unique_new)
            queries_executed += 1
            credits_used += result.get('pages_fetched', 5)

            print(f"   ✅ Added {len(unique_new)} unique candidates")
            print(f"   📊 Total: {len(all_candidates)} unique candidates")

    # Save extended search results
    save_extended_search_session(session_id, all_candidates, queries_executed)

    return {
        "success": True,
        "candidates": all_candidates,
        "total_unique": len(all_candidates),
        "queries_executed": queries_executed,
        "credits_used": credits_used,
        "cost_estimate": f"${credits_used * 0.20:.2f}",
        "deduplication_stats": {
            "total_fetched": queries_executed * 100,
            "duplicates_removed": (queries_executed * 100) - len(all_candidates),
            "unique_percentage": len(all_candidates) / (queries_executed * 100) * 100
        }
    }
```

## Deduplication Strategy

```python
class CandidateDeduplicator:
    """Handle duplicate detection across multiple searches."""

    def __init__(self):
        self.seen_ids = set()
        self.seen_profiles = {}  # emp_id -> full profile

    def is_duplicate(self, candidate):
        """Check if we've seen this candidate before."""
        # Primary: employee_id
        emp_id = candidate.get('employee_id') or candidate.get('id')
        if emp_id and emp_id in self.seen_ids:
            return True

        # Secondary: LinkedIn URL
        linkedin_url = candidate.get('linkedin_url')
        if linkedin_url and linkedin_url in self.seen_profiles:
            return True

        # Tertiary: Name + Company match (fuzzy)
        name = candidate.get('full_name', '').lower()
        company = candidate.get('current_company', '').lower()

        for seen in self.seen_profiles.values():
            if (self.fuzzy_match(name, seen.get('full_name', '').lower()) and
                self.fuzzy_match(company, seen.get('current_company', '').lower())):
                return True

        return False

    def add_candidate(self, candidate):
        """Add candidate to deduplication tracking."""
        emp_id = candidate.get('employee_id') or candidate.get('id')
        if emp_id:
            self.seen_ids.add(emp_id)
            self.seen_profiles[emp_id] = candidate
```

## Cost Analysis

```
To reach 1000 candidates:

Option 1: Company Batching (3 batches)
  3 searches × 5 pages = 15 credits = $3.00
  Expected yield: ~300 unique candidates

Option 2: Full Extended Search (10 variations)
  10 searches × 5 pages = 50 credits = $10.00
  Expected yield: ~800-1000 unique candidates

Option 3: Hybrid Progressive (recommended)
  Phase 1: Initial 100 (5 credits)
  Phase 2: Company batches +200 (10 credits)
  Phase 3: Seniority variations +300 (15 credits)
  Phase 4: Geographic +200 (10 credits)
  Total: 40 credits = $8.00 for ~800 candidates
```

## Rate Limiting Considerations

```python
RATE_LIMITS = {
    "searches_per_minute": 10,
    "pages_per_minute": 20,
    "daily_limit": 1000
}

async def rate_limited_extended_search():
    """Execute extended search with rate limiting."""

    # Space out searches
    for i, variation in enumerate(variations):
        if i > 0:
            wait_time = 60 / RATE_LIMITS["searches_per_minute"]
            await asyncio.sleep(wait_time)

        # Execute with exponential backoff on 429
        result = await execute_with_retry(variation)
```

## Database Schema for Extended Search

```sql
-- Store extended search sessions
CREATE TABLE extended_search_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    base_session_id VARCHAR(255) REFERENCES domain_search_sessions(id),
    variation_type VARCHAR(50),  -- 'company_batch', 'seniority', etc.
    variation_params JSONB,
    candidates_found INTEGER,
    duplicates_removed INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for deduplication
CREATE INDEX idx_employee_dedup ON discovered_candidates(employee_id, session_id);
```

## Summary

**Yes, reaching 1000 candidates is possible** through:

1. **Multiple Query Variations**: Run 10+ searches with different parameters
2. **Smart Deduplication**: Track employee IDs to avoid duplicates
3. **Progressive Loading**: Let users decide how deep to search
4. **Cost Transparency**: Show estimated costs before executing

**Practical Limits**:
- **API**: 5 pages per search (hard limit)
- **Cost**: ~$10-20 to reach 1000 candidates
- **Time**: 2-3 minutes with rate limiting
- **Relevance**: Quality degrades after ~500 candidates

**Recommendation**: Implement 3-tier progressive search:
1. **Tier 1**: 0-100 candidates (standard)
2. **Tier 2**: 100-500 candidates (extended)
3. **Tier 3**: 500-1000 candidates (exhaustive)

This gives users control over depth vs cost tradeoff!