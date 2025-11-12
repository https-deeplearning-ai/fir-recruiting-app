# Domain Search Pipeline - Complete Technical Documentation

**Last Updated:** November 11, 2025
**Version:** 2.0 (Post-Haiku Migration)
**Purpose:** Comprehensive reference for the complete domain search/candidate preview pipeline

---

## Executive Summary

The domain search pipeline enables users to discover relevant companies and candidate profiles by:
1. Parsing job requirements (JD)
2. Discovering 50-100 companies in the target domain
3. Screening companies for relevance using AI with web search
4. Finding candidate profiles at those companies via CoreSignal
5. Displaying rich candidate cards with full metadata

### Primary Endpoint

**`POST /api/jd/domain-company-preview-search`**
- **File:** `jd_analyzer/api/domain_search.py:2021-2260`
- **Search Time:** 2-5 minutes
- **Cost:** ~$1.35 (fresh) or ~$0.40 (70% cached)

### CoreSignal Endpoint Used

**Employee Search:** `/v2/employee_clean/search/es_dsl/preview`
- Returns ~20 employee objects per page
- Uses Elasticsearch DSL queries
- **NOTE:** Does NOT accept `size` parameter

---

## Complete 10-Step Data Flow

### Step 1: User Input
- **Frontend:** `App.js:2110`
- **User provides:** Domain, role, companies, skills
- **Payload:**
  ```json
  {
    "jd_requirements": {
      "target_domain": "voice ai",
      "role_title": "ML Engineer",
      "mentioned_companies": ["Deepgram"]
    }
  }
  ```

### Step 2: Company Discovery
- **Method:** `discover_companies()` (company_research_service.py:375-486)
- **APIs:** Tavily (web search) + Claude Haiku (validation)
- **Output:** 50-100 companies with domains
- **Time:** 30-60s | **Cost:** $0.40

### Step 3: CoreSignal ID Lookup (4-Tier)
- **Method:** `_get_company_coresignal_id()` (lines 1626-1702)
- **Tiers:**
  1. Direct company search (40-50%)
  2. Employee reverse lookup (+20-30%)
  3. Tavily + Claude WebSearch (+10-15%)
  4. Heuristic fallback (+5-10%)
- **Success Rate:** 60-80%
- **Time:** 20-40s | **Cost:** $0.50

### Step 4: Company Screening
- **Method:** `screen_companies_with_haiku()` (lines 675-782)
- **Model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
- **Tool:** Anthropic Web Search (`web_search_20250305`)
- **Adds:** `relevance_score` (1-10), `screening_reasoning`, `scored_by`
- **Time:** 90-180s | **Cost:** $0.50

### Step 5: Employee Query Construction
- **Method:** `_build_experience_based_query()` (domain_search.py:710-805)
- **Query:** ES DSL with MUST (company) + SHOULD (role)
- **Example:**
  ```json
  {
    "query": {
      "bool": {
        "must": [{"nested": {"path": "experience", "query": {"term": {"experience.company_id": 3829471}}}}],
        "should": [{"match": {"job_title": "ML Engineer"}}]
      }
    }
  }
  ```

### Step 6: CoreSignal Employee Search
- **Endpoint:** `POST /v2/employee_clean/search/es_dsl/preview?page=1`
- **Returns:** ~20 employees per page
- **Headers:** `apikey`, `Content-Type: application/json`
- **Cost:** $0.10 per search
- **Time:** 2-4s per search

### Step 7: Profile Normalization
- **Method:** `normalize_profile_fields()` (domain_search.py:1065-1242)
- **Mappings:**
  - `full_name` → `name`
  - `job_title` → `title`
  - `location_raw_address` → `location`
  - `generated_headline` → `headline`

### Step 8: Response Assembly
- **Format:** JSON with companies + candidates
- **Structure:**
  ```json
  {
    "stage1_companies": [{
      "name": "Deepgram",
      "relevance_score": 8.5,
      "screening_reasoning": "...",
      "scored_by": "claude_haiku_with_websearch"
    }],
    "stage2_previews": [{
      "name": "John Doe",
      "title": "Senior ML Engineer",
      "location": "San Francisco"
    }]
  }
  ```

### Step 9: Cache Storage
- **Table:** `company_discovery_cache`
- **TTL:** 7 days
- **Key:** Hash of JD requirements

