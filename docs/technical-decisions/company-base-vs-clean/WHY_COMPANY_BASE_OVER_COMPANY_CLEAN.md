# Technical Decision: Why company_base Over company_clean

**Decision Date:** October 23, 2025
**Decision Owner:** Gaurav Surtani
**Status:** ✅ Approved - Ready for Implementation
**Impact:** High - Core API functionality change

---

## 🎯 Executive Summary

**DECISION: Use CoreSignal `company_base` endpoint instead of `company_clean` for company enrichment**

**Primary Reason:** Funding data reliability - 100% success rate vs 60% success rate

**Impact on Product:**
- ✅ All companies will show funding information (when available)
- ✅ Investor names displayed in company tooltips
- ✅ Crunchbase validation links included
- ✅ Better assessment of company growth stage for recruiters
- ⚠️ Trade-off: Lose some enriched AI fields (acceptable for our use case)

---

## 📊 The Problem We Discovered

### Initial Issue: Bexorg Funding Data Missing

**User Report (October 22, 2025):**
> "I just want to confirm that what I have pasted in the chat earlier is a complete match with the collect company information from CoreSignal because I think that there is funding information for this particular company but I cannot see it."

**User's Dashboard showed:**
- Series A: $23.0M
- Investor: Engine Ventures
- Date: November 15, 2025

**Our app (using `company_clean`) showed:**
- `funding_rounds: null` ❌

### Root Cause Investigation

User discovered that **`company_base` endpoint** returned complete funding data while `company_clean` returned `null`. This prompted a comprehensive API comparison study.

---

## 🔬 Methodology: How We Tested

### Test Sample
- **5 diverse companies** with confirmed funding history
- Selected via CoreSignal search API (companies with `funding_total_rounds_count_gte: 1`)
- Mix of industries: Biotech, Construction, Software, Agriculture, Recreation

### Companies Tested
1. **Bexorg, Inc.** (Biotech) - Series A $23M
2. **Rabine** (Construction) - 3 rounds, Private Equity
3. **Griphic** (Software) - 3 rounds, Seed $2.4M
4. **Hybrid Poultry Farm** (Agriculture) - 3 rounds, Debt $10M
5. **We Rock the Spectrum** (Recreation) - 2 rounds, Grant $2K

### Test Process
1. Fetched data from both `/company_clean/collect/` and `/company_base/collect/`
2. Compared field counts, data richness, and funding availability
3. Analyzed unique fields in each endpoint
4. Saved raw JSON responses for evidence

---

## 📈 Results: Data Comparison

### Funding Data Availability

| Company | company_clean | company_base | Winner |
|---------|---------------|--------------|--------|
| Bexorg | ❌ `null` | ✅ Series A $23M | base |
| Rabine | ❌ `null` | ✅ 3 rounds (PE) | base |
| Griphic | ✅ Has data | ✅ 3 rounds, $2.4M | Both |
| Hybrid Poultry | ✅ Has data | ✅ 3 rounds, $10M | Both |
| We Rock Spectrum | ✅ Has data | ✅ 2 rounds, $2K | Both |

**Success Rate:**
- `company_clean`: 60% (3 out of 5 had data)
- `company_base`: **100%** (5 out of 5 had data)

**Conclusion:** `company_base` is more reliable for funding information

---

## 🔍 Field-Level Analysis

### Overall Statistics
- `company_clean`: **60 fields**
- `company_base`: **45 fields**
- **Common fields**: 8 (id, name, description, industry, type, founded, followers, last_updated)
- **Unique to clean**: 52 fields
- **Unique to base**: 37 fields

### Critical Differences for Our Use Case

#### ✅ What company_base Has (that clean doesn't)

**🌟 FUNDING & INVESTORS (CRITICAL):**
```json
{
  "company_funding_rounds_collection": [
    {
      "last_round_type": "Series A",
      "last_round_money_raised": "US$ 23.0M",
      "last_round_date": "2025-11-15",
      "last_round_investors_count": 1,
      "total_rounds_count": 1,
      "cb_url": "https://www.crunchbase.com/funding_round/..."
    }
  ],
  "company_featured_investors_collection": [
    {
      "company_investors_list": {
        "name": "Engine Ventures",
        "cb_url": "https://www.crunchbase.com/organization/engine-ventures"
      }
    }
  ],
  "company_crunchbase_info_collection": [...]
}
```

**📋 OTHER VALUABLE FIELDS:**
- `company_featured_employees_collection` - Notable team members
- `company_locations_collection` - Office locations with full addresses
- `company_similar_collection` - Similar companies for context
- `company_updates_collection` - Recent company posts/activity
- `logo_url` - Direct image URL (vs base64 in clean)

