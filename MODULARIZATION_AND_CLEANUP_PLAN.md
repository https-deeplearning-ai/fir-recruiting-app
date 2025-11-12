# Documentation Cleanup & Codebase Modularization Plan

**Created:** 2025-11-12
**Status:** Ready for Execution
**Branch Strategy:** Execute on separate branch
**Estimated Duration:** 6 days

---

## Executive Summary

This plan addresses two critical objectives for repository health and maintainability:

1. **Documentation Cleanup:** Remove 49+ outdated files (session handoffs, debug notes, checkpoint summaries) from 138 total documentation files
2. **Codebase Modularization:** Reorganize monolithic codebase into feature-domain modules with MCP server preparation

### Key Outcomes

- **Documentation:** 138 files → 60 relevant files (49 deleted, 23 archived)
- **app.py:** 3,887 lines → ~200 lines (98% reduction)
- **Architecture:** Monolithic → Feature-domain organization (50+ well-organized files)
- **MCP Ready:** Centralized prompts, API docs, and tools for Claude Code optimization

---

## Part 1: Documentation Audit & Cleanup

### Current State: 138 Documentation Files

**Breakdown:**
- ✅ **Keep (Current):** ~50 files - Accurate, relevant documentation
- ⚠️ **Review/Update:** ~15 files - Mix of current and obsolete info
- ❌ **Remove (Outdated):** ~50 files - Session notes, checkpoints, debug files
- 📄 **Archive (Historical):** ~23 files - Session handoffs for reference

### Files to Delete (49 files)

#### Root Directory (16 files)

**Session Handoff Documents:**
- `FINAL_SESSION_HANDOFF_NOV_10_2025.md` (11K)
- `SESSION_HANDOFF_NOV_10_2025.md` (9.2K)
- `SESSION_HANDOFF_NOV_10_SESSION_2.md` (11K)
- `SESSION_HANDOFF_NOV_11_2025_ENRICHED_COMPANIES.md` (20K)
- `NEXT_SESSION_HANDOVER.md` (16K)
- `HANDOFF_CURRENT.md` (11K)

**Feature Complete/Summary Documents:**
- `CACHE_REFRESH_FEATURE_COMPLETE.md` (7.4K)
- `COMPANY_RELEVANCE_SCREENING_COMPLETE.md` (2.4K)
- `ENRICHED_COMPANY_SCORING_COMPLETE.md` (8.4K)
- `SSE_PROGRESS_MESSAGES_ADDED.md` (8.1K)
- `CREDIT_OPTIMIZATION_SUMMARY.md` (4.5K)

**Integration Handoffs:**
- `HANDOFF_COMPANY_RESEARCH_IMPROVEMENTS.md` (14K)
- `HANDOFF_CORESIGNAL_ID_LOOKUP_INTEGRATION.md` (20K)
- `UI_FEATURE_RETROACTIVE_ID_LOOKUP.md` (14K)
- `UI_GAPS_FIXED.md` (6.1K)

**Research/Investigation:**
- `COMPANY_PRESCREENING_EXPLAINED.md` (15K)

#### Backend Directory (17 files)

**Debugging/Investigation Documents:**
- `backend/DOMAIN_SEARCH_0_EMPLOYEES_ROOT_CAUSE.md`
- `backend/DOMAIN_SEARCH_DEBUGGING_SUMMARY.md`
- `backend/EXPERIENCE_BASED_SEARCH_SOLUTION.md`
- `backend/FINAL_DIAGNOSIS_AND_SOLUTION.md`
- `backend/FINAL_INTEGRATION_GUIDE.md`
- `backend/INTEGRATION_EVIDENCE_NOV_10_2025.md`
- `backend/SYNTHFLOW_COMPANIES_ANALYSIS.md`

**Handoff Documents:**
- `backend/HANDOFF_CLAUDE_HAIKU_SCREENING_NOV_11.md`
- `backend/NEXT_SESSION_HANDOVER.md`
- `backend/SESSION_COMPLETE_SUMMARY.md`
- `backend/SESSION_INTEGRATION_HANDOVER.md`
- `backend/EXPERIENCE_SEARCH_INTEGRATION_HANDOVER.md`

**Feature Complete Documents:**
- `backend/PHASE1_IMPLEMENTATION_COMPLETE.md`
- `backend/READY_TO_TEST.md`
- `backend/SESSION_PROGRESS_UI_INTEGRATION.md`
- `backend/PAGINATION_LIMITATION_DISCOVERY.md`
- `backend/CODEBASE_AUDIT_NOV_11_2025.md`

#### Backend/Docs Directory (12 files)

**Planning Documents:**
- `backend/docs/PAGINATION_IMPLEMENTATION_PLAN.md`
- `backend/docs/ID_FIRST_PAGINATION_STRATEGY.md`
- `backend/docs/BEYOND_100_STRATEGY.md`
- `backend/docs/VERIFIED_1000_STRATEGY.md`
- `backend/docs/SOURCE_TRACKING_IMPLEMENTATION_PLAN.md`
- `backend/docs/COMPANY_BATCHING_IMPLEMENTATION.md`

**Architecture Documents:**
- `backend/docs/SEARCH_SESSION_ARCHITECTURE.md`
- `backend/docs/SEARCH_SESSION_MANAGER_DESIGN.md`
- `backend/docs/DOMAIN_DISCOVERY_FLOW.md`
- `backend/docs/UI_INTEGRATION_STATUS.md`

**Change Summaries:**
- `backend/docs/COMPANY_BATCHING_CHANGES.md`
- `backend/docs/CREDIT_AND_SOURCE_IMPLEMENTATION_SUMMARY.md`

#### Root Directory - Consolidate Then Archive (4 files)

