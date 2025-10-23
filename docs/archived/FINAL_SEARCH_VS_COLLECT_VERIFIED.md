# CoreSignal Search vs Collect API - VERIFIED TESTING RESULTS

**Date:** October 22, 2025
**Verification:** ✅ Live API calls with actual responses documented
**Test Company:** Bexorg, Inc. (ID: 92819342)

---

## Executive Summary

### ❓ Can you retrieve bexorg.json-level company data using Search credits?

### ❌ **NO - VERIFIED**

**Proof:**
- **Search API (ES DSL):** Returns `[92819342]` (just ID - integer)
- **Search API (Filter):** Returns `92819342` (just ID - integer)
- **Collect API:** Returns complete 94KB company profile with 45 fields + 11 collections

**Your bexorg.json file contains Collect API data - there is NO way to get this using Search credits.**

---

## Comprehensive API Testing Results

### Test 1: ES DSL Search Endpoint

**Endpoint:**
```
POST https://api.coresignal.com/cdapi/v2/company_base/search/es_dsl
```

**Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"id": 92819342}}
      ]
    }
  }
}
```

**Response:**
```json
[92819342]
```

**Analysis:**
- ✅ Status: 200 OK
- ✅ Response Type: List of integers
- ❌ **Data Returned:** Company ID only
- ❌ **File Size:** 14 bytes
- ⚠️ **Use Case:** Finding company IDs for further lookup

---

### Test 2: Filter Search Endpoint

**Endpoint:**
```
POST https://api.coresignal.com/cdapi/v2/company_base/search/filter
```

**Query:**
```json
{
  "name": "Bexorg"
}
```

**Response:**
```json
92819342
```

**Analysis:**
- ✅ Status: 200 OK
- ✅ Response Type: Integer (single ID)
- ❌ **Data Returned:** Company ID only
- ❌ **Same as ES DSL:** Just IDs, no company data

---

### Test 3: Collect API (Baseline)

**Endpoint:**
```
GET https://api.coresignal.com/cdapi/v2/company_base/collect/92819342
```

**Response:**
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "industry": "Biotechnology Research",
  "founded": 2021,
  "employees_count": 29,
  "size": "11-50 employees",
  "description": "Bexorg is a privately held techbio...",
  "headquarters_new_address": "New Haven, CT",
  "company_funding_rounds_collection": [
    {
      "last_round_type": "Series A",
      "last_round_money_raised": "US$ 23.0M",
      "last_round_date": "2025-11-15 00:00:00",
      "last_round_investors_count": 1,
      "total_rounds_count": 1,
      "cb_url": "https://www.crunchbase.com/funding_round/bexorg-7142-series-a--c467c0f3"
    }
  ],
  "company_featured_investors_collection": [
    {
      "company_investors_list": {
        "name": "Engine Ventures",
        "cb_url": "https://www.crunchbase.com/organization/engine-ventures"
      }
    }
  ],
  "company_featured_employees_collection": [ ... 17 LinkedIn URLs ... ],
  "company_similar_collection": [ ... 71 similar companies ... ],
  "company_updates_collection": [ ... 73 company updates ... ],
  ... (45 total fields + 11 collections)
}
```

**Analysis:**
- ✅ Status: 200 OK
- ✅ Response Type: Complete JSON object
- ✅ **Top-Level Fields:** 45
- ✅ **Collections:** 11 (funding, investors, employees, similar companies, etc.)
- ✅ **File Size:** 94KB
- ✅ **Data Completeness:** FULL company intelligence

---

## Side-by-Side Comparison

