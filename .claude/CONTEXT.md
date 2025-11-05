# Codebase Context Map

Quick reference for navigating the LinkedIn Profile Assessment application. Updated: 2025-10-30

---

## 📁 Project Structure

```
linkedin_profile_ai_assessor/
├── backend/
│   ├── app.py (2630 lines)           # Main Flask application
│   ├── coresignal_service.py         # CoreSignal API integration
│   ├── config.py                     # Deployment-specific config
│   ├── extension_service.py          # Chrome extension backend
│   └── jd_analyzer/                  # JD analysis module (13 files)
│       ├── api_endpoints.py          # 5 JD-related API routes
│       ├── jd_parser.py              # Stage 1: JD → structured requirements
│       ├── weight_generator.py       # Stage 2: Requirements → weighted criteria
│       ├── shortlist_analyzer.py     # Reverse-engineer implicit criteria
│       ├── query_builder.py          # Requirements → CoreSignal query
│       ├── llm_query_generator.py    # Multi-LLM comparison (Claude, GPT, Gemini)
│       ├── models.py                 # Pydantic models (JDRequirements, LLMQueryResult)
│       └── debug_logger.py           # Structured logging
├── frontend/
│   ├── src/
│   │   ├── App.js (3740 lines)       # Main React application
│   │   └── components/               # React components (8 files)
│       └── build/                    # Production build output
└── docs/                             # Documentation (32 markdown files)
```

---

## 🔧 Backend: app.py (2630 lines)

### Environment Setup (Lines 1-68)
- **Line 29-31**: Initialize Anthropic client
- **Line 34**: Initialize CoreSignalService
- **Line 45-50**: Register JD Analyzer routes (from `jd_analyzer.api_endpoints`)
- **Line 52-67**: Load environment config (API keys, deployment settings)

### Database Operations (Supabase REST API)
- **Line 69-71**: `save_candidate_assessment()` - Main save wrapper
- **Line 74-126**: `save_to_supabase_api()` - Save assessment to Supabase (upsert by linkedin_url)
- **Line 128-166**: `load_candidate_assessments()` - Load assessments with limit, sorted by score
- **Line 168-224**: `get_stored_profile()` - Check if profile exists in storage (with freshness check)
- **Line 227-254**: `save_stored_profile()` - Save profile to storage with timestamp
- **Line 256-311**: `get_stored_company()` - Check if company data is fresh (default: 30 days)
- **Line 313-339**: `save_stored_company()` - Save company data to storage

### Profile Search & Query Building
- **Line 341-424**: `process_user_prompt_for_search()` - Claude AI extracts structured criteria from natural language
- **Line 426-582**: `build_intelligent_elasticsearch_query()` - Converts criteria to CoreSignal ES DSL query
  - Location expansion (Bay Area → multiple cities)
  - Industry mapping to CoreSignal taxonomy
  - Seniority, department, skills filtering
- **Line 584-631**: `search_coresignal_profiles_preview()` - Execute search (max 100 profiles, pages 1-5)
- **Line 633-654**: `convert_search_results_to_csv()` - Format results for CSV download

### Profile Processing
- **Line 656-777**: `extract_profile_summary()` - Parse CoreSignal JSON → structured summary
  - Calculates total years of experience (with overlap handling)
  - Extracts education, skills, headline
  - Returns: `{full_name, headline, location, total_years, current_job, education, ...}`
- **Line 779-872**: `format_company_intelligence()` - Format enriched company data for display
  - Groups by experience: funding stage, growth signals, company size
  - Only includes companies from 2020+ (enrichment filter)

### AI Assessment System
- **Line 874-1004**: `generate_assessment_prompt()` - Builds Claude prompt with rubric
  - Weighted requirements (1-5 custom + General Fit)
  - Scoring: 1-10 scale per requirement
  - Returns: Detailed analysis + scores + reasoning
  - Temperature: 0.1 (consistency)

### API Endpoints

**Core Profile Assessment:**
- **Line 1006-1119**: `POST /fetch-profile` - Fetch profile from CoreSignal by URL
  - Optional: `enrich_companies` (default: true, 2020+ only)
  - Optional: `force_refresh` (bypass storage)
  - Returns: `{profile_summary, raw_data, enrichment_summary}`