**Extract key info first, then archive:**
- `PIPELINE_IMPROVEMENTS_SUMMARY.md` (12K) - Extract architecture notes
- `RESEARCH_SESSION_WORKFLOW.md` (24K) - Extract workflow diagrams
- `RESEARCH_SESSION_QUICK_REFERENCE.md` (9.9K) - Consolidate into permanent docs
- `DOCS_TO_UPDATE.md` (4.4K) - Meta doc, delete after review

### Files to Keep (Core Documentation)

#### Essential Core Docs
- ✅ `CLAUDE.md` - Project instructions (must update after modularization)
- ✅ `README.md` - Project overview
- ✅ `PROJECT_STATUS.md` - Current status (may need updates)
- ✅ `docs/README.md` - Documentation index
- ✅ `docs/QUICK_START.md`
- ✅ `docs/TESTING_GUIDE.md`
- ✅ `docs/SUPABASE_SCHEMA.sql` - Critical database schema

#### Technical Reference
- ✅ `docs/technical-decisions/` - All ADRs
- ✅ `docs/evidence/` - All evidence files
- ✅ `docs/reverse-engineering/` - Case studies
- ✅ `backend/jd_analyzer/docs/CORESIGNAL_FIELD_REFERENCE.md`

#### Feature Documentation
- ✅ `docs/JD_ANALYZER_INTEGRATION.md`
- ✅ `docs/JD_ANALYZER_PROMPT_ANALYSIS.md`
- ✅ `docs/COMPETITIVE_INTELLIGENCE_TRANSFORMATION.md`
- ✅ `docs/COMPANY_RESEARCH_USER_FLOW.md`
- ✅ `docs/chrome-extension/` - All files

#### Module Docs
- ✅ `backend/jd_analyzer/README.md`
- ✅ `frontend/README.md`

---

## Part 2: Codebase Modularization

### Current Architecture Analysis

#### Files Over 1000 Lines (Candidates for Splitting)

| File | Lines | Status | Action |
|------|-------|--------|--------|
| **app.py** | 3,887 | Monolithic | Split into 8 feature domains |
| **jd_analyzer/api/domain_search.py** | 2,491 | Large | Split routes from logic |
| **company_research_service.py** | 2,001 | Large | Split into discovery/evaluation/screening |
| **coresignal_service.py** | 1,798 | Large | Split into employee/company/search modules |
| **jd_analyzer/api/endpoints.py** | 1,520 | Large | Rename to routes.py, keep structure |
| **jd_analyzer/query/llm_query_generator.py** | 1,089 | Large | Keep as-is (single responsibility) |

#### app.py Responsibilities (3,887 lines - CRITICAL TO SPLIT)

**Routes & Functions:** 60+ functions, 40+ routes

1. **Profile Management** (Lines 1275-1700)
   - `/fetch-profile` - Fetch LinkedIn profiles from CoreSignal
   - `/fetch-profile-by-id/<employee_id>` - Fetch by employee ID
   - `/assess-profile` - AI assessment with Claude
   - `/batch-assess-profiles` - Parallel batch processing
   - `assess_single_profile_sync()` - Sync profile assessment
   - `extract_profile_summary()` - Parse CoreSignal JSON
   - `generate_assessment_prompt()` - Build Claude prompts (130 lines!)

2. **Database Operations** (Lines 171-265)
   - `save_candidate_assessment()` - Save to Supabase
   - `save_to_supabase_api()` - Supabase REST API wrapper
   - `load_candidate_assessments()` - Load from database
   - `load_from_supabase_api()` - Supabase GET wrapper

3. **Storage/Caching** (Lines 270-610)
   - `get_stored_profile()` - Profile freshness logic (3-90 days)
   - `save_stored_profile()` - Store profile data
   - `get_stored_company()` - Company caching (30 days)
   - `save_stored_company()` - Store company data
   - `get_cached_search_results()` - Search result caching
   - `save_search_results()` - Cache search results

4. **Search** (Lines 613-925)
   - `/search-profiles` - Natural language profile search
   - `process_user_prompt_for_search()` - Claude AI extraction (EMBEDDED PROMPT)
   - `build_intelligent_elasticsearch_query()` - Build CoreSignal queries
   - `search_coresignal_profiles_preview()` - Execute searches
   - `convert_search_results_to_csv()` - CSV export

5. **Recruiter Feedback** (Lines 2063-2200)
   - `/save-feedback` - Save recruiter notes
   - `/get-feedback/<linkedin_url>` - Load feedback history
   - `/clear-feedback` - Clear feedback

6. **Company Research** (Lines 2991-3650)
   - `/research-companies` - Company discovery endpoint
   - `/evaluate-more-companies` - Progressive evaluation
   - `/research-companies/<jd_id>/status` - Status polling
   - `/research-companies/<jd_id>/stream` - SSE streaming
   - `/research-companies/<jd_id>/results` - Get results
   - `/research-companies/<jd_id>/export-csv` - CSV export
   - `/company-lists` - Save/get company lists

7. **Chrome Extension** (Lines 2513-2850)
   - `/extension/lists` - List management
   - `/extension/create-list` - Create list
   - `/extension/lists/<list_id>` - Update/delete list
   - `/extension/add-profile` - Add profile to list
   - `/lists/<list_id>/assess` - Assess entire list
   - `/lists/<list_id>/export-csv` - Export list to CSV

8. **Crunchbase URL Management** (Lines 2202-2512)
   - `/regenerate-crunchbase-url` - Claude Agent SDK validation
   - `/verify-crunchbase-url` - Manual validation

### Identified Feature Domains

Based on codebase analysis, here are the natural feature boundaries:

