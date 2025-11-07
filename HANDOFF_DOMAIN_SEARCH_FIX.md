# Handoff: Domain Search (Employee/Candidate Search) Fix

**Date:** November 7, 2025
**Session Context:** Fixing company research streaming and enabling employee search at discovered companies
**Next Task:** Enable "Search for People" feature for discovered companies using CoreSignal

---

## 🎯 Correct Understanding of "Domain Search"

### What "Domain Search" Actually Does:

**Domain Search = Find EMPLOYEES/CANDIDATES at discovered companies who match the JD requirements**

This is a **recruiting workflow** feature:

1. ✅ **Company Research** → Find ~100 relevant companies (already working)
2. ✅ **Company Selection** → User picks companies via checkboxes
3. ❌ **Employee Search** → Query CoreSignal for employees at those companies (BROKEN - button not showing)
4. ❌ **Candidate Evaluation** → AI evaluates candidates against JD (exists but not accessible)

**NOT:** Domain search is NOT about searching for more companies. We already have company discovery working.

**IS:** Domain search IS about finding PEOPLE (employees/candidates) at the discovered companies using CoreSignal's employee database.

---

## 🔍 Technical Architecture

### CoreSignal Employee Search Pipeline

**Backend File:** `backend/jd_analyzer/api/domain_search.py`

**4-Stage Pipeline:**

#### **Stage 1: Company Discovery (Lines 170-358)**
- Input: Seed companies from JD (e.g., "Stripe, Plaid, Brex")
- Uses `CompanyDiscoveryAgent` to find 30-100 similar companies
- Validates with Claude Haiku 4.5
- *pending* To have claude code sdk find domains of evaluated companies and store the domain so that Coresignal can enrich them

#### **Stage 1.5: Figure out CoreSIgnal Id's of that company(Do a web research on how to solve it )**

- Looks up CoreSignal company IDs so that employee es_dsl knows which companies ID its supposed to look ULTRATHINK here

#### **Stage 2: Employee Preview Search (Lines 537-784)**
- Builds Elasticsearch DSL query with:
  - Company filters (company_id or company_name)
  - Role filters (title wildcards: "*engineer*", "*senior*")
  - Location filters (optional boost)
- Calls CoreSignal API: `/v2/employee_clean/search/es_dsl/preview`
- Returns 20 employee IDs (preview mode)

**Key Function:** `build_domain_company_query()` (Lines 365-534)

```python
# Two-tier company matching:
# 1. ID-based (FAST): last_company_id in [123, 456, 789]
# 2. Name-based (FALLBACK): experience.company_name match ["Stripe", "Plaid"]

# Role filtering:
# - active_experience_title wildcard "*senior engineer*"
# - experience.title wildcard (nested) for past roles
```

#### **Stage 3: Full Profile Collection (Lines 787-1065)**
- For each employee_id from Stage 2
- Fetches full profile: `/v2/employee_base/collect/{employee_id}`
- Enriches with company data (2020+ jobs only)
- Uses Supabase cache to avoid duplicate API calls

#### **Stage 4: AI Evaluation (Lines 1068-1300)**
- Claude Sonnet 4.5 evaluates each candidate or Gemini 2.5 Pro (as fallback)
- Scores against JD requirements
- Returns ranked candidate list

---

## 🚨 Current Broken State

### Why Button Not Showing

**The "Start Domain Search" button should appear after company research completes, but it doesn't.**

**Button Location:** `frontend/src/App.js:4135-4180`

**Current Condition (WRONG):**
```javascript
{!domainSearchSessionId && (
  <div className="domain-search-section">
    <button onClick={() => handleStartDomainSearch(selected)}>
      🚀 Start Domain Search
    </button>
  </div>
)}
```

**Problems:**

1. **Missing `discoveredCompanies` check:**
   - Button shows even when no companies discovered
   - Should check: `discoveredCompanies.length > 0`

