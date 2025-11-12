# Project Documentation Index

This folder contains organized technical documentation and decision records for the LinkedIn Profile AI Assessor project.

---

## 📂 Documentation Structure

```
docs/
├── README.md (this file)
├── QUICK_START.md
├── TESTING_GUIDE.md
├── SUPABASE_SCHEMA.sql
├── CORESIGNAL_MCP_SETUP.md
├── EXTENSION_API.md
│
├── sessions/                    # Session handoff documents (organized by date)
│   ├── nov-07/                  # November 7, 2025 sessions
│   ├── nov-10/                  # November 10, 2025 sessions
│   └── nov-11/                  # November 11, 2025 sessions
│
├── features/                    # Feature documentation and guides
│   ├── COMPANY_PRESCREENING_EXPLAINED.md
│   ├── COMPANY_RESEARCH_PIPELINE_VISUAL_FLOW.md
│   └── LOAD_MORE_VISUAL_GUIDE.md
│
├── integrations/                # Integration documentation
│   └── CORESIGNAL_ID_LOOKUP.md
│
├── architecture/                # Architecture designs and decisions
│   ├── SEARCH_SESSION_ARCHITECTURE.md
│   ├── SEARCH_SESSION_MANAGER_DESIGN.md
│   ├── DOMAIN_DISCOVERY_FLOW.md
│   ├── SOURCE_TRACKING_IMPLEMENTATION_PLAN.md
│   ├── scalability/             # Scalability strategies
│   │   ├── BEYOND_100_STRATEGY.md
│   │   └── VERIFIED_1000_STRATEGY.md
│   ├── pagination/              # Pagination strategies
│   │   ├── ID_FIRST_PAGINATION_STRATEGY.md
│   │   └── PAGINATION_IMPLEMENTATION_PLAN.md
│   └── batching/                # Batching implementations
│       ├── COMPANY_BATCHING_CHANGES.md
│       └── COMPANY_BATCHING_IMPLEMENTATION.md
│
├── database/                    # Database schemas and migrations
│   └── migrations/
│       ├── create_cached_searches_table.sql
│       ├── create_search_sessions_table.sql
│       └── migrate_search_sessions_add_pagination_fields.sql
│
├── completed/                   # Completed feature implementations
│   ├── CACHE_REFRESH_FEATURE_COMPLETE.md
│   ├── ENRICHED_COMPANY_SCORING_COMPLETE.md
│   ├── SSE_PROGRESS_MESSAGES_ADDED.md
│   ├── COMPANY_RELEVANCE_SCREENING_COMPLETE.md
│   ├── UI_GAPS_FIXED.md
│   ├── PHASE1_IMPLEMENTATION_COMPLETE.md
│   ├── READY_TO_TEST.md
│   ├── PIPELINE_FLOW_COMPLETE_GUIDE.md
│   ├── COMPANY_RESEARCH_IMPROVEMENTS.md
│   ├── CREDIT_AND_SOURCE_IMPLEMENTATION_SUMMARY.md
│   ├── PHASE_1_COMPANY_DISCOVERY.md
│   └── UI_INTEGRATION_STATUS.md
│
├── archived/                    # Historical documents and debugging artifacts
│   ├── debugging/               # Solved problem root cause analyses
│   │   ├── DOMAIN_SEARCH_0_EMPLOYEES_ROOT_CAUSE.md
│   │   ├── DOMAIN_SEARCH_DEBUGGING_SUMMARY.md
│   │   ├── FINAL_DIAGNOSIS_AND_SOLUTION.md
│   │   ├── PAGINATION_LIMITATION_DISCOVERY.md
│   │   └── EXPERIENCE_BASED_SEARCH_SOLUTION.md
│   ├── DOMAIN_SEARCH_PIPELINE_OLD.md
│   ├── CREDIT_OPTIMIZATION_SUMMARY.md
│   └── SYNTHFLOW_COMPANIES_ANALYSIS.md
│
├── technical-decisions/         # Architecture Decision Records
│   ├── WHY_SEARCH_API_DOESNT_WORK.md
│   └── company-base-vs-clean/
│       ├── COMPLETE_VERIFICATION_REPORT.md (Master document)
│       ├── FINAL_RECOMMENDATION.md (Executive summary)
│       ├── COMPARISON_MATRIX.csv
│       └── evidence/ (60 JSON test files from 26 companies)
│
├── evidence/                    # CoreSignal API evaluation data
│   ├── coresignal_multi_source_employee_data_dictionary.md
│   └── coresignal_search_api_reference.md
│
├── reverse-engineering/         # Case studies & analysis
│   └── (Voice AI role analysis - 68 candidates)
│
└── chrome-extension/            # Chrome extension documentation
    └── (Extension API and integration guides)
```

