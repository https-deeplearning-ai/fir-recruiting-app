# Synthflow Companies Analysis - Multiple Entities Discovered

**Date:** November 10, 2025
**Discovery:** CoreSignal `company_base` API reveals TWO different "Synthflow" companies
**Impact:** We may have searched the WRONG Synthflow company for Voice AI candidates

---

## 🚨 Critical Finding

The `company_similar_collection` from company_base API shows **multiple Synthflow entities**:

### 1. **SynthFlow** (Backend Automation) - ID: 98601775
**What We Currently Have:**
- URL: https://www.linkedin.com/company/synthflow
- Website: http://synthflow.ink/
- Industry: Software Development
- Size: 2-10 employees
- Description: "SynthFlow is developing a visual, **AI-driven backend automation platform** to help developers and teams quickly create and deploy secure APIs with minimal coding by using graph-based logic and automated infrastructure orchestration."
- Employee Count: `null` (no data)
- Created: 2025-05-22 (VERY NEW - only 6 months old!)
- Last Updated: 2025-11-09

**⚠️ RED FLAGS:**
- ❌ **NOT Voice AI** - This is an API automation platform
- ❌ Only 6 months old (May 2025)
- ❌ No employee data in CoreSignal
- ❌ Wrong domain for Voice AI industry

### 2. **SynthFlow AI** (Voice AI - Likely the RIGHT One!)
**From Similar Companies Collection:**
- URL: https://de.linkedin.com/company/synthflowai
- Domain: `.de` (Germany)
- **This is likely the VOICE AI company we're actually looking for!**
- Not yet looked up - need to fetch full company_base data

---

## 📊 All Synthflow Variations in company_similar_collection

From ID 98601775's similar companies (15 total):

| # | URL | Domain | Status | Notes |
|---|-----|--------|--------|-------|
| 1 | https://de.linkedin.com/company/**synthflowai** | Germany | Active | 🎯 **LIKELY THE VOICE AI COMPANY** |
| 2 | https://ca.linkedin.com/company/faxsipit-services-inc- | Canada | Active | Unrelated (fax services) |
| 3 | https://uk.linkedin.com/company/devfinn-limited | UK | Active | Unrelated (dev services) |
| 4 | https://www.linkedin.com/company/wx-technology-group | US | Active | Unrelated |
| 5 | https://fr.linkedin.com/company/soap-agence-bubble-io | France | Active | Unrelated (Bubble.io agency) |
| 6 | https://hk.linkedin.com/company/ivy-ai-solutions-limited | Hong Kong | Active (was deleted, restored) | Unrelated |
| 7 | https://www.linkedin.com/company/ahoimate | US | Active | Unrelated |
| 8 | https://www.linkedin.com/company/nobelbiz-inc- | US | Deleted | Unrelated (VoIP services) |
| 9 | https://uk.linkedin.com/company/azkytech | UK | Deleted (was restored) | Unrelated |
| 10 | https://www.linkedin.com/company/nerdheadz | US | Deleted | Unrelated |
| 11 | https://www.linkedin.com/company/seneca-gaming-corporation | US | Deleted | Unrelated (gaming) |
| 12 | https://uk.linkedin.com/company/ivy-ai-solutions-limited | UK | Active | Duplicate of #6 |
| 13 | https://ch.linkedin.com/company/iadi-org | Switzerland | Active | Unrelated |
| 14 | https://ca.linkedin.com/company/clotguard | Canada | Active | Unrelated (medical) |
| 15 | https://au.linkedin.com/company/modlr | Australia | Active | Unrelated (financial planning) |

---

## 🎯 The Real Synthflow AI (Voice AI Company)

### Public Information (from web)
**Website:** https://synthflow.ai (NOT .ink)
**Product:** AI voice agents for phone calls
**Description:** "Build AI voice agents that make and receive phone calls"
**Industry:** Voice AI, Conversational AI
**Use Case:** Customer support, sales calls, appointment booking

**This matches the Voice AI domain search!**

### How to Find in CoreSignal

**Option 1: Search by Website**
```python
lookup = CoreSignalCompanyLookup()
match = lookup.lookup_by_website("synthflow.ai")
```

**Option 2: Search by Name with Domain Filter**
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"name": "SynthFlow"}},
        {"wildcard": {"website": "*synthflow.ai*"}}
      ]
    }
  }
}
```

**Option 3: Direct LinkedIn URL Lookup**
```python
# Try to look up: https://de.linkedin.com/company/synthflowai
# or: https://www.linkedin.com/company/synthflowai
```

---

## 🔍 Why This Confusion Happened

### Root Cause: Name Collision
1. **Two different companies** both named "SynthFlow"
2. One is **backend automation** (.ink domain)
3. One is **voice AI** (.ai domain)
4. CoreSignal linked them as "similar companies" (correct categorization)

### Our Mistake
1. G2/Capterra search found "Synthflow" as Voice AI competitor
2. Company lookup found ID 98601775 (backend automation one)
3. We never verified the domain matched (.ink vs .ai)
4. Searched for employees at the WRONG company

### Why Lookup Found Wrong One
The four-tier lookup strategy probably matched on:
- **Tier 2:** Name exact match "SynthFlow" → Found ID 98601775 first
- Never checked if the **domain** matched the Voice AI company

---

## 💡 How to Fix the Lookup

### Immediate Fix: Add Domain Verification

**File:** `backend/coresignal_company_lookup.py`

**Current Tier 2 Logic:**
```python
# Line ~200
if company_data.get('name', '').lower() == search_name.lower():
    print(f"✅ Exact match found on page {page}: '{company_data.get('name')}'")
    return match_result
