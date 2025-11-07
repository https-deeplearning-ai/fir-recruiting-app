# Domain Search Credit Optimization Plan

**Goal:** Implement persistent caching to eliminate duplicate API calls and maximize credit utilization

**Expected Savings:** 84% credit reduction on repeat searches (675 credits / $135 saved per 10 searches)

---

## Progress Overview

- [x] **Phase 1:** CoreSignal API Taxonomy (720 lines) - COMPLETE
- [x] **Phase 2:** Stages 1-3 Implementation - COMPLETE
- [x] **Phase 3:** Stage 4 AI Evaluation with SSE - COMPLETE
- [x] **Phase 4:** Fix Company Name Extraction Regex - COMPLETE
- [x] **Phase 5:** Fix Credit Consumption Bug - COMPLETE
- [x] **Phase 6:** Domain Search Caching Integration - COMPLETE ✅
- [ ] **Phase 7:** Testing & Validation (NEXT)
- [ ] **Phase 8:** Documentation Updates

---

## Phase 6: Domain Search Caching Integration

### Task 1.1: Extract Storage Functions to Shared Module
- [x] Create `/backend/utils/supabase_storage.py`
- [x] Move `get_supabase_client()` from app.py (lines 95-118)
- [x] Move `get_stored_profile()` from app.py (lines 194-251)
- [x] Move `save_stored_profile()` from app.py (lines 194-251)
- [x] Move `get_stored_company()` from app.py (lines 282-337)
- [x] Move `save_stored_company()` from app.py (lines 340-368)
- [x] Add error handling and retry logic
- [x] Add module docstring with usage examples

**Files Modified:** `utils/supabase_storage.py` (NEW), `app.py` (REFACTOR)
**Estimated Time:** 20 minutes
**Status:** COMPLETE ✅

---

### Task 1.2: Add Profile Caching to domain_search.py
- [x] Import storage functions at top of domain_search.py
- [x] Update Stage 3 profile fetching (line 718)
- [x] Check cache before calling `fetch_linkedin_profile_by_id()`
- [x] Save to cache after successful fetch
- [x] Track cache hit/miss in result dict
- [x] Add logging for cache performance

**Files Modified:** `jd_analyzer/api/domain_search.py` (lines 37-43, 725-764)
**Estimated Time:** 15 minutes
**Status:** COMPLETE ✅

**Before:**
```python
result = service.fetch_linkedin_profile_by_id(employee_id)
```

**After:**
```python
# Check cache first
cached_profile = get_stored_profile(f"id:{employee_id}")
if cached_profile:
    result = {'success': True, 'profile_data': cached_profile, 'from_cache': True}
else:
    result = service.fetch_linkedin_profile_by_id(employee_id)
    if result.get('success'):
        save_stored_profile(f"id:{employee_id}", result['profile_data'], time.time())
```

---

### Task 1.3: Add Company Caching to domain_search.py
- [x] Pass `storage_functions` dict to `enrich_profile_with_company_data()`
- [x] Verify coresignal_service.py uses storage functions correctly
- [x] Test company cache hit/miss tracking

**Files Modified:** `jd_analyzer/api/domain_search.py` (lines 755-764)
**Estimated Time:** 10 minutes
**Status:** COMPLETE ✅

**Before:**
```python
enriched = service.enrich_profile_with_company_data(profile, min_year=min_year)
```

**After:**
```python
storage_functions = {
    'get': get_stored_company,
    'save': save_stored_company
}
enriched = service.enrich_profile_with_company_data(
    profile,
    min_year=min_year,
    storage_functions=storage_functions
)
```

---

### Task 1.4: Add Cache Statistics to Session Logs
- [x] Update collected_profiles dict to include cache_info
- [x] Add cache performance section to Stage 3 summary (lines 795-830)
- [x] Calculate and log credit savings percentage
- [x] Add cache stats to 03_collection_summary.txt

**Files Modified:** `jd_analyzer/api/domain_search.py` (lines 766-779, 827-838, 858-901)
**Estimated Time:** 15 minutes
**Status:** COMPLETE ✅

**New fields in collected_profiles:**
```python
"cache_info": {
    "profile_from_cache": True/False,
    "companies_from_cache": 15,  # Count
    "companies_fetched": 3,       # Count
}
```

**New summary section:**
```
CACHE PERFORMANCE:
  Profiles from cache: 18/20 (90%)
  Companies from cache: 54/60 (90%)
  Companies fetched: 6/60 (10%)
  Credit savings: 90%
```

---

## Phase 7: Testing & Validation