---

## 🎯 Quick Start

### For New Team Members:
1. Read [../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md](../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md) - Complete pipeline overview
2. Read [technical-decisions/company-base-vs-clean/COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-base-vs-clean/COMPLETE_VERIFICATION_REPORT.md) - Company API analysis
3. Read [WHY_SEARCH_API_DOESNT_WORK.md](technical-decisions/WHY_SEARCH_API_DOESNT_WORK.md) - Why we use Collect API
4. Review [SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql) for database structure

### For Understanding the Current System:
- **Pipeline Flow:** [../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md](../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md)
- **Company Research:** [features/COMPANY_PRESCREENING_EXPLAINED.md](features/COMPANY_PRESCREENING_EXPLAINED.md)
- **CoreSignal Integration:** [integrations/CORESIGNAL_ID_LOOKUP.md](integrations/CORESIGNAL_ID_LOOKUP.md)

### For Debugging Issues:
1. Check [archived/debugging/](archived/debugging/) for similar solved problems
2. Review [technical-decisions/](technical-decisions/) for API behavior documentation
3. Consult [sessions/](sessions/) for recent implementation context

---

## 📚 Key Documents

### Core Pipeline Documentation
- **[DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md](../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md)** (root)
  - Complete 10-step data flow from user input to UI rendering
  - All endpoints, APIs, input/output schemas
  - Field mappings and recent fixes
  - Performance analysis and troubleshooting

### Database & Schema
- **[SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql)** - Complete database schema:
  - `stored_profiles` - Profile caching
  - `stored_companies` - Company data caching
  - `candidate_assessments` - AI assessment results
  - `recruiter_feedback` - Feedback notes and ratings
  - `company_discovery_cache` - Domain search caching
  - `company_research_sessions` - Search session management

### Feature Guides
- **[features/COMPANY_PRESCREENING_EXPLAINED.md](features/COMPANY_PRESCREENING_EXPLAINED.md)**
  - How Claude Haiku 4.5 screening works
  - Web search integration
  - Scoring methodology

- **[features/COMPANY_RESEARCH_PIPELINE_VISUAL_FLOW.md](features/COMPANY_RESEARCH_PIPELINE_VISUAL_FLOW.md)**
  - Visual flow diagrams for company research
  - Multi-stage pipeline explanation

### Integration Documentation
- **[integrations/CORESIGNAL_ID_LOOKUP.md](integrations/CORESIGNAL_ID_LOOKUP.md)**
  - 4-tier CoreSignal ID lookup strategy
  - UI features and retroactive lookup
  - Implementation details

### Architecture Decisions

#### Company API Selection (October 2024)
**Decision:** Use `company_base` API endpoint exclusively

**Documents:**
- **[technical-decisions/company-base-vs-clean/COMPLETE_VERIFICATION_REPORT.md](technical-decisions/company-base-vs-clean/COMPLETE_VERIFICATION_REPORT.md)** (400+ lines)
  - Complete testing methodology across 26 companies
  - Field-by-field comparison of all three endpoints
  - Crunchbase URL availability analysis (69.2% coverage)
  - Implementation guide with Python + React examples

- **[technical-decisions/company-base-vs-clean/FINAL_RECOMMENDATION.md](technical-decisions/company-base-vs-clean/FINAL_RECOMMENDATION.md)**
  - Executive summary and decision rationale
  - Trade-offs and risk assessment

**Key Findings:**
- `company_base`: 100% availability, 69.2% Crunchbase URL coverage
- `company_clean`: 60% funding_rounds coverage
- Nested collections vs. flattened arrays

#### Scalability Strategies
**Documents:**
- **[architecture/scalability/BEYOND_100_STRATEGY.md](architecture/scalability/BEYOND_100_STRATEGY.md)**
- **[architecture/scalability/VERIFIED_1000_STRATEGY.md](architecture/scalability/VERIFIED_1000_STRATEGY.md)**

Strategies for scaling company discovery beyond 100 and up to 1000+ companies.

---

## 🗂️ Directory Guide

### `sessions/`
Historical session handoff documents organized by date. These document what was accomplished in each development session, what problems were solved, and what to work on next.

