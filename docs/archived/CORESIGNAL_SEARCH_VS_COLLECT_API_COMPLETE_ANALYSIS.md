# CoreSignal API: Search vs Collect - Complete Analysis

**Date:** October 22, 2025
**Test Subject:** Bexorg, Inc. (Company ID: 92819342)
**Test Files:**
- `test_search_vs_collect_simple.py` (test script)
- `collect_api_result_Bexorg_Inc_20251022_210020.json` (94KB - full data)
- `search_api_result_Bexorg_Inc_20251022_210020.json` (14B - just ID)
- `comparison_summary_Bexorg_Inc_20251022_210020.json` (1.6KB - summary)

---

## Executive Summary

**Can you get bexorg.json-level data using Search credits?**

**NO.** ❌

- **Search API:** Returns company IDs only (14 bytes)
- **Collect API:** Returns complete company profiles (94KB+ with full details)
- **Search credits are 2x cheaper** because they return 2000x less data

---

## Detailed Test Results

### Test Setup

```python
Company: Bexorg, Inc.
Company ID: 92819342
LinkedIn URL: https://www.linkedin.com/company/bexorg-inc
```

### Test 1: Search API (`/v2/company_base/search/es_dsl`)

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
- ✅ **Status:** 200 OK
- ✅ **Cost:** 1 Search credit
- ⚠️ **Data Returned:** Company ID only (integer)
- ⚠️ **File Size:** 14 bytes
- ⚠️ **Use Case:** Finding/filtering companies

**What You Get:**
- Just the company ID
- No company name, no industry, no funding data
- Must call Collect API to get actual data

---

### Test 2: Collect API (`/v2/company_base/collect/{id}`)

**Endpoint:**
```
GET https://api.coresignal.com/cdapi/v2/company_base/collect/92819342
```

**Response:** Complete company profile (see below for detailed breakdown)

**Analysis:**
- ✅ **Status:** 200 OK
- ✅ **Cost:** 1 Collect credit
- ✅ **Data Returned:** Full company profile
- ✅ **File Size:** 94KB (6,714x larger than Search API response)
- ✅ **Use Case:** Retrieving complete company data

**What You Get:**

#### 1. **Top-Level Fields: 45 fields**

**Basic Information:**
- `id`, `url`, `hash`, `name`
- `website`, `size`, `industry`, `description`
- `followers`, `founded`, `logo_url`
- `type` (e.g., "Privately Held")
- `employees_count` (29)

**Headquarters Data:**
- `headquarters_city`, `headquarters_country`, `headquarters_state`
- `headquarters_street1`, `headquarters_street2`, `headquarters_zip`
- `headquarters_new_address` ("New Haven, CT")
- `headquarters_country_parsed` ("United States")

**Metadata:**
- `created`, `last_updated`, `last_response_code`
- `company_shorthand_name` ("bexorg-inc")
- `canonical_url`, `canonical_hash`
- `source_id`, `deleted` flag

#### 2. **Collection Arrays: 11 collections**

| Collection Name | Items | Description |
|----------------|-------|-------------|
| `company_funding_rounds_collection` | **1** | Funding round details |
| `company_featured_investors_collection` | **1** | Investor information |
| `company_featured_employees_collection` | **17** | Featured employee profiles |
| `company_crunchbase_info_collection` | **1** | CrunchBase links |
| `company_locations_collection` | **1** | Office locations |
| `company_similar_collection` | **71** | Similar companies |
| `company_updates_collection` | **73** | Company updates/posts |
| `company_affiliated_collection` | 0 | Affiliated companies |
| `company_also_viewed_collection` | 0 | Related companies |
| `company_specialties_collection` | 0 | Specialties/tags |
| `company_stock_info_collection` | 0 | Stock data (N/A for private companies) |

---

## Deep Dive: Collection Data Examples

### 1. Funding Rounds Collection

