# CoreSignal API: Search vs Collect - Quick Reference

> **TL;DR:** Search API returns IDs only (14 bytes). Collect API returns full company profiles (94KB+). You MUST use Collect API to get bexorg.json-level data.

---

## At a Glance

| Feature | Search API | Collect API |
|---------|-----------|-------------|
| **What you get** | Company ID (integer) | Complete company profile |
| **Response size** | 14 bytes | 94KB+ |
| **Company name** | ❌ | ✅ |
| **Funding data** | ❌ | ✅ Series A, $23M, investors |
| **Employee list** | ❌ | ✅ 17 LinkedIn URLs |
| **Investors** | ❌ | ✅ Engine Ventures + CrunchBase |
| **Similar companies** | ❌ | ✅ 71 companies |
| **Company updates** | ❌ | ✅ 73 posts |
| **Top-level fields** | 0 | 45 |
| **Collections** | 0 | 11 |
| **Cost** | 1 Search credit | 1 Collect credit |
| **Credit ratio** | 2x cheaper | Baseline |
| **Use case** | **Finding** companies | **Retrieving** full data |

---

## Test Results Summary

### Bexorg, Inc. Test (Company ID: 92819342)

**Search API Response:**
```json
[92819342]
```
- Size: **14 bytes**
- Fields: **0**
- Collections: **0**

**Collect API Response:**
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
      ...
    }
  ],
  ... (45 fields + 11 collections)
}
```
- Size: **94KB**
- Fields: **45**
- Collections: **11** (funding, investors, employees, similar companies, etc.)

**Size Difference:** Collect API returns **6,714x more data**

---

## The Answer to Your Question

### ❓ Can we retrieve bexorg.json-level company information using Search credits?

### ❌ NO.

**Why:**
- Search API returns company IDs only
- No company name, funding, employees, or any details
- bexorg.json has 94KB of rich data
- Only Collect API provides complete profiles

**Proof:**
```bash
search_api_result_Bexorg_Inc_20251022_210020.json    # 14 bytes  ❌
collect_api_result_Bexorg_Inc_20251022_210020.json   # 94KB     ✅
bexorg.json                                          # 94KB     ✅ (Identical)
```

---

## What Collect API Gives You (That Search API Doesn't)

### 1. Funding Intelligence
```
✅ Round type: "Series A"
✅ Amount: "US$ 23.0M"
✅ Date: "2025-11-15"
✅ Investors: "Engine Ventures"
✅ Total rounds: 1
✅ CrunchBase URL: https://www.crunchbase.com/funding_round/...
```

### 2. Employee Network
```
✅ 17 featured employee LinkedIn URLs
✅ Network mapping capabilities
✅ Team quality assessment
```

### 3. Market Intelligence
```
✅ 71 similar companies
✅ 73 company updates/posts
✅ Competitive landscape
```

### 4. Company Details
```
✅ Name: "Bexorg, Inc."
✅ Industry: "Biotechnology Research"
✅ Founded: 2021
✅ Employees: 29
✅ Size: "11-50 employees"
✅ Location: "New Haven, CT"
✅ Type: "Privately Held"
```

### 5. Digital Presence
```
✅ Website
✅ Logo URL
✅ LinkedIn URL
✅ CrunchBase company page
```

---

## Why Search Credits Are Cheaper (2x vs Collect)

**Simple Math:**
- Search API returns: 14 bytes (just ID)
- Collect API returns: 94,000 bytes (full profile)
- **Ratio:** 1 : 6,714

**CoreSignal's Logic:**
- Search credits (2x quantity) = Finding companies
- Collect credits (baseline) = Getting actual data
- **Fair pricing** based on data volume

---

## Correct Usage Pattern

### ✅ Use Search API to FIND

```
1. Search for "Series A biotech in New England"
   → Returns: [12345, 67890, 11223, ...] (100 company IDs)
   → Cost: 100 Search credits (you have 200)

2. Download CSV with LinkedIn URLs

3. Manually review profiles (FREE!)

4. Select top 10 companies

5. Use Collect API for those 10
   → Returns: Full company profiles
   → Cost: 10 Collect credits
