# CoreSignal Data Mismatch Report - URGENT

**Date:** October 22, 2025
**Issue:** Funding data available in Dashboard but returns `null` in Public API
**Priority:** HIGH - Blocking feature deployment
**Company Example:** Bexorg, Inc. (ID: 92819342)

---

## 🚨 THE PROBLEM

**Your web dashboard shows complete funding data for Bexorg.**
**Your public API returns `funding_rounds: null` for the same company.**

This is blocking our recruiting tool from assessing company growth stage and funding status.

---

## 📊 SIDE-BY-SIDE COMPARISON

### ✅ Dashboard Data (What We See)

**Endpoint Used:** `https://dashboard.coresignal.com/api/collect-record`

**Request Made:**
```bash
curl 'https://dashboard.coresignal.com/api/collect-record' \
  -H 'content-type: application/json' \
  --data-raw '{"api":"company","id":92819342,"csrfToken":"..."}'
```

**Response (Funding Section):**
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "website": "www.bexorg.com",
  "industry": "Biotechnology Research",
  "founded": 2021,

  "company_funding_rounds_collection": [
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
  ],

  "company_featured_investors_collection": [
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
  ],

  "company_crunchbase_info_collection": [
    {
      "id": 507309,
      "company_id": 92819342,
      "cb_url": "https://www.crunchbase.com/organization/bexorg-7142",
      "created": "2025-10-21 11:04:23",
      "last_updated": "2025-10-21 11:04:23",
      "deleted": 0
    }
  ]
}
```

**✅ FUNDING DATA AVAILABLE:**
- Series A round: **$23.0M**
- Date: **November 15, 2025**
- Investors: **1** (Engine Ventures)
- Crunchbase link: ✅ Available
- Total rounds: **1**

---

### ❌ Public API Data (What Our App Gets)

**Endpoint Used:** `https://api.coresignal.com/cdapi/v2/company_clean/collect/92819342`

**Request Made:**
```python
import requests

url = 'https://api.coresignal.com/cdapi/v2/company_clean/collect/92819342'
headers = {
    'accept': 'application/json',
    'apikey': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
}
response = requests.get(url, headers=headers)
data = response.json()
```