```json
{
  "id": 12429636,
  "last_round_investors_count": 1,
  "total_rounds_count": 1,
  "last_round_type": "Series A",
  "last_round_date": "2025-11-15 00:00:00",
  "last_round_money_raised": "US$ 23.0M",
  "cb_url": "https://www.crunchbase.com/funding_round/bexorg-7142-series-a--c467c0f3",
  "created": "2025-10-21 11:04:23",
  "last_updated": "2025-10-21 11:04:23",
  "deleted": 0
}
```

**What This Gives You:**
- Round type (Series A, Seed, etc.)
- Amount raised ($23M)
- Date of funding
- Number of investors
- CrunchBase URL for verification

### 2. Featured Investors Collection

```json
{
  "company_investors_list": {
    "id": 33813,
    "name": "Engine Ventures",
    "hash": "85202ec52aa41c2ad218941631580326",
    "cb_url": "https://www.crunchbase.com/organization/engine-ventures",
    "created": "2024-03-13 00:10:58",
    "last_updated": "2024-03-13 00:10:58"
  }
}
```

**What This Gives You:**
- Investor names
- Investor CrunchBase profiles
- Multiple investors if applicable

### 3. Featured Employees Collection (Sample)

```json
{
  "id": 208644755,
  "company_id": 92819342,
  "url": "https://www.linkedin.com/in/wil-chow-0a8982",
  "created": "2024-07-04 13:22:01",
  "last_updated": "2025-10-21 11:04:23",
  "deleted": 0
}
```

**What This Gives You:**
- LinkedIn URLs of 17 featured employees
- Ability to assess team quality
- Network mapping opportunities
- Timestamps for tracking changes

### 4. CrunchBase Info Collection

```json
{
  "id": 507309,
  "company_id": 92819342,
  "cb_url": "https://www.crunchbase.com/organization/bexorg-7142",
  "created": "2025-10-21 11:04:23",
  "last_updated": "2025-10-21 11:04:23",
  "deleted": 0
}
```

**What This Gives You:**
- Direct CrunchBase company page link
- Additional funding/investor data source

### 5. Company Locations Collection

```json
{
  "id": 119105160,
  "company_id": 92819342,
  "location_address": "-; New Haven, CT 06519, US",
  "is_primary": 1,
  "created": "2023-05-15 17:51:52",
  "last_updated": "2025-10-21 11:04:23",
  "deleted": 0
}
```

**What This Gives You:**
- Full office addresses
- Primary location indicator
- Multi-office company detection

### 6. Similar Companies Collection (71 companies!)

```json
{
  "id": 824165195,
  "company_id": 92819342,
  "url": "https://www.linkedin.com/company/axinnov",
  "created": "2023-05-15 17:51:52",
  "last_updated": "2024-02-16 00:24:49",
  "deleted": 1
}
```

**What This Gives You:**
- 71 LinkedIn URLs of similar companies
- Market landscape understanding
- Competitive intelligence
- Candidate sourcing opportunities

### 7. Company Updates Collection (73 updates!)

Contains recent company posts, announcements, and social media activity. Useful for:
- Company activity level
- Recent initiatives
- Hiring signals
- Product launches

---

## Data Comparison Table

| Feature | Search API | Collect API |
|---------|-----------|-------------|
| **Response Size** | 14 bytes | 94KB (6,714x larger) |
| **Top-level Fields** | 0 | 45 |
| **Company Name** | ❌ | ✅ |
| **Industry** | ❌ | ✅ |
| **Founded Year** | ❌ | ✅ |
| **Employee Count** | ❌ | ✅ |
| **Description** | ❌ | ✅ |
| **Headquarters** | ❌ | ✅ |
| **Funding Data** | ❌ | ✅ (full details) |
| **Investors** | ❌ | ✅ (names + links) |
| **Employee List** | ❌ | ✅ (17 LinkedIn URLs) |
| **CrunchBase Links** | ❌ | ✅ |
| **Similar Companies** | ❌ | ✅ (71 companies) |
| **Company Updates** | ❌ | ✅ (73 updates) |
| **Office Locations** | ❌ | ✅ |
| **Logo URL** | ❌ | ✅ |
| **Website** | ❌ | ✅ |
| **Cost** | 1 Search credit | 1 Collect credit |
| **Credit Ratio** | 2x cheaper | Baseline |

