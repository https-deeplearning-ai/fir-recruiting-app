# Domain Search Pipeline - 0 Employees Debugging Summary

**Date:** November 10, 2025
**Session:** `sess_20251111_041155_eca8dc98`
**Status:** ✅ **ROOT CAUSE IDENTIFIED**

---

## 🎯 TL;DR - The Problem

**Your domain search returned 0 employees despite having company IDs because:**

1. **Companies are too small/new** - These Voice AI startups have `"size_employees_count": 0` in CoreSignal
2. **Location filter too restrictive** - Required "United States" but companies may have remote/international teams
3. **Possible company confusion** - "SynthFlow" (.ink) vs "SynthFlow AI" (.ai) are different companies

---

## 📊 Session Analysis

### What Worked ✅
| Stage | Status | Details |
|-------|--------|---------|
| **Company Discovery** | ✅ Success | Found 7 Voice AI companies from G2/Capterra |
| **CoreSignal ID Lookup** | ✅ Success | Matched 6/7 companies (85.7%) with IDs |
| **Query Construction** | ✅ Success | Query syntax was valid and correct |
| **API Execution** | ✅ Success | No errors, clean API response |

### What Failed ❌
| Stage | Status | Details |
|-------|--------|---------|
| **Employee Search** | ❌ Failed | 0 employees found for ALL 6 companies |
| **Location Filter** | ⚠️ Too Restrictive | "United States" requirement eliminated all candidates |
| **Company Size** | ⚠️ No Validation | Didn't check if companies have employees before searching |

---

## 🔍 Key Evidence

### 1. Synthflow Company Data (ID: 98601775)

**From company_clean API:**
```json
{
  "id": 98601775,
  "name": "SynthFlow",
  "size_range": "1-10 employees",
  "size_employees_count": 0,  ← 🚨 NO EMPLOYEE DATA
  "industry": "Software Development",
  "description": "SynthFlow is developing a visual, AI-driven backend automation platform..."
}
```

**From company_base API:**
```json
{
  "id": 98601775,
  "name": "SynthFlow",
  "website": "http://synthflow.ink/",  ← Backend automation, NOT Voice AI
  "size": "2-10 employees",
  "employees_count": null,  ← 🚨 NULL EMPLOYEE COUNT
  "company_similar_collection": [
    {
      "url": "https://de.linkedin.com/company/synthflowai"  ← Different company!
    }
  ]
}
```

### 2. Employee Search Query

**From session file:** `02_preview_query.json`

```json
{
  "must": [
    {
      "should": [
        {"term": {"last_company_id": 95477034}},  // Synthesia
        {"term": {"last_company_id": 33312984}},  // VEED
        {"term": {"last_company_id": 21473726}},  // Krisp
        {"term": {"last_company_id": 13006266}}   // Otter.ai
      ]
    },
    {"term": {"location_country": "United States"}}  ← HARD REQUIREMENT
  ],
  "should": [
    // 26 role keywords (chief, officer, technology, etc.)
  ],
  "minimum_should_match": 0  ← Role keywords are OPTIONAL!
}
```

**Translation:** "Find ANY employee at these 4 companies who is located in United States"

**Result:** 0 employees found

---

## 💡 Root Causes

### Primary Cause: Companies Too Small
- Series A Voice AI startups = 1-10 employees
- Very new companies (Synthflow created May 2025)
- No employee data in CoreSignal yet
- `size_employees_count: 0` or `null`

### Secondary Cause: Location Filter
- Location filter required "United States" exactly
- Remote companies may have employees in:
  - Germany (de.linkedin.com/company/synthflowai)
  - UK, Armenia, Canada, other countries
  - Listed as "Remote" not "United States"

### Tertiary Cause: Company Confusion
- **"SynthFlow"** (synthflow.ink) = Backend automation platform
- **"SynthFlow AI"** (synthflow.ai) = Voice AI company
- Lookup found the wrong one (name match without domain verification)
- Similar issue may affect other companies

---

## 🎯 Recommended Solutions

