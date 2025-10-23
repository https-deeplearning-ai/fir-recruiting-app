# Project Documentation Index

This folder contains organized technical documentation, decision records, and investigation reports for the LinkedIn Profile AI Assessor project.

---

## 📂 Complete Folder Structure

```
docs/
├── README.md (this file)
│
├── technical-decisions/ (Important decision records)
│   ├── company-base-vs-clean/
│   │   ├── README.md
│   │   ├── WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md
│   │   └── evidence/ (14 JSON test files)
│   │       ├── company_92819342_clean.json
│   │       ├── company_92819342_base.json
│   │       ├── company_7116608_clean.json
│   │       ├── company_7116608_base.json
│   │       ├── company_96309016_clean.json
│   │       ├── company_96309016_base.json
│   │       ├── company_12616963_clean.json
│   │       ├── company_12616963_base.json
│   │       ├── company_5883355_clean.json
│   │       ├── company_5883355_base.json
│   │       ├── bexorg_clean_API.json
│   │       ├── bexorg_base_API.json
│   │       ├── endpoint_comparison_summary.json
│   │       └── endpoint_comparison_results.json
│   └── WHY_SEARCH_API_DOESNT_WORK.md
│
├── investigations/ (Research & evidence)
│   ├── ENDPOINT_COMPARISON_REPORT.md
│   ├── COMPANY_DATA_VERIFICATION.md
│   ├── COMPANY_ENRICHMENT_GUIDE.md
│   ├── CORESIGNAL_DATA_MISMATCH_REPORT.md
│   └── IMPLEMENTATION_SUMMARY.md
│
└── archived/ (Superseded documents)
    ├── SESSION_SUMMARY.md
    ├── CORESIGNAL_SEARCH_VS_COLLECT_API_COMPLETE_ANALYSIS.md
    ├── FINAL_SEARCH_VS_COLLECT_VERIFIED.md
    ├── SEARCH_VS_COLLECT_QUICK_REFERENCE.md
    └── README_API_TESTING.md
```

---

## 📂 Folder Structure

### `/technical-decisions/` - Architecture Decision Records (ADRs)

**Purpose:** Documents explaining WHY we made specific technical choices

| Document | Decision | Date | Status |
|----------|----------|------|--------|
| [WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md](technical-decisions/WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md) | Use `company_base` API endpoint instead of `company_clean` | Oct 23, 2025 | ✅ Approved |
| [WHY_SEARCH_API_DOESNT_WORK.md](technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md) | Use Collect API instead of Search API for profiles | Earlier | ✅ Active |

**Key Insights:**
- **company_base vs company_clean:** Funding data reliability (100% vs 60% success rate) drove the decision
- **Collect vs Search API:** Search API returns incomplete data unsuitable for candidate assessment

---

### `/investigations/` - Evidence & Research Reports

**Purpose:** Detailed investigation reports with test data and analysis

| Document | Investigation Topic | Key Finding |
|----------|---------------------|-------------|
| [ENDPOINT_COMPARISON_REPORT.md](investigations/ENDPOINT_COMPARISON_REPORT.md) | Complete comparison of base vs clean endpoints | Base has funding data, clean often returns null |
| [COMPANY_DATA_VERIFICATION.md](investigations/COMPANY_DATA_VERIFICATION.md) | Bexorg funding data missing from public API | Confirmed data limitation in public API |
| [COMPANY_ENRICHMENT_GUIDE.md](investigations/COMPANY_ENRICHMENT_GUIDE.md) | Two different CoreSignal API access methods | Dashboard API vs Public API have different data |
| [CORESIGNAL_DATA_MISMATCH_REPORT.md](investigations/CORESIGNAL_DATA_MISMATCH_REPORT.md) | Dashboard shows data that API doesn't return | Formatted report for CoreSignal support |
| [IMPLEMENTATION_SUMMARY.md](investigations/IMPLEMENTATION_SUMMARY.md) | Complete timeline of funding data investigation | Summary of all findings and next steps |

**Supporting Evidence:**
- Test data from 5 companies (Bexorg, Rabine, Griphic, Hybrid Poultry, We Rock Spectrum)
- Raw JSON responses saved in `backend/company_{id}_base.json` and `backend/company_{id}_clean.json`
- Field-by-field comparison tables

---

### `/archived/` - Superseded Documentation

**Purpose:** Old documentation kept for historical reference

