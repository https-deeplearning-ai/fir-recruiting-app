# Why We Can't Use CoreSignal Search API (Instead of Collect API)

## TL;DR - The Problem

**CoreSignal's `/preview` Search API endpoints return INCOMPLETE data** that cannot be used for proper candidate assessment. We must use Collect API for full profile data.

---

## The Failed Optimization Attempt

### What We Tried to Do

Since CoreSignal gives you **2x more Search credits than Collect credits** (e.g., 100 Collect + 200 Search for the same price), I attempted to optimize the app to use Search API exclusively to save expensive Collect credits.

**The goal was:**
- Replace employee profile Collect API → Search API (save 1 Collect credit per profile)
- Replace company enrichment Collect API → Search API (save N Collect credits for N companies)
- **Net result:** Assess 2x more candidates with the same plan!

### The Implementation

I modified two methods in `coresignal_service.py`:

1. **Employee Profile Fetching:**
   - Changed from: `/v2/employee_clean/collect/{shorthand}`
   - To: `/v2/employee_clean/search/es_dsl/preview`
   - Expected to extract `member_data` field with full profile

2. **Company Enrichment:**
   - Changed from: `/v2/company_clean/collect/{company_id}`
   - To: `/v2/company_clean/search/es_dsl/preview`
   - Expected to extract `company_data` field with full company details

---

## Why It Doesn't Work

### CoreSignal's Official Documentation

According to CoreSignal's API documentation, the `/preview` endpoints:

> **"Retrieve a small set of PARTIAL data using Elasticsearch queries"**

This is the critical issue: **PARTIAL DATA**.

### What "Partial Data" Means

The Search API `/preview` endpoints are designed for **filtering and discovery**, NOT for full data retrieval. They return:

❌ **Incomplete work experience** (missing job descriptions, dates, responsibilities)
❌ **Missing education details**
❌ **Truncated skills lists**
❌ **Limited company information** (missing funding, growth metrics, employee counts)
❌ **Abbreviated fields** that the AI needs for proper assessment

### The Fundamental Trade-off

CoreSignal's API design intentionally separates two use cases:

| Use Case | API Type | Credits | Data Completeness |
|----------|----------|---------|-------------------|
| **Discovery/Filtering** | Search API | Cheaper (2x credits) | ⚠️ Partial/Preview only |
| **Full Data Retrieval** | Collect API | Expensive (1x credits) | ✅ Complete profile |

**This is by design** - CoreSignal wants you to:
1. Use cheap Search credits to FIND candidates
2. Use expensive Collect credits to GET full data for chosen candidates

### Real-World Impact

If we used Search API with partial data, the AI assessment would:
- **Miss critical job experience details** needed to evaluate fit
- **Lack company context** for understanding career progression
- **Have incomplete skills data** for technical assessment
- **Produce low-quality, inaccurate assessments** that hurt recruiting decisions

---

## The Correct API Architecture

### Search API Use Case (What It's Actually For)

The Search API is perfect for the **Profile Search feature** your app already has:

```
User Query: "Find Series A founders in San Francisco with AI/ML background"
                        ↓
            Search API returns 100 candidate IDs
                        ↓
        Download CSV with LinkedIn URLs
                        ↓
    User manually reviews and selects 10 promising candidates
                        ↓
    Upload those 10 URLs to Batch Assessment (uses Collect API)
                        ↓
            Full, accurate AI assessments
```

**Credit Usage:**
- Search: 100 Search credits (to find candidates)
- Collect: 10 × 11 = 110 Collect credits (for final assessments)
- **Net benefit:** You filtered 100 candidates down to 10 before using expensive Collect credits!

### Collect API Use Case (What We Must Use)

The Collect API is necessary for:
- **Single Profile Assessment** - Need full data for AI analysis
- **Batch Processing** - Need full data for all candidates in CSV
- **Company Deep Dive** - Need complete company intelligence for tooltips

**There is no workaround** - if you want quality assessments, you need complete data from Collect API.

---

## Credit Optimization Strategies That DO Work

Since we can't replace Collect with Search, here are real ways to save credits:

### 1. Use Profile Search to Pre-Filter (Already Implemented!)

Instead of assessing every candidate you find:
- Use Search API to find 50-100 candidates (cheap Search credits)
- Manually review LinkedIn profiles (free!)
- Only assess top 10-20 with Collect API (expensive credits)
- **Savings:** 80% reduction in Collect credit usage

### 2. Adjust Company Enrichment Year Filter

Currently set to `min_year=2015` in `app.py` line 826:

```python
enrichment_result = coresignal_service.enrich_profile_with_company_data(profile_data, min_year=2015)
```

**Options:**
- `min_year=2015` → Enriches ~10 companies per profile (11 Collect credits total)
- `min_year=2018` → Enriches ~7 companies per profile (8 Collect credits total)
- `min_year=2020` → Enriches ~4 companies per profile (5 Collect credits total)

**Trade-off:** Less company intelligence vs. more profiles assessed per month

### 3. Toggle Company Enrichment Off

Your app has a "Deep Dive Company Research" checkbox. When unchecked:
- Employee profile: 1 Collect credit
- Company enrichment: 0 Collect credits
- **Total:** 1 Collect credit per assessment (instead of 11!)

Use this for:
- Initial screening of large candidate pools
- Situations where company context isn't critical
- When you're running low on Collect credits

**Re-enable for final candidates** to get full company intelligence tooltips.

### 4. Batch Processing for Efficiency

The batch processing feature uses caching:
- First company fetch: 1 Collect credit
- Same company again: 0 credits (served from cache)

**Example:** Assessing 5 candidates from Google:
- Without caching: 5 × (1 employee + 10 companies) = 55 credits
- With caching: 5 × 1 employee + 10 unique companies = 15 credits
- **Savings:** 40 Collect credits!

**Best practice:** Batch process candidates from similar companies/industries.

---

## Current Implementation (Correct)

Your app now uses **Collect API exclusively** as it should:

**Employee Profile:**
- Endpoint: `/v2/employee_clean/collect/{shorthand}`
- Cost: 1 Collect credit
- Returns: Complete profile with full work history, education, skills

**Company Enrichment:**
- Endpoint: `/v2/company_clean/collect/{company_id}`
- Cost: 1 Collect credit per company
- Returns: Complete company data with funding, growth, employees

**Total per assessment:** ~11 Collect credits (1 employee + 10 companies)

This is the **only way** to get quality AI assessments.

---

## Bottom Line

❌ **Can't use Search API for assessment** - Returns partial/incomplete data
✅ **Must use Collect API for assessment** - Returns complete data needed for AI
✅ **Use Search API for discovery only** - Pre-filter before assessing
✅ **Optimize credits through filtering, caching, and smart year limits**

The 2x Search credit advantage is **for finding candidates**, not assessing them.