```

**Total:** 100 Search + 10 Collect = Efficient!

### ❌ Don't Use Search API to ASSESS

```
❌ Search API response: [92819342]
❌ Can't assess without company name
❌ Can't evaluate without funding data
❌ Can't analyze without employee info
❌ Useless for AI assessment
```

---

## Your App's Current (Correct) Implementation

### Single Profile Assessment
```
1. User submits LinkedIn URL
2. Collect employee profile (1 Collect credit)
3. Collect 10 company profiles (10 Collect credits)
4. AI assessment with FULL context
5. Professional-grade evaluation

Total: 11 Collect credits
Quality: ✅ Excellent
```

### Profile Search Feature
```
1. User: "Find ML engineers at Series A startups"
2. Search API: 50 employee IDs (50 Search credits) ✅
3. Download CSV: LinkedIn URLs
4. User reviews: Manual filtering (FREE)
5. Batch assess: 10 selected candidates
6. Collect API: 10 × 11 = 110 Collect credits

Savings: Filtered 50 → 10 before using Collect!
```

---

## Credit Optimization Strategies

### 1. ✅ Profile Search (Already Using!)
- Search finds 100 candidates (cheap Search credits)
- Manually review (free)
- Assess top 10 (expensive Collect credits)
- **Savings:** 90% reduction in Collect usage

### 2. ✅ Adjust Year Filter
```python
# app.py line 826
min_year=2015  →  ~10 companies  →  11 Collect credits
min_year=2018  →  ~7 companies   →  8 Collect credits
min_year=2020  →  ~4 companies   →  5 Collect credits
```

### 3. ✅ Toggle Deep Dive
```
☐ Deep Dive OFF: 1 Collect credit (screening)
☑️ Deep Dive ON:  11 Collect credits (final candidates)

Strategy: Screen 40 without, deep dive on 10 finalists
Savings: 40×1 + 10×11 = 150 (vs 550 if all deep)
```

### 4. ✅ Batch Caching (Already Implemented!)
```
5 candidates from Google:
- 1st: Fetch Google (1 credit)
- 2nd-5th: Cache hit (0 credits each)
Savings: 4 credits per batch
```

---

## Testing Files

All files in `/backend/`:

**Test Scripts:**
- ✅ `test_search_vs_collect_simple.py` - Run the test yourself

**API Responses:**
- ✅ `search_api_result_Bexorg_Inc_20251022_210020.json` (14B)
- ✅ `collect_api_result_Bexorg_Inc_20251022_210020.json` (94KB)

**Analysis:**
- ✅ `comparison_summary_Bexorg_Inc_20251022_210020.json`

**Documentation:**
- ✅ `CORESIGNAL_SEARCH_VS_COLLECT_API_COMPLETE_ANALYSIS.md` (Full details)
- ✅ `SEARCH_VS_COLLECT_QUICK_REFERENCE.md` (This file)

---

## Run the Test Yourself

```bash
cd backend
export CORESIGNAL_API_KEY="your_key"
python3 test_search_vs_collect_simple.py
```

**Output:**
```
Search API: [92819342]                    # 14 bytes
Collect API: {complete company profile}   # 94KB

Results saved to:
- search_api_result_*.json
- collect_api_result_*.json
- comparison_summary_*.json
```

---

## Bottom Line

| Question | Answer |
|----------|--------|
| Can Search API give me bexorg.json-level data? | ❌ **NO** |
| What does Search API return? | Company ID only (14 bytes) |
| What does Collect API return? | Complete profile (94KB) |
| Must I use Collect API for assessment? | ✅ **YES** |
| Why are Search credits cheaper (2x)? | They return 6,714x less data |
| How do I save Collect credits? | Use Search to pre-filter, then Collect chosen companies |
| Is my app using the right APIs? | ✅ **YES** (Collect for assessment, Search for discovery) |

---

**Your bexorg.json was created using Collect API. There is no way to get that level of data using Search credits.**

---

**Generated:** October 22, 2025
**Test Data:** Bexorg, Inc. (ID: 92819342)
**Verification:** ✅ Tested with live API calls