---

## Why Search Credits Are Cheaper (2x vs Collect)

CoreSignal's credit pricing reflects the data completeness:

### Search Credits (2x quantity for same price)
- **Purpose:** Finding companies that match criteria
- **Returns:** Company IDs only (14 bytes)
- **Workflow:**
  1. Search for "Series A biotech companies in Connecticut"
  2. Get back 50 company IDs
  3. Manually review on LinkedIn
  4. Select 5 promising companies
  5. Use Collect API for those 5

**Example Cost:**
- Search: 1 Search credit (found 50 companies)
- Collect: 5 Collect credits (full data for 5 selected companies)
- **Savings:** You filtered 50 → 5 before using expensive credits!

### Collect Credits (Baseline)
- **Purpose:** Retrieving complete company profiles
- **Returns:** Full company data (94KB+)
- **Use Case:** When you need actual data for assessment/analysis

---

## Verification: bexorg.json Analysis

Your existing `bexorg.json` file is **100% identical** to the Collect API response:

```bash
Fresh Collect API call vs Original bexorg.json:
  ✓ IDENTICAL: Both files contain the exact same data

Comparison:
  - Top-level fields: 45 (both)
  - Funding rounds: 1 (both)
  - Featured employees: 17 (both)
  - Last updated: 2025-10-21 11:04:23 (both)
```

**Conclusion:** Your `bexorg.json` was created using the **Collect API**, NOT the Search API.

---

## What Data You CANNOT Get From Search API

Based on our testing, Search API **does not provide**:

### Critical Business Intelligence
❌ Company name, industry, description
❌ Founded year, company age
❌ Employee count (current)
❌ Headquarters location
❌ Company type (Public/Private)

### Funding & Investor Data
❌ Funding round type (Seed, Series A, etc.)
❌ Funding amount ($23M for Bexorg)
❌ Funding date
❌ Investor names (Engine Ventures)
❌ Total rounds count
❌ CrunchBase URLs

### Employee & Network Data
❌ Featured employee LinkedIn URLs (17 for Bexorg)
❌ Employee list for team assessment
❌ Network mapping data

### Market Intelligence
❌ Similar companies (71 for Bexorg)
❌ Company updates (73 for Bexorg)
❌ Office locations
❌ Competitive landscape

### Brand & Online Presence
❌ Company website
❌ Logo URL
❌ Follower count
❌ Social media activity

---

## Correct API Usage Strategy

### ✅ When to Use Search API

**Scenario:** Pre-filtering large candidate pools

```
User Goal: "Find 100 Series A biotech companies in New England"
          ↓
1. Search API: Find 100 company IDs (100 Search credits)
          ↓
2. Manual Review: Check LinkedIn pages (FREE)
          ↓
3. Select Top 10: Based on manual review
          ↓
4. Collect API: Get full data for 10 (10 Collect credits)
          ↓
5. Deep Assessment: Use complete data for AI analysis
```

**Credit Efficiency:**
- Search: 100 credits (cheap, you have 2x)
- Collect: 10 credits (expensive, but only for chosen companies)
- **Total:** Assessed 100 companies, paid for 10 full profiles

### ❌ When NOT to Use Search API

**Wrong Scenario:** Trying to assess candidates with Search API

```
❌ Search API returns ID: 92819342
❌ No company name → Can't tell candidate's employer quality
❌ No funding data → Can't assess company stage/growth
❌ No employee list → Can't evaluate team strength
❌ No description → Can't understand business model

Result: Worthless assessment, wasted credit
```

### ✅ When to Use Collect API

