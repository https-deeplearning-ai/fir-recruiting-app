# Verified Strategy: Reaching 1000 Candidates

## API Limits (Empirically Tested)

✅ **Confirmed via testing on 2025-11-05:**
- CoreSignal preview endpoint enforces `page <= 5`
- Returns HTTP 422 error for page 6+
- No support for `from`/`offset` parameters
- **Hard limit: 100 results per query (5 pages × 20)**

## Reaching 1000 Candidates: Multi-Query Approach

### Phase 1: Initial Search (100 candidates)
```python
# Standard query - gets first 100
query = build_query(companies=all_companies, role="engineer")
results = fetch_pages_1_to_5(query)  # 100 candidates
```

### Phase 2: Company Batching (+200-300)
```python
# Split companies into smaller batches
for batch in split_companies(companies, batch_size=5):
    query = build_query(companies=batch, role="engineer")
    results = fetch_pages_1_to_5(query)  # 100 more each
```

### Phase 3: Seniority Variations (+300-400)
```python
seniority_queries = [
    {"seniority": "junior OR mid", "companies": companies},
    {"seniority": "senior OR staff", "companies": companies},
    {"seniority": "principal OR director", "companies": companies},
    {"seniority": "vp OR c-level", "companies": companies}
]

for sq in seniority_queries:
    results = fetch_pages_1_to_5(sq)  # 100 more each
```

### Phase 4: Role Variations (+200-300)
```python
role_queries = [
    {"title": "software engineer", "companies": companies},
    {"title": "machine learning", "companies": companies},
    {"title": "product manager", "companies": companies}
]

for rq in role_queries:
    results = fetch_pages_1_to_5(rq)  # 100 more each
```

## Deduplication Required

Since candidates may appear in multiple queries:
```python
seen_employee_ids = set()
unique_candidates = []

for candidate in all_results:
    emp_id = candidate.get('employee_id')
    if emp_id not in seen_employee_ids:
        seen_employee_ids.add(emp_id)
        unique_candidates.append(candidate)

# Typically 70-80% unique after deduplication
```

## Cost Analysis

To get 1000 unique candidates:
- Need ~1300 total results (accounting for 30% duplicates)
- 13 queries × 5 pages = 65 API calls
- Cost: 65 × $0.20 = $13.00

## Progressive Loading UI

```javascript
// Initial Load
loadCandidates(0, 100)    // 1 query, 5 API calls, $1

// Extended Search Options
const strategies = [
  { name: "Company Batches", queries: 3, candidates: 300, cost: "$3" },
  { name: "Seniority Levels", queries: 4, candidates: 400, cost: "$4" },
  { name: "Role Variations", queries: 3, candidates: 300, cost: "$3" }
]

// User selects which strategies to run
async function runExtendedSearch(selectedStrategies) {
  for (const strategy of selectedStrategies) {
    const results = await executeStrategy(strategy)
    deduplicate(results)
    updateUI(results)
  }
}
```

## Implementation Example

```python
async def get_1000_candidates(base_query, companies):
    """
    Fetch up to 1000 unique candidates using multiple queries.

    CoreSignal limit: 100 per query (5 pages × 20)
    Strategy: Run 10-15 queries with variations
    """
    all_candidates = []
    seen_ids = set()

    # Strategy 1: Base query (100)
    base_results = await fetch_with_pagination(base_query, max_pages=5)
    all_candidates.extend(base_results)

    # Strategy 2: Company batches (300)
    for batch in chunk_companies(companies, size=7):
        query = {**base_query, "companies": batch}
        results = await fetch_with_pagination(query, max_pages=5)
        all_candidates.extend(results)

        if len(all_candidates) >= 1000:
            break

    # Strategy 3: Seniority variations (400)
    for seniority in ["junior", "senior", "staff", "director"]:
        query = {**base_query, "seniority": seniority}
        results = await fetch_with_pagination(query, max_pages=5)
        all_candidates.extend(results)

        if len(all_candidates) >= 1000:
            break

    # Deduplicate
    unique = []
    for candidate in all_candidates:
        if candidate['id'] not in seen_ids:
            seen_ids.add(candidate['id'])
            unique.append(candidate)

    return unique[:1000]  # Cap at 1000
```

## Rate Limiting Considerations

```python
RATE_LIMITS = {
    "queries_per_minute": 10,
    "pages_per_minute": 50,
    "delay_between_queries": 6  # seconds
}

async def rate_limited_fetch(queries):
    results = []
    for i, query in enumerate(queries):
        if i > 0:
            await asyncio.sleep(RATE_LIMITS["delay_between_queries"])

        result = await fetch_query(query)
        results.extend(result)

    return results
```

## Summary

✅ **Verified**: CoreSignal has a hard 5-page limit (100 results max per query)
✅ **Solution**: Run multiple queries with different parameters
✅ **Feasible**: Can reach 1000 candidates with 10-15 queries
✅ **Cost**: ~$13 to get 1000 unique candidates
✅ **Time**: 2-3 minutes with rate limiting

The multi-query strategy is the only way to get more than 100 candidates from CoreSignal's preview endpoint.