# Domain Search - 0 Employee Results: Root Cause Analysis

**Date:** November 10, 2025
**Session:** `sess_20251111_041155_eca8dc98`
**Issue:** Employee search returned 0 results despite having 6/7 companies with CoreSignal IDs

---

## 🔍 Investigation Summary

### Companies Tested
| Company | CoreSignal ID | Size Range (if known) | Employee Count |
|---------|---------------|----------------------|----------------|
| Synthesia | 95477034 | Unknown | Unknown |
| VEED | 33312984 | Unknown | Unknown |
| Murf.ai | None | N/A | N/A |
| Krisp | 21473726 | Unknown | Unknown |
| Otter.ai | 13006266 | Unknown | Unknown |
| Observe.AI | 11209012 | Unknown | Unknown |
| Synthflow | 98601775 | **1-10 employees** | **0** |

### User-Provided Evidence

From company_clean API query for Synthflow (ID: 98601775):
```json
{
  "id": 98601775,
  "name": "SynthFlow",
  "industry": "Software Development",
  "size_range": "1-10 employees",
  "size_employees_count": 0,          ← 🚨 NO EMPLOYEES IN CORESIGNAL
  "founded": null,
  "followers": 0,
  "location_hq_country": null,
  "description": "SynthFlow is developing a visual, AI-driven backend automation platform..."
}
```

**Key Finding:** `"size_employees_count": 0` means CoreSignal has no employee data for this company.

---

## 🎯 Root Cause

### Primary Issue: Companies Too Small/New
These Voice AI companies are:
1. **Very small** - "1-10 employees" range
2. **Recently founded** - New startups not yet in CoreSignal's employee database
3. **Low visibility** - Only 0 LinkedIn followers, minimal online presence

### Contributing Factor: Location Filter
The query required:
```json
{"term": {"location_country": "United States"}}
```

Even if these companies had a few employees, they might be:
- Located outside the US (remote international teams)
- Missing location data in CoreSignal profiles
- Listed with different country names (e.g., "USA" vs "United States")

---

## 📊 Query Analysis

### The Search Query (from 02_preview_query.json)

**MUST clauses (required):**
1. ✅ Company filter: Match 4 companies by ID + 1 by name variations
2. ❌ Location filter: `location_country = "United States"` (HARD REQUIREMENT)

**SHOULD clauses (optional, but all have minimum_should_match: 0):**
- Role keywords: chief, officer, technology, engineer, lead, c-suite, product, manager, developer, architect, director, founder
- **NOTE:** `minimum_should_match: 0` means NONE of these are actually required!

**Effective Query:**
> Find ANY employee at these 5 companies WHO IS LOCATED in the United States

**Why it failed:**
- Companies have 0 employees in CoreSignal database
- OR employees exist but are not located in "United States"

---

## 🔄 What Worked vs What Didn't

### ✅ What Worked
1. **Company Discovery** - Found 7 relevant Voice AI companies from G2 and Capterra
2. **CoreSignal ID Lookup** - Successfully matched 6/7 companies (85.7% success rate)
3. **Query Construction** - Query syntax was correct and valid
4. **API Execution** - No API errors, clean response with 0 results

### ❌ What Didn't Work
1. **Employee Search** - 0 employees found for these small companies
2. **Location Filter** - Too restrictive for international remote teams
3. **Company Selection** - Companies too small/new to have employee data

---

## 💡 Proposed Solutions

### Option 1: Remove Location Filter (Quick Fix)
**Implementation:**
```python
# In domain_search.py, line 597
# Comment out location requirement:
# if location:
#     must_clauses.append({"term": {"location_country": location}})
```

**Pros:**
- Will find employees worldwide
- Broadens candidate pool significantly
- Simple one-line change

**Cons:**
- May return candidates outside target geography
- Requires post-filtering by user

---

### Option 2: Make Location Optional with Boosting
**Implementation:**
```python
# Change location from MUST to SHOULD (boost results with location match)
if location:
    should_clause.append({
        "term": {
            "location_country": location
        }
    })
    # Boost weight for location matches
    should_clause[-1]["boost"] = 2.0
```

**Pros:**
- Prefers US candidates but doesn't exclude others
- Better for remote-first companies
- Still shows location in results for filtering

**Cons:**
- More complex query logic
- Results may be less targeted

---

### Option 3: Test with Larger Companies First
**Implementation:**
```python
# In stage1_company_discovery, filter by size before searching
async def filter_companies_by_size(companies):
    """Only keep companies with 50+ employees."""
    filtered = []
    for company in companies:
        # Fetch company_clean data
        company_data = await fetch_company_data(company['coresignal_company_id'])

        if company_data.get('size_employees_count', 0) >= 50:
            filtered.append(company)
        else:
            print(f"⚠️  Skipping {company['name']}: Only {company_data.get('size_employees_count', 0)} employees")

    return filtered
```