#### ⚠️ What We Lose from company_clean

**ENRICHED AI FIELDS:**
- `enriched_category` - AI-generated category (e.g., "Software Development")
- `enriched_keywords` - SEO keywords
- `enriched_summary` - AI-generated summary
- `technologies` - Tech stack list
- `enriched_b2b` - B2B classification flag

**DETAILED METADATA:**
- `size_range` - "11-50 employees" format (base has just "size")
- `size_employees_count_inferred` - Inferred count
- `location_hq_regions` - Geographic regions
- `metadata_title`, `metadata_description` - SEO metadata
- `social_*_urls` - Social media profile URLs (mostly null anyway)
- Various feature flags: `api_docs_exist`, `demo_available`, `pricing_available`, etc.

**ASSESSMENT:** Most of these fields are either:
1. Nice-to-have but not critical for recruiting
2. Mostly null/empty in practice
3. Can be inferred or omitted without major impact

---

## 🎯 Why This Decision Makes Sense for Our Product

### Our Product: LinkedIn Profile Assessor for Recruiters

**Primary Use Case:**
Help recruiters evaluate candidates by understanding their **current company context**:
- Is the company well-funded and stable?
- What growth stage is the company at?
- Who invested in the company (credibility signal)?
- How established is the organization?

### Why Funding Data Is Critical

1. **Startup vs. Established Assessment**
   - Series A = Early stage, high risk, high reward
   - Series C+ = Established, more stable
   - No funding = Bootstrapped or very early

2. **Compensation Context**
   - Well-funded startups can offer competitive packages
   - Underfunded = potential compensation risk
   - Helps candidates evaluate offers

3. **Career Trajectory Signal**
   - Working at a well-funded startup = valuable experience
   - Backed by top-tier VCs = prestige signal
   - Company growth stage matters for career decisions

4. **Risk Assessment**
   - Funding indicates runway and stability
   - Multiple rounds = proven business model
   - Recent funding = company is actively growing

### Why Losing Enriched Fields Is Acceptable

1. **Tech Stack** - Nice to have but not critical
   - Recruiters care more about "is it funded?" than "what tech does it use?"
   - Candidates can research tech stack independently

2. **AI Categories** - Often inaccurate anyway
   - Example: Bexorg (brain science company) was tagged as "mining" and "Software Development"
   - LinkedIn industry field is more accurate

3. **Social URLs** - Mostly null in practice
   - Most companies don't populate all social media fields
   - LinkedIn URL is available in both endpoints

4. **SEO Metadata** - Not relevant for recruiting
   - `meta_description` and `meta_title` are website optimization fields
   - Recruiters don't need this

---

## 💰 Cost-Benefit Analysis

### Option A: company_clean (Current)
**Benefits:**
- More total fields (60 vs 45)
- Enriched AI classifications
- Tech stack information

**Costs:**
- ❌ **40% of companies missing funding data**
- ❌ No investor information
- ❌ No Crunchbase validation
- ❌ Poor user experience ("Why can't I see funding for this company?")

### Option B: company_base (Proposed) ✅
**Benefits:**
- ✅ **100% funding data availability**
- ✅ Investor names included
- ✅ Crunchbase links for validation
- ✅ Featured employees list
- ✅ Similar companies suggestions
- ✅ Direct logo URLs (simpler than base64)

**Costs:**
- Lose enriched AI fields (acceptable trade-off)
- Slightly fewer total fields (but the important ones are there)

**API Cost Impact:** None - same credit usage per company

---

## 📋 Implementation Requirements

### Code Changes Needed

**File:** `backend/coresignal_service.py`

**1. Update Endpoint:**
```python
# OLD
url = f'https://api.coresignal.com/cdapi/v2/company_clean/collect/{company_id}'

# NEW
url = f'https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}'
```

**2. Update Field Names:**
```python
# Funding data
funding_rounds = company_data.get('company_funding_rounds_collection', [])  # Not 'funding_rounds'

# Investors
investors = company_data.get('company_featured_investors_collection', [])

# Crunchbase
crunchbase = company_data.get('company_crunchbase_info_collection', [])

# Logo
logo_url = company_data.get('logo_url')  # Not base64 'logo'

# Website
website = company_data.get('website')  # Not 'websites_main'

# Employee count
employees = company_data.get('employees_count')  # Not 'size_employees_count'

# Size range
size = company_data.get('size')  # Not 'size_range'

# LinkedIn URL
linkedin_url = company_data.get('url')  # Not 'websites_linkedin'
```

