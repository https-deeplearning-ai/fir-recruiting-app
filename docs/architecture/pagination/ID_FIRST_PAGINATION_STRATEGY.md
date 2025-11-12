# ID-First Pagination Strategy

## The Brilliant Insight
Instead of fetching full profiles with pagination limits, we could:
1. Get employee IDs from the search (lightweight)
2. Cache the IDs
3. Fetch full profiles on-demand
4. Find ways to get MORE IDs from the same query

## Investigating Alternative Endpoints

### Option 1: Full Search Endpoint (Not Just Preview)
```python
# The preview endpoint we currently use:
/v2/employee_clean/search/es_dsl/preview?page=1  # Limited to page 5

# But there might be a full search endpoint:
/v2/employee_clean/search/es_dsl  # Different limits?

# This could support:
{
    "query": {...},
    "from": 100,  # Offset
    "size": 100   # Next batch
}
```

### Option 2: Scroll API Pattern
Many Elasticsearch-based APIs support scrolling:
```python
# Initial request
POST /search/es_dsl
{
    "query": {...},
    "scroll": "1m"  # Keep context alive for 1 minute
}

# Subsequent requests
POST /_search/scroll
{
    "scroll_id": "abc123...",
    "scroll": "1m"
}
```

### Option 3: Search After Pattern
```python
# First batch
{
    "query": {...},
    "size": 100,
    "sort": ["_score", {"employee_id": "asc"}]
}

# Next batch (using last result as cursor)
{
    "query": {...},
    "size": 100,
    "search_after": [0.95, "employee_12345"],  # Last score and ID
    "sort": ["_score", {"employee_id": "asc"}]
}
```

## ID-Centric Architecture

```python
class IDFirstSearchManager:
    """
    Separate ID discovery from profile fetching for better pagination.
    """

    def __init__(self):
        self.discovered_ids = []
        self.fetched_profiles = {}
        self.search_query = None

    def discover_all_ids(self, query):
        """
        Step 1: Get ALL matching employee IDs (not profiles).
        Try multiple methods to bypass pagination limits.
        """
        all_ids = []

        # Method 1: Preview endpoint (guaranteed to work)
        preview_ids = self.fetch_preview_pages(query, pages=5)
        all_ids.extend(preview_ids)  # First 100

        # Method 2: Try full search with offset
        if self.supports_offset():
            offset_ids = self.fetch_with_offset(query, from_=100, size=900)
            all_ids.extend(offset_ids)  # Next 900

        # Method 3: Try search_after
        elif self.supports_search_after():
            last_id = preview_ids[-1]
            more_ids = self.fetch_search_after(query, after=last_id, size=900)
            all_ids.extend(more_ids)

        # Method 4: Query modifications (fallback)
        else:
            # Your time-window approach
            for year in [2023, 2022, 2021]:
                year_ids = self.fetch_by_year(query, year)
                all_ids.extend(year_ids)

        self.discovered_ids = list(set(all_ids))  # Deduplicate
        return len(self.discovered_ids)

    def fetch_profiles_batch(self, start_idx=0, batch_size=20):
        """
        Step 2: Fetch full profiles for a batch of IDs.
        This is where we consume API credits.
        """
        batch_ids = self.discovered_ids[start_idx:start_idx + batch_size]

        profiles = []
        for emp_id in batch_ids:
            # Check cache first
            if emp_id in self.fetched_profiles:
                profiles.append(self.fetched_profiles[emp_id])
            else:
                # Fetch from API
                profile = fetch_employee_by_id(emp_id)
                self.fetched_profiles[emp_id] = profile
                profiles.append(profile)

        return profiles
```

## Testing Different Search Methods

```python
def test_search_capabilities():
    """Test what search methods CoreSignal supports."""

    base_query = {
        "query": {
            "match": {"location_country": "United States"}
        }
    }

    tests = [
        {
            "name": "Offset Support",
            "query": {**base_query, "from": 100, "size": 20},
            "endpoint": "/search/es_dsl"
        },
        {
            "name": "Search After",
            "query": {
                **base_query,
                "search_after": [1.0, "emp_123"],
                "sort": ["_score", {"employee_id": "asc"}]
            },
            "endpoint": "/search/es_dsl"
        },
        {
            "name": "Scroll API",
            "query": {**base_query, "scroll": "1m"},
            "endpoint": "/search/es_dsl"
        },
        {
            "name": "Higher Page Limit",
            "query": base_query,
            "endpoint": "/search/es_dsl?page=10"
        }
    ]

    for test in tests:
        print(f"\nTesting: {test['name']}")
        response = make_request(test['endpoint'], test['query'])
        print(f"Result: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ {test['name']} SUPPORTED!")
```

## The Optimal Flow

```
1. DISCOVERY PHASE (Get IDs only)
   ├─ Preview API → 100 IDs (guaranteed)
   ├─ Try offset/scroll → 900 more IDs (if supported)
   └─ Store all 1000 IDs (lightweight, no credit cost)

2. PROGRESSIVE LOADING (On-demand profiles)
   ├─ User views first 20 → Fetch 20 profiles (cached)
   ├─ User scrolls → Fetch next 20 profiles
   ├─ User exports → Fetch remaining profiles
   └─ Total control over credit consumption
```

## Benefits of ID-First Approach

### 1. **Maintains Search Quality**
- Same query throughout = consistent quality
- No need to modify criteria

### 2. **Better Caching**
- IDs are tiny (just integers)
- Can cache thousands of IDs easily
- Fetch profiles only when needed

### 3. **Progressive Cost**
```python
# Current approach: Fetch all profiles upfront
cost = 100 profiles × $0.20 = $20

# ID-first approach: Fetch on-demand
cost = {
    "Discovery": $0 (just IDs),
    "First view": 20 × $0.20 = $4,
    "If user continues": 80 × $0.20 = $16,
    "If user stops": $0 saved
}
```

### 4. **Better UX**
```javascript
// Show total available immediately
"Found 847 matching candidates"

// Load progressively
[Show 20] [Load 50 more] [Load all 847]

// User knows full scope upfront
```

## Implementation Priority

1. **Test if CoreSignal supports offset/scroll** (I can write a test)
2. **If yes**: Implement ID-first architecture
3. **If no**: Use your time-window approach (maintains quality)
4. **Cache aggressively**: Store IDs for 24 hours

## Next Step Test Script

```python
# test_advanced_search.py
def test_coresignal_advanced_search():
    """Test if CoreSignal supports offset, scroll, or search_after."""

    # Test 1: Does /search/es_dsl (without /preview) exist?
    # Test 2: Does it support "from" parameter?
    # Test 3: Does it support "search_after"?
    # Test 4: Does it return more than 100 results?

    # This will tell us our options
```

Want me to test these alternative endpoints to see if we can get more than 100 IDs from a single query?