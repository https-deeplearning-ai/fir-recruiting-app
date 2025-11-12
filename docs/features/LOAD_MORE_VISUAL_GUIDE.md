# Domain Search "Load More" Visual Guide

## How It Works: From 20 to 100 Candidates

```
┌──────────────────────────────────────────────────────────────┐
│                     INITIAL SEARCH                           │
├──────────────────────────────────────────────────────────────┤
│  User: "Find Voice AI engineers"                             │
│    ↓                                                          │
│  Stage 1: Discover 15 companies (Deepgram, Otter.ai, etc.)   │
│    ↓                                                          │
│  Stage 2: Fetch Page 1 (20 candidates) ← YOU START HERE      │
│    ↓                                                          │
│  Response: {                                                 │
│    "stage2_previews": [20 candidates],                       │
│    "pagination": {                                           │
│      "has_more": true,                                       │
│      "session_id": "domain_search_xyz123",                   │
│      "total_available": 87  // Estimated                     │
│    }                                                          │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘

                            ↓ User sees 20 candidates
                            ↓ Clicks "Load More"

┌──────────────────────────────────────────────────────────────┐
│                     LOAD MORE - ROUND 1                      │
├──────────────────────────────────────────────────────────────┤
│  Frontend: POST /api/jd/domain-load-more-previews            │
│  {                                                            │
│    "session_id": "domain_search_xyz123",                     │
│    "current_count": 20,                                      │
│    "load_count": 20                                          │
│  }                                                            │
│    ↓                                                          │
│  Backend:                                                     │
│    1. Load saved query from session                          │
│    2. Wait 2 seconds (rate limit)                            │
│    3. Fetch Page 2 from CoreSignal                           │
│    4. Return 20 more candidates                              │
│    ↓                                                          │
│  Response: {                                                 │
│    "candidates": [20 new candidates],                        │
│    "pagination": {                                           │
│      "new_total": 40,                                        │
│      "has_more": true,                                       │
│      "can_load_count": 20                                    │
│    }                                                          │
│  }                                                            │
└──────────────────────────────────────────────────────────────┤

                            ↓ User now has 40 candidates
                            ↓ Can click "Load More" again

┌──────────────────────────────────────────────────────────────┐
│                     LOAD MORE - ROUND 2                      │
├──────────────────────────────────────────────────────────────┤
│  Frontend: POST /api/jd/domain-load-more-previews            │
│  {                                                            │
│    "session_id": "domain_search_xyz123",                     │
│    "current_count": 40,                                      │
│    "load_count": 20                                          │
│  }                                                            │
│    ↓                                                          │
│  Backend: Fetches Page 3 → Returns 20 more                   │
│    ↓                                                          │
│  User now has: 60 candidates                                 │
└──────────────────────────────────────────────────────────────┤

                            ↓ Continue until...

┌──────────────────────────────────────────────────────────────┐
│                         FINAL STATE                          │
├──────────────────────────────────────────────────────────────┤
│  After 5 rounds (or less if results run out):                │
│                                                               │
│  Total Candidates: 87 (all available)                        │
│  Pages Fetched: 5                                            │
│  API Calls: 5                                                │
│  Credits Used: 5                                             │
│                                                               │
│  UI Shows: "✅ All available candidates loaded (87 total)"    │
└──────────────────────────────────────────────────────────────┘
```

## UI Flow Diagram

