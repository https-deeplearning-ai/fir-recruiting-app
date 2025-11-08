# Handoff: Website-Based Company ID Lookup

## Current State (Nov 7, 2025 - 3:30 PM)

### ✅ Completed Today
1. **Skip Stage 1 for pre-selected companies** - Working!
   - Detects companies with `coresignal_company_id`
   - Passes directly to Stage 2 with IDs intact

2. **Anthropic debug logging** - Working!
   - Shows what's being validated
   - Shows responses and results
   - **Key Discovery:** Validation returns `website` field!

3. **Company structure preservation** - Working!
   - Company objects maintain IDs through batching
   - Session mapping preserves full company data

4. **Improved company lookup** - Partially working
   - Uses wildcard + exact + fuzzy matching
   - Filters to US companies
   - **Problem:** Still 0% success rate on name-based lookup

---

## 🎯 Next Steps: Website-Based Lookup

### Problem
Current approach uses fuzzy name matching → 0% success rate
- "Vena" → No CoreSignal ID found
- "FloQast" → No CoreSignal ID found
- "BlackLine" → No CoreSignal ID found

### Solution
**Use the website domain from Anthropic validation!**

Validation already returns:
```json
{
  "company_name": "Vena",
  "website": "vena.io",  // ← USE THIS!
  "is_valid": true,
  "relevance_to_domain": "high"
}
```

---

## Implementation Plan

### 1. Update Company ID Lookup Logic

**File:** `backend/jd_analyzer/api/domain_search.py` (lines 310-367)

**Current (broken):**
```python
# Look up company ID with confidence threshold of 0.75
match = company_lookup.get_best_match(company_name, confidence_threshold=0.75)
```

**New (reliable):**
```python
# If validation provided a website, use that for lookup (MUCH more reliable)
website = company.get('website')
if website:
    # Use website.exact field in CoreSignal ES DSL
    match = company_lookup.get_by_website(website)
else:
    # Fall back to name-based search
    match = company_lookup.get_best_match(company_name, confidence_threshold=0.75)
```

---

### 2. Add Website Lookup Method

**File:** `backend/coresignal_company_lookup.py`

**Add new method:**
```python
def get_by_website(self, website: str) -> Optional[Dict[str, Any]]:
    """
    Look up company by exact website domain (most reliable method).

    Uses CoreSignal's website.exact field for precise matching.

    Args:
        website: Company website domain (e.g., "vena.io")

    Returns:
        Company data with ID, or None if not found
    """
    # Clean website (remove http://, https://, www.)
    cleaned_website = website.lower().strip()
    cleaned_website = cleaned_website.replace('https://', '').replace('http://', '')
    cleaned_website = cleaned_website.replace('www.', '').rstrip('/')

    # Build ES DSL query
    search_url = f"{self.base_url}/cdapi/v2/company_base/search/es_dsl"

    payload = {
        "query": {
            "term": {
                "website.exact": cleaned_website
            }
        }
    }

    try:
        print(f"[COMPANY LOOKUP] Searching by website: {cleaned_website}")

        response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)

        if response.status_code != 200:
            print(f"[COMPANY LOOKUP] Website search failed: {response.status_code}")
            return None

        company_ids = response.json()  # List of IDs

        if not company_ids:
            print(f"[COMPANY LOOKUP] No companies found for website: {cleaned_website}")
            return None

        # Get first result (should be exact match)
        company_id = company_ids[0]

        # Fetch full company data
        company_data = self._fetch_company_by_id(company_id)

        if company_data:
            print(f"[COMPANY LOOKUP] ✅ Found via website: ID={company_id}, Name={company_data.get('name')}")
            return {
                "company_id": company_data["company_id"],
                "name": company_data["name"],
                "website": cleaned_website,
                "confidence": 1.0,  # Exact match via website
                "employee_count": company_data.get("employee_count")
            }

        return None

    except Exception as e:
        print(f"[COMPANY LOOKUP] Error in website lookup: {e}")
        return None
```

---

### 3. Show Website in Frontend UI

**File:** `frontend/src/App.js` (company research results display)

