# CoreSignal Company Enrichment APIs - CRITICAL DISCOVERY

**Date:** October 22, 2025
**Issue:** Funding data missing from public API but present in Dashboard API

---

## 🚨 CRITICAL FINDING

**There are TWO different CoreSignal Company APIs with DIFFERENT data:**

### 1. Public API Endpoint (Currently Used)
**Endpoint:** `https://api.coresignal.com/cdapi/v2/company_clean/collect/{company_id}`

**Authentication:**
```python
headers = {
    'accept': 'application/json',
    'apikey': CORESIGNAL_API_KEY,
    'Content-Type': 'application/json'
}
```

**Data Structure:**
- Returns ~60 fields
- `funding_rounds` field exists but is **NULL** for many companies
- Missing rich funding data

**Example Response for Bexorg (ID: 92819342):**
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "funding_rounds": null,  // ❌ NULL
  ...
}
```

---

### 2. Dashboard API Endpoint (Discovered by User)
**Endpoint:** `https://dashboard.coresignal.com/api/collect-record`

**Authentication:**
- Requires dashboard session cookies (logged-in state)
- Uses CSRF token
- Cookie-based authentication

**Request Body:**
```json
{
  "api": "company",
  "id": 92819342,
  "csrfToken": "..."
}
```

**Data Structure:**
- Returns **MUCH MORE** data
- Has `company_funding_rounds_collection` array with detailed funding data
- Has `company_featured_investors_collection` with investor details
- Has `company_crunchbase_info_collection` with Crunchbase links

**Example Response for Bexorg (ID: 92819342):**
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "company_funding_rounds_collection": [
    {
      "id": 12429636,
      "last_round_investors_count": 1,
      "total_rounds_count": 1,
      "last_round_type": "Series A",
      "last_round_date": "2025-11-15 00:00:00",
      "last_round_money_raised": "US$ 23.0M",
      "cb_url": "https://www.crunchbase.com/funding_round/bexorg-7142-series-a--c467c0f3",
      ...
    }
  ],
  "company_featured_investors_collection": [
    {
      "company_investors_list": {
        "id": 33813,
        "name": "Engine Ventures",
        "hash": "85202ec52aa41c2ad218941631580326",
        "cb_url": "https://www.crunchbase.com/organization/engine-ventures",
        ...
      }
    }
  ],
  "company_crunchbase_info_collection": [
    {
      "id": 507309,
      "company_id": 92819342,
      "cb_url": "https://www.crunchbase.com/organization/bexorg-7142",
      ...
    }
  ]
}
```

---

## 📊 Data Comparison: Bexorg Example

| Field | Public API | Dashboard API |
|-------|-----------|---------------|
| **Funding Rounds** | `null` ❌ | Series A, $23M ✅ |
| **Investors** | Not present | Engine Ventures ✅ |
| **Crunchbase Link** | Not present | Full URL ✅ |
| **Funding Date** | Not present | Nov 15, 2025 ✅ |
| **Total Rounds** | Not present | 1 round ✅ |

---

## 🔑 Key Questions

### 1. Can we access the Dashboard API with our API key?
**Status:** Unknown - needs testing

**Hypothesis:** Dashboard API may require:
- Different authentication method
- Higher-tier subscription
- Dashboard-specific credentials

### 2. Is the Dashboard API documented?
**Status:** Unknown - not in our current API docs

**Need to check:**
- Official CoreSignal API documentation
- Support/sales contact for access
- Alternative authentication methods

### 3. Can we use the public API differently?
**Possible approaches:**
- Check if there's a query parameter to request full data
- Look for alternate endpoints in the `/cdapi/` namespace
- Check if there's a "premium" data flag

---

## 🛠️ Immediate Action Items

### Option A: Try Dashboard API with API Key
Test if dashboard endpoint accepts `apikey` header instead of cookies:

```python
url = 'https://dashboard.coresignal.com/api/collect-record'
headers = {
    'accept': 'application/json',
    'apikey': CORESIGNAL_API_KEY,
    'Content-Type': 'application/json'
}
payload = {
    'api': 'company',
    'id': 92819342
}
response = requests.post(url, headers=headers, json=payload)
```

### Option B: Contact CoreSignal Support
- Ask about funding data availability in public API
- Request documentation for dashboard API
- Check if our subscription tier includes funding data

### Option C: Parse Dashboard Manually
- If dashboard API not accessible via API key
- User could manually export company data from dashboard
- Import as supplementary data source

---

## 📝 Current Implementation Status

**Our App Currently:**
1. ✅ Uses public API `/cdapi/v2/company_clean/collect/`
2. ✅ Stores ALL 60 fields in `raw_data`
3. ✅ Properly extracts logo, website, LinkedIn URL
4. ❌ Gets `null` for `funding_rounds` on many companies

**Dashboard API Would Give Us:**
1. ✅ Full funding history
2. ✅ Investor names and Crunchbase links
3. ✅ Total rounds count
4. ✅ Money raised per round
5. ✅ Round types (Seed, Series A, etc.)
6. ✅ Round dates

---

## 🎯 Recommendation

**PRIORITY 1:** Test if dashboard API accepts our API key (see Option A above)

**PRIORITY 2:** If that fails, contact CoreSignal support:
> "Hi CoreSignal team,
>
> We're using the `/cdapi/v2/company_clean/collect/` endpoint and noticed that `funding_rounds` returns `null` for many companies.
>
> However, your dashboard shows rich funding data (rounds, investors, amounts) for the same companies.
>
> Question: Is there an API endpoint that provides the same funding data shown in the dashboard? We have API access and would like to programmatically access funding information.
>
> Company example: Bexorg (ID: 92819342) shows Series A $23M in dashboard but `null` via API."

**PRIORITY 3:** Document findings and update codebase once we know the answer

---

## 🔗 Related Files

- [coresignal_service.py](backend/coresignal_service.py) - Current API implementation
- [COMPANY_DATA_VERIFICATION.md](COMPANY_DATA_VERIFICATION.md) - Bexorg data investigation
- [CLAUDE.md](CLAUDE.md) - Project overview

---

**Status:** Investigation in progress
**Next Step:** Test dashboard API with API key authentication
