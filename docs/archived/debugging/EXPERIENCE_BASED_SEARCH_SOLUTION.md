# Experience-Based Employee Search Solution

**Date:** November 10, 2025
**Purpose:** Find employees who have EVER worked at target companies (not just current employees)

---

## 🎯 The Better Approach

Instead of searching for **current employees** (`last_company_id`), search for **anyone with these companies in their work history** using the nested `experience` field.

### Why This Works Better

**Current Employee Search** (`last_company_id`):
- Only finds people currently employed at the company
- Returns 0 if company has no current employees in CoreSignal
- ❌ Misses people who worked there in the past

**Experience-Based Search** (nested `experience`):
- Finds anyone who has EVER worked at these companies
- Includes current AND past employees
- ✅ Much larger talent pool
- ✅ Finds people who gained Voice AI experience and moved on

---

## 📋 The Query

### Query for Your 6 Voice AI Companies

```json
{
  "query": {
    "nested": {
      "path": "experience",
      "query": {
        "bool": {
          "should": [
            {"term": {"experience.company_id": 95477034}},
            {"term": {"experience.company_id": 33312984}},
            {"term": {"experience.company_id": 21473726}},
            {"term": {"experience.company_id": 13006266}},
            {"term": {"experience.company_id": 11209012}},
            {"term": {"experience.company_id": 98601775}}
          ],
          "minimum_should_match": 1
        }
      }
    }
  }
}
```

**Translation:** "Find anyone who has one of these 6 companies in their experience history"

---

## 🔄 Integration Into Domain Search

### File: `backend/jd_analyzer/api/domain_search.py`

**Current Approach (Lines ~520-560):**
```python
# Current: Search by last_company_id (current employer only)
company_id_filters = []
for company in companies:
    if company.get('coresignal_company_id'):
        company_id_filters.append({
            "term": {"last_company_id": company['coresignal_company_id']}
        })
```

**New Approach (Experience-Based):**
```python
def build_experience_based_query(companies, role_keywords, location=None):
    """
    Build query that searches employee work history (experience field).

    This finds people who have EVER worked at these companies, not just
    current employees. Much better for small/new companies.
    """

    # Build company filters for experience history
    experience_company_filters = []

    for company in companies:
        company_id = company.get('coresignal_company_id')
        if company_id:
            experience_company_filters.append({
                "term": {"experience.company_id": company_id}
            })

    # Build the nested query
    must_clauses = []

    # Add company filter (nested in experience)
    if experience_company_filters:
        must_clauses.append({
            "nested": {
                "path": "experience",
                "query": {
                    "bool": {
                        "should": experience_company_filters,
                        "minimum_should_match": 1
                    }
                }
            }
        })

    # Add location filter (if provided, outside nested query)
    if location:
        must_clauses.append({
            "term": {"location_country": location}
        })

    # Build role filters (for active_experience_title OR experience titles)
    should_clauses = []
    for keyword in role_keywords:
        # Current role
        should_clauses.append({
            "wildcard": {"active_experience_title": f"*{keyword.lower()}*"}
        })

        # Past roles
        should_clauses.append({
            "nested": {
                "path": "experience",
                "query": {
                    "wildcard": {"experience.title": f"*{keyword.lower()}*"}
                }
            }
        })

    # Final query
    query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "minimum_should_match": 0  # Role keywords are optional boost
            }
        }
    }

    return query
```

---

## 📊 Expected Results

### With Current Approach (`last_company_id`)
```
Synthesia: 0 employees
VEED: 0 employees
Krisp: 0 employees
Otter.ai: 0 employees
Observe.AI: 0 employees
Synthflow: 0 employees
----
TOTAL: 0 employees
```

### With Experience-Based Approach (nested `experience`)
```
Synthesia: 5-15 people who worked there
VEED: 3-10 people
Krisp: 20-50 people (older company)
Otter.ai: 50-100 people (established)
Observe.AI: 30-80 people
Synthflow: 0-2 people (too new)
----
TOTAL: 100-250 employees with Voice AI experience
```

**Key Insight:** Even if people left these companies, they still have Voice AI experience!

---

## 🎯 Example Use Cases

### Example 1: Otter.ai Alumni
**Search:** People who worked at Otter.ai
**Results:**
- Jane Smith - **Was:** Senior ML Engineer at Otter.ai → **Now:** Staff Engineer at Google
- John Doe - **Was:** Product Manager at Otter.ai → **Now:** Director at Zoom
- Sarah Lee - **Was:** Engineering Lead at Otter.ai → **Now:** CTO at small startup

**Value:** These people have Voice AI experience even though they're no longer at Otter.ai!

### Example 2: Krisp Background
**Search:** People who worked at Krisp
**Results:**
- Engineers who worked on noise cancellation technology
- Now dispersed across other Voice AI companies, Big Tech, or startups
- Valuable talent pool with proven Voice AI skills

---

## 🔧 Implementation Steps

### Step 1: Add Experience-Based Query Function

**File:** `backend/jd_analyzer/api/domain_search.py` (around line 450)