1. **profile/** - Profile fetching, assessment, batch processing, summary extraction
2. **company/** - Company discovery, evaluation, enrichment, research orchestration
3. **search/** - Profile search, query building, natural language processing, CSV export
4. **jd_analyzer/** - Already modular! JD parsing, weight generation, shortlist analysis
5. **feedback/** - Recruiter feedback CRUD operations, history
6. **extension/** - Chrome extension integration, list management, quick add
7. **database/** - Supabase operations, caching, storage with freshness logic
8. **coresignal/** - CoreSignal API client (employee, company, search)
9. **ai/** - AI clients and prompt templates (NEW - centralize all prompts)

### Target Modular Structure

```
backend/
├── app.py (NEW - 200 lines max)
│   ├── Flask app initialization
│   ├── Blueprint registration
│   ├── Static file serving
│   └── Health check endpoint
│
├── config.py (KEEP - 68 lines)
│   └── Deployment configuration
│
├── profile/  (NEW DOMAIN)
│   ├── __init__.py
│   ├── routes.py - Profile endpoints blueprint
│   ├── assessment.py - AI assessment logic
│   ├── summary.py - Profile summary extraction
│   └── batch.py - Batch processing
│
├── company/  (CONSOLIDATE EXISTING FILES)
│   ├── __init__.py
│   ├── routes.py - Company research endpoints
│   ├── discovery.py - Company discovery (web search, competitors)
│   ├── evaluation.py - AI evaluation (screening, deep research)
│   ├── screening.py - Batch screening logic
│   └── enrichment.py - CoreSignal enrichment
│
├── search/  (NEW DOMAIN)
│   ├── __init__.py
│   ├── routes.py - Search endpoints
│   ├── query_builder.py - Elasticsearch DSL
│   ├── natural_language.py - NL to criteria extraction
│   └── export.py - CSV export
│
├── jd_analyzer/  (REFINE EXISTING - Already well-organized!)
│   ├── api/
│   │   ├── routes.py (Rename from endpoints.py)
│   │   └── domain_search_routes.py (Split from domain_search.py)
│   ├── core/ - Parsing, weights, models (KEEP)
│   ├── query/ - Query generation (KEEP)
│   ├── company/ - Company agents (KEEP)
│   └── utils/ - Utilities (KEEP)
│
├── feedback/  (NEW DOMAIN)
│   ├── __init__.py
│   ├── routes.py - Feedback endpoints
│   └── service.py - Feedback operations
│
├── extension/  (NEW DOMAIN)
│   ├── __init__.py
│   ├── routes.py - Extension endpoints
│   └── service.py - Extension operations (move from extension_service.py)
│
├── database/  (NEW - CENTRALIZE ALL SUPABASE OPS)
│   ├── __init__.py
│   ├── supabase_client.py - Shared client with retry logic
│   ├── assessments.py - Assessment CRUD
│   ├── profiles.py - Profile storage with freshness logic
│   ├── companies.py - Company storage (30-day cache)
│   ├── search_cache.py - Search result caching (7 days)
│   ├── feedback.py - Feedback CRUD
│   └── schema.py - Schema documentation for MCP
│
├── coresignal/  (REFACTOR EXISTING)
│   ├── __init__.py
│   ├── client.py - Main client class (refactored)
│   ├── employee.py - Employee API methods
│   ├── company.py - Company API methods
│   ├── search.py - Search API methods
│   ├── taxonomy.py - Field mappings (move from coresignal_api_taxonomy.py)
│   └── retry.py - Retry logic
│
├── ai/  (NEW - CENTRALIZE ALL PROMPTS)
│   ├── __init__.py
│   ├── claude_client.py - Anthropic client wrapper
│   ├── gpt_client.py - OpenAI client (move from gpt5_client.py)
│   └── prompts/
│       ├── __init__.py
│       ├── profile_assessment.py - Profile assessment prompts
│       ├── search_extraction.py - Search criteria extraction prompts
│       ├── company_evaluation.py - Company screening/evaluation prompts
│       ├── jd_parsing.py - JD parsing prompts
│       └── crunchbase_validation.py - URL validation prompts
│
├── utils/  (KEEP & REFINE)
│   ├── __init__.py
│   ├── search_session.py (KEEP - 583 lines)
│   ├── session_logger.py (KEEP)
│   ├── timestamp.py (NEW - Move safe_parse_timestamp)
│   └── formatting.py (NEW - Move format_company_intelligence)
│
├── mcp/  (NEW - MCP SERVER FOR CLAUDE CODE)
│   ├── __init__.py
│   ├── server.py - MCP server entrypoint
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── api_docs.py - 40+ API endpoint documentation
│   │   ├── database_schema.py - 8 Supabase tables
│   │   ├── field_mappings.py - CoreSignal field taxonomy
│   │   └── prompts_catalog.py - Prompt templates registry
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py - Parameterized prompt templates
│   └── tools/
│       ├── __init__.py
│       ├── profile_tools.py - Profile fetch/assess operations
│       ├── search_tools.py - Search operations
│       └── research_tools.py - Company research operations
│
└── tests/  (REORGANIZE)
    ├── test_profile.py
    ├── test_company.py
    ├── test_search.py
    ├── test_jd_analyzer.py
    ├── test_feedback.py
    ├── test_extension.py
    ├── test_database.py
    ├── test_coresignal.py
    └── test_mcp.py
```

---

## Detailed Migration Map

### From app.py (3,887 lines → ~200 lines)

#### To profile/routes.py (Lines 1275-1953)
```python
# Profile endpoints
- Lines 1275-1390: POST /fetch-profile
- Lines 1390-1479: GET /fetch-profile-by-id/<employee_id>
- Lines 1479-1622: POST /assess-profile
- Lines 1703-1900: POST /batch-assess-profiles
- Lines 1900-1938: POST /save-assessment
- Lines 1938-1953: GET /load-assessments
```

#### To profile/assessment.py
```python
# Assessment logic
- Lines 1623-1703: assess_single_profile_sync()
```

#### To profile/summary.py
```python
# Profile summary extraction
- Lines 925-1048: extract_profile_summary()
```

#### To ai/prompts/profile_assessment.py
```python
# Profile assessment prompt (130 lines!)
- Lines 1143-1273: generate_assessment_prompt()
```

#### To search/routes.py
```python
# Search endpoints
- Lines 1954-2063: POST /search-profiles
- Lines 3752-3887: POST /search-by-company-list
```

#### To search/natural_language.py
```python
# NL to search criteria
- Lines 613-698: process_user_prompt_for_search() (contains embedded prompt!)
```

#### To search/query_builder.py
```python
# Query building
- Lines 698-856: build_intelligent_elasticsearch_query()
- Lines 856-902: search_coresignal_profiles_preview()
```

#### To search/export.py
```python
# CSV export
- Lines 902-925: convert_search_results_to_csv()
```

#### To feedback/routes.py
```python
# Feedback endpoints
- Lines 2063-2120: POST /save-feedback
- Lines 2120-2161: GET /get-feedback/<linkedin_url>
- Lines 2161-2202: POST /clear-feedback
```

#### To company/routes.py
```python
# Company research endpoints
- Lines 2991-3129: POST /research-companies
- Lines 3129-3182: POST /evaluate-more-companies
- Lines 3182-3220: GET /research-companies/<jd_id>/status
- Lines 3220-3363: GET /research-companies/<jd_id>/stream (SSE)
- Lines 3363-3491: GET /research-companies/<jd_id>/results
- Lines 3491-3514: POST /research-companies/<jd_id>/reset
- Lines 3514-3582: GET /research-companies/<jd_id>/export-csv
- Lines 3582-3647: POST /company-lists
- Lines 3647-3667: GET /company-lists
- Lines 3667-3697: GET /company-lists/<int:list_id>
- Lines 3697-3717: DELETE /company-lists/<int:list_id>

# Crunchbase URL endpoints
- Lines 2202-2402: POST /regenerate-crunchbase-url
- Lines 2402-2513: POST /verify-crunchbase-url
```

#### To extension/routes.py
```python
# Extension endpoints
- Lines 2513-2524: GET /extension/lists
- Lines 2524-2546: POST /extension/create-list
- Lines 2546-2560: PUT /extension/lists/<list_id>
- Lines 2560-2573: DELETE /extension/lists/<list_id>
- Lines 2573-2586: GET /extension/lists/<list_id>/stats
- Lines 2586-2611: POST /extension/add-profile
- Lines 2611-2635: GET /extension/profiles/<list_id>
- Lines 2635-2654: PUT /extension/profiles/<profile_id>/status
- Lines 2654-2674: GET /extension/auth
- Lines 2674-2824: POST /lists/<list_id>/assess
- Lines 2824-2967: GET /lists/<list_id>/export-csv
```

#### To database/assessments.py
```python
# Assessment database operations
- Lines 171-173: save_candidate_assessment()
- Lines 176-229: save_to_supabase_api()
- Lines 230-232: load_candidate_assessments()
- Lines 235-265: load_from_supabase_api()
```

#### To database/profiles.py
```python
# Profile storage with freshness logic
- Lines 270-328: get_stored_profile() (3-90 day freshness!)
- Lines 329-379: get_stored_profile_by_employee_id()
- Lines 380-422: save_stored_profile()
```

#### To database/companies.py
```python
# Company storage (30-day cache)
- Lines 423-479: get_stored_company()
- Lines 480-507: save_stored_company()
```

#### To database/search_cache.py
```python
# Search result caching (7 days)
- Lines 520-538: generate_search_cache_key()
- Lines 539-578: get_cached_search_results()
- Lines 579-612: save_search_results()
```

#### To utils/timestamp.py
```python
# Timestamp utilities
- Lines 32-76: safe_parse_timestamp()
```

#### To utils/formatting.py
```python
# Data formatting
- Lines 1048-1143: format_company_intelligence()
```

#### To database/supabase_client.py
```python
# Centralize Supabase config
- Lines 157-160: SUPABASE_URL, SUPABASE_KEY
```

### From jd_analyzer/api/domain_search.py (2,491 lines)

**Split into:**
- `jd_analyzer/api/domain_search_routes.py` (~300 lines) - Blueprint registration only
- `company/discovery.py` - Move company discovery logic
- `search/candidate_search.py` - Move candidate search logic
- `ai/prompts/candidate_evaluation.py` - Extract embedded prompts

### From company_research_service.py (2,001 lines)

**Split into:**
- `company/research_service.py` (~500 lines) - Main orchestration
- `company/discovery.py` (~400 lines) - Discovery methods (web search, competitors)
- `company/evaluation.py` (~400 lines) - AI evaluation (deep research)
- `company/screening.py` (~300 lines) - Batch screening with GPT-5/Claude Haiku
- `ai/prompts/company_evaluation.py` (~200 lines) - Extract all prompts

### From coresignal_service.py (1,798 lines)

**Split into:**
- `coresignal/client.py` (~200 lines) - Main client class
- `coresignal/employee.py` (~400 lines) - Employee API methods
- `coresignal/company.py` (~300 lines) - Company API methods
- `coresignal/search.py` (~500 lines) - Search API methods
- `coresignal/retry.py` (~100 lines) - Retry logic

---

## MCP Server Structure

### Purpose
Enable Claude Code to efficiently access:
1. **API endpoint documentation** (40+ routes)
2. **Database schema** (8 Supabase tables)
3. **AI prompt templates** (5 major categories)
4. **CoreSignal API patterns** (field mappings, query structures)

### MCP Resources (Read-Only Knowledge)

#### 1. API Endpoint Documentation
```python
# mcp/resources/api_docs.py
"""
Exposes all 40+ API endpoints with request/response schemas
"""

ENDPOINTS = {
    "profile": {
        "fetch_profile": {
            "method": "POST",
            "path": "/fetch-profile",
            "description": "Fetch LinkedIn profile from CoreSignal",
            "request_schema": {
                "linkedin_url": "string (required)",
                "enrich_companies": "boolean (optional, default: true)"
            },
            "response_schema": {
                "profile_data": "object",
                "company_intelligence": "array"
            }
        },
        # ... all profile endpoints
    },
    "search": {...},
    "company": {...},
    "jd_analyzer": {...},
    "feedback": {...},
    "extension": {...}
}
```

#### 2. Database Schema Documentation
```python
# mcp/resources/database_schema.py
"""
Exposes all 8 Supabase tables with field definitions
"""

TABLES = {
    "candidate_assessments": {
        "description": "Stores LinkedIn profile assessments",
        "fields": {
            "linkedin_url": "text (primary key)",
            "profile_data": "jsonb",
            "assessment_data": "jsonb",
            "weighted_score": "numeric",
            # ... all fields
        },
        "indexes": ["linkedin_url", "weighted_score"],
        "freshness": "No expiry (permanent storage)"
    },
    "stored_profiles": {
        "description": "Cached LinkedIn profiles with freshness logic",
        "fields": {...},
        "freshness": "3-90 days based on seniority"
    },
    # ... all 8 tables
}
```

#### 3. CoreSignal Field Mappings
```python
# mcp/resources/field_mappings.py
"""
Exposes CoreSignal API field taxonomy and mappings
"""

EMPLOYEE_FIELDS = {
    "websites_professional_network": "LinkedIn URL (exact match)",
    "generated_headline": "Auto-generated headline (FRESH)",
    "headline": "User-set headline (STALE)",
    "experiences": "Work history array",
    # ... all employee fields
}

COMPANY_FIELDS = {
    "company_base": {
        "total_fields": 45,
        "description": "Granular company structure with nested collections",
        "key_fields": [
            "company_crunchbase_info_collection",
            "funding_rounds",
            "locations",
            # ...
        ]
    }
}

SEARCH_QUERY_PATTERNS = {
    "by_url": "websites_professional_network.exact",
    "by_experience": "experiences.company_id",
    "by_title": "experiences.title",
    # ...
}
```

#### 4. Prompt Templates Catalog
```python
# mcp/resources/prompts_catalog.py
"""
Registry of all AI prompt templates with parameters
"""

PROMPT_TEMPLATES = {
    "profile_assessment": {
        "model": "claude-sonnet-4-5-20250929",
        "temperature": 0.1,
        "description": "Assess LinkedIn profile against weighted criteria",
        "parameters": [
            "profile_summary",
            "assessment_criteria",
            "weighted_requirements",
            "company_analysis_guidance"
        ],
        "output_format": "JSON with scores and analysis"
    },
    "search_extraction": {
        "model": "claude-sonnet-4-5-20250929",
        "temperature": 0.2,
        "description": "Extract search criteria from natural language",
        "parameters": ["user_query"],
        "output_format": "JSON with CoreSignal query structure"
    },
    # ... all 5 prompt categories
}
```

### MCP Prompts (Reusable Templates)

```python
# mcp/prompts/templates.py
"""
Parameterized prompt templates for reuse
"""

@mcp_server.prompt("assess_profile")
def get_assessment_prompt(
    profile_summary: dict,
    criteria: str,
    weights: list
) -> str:
    """Generate profile assessment prompt"""
    return PROFILE_ASSESSMENT_PROMPT.format(
        profile_summary=format_profile(profile_summary),
        assessment_criteria=criteria,
        weighted_section=format_weights(weights),
        company_analysis_guidance=COMPANY_GUIDANCE
    )

@mcp_server.prompt("extract_search_criteria")
def get_search_prompt(user_query: str) -> str:
    """Generate search extraction prompt"""
    return SEARCH_EXTRACTION_PROMPT.format(
        user_query=user_query,
        taxonomy=CORESIGNAL_TAXONOMY
    )

# ... all 5 prompt types
```

### MCP Tools (Executable Operations)

```python
# mcp/tools/profile_tools.py
"""
Executable profile operations
"""

@mcp_server.tool("fetch_linkedin_profile")
async def fetch_profile(
    linkedin_url: str,
    enrich_companies: bool = True
) -> dict:
    """Fetch LinkedIn profile from CoreSignal with company enrichment"""
    from profile.routes import fetch_profile_logic
    return await fetch_profile_logic(linkedin_url, enrich_companies)

@mcp_server.tool("assess_profile")
async def assess_profile(
    profile_data: dict,
    criteria: str,
    weights: list
) -> dict:
    """Assess LinkedIn profile using AI"""
    from profile.assessment import assess_profile_logic
    return await assess_profile_logic(profile_data, criteria, weights)

# mcp/tools/search_tools.py
@mcp_server.tool("search_profiles")
async def search_profiles(
    query: str,
    limit: int = 100
) -> dict:
    """Natural language profile search"""
    from search.routes import search_profiles_logic
    return await search_profiles_logic(query, limit)

# mcp/tools/research_tools.py
@mcp_server.tool("research_companies")
async def research_companies(
    jd_context: dict,
    num_companies: int = 100
) -> dict:
    """Discover and research companies"""
    from company.routes import research_companies_logic
    return await research_companies_logic(jd_context, num_companies)
```

---

## Phased Execution Plan

### Day 1: Documentation Cleanup + Extract AI Prompts

#### Morning: Documentation Cleanup
1. **Delete session handoff docs from root** (16 files)
2. **Delete backend debug/investigation docs** (17 files)
3. **Delete backend/docs planning files** (12 files)
4. **Extract key info from summary docs** (4 files)
   - Read each file, extract unique architecture notes
   - Add relevant info to CLAUDE.md
   - Archive or delete

**Estimated Time:** 3-4 hours

#### Afternoon: Extract AI Prompts
1. **Create `backend/ai/` directory structure**
2. **Create `backend/ai/prompts/` module**
3. **Extract prompts from app.py:**
   - Profile assessment prompt (lines 1143-1273) → `profile_assessment.py`
   - Search extraction prompt (lines 627-675) → `search_extraction.py`
4. **Extract prompts from company_research_service.py:**
   - Screening prompts → `company_evaluation.py`
5. **Extract prompts from jd_analyzer/core/:**
   - JD parsing prompts → `jd_parsing.py`
6. **Move `gpt5_client.py` → `ai/gpt_client.py`**

**Estimated Time:** 3-4 hours

**Deliverables:**
- 49 files deleted
- `ai/prompts/` module created with 5 prompt files
- All prompts centralized

---

### Day 2: Create Database & Utils Modules

#### Morning: Database Module
1. **Create `backend/database/` directory**
2. **Create `database/supabase_client.py`**
   - Extract Supabase config from app.py (lines 157-160)
   - Create shared client class with retry logic
3. **Create `database/assessments.py`**
   - Move assessment CRUD from app.py (lines 171-265)
4. **Create `database/profiles.py`**
   - Move profile storage from app.py (lines 270-422)
   - Include freshness logic (3-90 days)
5. **Create `database/companies.py`**
   - Move company storage from app.py (lines 423-507)
6. **Create `database/search_cache.py`**
   - Move search caching from app.py (lines 520-612)
7. **Create `database/feedback.py`**
   - Move feedback CRUD (if needed)
8. **Create `database/schema.py`**
   - Document all 8 tables for MCP

**Estimated Time:** 4-5 hours

#### Afternoon: Utils Module
1. **Create `utils/timestamp.py`**
   - Move `safe_parse_timestamp()` from app.py (lines 32-76)
2. **Create `utils/formatting.py`**
   - Move `format_company_intelligence()` from app.py (lines 1048-1143)
3. **Verify existing utils:**
   - `search_session.py` (583 lines) - Keep as-is
   - `session_logger.py` - Keep as-is

**Estimated Time:** 1-2 hours

**Deliverables:**
- `database/` module with 7 files
- `utils/` module updated
- All database operations centralized

---

### Day 3: Split Profile, Search, Feedback, Extension Domains

#### Morning: Profile Domain
1. **Create `backend/profile/` directory**
2. **Create `profile/routes.py`**
   - Blueprint registration
   - All profile endpoints from app.py (lines 1275-1953)
3. **Create `profile/assessment.py`**
   - Move `assess_single_profile_sync()` (lines 1623-1703)
   - Use prompts from `ai/prompts/profile_assessment.py`
4. **Create `profile/summary.py`**
   - Move `extract_profile_summary()` (lines 925-1048)
5. **Create `profile/batch.py`**
   - Extract batch processing logic
6. **Update imports in app.py**

**Estimated Time:** 4-5 hours

#### Afternoon: Search, Feedback, Extension Domains

**Search Domain:**
1. **Create `backend/search/` directory**
2. **Create `search/routes.py`** - All search endpoints (lines 1954-2063, 3752-3887)
3. **Create `search/natural_language.py`** - NL extraction (lines 613-698)
4. **Create `search/query_builder.py`** - Query building (lines 698-902)
5. **Create `search/export.py`** - CSV export (lines 902-925)

**Feedback Domain:**
1. **Create `backend/feedback/` directory**
2. **Create `feedback/routes.py`** - Feedback endpoints (lines 2063-2202)
3. **Create `feedback/service.py`** - Business logic

**Extension Domain:**
1. **Create `backend/extension/` directory**
2. **Create `extension/routes.py`** - Extension endpoints (lines 2513-2967)
3. **Move `extension_service.py` → `extension/service.py`**

**Estimated Time:** 4-5 hours

**Deliverables:**
- `profile/`, `search/`, `feedback/`, `extension/` modules created
- ~1500 lines migrated from app.py
- All domains have clear blueprints

---

### Day 4: Consolidate Company Domain + Refactor CoreSignal

#### Morning: Company Domain
1. **Create `backend/company/` directory**
2. **Create `company/routes.py`**
   - All company endpoints from app.py (lines 2202-2513, 2991-3717)
3. **Split `company_research_service.py` (2,001 lines):**
   - Create `company/research_service.py` (~500 lines) - Orchestration
   - Create `company/discovery.py` (~400 lines) - Discovery methods
   - Create `company/evaluation.py` (~400 lines) - AI evaluation
   - Create `company/screening.py` (~300 lines) - Batch screening
4. **Consolidate enhanced research:**
   - Move `enhanced_company_research_service.py` → `company/enrichment.py`
5. **Extract company prompts:**
   - Move to `ai/prompts/company_evaluation.py`

**Estimated Time:** 5-6 hours

#### Afternoon: Refactor CoreSignal Client
1. **Create `backend/coresignal/` directory**
2. **Split `coresignal_service.py` (1,798 lines):**
   - Create `coresignal/client.py` (~200 lines) - Main client
   - Create `coresignal/employee.py` (~400 lines) - Employee API
   - Create `coresignal/company.py` (~300 lines) - Company API
   - Create `coresignal/search.py` (~500 lines) - Search API
   - Create `coresignal/retry.py` (~100 lines) - Retry logic
3. **Move taxonomy:**
   - `coresignal_api_taxonomy.py` → `coresignal/taxonomy.py`
4. **Move lookup:**
   - `coresignal_company_lookup.py` → `coresignal/company_lookup.py`

**Estimated Time:** 3-4 hours

**Deliverables:**
- `company/` module with 5 files
- `coresignal/` module with 6 files
- Major services split and organized

---

### Day 5: Refactor app.py + Create MCP Server

#### Morning: Refactor app.py
1. **Create new minimal `app.py`** (~200 lines)
   - Flask initialization
   - CORS setup
   - Blueprint registration (6 blueprints)
   - Static file serving
   - Health check endpoint
2. **Register all blueprints:**
   - `profile_bp` → `/api/profile`
   - `search_bp` → `/api/search`
   - `feedback_bp` → `/api/feedback`
   - `extension_bp` → `/api/extension`
   - `company_bp` → `/api/company`
   - `jd_bp` → `/api/jd`
3. **Test Flask server startup**
4. **Verify all routes still work**

**Estimated Time:** 3-4 hours

#### Afternoon: Create MCP Server
1. **Create `backend/mcp/` directory structure**
2. **Create MCP resources:**
   - `mcp/resources/api_docs.py` - Document all 40+ endpoints
   - `mcp/resources/database_schema.py` - Document all 8 tables
   - `mcp/resources/field_mappings.py` - CoreSignal field taxonomy
   - `mcp/resources/prompts_catalog.py` - Prompt registry
3. **Create MCP prompts:**
   - `mcp/prompts/templates.py` - Parameterized templates
4. **Create MCP tools:**
   - `mcp/tools/profile_tools.py` - Profile operations
   - `mcp/tools/search_tools.py` - Search operations
   - `mcp/tools/research_tools.py` - Company research
5. **Create `mcp/server.py`** - MCP server entrypoint

**Estimated Time:** 4-5 hours

**Deliverables:**
- app.py reduced from 3,887 → ~200 lines (98% reduction!)
- MCP server structure complete with resources/prompts/tools
- All endpoints working via blueprints

---

### Day 6: Update Documentation + Testing

#### Morning: Update Documentation
1. **Update `CLAUDE.md`**
   - Reflect new modular structure
   - Update file paths and imports
   - Document new feature domains
2. **Update `README.md`**
   - Update architecture section
   - Add modularization notes
3. **Update `docs/README.md`**
   - Update documentation index
   - Remove references to deleted files
4. **Update `PROJECT_STATUS.md`**
   - Mark modularization complete
5. **Create new docs:**
   - `docs/ARCHITECTURE.md` - Document feature-domain organization
   - `docs/MCP_SERVER.md` - MCP server usage guide
   - `backend/profile/README.md` - Profile module docs
   - `backend/company/README.md` - Company module docs
   - `backend/search/README.md` - Search module docs

**Estimated Time:** 3-4 hours

#### Afternoon: Testing & Validation
1. **Reorganize test suite:**
   - Create `tests/test_profile.py`
   - Create `tests/test_company.py`
   - Create `tests/test_search.py`
   - Create `tests/test_jd_analyzer.py`
   - Create `tests/test_feedback.py`
   - Create `tests/test_extension.py`
   - Create `tests/test_database.py`
   - Create `tests/test_coresignal.py`
   - Create `tests/test_mcp.py`
2. **Run existing test suite** (23 active tests)
3. **Test Flask server startup**
4. **Test all endpoints via curl/Postman**
5. **Test frontend integration**
6. **Test MCP server resources/prompts/tools**
7. **Fix any issues**

**Estimated Time:** 4-5 hours

**Deliverables:**
- All documentation updated
- Test suite reorganized
- All tests passing
- Frontend working with new backend
- MCP server functional

---

## Expected Outcomes

### Documentation Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total files | 138 | ~60 | -56% |
| Outdated files | 50+ | 0 | -100% |
| Session handoffs | 23 | 0 (archived) | Moved to docs/archived/sessions/ |
| Core docs | 50 | 60 | +10 (new module docs) |

### Codebase Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| app.py lines | 3,887 | ~200 | -98% |
| Files over 1000 lines | 6 | 0 | -100% |
| Feature domains | 1 (monolithic) | 9 (modular) | Clear boundaries |
| Average file size | ~800 lines | ~300 lines | -62% |
| Total backend files | ~15 major files | ~50 organized files | Better organization |

### Architecture Improvements

**Before:**
- ❌ Monolithic app.py with 60+ functions
- ❌ Prompts embedded in code (hard to version)
- ❌ Database operations scattered
- ❌ No clear feature boundaries
- ❌ Difficult to test in isolation

**After:**
- ✅ Feature-domain organization (profile, company, search, etc.)
- ✅ Centralized prompts in `ai/prompts/` (easy to version)
- ✅ Unified database layer with `database/` module
- ✅ Clear boundaries and single responsibility
- ✅ Easy to test individual modules
- ✅ MCP server ready for Claude Code

### MCP Server Benefits

**Resources (Read-Only Knowledge):**
- 40+ API endpoints with request/response schemas
- 8 Supabase tables with field definitions
- CoreSignal field mappings and query patterns
- 5 prompt templates with parameters

**Prompts (Reusable Templates):**
- Profile assessment prompt
- Search extraction prompt
- Company evaluation prompt
- JD parsing prompt
- Crunchbase validation prompt

**Tools (Executable Operations):**
- `fetch_linkedin_profile` - Fetch profile from CoreSignal
- `assess_profile` - AI assessment
- `search_profiles` - Natural language search
- `research_companies` - Company discovery and research

**Claude Code Performance Gains:**
- Faster context retrieval (MCP resources vs searching files)
- Reusable prompts (no need to reconstruct)
- Executable tools (direct operations vs multi-step)
- Accurate documentation (always up-to-date)

---

## Risk Mitigation

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Execute on separate branch, comprehensive testing before merge |
| Import circular dependencies | Use dependency injection, careful module design |
| Frontend breaks | Keep all endpoints backward compatible, test thoroughly |
| Test suite breaks | Update tests incrementally as modules are created |
| Lost code during migration | Git track every change, use git mv when possible |
| Merge conflicts with main | Regular rebasing, communicate with team |

### Rollback Strategy

If issues arise:
1. **Immediate rollback:** `git checkout main`
2. **Partial rollback:** Cherry-pick working commits
3. **Keep progress:** Fix issues on branch, merge when stable

### Testing Checkpoints

After each phase:
1. ✅ Run Flask server and verify startup
2. ✅ Test affected endpoints with curl
3. ✅ Run relevant test suite
4. ✅ Commit working state with descriptive message

---

## Branch Strategy

### Recommended Branch Workflow

```bash
# Create feature branch
git checkout -b feature/modularization-cleanup

# Work in phases (commit after each phase)
git add .
git commit -m "Phase 1: Documentation cleanup - Remove 49 outdated files"

git add .
git commit -m "Phase 2: Extract AI prompts to ai/prompts/ module"

git add .
git commit -m "Phase 3: Create database/ module with centralized Supabase ops"

# ... continue for all phases

# When complete and tested
git checkout main
git merge feature/modularization-cleanup
```

### Commit Messages Template

```
Phase X: [Brief description]

- What was changed
- Why it was changed
- What was tested

Files changed: X added, Y modified, Z deleted
```

---

## Success Criteria

### Phase Completion Criteria

Each phase is complete when:
1. ✅ All code migrated to new modules
2. ✅ All imports updated
3. ✅ Flask server starts successfully
4. ✅ Affected endpoints return correct responses
5. ✅ Relevant tests pass
6. ✅ Git commit made with descriptive message

### Overall Success Criteria

Project is complete when:
1. ✅ 49 outdated documentation files deleted
2. ✅ app.py reduced from 3,887 → ~200 lines
3. ✅ All 9 feature domains created and organized
4. ✅ All prompts centralized in `ai/prompts/`
5. ✅ Database operations unified in `database/` module
6. ✅ MCP server structure created with resources/prompts/tools
7. ✅ All 23 active tests passing
8. ✅ Frontend working with new backend structure
9. ✅ All documentation updated (CLAUDE.md, README.md, etc.)
10. ✅ Code merged to main branch

---

## Next Steps

When ready to execute:

1. **Create feature branch:**
   ```bash
   git checkout -b feature/modularization-cleanup
   ```

2. **Start with Phase 1 (Day 1):**
   - Delete outdated documentation (49 files)
   - Extract AI prompts to `ai/prompts/` module

3. **Work through phases sequentially**
   - Commit after each phase
   - Test thoroughly before moving to next phase

4. **Use this plan as checklist**
   - Check off each item as completed
   - Update plan if deviations occur

5. **Communicate progress**
   - Update PROJECT_STATUS.md
   - Document any blockers or changes

---

## Questions & Clarifications

Before starting, clarify:

1. **Deployment:** Will this require deployment changes? (e.g., updated requirements.txt, new env vars)
2. **Team coordination:** Are others working on overlapping code?
3. **Timeline:** Is 6-day timeline acceptable or need compression?
4. **MCP priority:** Is MCP server critical path or can it be done later?
5. **Testing:** Should we add new tests or just maintain existing coverage?

---

## Appendix

### A. Files Currently Well-Organized

**Good Examples to Follow:**

```
jd_analyzer/
├── api/ - API endpoints
├── core/ - Business logic
├── query/ - Query generation
├── company/ - Company-specific logic
└── utils/ - Utilities
```

This structure demonstrates:
- Clear separation of concerns
- Easy to navigate
- Logical grouping
- Single responsibility

### B. Prompt Extraction Checklist

For each prompt:
- [ ] Extract to separate file in `ai/prompts/`
- [ ] Add parameters for dynamic content
- [ ] Document expected inputs/outputs
- [ ] Add to MCP prompts catalog
- [ ] Update original code to import from new location
- [ ] Test that prompt still works

### C. Database Module Design Pattern

```python
# database/supabase_client.py
class SupabaseClient:
    """Shared Supabase client with retry logic"""
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

    def get(self, table, params):
        """Generic GET with retry"""
        ...

    def post(self, table, data):
        """Generic POST with retry"""
        ...

# database/assessments.py
from .supabase_client import SupabaseClient

class AssessmentRepository:
    """Assessment CRUD operations"""
    def __init__(self):
        self.client = SupabaseClient()

    def save(self, assessment):
        return self.client.post('candidate_assessments', assessment)

    def load(self, limit=50):
        return self.client.get('candidate_assessments', {'limit': limit})
```

### D. Blueprint Registration Pattern

```python
# profile/routes.py
from flask import Blueprint, request, jsonify

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/fetch-profile', methods=['POST'])
def fetch_profile():
    """Fetch LinkedIn profile from CoreSignal"""
    ...

# app.py
from profile.routes import profile_bp

app.register_blueprint(profile_bp, url_prefix='/api/profile')
```

---

**End of Plan**

This plan provides a comprehensive roadmap for cleaning up documentation and modularizing the codebase. Execute phases sequentially, test thoroughly, and commit frequently. Good luck!