### Step 10: UI Rendering
- **Component:** Candidate cards (App.js:4373-4640)
- **Displays:** Name, title, company, headline, location, connections

---

## Field Mappings

| UI Display | Backend Field | CoreSignal Source | Fallback Chain |
|------------|---------------|-------------------|----------------|
| Name | `name` | `full_name` | `full_name` |
| Job Title | `title` | `job_title` | `job_title` → `headline` |
| Company | `current_company` | `company_name` | Direct |
| Headline | `headline` | `generated_headline` | `generated_headline` → `headline` |
| Location | `location` | `location_raw_address` | `location_raw_address` → `location` |

---

## Recent Fixes (Nov 11, 2025)

### Fix 1: Field Name Mismatch ✅ FIXED
- **Problem:** Backend sends `screening_reasoning`, frontend expects `relevance_reasoning`
- **Files:** `App.js:747, 4940`
- **Result:** UI now displays reasoning text (not "undefined")

### Fix 2: Employee Field Names ✅ FIXED
- **Problem:** Using `title` instead of `job_title`
- **Files:** `company_research_service.py:1732`, `enhanced_company_research_service.py:619`
- **Result:** Employee titles now populate correctly

### Fix 3: Duplicate Headlines ⚠️ IDENTIFIED
- **Problem:** Same text shown as job title AND italicized quote
- **Cause:** Fallback chain uses `headline` for title, then displays `headline` again
- **Solution:** Add deduplication check (NOT YET APPLIED)

### Fix 4: Role Field Priority ✅ FIXED
- **Problem:** Using `jd_context["title"]` instead of `jd_context["role_title"]`
- **File:** `company_research_service.py:1770`
- **Result:** SHOULD clause now matches specific role

### Fix 5: Cache TTL ✅ FIXED (Temporary)
- **Changed:** 48 hours → 1 hour
- **File:** `app.py:3079`
- **Reason:** Invalidate old GPT-5 results
- **TODO:** Increase back to 48 hours after migration

---

## Performance & Costs

### Timing
- **Total:** 2-5 minutes
- **Bottleneck:** Company screening (60-70% of time)

### Cost Breakdown
| Component | Cost |
|-----------|------|
| Company Discovery | $0.40 |
| CoreSignal ID Lookup | $0.50 |
| Company Screening | $0.50 |
| Employee Search | $0.50 |
| **Total** | **$1.90** |
| **With 70% Cache** | **$0.57** |

---

## Visual Flow

```
User Input → /api/jd/domain-company-preview-search
    ↓
Company Discovery (Tavily + Claude) → 50-100 companies
    ↓
CoreSignal ID Lookup (4-tier) → 60-80% success
    ↓
Company Screening (Haiku + WebSearch) → relevance scores
    ↓
Employee Query (ES DSL) → MUST (company) + SHOULD (role)
    ↓
CoreSignal Search → ~20 employees per search
    ↓
Profile Normalization → field mapping
    ↓
UI Rendering → Candidate cards
```

---

## Key File Locations

| Component | File | Lines |
|-----------|------|-------|
| Main Endpoint | `jd_analyzer/api/domain_search.py` | 2021-2260 |
| Company Discovery | `company_research_service.py` | 375-486 |
| Haiku Screening | `company_research_service.py` | 675-782 |
| ID Lookup | `company_research_service.py` | 1626-1702 |
| Employee Queries | `domain_search.py` | 710-805 |
| Normalization | `domain_search.py` | 1065-1242 |
| UI Cards | `App.js` | 4373-4640 |
| Role Filtering | `company_research_service.py` | 1770 |

---

## Troubleshooting

### All Companies Score 5.0
- **Cause:** Cache hit (old GPT-5 results) or screening errors
- **Fix:** Add `"bypass_cache": true` to request

### Employee Titles Show "N/A"
- **Cause:** Field mapping uses wrong field name
- **Fix:** Verify `job_title` field extraction (already fixed)

### Duplicate Headlines
- **Cause:** Fallback logic reuses `headline` field
- **Fix:** Apply deduplication in App.js:4445 (pending)

### UI Shows "undefined"
- **Cause:** Field name mismatch (`screening_reasoning` vs `relevance_reasoning`)
- **Fix:** Already applied in App.js:747, 4940

---

**End of Documentation**

For detailed code examples and API schemas, see original 64KB version or check source files directly.