2. **Wrong data source:**
   - Uses `companyResearchResults.companies_by_category` (evaluation categories)
   - Should use `discoveredCompanies` (all discovered companies)

3. **Button location:**
   - Inside `{companyResearchResults && (` block (line 3998)
   - Only shows AFTER evaluation completes
   - Should show AFTER discovery completes (with or without evaluation)

---

## 📊 Data Flow Analysis

### What Backend Returns

**Endpoint:** `/research-companies/{jd_id}/results`

**After Discovery Completes (status=completed, phase=discovery):**
```json
{
  "success": true,
  "results": {
    "discovered_companies": [          // ← THIS is what we need!
      {
        "name": "Stripe",
        "company_id": 123456,           // CoreSignal ID
        "discovered_via": "mentioned",
        "source": "Job description",
        "rank": 1
      },
      {
        "name": "Plaid",
        "company_id": 789012,
        "discovered_via": "seed_expansion",
        "source": "Tavily search",
        "rank": 2
      }
      // ... up to 100 companies
    ],
    "screened_companies": [],           // Empty until screening
    "companies_by_category": {},        // Empty until evaluation
    "evaluated_companies": []           // Empty until evaluation
  }
}
```

**Frontend State:**
```javascript
const [discoveredCompanies, setDiscoveredCompanies] = useState([]);  // Line 96

// Set at line 3676 (after streaming completes):
if (results.discovered_companies && results.discovered_companies.length > 0) {
  setDiscoveredCompanies(results.discovered_companies);  // Should have ~100 companies
}
```

---

## 🛠️ Required Fixes

### Fix 1: Move Button Outside Results Block

**Current Structure:**
```javascript
{discoveredCompanies && discoveredCompanies.length > 0 && (
  <div className="discovered-companies-section">
    {/* Checkbox list - line 3828 */}
  </div>
)}

{companyResearchResults && (           // ← Button is INSIDE here (line 3998)
  <div>
    {/* Evaluation results */}
    {!domainSearchSessionId && (      // ← Button (line 4136)
      <button>Start Domain Search</button>
    )}
  </div>
)}
```

**Fixed Structure:**
```javascript
{discoveredCompanies && discoveredCompanies.length > 0 && (
  <div className="discovered-companies-section">
    {/* Checkbox list */}

    {/* Move button HERE - inside discovered companies section */}
    {!domainSearchSessionId && selectedCompanies.length > 0 && (
      <div className="domain-search-action">
        <button onClick={() => handleStartDomainSearch(selectedCompanies)}>
          🔍 Search for People ({selectedCompanies.length} companies)
        </button>
      </div>
    )}
  </div>
)}
```

### Fix 2: Update Button to Use Checkbox Selection

**Current (WRONG):**
```javascript
onClick={() => {
  // Uses category-based selection (WRONG!)
  const selected = [];
  Object.entries(companyResearchResults.companies_by_category).forEach(([cat, companies]) => {
    if (selectedCategories[cat]) {
      selected.push(...companies.map(c => c.company_name || c.name));
    }
  });
  handleStartDomainSearch(selected);
}}
```

**Fixed:**
```javascript
onClick={() => {
  // Uses checkbox selection (CORRECT!)
  handleStartDomainSearch(selectedCompanies);
}}
```

### Fix 3: Update handleStartDomainSearch Function

**Current (Line ~2060):**
```javascript
const handleStartDomainSearch = async (companyNames) => {
  // Should accept array of company name strings
  // e.g., ["Stripe", "Plaid", "Brex"]
}
```

**Verify it works with checkbox-selected company names** - should already work!

---

## 📋 Step-by-Step Implementation

### Step 1: Verify Data Flow (5 min)

**Add debug logging to check if data is flowing:**

```javascript
// After line 3676 in App.js
console.log('[DEBUG] After setting discoveredCompanies:', {
  length: discoveredCompanies?.length,
  first_company: discoveredCompanies?.[0],
  has_company_id: discoveredCompanies?.[0]?.company_id
});

// After line 96 (state definition)
useEffect(() => {
  console.log('[DEBUG] discoveredCompanies state updated:', {
    length: discoveredCompanies.length,
    companies: discoveredCompanies.slice(0, 3)
  });
}, [discoveredCompanies]);
```