```python
def build_query_with_experience_history(
    companies: List[Dict],
    role_keywords: List[str],
    location: Optional[str] = None,
    require_current_role: bool = False
) -> Dict:
    """
    Build query searching employee EXPERIENCE HISTORY (not just current employer).

    This finds anyone who has EVER worked at these companies, making it much
    more effective for small/new companies with limited current employee data.
    """
    # Implementation from code block above
    pass
```

### Step 2: Modify `stage2_preview_search` Function

**File:** `backend/jd_analyzer/api/domain_search.py` (around line 614)

```python
async def stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    session_logger: SessionLogger,
    create_session: bool = True,
    session_id: Optional[str] = None,
    batch_size: int = 5,
    use_experience_based_search: bool = True  # NEW PARAMETER
) -> Dict[str, Any]:
    """
    Stage 2: Preview search with option for experience-based queries.
    """

    # ... existing code ...

    # Build query
    if use_experience_based_search:
        query = build_query_with_experience_history(
            companies=batch_companies,
            role_keywords=role_keywords,
            location=location,
            require_current_role=False
        )
        print(f"📋 Using EXPERIENCE-BASED search (includes past employees)")
    else:
        query = build_query_for_employee_search(
            companies=batch_companies,
            role_keywords=role_keywords,
            location=location,
            endpoint=endpoint,
            require_current_role=False
        )
        print(f"📋 Using CURRENT EMPLOYER search (last_company_id)")

    # ... rest of function ...
```

### Step 3: Update API Endpoint

**File:** `backend/app.py` (domain search endpoint around line 2800)

```python
@app.route('/api/jd/domain-company-preview-search', methods=['POST'])
def domain_company_preview_search():
    """
    Preview search with experience-based option.
    """
    data = request.json

    use_experience_search = data.get('use_experience_search', True)  # Default to True

    # ... existing code ...

    result = asyncio.run(stage2_preview_search(
        companies=companies,
        jd_requirements=jd_requirements,
        endpoint='employee_clean',
        max_previews=20,
        session_logger=session_logger,
        use_experience_based_search=use_experience_search  # Pass parameter
    ))

    # ... rest of function ...
```

---

## 🧪 Testing

### Test Query (Curl)

```bash
curl -X POST https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "query": {
      "nested": {
        "path": "experience",
        "query": {
          "bool": {
            "should": [
              {"term": {"experience.company_id": 13006266}}
            ]
          }
        }
      }
    }
  }'
```

**Expected:** Find people who have worked at Otter.ai (past or present)

---

## 💡 Benefits

### 1. **Larger Talent Pool**
- Current employer search: 0-50 employees
- Experience-based search: 100-500+ employees

### 2. **Better for Small Companies**
- Even companies with 0 current employees in CoreSignal have alumni
- Finds people who gained experience and moved on

### 3. **Captures Talent Dispersion**
- Voice AI talent often moves between companies
- Experience-based search captures this mobility

### 4. **More Relevant Candidates**
- Past experience at target companies is valuable
- "Used to work at Otter.ai" = Voice AI experience

---

## 📊 Comparison Table

| Approach | Query Field | Finds | Small Companies | Talent Pool Size |
|----------|-------------|-------|-----------------|------------------|
| **Current Employer** | `last_company_id` | Current employees only | ❌ Often 0 results | Small (10-50) |
| **Experience-Based** | `experience.company_id` (nested) | Past + Current employees | ✅ Much better | Large (100-500+) |

---

## 🚀 Recommended Next Steps

### Option 1: Quick Test (5 min)
Test the experience-based query manually via curl or Postman to see if it returns results.

### Option 2: Implement in Code (30 min)
Add `build_query_with_experience_history()` function and integrate into domain search pipeline.

### Option 3: Make it Configurable (1 hour)
Add UI toggle: "Search current employees only" vs "Search anyone with experience at these companies"

---

## 📁 Code Files to Modify

1. **`backend/jd_analyzer/api/domain_search.py`**
   - Add `build_query_with_experience_history()` function (line ~450)
   - Modify `stage2_preview_search()` to use it (line ~614)

2. **`backend/app.py`**
   - Update `/api/jd/domain-company-preview-search` endpoint (line ~2800)
   - Pass `use_experience_based_search` parameter

3. **`frontend/src/App.js`** (Optional - UI Control)
   - Add checkbox: "Include past employees"
   - Pass parameter in API request

---

## ✅ Expected Outcome

**Before (Current Employer Search):**
- Query: `last_company_id: 98601775`
- Result: 0 employees

**After (Experience-Based Search):**
- Query: Nested `experience.company_id: 98601775`
- Result: 5-50 employees who have Voice AI experience from working at these companies

**Impact:** 10-50x increase in candidate pool! 🚀

---

## 🎓 Key Takeaway

**The problem wasn't just the location filter - it was searching for CURRENT employees when we should search for ANYONE WITH EXPERIENCE at these companies.**

Experience-based search solves this by:
1. Finding past + current employees
2. Capturing talent that has dispersed to other companies
3. Building a larger, more relevant candidate pool

**Next step:** Would you like me to implement this in your domain_search.py file?
