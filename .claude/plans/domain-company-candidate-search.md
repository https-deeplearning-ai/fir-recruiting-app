# Domain Company-Based Candidate Search - Implementation Plan

**Started:** 2025-11-04
**Status:** In Progress

---

## Overview

Build an adaptive candidate search system that:
1. Uses existing `CompanyDiscoveryAgent` to find domain companies
2. Searches CoreSignal for people who worked at those companies
3. Shows 20 preview profiles to validate quality
4. If quality is good (>50% relevant), collects full profiles for 100-200 candidates
5. Uses Gemini 2.5 Flash to filter, then Claude Sonnet 4.5 to rank

**Key Innovation:** Comprehensive logging at every stage - all outputs saved to session logs.

---

## Phase 1: Foundation + Logging

### Task 1.1: Plan Tracking File ✅
- [x] Create this file at `.claude/plans/domain-company-candidate-search.md`
- [x] Add task tracking with checkboxes
- [x] Reference throughout implementation

### Task 1.2: Session Logging Utility
- [ ] Create `/backend/utils/session_logger.py`
  - [ ] `SessionLogger` class for managing session logs
  - [ ] `create_session()` - creates log directory
  - [ ] `log_json()` - writes JSON log files
  - [ ] `log_text()` - writes human-readable TXT files
  - [ ] `log_jsonl()` - appends to JSONL streaming logs
  - [ ] Log directory: `backend/logs/domain_search_sessions/{session_id}/`

### Task 1.3: Company Discovery Integration
- [ ] Create new endpoint file `/backend/jd_analyzer/api/domain_search.py`
- [ ] Import `CompanyDiscoveryAgent`
- [ ] Implement Stage 1: Domain company discovery
  - [ ] Extract domain + mentioned companies from JD
  - [ ] Call `discover_companies()`
  - [ ] Get 25-30 companies with confidence scores
- [ ] Add logging:
  - [ ] `01_company_discovery.json` (structured data)
  - [ ] `01_company_discovery_debug.txt` (human-readable)

### Task 1.4: Domain Company Query Builder
- [ ] Create function `build_domain_company_query(companies, role_keywords, location, endpoint)`
- [ ] Build nested Elasticsearch query:
  - [ ] Nested query for `experience.company_name` (wildcard match)
  - [ ] Basic role filter (engineer, founder, CEO, product)
  - [ ] Location filter (United States)
- [ ] Support 3 endpoints: employee_base, employee_clean, multi_source_employee
- [ ] Add logging:
  - [ ] `02_preview_query.json` (full ES DSL query)

### Task 1.5: Preview Search Endpoint
- [ ] Create route `/api/jd/domain-company-preview-search`
- [ ] Request format:
  ```json
  {
    "jd_requirements": {...},
    "endpoint": "employee_clean",
    "max_previews": 20
  }
  ```
- [ ] Response format:
  ```json
  {
    "session_id": "sess_abc123",
    "stage1_companies": [...],
    "stage2_previews": [...],
    "relevance_score": 0.70,
    "log_directory": "backend/logs/domain_search_sessions/sess_abc123/"
  }
  ```
- [ ] Add logging:
  - [ ] `02_preview_results.json` (20 candidate profiles)
  - [ ] `02_preview_analysis.txt` (quality analysis)

---

## Phase 2: Full Collection + AI Evaluation

### Task 2.1: Full Profile Collection
- [ ] Create route `/api/jd/collect-domain-profiles`
- [ ] Input: session_id, num_profiles (100-200)
- [ ] Reuse existing `/fetch-profile` logic
- [ ] Parallel processing with progress tracking
- [ ] Add streaming logs:
  - [ ] `03_collection_progress.jsonl` (real-time progress)
  - [ ] `03_collection_summary.json` (final stats)