**Response (Funding Section):**
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "website": "www.bexorg.com",
  "industry": "Biotechnology Research",
  "founded": 2021,

  "funding_rounds": null
}
```

**❌ FUNDING DATA MISSING:**
- `funding_rounds`: **null**
- No `company_funding_rounds_collection` field
- No `company_featured_investors_collection` field
- No `company_crunchbase_info_collection` field
- No funding information whatsoever

---

## 🔍 DETAILED FIELD COMPARISON

| Field Name | Dashboard API | Public API | Status |
|------------|---------------|------------|--------|
| `company_funding_rounds_collection` | ✅ Array with 1 item | ❌ Field doesn't exist | **MISSING** |
| `funding_rounds` | N/A (doesn't use this field) | ❌ `null` | **NULL** |
| `last_round_type` | ✅ "Series A" | ❌ Not present | **MISSING** |
| `last_round_date` | ✅ "2025-11-15" | ❌ Not present | **MISSING** |
| `last_round_money_raised` | ✅ "US$ 23.0M" | ❌ Not present | **MISSING** |
| `last_round_investors_count` | ✅ 1 | ❌ Not present | **MISSING** |
| `total_rounds_count` | ✅ 1 | ❌ Not present | **MISSING** |
| `company_featured_investors_collection` | ✅ Engine Ventures | ❌ Field doesn't exist | **MISSING** |
| `company_crunchbase_info_collection` | ✅ Crunchbase URL | ❌ Field doesn't exist | **MISSING** |

---

## 🎯 WHAT WE NEED FROM CORESIGNAL

### Question 1: API Endpoint
**Is there a different public API endpoint that provides funding data?**

We tried:
- ❌ `/cdapi/v2/company_clean/collect/{id}` - Returns `funding_rounds: null`
- ✅ Dashboard `/api/collect-record` - Returns full data (but requires cookies, not API key)

### Question 2: Field Names
**What is the correct field name for funding data in the public API?**

Documentation says: `company_funding_rounds` (array)
Dashboard uses: `company_funding_rounds_collection` (array)
Public API has: `funding_rounds` (null)

### Question 3: Data Availability
**Is funding data available in our subscription tier?**

If yes → How do we access it programmatically?
If no → What tier do we need to upgrade to?

### Question 4: Authentication
**Does the dashboard API accept API key authentication?**

Currently dashboard requires session cookies (logged-in user).
Can we access `/api/collect-record` with our API key for programmatic access?

---

## 📝 OUR USE CASE

**Application:** LinkedIn Profile Assessor for Recruiters

**Why We Need Funding Data:**
1. Assess company growth stage (early-stage vs. established)
2. Evaluate company stability and runway
3. Help recruiters understand compensation context
4. Show investors and funding rounds to candidates

**Current Impact:**
- ❌ Company tooltips show "No funding data"
- ❌ Cannot assess startup vs. established company
- ❌ Missing critical company intelligence

**Example Companies Affected:**
- Bexorg, Inc. (ID: 92819342) - Series A, $23M (confirmed via dashboard)
- Many other startups showing `funding_rounds: null` in public API

---

## 🔬 TECHNICAL INVESTIGATION SUMMARY

### Tests Performed:

#### Test 1: Public API with API Key ✅
```python
GET https://api.coresignal.com/cdapi/v2/company_clean/collect/92819342
Headers: {'apikey': 'xxx'}
Result: 200 OK, but funding_rounds: null
```

#### Test 2: Dashboard API with API Key ❌
```python
POST https://dashboard.coresignal.com/api/collect-record
Headers: {'apikey': 'xxx'}
Body: {'api': 'company', 'id': 92819342}
Result: 200 OK, but returns HTML login page (not JSON)
```

#### Test 3: Documentation Review ✅
**According to:** https://docs.coresignal.com/company-data/clean-company-data/dictionary-clean-company-data

Field `company_funding_rounds` should contain:
```json
{
  "last_round_investors_count": Integer,
  "total_rounds_count": Integer,
  "last_round_type": String,
  "last_round_date": String (yyyy-mm-dd),
  "last_round_money_raised": Integer,
  "financial_website_url": String
}
```

**What we actually get:** `funding_rounds: null` (different field name, null value)

---

## 💰 SUBSCRIPTION DETAILS

**Our CoreSignal Account:**
- Account Email: [Your email]
- Plan: [Your plan name]
- API Key: [Redacted]

**Request:** Please review our account and confirm:
1. Does our plan include funding data access?
2. If yes, what endpoint/field should we use?
3. If no, what plan do we need?

---

## 🎯 REQUESTED ACTIONS

### Immediate (Priority 1):
1. **Clarify funding data availability** in public API
2. **Provide correct endpoint** or field name for programmatic access
3. **Confirm our subscription tier** includes funding data

### Short-term (Priority 2):
4. If not available, provide pricing for tier that includes funding data
5. Estimate timeline for API upgrade if needed
6. Confirm if dashboard API can accept API key authentication

---

## 📞 CONTACT INFORMATION

**Submitted by:** [Your name]
**Email:** [Your email]
**Company:** [Your company]
**Use case:** LinkedIn Profile Assessment Tool
**Date:** October 22, 2025
**Urgency:** High (blocking feature launch)

---

## 📎 ATTACHMENTS

1. **Dashboard Response Sample:** [See JSON above - company_funding_rounds_collection with Bexorg data]
2. **Public API Response Sample:** [See JSON above - funding_rounds: null]
3. **Test Scripts:** Available upon request
4. **Documentation References:**
   - https://docs.coresignal.com/company-data/clean-company-data/dictionary-clean-company-data
   - https://coresignal.com/alternative-data/company-funding-data/

---

## ✅ EXPECTED OUTCOME

**Ideal Resolution:**
- CoreSignal provides correct endpoint/field name for funding data
- We update our code to use correct field
- Funding data populates for all companies (where available)
- Feature deployment unblocked

**Alternative Resolution:**
- CoreSignal confirms funding data requires tier upgrade
- We evaluate cost vs. benefit of upgrade
- We implement alternative data source (Crunchbase) if needed

---

## 📊 APPENDIX: Full Dashboard Response

<details>
<summary>Click to expand - Full Bexorg company data from dashboard API</summary>

```json
{
  "id": 92819342,
  "url": "https://www.linkedin.com/company/bexorg-inc",
  "hash": "5d246c89db2a4607a7cea5ff96b2e9b4",
  "name": "Bexorg, Inc.",
  "website": "www.bexorg.com",
  "size": "11-50 employees",
  "industry": "Biotechnology Research",
  "description": "Bexorg is a privately held techbio company with the first-ever full tech stack platform to support CNS drug discovery and development in the human brain in a way that has not been possible before...",
  "followers": 1915,
  "founded": 2021,
  "headquarters_new_address": "New Haven, CT",
  "employees_count": 29,
  "type": "Privately Held",
  "logo_url": "https://media.licdn.com/dms/image/v2/D4E0BAQHy56N7hlFN2Q/company-logo_200_200/...",
  "created": "2023-05-15 17:51:53",
  "last_updated": "2025-10-21 11:04:23",
  "last_response_code": 200,

  "company_funding_rounds_collection": [
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
  ],

  "company_featured_investors_collection": [
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
  ],

  "company_crunchbase_info_collection": [
    {
      "id": 507309,
      "company_id": 92819342,
      "cb_url": "https://www.crunchbase.com/organization/bexorg-7142",
      "created": "2025-10-21 11:04:23",
      "last_updated": "2025-10-21 11:04:23",
      "deleted": 0
    }
  ]
}
```

</details>

---

**END OF REPORT**

*This document can be sent directly to CoreSignal support or used internally for investigation tracking.*