**Scenario:** Need actual company intelligence for assessment

```
Use Collect API when you need:
- Candidate assessment (need full company context)
- Batch processing (assessing multiple known candidates)
- Company deep dive (tooltips, enrichment in your app)
- Funding analysis (investor quality, round size)
- Team evaluation (employee LinkedIn URLs)
```

**Example: Your Current App**
```
Single Profile Assessment:
  1. User submits LinkedIn URL
  2. Collect employee profile (1 Collect credit)
  3. Collect 10 company profiles for work history (10 Collect credits)
  4. AI assessment with FULL company context
  5. HIGH-QUALITY evaluation

Total: 11 Collect credits per assessment
Quality: Professional-grade intelligence
```

---

## Credit Optimization Strategies

Since you **must** use Collect API for full data, optimize spend with:

### 1. ✅ Profile Search Feature (Already Implemented!)

Your app's search feature uses Search API correctly:

```
1. User: "Find AI/ML engineers at Series A startups in Bay Area"
2. Search API: Returns 50 employee IDs (50 Search credits)
3. Download CSV: LinkedIn URLs only
4. User reviews: Manually checks profiles
5. Batch assess: Upload 10 promising candidates
6. Collect API: 10 × 11 = 110 Collect credits
7. Quality results: Full company intelligence

Savings: Filtered 50 → 10 before using Collect credits!
```

### 2. ✅ Adjust Company Enrichment Year Filter

In `app.py` line 826:

```python
# Current: Enriches companies from 2015+
enrichment_result = coresignal_service.enrich_profile_with_company_data(
    profile_data,
    min_year=2015  # ← Adjust this
)
```

**Options:**
- `min_year=2015` → ~10 companies → 11 Collect credits/assessment
- `min_year=2018` → ~7 companies → 8 Collect credits/assessment
- `min_year=2020` → ~4 companies → 5 Collect credits/assessment

**Trade-off:** Less historical company data vs more profiles assessed per month

### 3. ✅ Toggle Company Enrichment On/Off

"Deep Dive Company Research" checkbox in your app:

```
☑️ Deep Dive ON:  11 Collect credits → Rich company tooltips
☐ Deep Dive OFF:  1 Collect credit  → Basic assessment only

Strategy:
- Initial screening: Deep Dive OFF (1 credit)
- Final 10 candidates: Deep Dive ON (11 credits)

Example: 50 candidates
- 40 screened without deep dive: 40 × 1 = 40 credits
- 10 finalists with deep dive: 10 × 11 = 110 credits
- Total: 150 credits (vs 550 if deep dive for all)
```

### 4. ✅ Batch Processing with Caching

Your app caches company data within batches:

```
Assessing 5 candidates from Google:
- Candidate 1: Fetch Google (1 credit) + profile (1 credit) = 2 credits
- Candidate 2: Cache Google (0 credits) + profile (1 credit) = 1 credit
- Candidate 3: Cache Google (0 credits) + profile (1 credit) = 1 credit
- Candidate 4: Cache Google (0 credits) + profile (1 credit) = 1 credit
- Candidate 5: Cache Google (0 credits) + profile (1 credit) = 1 credit

Total: 7 credits (vs 10 without caching)
```

**Best Practice:** Batch similar candidates together

---

## Testing Methodology

### Test Script: `test_search_vs_collect_simple.py`

**Features:**
- Tests both APIs for the same company
- Compares response size and structure
- Analyzes data completeness
- Generates comparison reports
- Saves full API responses for inspection

**Usage:**
```bash
export CORESIGNAL_API_KEY="your_key"
python3 test_search_vs_collect_simple.py
```

**Output Files:**
- `search_api_result_*.json` - Search API response (14B)
- `collect_api_result_*.json` - Collect API response (94KB)
- `comparison_summary_*.json` - Side-by-side comparison

### Test Results Summary