- **Line 1121-1263**: `POST /assess-profile` - AI assessment with weighted scoring
  - Requires: `profile_data`, `user_prompt`, `weighted_requirements`
  - Returns: `{weighted_analysis: {requirement_scores, weighted_score, analysis}}`

- **Line 1265-1343**: `assess_single_profile_sync()` - Synchronous assessment helper
  - Used by batch processing

**Batch Processing:**
- **Line 1345-1540**: `POST /batch-assess-profiles` - Parallel processing of CSV
  - Step 1: Parse CSV (extract LinkedIn URLs)
  - Step 2: Async fetch all profiles (aiohttp)
  - Step 3: ThreadPoolExecutor for parallel AI assessments
  - Returns: Sorted results by weighted_score

**Database Operations:**
- **Line 1542-1578**: `POST /save-assessment` - Save single assessment to Supabase
- **Line 1580-1594**: `GET /load-assessments` - Load saved assessments (limit: 50)

**Profile Search:**
- **Line 1596-1703**: `POST /search-profiles` - Natural language search
  - Claude extracts criteria → CoreSignal ES query → CSV export
  - Max: 100 profiles (5 pages × 20 results)

**Recruiter Feedback System:**
- **Line 1705-1755**: `POST /save-feedback` - Save feedback (like/dislike/note)
  - Fields: `linkedin_url`, `feedback_type`, `feedback_text`, `recruiter_name`
  - Upserts by linkedin_url + recruiter_name

- **Line 1757-1790**: `GET /get-feedback/<linkedin_url>` - Load all feedback for candidate
  - Returns: Array of feedback entries with timestamps

- **Line 1792-1831**: `POST /clear-feedback` - Delete feedback entries
  - Can delete specific feedback_id or all for a candidate

**Crunchbase URL Management:**
- **Line 1833-2031**: `POST /regenerate-crunchbase-url` - 4-tier hybrid strategy
  - Tier 1: CoreSignal direct (`company_crunchbase_info_collection`)
  - Tier 2a: Tavily candidate discovery (5-10 URLs)
  - Tier 2b: Claude Agent SDK WebSearch validation (Haiku 4.5)
  - Tier 3: Heuristic fallback (name → slug)
  - Returns: `{crunchbase_url, source, tavily_candidates}`

- **Line 2033-2142**: `POST /verify-crunchbase-url` - Verify URL matches company profile
  - Uses Claude Agent SDK WebSearch
  - Returns: `{is_correct, confidence, reason}`

**Chrome Extension API:**
- **Line 2144-2153**: `GET /extension/lists` - Get all candidate lists
- **Line 2155-2175**: `POST /extension/create-list` - Create new list
- **Line 2177-2189**: `PUT /extension/lists/<list_id>` - Update list metadata
- **Line 2191-2202**: `DELETE /extension/lists/<list_id>` - Delete list
- **Line 2204-2215**: `GET /extension/lists/<list_id>/stats` - Get list statistics
- **Line 2217-2240**: `POST /extension/add-profile` - Add profile to list
- **Line 2242-2264**: `GET /extension/profiles/<list_id>` - Get profiles in list
- **Line 2266-2283**: `PUT /extension/profiles/<profile_id>/status` - Update profile status
- **Line 2285-2303**: `GET /extension/auth` - Check authentication
- **Line 2305-2453**: `POST /lists/<list_id>/assess` - Batch assess list profiles
- **Line 2455-2589**: `GET /lists/<list_id>/export-csv` - Export list to CSV

**Health Check:**
- **Line 2591-2593**: `GET /health` - Health check endpoint
- **Line 2595-2607**: `GET /` - Serve React frontend (production)

---

## 🧠 Backend: jd_analyzer/ Module

### Module Structure
- **__init__.py**: Exports main classes (JDParser, WeightGenerator, ShortlistAnalyzer)
- **models.py**: Pydantic models for type-safe API responses

### Core Classes

**jd_parser.py (Line 15+)**
- `class JDParser`
  - `parse(jd_text: str) -> dict` - Stage 1: JD text → structured requirements
  - Uses: Claude Sonnet 4.5, temp 0.2 (deterministic)
  - Returns: `JDRequirements` model with must-have, nice-to-have, skills, seniority, etc.