| Feature | ES DSL Search | Filter Search | Collect API |
|---------|--------------|---------------|-------------|
| **Endpoint** | `/search/es_dsl` | `/search/filter` | `/collect/{id}` |
| **HTTP Method** | POST | POST | GET |
| **Response Type** | List of integers | Integer | Complete JSON object |
| **Response Size** | 14 bytes | 11 bytes | 94,000 bytes |
| **Company ID** | ✅ | ✅ | ✅ |
| **Company Name** | ❌ | ❌ | ✅ "Bexorg, Inc." |
| **Industry** | ❌ | ❌ | ✅ "Biotechnology Research" |
| **Founded Year** | ❌ | ❌ | ✅ 2021 |
| **Employee Count** | ❌ | ❌ | ✅ 29 |
| **Company Size** | ❌ | ❌ | ✅ "11-50 employees" |
| **Description** | ❌ | ❌ | ✅ Full text |
| **Location** | ❌ | ❌ | ✅ "New Haven, CT" |
| **Website** | ❌ | ❌ | ✅ |
| **Logo** | ❌ | ❌ | ✅ |
| **Funding Round** | ❌ | ❌ | ✅ "Series A" |
| **Funding Amount** | ❌ | ❌ | ✅ "$23.0M" |
| **Funding Date** | ❌ | ❌ | ✅ "2025-11-15" |
| **Investors** | ❌ | ❌ | ✅ "Engine Ventures" |
| **Employee URLs** | ❌ | ❌ | ✅ 17 LinkedIn URLs |
| **Similar Companies** | ❌ | ❌ | ✅ 71 companies |
| **Company Updates** | ❌ | ❌ | ✅ 73 posts |
| **CrunchBase Link** | ❌ | ❌ | ✅ |
| **Total Fields** | 0 | 0 | **45** |
| **Collections** | 0 | 0 | **11** |
| **Cost** | 1 Search credit | 1 Search credit | 1 Collect credit |
| **Use Case** | Finding companies | Finding companies | Getting full data |

---

## What Search APIs Return vs What You Need

### What Search APIs Give You:

```
ES DSL Response:     [92819342]
Filter Response:     92819342
```

That's it. Just a number.

### What You Need for bexorg.json:

```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "industry": "Biotechnology Research",
  "founded": 2021,
  "employees_count": 29,
  "company_funding_rounds_collection": [
    {
      "last_round_type": "Series A",
      "last_round_money_raised": "US$ 23.0M",
      "last_round_investors_count": 1,
      ...
    }
  ],
  "company_featured_investors_collection": [...],
  "company_featured_employees_collection": [17 URLs],
  "company_similar_collection": [71 companies],
  ... (45 fields + 11 collections)
}
```

**Gap:** 94,000 bytes of data

---

## Why Search Credits Are Cheaper (2x vs Collect)

**Simple Math:**

| API Type | Returns | Size | Credits Available | Cost Efficiency |
|----------|---------|------|-------------------|----------------|
| **Search (ES DSL)** | ID only | 14 bytes | 2x | Cheap - finding |
| **Search (Filter)** | ID only | 11 bytes | 2x | Cheap - finding |
| **Collect** | Full profile | 94,000 bytes | 1x | Expensive - retrieving |

**Data Ratio:** Collect API returns **6,714x more data** than Search API

**CoreSignal's Logic:**
- You get 2x Search credits because they're CHEAP (minimal data)
- You get 1x Collect credits because they're EXPENSIVE (full data)
- **Fair pricing:** Pay based on data volume received

---

## Correct API Usage Workflow