```
Company: Bexorg, Inc. (ID: 92819342)

Search API:
  ✓ Status: 200 OK
  ✓ Response: [92819342]
  ✓ Size: 14 bytes
  ✗ Data: ID only, no company details

Collect API:
  ✓ Status: 200 OK
  ✓ Response: Complete company profile
  ✓ Size: 94KB
  ✓ Fields: 45 top-level + 11 collections
  ✓ Data: Full company intelligence

Comparison:
  • Collect API returns 6,714x more data
  • Search API useful for finding only
  • Collect API required for assessment
```

---

## Conclusion

### ❌ Search API CANNOT Provide bexorg.json-level Data

**What Search API Returns:**
- Company ID only (integer)
- 14 bytes of data
- No company details whatsoever

**What bexorg.json Contains:**
- 45 top-level fields
- 11 collection arrays
- 94KB of rich company intelligence
- Funding, investors, employees, locations, etc.

**The Gap:** 6,714x difference in data volume

### ✅ Collect API is REQUIRED for Full Data

To get bexorg.json-quality data, you **must** use Collect API:
- **Endpoint:** `/v2/company_base/collect/{company_id}`
- **Cost:** 1 Collect credit per company
- **Returns:** Complete company profile (94KB+)

### ✅ Search API's Actual Purpose

Search API is for **finding** companies, not **retrieving** data:
- Filter large datasets
- Pre-screen candidates
- Discovery workflows
- **Then** use Collect API for chosen companies

### Credit Optimization Reality

You **cannot** replace Collect credits with Search credits for assessment work. Instead:
1. ✅ Use Search API to pre-filter (cheap)
2. ✅ Manually review candidates (free)
3. ✅ Use Collect API for selected profiles (expensive but necessary)
4. ✅ Adjust enrichment scope (2015+ vs 2020+)
5. ✅ Toggle deep dive on/off strategically
6. ✅ Batch similar candidates for caching

---

## Files Generated by Testing

All test results saved to `/backend/`:

1. **Test Scripts:**
   - `test_search_vs_collect.py` - Complex multi-company test
   - `test_search_vs_collect_simple.py` - Focused single-company test ✓

2. **API Response Data:**
   - `search_api_result_Bexorg_Inc_20251022_210020.json` (14B)
   - `collect_api_result_Bexorg_Inc_20251022_210020.json` (94KB)

3. **Analysis Reports:**
   - `comparison_summary_Bexorg_Inc_20251022_210020.json` (1.6KB)

4. **Reference Data:**
   - `bexorg.json` (94KB) - Original file, identical to Collect API response

---

## Recommendations

### For Your LinkedIn Assessment App

1. **Keep Using Collect API** for all assessment work (no alternative)

2. **Optimize Credit Usage:**
   - Use Profile Search feature to pre-filter candidates
   - Adjust `min_year` based on budget (2015 vs 2020)
   - Toggle "Deep Dive" strategically
   - Batch candidates from similar companies

3. **Educate Users:**
   - Search feature finds candidates (cheap Search credits)
   - Assessment feature analyzes candidates (expensive Collect credits)
   - Workflow: Search → Review → Assess

4. **Monitor Credit Spend:**
   - Track credits per assessment (1-11 depending on deep dive)
   - Estimate monthly capacity
   - Prioritize high-value candidates for deep dive

### For Future Development

1. **Database Caching (Already Implemented):**
   - Store company data with 30-day freshness
   - Saves 1 Collect credit per cached company
   - Your app already does this! ✓

2. **Smart Enrichment:**
   - Only enrich companies where candidate worked 1+ year
   - Skip internships/short stints
   - Focus credits on meaningful experience

3. **Bulk Discounts:**
   - Consider higher-tier CoreSignal plans
   - More Collect credits = lower per-credit cost
   - Calculate breakeven based on usage

---

**Last Updated:** October 22, 2025
**Test Environment:** CoreSignal API v2
**Test Company:** Bexorg, Inc. (ID: 92819342)
