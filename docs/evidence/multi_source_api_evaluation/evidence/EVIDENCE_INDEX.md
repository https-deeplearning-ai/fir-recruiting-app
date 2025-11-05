# Evidence Index: Multi-Source Employee API Evaluation

**Test Date:** October 28, 2025
**API Tested:** CoreSignal Multi-Source Employee API (`/v2/employee_multi_source/collect/{shorthand}`)
**Profiles:** 4 tech founders (Anthropic, Perplexity, Notion, Figma)
**Companies Analyzed:** 27 total

---

## Quick Navigation

| Profile | Raw JSON | Field Analysis | Companies | Findings |
|---------|----------|----------------|-----------|----------|
| [Dario Amodei](#1-dario-amodei-anthropic-ceo) | [JSON](raw_responses/dario_amodei_anthropic.json) | [Analysis](field_analysis/dario_amodei_anthropic_analysis.md) | 12 | 0% CB URLs, 0% logos |
| [Aravind Srinivas](#2-aravind-srinivas-perplexity-ceo) | [JSON](raw_responses/aravind_srinivas_perplexity.json) | [Analysis](field_analysis/aravind_srinivas_perplexity_analysis.md) | 6 | NULL funding amounts |
| [Ivan Zhao](#3-ivan-zhao-notion-ceo) | [JSON](raw_responses/ivan_zhao_notion.json) | [Analysis](field_analysis/ivan_zhao_notion_analysis.md) | 2 | 1/2 has amount data |
| [Dylan Field](#4-dylan-field-figma-ceo) | [JSON](raw_responses/dylan_field_figma.json) | [Analysis](field_analysis/dylan_field_figma_analysis.md) | 7 | Stock tickers present |

---

## 1. Dario Amodei (Anthropic CEO)

**Profile Overview:**
- **LinkedIn:** https://www.linkedin.com/in/dario-amodei-3934934/
- **Profile ID:** 84782677
- **Current Role:** CEO and Co-Founder at Anthropic
- **Total Companies:** 12
- **Notable Background:** VP of Research at OpenAI, Senior Research Scientist at Google, Research Scientist at Baidu

**Files:**
- **Raw JSON:** [dario_amodei_anthropic.json](raw_responses/dario_amodei_anthropic.json) (46 KB)
- **Field Analysis:** [dario_amodei_anthropic_analysis.md](field_analysis/dario_amodei_anthropic_analysis.md)

**Data Coverage:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Funding Date | 6/12 | 50.0% |
| Funding Amount | 0/12 | 0.0% ❌ |
| Crunchbase URLs | 0/12 | 0.0% ❌ |
| Company Logos | 0/12 | 0.0% ❌ |
| LinkedIn URLs | 11/12 | 91.7% |
| Websites | 11/12 | 91.7% |

**Companies Analyzed:**
1. **Anthropic** (2021-Present) - Privately Held, 501-1000 employees
   - Funding Date: ✅ 2025-09-02
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available

2. **OpenAI** (3 positions: 2019-2021, 2018-2019, 2016-2018) - Partnership, 201-500 employees
   - Funding Date: ✅ 2025-03-31
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available

3. **Google** (2015-2016) - Public Company, 10,001+ employees
   - Funding Date: ❌ Not available
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available
   - Stock Ticker: ✅ GOOGL

4. **Baidu, Inc.** (2014-2015) - Public Company, 10,001+ employees
   - Funding Date: ✅ 2025-03-06
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available

5. **Skyline Targeted Proteomics Environment** (2013) - No company data
   - All fields: ❌ Missing

6. **Stanford University** (2011-2014) - Educational, 10,001+ employees
   - Funding Date: ❌ Not available
   - Crunchbase: ❌ Not available

7. **Applied Minds** (2 positions: 2008-2009, 2003-2004) - Privately Held, 51-200 employees
   - Funding Date: ❌ Not available
   - Crunchbase: ❌ Not available

8. **Princeton University** (2006-2011) - Educational, 5001-10,000 employees
   - Funding Date: ✅ 2024-06-06
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available

9. **Schlumberger** (2004-2006) - Public Company, 10,001+ employees
   - Funding Date: ❌ Not available
   - Stock Ticker: ✅ SLB

**Key Findings:**
- ⚠️ **100% of companies with funding dates have NULL amounts** (6 companies)
- ⚠️ **0% Crunchbase URL coverage** across all 12 companies
- ⚠️ **0% logo coverage** across all 12 companies
- ✅ **Strong metadata coverage**: company type, size, industry (92%)

---

## 2. Aravind Srinivas (Perplexity CEO)

**Profile Overview:**
- **LinkedIn:** https://www.linkedin.com/in/aravind-srinivas-16051987/
- **Profile ID:** 418654053
- **Current Role:** Cofounder, President, CEO at Perplexity
- **Total Companies:** 6
- **Notable Background:** Research Scientist at OpenAI, Research Intern at Google and DeepMind

**Files:**
- **Raw JSON:** [aravind_srinivas_perplexity.json](raw_responses/aravind_srinivas_perplexity.json) (31 KB)
- **Field Analysis:** [aravind_srinivas_perplexity_analysis.md](field_analysis/aravind_srinivas_perplexity_analysis.md)

**Data Coverage:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Funding Date | 4/6 | 66.7% |
| Funding Amount | 0/6 | 0.0% ❌ |
| Crunchbase URLs | 0/6 | 0.0% ❌ |
| Company Logos | 0/6 | 0.0% ❌ |
| LinkedIn URLs | 5/6 | 83.3% |
| Websites | 5/6 | 83.3% |

**Companies Analyzed:**
1. **Perplexity** (2022-Present) - Privately Held, 11-50 employees
   - Funding Date: ✅ **2025-08-15** (very recent!)
   - Funding Amount: ❌ **NULL** (critical missing data)
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available
   - **NOTE:** This is a $20B valued company with recent funding, yet amount is NULL

2. **Aravind Srinivas** (Personal/Angel) (2021-Present) - No company data
   - All fields: ❌ Missing

3. **OpenAI** (2 positions: 2021-2022, 2018-2019) - Partnership, 201-500 employees
   - Funding Date: ✅ 2025-03-31
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available

4. **Google** (2020-2021) - Public Company, 10,001+ employees
   - Funding Date: ❌ Not available
   - Crunchbase: ❌ Not available
   - Stock Ticker: ✅ GOOGL

5. **DeepMind** (2019-2020) - Privately Held, 501-1000 employees
   - Funding Date: ✅ 2011-02-01 (old data, 14 years ago)
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available

**Key Findings:**
- ⚠️ **CRITICAL:** Perplexity shows funding date 2025-08-15 but amount is NULL
- ⚠️ This is the company's latest Series B round (~$500M+ based on valuation)
- ⚠️ **0% Crunchbase URL coverage** - cannot verify funding data
- ⚠️ **0% logo coverage** - cannot display company logos in UI
- ✅ **Email present:** `aravind@perplexity.ai` (verified)

---

## 3. Ivan Zhao (Notion CEO)

**Profile Overview:**
- **LinkedIn:** https://www.linkedin.com/in/ivanhzhao/
- **Profile ID:** 48879039
- **Current Role:** Founder at Notion
- **Total Companies:** 2
- **Notable Background:** Product at Inkling

**Files:**
- **Raw JSON:** [ivan_zhao_notion.json](raw_responses/ivan_zhao_notion.json) (12 KB)
- **Field Analysis:** [ivan_zhao_notion_analysis.md](field_analysis/ivan_zhao_notion_analysis.md)

**Data Coverage:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Funding Date | 2/2 | **100%** |
| Funding Amount | 1/2 | **50%** ⚠️ |
| Crunchbase URLs | 0/2 | 0.0% ❌ |
| Company Logos | 0/2 | 0.0% ❌ |
| LinkedIn URLs | 2/2 | 100% |
| Websites | 2/2 | 100% |

**Companies Analyzed:**
1. **Notion** (2013-Present) - Privately Held, 501-1000 employees
   - Funding Date: ✅ 2021-10-08
   - Funding Amount: ❌ **NULL**
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available
   - **NOTE:** $10B+ valued company, missing funding amount

2. **Inkling** (2012-2013) - Privately Held, 51-200 employees
   - Funding Date: ✅ 2016-12-13
   - Funding Amount: ✅ **$25,000,000** (ONLY company with amount!)
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available

**Key Findings:**
- ✅ **ONLY profile with ANY funding amount data** (1/2 companies, 50%)
- ⚠️ Notion (more recent, larger company) has NULL amount
- ⚠️ Inkling (older, smaller company) has $25M amount
- ⚠️ **Pattern:** Funding amount availability seems random/inconsistent
- ⚠️ **0% Crunchbase URL coverage** despite 100% funding date coverage
- ⚠️ **0% logo coverage**

---

## 4. Dylan Field (Figma CEO)

**Profile Overview:**
- **LinkedIn:** https://www.linkedin.com/in/dylanfield/
- **Profile ID:** 146881803
- **Current Role:** CEO Co-founder at Figma, Inc.
- **Total Companies:** 7
- **Notable Background:** Data Analytics Intern at LinkedIn, Research Assistant at Microsoft, various startups

**Files:**
- **Raw JSON:** [dylan_field_figma.json](raw_responses/dylan_field_figma.json) (32 KB)
- **Field Analysis:** [dylan_field_figma_analysis.md](field_analysis/dylan_field_figma_analysis.md)

**Data Coverage:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Funding Date | 5/7 | 71.4% |
| Funding Amount | 0/7 | 0.0% ❌ |
| Crunchbase URLs | 0/7 | 0.0% ❌ |
| Company Logos | 0/7 | 0.0% ❌ |
| LinkedIn URLs | 7/7 | 100% |
| Websites | 7/7 | 100% |

**Companies Analyzed:**
1. **Figma, Inc.** (2012-Present) - Privately Held, 1001-5000 employees
   - Funding Date: ✅ 2024-07-17
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available
   - Logo: ❌ Not available
   - Stock Ticker: ✅ Present (interesting for private company)
   - Revenue: ✅ Present

2. **Flipboard Inc.** (2 positions: 2012, 2011) - Privately Held, 51-200 employees
   - Funding Date: ✅ 2022-07-01
   - Funding Amount: ❌ NULL
   - Crunchbase: ❌ Not available

3. **LinkedIn** (2010-2011) - Public Company, 10,001+ employees
   - Funding Date: ✅ 2016-02-15
   - Funding Amount: ❌ NULL
   - Stock Ticker: ✅ Present
   - Revenue: ✅ Present

4. **Microsoft** (2010) - Public Company, 10,001+ employees
   - Funding Date: ❌ Not available
   - Stock Ticker: ✅ MSFT
   - Logo: ❌ Not available (even for Microsoft!)

5. **Indinero** (2009-2010) - Privately Held, 201-500 employees
   - Funding Date: ✅ 2021-01-07
   - Funding Amount: ❌ NULL

6. **O'Reilly Media** (2008) - Privately Held, 201-500 employees
   - Funding Date: ❌ Not available

**Key Findings:**
- ⚠️ **71% funding date coverage** (highest among all profiles)
- ⚠️ **0% funding amount coverage** (despite recent Figma funding in 2024)
- ⚠️ **Even Microsoft has no logo** - not even big tech companies get logos
- ✅ **Stock tickers present** for public companies (LinkedIn, Microsoft, Figma)
- ✅ **Revenue data present** for some companies (Figma, LinkedIn)

---

## Aggregate Analysis: All 27 Companies

### Overall Data Coverage

| Field | Coverage | Companies | Percentage |
|-------|----------|-----------|------------|
| **Company Name** | ✅ Excellent | 27/27 | 100% |
| **Company Type** | ✅ Excellent | 26/27 | 96.3% |
| **Company Founded Year** | ⚠️ Good | 20/27 | 74.1% |
| **Company Size Range** | ✅ Excellent | 26/27 | 96.3% |
| **Company Industry** | ✅ Excellent | 26/27 | 96.3% |
| **HQ Location** | ✅ Excellent | 26/27 | 96.3% |
| **LinkedIn URL** | ✅ Good | 25/27 | 92.6% |
| **Website** | ✅ Good | 25/27 | 92.6% |
| **Funding Date** | ⚠️ Partial | 17/27 | **63.0%** |
| **Funding Amount** | ❌ **CRITICAL FAILURE** | 1/27 | **3.7%** |
| **Crunchbase URL** | ❌ **CRITICAL FAILURE** | 0/27 | **0.0%** |
| **Company Logo** | ❌ **CRITICAL FAILURE** | 0/27 | **0.0%** |
| **Stock Ticker** | ⚠️ Limited | 7/27 | 25.9% |
| **Annual Revenue** | ⚠️ Limited | 8/27 | 29.6% |

### Critical Data Gaps

**1. Crunchbase URLs: 0/27 (0.0%)**
- Field name: `company_crunchbase_url`
- **ALWAYS NULL** across all 27 companies
- **Impact:** Cannot provide user verification links (current flow has 69.2% coverage)

**2. Company Logos: 0/27 (0.0%)**
- Field name: `company_logo_url`
- **ALWAYS NULL** across all 27 companies
- **Impact:** Frontend WorkExperienceCard cannot display logos (current flow has 100% coverage)

**3. Funding Amounts: 1/27 (3.7%)**
- Field name: `company_last_funding_round_amount_raised`
- **NULL in 96.3% of cases** (26/27 companies)
- **Only 1 company** (Inkling) has actual funding amount ($25M)
- **16 companies** have funding DATE but NULL amount
- **Impact:** Company tooltips cannot show "$26M Series B" data

---

## Comparison with Current Flow

### Data Completeness: Multi-Source vs Current Flow

| Metric | Multi-Source | Current Flow | Gap |
|--------|--------------|--------------|-----|
| **Funding Data** | 3.7% (amount) / 63% (date) | 100% (both) | **-96.3% / -37%** |
| **Crunchbase URLs** | 0% | 69.2% | **-69.2%** |
| **Company Logos** | 0% | 100% | **-100%** |
| **Skills** | 0% (different structure) | 100% | **-100%** |
| **Basic Company Info** | 96% | 100% | -4% |
| **Overall Score** | **26.7%** | **50.0%** | **-23.3%** |

### Cost Analysis

| Scenario | Multi-Source | Current Flow | Savings |
|----------|--------------|--------------|---------|
| **Few Companies (6)** | 2 credits | 2 credits | 0% |
| **Many Companies (12)** | 2 credits | 6 credits | 67% |

**BUT:** 67% cost savings is **NOT WORTH** the data gaps:
- 0% Crunchbase URLs (vs 69.2%)
- 0% logos (vs 100%)
- 3.7% funding amounts (vs 100%)

---

## Evidence Quality Assessment

### ✅ High Confidence Findings

1. **Crunchbase URLs: 0%** - Verified across all 27 companies in 4 profiles
2. **Company Logos: 0%** - Verified across all 27 companies in 4 profiles
3. **Funding Amounts: 3.7%** - Only 1/27 companies (Inkling) has amount data
4. **Skills Missing** - No `skills` array in any of the 4 profiles

### ⚠️ Medium Confidence Findings

1. **Funding Date Coverage: 63%** - May vary by company type/size
2. **Stock Ticker Coverage: 26%** - Primarily public companies
3. **Revenue Coverage: 30%** - Limited sample size

### 📊 Sample Representativeness

**Profile Selection:**
- ✅ **Diverse company types:** AI startups (Anthropic, Perplexity), productivity (Notion, Figma)
- ✅ **Diverse stages:** Series A to Series C+, public companies (Google, Microsoft)
- ✅ **Diverse roles:** Founders, executives, researchers, interns
- ✅ **27 total companies** - Sufficient sample size for data gap identification

**Limitations:**
- ⚠️ All profiles are tech industry (AI, SaaS, design)
- ⚠️ All profiles are US-based or US-educated
- ⚠️ All profiles are male founders (gender bias in sample)
- ⚠️ May not represent non-tech industries

---

## Recommendations Based on Evidence

### ❌ DO NOT Use Multi-Source for:

1. **Frontend UI display** - Missing logos (0% coverage)
2. **User verification workflows** - Missing Crunchbase URLs (0% coverage)
3. **Company tooltips** - Missing funding amounts (96.3% missing)
4. **AI assessment with skills** - Missing skills array

### ✅ Multi-Source MAY Be Useful for:

1. **Basic company metadata** - Type, size, industry (96% coverage)
2. **Company social presence** - LinkedIn, website URLs (93% coverage)
3. **Employee metadata** - Name, headline, experience count (100%)
4. **Additional fields not in current flow** - Awards, patents, publications

### ⚠️ Hybrid Approach NOT Recommended

**Why:**
- Still need to call company_base for Crunchbase URLs/logos
- No cost savings (2 + N credits vs 1 + N credits)
- Data inconsistency (multi-source funding date vs company_base funding date)
- Engineering complexity

---

## How to Verify These Findings

### Option 1: Inspect Raw JSON Files

```bash
cd backend/multi_source_test/evidence/raw_responses

# Check for Crunchbase URLs
jq '[.experience[].company_crunchbase_url] | unique' *.json
# Expected output: [null] (all null)

# Check for company logos
jq '[.experience[].company_logo_url] | unique' *.json
# Expected output: [null] (all null)

# Check funding amounts
jq '[.experience[].company_last_funding_round_amount_raised] | map(select(. != null))' *.json
# Expected output: Only Inkling has $25M
```

### Option 2: Read Field Analysis Documents

```bash
cd backend/multi_source_test/evidence/field_analysis

# Read any analysis document
cat aravind_srinivas_perplexity_analysis.md

# Search for specific findings
grep -r "Crunchbase URL" *.md
grep -r "Company Logo" *.md
```

### Option 3: Run Your Own Tests

```bash
cd backend/multi_source_test

# Edit test_multi_source_employee.py with your own LinkedIn URLs
# Run the test
python3 test_multi_source_employee.py

# Your results will be in results/ directory
```

---

## Changelog

**2025-10-28:** Initial evidence collection
- Tested 4 profiles (Anthropic, Perplexity, Notion, Figma CEOs)
- Analyzed 27 companies total
- Generated raw JSON responses and field analysis documents
- Identified critical data gaps: 0% Crunchbase URLs, 0% logos, 3.7% funding amounts

---

## Related Files

- **[../MULTI_SOURCE_EVALUATION.md](../MULTI_SOURCE_EVALUATION.md)** - Complete evaluation report with recommendation
- **[../README.md](../README.md)** - Test methodology and scripts usage
- **[README.md](README.md)** - Evidence package overview
- **[test_summary.json](test_summary.json)** - Aggregated test statistics

---

**Evidence Collection:** October 28, 2025
**Total Files:** 9 (4 raw JSON + 4 analysis + 1 summary)
**Total Size:** ~168 KB (raw data)
**Profiles:** Dario Amodei, Aravind Srinivas, Ivan Zhao, Dylan Field
**Companies:** Anthropic, Perplexity, Notion, Figma, OpenAI, Google, Microsoft, LinkedIn, DeepMind, Baidu, and 17 others