**weight_generator.py (Line 13+)**
- `class WeightGenerator`
  - `generate_weighted_requirements(requirements: dict, num_requirements: int) -> list` - Stage 2: Requirements → weighted criteria
  - Uses: Claude Sonnet 4.5, temp 0.3 (slightly creative)
  - Returns: Array of weighted requirements (e.g., 35%, 25%, 20%, 10%, 10%)
  - Each includes: `requirement`, `weight`, `description`, `scoring_criteria`

**shortlist_analyzer.py (Line 12+)**
- `class ShortlistAnalyzer`
  - `load_candidates(csv_path: str)` - Parse CSV with Profile URL, Title, Company, Location
  - `analyze_patterns()` - Extract location, seniority, company distributions
  - `compare_to_jd(jd_requirements: dict)` - Discover gaps between JD and reality
  - Returns: Location gap, seniority gap, domain clustering, company pedigree

**query_builder.py (Line 16+)**
- `class JDToQueryBuilder`
  - `build_3_tier_queries(requirements: dict)` - Generate 3 CoreSignal queries
    - Tier 1: Strict (all must-haves)
    - Tier 2: Balanced (some OR conditions)
    - Tier 3: Broad (role + seniority only)
  - Returns: Array of ES DSL queries with estimated coverage

**llm_query_generator.py (Line 17+)**
- `class MultiLLMQueryGenerator`
  - `generate_all(jd_text: str)` - Parallel query generation
  - Returns: `{claude, gpt, gemini}` results with independent loading states
  - Used for LLM comparison view in frontend

### API Endpoints (api_endpoints.py, Line 30+)

**function: `register_jd_analyzer_routes(app)`** - Registers 5 routes:

1. **`POST /api/jd/parse`** (Line ~50)
   - Body: `{jd_text: str}`
   - Returns: `{success: bool, requirements: dict}`

2. **`POST /api/jd/generate-weights`** (Line ~100)
   - Body: `{jd_text: str, num_requirements: int}`
   - Returns: `{success: bool, weighted_requirements: array}`

3. **`POST /api/jd/full-analysis`** (Line ~150)
   - Body: `{jd_text: str, num_requirements: int}`
   - Returns: `{success: bool, requirements: dict, weighted_requirements: array, keywords: array}`
   - Most commonly used endpoint (complete pipeline)

4. **`POST /api/jd/analyze-shortlist`** (Line ~250)
   - Form Data: `csv_file`, optional `jd_text`
   - Returns: `{success: bool, analysis: dict, gaps: dict}`
   - CSV columns: Profile URL, Current Title, Current Company, Location

5. **`POST /api/jd/extract-keywords`** (Line ~350)
   - Body: `{jd_text: str}`
   - Returns: `{success: bool, keywords: array, role_titles: array, companies: array}`

---

## ⚛️ Frontend: App.js (3740 lines)

### State Variables (Lines 11-88)

**Assessment State:**
- `linkedinUrl` (11) - Input URL for single profile
- `userPrompt` (12) - Assessment instructions
- `assessment` (13) - Current assessment result
- `profileSummary` (17) - Extracted profile data
- `weightedRequirements` (18) - Array of weighted criteria (auto-populated by JD Analyzer)
- `singleProfileResults` (29) - Array of single profile assessments
- `batchResults` (21) - Array of batch assessment results
- `savedAssessments` (30) - Loaded from Supabase

**Loading States:**
- `loading` (14) - Assessment in progress
- `fetchingProfile` (15) - Profile fetch in progress
- `batchLoading` (22) - Batch processing in progress
- `searchLoading` (27) - Profile search in progress
- `savingAssessments` (32) - Saving to database

**Mode Toggles:**
- `batchMode` (23) - Batch processing view
- `searchMode` (24) - Profile search view
- `listsMode` (25) - Chrome extension lists view
- `jdAnalyzerMode` (61) - JD analyzer view