| Document | Reason for Archival |
|----------|---------------------|
| SESSION_SUMMARY.md | Old session notes, superseded by newer investigations |
| CORESIGNAL_SEARCH_VS_COLLECT_API_COMPLETE_ANALYSIS.md | Early analysis, superseded by WHY_SEARCH_API_DOESNT_WORK.md |
| FINAL_SEARCH_VS_COLLECT_VERIFIED.md | Superseded by technical decision document |
| SEARCH_VS_COLLECT_QUICK_REFERENCE.md | Old quick reference, no longer maintained |
| README_API_TESTING.md | Old testing notes, superseded by investigation reports |

⚠️ **Note:** These documents are kept for historical reference but should not be used for current decision-making.

---

## 🎯 Quick Start

### For New Team Members:
1. Read [WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md](technical-decisions/WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md) - Understand our core API decision
2. Read [WHY_SEARCH_API_DOESNT_WORK.md](technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md) - Understand why we use Collect API
3. Review [ENDPOINT_COMPARISON_REPORT.md](investigations/ENDPOINT_COMPARISON_REPORT.md) for detailed evidence

### For Debugging Funding Data Issues:
1. Check [COMPANY_DATA_VERIFICATION.md](investigations/COMPANY_DATA_VERIFICATION.md) for verification methodology
2. Review test data in `backend/company_*_base.json` files
3. Compare with [ENDPOINT_COMPARISON_REPORT.md](investigations/ENDPOINT_COMPARISON_REPORT.md) field tables

### For API Questions:
1. [COMPANY_ENRICHMENT_GUIDE.md](investigations/COMPANY_ENRICHMENT_GUIDE.md) - Dashboard vs Public API differences
2. [CORESIGNAL_DATA_MISMATCH_REPORT.md](investigations/CORESIGNAL_DATA_MISMATCH_REPORT.md) - Report template for CoreSignal support

---

## 📊 Test Data Reference

**Location:** `backend/`

**Files:**
- `company_92819342_clean.json` & `company_92819342_base.json` - Bexorg (Series A $23M)
- `company_7116608_clean.json` & `company_7116608_base.json` - Rabine (PE funding)
- `company_96309016_clean.json` & `company_96309016_base.json` - Griphic (Seed $2.4M)
- `company_12616963_clean.json` & `company_12616963_base.json` - Hybrid Poultry (Debt $10M)
- `company_5883355_clean.json` & `company_5883355_base.json` - We Rock Spectrum (Grant $2K)
- `endpoint_comparison_summary.json` - Statistical summary

**How to Use:**
```bash
# Compare clean vs base for a specific company
diff backend/company_92819342_clean.json backend/company_92819342_base.json

# Search for specific fields
grep -r "funding_rounds" backend/company_*.json
grep -r "company_funding_rounds_collection" backend/company_*.json
```

---

## 🔍 Key Takeaways

### Critical Decisions:
1. **Use `company_base` endpoint** - More reliable funding data (100% vs 60%)
2. **Use Collect API not Search** - Search returns incomplete data
3. **Store all raw data** - Never lose information from API responses

### Data Availability Findings:
- Funding data: `company_base` reliable, `company_clean` spotty
- Investor data: Only in `company_base`
- Crunchbase links: Only in `company_base`
- Enriched AI fields: Only in `company_clean` (but often inaccurate)

### Implementation Status:
- ✅ Investigation complete
- ✅ Decision approved
- ⏳ Code implementation pending
- ⏳ Testing pending
- ⏳ Deployment pending

---

## 📝 Document Maintenance

### When to Add New Documents:

**Technical Decisions:**
- Making a significant architectural choice
- Choosing between multiple API options
- Changing core data sources
- Format: Problem → Options → Decision → Rationale → Evidence

**Investigations:**
- Discovering unexpected API behavior
- Debugging missing or incorrect data
- Comparing multiple data sources
- Format: Issue → Methodology → Findings → Evidence → Conclusion

**Archiving:**
- Document superseded by newer version
- Implementation approach changed
- No longer relevant to current architecture

### Document Template:

See [WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md](technical-decisions/WHY_COMPANY_BASE_OVER_COMPANY_CLEAN.md) for a comprehensive ADR template including:
- Executive Summary
- Problem Statement
- Test Methodology
- Evidence & Data
- Decision Rationale
- Implementation Requirements
- Risk Assessment
- Approval & Sign-off

---

**Last Updated:** October 23, 2025
**Maintained By:** Project Team
**Questions?** See root [README.md](../README.md) or [CLAUDE.md](../CLAUDE.md)