**Test:**
1. Complete company research
2. Check browser console for `[DEBUG]` logs
3. Verify `discoveredCompanies` has items

### Step 2: Find Button Current Location (5 min)

**Search in App.js:**
```bash
grep -n "Start Domain Search\|domain-search-section" frontend/src/App.js
```

Expected: Line ~4136-4180

### Step 3: Cut Button from Current Location (10 min)

**Find this block (around line 4135):**
```javascript
{!domainSearchSessionId && (
  <div className="domain-search-section" style={{...}}>
    <h3>Stage 3: Domain Search</h3>
    <button onClick={() => {
      // Category-based selection logic
    }}>
      🚀 Start Domain Search
    </button>
  </div>
)}
```

**Cut entire block** (save to clipboard)

### Step 4: Paste Button in Discovered Companies Section (15 min)

**Find discovered companies section (around line 3828):**
```javascript
{discoveredCompanies && discoveredCompanies.length > 0 && (
  <div className="discovered-companies-section">
    <h4>Discovered Companies ({discoveredCompanies.length})</h4>

    {/* Search/filter input */}
    {/* Select All / Clear buttons */}
    {/* Checkbox list */}

    {/* ADD BUTTON HERE - at the end, before closing </div> */}
  </div>
)}
```

**Insert new button:**
```javascript
{/* Domain Search Action */}
{!domainSearchSessionId && selectedCompanies.length > 0 && (
  <div style={{
    marginTop: '20px',
    paddingTop: '20px',
    borderTop: '1px solid #ddd'
  }}>
    <button
      onClick={() => {
        console.log('[DOMAIN SEARCH] Starting with companies:', selectedCompanies);
        handleStartDomainSearch(selectedCompanies);
      }}
      style={{
        padding: '12px 24px',
        fontSize: '15px',
        background: '#6366f1',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        fontWeight: '600'
      }}
    >
      🔍 Search for People at {selectedCompanies.length} {selectedCompanies.length === 1 ? 'Company' : 'Companies'}
    </button>
    <p style={{ marginTop: '8px', fontSize: '13px', color: '#6b7280' }}>
      Find employees at selected companies who match this job description
    </p>
  </div>
)}
```

### Step 5: Verify handleStartDomainSearch Works (5 min)

**Find function (around line 2060):**
```javascript
const handleStartDomainSearch = async (companyNames) => {
```

**Check parameters:**
- Should accept: `string[]` (array of company names)
- Should call: `/api/jd/domain-company-preview-search`

**Should already work!** Just verify the endpoint call is correct.

### Step 6: Test End-to-End (10 min)

1. **Start company research** with specific JD:
   ```
   Senior Software Engineer
   Location: San Francisco, United States
   Companies: Stripe, Plaid, Brex, Ramp, Mercury
   Skills: React, Python, AWS
   ```

2. **Wait for discovery** to complete (status=completed, phase=discovery)

3. **Verify UI shows:**
   - ✅ Discovered Companies section appears
   - ✅ List of companies with checkboxes
   - ✅ Can select/deselect companies
   - ✅ "Search for People" button appears below checkboxes
   - ✅ Button shows count: "Search for People at 3 Companies"

4. **Click "Search for People" button**

5. **Verify backend call:**
   - Check Network tab for POST `/api/jd/domain-company-preview-search`
   - Request body should have `mentioned_companies: ["Stripe", "Plaid", "Brex"]`

6. **Verify results:**
   - Candidates section appears
   - Shows employee profiles from selected companies
   - Each profile has: name, headline, current company, LinkedIn URL

---

## 🐛 Troubleshooting Guide

### Issue 1: discoveredCompanies is Empty

**Symptom:** Checkbox list doesn't appear after discovery completes