```
┌─────────────────────────────────────────────┐
│            CANDIDATE LIST VIEW              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────┐           │
│  │  Candidate 1: John Smith     │           │
│  │  Deepgram • ML Engineer      │           │
│  └─────────────────────────────┘           │
│                                             │
│  ┌─────────────────────────────┐           │
│  │  Candidate 2: Jane Doe       │           │
│  │  Otter.ai • Senior Engineer  │           │
│  └─────────────────────────────┘           │
│                                             │
│         ... 18 more candidates ...         │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │      LOAD MORE CANDIDATES           │   │  ← Initial state
│  │   Showing 20 of 87 available        │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
                    ↓ Click

┌─────────────────────────────────────────────┐
│            LOADING STATE                    │
├─────────────────────────────────────────────┤
│                                             │
│         ... 20 candidates shown ...         │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │         Loading...                  │   │  ← Loading
│  │   ████████░░░░░░░░░░░              │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
                    ↓ 3 seconds

┌─────────────────────────────────────────────┐
│            EXPANDED VIEW                    │
├─────────────────────────────────────────────┤
│                                             │
│         ... 40 candidates shown ...         │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │      LOAD MORE CANDIDATES           │   │  ← Can load more
│  │   Showing 40 of 87 available        │   │
│  │   • 2 more pages available          │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

## Implementation Status

### ✅ What We've Built
1. **Pagination Logic** (`domain_search_pagination.py`)
   - DomainSearchPagination class
   - Session state management
   - Multi-page fetching with rate limits

2. **API Endpoint** (`load_more_endpoint.py`)
   - `/api/jd/domain-load-more-previews`
   - Session validation
   - Progressive loading

3. **Enhanced Search** (`coresignal_service_paginated.py`)
   - Multi-page support in search function
   - Rate limit protection (2s between pages)
   - Error recovery

### 🔨 What Needs Integration

1. **Update domain_search.py Stage 2**:
```python
# Add pagination info to response
return {
    "stage2_previews": previews[:20],  # Only return first 20
    "pagination": {
        "session_id": session_id,
        "has_more": total_available > 20,
        "total_available": min(100, total_available)
    }
}
```

2. **Register the new endpoint in endpoints.py**:
```python
from .load_more_endpoint import load_more_previews
# Add route registration
```

3. **Add React component to frontend**:
```jsx
// In DomainSearchResults component
{pagination.has_more && (
  <LoadMoreButton
    sessionId={pagination.session_id}
    currentCandidates={candidates}
    onLoadMore={handleLoadMore}
  />
)}
```

## Benefits Summary

### For Users
- **Start Fast**: See first 20 candidates immediately
- **Load on Demand**: Only fetch more if initial results look good
- **Cost Conscious**: Pay for extra API calls only when needed
- **Transparency**: Always know how many candidates are available

### For System
- **Progressive Cost**: 1 credit for first 20, up to 5 credits for 100
- **Rate Limit Safe**: 2-second delays prevent API throttling
- **Session Based**: Each search maintains its own pagination state
- **Error Recovery**: If page 3 fails, still have pages 1-2

## Credit Economics

```
Scenario 1: User happy with first 20
  Credits used: 1
  Cost: $0.20

Scenario 2: User loads 60 candidates
  Credits used: 3
  Cost: $0.60

Scenario 3: User loads all 100 candidates
  Credits used: 5
  Cost: $1.00

Average usage (estimated): 2.5 credits ($0.50)
```

## Testing the Implementation

```bash
# 1. Start Flask server
cd backend && python3 app.py

# 2. Run initial domain search (gets 20)
curl -X POST http://localhost:5001/api/jd/domain-company-preview-search \
  -H "Content-Type: application/json" \
  -d '{
    "jd_requirements": {
      "target_domain": "voice ai"
    },
    "max_previews": 20
  }'

# 3. Load more (gets next 20)
curl -X POST http://localhost:5001/api/jd/domain-load-more-previews \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "domain_search_xyz123",
    "current_count": 20,
    "load_count": 20
  }'
```

## Next Steps

1. **Priority 1**: Integrate load_more_endpoint.py into existing endpoints
2. **Priority 2**: Update Stage 2 to return pagination info
3. **Priority 3**: Add React component to frontend
4. **Priority 4**: Test with real queries

---

**Summary**: The "Load More" feature is ready to integrate. It allows users to progressively load up to 100 candidates (5 pages × 20 per page) with proper rate limiting and session management. The implementation is backward-compatible - users who don't need more than 20 candidates won't be affected.