**JD Analyzer State (Lines 61-88):**
- `jdText` (62) - Raw job description textarea input
- `jdAnalyzing` (63) - Loading during AI analysis
- `extractedRequirements` (64) - Parsed requirements from JD
- `activeJD` (65) - Currently active JD object `{title, requirements, timestamp}`
- `jdTitle` (66) - User-provided JD title
- `jdSearching` (68) - Loading during CoreSignal search
- `jdSearchResults` (69) - Search results preview
- `jdFullResults` (70) - Full 100 candidates from "Search with model" button
- `jdCsvData` (71) - CSV data for download
- `currentPage` (72) - Pagination for full results
- `hoveredProfile` (73) - For tooltip display
- `tooltipPosition` (74) - Tooltip x/y coordinates

**Multi-LLM Comparison (Lines 77-86):**
- `claudeResult` (77), `gptResult` (78), `geminiResult` (79) - Independent query results
- `claudeLoading` (80), `gptLoading` (81), `geminiLoading` (82) - Independent loading states
- `selectedLlmQuery` (83) - Which query to use ('claude', 'gpt', 'gemini')
- `activeLlmTab` (84) - Which tab is visible

**Crunchbase Validation (Lines 87-88):**
- `validationModalOpen` (87) - Modal visibility
- `validationData` (88) - `{companyId, companyName, crunchbaseUrl, source}`

**Recruiter Feedback State (Lines 44-58):**
- `selectedRecruiter` (44) - Current recruiter name (localStorage)
- `candidateFeedback` (48) - Feedback per candidate URL (temporary)
- `feedbackHistory` (49) - All feedback from DB per candidate
- `isRecording` (50) - Voice recording state per candidate
- `showFeedbackInput` (51) - Show/hide note input per candidate
- `hideAIAnalysis` (52) - Collapse AI sections per candidate
- `drawerOpen` (53) - Feedback drawer open/closed per candidate
- `activeCandidate` (54) - Currently active candidate for feedback
- `openAccordionId` (55) - Which accordion is open (single-accordion mode)
- `candidateVisibility` (56) - Viewport visibility ratio (0-1) per candidate
- `aiAnalysisLoading` (57) - AI analysis loading per candidate
- `autoGenerateAI` (58) - Toggle for automatic AI analysis

**Data Options (Lines 36-43):**
- `useRealtimeData` (36) - Toggle for fresh profile data
- `enrichCompanies` (37) - Toggle company enrichment (default: true)
- `forceRefresh` (38) - Bypass storage, force fresh fetch
- `rawCoreSignalData` (39) - Store full CoreSignal JSON
- `showRawJSON` (40) - Toggle raw JSON display
- `enrichmentSummary` (41) - Company enrichment stats

### Key Handler Functions

**Feedback System (Lines 228-509):**
- `saveFeedback(linkedinUrl, feedbackType, feedbackText)` (228) - Save to Supabase
- `handleNoteChange(linkedinUrl, noteText)` (260) - Update note text state
- `handleNoteBlur(linkedinUrl, noteText)` (287) - Auto-save on blur
- `handleFeedbackClick(linkedinUrl, feedbackType)` (302) - Like/dislike click handler
- `toggleDrawer(linkedinUrl, candidateName)` (406) - Open/close feedback drawer
  - Opens drawer for most visible candidate (viewport detection)
  - Auto-collapses other accordions
  - Loads feedback history if not already loaded
- `handleDrawerCollapse(linkedinUrl)` (442) - Auto-save note on drawer close
- `clearMyFeedback(linkedinUrl, candidateName)` (459) - Delete feedback entries
- `loadFeedbackHistory(linkedinUrl)` (494) - Load all feedback from DB
- `handleQuickFeedback(linkedinUrl, feedbackType, reason)` (510) - Quick like/dislike with reason

**Crunchbase URL Management (Lines 867-975):**
- `handleCrunchbaseClick(clickData)` (867) - Open validation modal
- `handleValidation(validationPayload)` (913) - Verify URL via backend
  - Calls `/verify-crunchbase-url` with Claude Agent SDK

**Profile Assessment (Lines 977-1161):**
- `handleSubmit(e)` (977) - Single profile assessment flow
  1. Fetch profile (`/fetch-profile`)
  2. Assess with Claude (`/assess-profile`)
  3. Display results