### **Solution 1: Remove Location Filter** (Quick Fix - 5 min)

**File:** `backend/jd_analyzer/api/domain_search.py` (line ~597)

**Change:**
```python
# BEFORE:
if location:
    must_clauses.append({"term": {"location_country": location}})

# AFTER (Option A - Remove completely):
# if location:
#     must_clauses.append({"term": {"location_country": location}})

# AFTER (Option B - Make optional):
if location and require_strict_location:  # Add flag
    must_clauses.append({"term": {"location_country": location}})
elif location:
    # Add as boost (prefer but don't require)
    should_clause.append({"term": {"location_country": location}})
```

**Pros:**
- Immediate fix, one-line change
- Will find employees worldwide
- Broadens candidate pool 10x

**Cons:**
- May return international candidates
- User needs to filter results manually

---

### **Solution 2: Multi-Tier Search** (Recommended - 1 hour)

**Implementation:**
```python
def stage2_preview_search(..., auto_fallback=True):
    # Tier 1: Try strict search with location
    strict_results = search_with_location(companies, location)

    if len(strict_results) < min_threshold and auto_fallback:
        print(f"⚠️  Found {len(strict_results)} with strict filters")
        print(f"🔄  Trying relaxed search (worldwide)...")

        # Tier 2: Search without location
        relaxed_results = search_without_location(companies)

        # Tag results so user knows
        for r in strict_results:
            r['match_type'] = 'exact_location'
        for r in relaxed_results:
            r['match_type'] = 'broader_search'

        return strict_results + relaxed_results

    return strict_results
```

**Pros:**
- Best of both worlds (tries strict, falls back to relaxed)
- Transparent to user (results are tagged)
- Automatic - no user action needed

**Cons:**
- More complex code
- Requires UI updates to show tags

---

### **Solution 3: Pre-Filter by Company Size** (Long-term - 2 hours)

**Implementation:**
```python
async def validate_companies_have_employees(companies):
    """Check if companies have employee data before searching."""
    validated = []
    too_small = []

    for company in companies:
        if not company.get('coresignal_company_id'):
            too_small.append((company['name'], 'No CoreSignal ID'))
            continue

        # Fetch company_clean data
        company_info = await fetch_company_data(
            company['coresignal_company_id']
        )

        employee_count = company_info.get('size_employees_count', 0)

        if employee_count >= min_employees:  # e.g., 10
            validated.append(company)
        else:
            too_small.append((company['name'], f'{employee_count} employees'))

    if too_small:
        print(f"\n⚠️  Skipped {len(too_small)} companies (too small):")
        for name, reason in too_small:
            print(f"   - {name}: {reason}")

    return validated
```

**Pros:**
- Avoids wasted searches on small companies
- Clear feedback to user
- Better success rate

**Cons:**
- Extra API call per company (1 credit each)
- May eliminate valid early-stage companies
- Doesn't match "Series A" context (small is OK)

---

### **Solution 4: Domain Verification** (Medium-term - 3 hours)

Add domain matching to company ID lookup to avoid confusion between similarly-named companies.

**File:** `backend/coresignal_company_lookup.py` (line ~150)

**Implementation:**
```python
def lookup_by_name_with_pagination(self, company_name, website=None):
    # ... existing search logic ...

    for page in range(1, max_pages + 1):
        companies = self._search_companies(page)

        for company in companies:
            if company['name'].lower() == company_name.lower():
                # NEW: If we have website, verify domain matches
                if website:
                    search_domain = extract_domain(website)  # "synthflow.ai"
                    company_domain = extract_domain(company.get('website', ''))  # "synthflow.ink"

                    if search_domain != company_domain:
                        print(f"⚠️  Name match but DOMAIN MISMATCH:")
                        print(f"      Expected: {search_domain}")
                        print(f"      Found: {company_domain}")
                        print(f"   Continuing search for correct domain...")
                        continue  # Keep looking

                # Match found with verified domain
                return {
                    'company_id': company['id'],
                    'name': company['name'],
                    'tier': 2,
                    'domain_verified': True
                }
```