**Debug:**
```javascript
// Check these console logs:
console.log('[RESULTS] Fetched results:', resultsData);
console.log('[DISCOVERED] discovered_companies:', resultsData.results?.discovered_companies);
```

**Possible Causes:**
1. Backend not returning `discovered_companies` array
2. Company research found 0 companies (check backend logs for "Discovery complete: 0 companies")
3. JD too generic (use specific company names)

**Fix:**
- Use specific JD with company names (Stripe, Plaid, etc.)
- Check backend logs for discovery success
- Verify `/research-companies/{id}/results` endpoint response

### Issue 2: Button Shows But No Companies Selected

**Symptom:** Button appears but clicking shows "No companies selected"

**Debug:**
```javascript
console.log('[CHECKBOX] selectedCompanies:', selectedCompanies);
```

**Cause:** `selectedCompanies` state not being updated when checkboxes clicked

**Fix:** Verify checkbox onChange handler updates `selectedCompanies` state

### Issue 3: Domain Search Returns 405 Error

**Symptom:** Button click fails with "Method Not Allowed"

**Debug:**
```bash
curl -X POST http://localhost:5001/api/jd/domain-company-preview-search \
  -H "Content-Type: application/json" \
  -d '{"jd_requirements": {}, "endpoint": "employee_clean"}'
```

**Expected:** 400 (bad request) NOT 405 (method not allowed)

**Cause:** Blueprint not registered (lazy loading issue)

**Fix:** Already fixed in previous session - verify backend logs show:
```
✓ Domain Search routes registered successfully
```

### Issue 4: CoreSignal Returns 422 Error

**Symptom:** Backend logs show "CoreSignal API 422 error"

**Cause:** Invalid Elasticsearch query or API rate limit

**Fix:**
1. Check CoreSignal API key is valid
2. Verify query structure in `build_domain_company_query()`
3. Check API credits remaining

### Issue 5: No Candidates Found

**Symptom:** Search completes but shows 0 candidates

**Possible Causes:**
1. Company names don't match CoreSignal records
2. Role filters too restrictive
3. No employees at selected companies

**Debug:**
```python
# Check backend logs for:
print(f"[SEARCH] Built query for companies: {company_names}")
print(f"[SEARCH] CoreSignal returned {len(results)} employee IDs")
```

**Fix:**
- Verify company names are correct (not misspelled)
- Broaden role filters (remove very specific keywords)
- Try larger/well-known companies (Stripe, Google, etc.)

---

## 📁 Key Files Reference

### Frontend Files
- `frontend/src/App.js:96` - State variable: `discoveredCompanies`
- `frontend/src/App.js:3828-3994` - Discovered companies checkbox list
- `frontend/src/App.js:4135-4180` - Current button location (MOVE FROM HERE)
- `frontend/src/App.js:~2060` - `handleStartDomainSearch` function

### Backend Files
- `backend/jd_analyzer/api/domain_search.py:1306` - Domain search endpoint
- `backend/jd_analyzer/api/domain_search.py:365-534` - `build_domain_company_query()`
- `backend/jd_analyzer/api/domain_search.py:59-73` - Lazy-loaded Anthropic client
- `backend/app.py:3324` - Results endpoint (discovery complete response)
- `backend/coresignal_service.py` - CoreSignal API integration

### Documentation
- `backend/jd_analyzer/CORESIGNAL_FIELD_REFERENCE.md` - CoreSignal field mappings
- `docs/COMPANY_INTELLIGENCE_CACHE_SCHEMA.sql` - Database schema

---

## 🧪 Testing Checklist

**After implementing the fix:**

