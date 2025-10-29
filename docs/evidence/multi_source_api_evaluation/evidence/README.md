# Multi-Source Employee API: Evidence Package

**Date:** October 28, 2025
**Test Type:** Multi-Source Employee API Evaluation
**Profiles Tested:** 4 tech founders
**Total Companies Analyzed:** 27

---

## Purpose

This evidence package contains raw API responses and detailed field analysis from testing CoreSignal's multi-source employee API as a potential replacement for the current `employee_clean` + `company_base` enrichment flow.

**Evaluation Question:** Can multi-source provide embedded company data that eliminates the need for separate company API calls?

**Answer:** **NO** - Multi-source has critical data gaps (0% Crunchbase URLs, 0% company logos, null funding amounts) that make it unsuitable for the LinkedIn Profile Assessor application.

---

## Directory Structure

```
evidence/
├── README.md                                    # This file
├── EVIDENCE_INDEX.md                            # Master index of all evidence
├── test_summary.json                            # Aggregated test statistics
├── raw_responses/                               # Raw JSON responses from multi-source API
│   ├── dario_amodei_anthropic.json             # Dario Amodei (Anthropic CEO) - 12 companies
│   ├── aravind_srinivas_perplexity.json        # Aravind Srinivas (Perplexity CEO) - 6 companies
│   ├── ivan_zhao_notion.json                   # Ivan Zhao (Notion CEO) - 2 companies
│   └── dylan_field_figma.json                  # Dylan Field (Figma CEO) - 7 companies
└── field_analysis/                              # Detailed field-by-field analysis
    ├── dario_amodei_anthropic_analysis.md
    ├── aravind_srinivas_perplexity_analysis.md
    ├── ivan_zhao_notion_analysis.md
    └── dylan_field_figma_analysis.md
```

---

## Test Profiles

### 1. Dario Amodei (Anthropic CEO)
- **File:** [raw_responses/dario_amodei_anthropic.json](raw_responses/dario_amodei_anthropic.json)
- **Analysis:** [field_analysis/dario_amodei_anthropic_analysis.md](field_analysis/dario_amodei_anthropic_analysis.md)
- **LinkedIn:** https://www.linkedin.com/in/dario-amodei-3934934/
- **Companies:** 12 (Anthropic, OpenAI, Google, Baidu, Stanford, Princeton, etc.)
- **Key Findings:**
  - Funding date coverage: 6/12 (50.0%)
  - Crunchbase URLs: 0/12 (0.0%)
  - Company logos: 0/12 (0.0%)

### 2. Aravind Srinivas (Perplexity CEO)
- **File:** [raw_responses/aravind_srinivas_perplexity.json](raw_responses/aravind_srinivas_perplexity.json)
- **Analysis:** [field_analysis/aravind_srinivas_perplexity_analysis.md](field_analysis/aravind_srinivas_perplexity_analysis.md)
- **LinkedIn:** https://www.linkedin.com/in/aravind-srinivas-16051987/
- **Companies:** 6 (Perplexity, OpenAI, Google, DeepMind)
- **Key Findings:**
  - Funding date coverage: 4/6 (66.7%)
  - Crunchbase URLs: 0/6 (0.0%)
  - Company logos: 0/6 (0.0%)
  - **CRITICAL:** Perplexity funding date shows 2025-08-15 but amount is NULL

### 3. Ivan Zhao (Notion CEO)
- **File:** [raw_responses/ivan_zhao_notion.json](raw_responses/ivan_zhao_notion.json)
- **Analysis:** [field_analysis/ivan_zhao_notion_analysis.md](field_analysis/ivan_zhao_notion_analysis.md)
- **LinkedIn:** https://www.linkedin.com/in/ivanhzhao/
- **Companies:** 2 (Notion, Inkling)
- **Key Findings:**
  - Funding date coverage: 2/2 (100%)
  - Funding amount coverage: 1/2 (50%) - Inkling has $25M, Notion is NULL
  - Crunchbase URLs: 0/2 (0.0%)
  - Company logos: 0/2 (0.0%)