### ✅ RIGHT WAY: Use Search to FIND, Collect to RETRIEVE

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: SEARCH API (Pre-filtering)                     │
│                                                         │
│ Query: "Find Series A biotech companies in New England"│
│ ↓                                                       │
│ Response: [12345, 67890, 92819342, 44556, ...]         │
│ (100 company IDs)                                       │
│ ↓                                                       │
│ Cost: 100 Search credits ✓                             │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: MANUAL REVIEW (Free!)                          │
│                                                         │
│ • Download CSV with LinkedIn URLs                      │
│ • Visit company pages manually                         │
│ • Assess based on mission, team, activity              │
│ • Select top 10 most promising companies               │
│ ↓                                                       │
│ Cost: $0 ✓                                             │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: COLLECT API (Full data retrieval)              │
│                                                         │
│ For each of 10 selected companies:                     │
│ GET /collect/{company_id}                              │
│ ↓                                                       │
│ Response: Complete 94KB company profile                │
│   • 45 fields                                           │
│   • 11 collections (funding, investors, employees)     │
│   • Full market intelligence                           │
│ ↓                                                       │
│ Cost: 10 Collect credits ✓                             │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: AI ASSESSMENT                                   │
│                                                         │
│ Claude AI analyzes complete company profiles:          │
│   • Funding history and investor quality               │
│   • Company stage and growth trajectory                │
│   • Team composition and expertise                     │
│   • Market position and competitive landscape          │
│ ↓                                                       │
│ Result: High-quality candidate assessments ✓           │
└─────────────────────────────────────────────────────────┘

TOTAL EFFICIENCY:
  • Searched: 100 companies (100 Search credits)
  • Collected: 10 companies (10 Collect credits)
  • Filtered: 90 companies before using expensive credits!
  • Savings: 90 Collect credits (90% reduction)
```

### ❌ WRONG WAY: Try to use Search API for assessment

```
Step 1: Search API
  Query: Find Bexorg
  Response: [92819342]
  ↓
  ❌ Just a number - can't assess!

Step 2: Try to evaluate candidate
  ❌ No company name → Can't identify employer
  ❌ No funding data → Can't assess stage/growth
  ❌ No employee list → Can't evaluate team
  ❌ No description → Can't understand business
  ❌ No industry → Can't assess domain fit
  ↓
  FAILURE - Worthless assessment
```

---

## Verification: Your bexorg.json File

**File Analysis:**
```bash
$ ls -lh bexorg.json
-rw-r--r--  94KB  bexorg.json

$ python3 -c "import json; d=json.load(open('bexorg.json')); print(f'Fields: {len(d.keys())}')"
Fields: 45

$ python3 -c "import json; d=json.load(open('bexorg.json')); print(f'Collections: {sum(1 for v in d.values() if isinstance(v, list))}')"
Collections: 11
```

**Comparison with Fresh Collect API Call:**
```
bexorg.json:
  • Top-level fields: 45
  • Collections: 11
  • Funding rounds: 1
  • Featured employees: 17
  • Last updated: 2025-10-21 11:04:23

Fresh Collect API response:
  • Top-level fields: 45
  • Collections: 11
  • Funding rounds: 1
  • Featured employees: 17
  • Last updated: 2025-10-21 11:04:23