- `handleGenerateAIAnalysis(linkedinUrl, profileData)` (1068) - Generate AI analysis for feedback
- `handleRefreshProfile(linkedinUrl)` (1118) - Force fresh profile fetch
- `handleRegenerateCrunchbaseUrl(companyName, companyId, currentUrl)` (1162) - 4-tier URL regeneration
  - Calls `/regenerate-crunchbase-url`
  - Updates profile data with new URL

**Batch Processing (Lines 1344-1524):**
- `handleCsvFileChange(e)` (1344) - File input handler
- `handleBatchProcess()` (1443) - Main batch flow
  1. Parse CSV file (extract LinkedIn URLs)
  2. Call `/batch-assess-profiles` with parallel processing
  3. Display sorted results

**Profile Search (Lines 1526-1588):**
- `handleProfileSearch()` (1526) - Natural language search
  - Calls `/search-profiles`
  - Downloads CSV file automatically

**Database Operations (Lines 1590-1683):**
- `loadSavedAssessments()` (1590) - Load from Supabase
- `saveCurrentAssessments()` (1613) - Save batch/single results to database

---

## 🎨 Frontend: Components

### WorkExperienceCard.js (~310 lines)
**Purpose:** Individual job card with company enrichment
- **Props:** `experience, onCrunchbaseClick, onRegenerateCrunchbase`
- **Features:**
  - Company logo display (CoreSignal `logo` field)
  - Funding stage badge (Seed, Series A, etc.)
  - Growth signals (headcount growth, hiring velocity)
  - Crunchbase URL clickable link
  - Edit/Regenerate buttons for Crunchbase URL
  - Date formatting (MMM YYYY)
- **CSS:** `WorkExperienceCard.css` (6579 lines)

### WorkExperienceSection.js (~80 lines)
**Purpose:** Container for all work experiences
- **Props:** `experiences, onCrunchbaseClick, onRegenerateCrunchbase`
- **Renders:** Array of WorkExperienceCard components
- **Layout:** Vertical timeline-style layout
- **CSS:** `WorkExperienceSection.css` (1405 lines)

### CompanyTooltip.js (~500 lines)
**Purpose:** Hover tooltip showing detailed company intelligence
- **Props:** `company, position`
- **Features:**
  - Funding history (rounds, amounts, dates)
  - Company description
  - Growth signals breakdown
  - Employee count trends
  - Industry & location
- **Positioning:** Fixed position at cursor (x, y)
- **CSS:** `CompanyTooltip.css` (9730 lines)

### CrunchbaseEditModal.js (~140 lines)
**Purpose:** Modal for manually editing Crunchbase URL
- **Props:** `isOpen, onClose, companyName, currentUrl, onSave`
- **Features:**
  - Text input for URL
  - Validation (must contain "crunchbase.com/organization/")
  - Save/Cancel buttons
- **CSS:** `CrunchbaseEditModal.css` (3658 lines)

### CrunchbaseValidationModal.js (~350 lines)
**Purpose:** Modal for validating Crunchbase URL with AI
- **Props:** `isOpen, onClose, validationData, onValidate`
- **Features:**
  - Display Tavily candidate URLs (Tier 2a)
  - Claude Agent SDK validation (Tier 2b)
  - Confidence score display
  - Accept/Regenerate buttons
- **CSS:** `CrunchbaseValidationModal.css` (7233 lines)

### ListsView.js (~160 lines)
**Purpose:** Chrome extension lists management view
- **Features:**
  - Display all candidate lists
  - Create new lists
  - Edit list metadata
  - Delete lists
  - Navigate to list detail view
- **CSS:** `ListsView.css` (9228 lines)

### ListCard.js (~80 lines)
**Purpose:** Individual list card in lists view
- **Props:** `list, onClick, onDelete`
- **Features:**
  - List name & description
  - Profile count badge
  - Delete button with confirmation

### ListDetail.js (~300 lines)
**Purpose:** Detailed view of single list with profiles
- **Props:** `listId`
- **Features:**
  - Display all profiles in list
  - Update profile status (saved, contacted, etc.)
  - Batch assess all profiles in list
  - Export list to CSV
  - Filter by status

---

## 🗄️ Database Schema (Supabase)