- [ ] Backend starts without errors (`✓ Domain Search routes registered successfully`)
- [ ] Frontend compiles without errors
- [ ] Start company research with specific JD (include company names)
- [ ] Discovery completes (check logs: "Discovery complete: X companies")
- [ ] Discovered companies checkbox list appears
- [ ] Can select/deselect companies
- [ ] "Search for People" button appears below checkboxes
- [ ] Button shows count (e.g., "Search for People at 3 Companies")
- [ ] Button disabled/hidden when no companies selected
- [ ] Clicking button shows loading state
- [ ] POST request to `/api/jd/domain-company-preview-search` succeeds
- [ ] Request body includes `mentioned_companies: [...]`
- [ ] Response includes `stage2_previews: [...]` (employee IDs)
- [ ] Candidates section appears with employee profiles
- [ ] Each profile shows: name, headline, company, LinkedIn URL
- [ ] Can click profile to view full details
- [ ] "Load More" button works if more candidates available

---

## 🚀 Quick Start Commands

```bash
# Terminal 1: Backend
cd backend
python3 app.py

# Should see:
# ✓ Domain Search routes registered successfully
# Running on http://127.0.0.1:5001

# Terminal 2: Frontend
cd frontend
npm start

# Should compile and open http://localhost:3000
```

**Test JD:**
```
Senior Software Engineer

Location: San Francisco, United States

Industry: Financial Technology (fintech)

Companies: Stripe, Plaid, Brex, Ramp, Mercury, Chime

Requirements:
- 5+ years software engineering experience
- Strong background in backend systems (Python, Go, or Java)
- Experience at B2B SaaS companies
- AWS or GCP cloud infrastructure experience

Nice to have:
- Fintech domain experience
- Payment systems knowledge
- High-scale distributed systems experience
```

---

## 💡 Expected User Experience

### Complete Workflow:

1. **User enters JD** with company names (Stripe, Plaid, Brex)
2. **Clicks "Start Research"**
3. **Company Discovery runs** (~30 seconds)
   - Finds 100 companies via seed expansion + web search
   - Enriches with CoreSignal company IDs
4. **UI shows:** "Discovery complete: 100 companies ready"
5. **Discovered Companies section appears:**
   - Checkbox list of all 100 companies
   - Search/filter input
   - Select All / Clear buttons
6. **User selects companies:** Checks Stripe, Plaid, Brex (3 selected)
7. **"Search for People" button appears:** "Search for People at 3 Companies"
8. **User clicks button**
9. **Domain Search runs** (~10-30 seconds depending on number of companies)
   - Queries CoreSignal for employees at 3 companies
   - Filters by JD requirements (senior engineer, backend, etc.)
   - Fetches full profiles
   - Evaluates with Claude Sonnet 4.5
10. **Candidates section appears:**
    - Shows 20-60 candidates (20 per company batch)
    - Each candidate: name, headline, company, skills, LinkedIn URL
    - Sorted by relevance score
11. **User can:** Click candidate to assess profile, load more candidates

---

## 📞 Implementation Summary

**Goal:** Enable "Search for People" button after company discovery completes

**Changes Required:**
1. **Move button** from line 4136 → inside discovered companies section (line 3990)
2. **Update condition** from `!domainSearchSessionId` → `!domainSearchSessionId && selectedCompanies.length > 0`
3. **Update onClick** from category-based → checkbox-based: `handleStartDomainSearch(selectedCompanies)`

**Estimated Time:** 30-45 minutes (including testing)

**Risk Level:** LOW (moving existing, working code to new location)

---

## 🎬 Next Steps

1. ✅ Verify `discoveredCompanies` is populated (check console logs)
2. ✅ Move button to discovered companies section
3. ✅ Update button onClick to use `selectedCompanies`
4. ✅ Test with specific company names in JD
5. ✅ Verify CoreSignal employee search works
6. ✅ Polish button UI and loading states

**Good luck! 🚀**

If you encounter issues:
1. Check browser console for `[DEBUG]`, `[DISCOVERED]`, `[DOMAIN SEARCH]` logs
2. Check backend logs for CoreSignal API calls and errors
3. Verify `/api/jd/domain-company-preview-search` endpoint is registered
4. Test with well-known companies (Stripe, Google, etc.) that definitely have employees in CoreSignal