### 4. Dylan Field (Figma CEO)
- **File:** [raw_responses/dylan_field_figma.json](raw_responses/dylan_field_figma.json)
- **Analysis:** [field_analysis/dylan_field_figma_analysis.md](field_analysis/dylan_field_figma_analysis.md)
- **LinkedIn:** https://www.linkedin.com/in/dylanfield/
- **Companies:** 7 (Figma, Flipboard, LinkedIn, Microsoft, Indinero, O'Reilly)
- **Key Findings:**
  - Funding date coverage: 5/7 (71.4%)
  - Crunchbase URLs: 0/7 (0.0%)
  - Company logos: 0/7 (0.0%)

---

## Aggregated Statistics

**From:** [test_summary.json](test_summary.json)

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Profiles** | 4 | 100% |
| **Profiles Success** | 4 | 100% |
| **Profiles Failed** | 0 | 0% |
| **Total Companies** | 27 | - |
| **Companies with Funding Date** | 17 | 63.0% |
| **Companies with Funding Amount** | 1 | 3.7% ⚠️ |
| **Companies with Crunchbase URLs** | 0 | **0.0%** ❌ |
| **Companies with Logos** | 0 | **0.0%** ❌ |

---

## Critical Findings

### 1. Crunchbase URLs: 0% Coverage ❌

**Evidence:**
- Searched all 27 companies across 4 profiles
- Field name: `company_crunchbase_url`
- Result: **NULL in 100% of cases**

**Example from Aravind Srinivas (Perplexity):**
```json
{
  "company_name": "Perplexity",
  "company_crunchbase_url": null  // ❌ Always null
}
```

**Impact:** Your app relies on Crunchbase URLs for user verification (69.2% coverage in current flow). Multi-source provides 0%.

---

### 2. Company Logos: 0% Coverage ❌

**Evidence:**
- Searched all 27 companies across 4 profiles
- Field name: `company_logo_url`
- Result: **NULL in 100% of cases**

**Example from Dario Amodei (Anthropic):**
```json
{
  "company_name": "Anthropic",
  "company_logo_url": null  // ❌ Always null
}
```

**Impact:** Your `WorkExperienceCard.js` component requires logos for visual display. Multi-source cannot provide them.

---

### 3. Funding Amounts: Mostly NULL ⚠️

**Evidence:**
- 17/27 companies have `company_last_funding_round_date` (63%)
- 1/27 companies have `company_last_funding_round_amount_raised` (3.7%)
- **16 companies have funding date but NULL amount**

**Example from Aravind Srinivas (Perplexity):**
```json
{
  "company_name": "Perplexity",
  "company_last_funding_round_date": "2025-08-15",  // ✅ Date present
  "company_last_funding_round_amount_raised": null   // ❌ Amount NULL
}
```

**Example from Ivan Zhao (Inkling) - ONE company with amount:**
```json
{
  "company_name": "Inkling",
  "company_last_funding_round_date": "2016-12-13",       // ✅ Date present
  "company_last_funding_round_amount_raised": 25000000   // ✅ Amount present ($25M)
}
```

**Impact:** Your company tooltips display funding amounts ("$26M Series B"). Multi-source can only show dates without amounts in 94% of cases.

---

### 4. Skills Data: Missing ❌

**Evidence:**
- Field `skills` does not exist in multi-source API
- Alternative field: `inferred_skills` (present but different structure)

**Example from Aravind Srinivas:**
```json
{
  "skills": null,  // ❌ Not available
  "inferred_skills": [
    {
      "name": "Machine Learning",
      "inferred_from": "experience"
    }
  ]
}
```

**Impact:** Your AI assessment uses skills array for technical evaluation. Multi-source provides different data structure.

---

## Field-by-Field Comparison

### Employee-Level Fields

| Field | Multi-Source | Current Flow | Winner |
|-------|--------------|--------------|--------|
| `full_name` | ✅ 100% | ✅ 100% | Tie |
| `headline` | ✅ 100% | ✅ 100% | Tie |
| `location` | ⚠️ Partial | ⚠️ Partial | Tie |
| `summary` | ⚠️ 25% (1/4 profiles) | ❌ Missing | Multi-Source |
| `experience` (count) | ✅ 100% | ✅ 100% | Tie |
| `education` (count) | ✅ 100% | ✅ 100% | Tie |
| `skills` | ❌ Missing | ✅ 100% | Current Flow |
| `inferred_skills` | ✅ Present | ❌ N/A | Multi-Source |
| `certifications` | ✅ 100% | ✅ 100% | Tie |
| `awards` | ✅ Present | ❌ N/A | Multi-Source |
| `patents` | ✅ Present | ❌ N/A | Multi-Source |
| `publications` | ✅ Present | ❌ N/A | Multi-Source |

---

### Company-Level Fields (Embedded in Experiences)

| Field | Multi-Source | Current Flow | Winner |
|-------|--------------|--------------|--------|
| `company_name` | ✅ 100% (27/27) | ✅ 100% | Tie |
| `company_type` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| `company_founded_year` | ⚠️ 74% (20/27) | ✅ 100% | Current Flow |
| `company_size_range` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| `company_employees_count` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| `company_industry` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| `company_hq_full_address` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| **`company_last_funding_round_date`** | ⚠️ 63% (17/27) | ✅ 100% | Current Flow |
| **`company_last_funding_round_amount_raised`** | **❌ 3.7% (1/27)** | ✅ 100% | **Current Flow** |
| **`company_crunchbase_url`** | **❌ 0% (0/27)** | ✅ 69.2% | **Current Flow** |
| **`company_logo_url`** | **❌ 0% (0/27)** | ✅ 100% | **Current Flow** |
| `company_linkedin_url` | ✅ 93% (25/27) | ✅ 100% | Current Flow |
| `company_website` | ✅ 93% (25/27) | ✅ 100% | Current Flow |
| `company_stock_ticker` | ✅ 26% (7/27) | ✅ 30% | Tie |
| `company_annual_revenue` | ⚠️ 30% (8/27) | ✅ 50% | Current Flow |
| `company_is_b2b` | ✅ 96% (26/27) | ✅ 100% | Current Flow |
| `company_followers_count` | ✅ 96% (26/27) | ✅ 100% | Current Flow |

---

## How to Use This Evidence

### 1. Review Raw JSON Responses

**Location:** `raw_responses/`

Each file contains the complete multi-source API response for one profile. Use these to:
- Verify field names and data structures
- Check for any fields we may have missed
- Compare with your own test results
- Reference exact API response format

**Example:**
```bash
# Pretty-print a raw response
cat raw_responses/aravind_srinivas_perplexity.json | python3 -m json.tool | less
```

---

### 2. Read Field Analysis Documents

**Location:** `field_analysis/`

Each analysis document provides:
- Complete field breakdown for employee data
- Detailed company-by-company analysis
- Coverage statistics (funding, logos, Crunchbase)
- Critical findings highlighted

**Example:**
```bash
# Read Aravind Srinivas analysis
cat field_analysis/aravind_srinivas_perplexity_analysis.md
```

---

### 3. Compare with Current Flow

To see how multi-source compares with your current `company_base` data:

1. Check the Crunchbase URL field in multi-source: **Always null**
2. Check the logo field in multi-source: **Always null**
3. Check funding amounts in multi-source: **Mostly null**
4. Compare with your `FINAL_RECOMMENDATION.md` findings for company_base:
   - Crunchbase URLs: 69.2% coverage ✅
   - Logos: 100% coverage ✅
   - Funding amounts: 100% coverage ✅

**Conclusion:** Multi-source cannot match current flow data completeness.

---

### 4. Extract Specific Fields

Use the raw JSON files to extract any specific fields you need:

```bash
# Example: Extract all company names from Aravind's profile
cat raw_responses/aravind_srinivas_perplexity.json | \
  python3 -c "import json, sys; data = json.load(sys.stdin); \
  print('\n'.join([exp.get('company_name', 'N/A') for exp in data.get('experience', [])]))"
```

---

## Related Documentation

- **[../MULTI_SOURCE_EVALUATION.md](../MULTI_SOURCE_EVALUATION.md)** - Complete evaluation report with final recommendation
- **[../README.md](../README.md)** - Test methodology and usage instructions
- **[../../docs/technical-decisions/company-api-comparison-2024/](../../docs/technical-decisions/company-api-comparison-2024/)** - Previous company API comparison (company_base vs company_clean vs company_multi_source)
- **[../../docs/technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md](../../docs/technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md)** - Why search API can't replace collect API

---

## Key Takeaways

1. ❌ **0% Crunchbase URL coverage** - Dealbreaker for user verification workflow
2. ❌ **0% company logo coverage** - Dealbreaker for frontend UI requirements
3. ⚠️ **3.7% funding amount coverage** - 94% of companies have date but NULL amount
4. ❌ **Missing skills data** - Different structure (`inferred_skills` vs `skills` array)
5. ✅ **63% funding date coverage** - Better than nothing, but incomplete without amounts
6. ⚠️ **Lower data completeness** - 26.7% vs 50.0% for current flow

**Final Verdict:** Multi-source is **not viable** as a replacement for current flow.

---

**Evidence Collection Date:** October 28, 2025
**API Version:** CoreSignal v2 Multi-Source Employee API
**Endpoint:** `/v2/employee_multi_source/collect/{shorthand}`
**Cost:** 2 Collect credits per profile