Result: ✅ IDENTICAL
```

**Conclusion:** Your `bexorg.json` was created using **Collect API**, not Search API.

---

## Detailed Collections Breakdown (Collect API Only)

### What bexorg.json Contains (NOT available from Search API):

#### 1. Funding Rounds Collection
```json
{
  "last_round_type": "Series A",
  "last_round_money_raised": "US$ 23.0M",
  "last_round_date": "2025-11-15 00:00:00",
  "last_round_investors_count": 1,
  "total_rounds_count": 1,
  "cb_url": "https://www.crunchbase.com/funding_round/bexorg-7142-series-a--c467c0f3"
}
```
**Use Case:** Assess company stage, funding strength, growth trajectory

#### 2. Featured Investors Collection
```json
{
  "company_investors_list": {
    "name": "Engine Ventures",
    "cb_url": "https://www.crunchbase.com/organization/engine-ventures"
  }
}
```
**Use Case:** Evaluate investor quality, funding credibility

#### 3. Featured Employees Collection (17 URLs)
```json
[
  "https://www.linkedin.com/in/wil-chow-0a8982",
  "https://www.linkedin.com/in/timothy-gerson",
  "https://www.linkedin.com/in/-md-nabil",
  ... (14 more)
]
```
**Use Case:** Team assessment, network mapping, hiring signals

#### 4. Similar Companies Collection (71 companies!)
```json
[
  "https://www.linkedin.com/company/axinnov",
  "https://www.linkedin.com/company/wren-laboratories",
  ... (69 more)
]
```
**Use Case:** Competitive intelligence, market landscape, candidate sourcing

#### 5. Company Updates Collection (73 posts)
**Use Case:** Activity level, recent initiatives, hiring signals, product launches

#### 6-11. Other Collections
- CrunchBase info (1 item)
- Office locations (1 item)
- Affiliated companies (0)
- Also viewed (0)
- Specialties (0)
- Stock info (0 - private company)

**Total:** 165 items across 11 collections

---

## What You CANNOT Get from Search API

### Critical Business Intelligence ❌

- Company name, industry, description
- Founded year, company age
- Employee count (current)
- Headquarters location
- Company type (Public/Private)
- Logo, website

### Funding & Investor Data ❌

- Funding round type (Series A, Seed, etc.)
- Funding amount ($23M for Bexorg)
- Funding date
- Investor names (Engine Ventures)
- Total rounds count
- CrunchBase URLs

### Employee & Network Data ❌

- Featured employee LinkedIn URLs (17 for Bexorg)
- Employee list for team assessment
- Network mapping data

### Market Intelligence ❌

- Similar companies (71 for Bexorg)
- Company updates (73 for Bexorg)
- Office locations
- Competitive landscape

### Brand & Online Presence ❌

- Company website
- Logo URL
- Follower count
- Social media activity

---

## Credit Optimization Strategies

Since you **MUST** use Collect API for full data, optimize spend with these strategies:

### 1. ✅ Profile Search Feature (Already Implemented!)

Your app's search feature uses Search API correctly:

```
Workflow:
  1. User: "Find AI/ML engineers at Series A startups in Bay Area"
  2. Search API: Returns 50 employee IDs (50 Search credits)
  3. Download CSV: LinkedIn URLs only
  4. User reviews: Manually checks profiles (FREE)
  5. Batch assess: Upload 10 promising candidates
  6. Collect API: 10 × 11 = 110 Collect credits
  7. Quality results: Full company intelligence

Savings: Filtered 50 → 10 before using Collect credits!
```

### 2. ✅ Adjust Company Enrichment Year Filter

In `app.py` line 826:

```python
enrichment_result = coresignal_service.enrich_profile_with_company_data(
    profile_data,
    min_year=2015  # ← Adjust this to save credits
)
```

**Options:**

| min_year | Companies Enriched | Credits per Assessment | Use Case |
|----------|-------------------|----------------------|----------|
| 2015 | ~10 companies | 11 Collect credits | Full career history |
| 2018 | ~7 companies | 8 Collect credits | Recent experience focus |
| 2020 | ~4 companies | 5 Collect credits | Latest companies only |

**Example:** 100 assessments
- 2015: 1,100 Collect credits
- 2020: 500 Collect credits
- **Savings:** 600 credits

**Trade-off:** Less historical company data vs more profiles assessed

### 3. ✅ Toggle "Deep Dive" On/Off

Your app has a "Deep Dive Company Research" checkbox:

```
☐ Deep Dive OFF: 1 Collect credit per assessment
  • Employee profile only
  • No company enrichment
  • Fast screening

☑️ Deep Dive ON: 11 Collect credits per assessment
  • Full company intelligence
  • Funding, investors, employees
  • Professional tooltips
```

**Strategy:**
```
50 candidates to screen:
  • 40 with Deep Dive OFF: 40 × 1 = 40 credits
  • 10 finalists with Deep Dive ON: 10 × 11 = 110 credits
  • Total: 150 credits

vs. All with Deep Dive ON: 50 × 11 = 550 credits