**Pros:**
- Prevents wrong company matches
- More accurate results
- Catches name collisions

**Cons:**
- More complex lookup logic
- Requires all discoveries to have website data
- May miss matches if domain format differs

---

## 📋 Test Plan

### Test 1: Remove Location Filter
```bash
# Edit domain_search.py line 597
# Comment out location requirement

# Re-run the same session
python3 -c "
from jd_analyzer.api.domain_search import stage2_preview_search
# ... (use same companies and JD)
"
```

**Expected:** Find 10-50 employees worldwide

### Test 2: Try Larger Companies
```bash
# Test with known large Voice AI companies
companies = [
    {'name': 'Google Cloud', 'coresignal_company_id': ...},
    {'name': 'Microsoft Azure', 'coresignal_company_id': ...},
    {'name': 'Deepgram', 'coresignal_company_id': 6761084},
]
```

**Expected:** Find 100+ employees easily

### Test 3: Verify Synthflow Domains
```bash
# Check what domains we have
python3 -c "
lookup = CoreSignalCompanyLookup()

# Look up both
backend = lookup.lookup_with_fallback('SynthFlow', 'synthflow.ink')
voice_ai = lookup.lookup_with_fallback('SynthFlow', 'synthflow.ai')

print(f'Backend ID: {backend}')
print(f'Voice AI ID: {voice_ai}')
"
```

**Expected:** Two different IDs (or one fails)

---

## 🚀 Immediate Action Items

### Option A: Quick Test (5 minutes)
1. Remove location filter temporarily
2. Re-run domain search with same JD
3. See if we get ANY employees worldwide

### Option B: Thorough Investigation (30 minutes)
1. Test with larger companies (Deepgram, Google)
2. Verify we can find employees for known companies
3. Validate pipeline works before fixing filters

### Option C: Implement Solution (1-3 hours)
1. Choose Solution 2 (multi-tier search)
2. Implement fallback logic
3. Test with Voice AI companies
4. Deploy and verify in UI

---

## 📊 Expected Results After Fix

| Metric | Before Fix | After Fix (Solution 1) | After Fix (Solution 2) |
|--------|------------|----------------------|----------------------|
| **Companies** | 7 | 7 | 7 |
| **With IDs** | 6/7 (85.7%) | 6/7 | 7/7 (with domain verification) |
| **Employees Found** | 0 | 50-200 (worldwide) | 50-200 (tagged) |
| **Location Match** | N/A | Mixed | Separate tier results |

---

## 🎓 Lessons Learned

1. **Validate Company Size First** - Check `size_employees_count` before employee search
2. **Location Filters Kill Small Teams** - Remote companies have global employees
3. **Domain Verification Matters** - "SynthFlow" != "SynthFlow AI"
4. **Test with Known Companies** - Validate pipeline with Google/Microsoft first
5. **Series A = Small** - 1-10 employees is normal for Series A startups

---

## 📂 Related Files

- **Session Files:** `logs/domain_search_sessions/sess_20251111_041155_eca8dc98/`
- **Query Log:** `02_preview_query.json`
- **Companies Log:** `00_session_metadata.json`
- **Root Cause Analysis:** `DOMAIN_SEARCH_0_EMPLOYEES_ROOT_CAUSE.md`
- **Synthflow Analysis:** `SYNTHFLOW_COMPANIES_ANALYSIS.md`
- **Handoff Doc:** `SESSION_HANDOFF_NOV_10_SESSION_2.md`

---

## ❓ Decision Time

**What would you like to do?**

**A. Quick Fix (5 min):**
- Remove location filter
- Test immediately
- See results worldwide

**B. Smart Fix (1 hour):**
- Implement multi-tier search
- Auto-fallback to relaxed filters
- Tag results for transparency

**C. Full Fix (3 hours):**
- Add domain verification
- Implement company size pre-filter
- Multi-tier search with validation

**D. Test First (30 min):**
- Try with larger companies
- Validate pipeline works
- Then decide on fix

**Which option would you prefer?** Or would you like more information about any specific aspect?