### Table: `candidate_assessments`
**Purpose:** Store all candidate assessments
**Key Columns:**
- `id` - UUID (primary key)
- `linkedin_url` - TEXT (unique index)
- `full_name` - TEXT
- `headline` - TEXT
- `profile_data` - JSONB (full CoreSignal profile)
- `assessment_data` - JSONB (complete AI assessment)
- `weighted_score` - NUMERIC (extracted for sorting)
- `overall_score` - NUMERIC (fallback if no weighted score)
- `assessment_type` - TEXT ('single' or 'batch')
- `session_name` - TEXT (optional grouping identifier)
- `created_at` - TIMESTAMP
- `updated_at` - TIMESTAMP

**Indexes:**
- `linkedin_url` (unique)
- `weighted_score` (DESC)
- `created_at` (DESC)

### Table: `recruiter_feedback`
**Purpose:** Store recruiter notes and like/dislike feedback
**Key Columns:**
- `id` - UUID (primary key)
- `candidate_linkedin_url` - TEXT (references candidate)
- `feedback_text` - TEXT (nullable for like/dislike only)
- `feedback_type` - TEXT ('like', 'dislike', or 'note')
- `recruiter_name` - TEXT (who gave feedback)
- `created_at` - TIMESTAMP
- `updated_at` - TIMESTAMP

**Indexes:**
- `candidate_linkedin_url` (for fast lookup)
- `recruiter_name` (for filtering by recruiter)
- Unique constraint: `(candidate_linkedin_url, recruiter_name, feedback_type)`

### Table: `stored_profiles`
**Purpose:** Cache CoreSignal profile data (reduce API calls)
**Key Columns:**
- `linkedin_url` - TEXT (primary key)
- `profile_data` - JSONB
- `checked_at` - TIMESTAMP (for freshness check)

### Table: `stored_companies`
**Purpose:** Cache CoreSignal company data (reduce API calls)
**Key Columns:**
- `company_id` - TEXT (primary key)
- `company_data` - JSONB
- `stored_at` - TIMESTAMP (for freshness check, default: 30 days)

### Table: `extension_lists`
**Purpose:** Chrome extension candidate lists
**Key Columns:**
- `id` - UUID (primary key)
- `name` - TEXT
- `description` - TEXT
- `created_at` - TIMESTAMP

### Table: `extension_profiles`
**Purpose:** Profiles saved from Chrome extension
**Key Columns:**
- `id` - UUID (primary key)
- `list_id` - UUID (references `extension_lists`)
- `linkedin_url` - TEXT
- `profile_name` - TEXT
- `profile_headline` - TEXT
- `status` - TEXT ('new', 'saved', 'contacted', 'rejected')
- `notes` - TEXT
- `added_at` - TIMESTAMP

---

## 🔑 Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` - Claude AI API key
- `CORESIGNAL_API_KEY` - CoreSignal API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/public key
- `TAVILY_API_KEY` - Tavily Search API key (for Crunchbase URL fallback)

**Optional:**
- `RENDER` - Set to "true" for Render deployment (enables Render-specific config)
- `PORT` - Flask port (default: 5001)

---

## 🚀 Common Workflows

### 1. Single Profile Assessment
```
User Flow:
1. Paste LinkedIn URL (frontend line ~2000)
2. Add weighted requirements (frontend line ~2100)
3. Click "Assess Candidate" → handleSubmit() (line 977)
4. Backend: /fetch-profile (line 1006) → /assess-profile (line 1121)
5. Display results with accordion (frontend line ~2500)
```

### 2. Batch CSV Processing
```
User Flow:
1. Upload CSV file → handleCsvFileChange() (line 1344)
2. Click "Process Batch" → handleBatchProcess() (line 1443)
3. Backend: /batch-assess-profiles (line 1345)
   - Parse CSV → async fetch → ThreadPoolExecutor assess
4. Display sorted results (frontend line ~2800)
```

### 3. JD Analyzer → Auto-populate Criteria
```
User Flow:
1. Switch to JD Analyzer mode → setJdAnalyzerMode(true) (line 61)
2. Paste JD text (frontend line ~3200)
3. Click "Analyze JD" → calls /api/jd/full-analysis
4. Backend: jd_analyzer/api_endpoints.py (line ~150)
   - JDParser.parse() → WeightGenerator.generate_weighted_requirements()
5. Frontend: Auto-populate weightedRequirements state (line 18)
6. User reviews/edits weights
7. Use for candidate assessment
```

