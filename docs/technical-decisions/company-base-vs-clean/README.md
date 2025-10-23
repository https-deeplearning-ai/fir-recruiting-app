# Technical Decision: company_base vs company_clean

**Decision:** Use `company_base` API endpoint instead of `company_clean`  
**Date:** October 23, 2025  
**Status:** ✅ Approved - Ready for Implementation

---

## Quick Summary

After testing 5 diverse companies, we found that `company_base` provides **100% funding data availability** compared to only 60% for `company_clean`. Since funding information is critical for assessing company growth stage and stability in our recruiting tool, we're switching endpoints despite losing some enriched AI fields.

---

## Documents in this Folder

### Main Decision Document
- **[WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md](WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md)** - Complete decision record with rationale, evidence, and implementation plan

### Evidence Folder
- **[evidence/](evidence/)** - Raw test data from 5 companies proving funding data availability

---

## Test Data (Evidence)

All raw JSON responses from CoreSignal API comparison:

### Companies Tested:
1. **Bexorg** (ID: 92819342) - Biotech, Series A $23M
2. **Rabine** (ID: 7116608) - Construction, 3 PE rounds  
3. **Griphic** (ID: 96309016) - Software, Seed $2.4M
4. **Hybrid Poultry Farm** (ID: 12616963) - Agriculture, Debt $10M
5. **We Rock the Spectrum** (ID: 5883355) - Recreation, Grant $2K

### Files:
```
evidence/
├── company_92819342_clean.json     (Bexorg - company_clean response)
├── company_92819342_base.json      (Bexorg - company_base response)
├── company_7116608_clean.json      (Rabine - company_clean response)
├── company_7116608_base.json       (Rabine - company_base response)
├── company_96309016_clean.json     (Griphic - company_clean response)
├── company_96309016_base.json      (Griphic - company_base response)
├── company_12616963_clean.json     (Hybrid Poultry - company_clean response)
├── company_12616963_base.json      (Hybrid Poultry - company_base response)
├── company_5883355_clean.json      (We Rock - company_clean response)
├── company_5883355_base.json       (We Rock - company_base response)
├── bexorg_clean_API.json           (Original Bexorg test - clean)
├── bexorg_base_API.json            (Original Bexorg test - base)
├── endpoint_comparison_summary.json (Statistical summary)
└── endpoint_comparison_results.json (Detailed comparison data)
```

---

## Key Findings

### Funding Data Availability

| Company | company_clean | company_base | Winner |
|---------|---------------|--------------|--------|
| Bexorg | ❌ `null` | ✅ Series A $23M | base |
| Rabine | ❌ `null` | ✅ 3 rounds (PE) | base |
| Griphic | ✅ Has data | ✅ 3 rounds, $2.4M | Both |
| Hybrid Poultry | ✅ Has data | ✅ 3 rounds, $10M | Both |
| We Rock | ✅ Has data | ✅ 2 rounds, $2K | Both |

**Success Rate:**
- `company_clean`: 60% (3 out of 5)
- `company_base`: **100%** (5 out of 5)

---

## What We Get from company_base

✅ **Funding rounds** (`company_funding_rounds_collection`)  
✅ **Investor names** (`company_featured_investors_collection`)  
✅ **Crunchbase links** (`company_crunchbase_info_collection`)  
✅ **Featured employees** (`company_featured_employees_collection`)  
✅ **Similar companies** (`company_similar_collection`)  
✅ **Direct logo URLs** (not base64)

---

## What We Lose from company_clean

❌ **Tech stack** (`technologies`)  
❌ **Enriched AI categories** (`enriched_category`, `enriched_keywords`)  
❌ **Detailed social URLs** (mostly null anyway)  
❌ **SEO metadata** (`metadata_title`, `metadata_description`)

**Trade-off:** Acceptable - funding data is more critical than enriched fields for recruiting

---

## How to Use This Evidence

### Compare Funding Data:
```bash
# Check funding in clean (often null)
grep -A 5 '"funding_rounds"' evidence/company_92819342_clean.json

# Check funding in base (reliable)
grep -A 20 '"company_funding_rounds_collection"' evidence/company_92819342_base.json
```

### Field Count Comparison:
```bash
# Count fields in each response
jq 'keys | length' evidence/company_92819342_clean.json  # 60 fields
jq 'keys | length' evidence/company_92819342_base.json   # 45 fields
```

### Find Unique Fields:
```bash
# Fields only in clean
jq 'keys' evidence/company_92819342_clean.json > /tmp/clean_fields.json
jq 'keys' evidence/company_92819342_base.json > /tmp/base_fields.json
diff /tmp/clean_fields.json /tmp/base_fields.json
```

---

## Implementation Status

- [x] Investigation complete
- [x] Evidence collected (5 companies)
- [x] Decision approved
- [ ] Update coresignal_service.py
- [ ] Update field mappings
- [ ] Update frontend (investor display)
- [ ] Testing
- [ ] Deployment

---

**For detailed analysis, see:** [WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md](WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md)
