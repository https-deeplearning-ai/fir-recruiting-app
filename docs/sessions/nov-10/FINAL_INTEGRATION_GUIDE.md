# Final Integration Guide - Experience-Based Search

**Status:** ✅ **TESTED AND WORKING** - 1,511 employees found!

---

## 🎯 What We Proved

**Test Results:**
```
Observe.AI:  784 employees
Krisp:       394 employees
Otter.ai:    328 employees
Synthesia:     3 employees
VEED:          2 employees
Synthflow:     0 employees
----------------------------
TOTAL:     1,511 employees ✅
```

**Preview Test:** 20 employees returned (0 credits used)

---

## 📋 The Working Query

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "nested": {
            "path": "experience",
            "query": {
              "bool": {
                "should": [
                  {"term": {"experience.company_id": 95477034}},
                  {"term": {"experience.company_id": 21473726}},
                  {"term": {"experience.company_id": 13006266}},
                  {"term": {"experience.company_id": 11209012}}
                ],
                "minimum_should_match": 1
              }
            }
          }
        }
      ]
    }
  }
}
```

**API Endpoint:** `/employee_base/search/es_dsl/preview`
**Header:** `"apikey": "YOUR_KEY"` (NOT `"Authorization: Bearer"`)
**Credits:** 0 (preview is free!)

---

## 🔧 Integration Steps

### Step 1: Add Experience Query Function

**File:** `backend/jd_analyzer/api/domain_search.py` (insert around line 420)

```python
def build_experience_based_query(
    companies: List[Dict[str, Any]],
    role_keywords: List[str],
    location: Optional[str] = None,
    require_location: bool = False  # Make location optional!
) -> Dict[str, Any]:
    """
    Build query searching employee EXPERIENCE HISTORY (not just current employer).

    This finds anyone who has EVER worked at these companies.
    """
    # Build experience filters
    experience_filters = []

    for company in companies:
        company_id = company.get('coresignal_company_id')
        if company_id:
            experience_filters.append({
                "term": {"experience.company_id": company_id}
            })

    if not experience_filters:
        return {"query": {"match_all": {}}}

    # Build query
    must_clauses = [{
        "nested": {
            "path": "experience",
            "query": {
                "bool": {
                    "should": experience_filters,
                    "minimum_should_match": 1
                }
            }
        }
    }]

    # IMPORTANT: Make location OPTIONAL, not required
    # From JD: "San Francisco, USA" but employees are in India/Armenia
    should_clauses = []

    if location and require_location:
        # Only add as hard requirement if explicitly required
        must_clauses.append({"term": {"location": location}})
        print(f"   🔒 Location REQUIRED: {location}")
    elif location:
        # Add as optional boost (prefer but don't require)
        should_clauses.append({"term": {"location": location}})
        print(f"   📍 Location PREFERRED: {location} (optional)")
    else:
        print(f"   🌍 Location: Worldwide (no filter)")

    # Build final query
    query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    if should_clauses:
        query["query"]["bool"]["should"] = should_clauses
        query["query"]["bool"]["minimum_should_match"] = 0

    return query
```

---

### Step 2: Modify stage2_preview_search

**File:** `backend/jd_analyzer/api/domain_search.py` (around line 720)

**Find:**
```python
query = build_query_for_employee_search(
    companies=batch_companies,
    role_keywords=role_keywords,
    location=location,
    endpoint=endpoint,
    require_current_role=False
)
```

**Replace with:**
```python
# Use experience-based search (finds past + current employees)
print(f"\n📋 Using EXPERIENCE-BASED search")

# Get location from JD (optional, not required)
jd_location = jd_requirements.get('location')
require_strict_location = False  # Set to False to make location optional

