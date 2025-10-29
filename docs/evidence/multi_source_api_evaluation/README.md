# Multi-Source Employee API Evaluation

**Purpose**: Test whether CoreSignal's multi-source employee API can replace the current two-step flow (employee_clean + company_base enrichment) for the LinkedIn Profile Assessor application.

## Current Architecture (Baseline)

```
User submits LinkedIn URL
    ↓
1. Fetch employee via employee_clean/collect/{shorthand} (1 credit)
    ↓
2. For each company (2020+), fetch via company_base/collect/{company_id} (N credits)
    ↓
Total: 1 + N credits per candidate (typically 5-10 credits)
```

## Multi-Source Hypothesis

The multi-source employee API claims to provide enriched company data embedded within work experiences, potentially eliminating separate company API calls.

**Claimed Benefits:**
- Single API call (faster)
- Reduced cost (2 credits vs 5-10 credits)
- Company data includes: funding, locations, size, industry, social URLs

**Known Concerns (from prior testing):**
- Crunchbase URLs: 0% coverage in company_multi_source (per FINAL_RECOMMENDATION.md)
- Data freshness: Unknown if funding data is current
- Logo availability: Unknown if logo URLs included

## Test Scripts

### 1. `test_multi_source_employee.py`

**Purpose**: Fetch multi-source employee data and analyze embedded company information

**Usage**:
```bash
cd backend/multi_source_test
python test_multi_source_employee.py
```

**What it does**:
1. Fetches employee profiles via `/v2/employee_multi_source/collect/{shorthand}`
2. Analyzes embedded company data for each work experience
3. Calculates coverage statistics:
   - Funding data availability (%)
   - Crunchbase URL coverage (%)
   - Company logo availability (%)
4. Saves raw JSON responses to `results/` directory
5. Generates summary report with statistics

**Output**:
- `results/multi_source_{shorthand}_{timestamp}.json` - Raw API responses
- `results/test_summary_{timestamp}.json` - Aggregated statistics

**Edit before running**:
Add LinkedIn profile URLs to the `test_profiles` list at bottom of script:
```python
test_profiles = [
    "https://www.linkedin.com/in/firstname-lastname/",
    "https://www.linkedin.com/in/another-person/",
    # Add 3-5 profiles from Series A companies
]
```

### 2. `compare_api_responses.py`

**Purpose**: Side-by-side comparison of multi-source vs current flow (employee_clean + company_base)

**Usage**:
```bash
cd backend/multi_source_test
python compare_api_responses.py https://www.linkedin.com/in/firstname-lastname/
```

**What it does**:
1. Fetches same profile via BOTH methods:
   - Multi-source employee API (2 credits)
   - Current flow: employee_clean + company_base (1 + N credits)
2. Compares employee-level data completeness
3. Compares company-level data for each work experience:
   - Funding data (date, amount, round type)
   - Crunchbase URLs
   - Company logos
   - Additional metadata (size, industry, location)
4. Calculates cost-benefit:
   - Credit savings (%)
   - Data completeness scores (0-100)
   - Recommendation (switch, keep, or hybrid)
5. Saves comparison report to `comparisons/` directory

**Output**:
- `comparisons/comparison_{shorthand}_{timestamp}.json` - Full comparison report
- Console output with visual comparison tables

## Test Profiles (Recommended)

For best evaluation, test with profiles that have:
- ✅ **Recent experience** (jobs from 2020+)
- ✅ **Series A companies** (more likely to have funding data)
- ✅ **Multiple companies** (test coverage across different company types)
- ✅ **Mix of startup stages** (seed, Series A/B, growth)
- ✅ **Geographic diversity** (US, international)

**Example test cases**:
1. **Recent Series A founder** (2024-2025 funding)
   - Tests: Latest funding data accuracy

2. **Executive at established Series A company** (2022-2023 funding)
   - Tests: Funding data freshness

3. **Engineer at early-stage startup** (seed or pre-seed)
   - Tests: Coverage for smaller companies

4. **Multiple companies in profile** (5+ work experiences)
   - Tests: Data completeness across company types

5. **International company experience**
   - Tests: Non-US company data quality

## Key Evaluation Criteria

### ✅ Multi-Source is VIABLE if:
- Funding data coverage ≥50%
- Funding data is as fresh or fresher than company_base
- Company logos available (critical for UI)
- No major data gaps for AI assessment
- Cost savings justify any loss of Crunchbase URLs

### ❌ Multi-Source is NOT VIABLE if:
- Funding data coverage <30%
- Critical fields missing (logos, industry, size)
- Data significantly staler than company_base
- No cost savings (if 2× credit pricing negates benefit)
- Crunchbase URL coverage is 0% (known from prior testing)

## Expected Findings

Based on prior investigation (`FINAL_RECOMMENDATION.md`):

| Field | Multi-Source (Expected) | Current Flow (Known) | Winner |
|-------|------------------------|---------------------|--------|
| **Funding Data Coverage** | 50% (estimated) | 100% | Current |
| **Crunchbase URLs** | 0% (known) | 69.2% | Current |
| **Company Logos** | Unknown | 100% (via logo_url + Clearbit) | ? |
| **Funding Freshness** | Unknown | Stale (2020 for 2025 companies) | ? |
| **API Cost** | 2 credits | 6-10 credits | Multi |
| **API Calls** | 1 call | 6-10 calls | Multi |

**Critical Question**: Does the 50-70% cost savings from multi-source justify the loss of:
- Crunchbase URLs (69.2% → 0%)?
- Guaranteed company data (100% → 50%)?

## Next Steps

1. **Run Tests**:
   ```bash
   # Test multi-source API
   python test_multi_source_employee.py

   # Compare with current flow
   python compare_api_responses.py <linkedin_url>
   ```

2. **Analyze Results**:
   - Check `results/test_summary_*.json` for coverage statistics
   - Review `comparisons/comparison_*.json` for data quality comparison
   - Note any critical missing fields

3. **Decision Matrix**:
   - If multi-source has ≥80% data completeness + ≥50% cost savings → **Switch**
   - If multi-source has 50-80% completeness + significant gaps → **Hybrid** (multi-source + selective company_base)
   - If multi-source has <50% completeness → **Keep current flow**

4. **Document Findings**:
   - Create `MULTI_SOURCE_EVALUATION.md` with:
     - Test results summary
     - Field-by-field comparison table
     - Cost-benefit analysis
     - Final recommendation with evidence

## Environment Requirements

```bash
# Required environment variable
export CORESIGNAL_API_KEY="your_api_key_here"

# Python dependencies (already in backend/requirements.txt)
pip install requests
```

## File Structure

```
backend/multi_source_test/
├── README.md                        # This file
├── test_multi_source_employee.py    # Main test script
├── compare_api_responses.py         # Comparison tool
├── results/                         # Raw test results (gitignored)
│   ├── multi_source_*.json
│   └── test_summary_*.json
└── comparisons/                     # Comparison reports (gitignored)
    └── comparison_*.json
```

## Credits Used During Testing

**Per profile tested**:
- Multi-source only: 2 credits
- Current flow only: 1 + N credits (typically 6-10)
- Full comparison: 2 + (1 + N) = 8-12 credits per profile

**Budget for 5 profiles**:
- Multi-source only: 10 credits
- Full comparison: 40-60 credits

**Recommendation**: Test with 3 profiles first, evaluate results, then decide if more testing needed.
