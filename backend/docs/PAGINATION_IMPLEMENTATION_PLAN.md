# Domain Search Pagination Implementation Plan

## Executive Summary
Enable users to fetch more than 20 preview candidates by implementing pagination in the domain search pipeline's Stage 2.

## Current Limitations
- **Hard limit**: 20 candidates max (1 page from CoreSignal)
- **User impact**: Can't explore beyond initial results even if query is good
- **API waste**: May miss better candidates on pages 2-5

## Implementation Plan

### Phase 1: Backend Enhancement (2 hours)

#### 1.1 Update `search_profiles_with_endpoint` Function
**File**: `coresignal_service.py`
**Changes**:
```python
def search_profiles_with_endpoint(
    query: Dict[str, Any],
    endpoint: str = "employee_clean",
    max_results: int = 20,
    page_start: int = 1  # NEW: Starting page
) -> Dict[str, Any]:
    """
    Enhanced with pagination support.

    Args:
        query: ES DSL query
        endpoint: CoreSignal endpoint
        max_results: Total results to fetch (can be > 20)
        page_start: Starting page number (for "Load More")
    """
    results = []
    total_pages = math.ceil(max_results / 20)

    for page in range(page_start, min(page_start + total_pages, 6)):
        # Fetch page with ?page={page} parameter
        # Add 2s delay between pages to avoid rate limits
        # Combine results
        # Stop when max_results reached
```

#### 1.2 Update Stage 2 Preview Search
**File**: `jd_analyzer/api/domain_search.py`
**Changes**:
```python
async def stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    page_start: int = 1,  # NEW: For pagination
    session_logger: SessionLogger
):
    # Use enhanced search function with pagination
    search_result = search_profiles_with_endpoint(
        query=query,
        endpoint=endpoint,
        max_results=max_previews,
        page_start=page_start
    )
```

### Phase 2: API Endpoints (1 hour)

#### 2.1 Add "Load More" Endpoint
**File**: `jd_analyzer/api/endpoints.py`
**New Endpoint**: `/api/jd/domain-load-more-previews`
```python
@bp.route('/domain-load-more-previews', methods=['POST'])
async def domain_load_more_previews():
    """
    Load additional preview candidates beyond initial 20.

    Request:
    {
        "session_id": "abc123",
        "current_count": 20,
        "additional_count": 20  # Fetch 20 more
    }

    Response:
    {
        "previews": [...],  # New candidates
        "total_loaded": 40,
        "has_more": true,   # Can load more (up to 100)
        "max_available": 100
    }
    """
```

#### 2.2 Update Initial Search Response
**Endpoint**: `/api/jd/domain-company-preview-search`
**Changes**:
```python
return {
    "stage1_companies": companies,
    "stage2_previews": previews[:20],  # Initial 20
    "pagination": {
        "total_found": total_count,
        "loaded": 20,
        "has_more": total_count > 20,
        "max_available": min(total_count, 100)  # Cap at 100
    }
}
```

### Phase 3: Frontend Integration (2 hours)

#### 3.1 UI Components
```jsx
// DomainSearchResults.js
const DomainSearchResults = ({ results }) => {
  const [previews, setPreviews] = useState(results.stage2_previews);
  const [loading, setLoading] = useState(false);
  const pagination = results.pagination;

  const loadMore = async () => {
    setLoading(true);
    const response = await fetch('/api/jd/domain-load-more-previews', {
      method: 'POST',
      body: JSON.stringify({
        session_id: results.session_id,
        current_count: previews.length,
        additional_count: 20
      })
    });
    const data = await response.json();
    setPreviews([...previews, ...data.previews]);
    setLoading(false);
  };

  return (
    <div>
      {/* Preview cards */}
      {previews.map(preview => <PreviewCard key={preview.id} {...preview} />)}

      {/* Load More Button */}
      {pagination.has_more && (
        <div className="load-more-container">
          <p>Showing {previews.length} of {pagination.max_available} available</p>
          <button onClick={loadMore} disabled={loading}>
            {loading ? 'Loading...' : 'Load 20 More Candidates'}
          </button>
        </div>
      )}
    </div>
  );
};
```

#### 3.2 Progressive Loading States
```
Initial Load: "Found 87 candidates, showing top 20"
After Load More: "Showing 40 of 87 candidates"
At Maximum: "Showing all 87 candidates"
```

### Phase 4: Testing Strategy

#### 4.1 Test Scenarios
1. **Small Result Set** (<20 candidates)
   - No "Load More" button shown
   - All results in initial load

2. **Medium Result Set** (20-100 candidates)
   - "Load More" available
   - Can fetch all results in chunks

3. **Large Result Set** (>100 candidates)
   - Capped at 100 for performance
   - Message: "Showing top 100 of 234 candidates"

#### 4.2 Performance Tests
```python
# test_pagination.py
def test_pagination_performance():
    """Test that pagination doesn't exceed rate limits"""
    # Test fetching 100 candidates (5 pages)
    # Verify 2s delays between pages
    # Check total time < 15s
    # Verify no 429 errors
```

## Benefits

### For Users
1. **Better Exploration**: Can review more candidates if initial 20 look promising
2. **Flexible Discovery**: Load more only when needed (cost-conscious)
3. **Transparency**: See total available vs loaded

### For System
1. **Progressive Cost**: Only pay for API calls when user wants more
2. **Better UX**: Fast initial load (20), optional expansion
3. **Rate Limit Safe**: 2s delays prevent API throttling

## Implementation Timeline
- **Phase 1**: Backend (2 hours)
- **Phase 2**: API Endpoints (1 hour)
- **Phase 3**: Frontend (2 hours)
- **Phase 4**: Testing (1 hour)
- **Total**: 6 hours

## API Credit Impact
```
Current: 20 candidates max = 1 credit (1 API call)
With Pagination:
- 20 candidates = 1 credit (no change for basic use)
- 40 candidates = 2 credits
- 60 candidates = 3 credits
- 100 candidates = 5 credits (max)
```

## Risk Mitigation
1. **Rate Limits**: 2-second delay between pages
2. **Timeout**: 30s timeout per page fetch
3. **Error Recovery**: If page 3 fails, return pages 1-2
4. **Cost Control**: Hard cap at 100 candidates (5 pages)

## Success Metrics
- Users load beyond 20 candidates in 30% of searches
- Average candidates reviewed: 35 (up from 20)
- No increase in API errors or timeouts
- User satisfaction: "I can finally see all relevant candidates!"

## Next Steps
1. Review plan with team
2. Create feature branch `feature/domain-search-pagination`
3. Implement Phase 1 (backend) first
4. Test with real queries before frontend work