```

**Improved Logic with Domain Check:**
```python
# If we have a website, verify domain matches
if website and company_data.get('name', '').lower() == search_name.lower():
    company_website = company_data.get('website', '')

    # Extract domains for comparison
    search_domain = extract_domain(website)  # "synthflow.ai"
    company_domain = extract_domain(company_website)  # "synthflow.ink"

    if search_domain == company_domain:
        print(f"✅ Exact match with verified domain on page {page}")
        return match_result
    else:
        print(f"⚠️  Name match but domain mismatch: {company_domain} != {search_domain}")
        print(f"   Continuing search for correct domain...")
        continue  # Keep looking
```

---

## 🧪 Test Plan

### Test 1: Look Up Correct Synthflow AI
```python
from coresignal_company_lookup import CoreSignalCompanyLookup

lookup = CoreSignalCompanyLookup()

# Try with .ai domain
result = lookup.lookup_with_fallback(
    company_name="Synthflow",
    website="https://synthflow.ai",  # Correct domain
    confidence_threshold=0.75
)

print(f"Company ID: {result['company_id']}")
print(f"Tier: {result['tier']}")
```

**Expected Result:** Different company ID (NOT 98601775)

### Test 2: Search Employees at Correct Company
```python
# Use the correct ID from Test 1
correct_id = result['company_id']

query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"last_company_id": correct_id}}
            ]
        }
    }
}

# Search without location filter
employees = search_employees(query)
print(f"Found {len(employees)} employees")
```

**Expected Result:** 10-50 employees (Synthflow AI is a real company with a team)

### Test 3: Verify Domain in company_base
```python
# Fetch company_base data for correct ID
company_data = fetch_company_base(correct_id)
print(f"Website: {company_data.get('website')}")
# Should print: "https://synthflow.ai" or "http://synthflow.ai"
```

---

## 📋 Other Companies to Verify

**These may also have similar issues:**

### Murf.ai (No ID Found)
- **Expected:** Murf.ai - AI voice generation
- **Possible Issue:** Name collision with "Murf" (unrelated companies)
- **Action:** Search explicitly with "murf.ai" domain

### VEED (ID: 33312984)
- **Expected:** VEED.io - Video editing with AI voiceovers
- **Verify:** Website should be "veed.io"
- **Action:** Check if domain matches

### Krisp (ID: 21473726)
- **Expected:** Krisp.ai - Noise cancellation for calls
- **Verify:** Website should be "krisp.ai"
- **Action:** Check if domain matches

### Otter.ai (ID: 13006266)
- **Expected:** Otter.ai - AI meeting transcription
- **Verify:** Website should be "otter.ai"
- **Action:** Check if domain matches

---

## 🎯 Action Items

### HIGH PRIORITY (Do Now)
1. ✅ Document all Synthflow variations (DONE - this doc)
2. ⏳ Look up correct Synthflow AI company (with .ai domain)
3. ⏳ Test employee search with correct ID
4. ⏳ Verify domains for all 7 companies in session

### MEDIUM PRIORITY (This Week)
1. ⏳ Implement domain verification in lookup logic
2. ⏳ Re-run domain search with corrected company IDs
3. ⏳ Update session files with correct companies
4. ⏳ Test with verified correct IDs

### LOW PRIORITY (Future)
1. ⏳ Add domain validation to company discovery stage
2. ⏳ Warn user when multiple companies match same name
3. ⏳ Show domain in UI to help users verify correctness

---

## 📊 Expected Impact After Fix

**Before Fix:**
- Companies: 7 discovered
- IDs: 6/7 matched (85.7%)
- Employees: 0 found
- **Root Cause:** Wrong company IDs (domain mismatch)

**After Fix:**
- Companies: 7 discovered
- IDs: 7/7 with domain verification (100%)
- Employees: **50-200 expected** (these are real Voice AI companies)
- **Root Cause Resolved:** Correct company IDs

---

## 💡 Lessons Learned

1. **Company Names Are Not Unique** - Always verify domain
2. **Similar Names ≠ Same Company** - "SynthFlow" (.ink) vs "SynthFlow AI" (.ai)
3. **Domain Is Critical** - Should be part of matching criteria
4. **Test with Known Companies** - Use larger, well-known companies first
5. **Verify API Responses** - Don't assume first match is correct

---

## 🔗 References

- **SynthFlow (Backend):** https://synthflow.ink/ - API automation
- **SynthFlow AI (Voice):** https://synthflow.ai/ - Voice AI agents
- **LinkedIn (Backend):** https://www.linkedin.com/company/synthflow
- **LinkedIn (Voice AI):** https://de.linkedin.com/company/synthflowai
- **Session Files:** `logs/domain_search_sessions/sess_20251111_041155_eca8dc98/`
- **Company Base API Response:** See user message (this document)

---

## 📞 Next Steps

**Immediate Action:** Let's look up the CORRECT Synthflow AI company and test if it has employees!

```bash
# Test 1: Find correct Synthflow AI
python3 -c "
from coresignal_company_lookup import CoreSignalCompanyLookup
lookup = CoreSignalCompanyLookup()
result = lookup.lookup_with_fallback('Synthflow', 'https://synthflow.ai')
print(f'Correct ID: {result}')
"

# Test 2: Search employees at correct company
# (Use ID from Test 1)
```

Would you like me to:
1. **Look up the correct Synthflow AI now?**
2. **Implement domain verification in the lookup code?**
3. **Re-run the entire domain search with verified companies?**
