# Credit Optimization: All Tiers Now Free

**Date:** November 10, 2025
**Change:** Fixed Tier 4 to use `/preview` instead of `/collect`
**Impact:** ID lookup phase is now **100% FREE (0 credits)**

---

## 🎯 **What Changed**

### Before (Tier 4 was wasteful):
```python
# Tier 4: company_clean fallback
search_url = "/cdapi/v2/company_clean/search/es_dsl"  # Returns IDs
response = requests.post(search_url, ...)
company_ids = response.json()

# Then /collect to get name for validation
collect_url = f"/cdapi/v2/company_clean/collect/{company_ids[0]}"
response = requests.get(collect_url, ...)  # ← WASTES 1 CREDIT! ❌
company_data = response.json()
```

### After (Tier 4 optimized):
```python
# Tier 4: company_clean fallback
search_url = "/cdapi/v2/company_clean/search/es_dsl/preview"  # Returns full basic data
response = requests.post(search_url, ...)
companies = response.json()  # ← 0 CREDITS! ✅

# Already has ID + name for validation (no /collect needed)
company_id = companies[0]['id']
company_name = companies[0]['name']
```

---

## 💰 **Credit Breakdown**

### All Four Tiers:

| Tier | Endpoint | Before | After | Savings |
|------|----------|--------|-------|---------|
| **1** | `/filter?exact_website` | 0 | 0 | - |
| **2** | `/preview?page=N` | 0 | 0 | - |
| **3** | `/preview` | 0 | 0 | - |
| **4** | `/company_clean/preview` | **1** ❌ | **0** ✅ | 1 credit/lookup |

**Total ID Lookup Cost:** **0 CREDITS** (100% FREE!)

---

## 🎯 **Why This Matters**

### ID Lookup vs. Research (Separation of Concerns)

**Phase 1: ID Lookup (This Work)** ← FREE
- Get CoreSignal company IDs
- Uses `/preview` endpoints (0 credits)
- Returns: ID + basic fields (name, website, location)
- Purpose: Match company names to database IDs

**Phase 2: Research (Future Agent)** ← PAID
- Collect full company data: `/company_base/collect/{id}` (1 credit)
- Search employees at companies (credits based on search)
- Purpose: Actually research the companies

**Key Benefit:** ID lookup is exploratory/matching phase (free), research phase is when you commit credits (paid).

---

## 📊 **Impact on Research Pipeline**

### Scenario: Discovering 100 companies

**Before (with Tier 4 waste):**
```
100 companies discovered
↓ (ID lookup)
85 IDs found:
  - 80 via Tiers 1-3 (0 credits)
  - 5 via Tier 4 (5 credits wasted!) ❌
↓ (Research)
85 companies researched (85 credits for /collect)
---
Total: 90 credits (5 wasted on ID lookup)
```

**After (all tiers free):**
```
100 companies discovered
↓ (ID lookup)
85 IDs found:
  - 80 via Tiers 1-3 (0 credits)
  - 5 via Tier 4 (0 credits!) ✅
↓ (Research)
85 companies researched (85 credits for /collect)
---
Total: 85 credits (0 wasted!)
```

**Savings:** 5 credits per 100 companies (Tier 4 triggers ~5% of time)

---

## ✅ **What Was Fixed**

**File:** `backend/coresignal_company_lookup.py` (lines 181-286)

**Changes:**
1. Changed endpoint: `/search/es_dsl` → `/search/es_dsl/preview`
2. Response format: `company_ids` → `companies` (full objects with basic fields)
3. Removed `/collect` call (was only used for name validation)
4. Name validation now uses data from `/preview` response

**Result:** Same functionality, 0 credits instead of 1

---

## 🧪 **Test Results**

```bash
python3 backend/test_heuristic_filter.py

✅ Deepgram: FOUND (Tier 1)
✅ AssemblyAI: FOUND (Tier 1)
✅ Krisp: FOUND (Tier 2)
✅ Text API: FOUND (Tier 3)
❌ Google Cloud Speech: NO MATCH (product name)

Match Rate: 4/5 (80%)
Credits Used: 0 ✅
```

**Tier 4 Status:**
- Attempted for "Google Cloud Speech" (correctly found no match)
- Would trigger for ~3-5% of lookups
- Now uses 0 credits when it does trigger

---

## 📁 **Files Modified**

1. **`backend/coresignal_company_lookup.py`** (lines 181-286)
   - Fixed Tier 4 to use `/preview`
   - Added note about credit optimization

2. **`HANDOFF_CORESIGNAL_ID_LOOKUP_INTEGRATION.md`**
   - Updated credit usage tables
   - Clarified ID lookup vs. research phases
   - Added "Don't call /collect during lookup!" warning

3. **`CREDIT_OPTIMIZATION_SUMMARY.md`** (this file)
   - Documents the optimization

---

## 🎯 **Bottom Line**

**ID Lookup Phase:** 100% FREE (0 credits)
- All 4 tiers optimized
- Returns company IDs for future research
- No full data collection during lookup

**Research Phase:** Future agent decides when to spend credits
- `/collect` for full company data (1 credit/company)
- Employee search (credits based on search)
- Full control over credit usage

**Key Benefit:** Separation of concerns = better credit control! ✅