### 4. Reverse-Engineer Implicit Criteria
```
User Flow:
1. Upload candidate shortlist CSV (Profile URL, Title, Company, Location)
2. Optionally: Paste JD text for gap analysis
3. Click "Analyze Shortlist" → calls /api/jd/analyze-shortlist
4. Backend: ShortlistAnalyzer.analyze_patterns() + compare_to_jd()
5. Display: Location distribution, seniority patterns, company clusters, gaps
```

### 5. Crunchbase URL 4-Tier Regeneration
```
User Flow:
1. Click "Regenerate" on company card
2. handleRegenerateCrunchbaseUrl() (line 1162)
3. Backend: /regenerate-crunchbase-url (line 1833)
   - Tier 1: CoreSignal direct (company_crunchbase_info_collection)
   - Tier 2a: Tavily search (5-10 candidates)
   - Tier 2b: Claude Agent SDK WebSearch (pick correct one)
   - Tier 3: Heuristic fallback (name → slug)
4. Frontend: Update profile data with new URL
5. Display validation modal if needed
```

### 6. Recruiter Feedback Loop
```
User Flow:
1. Open feedback drawer → toggleDrawer() (line 406)
   - Viewport detection finds most visible candidate
   - Auto-collapses other accordions
2. Like/Dislike → handleQuickFeedback() (line 510)
3. Voice note → Web Speech API → handleNoteBlur() (line 287)
4. Auto-save on blur, drawer close, accordion collapse
5. Backend: /save-feedback (line 1705) → Supabase
6. Load history: /get-feedback/<url> (line 1757)
```

---

## 📊 Key Patterns & Techniques

### 1. Viewport-Aware UI (Intersection Observer)
**Location:** frontend/src/App.js (lines ~500-600)
- Tracks visibility ratio (0-1) for each candidate card
- 11 thresholds: [0, 0.1, 0.2, ..., 1.0]
- Opens feedback drawer for most visible candidate
- Prevents UI overlap and race conditions
- Pattern: `candidateVisibility[url]` → `getMostVisibleCandidate()`

### 2. Controlled Accordion Pattern
**Location:** frontend/src/App.js (lines ~2500-2700)
- Single source of truth: `openAccordionId` (line 55)
- Uses `<details open={openAccordionId === url}>`
- `e.preventDefault()` on `<summary>` clicks
- NO `onToggle` handler (causes race conditions)
- Auto-collapse other accordions when feedback drawer opens

### 3. Two-Stage AI Pipeline (JD Analyzer)
**Location:** backend/jd_analyzer/
- **Stage 1:** JDParser (temp 0.2, deterministic)
  - JD text → structured requirements
  - Returns: Pydantic `JDRequirements` model
- **Stage 2:** WeightGenerator (temp 0.3, slightly creative)
  - Requirements → weighted criteria with rubrics
  - Returns: Array of 1-5 requirements with % weights

### 4. 4-Tier Hybrid Crunchbase URL Strategy
**Location:** backend/app.py (line 1833)
- **Tier 1:** CoreSignal direct (69.2% coverage, 100% accuracy)
- **Tier 2a:** Tavily search (100% findability in top 10)
- **Tier 2b:** Claude Agent SDK WebSearch (100% combined accuracy)
- **Tier 3:** Heuristic fallback (name → slug, ~30% accuracy)
- **Test Results:** 20/20 correct (100%) on Series A companies

### 5. Session-Based Caching
**Location:** backend/coresignal_service.py
- Company data cached in session (resets on server restart)
- Prevents duplicate API calls during same session
- Pattern: Check session cache → Check database → Fetch fresh

### 6. Experience Overlap Handling
**Location:** backend/app.py (line ~700)
- Merges overlapping date intervals
- Prevents double-counting years
- Handles: Missing end dates, partial months, invalid years
- Algorithm: Sort by start date → merge overlapping intervals

### 7. Pydantic Model Validation
**Location:** backend/jd_analyzer/models.py
- Type-safe API responses
- Automatic validation and error handling
- Pattern: `JDRequirements.from_dict()` with edge case handling
- Prevents: `'list' object has no attribute 'get'` errors