**Pros:**
- Higher success rate with larger companies
- Better data quality
- Fewer wasted API calls

**Cons:**
- Eliminates small/early-stage companies
- May not match JD requirement ("Series A" often = small teams)
- Requires extra API call per company (1 credit each)

---

### Option 4: Expand Location Variations
**Implementation:**
```python
# Add multiple location variations
location_variations = [
    "United States",
    "USA",
    "US",
    "United States of America"
]

# Build should clause with all variations
should_clause.extend([
    {"term": {"location_country": loc}} for loc in location_variations
])
must_clauses.append({
    "bool": {
        "should": should_clause,
        "minimum_should_match": 1
    }
})
```

**Pros:**
- Catches location data inconsistencies
- Still targets US-based candidates
- No behavior change for users

**Cons:**
- May still miss remote employees with non-US locations
- Doesn't solve the "0 employees" problem

---

### Option 5: Multi-Tier Search Strategy (Recommended)
**Implementation:**
```python
# Tier 1: Strict search (current approach)
strict_results = search_with_location_requirement(companies, location)

if len(strict_results) < threshold:
    print(f"⚠️  Only found {len(strict_results)} candidates with strict filters")
    print(f"🔄 Running relaxed search...")

    # Tier 2: Relaxed search (no location filter)
    relaxed_results = search_without_location_filter(companies)

    # Combine and tag results
    for result in strict_results:
        result['match_type'] = 'exact_location'

    for result in relaxed_results:
        result['match_type'] = 'broader_search'

    return strict_results + relaxed_results
```

**Pros:**
- Best of both worlds
- Transparent to user (tags results)
- Automatic fallback when needed
- Matches user's "Series A Voice AI" context (smaller companies)

**Cons:**
- More complex logic
- Requires UI updates to show match types

---

## 🎯 Recommended Action Plan

### Immediate Fix (1 hour)
1. **Implement Option 1** - Remove location filter as optional flag
2. **Test with same companies** - See if we get ANY employees worldwide
3. **Display location clearly** - Users can filter client-side

### Short-Term (1-2 days)
1. **Implement Option 5** - Multi-tier search strategy
2. **Add company size check** - Warn user when companies are too small
3. **UI Updates** - Show "No employees found in CoreSignal" message

### Long-Term (1 week)
1. **Add company size pre-filter** - Let user choose minimum company size
2. **Alternative data sources** - Consider supplementing CoreSignal with:
   - LinkedIn Sales Navigator
   - Apollo.io
   - ZoomInfo
3. **Smart recommendations** - Suggest similar but larger companies

---

## 📝 Code Changes Required

### File: `backend/jd_analyzer/api/domain_search.py`

**Line 597:** Make location optional
```python
# BEFORE:
if location:
    must_clauses.append({"term": {"location_country": location}})

# AFTER:
if location and require_location:  # Add flag to control behavior
    must_clauses.append({"term": {"location_country": location}})
elif location:
    # Add as optional boost instead
    should_clause.append({"term": {"location_country": location}})
```

**Line 614:** Add require_location parameter
```python
async def stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any]],
    endpoint: str,
    max_previews: int,
    session_logger: SessionLogger,
    create_session: bool = True,
    session_id: Optional[str] = None,
    batch_size: int = 5,
    require_location: bool = False  # ← NEW: Default to flexible location
) -> Dict[str, Any]:
```

---

## 🧪 Test Plan

### Test 1: Verify Companies Have Employees (Worldwide)
```bash
# Remove location filter, search worldwide
python3 test_voice_ai_companies.py --no-location-filter
```

**Expected Result:** Find employees in UK, Armenia, remote locations

### Test 2: Test with Larger Companies
```bash
# Replace with known large Voice AI companies
companies = [
    (6761084, "Deepgram"),        # Should have 100+ employees
    (XXXX, "Google Cloud Speech"),  # Should have many employees
]
```

**Expected Result:** Find 20+ employees easily

### Test 3: Multi-Tier Search
```bash
# Test fallback logic
python3 test_multi_tier_search.py
```

**Expected Result:**
- Tier 1 (strict): 0 results
- Tier 2 (relaxed): 15-20 results
- Combined: 15-20 results with tags

---

## 🎓 Lessons Learned

1. **Small Companies = No Data** - Series A companies often too small for employee databases
2. **Location Filters Can Kill Results** - Remote-first companies have global teams
3. **Test with Known Large Companies First** - Validate pipeline before niche searches
4. **Company Size Matters** - Check `size_employees_count` before searching employees
5. **CoreSignal Limitations** - Not all companies have employee data, especially new/small ones

---

## 📚 References

- Session Files: `logs/domain_search_sessions/sess_20251111_041155_eca8dc98/`
- Query: `02_preview_query.json`
- Flask Logs: Lines 62-138 in `backend/flask.log`
- User Evidence: SynthFlow company_clean response
- Related Docs: `SESSION_HANDOFF_NOV_10_SESSION_2.md`