### Task 5.1: Test Cache Cold Start (First Search)
- [ ] Run `test_complete_4stage_pipeline.py` with max_previews=5
- [ ] Verify 0 cache hits on first run
- [ ] Check Supabase: 5 new profiles, ~15-20 new companies
- [ ] Verify session log shows cache stats
- [ ] Expected credits: ~20-25

**Estimated Time:** 10 minutes
**Status:** PENDING

---

### Task 5.2: Test Cache Warm Start (Second Search)
- [ ] Run same test again immediately
- [ ] Verify 100% profile cache hit rate
- [ ] Verify ~90% company cache hit rate
- [ ] Check session log shows cache savings
- [ ] Expected credits: ~0-2 (94% savings)

**Estimated Time:** 10 minutes
**Status:** PENDING

---

### Task 5.3: Validate Supabase Data
- [ ] Query `stored_profiles` table - verify 5 entries
- [ ] Query `stored_companies` table - verify 15-20 entries
- [ ] Check `fetched_at` timestamps are recent
- [ ] Verify `profile_data` and `company_data` JSONB fields are populated
- [ ] Test freshness logic (3-day, 30-day rules)

**Estimated Time:** 10 minutes
**Status:** PENDING

---

## Phase 8: Documentation Updates

### Task 6.1: Update IMPLEMENTATION_COMPLETE.md
- [ ] Add "Persistent Caching System" section
- [ ] Document cache architecture diagram
- [ ] Explain freshness rules (3/90 days, 30 days)
- [ ] Add expected cache hit rates over time
- [ ] Include credit savings analysis

**Estimated Time:** 10 minutes
**Status:** PENDING

---

### Task 6.2: Update CLAUDE.md
- [ ] Add caching guidelines section
- [ ] Document storage_functions usage
- [ ] Explain cache statistics in session logs
- [ ] Add freshness rules reference

**Estimated Time:** 5 minutes
**Status:** PENDING

---

### Task 6.3: Clean Up Test Files
- [ ] Archive old test sessions (keep most recent)
- [ ] Remove test log files (api_debug.log, test_with_ids.log, etc.)
- [ ] Kill all background Python processes
- [ ] Clean up test scripts if not needed

**Estimated Time:** 5 minutes
**Status:** PENDING

---

## Expected Outcomes

### Before Caching (Current State)
```
Search 1: 80 credits ($16) - Everything fetched
Search 2: 80 credits ($16) - Everything fetched again ❌
Search 10: 80 credits ($16) - Still fetching everything ❌

Total for 10 searches: 800 credits ($160)
```

### After Caching (Target State)
```
Search 1: 80 credits ($16) - Cold cache, fetch everything
Search 2: 5 credits ($1)   - 94% cache hit rate ✅
Search 3: 5 credits ($1)   - 94% cache hit rate ✅
Search 10: 5 credits ($1)  - 94% cache hit rate ✅

Total for 10 searches: 125 credits ($25)
Savings: 675 credits ($135) - 84% reduction ✅
```

---

## Implementation Notes

### Cache Freshness Rules
- **Profiles:**
  - < 3 days: Use cache (no API call)
  - 3-90 days: Use cache but mark stale (background refresh possible)
  - > 90 days: Force fresh fetch (1 API call)

- **Companies:**
  - < 30 days: Use cache (no API call)
  - > 30 days: Force fresh fetch (1 API call)

### Cache Storage
- **Database:** Supabase PostgreSQL
- **Tables:** `stored_profiles`, `stored_companies`
- **Indexes:** On employee_id, company_id, fetched_at
- **Cleanup:** Automatic via Supabase TTL policies

### Error Handling
- Cache check fails → Fall back to API
- Save fails → Log warning, continue
- Supabase down → Use in-memory session cache as backup

---

## Progress Tracking

**Last Updated:** 2025-11-05
**Current Phase:** 7 (Testing & Validation)
**Current Task:** Ready to begin Phase 7 testing
**Completion:** 75% (6/8 phases complete)

**Time Spent:** ~6 hours
**Time Remaining:** ~2-3 hours
**Blocked By:** None
**Next Milestone:** Complete Phase 6 (caching integration)

---

## Git Commits

- [ ] Commit 1: "feat: Extract Supabase storage functions to shared module"
- [ ] Commit 2: "feat: Add profile and company caching to domain_search.py"
- [ ] Commit 3: "feat: Add cache statistics to session logs"
- [ ] Commit 4: "test: Validate caching with cold and warm start tests"
- [ ] Commit 5: "docs: Update documentation with caching architecture"

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Supabase downtime | High | Low | Fallback to API, session cache |
| Cache staleness | Medium | Medium | TTL-based freshness, background refresh |
| Duplicate cache writes | Low | Low | Check before write, unique constraints |
| Memory overflow | Low | Low | Database storage (not in-memory) |