### 8. Multi-LLM Comparison (Parallel)
**Location:** backend/jd_analyzer/llm_query_generator.py
- Independent loading states (Claude, GPT, Gemini)
- No blocking between LLMs
- Frontend: 3 tabs with independent results
- Pattern: `asyncio.gather()` for parallel execution

---

## 🐛 Common Debugging Points

### Profile Not Found
- **Check:** `backend/app.py` line 1050-1080 (fetch-profile error handling)
- **Reason:** URL not in CoreSignal or URL format incorrect
- **Debug:** Look for "Profile not found" in response

### Weighted Score Calculation
- **Check:** `backend/app.py` line 874-1004 (generate_assessment_prompt)
- **Formula:** `weighted_score = Σ(requirement_score × weight%)`
- **Debug:** Ensure weights sum to ≤100% (General Fit = 100% - sum(custom weights))

### Company Enrichment Missing
- **Check:** `backend/coresignal_service.py` (enrich_with_company_data)
- **Reason:** Job start date < 2020 (filtered out to save API credits)
- **Debug:** Look at enrichment_summary in response

### Crunchbase URL Incorrect
- **Check:** `backend/app.py` line 1833-2031 (regenerate_crunchbase_url)
- **Debug:** Check `source` field ('coresignal', 'tavily', 'claude_websearch', 'heuristic')
- **Fix:** Use validation modal to verify with Claude WebSearch

### Accordion Race Conditions
- **Check:** `frontend/src/App.js` lines 2500-2700
- **Reason:** Mixed controlled/uncontrolled state or using `onToggle`
- **Fix:** Use `openAccordionId` as single source of truth + `e.preventDefault()`

### Feedback Not Saving
- **Check:** `backend/app.py` line 1705-1755 (save-feedback endpoint)
- **Debug:** Check Supabase unique constraint (linkedin_url + recruiter_name + feedback_type)
- **Fix:** Ensure upsert logic is working (should update existing, not fail)

### JD Analyzer Parse Error
- **Check:** `backend/jd_analyzer/jd_parser.py` (JDParser.parse)
- **Reason:** Invalid JSON response from Claude or missing fields
- **Debug:** Look at `debug_logger` output (structured logging)
- **Fix:** Check Pydantic model validation in `models.py`

---

## 📝 Quick Reference: File Line Counts

```
Backend:
  app.py                         2630 lines  (Main Flask app)
  coresignal_service.py          ~400 lines  (CoreSignal API)
  jd_analyzer/api_endpoints.py  ~1100 lines  (JD API routes)
  jd_analyzer/jd_parser.py       ~200 lines  (Stage 1: Parse)
  jd_analyzer/weight_generator.py ~180 lines (Stage 2: Weights)
  jd_analyzer/shortlist_analyzer.py ~250 lines (Reverse-engineer)

Frontend:
  App.js                         3740 lines  (Main React app)
  WorkExperienceCard.js          ~310 lines  (Job card component)
  CompanyTooltip.js              ~500 lines  (Hover tooltip)
  CrunchbaseValidationModal.js   ~350 lines  (Validation modal)

CSS:
  App.css                        ~2000 lines (Main styles)
  CompanyTooltip.css             9730 lines  (Tooltip styles)
  WorkExperienceCard.css         6579 lines  (Card styles)
```

---

## 🔗 Related Documentation

- **CLAUDE.md** - Main project guide (comprehensive overview)
- **docs/JD_ANALYZER_INTEGRATION.md** - Frontend integration guide (17 pages)
- **docs/JD_ANALYZER_PROMPT_ANALYSIS.md** - Prompt engineering analysis (16 pages)
- **docs/reverse-engineering/REVERSE_ENGINEERING_REPORT.md** - Voice AI role case study (15 pages)
- **backend/jd_analyzer/README.md** - JD Analyzer module documentation
- **backend/jd_analyzer/CORESIGNAL_FIELD_REFERENCE.md** - Complete field mappings

---

**Last Updated:** 2025-10-30
**Total Files Documented:** 20+ backend files, 8 frontend components, 5 database tables
**Total Lines Mapped:** ~10,000+ lines of critical code paths
