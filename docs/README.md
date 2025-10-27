# Project Documentation Index

This folder contains organized technical documentation and decision records for the LinkedIn Profile AI Assessor project.

---

## 📂 Documentation Structure

```
docs/
├── README.md (this file)
├── SUPABASE_SCHEMA.sql
├── CORESIGNAL_MCP_SETUP.md
├── EXTENSION_API.md
├── TESTING_GUIDE.md
│
└── technical-decisions/
    ├── WHY_SEARCH_API_DOESNT_WORK.md
    └── company-api-comparison-2024/
        ├── COMPLETE_VERIFICATION_REPORT.md (Master document)
        ├── FINAL_RECOMMENDATION.md (Executive summary)
        ├── COMPARISON_MATRIX.csv
        └── evidence/ (60 JSON test files from 26 companies)
```

---

## 🎯 Quick Start

### For New Team Members:
1. Read [COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-api-comparison-2024/COMPLETE_VERIFICATION_REPORT.md) - Comprehensive company API analysis
2. Read [WHY_SEARCH_API_DOESNT_WORK.md](technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md) - Why we use Collect API for profiles
3. Review [SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql) for database structure

### For Debugging Company Data Issues:
1. Check [COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-api-comparison-2024/COMPLETE_VERIFICATION_REPORT.md) for API behavior
2. Review test evidence in `technical-decisions/company-api-comparison-2024/evidence/`
3. Consult [FINAL_RECOMMENDATION.md](technical-decisions/company-api-comparison-2024/FINAL_RECOMMENDATION.md) for decision rationale

---

## 📚 Key Documents

### Database & Schema
- **[SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql)** - Complete database schema with tables:
  - `stored_profiles` - Profile caching
  - `stored_companies` - Company data caching
  - `candidate_assessments` - AI assessment results
  - `recruiter_feedback` - Feedback notes and ratings

### Technical Decisions (Architecture Decision Records)

#### Company API Selection (October 2024)
**Decision:** Use `company_base` API endpoint exclusively

**Documents:**
- **[COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-api-comparison-2024/COMPLETE_VERIFICATION_REPORT.md)** (400+ lines)
  - Complete testing methodology across 26 companies
  - Field-by-field comparison of all three endpoints
  - Crunchbase URL availability analysis (69.2% coverage)
  - Implementation guide with Python + React examples
  - Evidence files index (60 JSON files)

- **[FINAL_RECOMMENDATION.md](technical-decisions/company-api-comparison-2024/FINAL_RECOMMENDATION.md)**
  - Executive summary and decision rationale
  - Trade-offs and risk assessment
  - Quick reference guide

**Key Findings:**
- `company_base`: 100% availability, 69.2% Crunchbase URL coverage
- `company_clean`: Inconsistent funding data, no Crunchbase URLs
- `company_multi_source`: 50% availability, not reliable enough

**Test Evidence:**
- Cohort 1: Initial 5 companies (15 JSON files)
- Cohort 2: August 2025 funded companies (30 JSON files)
- Cohort 3: Healthcare verification (15 JSON files)
- Total: 26 companies × 3 endpoints = 60 evidence files

#### Profile Search API (Earlier)
**Decision:** Use Collect API instead of Search API for profile data

**Document:** [WHY_SEARCH_API_DOESNT_WORK.md](technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md)

**Rationale:** Search API returns incomplete data unsuitable for candidate assessment

---

## 🔍 Key Technical Decisions Summary

### 1. Company Data Enrichment
- **API Endpoint:** `company_base` (NOT `company_clean` or `company_multi_source`)
- **Field Priority:** `company_crunchbase_info_collection[0].cb_url` for Crunchbase URLs
- **Optimization:** Only enrich companies from jobs starting 2020+ (saves 60-80% API credits)
- **Fallback Chain:** Company CB URL → Funding round CB URL → None

### 2. Data Freshness Strategy
- Display `last_updated` timestamps from CoreSignal
- Provide Crunchbase links for users to verify current data
- Color-coded freshness indicators (green < 6mo, yellow 6mo-2yr, red > 2yr)
- Store all raw API data for future flexibility

### 3. Profile Data Fetching
- Use Collect API (2-step: search by URL → fetch by ID)
- Prefer `generated_headline` over `headline` field
- Handle date overlaps in experience calculation
- Session-based caching to avoid duplicate API calls

---

## 📊 Evidence Files

**Location:** `technical-decisions/company-api-comparison-2024/evidence/`

**Structure:**
- `cohort_1/` - Initial verification (5 companies × 3 endpoints = 15 files)
- `comprehensive_august_2025/` - August 2025 funding search (10 companies × 3 endpoints = 30 files)
- `healthcare_verification/` - Healthcare companies (5 companies × 3 endpoints = 15 files)

**Naming Convention:**
- `{company_id}_base.json` - company_base endpoint response
- `{company_id}_clean.json` - company_clean endpoint response
- `{company_id}_multi_source.json` - company_multi_source endpoint response

**Usage:**
```bash
# Search for specific field across all evidence
grep -r "company_crunchbase_info_collection" docs/technical-decisions/company-api-comparison-2024/evidence/

# Compare endpoints for same company
diff evidence/cohort_1/92819342_clean.json evidence/cohort_1/92819342_base.json
```

---

## 🛠️ Setup Guides

### CoreSignal MCP Server
**Document:** [CORESIGNAL_MCP_SETUP.md](CORESIGNAL_MCP_SETUP.md)

Instructions for integrating CoreSignal API via Model Context Protocol (MCP) server for Claude Code.

### Extension API
**Document:** [EXTENSION_API.md](EXTENSION_API.md)

API documentation for browser extension integration (if applicable).

### Testing Guide
**Document:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

Testing procedures for API integration, data validation, and quality assurance.

---

## 📝 Document Maintenance Guidelines

### When to Add New Documents

**Technical Decisions:**
- Making significant architectural choices
- Choosing between multiple API options
- Changing core data sources
- Format: Problem → Options → Decision → Rationale → Evidence

**Investigation Reports:**
- Discovering unexpected API behavior
- Comprehensive testing and verification
- Comparing multiple data sources
- Format: Methodology → Test Results → Analysis → Evidence → Conclusion

### Document Template Structure
See [COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-api-comparison-2024/COMPLETE_VERIFICATION_REPORT.md) for comprehensive template including:
- Executive Summary
- Testing Methodology
- Test Results with Evidence
- Field Comparison Tables
- API Behavior Documentation
- Implementation Guide
- Decision Rationale
- Evidence Files Index

---

## 🗂️ Related Files

- **[../README.md](../README.md)** - Project overview and usage guide
- **[../CLAUDE.md](../CLAUDE.md)** - Instructions for Claude Code when working with this codebase
- **[../render.yaml](../render.yaml)** - Deployment configuration

---

**Last Updated:** October 27, 2025
**Maintained By:** Project Team
**Questions?** See root [README.md](../README.md) or [CLAUDE.md](../CLAUDE.md)