**3. Extract Investor Data (New Feature):**
```python
investors = company_data.get('company_featured_investors_collection', [])
if investors:
    intelligence['investors'] = [
        {
            'name': inv['company_investors_list'].get('name'),
            'crunchbase_url': inv['company_investors_list'].get('cb_url')
        }
        for inv in investors
    ]
```

**Frontend Changes Needed:**

**File:** `frontend/src/App.js`

Add investor display in company tooltip:
```javascript
{companyData.investors && companyData.investors.length > 0 && (
  <div>
    <strong>Investors:</strong>
    <ul>
      {companyData.investors.map((inv, idx) => (
        <li key={idx}>
          {inv.crunchbase_url ? (
            <a href={inv.crunchbase_url} target="_blank" rel="noopener noreferrer">
              {inv.name}
            </a>
          ) : (
            inv.name
          )}
        </li>
      ))}
    </ul>
  </div>
)}
```

---

## 🧪 Evidence & Supporting Documents

### Raw Test Data
**Location:** `backend/`
- `company_92819342_clean.json` - Bexorg (company_clean response)
- `company_92819342_base.json` - Bexorg (company_base response)
- `company_7116608_clean.json` - Rabine (company_clean response)
- `company_7116608_base.json` - Rabine (company_base response)
- `company_96309016_clean.json` - Griphic (company_clean response)
- `company_96309016_base.json` - Griphic (company_base response)
- `company_12616963_clean.json` - Hybrid Poultry (company_clean response)
- `company_12616963_base.json` - Hybrid Poultry (company_base response)
- `company_5883355_clean.json` - We Rock Spectrum (company_clean response)
- `company_5883355_base.json` - We Rock Spectrum (company_base response)
- `endpoint_comparison_summary.json` - Statistical summary

### Detailed Analysis Documents
- `docs/investigations/ENDPOINT_COMPARISON_REPORT.md` - Complete field-by-field analysis
- `docs/investigations/COMPANY_DATA_VERIFICATION.md` - Initial Bexorg investigation
- `docs/investigations/CORESIGNAL_DATA_MISMATCH_REPORT.md` - Dashboard vs API comparison

---

## ⚠️ Risks & Mitigation

### Risk 1: Loss of Enriched Fields
**Impact:** Medium
**Likelihood:** Certain
**Mitigation:** Acceptable trade-off - funding data is more critical for recruiting use case

### Risk 2: Future Feature Requests for Tech Stack
**Impact:** Low
**Likelihood:** Low
**Mitigation:** Can add supplementary `company_clean` call in future if needed (2x credits)

### Risk 3: Field Name Changes Break Production
**Impact:** High
**Likelihood:** Medium
**Mitigation:**
- Thorough testing before deployment
- Update all field references in one commit
- Test with multiple company profiles

---

## ✅ Acceptance Criteria

Before deploying this change, verify:

- [ ] All funding data displays correctly for test companies
- [ ] Investor names appear in tooltips
- [ ] Crunchbase links are clickable and work
- [ ] Company logos display (using `logo_url` not base64)
- [ ] No broken field references in frontend
- [ ] Bexorg shows "Series A $23M" funding
- [ ] Companies without funding gracefully show "No funding data"
- [ ] Similar companies section works (if implemented)
- [ ] Featured employees section works (if implemented)

---

## 📅 Timeline

**Investigation:** October 22-23, 2025 ✅
**Decision Made:** October 23, 2025 ✅
**Implementation:** TBD
**Testing:** TBD
**Deployment:** TBD

---

## 🔄 Rollback Plan

If issues arise post-deployment:

1. Revert endpoint back to `company_clean`
2. Revert all field name changes
3. Remove investor display features
4. Deploy previous working version

**Estimated Rollback Time:** 15 minutes

---

## 📝 Approval & Sign-off

**Decision Maker:** Gaurav Surtani
**Technical Lead:** Claude Code (Anthropic)
**Approved:** ✅ October 23, 2025

**Rationale Summary:**
> After testing 5 diverse companies, company_base provides 100% funding data availability compared to 60% for company_clean. Since funding information is critical for our recruiting use case (assessing company growth stage, stability, and credibility), we accept the trade-off of losing enriched AI fields. The investor information and Crunchbase validation links add significant value for recruiters and candidates evaluating opportunities.

---

## 📚 References

- CoreSignal API Documentation: https://docs.coresignal.com/
- Test Data Location: `backend/company_*_base.json`
- Investigation Report: `docs/investigations/ENDPOINT_COMPARISON_REPORT.md`
- Original Issue: User report on October 22, 2025 regarding Bexorg funding data

---

**Last Updated:** October 23, 2025
**Document Owner:** Gaurav Surtani
**Next Review:** After implementation and 1 week of production use