**Add website display next to company name:**
```jsx
<span className="discovered-name">{companyName || 'Unknown'}</span>
{company.website && (
  <a
    href={`https://${company.website}`}
    target="_blank"
    rel="noopener noreferrer"
    className="company-website-link"
    style={{
      fontSize: '11px',
      color: '#6366f1',
      marginLeft: '8px',
      textDecoration: 'none'
    }}
  >
    🌐 {company.website}
  </a>
)}
```

---

## ES DSL Reference (CoreSignal company_base)

### Available Fields for Search

**High-Confidence Fields:**
- `website.exact` - Exact domain match (BEST for lookup)
- `name.exact` - Exact name match
- `company_shorthand_name` - URL slug (e.g., "vena-solutions")

**Fuzzy Match Fields:**
- `name` - Text search on name
- `website.filter` - Text search on website
- `description` - Full-text description

**Metadata Fields:**
- `id` - CoreSignal company ID (what we need!)
- `employees_count` - Employee count
- `industry.exact` - Industry classification
- `headquarters_country_parsed` - Country filter
- `founded` - Founding year

---

## Testing Checklist

### Test 1: Website-Based Lookup
1. Run company research
2. Check backend logs for validation results with websites
3. Verify CoreSignal lookup uses website field
4. Expected: **Much higher success rate** (50%+ vs 0%)

### Test 2: Fallback to Name
1. Test with company that validation doesn't find website for
2. Verify it falls back to name-based search
3. Should still work (but lower confidence)

### Test 3: Frontend Website Display
1. After company research completes
2. Check if websites are shown next to company names
3. Click website links to verify they're correct

---

## Expected Impact

**Before:**
```
❌ Vena: No CoreSignal ID found
❌ FloQast: No CoreSignal ID found
❌ BlackLine: No CoreSignal ID found
Coverage: 0.0%
```

**After (using website):**
```
✅ Vena: ID=123456 (via website: vena.io, confidence: 1.00)
✅ FloQast: ID=789012 (via website: floqast.com, confidence: 1.00)
✅ BlackLine: ID=345678 (via website: blackline.com, confidence: 1.00)
Coverage: 70-90%
```

---

## Files to Modify

1. **`backend/coresignal_company_lookup.py`**
   - Add `get_by_website()` method
   - ~40 lines of code

2. **`backend/jd_analyzer/api/domain_search.py`** (lines 310-367)
   - Update ID lookup to try website first
   - ~10 lines of code change

3. **`frontend/src/App.js`** (company display section)
   - Add website link display
   - ~15 lines JSX

**Estimated Time:** 45 minutes

---

## Why This Works Better

**Name-Based Search Problems:**
- "Vena" could be "Vena Solutions", "Vena Inc.", "Vena Software"
- Variations, typos, legal suffixes cause mismatches
- Wildcard too broad, exact too narrow

**Website-Based Search Benefits:**
- Domains are unique: "vena.io" only matches one company
- No ambiguity with legal suffixes or variations
- CoreSignal already has website data indexed
- Anthropic validation already extracts it

**Success Rate Comparison:**
- Name-based: ~0-30% success (current)
- Website-based: ~70-90% success (expected)

---

## Current Code Status

**All uncommitted changes (staged but not committed):**
```
backend/coresignal_company_lookup.py               | 56 ++++++++++++
backend/jd_analyzer/api/domain_search.py           | 45 ++++++++++
backend/jd_analyzer/company/company_validation_agent.py | 13 +++
```

**These changes add:**
- Skip Stage 1 for pre-selected companies
- Anthropic debug logging
- Company structure preservation
- Improved name-based lookup (wildcard + US filter)

**Next session should:**
1. Add website-based lookup (this document)
2. Test end-to-end flow
3. Commit all working code together

---

## Questions for Next Session

1. Should we show website in company research UI? (recommended: YES)
2. Should we cache website → company_id mappings? (recommended: YES, in Supabase)
3. Should we fall back to name search if website lookup fails? (recommended: YES)
4. Should we validate that website actually exists before lookup? (recommended: NO, trust Anthropic)

---

**Last Updated:** Nov 7, 2025 - 3:35 PM
**Status:** Ready for implementation
**Priority:** HIGH (blocks employee search functionality)
