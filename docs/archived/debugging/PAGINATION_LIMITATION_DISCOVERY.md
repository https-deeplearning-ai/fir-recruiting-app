# ~~CoreSignal API Pagination Limitation Discovery~~ → RESOLVED! ✅

**Date:** 2025-11-10
**Initial Discovery:** CoreSignal's search endpoints do NOT support pagination (via from/size)
**RESOLUTION:** Pagination DOES work using `?page=N` URL parameter!

## 🎉 UPDATE: PROBLEM SOLVED!

This document was created during initial investigation when we tried incorrect parameter format.

**What we thought:** "CoreSignal doesn't support pagination"
**Reality:** CoreSignal uses `?page=N` URL query parameter (not `from/size` in body)

See `FINAL_SESSION_HANDOFF_NOV_10_2025.md` for success story!

## Problem

We attempted to implement pagination to search through 100 results (5 pages × 20 per page) instead of being limited to 20 results.

**Attempted Implementation:**
```python
payload = {
    "query": {...},
    "from": 0,  # Pagination offset
    "size": 20  # Page size
}
```

## Result

Both endpoints return **422 "Extra inputs not permitted"** errors:

### `/cdapi/v2/company_base/search/es_dsl/preview`
```
Status 422
{"detail":[
    {"type":"extra_forbidden","loc":["body","from"],"msg":"Extra inputs are not permitted","input":0},
    {"type":"extra_forbidden","loc":["body","size"],"msg":"Extra inputs are not permitted","input":20}
]}
```

### `/cdapi/v2/company_base/search/es_dsl`
Same error - pagination parameters not supported.

## Root Cause

CoreSignal's API implementation does not follow standard ElasticSearch DSL pagination conventions. The API:
- Returns max **20 results per search** (hard limit)
- Does not accept `from` or `size` parameters
- Does not provide alternative pagination mechanism

## Impact on Match Rates

**Original Plan:**
- With pagination: Search 100 results → Find exact match in top 100 → **85-90% match rate**

**Reality:**
- Without pagination: Search 20 results → Find exact match in top 20 → **~60% match rate**

**Gap:** ~25-30% of companies that would be found in results 21-100 are now **unfindable**.

## Current Solution

Reverted to using `/preview` endpoint without pagination:
- Returns max 20 results with full company data (0 extra credits)
- Prioritizes exact matches at top of results array
- Accepts API limitation

## Alternative Approaches (Not Implemented)

### Option 1: Multiple Targeted Searches
Instead of one broad search, make multiple specific searches:
```python
# Search 1: Exact company name
search("Krisp")  # 20 results

# Search 2: Company name + industry
search("Krisp noise cancellation")  # Different 20 results

# Search 3: Company name + location
search("Krisp San Francisco")  # Different 20 results
```

**Pros:** Could cover more than 20 total companies
**Cons:** 3x API calls, overlapping results, complex deduplication

### Option 2: Use Different CoreSignal Endpoint
Check if other endpoints support pagination:
- `/cdapi/v2/multi_source_company`?
- `/cdapi/v2/company_clean`?

**Status:** Not explored yet

### Option 3: Accept 20-Result Limitation
Focus on improving match rate within 20 results:
- Better query construction (exact match prioritization) ✅ **IMPLEMENTED**
- Four-tier fallback strategy ✅ **IMPLEMENTED**
- Website-first lookup ✅ **IMPLEMENTED**

## Recommendations

1. **Document Limitation** - Update all docs to reflect 20-result max
2. **Focus on Integration** - Proceed with integrating `lookup_with_fallback()` into production (bigger win than pagination)
3. **Contact CoreSignal** - Ask if pagination is supported via different mechanism
4. **Monitor Coverage** - Track % of companies found vs. total discovered (may need multi-search strategy later)

## Updated Expected Match Rates

| Configuration | Match Rate | Notes |
|---------------|------------|-------|
| **Current (Tier 1-4, no pagination)** | **60-70%** | Limited to 20 results per search |
| **With Production Integration** | **75-80%** | Website lookups work in production |
| **Theoretical Max (with pagination)** | **85-90%** | Would require API support |

## ✅ RESOLUTION (Same Day)

1. ✅ **User provided official CoreSignal documentation** showing `?page=N` syntax
2. ✅ **Implemented pagination correctly** using URL query parameter
3. ✅ **Tested successfully** - Match rate improved from 60% to 80%
4. ✅ **Documented success** in FINAL_SESSION_HANDOFF_NOV_10_2025.md

## Correct Implementation

```python
# WRONG (This document's original attempt):
payload = {"query": {...}, "from": 0, "size": 20}  # ❌ 422 error

# CORRECT (What actually works):
url = f"{base_url}/cdapi/v2/company_base/search/es_dsl/preview?page=3"  # ✅ Works!
```

This document is kept for historical reference. For current implementation, see:
- `backend/coresignal_company_lookup.py` (lines 39-145)
- `FINAL_SESSION_HANDOFF_NOV_10_2025.md`
