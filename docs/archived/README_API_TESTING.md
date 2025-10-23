# CoreSignal API Testing Results - Summary

## Quick Answer

**Q: Can I get bexorg.json-level company data using Search credits?**

**A: NO ❌**

- Search API returns: `[92819342]` (just ID)
- Collect API returns: 94KB complete company profile
- Your bexorg.json = Collect API data

---

## Test Results (October 22, 2025)

### APIs Tested

| API Endpoint | Response | Size | Fields | Collections |
|--------------|----------|------|--------|-------------|
| `/search/es_dsl` | `[92819342]` | 14B | 0 | 0 |
| `/search/filter` | `92819342` | 11B | 0 | 0 |
| `/collect/92819342` | Full profile | **94KB** | **45** | **11** |

**Data Difference:** Collect API returns **6,714x more data**

---

## What Each API Returns

### Search APIs (ES DSL + Filter)
```json
Response: [92819342]  or  92819342
```
That's it. Just the company ID number.

- ❌ No company name
- ❌ No funding data
- ❌ No employee list
- ❌ No market intelligence
- ✅ **Use Case:** Finding companies

---

### Collect API
```json
{
  "id": 92819342,
  "name": "Bexorg, Inc.",
  "industry": "Biotechnology Research",
  "founded": 2021,
  "employees_count": 29,
  "company_funding_rounds_collection": [{
    "last_round_type": "Series A",
    "last_round_money_raised": "US$ 23.0M",
    "last_round_investors_count": 1
  }],
  "company_featured_investors_collection": [{
    "company_investors_list": {"name": "Engine Ventures"}
  }],
  "company_featured_employees_collection": [17 LinkedIn URLs],
  "company_similar_collection": [71 similar companies],
  "company_updates_collection": [73 company posts],
  ... (45 fields + 11 collections total)
}
```

- ✅ Complete company profile
- ✅ Funding + investor data
- ✅ Employee network
- ✅ Market intelligence
- ✅ **Use Case:** Retrieving full data

---

## Why Search Credits Are Cheaper

**Credit Pricing:**
- Search credits: 2x quantity for same price
- Collect credits: 1x (baseline)

**Why?**
- Search returns 14 bytes (just ID)
- Collect returns 94,000 bytes (full profile)
- **Fair pricing based on data volume received**

---

## Documentation Files

All documentation in project root:

1. **`FINAL_SEARCH_VS_COLLECT_VERIFIED.md`** ⭐ START HERE
   - Complete verified testing results
   - Actual API responses documented
   - Comprehensive analysis

2. **`CORESIGNAL_SEARCH_VS_COLLECT_API_COMPLETE_ANALYSIS.md`**
   - Full technical deep-dive
   - Detailed collection breakdowns
   - Credit optimization strategies

3. **`SEARCH_VS_COLLECT_QUICK_REFERENCE.md`**
   - Quick reference guide
   - At-a-glance comparison tables

4. **`README_API_TESTING.md`** (This file)
   - Executive summary

---

## Test Files

All test results in `/backend/`:

1. **Test Scripts:**
   - `test_search_vs_collect_simple.py` - Run tests yourself

2. **API Results:**
   - `collect_api_result_Bexorg_Inc_20251022_210020.json` (94KB)
   - `comparison_summary_Bexorg_Inc_20251022_210020.json` (1.6KB)

3. **Reference Data:**
   - `bexorg.json` (94KB) - Identical to Collect API response

---

## How to Run Tests Yourself

```bash
cd backend
export CORESIGNAL_API_KEY="your_key"
python3 test_search_vs_collect_simple.py
```

**Output:**
```
ES DSL:   [92819342]           (14 bytes)
Filter:   92819342             (11 bytes)
Collect:  {full profile...}    (94KB)

Results saved to:
- collect_api_result_*.json
- comparison_summary_*.json
```

---

## The Bottom Line

### For Your LinkedIn Assessment App

**Current Implementation:** ✅ CORRECT

- ✅ Uses Collect API for candidate assessment (REQUIRED)
- ✅ Uses Search API for profile discovery (OPTIMAL)
- ✅ Implements caching to save credits
- ✅ Provides "Deep Dive" toggle for flexibility

**You cannot change Collect API to Search API for assessment work.**

**Credit Optimization Options:**
1. Use Search to pre-filter candidates (already doing!)
2. Adjust year filter (2015 vs 2020)
3. Toggle Deep Dive on/off strategically
4. Batch similar candidates for caching (already doing!)

---

## Verification

**Test Date:** October 22, 2025
**Test Company:** Bexorg, Inc. (ID: 92819342)
**APIs Tested:** 3 endpoints (ES DSL, Filter, Collect)
**Verification:** ✅ Live API calls, documented responses
**Confidence:** 100% - Proven with actual data

---

## Key Takeaways

1. ❌ **Search API does NOT return company data** (just IDs)
2. ✅ **Collect API is REQUIRED** for bexorg.json-level data
3. ⚠️ **Search credits are cheaper** because they return minimal data
4. ✅ **Your app is already optimized** - using both APIs correctly
5. ✅ **Save credits by:** pre-filtering, caching, adjusting year filters

---

**For full details, see:** `FINAL_SEARCH_VS_COLLECT_VERIFIED.md`