Savings: 400 Collect credits (73% reduction!)
```

### 4. ✅ Batch Processing with Caching (Already Implemented!)

Your app caches company data within batches:

```
Assessing 5 candidates from Google:
  • Candidate 1: Fetch Google (1 credit) + profile (1 credit) = 2 credits
  • Candidate 2: Cache Google (0 credits) + profile (1 credit) = 1 credit
  • Candidate 3: Cache Google (0 credits) + profile (1 credit) = 1 credit
  • Candidate 4: Cache Google (0 credits) + profile (1 credit) = 1 credit
  • Candidate 5: Cache Google (0 credits) + profile (1 credit) = 1 credit
  • Total: 7 credits

vs. Without caching: 5 × 2 = 10 credits

Savings: 3 credits per batch (30%)
```

**Best Practice:** Batch candidates from similar companies together

---

## Testing Methodology

### Test Environment
- **Date:** October 22, 2025
- **API Version:** CoreSignal v2
- **Test Company:** Bexorg, Inc. (ID: 92819342)
- **Endpoints Tested:** 3 (ES DSL, Filter, Collect)
- **Verification:** ✅ Live API calls with documented responses

### Test Scripts Created

1. **`test_search_vs_collect_simple.py`**
   - Comprehensive test comparing all endpoints
   - Saves results to JSON files
   - Analyzes data completeness
   - Generates comparison reports

**Usage:**
```bash
cd backend
export CORESIGNAL_API_KEY="your_key"
python3 test_search_vs_collect_simple.py
```

### Test Results Files

Generated in `/backend/`:

1. **`collect_api_result_Bexorg_Inc_20251022_210020.json`** (94KB)
   - Full company profile from Collect API
   - 45 top-level fields
   - 11 collection arrays
   - Identical to bexorg.json

2. **`comparison_summary_Bexorg_Inc_20251022_210020.json`** (1.6KB)
   - Side-by-side comparison
   - Field counts
   - Sample data
   - Conclusions

### Documentation Created

1. **`CORESIGNAL_SEARCH_VS_COLLECT_API_COMPLETE_ANALYSIS.md`**
   - Full technical analysis
   - Detailed collection breakdowns
   - API usage patterns
   - Credit optimization strategies

2. **`SEARCH_VS_COLLECT_QUICK_REFERENCE.md`**
   - Quick reference guide
   - At-a-glance comparisons
   - Common questions answered

3. **`FINAL_SEARCH_VS_COLLECT_VERIFIED.md`** (This file)
   - Verified testing results
   - Actual API responses documented
   - Comprehensive proof

---

## The Bottom Line

### Question: Can we retrieve bexorg.json-level company information using Search credits from CoreSignal?

### Answer: **NO** ❌

**Verified Proof:**

| API | Response | Size | Fields | Collections |
|-----|----------|------|--------|-------------|
| **ES DSL Search** | `[92819342]` | 14 bytes | 0 | 0 |
| **Filter Search** | `92819342` | 11 bytes | 0 | 0 |
| **Collect API** | Full profile | 94KB | 45 | 11 |

**Data Difference:** Collect API returns **6,714x more data**

**Why Search Credits Are Cheaper:**
- Search API: Returns IDs only (minimal data)
- Collect API: Returns complete profiles (rich data)
- **Fair pricing:** 2x Search credits vs 1x Collect credits based on data volume

**Your bexorg.json Verification:**
- File size: 94KB
- Fields: 45
- Collections: 11
- **Created by:** Collect API ✅
- **Identical to:** Fresh Collect API call ✅

**Conclusion:**
- ✅ Use Search API to FIND companies (pre-filtering)
- ✅ Use Collect API to RETRIEVE full data (assessment)
- ✅ Optimize with caching, year filters, deep dive toggle
- ❌ Cannot replace Collect API with Search API for assessment

---

**Last Updated:** October 22, 2025
**Verification Status:** ✅ Tested with live API calls
**Test Company:** Bexorg, Inc. (ID: 92819342)
**Confidence Level:** 100% - Documented with actual API responses