- **nov-07/** - Initial company research improvements
- **nov-10/** - CoreSignal ID integration, experience-based search
- **nov-11/** - Claude Haiku screening, enriched companies

### `features/`
Feature-specific documentation explaining how major features work.

### `integrations/`
Documentation for third-party integrations (CoreSignal, Tavily, etc.).

### `architecture/`
Architecture designs, technical strategies, and system design documents.

- **scalability/** - Strategies for scaling to 100+ and 1000+ companies
- **pagination/** - Pagination implementation strategies
- **batching/** - Batch processing designs

### `database/`
Database schemas and migration scripts.

### `completed/`
Summaries of completed feature implementations. Useful for understanding what was built and why.

### `archived/`
Historical documents and solved debugging artifacts. Kept for reference but no longer actively maintained.

- **debugging/** - Root cause analyses for problems that have been solved

### `technical-decisions/`
Architecture Decision Records (ADRs) documenting major technical choices.

---

## 🔍 Key Technical Decisions Summary

### 1. Company Data Enrichment
- **API Endpoint:** `company_base` (NOT `company_clean` or `company_multi_source`)
- **Field Priority:** `company_crunchbase_info_collection[0].cb_url` for Crunchbase URLs
- **Optimization:** Only enrich companies from jobs starting 2020+ (saves 60-80% API credits)
- **Fallback Chain:** 4-tier hybrid strategy with Tavily + Claude WebSearch

### 2. Company Screening
- **Model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
- **Tool:** Anthropic Web Search (`web_search_20250305`)
- **Output:** `relevance_score` (1-10), `screening_reasoning`, `scored_by`

### 3. Profile Data Fetching
- **API:** CoreSignal Employee Collect API (2-step: search by URL → fetch by ID)
- **Headline:** Prefer `generated_headline` over `headline` field
- **Optimization:** Session-based caching to avoid duplicate API calls

### 4. Domain Search Pipeline
- **Endpoint:** `/api/jd/domain-company-preview-search`
- **CoreSignal:** `/v2/employee_clean/search/es_dsl/preview`
- **Query:** ES DSL with MUST (company) + SHOULD (role)
- **Performance:** 2-5 minutes, ~$1.90 fresh / ~$0.57 cached

---

## 🛠️ Setup Guides

### CoreSignal MCP Server
**Document:** [CORESIGNAL_MCP_SETUP.md](CORESIGNAL_MCP_SETUP.md)

Instructions for integrating CoreSignal API via Model Context Protocol (MCP) server for Claude Code.

### Extension API
**Document:** [EXTENSION_API.md](EXTENSION_API.md)

API documentation for browser extension integration.

### Testing Guide
**Document:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

Testing procedures for API integration, data validation, and quality assurance.

---

## 📝 Document Maintenance Guidelines

### When to Add New Documents

**Session Handoffs (→ sessions/):**
- End-of-session summaries
- What was accomplished
- What to work on next
- Format: Date, Status, Accomplishments, Next Steps

**Feature Documentation (→ features/):**
- Major feature explanations
- User-facing functionality
- How it works guides
- Format: Overview, How It Works, Implementation, Examples

**Technical Decisions (→ technical-decisions/):**
- Significant architectural choices
- API or technology comparisons
- Core data source changes
- Format: Problem → Options → Decision → Rationale → Evidence

**Architecture (→ architecture/):**
- System design documents
- Scalability strategies
- Technical architecture patterns
- Format: Context, Design, Trade-offs, Implementation

**Completed Features (→ completed/):**
- Implementation summaries
- Feature completion announcements
- What was built and why
- Format: Summary, Changes, Testing, Next Steps

### Archiving Old Documents

Documents should be moved to `archived/` when:
- They describe problems that have been solved
- They document debugging sessions for resolved issues
- They are superseded by newer, more comprehensive docs
- They are no longer relevant to current architecture

---

## 🗂️ Related Files

- **[../README.md](../README.md)** - Project overview and usage guide
- **[../CLAUDE.md](../CLAUDE.md)** - Instructions for Claude Code when working with this codebase
- **[../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md](../DOMAIN_SEARCH_PIPELINE_DOCUMENTATION.md)** - Complete pipeline reference
- **[../RESEARCH_SESSION_WORKFLOW.md](../RESEARCH_SESSION_WORKFLOW.md)** - Session workflow reference
- **[../RESEARCH_SESSION_QUICK_REFERENCE.md](../RESEARCH_SESSION_QUICK_REFERENCE.md)** - Quick lookup table

---

**Last Updated:** November 11, 2025
**Documentation Reorganization:** Completed Nov 11, 2025 - Consolidated 140+ files into organized structure
**Maintained By:** Project Team
**Questions?** See root [README.md](../README.md) or [CLAUDE.md](../CLAUDE.md)