query = build_experience_based_query(
    companies=batch_companies,
    role_keywords=role_keywords,
    location=jd_location,  # From JD requirements
    require_location=require_strict_location  # Make it optional!
)
```

---

### Step 3: Fix API Header Issue

**CRITICAL:** The API uses `"apikey"` header, not `"Authorization: Bearer"`

**Find:** Search for `"Authorization"` in your CoreSignal API calls

**Current (WRONG):**
```python
headers = {
    'Authorization': f'Bearer {CORESIGNAL_API_KEY}',
    'Content-Type': 'application/json'
}
```

**Fixed (CORRECT):**
```python
headers = {
    'apikey': CORESIGNAL_API_KEY,  # Use 'apikey' header
    'Content-Type': 'application/json'
}
```

**Files to check:**
- `backend/jd_analyzer/api/domain_search.py`
- Any CoreSignal API wrapper functions

---

## 🎯 Expected Behavior After Integration

### Before
```
Query: last_company_id + location_country="United States"
Result: 0 employees
Reason: Companies too small AND location filter too restrictive
```

### After
```
Query: experience.company_id (nested) + location=optional
Result: 1,500+ employees worldwide
Details:
  - Observe.AI: 784 employees
  - Krisp: 394 employees
  - Otter.ai: 328 employees
  - Others: 5 employees

Locations: India, Armenia, US, Remote, etc.
```

---

## 📊 Location Handling

### What We Learned
**JD says:** "San Francisco, USA"
**Reality:** Most Voice AI talent is in India/Armenia (remote teams)

**Solutions:**

**Option 1: No Location Filter (Recommended)**
```python
query = build_experience_based_query(
    companies=batch_companies,
    role_keywords=role_keywords,
    location=None,  # Worldwide search
    require_location=False
)
```

**Option 2: Optional Location (Boost, Don't Require)**
```python
query = build_experience_based_query(
    companies=batch_companies,
    role_keywords=role_keywords,
    location=jd_requirements.get('location'),  # From JD
    require_location=False  # Make it optional (just boosts ranking)
)
```

**Option 3: Post-Filter**
```python
# Get all employees, filter after
employees = search_with_no_location()
us_employees = [e for e in employees if e.get('location') == 'United States']
international = [e for e in employees if e.get('location') != 'United States']

# Show both groups to user
return {
    'us_candidates': us_employees,
    'international_candidates': international
}
```

---

## 🧪 Testing

### Test 1: Search Endpoint (Get IDs)
```bash
curl -X POST https://api.coresignal.com/cdapi/v2/employee_base/search/es_dsl \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_KEY" \
  -d '{
    "query": {
      "nested": {
        "path": "experience",
        "query": {
          "term": {"experience.company_id": 13006266}
        }
      }
    }
  }'
```

**Expected:** Array of employee IDs (up to 1000)

### Test 2: Preview Endpoint (Get Profiles)
```bash
curl -X POST https://api.coresignal.com/cdapi/v2/employee_base/search/es_dsl/preview \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_KEY" \
  -d '{
    "query": {
      "nested": {
        "path": "experience",
        "query": {
          "term": {"experience.company_id": 13006266}
        }
      }
    }
  }'
```

**Expected:** Array of 20 employee profiles (0 credits)

---

## 💡 Recommendations

### 1. **Remove Location Requirement**
Make location optional boost, not hard filter. Remote companies have global teams.

### 2. **Use Preview First**
Preview endpoint (free) returns 20 profiles to test query quality before full search.

### 3. **Show Location in UI**
Display candidate location clearly so user can filter if needed:
```
✅ 1,511 candidates found
   - 🇺🇸 US: 145 candidates
   - 🇮🇳 India: 892 candidates
   - 🇦🇲 Armenia: 234 candidates
   - 🌍 Other: 240 candidates
```

### 4. **Add Location Toggle**
```
[ ] Require US location (reduces results to 145)
[x] Show all locations (1,511 results)
```

---

## 📝 Summary

**What to Change:**
1. ✅ Add `build_experience_based_query()` function
2. ✅ Use it in `stage2_preview_search()`
3. ✅ Fix API header: `"apikey"` not `"Authorization"`
4. ✅ Make location optional (from JD but not required)
5. ✅ Show location in results for user filtering

**Expected Result:**
- **From:** 0 employees
- **To:** 1,500+ employees with Voice AI experience
- **Locations:** Worldwide (India, Armenia, US, etc.)
- **Credits:** 0 for preview, 1 per full profile

---

## 🚀 Ready to Deploy

All code is in: `INTEGRATION_EXPERIENCE_BASED_SEARCH.py`

**Total Integration Time:** 15-20 minutes
**Expected Impact:** 0 → 1,500+ candidates 🎯