### Task 2.2: Gemini 2.5 Flash Screening
- [ ] Create `/backend/gemini_screening_service.py`
- [ ] Function: `screen_candidates_binary(profiles, jd_requirements, session_logger)`
- [ ] Gemini 2.5 Flash API integration
- [ ] Binary filter prompt: "Is this person relevant? Yes/No + reasoning"
- [ ] Add streaming logs:
  - [ ] `04_gemini_filtering.jsonl` (per-candidate decisions)
  - [ ] `04_gemini_summary.json` (stats + common reasons)

### Task 2.3: Claude Assessment Integration
- [ ] Create route `/api/jd/evaluate-domain-candidates`
- [ ] Take RELEVANT candidates from Gemini
- [ ] Reuse existing `/assess-profile` weighted scoring
- [ ] Add streaming logs:
  - [ ] `05_claude_assessment.jsonl` (per-candidate scores)
  - [ ] `05_final_results.json` (ranked candidates)

---

## Phase 3: UI + Debug Views

### Task 3.1: Frontend Stage Progress
- [ ] Add state variables in `App.js`:
  - [ ] `domainSearchSession` - session ID
  - [ ] `stage1Companies` - discovered companies
  - [ ] `stage2Previews` - 20 preview profiles
  - [ ] `relevanceScore` - quality metric
  - [ ] `stage3FullProfiles` - collected profiles
  - [ ] `stage4FilteredResults` - final ranked list
- [ ] Add UI components:
  - [ ] 4-stage progress indicator
  - [ ] Company discovery results display
  - [ ] Preview quality analysis
  - [ ] "Collect Full Profiles" button (conditional)
  - [ ] Final ranked candidates view

### Task 3.2: Irrelevant Candidates Debug View
- [ ] Collapsible section: "View Filtered Candidates (44)"
- [ ] Display:
  - [ ] Name, headline, location
  - [ ] Gemini's reasoning for filtering
  - [ ] Search/filter capability

### Task 3.3: Session Log Viewer
- [ ] Create route `/api/jd/session-logs/{session_id}`
- [ ] List all log files in session
- [ ] View any log file in browser
- [ ] Download session folder as ZIP

---

## Current Progress

**Phase 1 - Task 1.1:** ✅ COMPLETE
**Phase 1 - Task 1.2:** 🔄 IN PROGRESS

---

## Notes & Decisions

### 2025-11-04: Initial Planning
- Decided to reuse existing `CompanyDiscoveryAgent` instead of recreating
- Gemini 2.5 Flash (not 2.0) for binary filtering
- Comprehensive logging at every stage with both JSON and TXT formats
- Session-based log directories for easy debugging

### Key File Locations
```
.claude/plans/domain-company-candidate-search.md  # This file
backend/utils/session_logger.py                   # Logging utility (to create)
backend/jd_analyzer/api/domain_search.py          # New endpoints (to create)
backend/gemini_screening_service.py               # Gemini filtering (to create)
backend/logs/domain_search_sessions/              # Session logs directory
```

---

## Testing Checklist

- [ ] Test Stage 1: Company discovery with "voice ai" domain
- [ ] Test Stage 2: Preview search returns 20 relevant candidates
- [ ] Test Stage 3: Full profile collection completes successfully
- [ ] Test Stage 4: Gemini filtering + Claude ranking works end-to-end
- [ ] Verify all log files are created correctly
- [ ] Verify log files are human-readable
- [ ] Test with different endpoints (employee_base, employee_clean, multi_source)
- [ ] Test error handling (API failures, rate limits)

---

## Success Metrics

**Quality:**
- Preview relevance: >50% with domain company experience
- Final relevance: >70% worth outreach
- False negative rate: <10%

**Performance:**
- Stage 1: <5 seconds
- Stage 2: <5 seconds
- Stage 3: <5 minutes (150 profiles)
- Stage 4: <5 minutes (AI evaluation)

**Debuggability:**
- All stages logged (JSON + TXT)
- Long outputs saved to files
- Easy to trace filtering decisions
- Logs comprehensible by non-technical users
