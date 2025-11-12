# Research Session Quick Reference

**Last Updated:** November 11, 2025
**Purpose:** Fast lookup guide for developers
**See Also:** [RESEARCH_SESSION_WORKFLOW.md](RESEARCH_SESSION_WORKFLOW.md) for detailed workflows

---

## Session Types at a Glance

```
┌───────────────────┬──────────────┬──────────┬────────┬──────────┐
│ Type              │ Duration     │ Cost     │ API    │ Resume?  │
├───────────────────┼──────────────┼──────────┼────────┼──────────┤
│ Single Profile    │ 5-10s        │ $0.30    │ 2 APIs │ ✓        │
│ Batch Processing  │ 2-5 min      │ $0.30 ea │ Many   │ ✓        │
│ Domain Search     │ 3-5 min      │ $1.90    │ Many   │ ✓        │
│ Profile Search    │ 1-3 min      │ $0.20-50 │ 2 APIs │ ✓        │
└───────────────────┴──────────────┴──────────┴────────┴──────────┘
```

---

## API Endpoints Cheat Sheet

### Single Profile Assessment
```
POST /fetch-profile                  app.py:1275
  → CoreSignal fetch + company enrichment

POST /assess-profile                 app.py:1479
  → Claude AI assessment with weighted scoring
```

### Batch Processing
```
POST /batch-assess-profiles          app.py:1703
  → Parallel fetch + assess for multiple candidates
```

### Domain Search & Company Research
```
POST /research-companies             app.py:2991
  → Start company discovery + screening

GET /research-companies/<id>/stream  app.py:3220
  → SSE stream for real-time progress

GET /research-companies/<id>/status  app.py:3182
  → Poll session status

GET /research-companies/<id>/results app.py:3363
  → Get final results

POST /evaluate-more-companies        app.py:3129
  → Resume and evaluate more companies
```

### Profile Search
```
POST /search-profiles                app.py:1954
  → Natural language search → CoreSignal
```

### JD Analyzer
```
POST /api/jd/parse                   jd_analyzer/api/*
  → Parse job description

POST /api/jd/generate-weights        jd_analyzer/api/*
  → Generate weighted criteria

POST /api/jd/full-analysis           jd_analyzer/api/*
  → Complete pipeline (parse + weights + keywords)
```

---

## Database Tables Quick Ref

```
candidate_assessments
├─ PK: id (SERIAL)
├─ linkedin_url (TEXT, indexed)
├─ profile_data (JSONB)
├─ assessment_data (JSONB)
├─ weighted_score (DECIMAL)
├─ assessment_type ('single' | 'batch')
└─ session_name (TEXT, nullable)

company_research_sessions
├─ PK: session_id (UUID/TEXT)
├─ jd_context (JSONB)
├─ discovered_companies (JSONB array)
├─ screened_companies (JSONB array)
├─ status ('in_progress' | 'completed' | 'failed')
└─ created_at, updated_at (TIMESTAMP)

search_sessions
├─ PK: session_id (TEXT)
├─ search_query (JSONB)
├─ employee_ids (TEXT array, max 1000)
├─ company_batches (JSONB)
├─ batch_index (INTEGER)
└─ profiles_offset (INTEGER)

stored_profiles (cache)
├─ PK: linkedin_url (TEXT)
├─ profile_data (JSONB)
├─ fetched_at (TIMESTAMP)
└─ Freshness: <3d=use, 3-90d=refresh, >90d=force

stored_companies (cache)
├─ PK: company_id (INTEGER)
├─ company_data (JSONB)
├─ fetched_at (TIMESTAMP)
└─ Freshness: <30d=use, >30d=force

recruiter_feedback
├─ candidate_linkedin_url (TEXT)
├─ feedback_text (TEXT, nullable)
├─ feedback_type ('like' | 'dislike' | 'note')
├─ recruiter_name (TEXT: Jon, Mary, etc.)
└─ source_tab (TEXT)
```

---

## Common Workflows

### 1. Single Profile Assessment
```
User Input → /fetch-profile → /assess-profile → Display
   (5s)         (3s)              (6s)           (instant)

Cache strategy:
  stored_profiles check → CoreSignal API (if miss)
```

### 2. Batch Processing (15 candidates)
```
CSV Upload → Parse → Async Fetch (all) → Parallel Assess → Sort → Display
  (1s)       (1s)      (45s)              (2min)          (1s)    (instant)

Parallel execution:
  - aiohttp for fetching (15 concurrent)
  - ThreadPoolExecutor for AI (50 workers on Render)
```

### 3. Domain Search
```
JD Input → Parse → Discovery → Screening → Employee Sampling → Results
 (paste)    (5s)    (60s)       (180s)        (90s)           (display)

Real-time updates via SSE:
  - GET /stream connection opened
  - Events: discovery, screening, employee_sampling, complete
```

### 4. Profile Search
```
Query → Extract Criteria → CoreSignal → Create Session → Display 20
(type)     (2s)              (3s)         (1s)           (instant)

Progressive loading:
  Initial: 20 profiles
  "Load More" → Discover all 100 IDs → Progressive fetch
```

---

## Status Codes & Session States

### Session States
```
┌────────────┐
│  initial   │ → Session created, not started
└────┬───────┘
     ↓
┌────────────┐
│in_progress │ → Discovery/screening/sampling active
└────┬───────┘
     ├─→ completed → All phases done, results available
     ├─→ failed    → Error occurred, partial results
     └─→ paused    → User can resume later
```

### HTTP Status Codes
```
200 OK                  → Success
201 Created             → Session created
400 Bad Request         → Invalid input (missing fields)
404 Not Found           → Profile/session not found
422 Unprocessable       → CoreSignal API validation error
429 Too Many Requests   → Rate limit (Claude/CoreSignal)
500 Internal Error      → Server error
503 Service Unavailable → External API down
```

---

## Performance Metrics

### Timing Benchmarks
```
Single Profile:
  Fetch: 3-5s
  Assess: 5-7s
  Total: 8-12s

Batch (50 profiles):
  Fetch: 60-90s (parallel)
  Assess: 3-5 min (50 workers)
  Total: 4-6 min

Domain Search:
  Discovery: 45-60s
  Screening: 2-4 min (100 companies)
  Sampling: 1-2 min
  Total: 4-7 min

Profile Search:
  Query: 2-5s
  Load More: +3-5s (discover 100 IDs)
  Progressive fetch: As needed
```

### Cost Per Operation
```
Single Profile:     $0.30
Batch (per profile): $0.30
Domain Search:      $1.90 (fresh) / $0.57 (70% cached)
Profile Search:     $0.20-0.50 (depends on load more usage)

Cost Breakdown (Domain Search):
  - Company Discovery: $0.40 (Tavily + Claude)
  - CoreSignal ID Lookup: $0.50 (4-tier hybrid)
  - Company Screening: $0.50 (Haiku + WebSearch)
  - Employee Search: $0.50 (CoreSignal preview API)
```

---

## Key Code Locations

### Frontend (App.js)
```
Line Range    Component
──────────    ─────────────────────────────
1500-1700     JD Analyzer UI
1850-1950     Batch CSV Upload
2110-2180     Single Profile URL Input
2400-2800     Batch Results Display
2850-3200     Single Profile Results
3600-3900     Feedback Drawer
4200-4900     Company Research Results
```

### Backend (app.py)
```
Line Range    Endpoint/Function
──────────    ───────────────────────────────
870-1020      extract_profile_summary()
1275-1430     POST /fetch-profile
1479-1650     POST /assess-profile
1703-1950     POST /batch-assess-profiles
1954-2100     POST /search-profiles
2991-3120     POST /research-companies
3129-3180     POST /evaluate-more-companies
3182-3220     GET /research-companies/<id>/status
3220-3350     GET /research-companies/<id>/stream
3363-3450     GET /research-companies/<id>/results
```

### Services
```
File                          Lines       Purpose
────────────────────────      ─────       ───────────────────────────
coresignal_service.py         45-280      Profile fetching
coresignal_service.py         350-550     Company enrichment
company_research_service.py   117-250     Session management
company_research_service.py   375-486     Company discovery
company_research_service.py   675-782     Haiku screening
company_research_service.py   1715-1850   Employee sampling
utils/search_session.py       All         Search session management
jd_analyzer/jd_parser.py      All         JD parsing (Stage 1)
jd_analyzer/weight_generator.py All       Weight generation (Stage 2)
```

---

## Common Troubleshooting

### Issue: All companies score 5.0
```
Cause: Cache hit with old GPT-5 results
Fix:   Add "bypass_cache": true to request
       OR wait for cache expiry (7 days)
```

### Issue: Employee titles show "N/A"
```
Cause: Wrong field mapping (using 'title' instead of 'job_title')
Fix:   Already fixed in v2.0 (Nov 11, 2025)
       Verify: job_title field extraction
```

### Issue: UI shows "undefined" for reasoning
```
Cause: Field name mismatch (screening_reasoning vs relevance_reasoning)
Fix:   Already fixed in App.js:747, 4940
       Frontend now reads: screening_reasoning
```

### Issue: Duplicate headlines in candidate cards
```
Cause: Fallback logic reuses headline field
Status: Identified, fix pending
Solution: Add deduplication check in App.js:4445
```

### Issue: CoreSignal 422 error on employee search
```
Cause: Preview endpoint doesn't accept 'size' parameter
Fix:   Remove size from query, limit results in Python
       Already fixed in domain_search.py
```

### Issue: SSE connection drops
```
Cause: Network timeout or server restart
Fix:   Frontend auto-reconnects (3 retries)
       Check backend logs for errors
```

---

## Mini Flow Diagrams

### Single Profile Flow
```
URL Input → Fetch → Enrich → Assess → Display
```

### Batch Flow
```
CSV → Parse → [Fetch All] → [Assess All] → Sort → Display
               ↑ Parallel      ↑ Parallel
```

### Domain Search Flow
```
JD → Parse → Discovery → Screening → Sampling → Results
                ↓ SSE      ↓ SSE       ↓ SSE
             [Progress Updates in Real-time]
```

### Session Resume Flow
```
Load Session → Check Status → [Evaluate More] → Update Session
   ↓                             ↑
[Show Results]         [User clicks button]
```

---

## Configuration Quick Ref

### Deployment Configs (config.py)
```
Platform    Workers    Timeout    Batch Size
────────    ───────    ───────    ──────────
Render      50         60s        100
Heroku      15         25s        50
Local       5          120s       20
```

### Cache TTLs
```
Resource              TTL
────────────────      ──────────────
stored_profiles       90 days
stored_companies      30 days
company_discovery     7 days (was 48h, temp 1h)
search_sessions       Indefinite (manual cleanup)
```

### AI Model Settings
```
Model                    Temperature    Purpose
───────────────────      ───────────    ─────────────────────
Claude Sonnet 4.5        0.1            Profile assessment
Claude Sonnet 4.5        0.2            JD parsing
Claude Sonnet 4.5        0.3            Weight generation
Claude Haiku 4.5         Default        Company screening
```

---

## External API Limits

### CoreSignal API
```
Endpoint                    Rate Limit    Cost
──────────────────────      ──────────    ────────
/employee_clean/search      ?             $0.10
/employee_clean/collect     ?             $0.20
/company_base/collect       ?             $0.10
/employee_clean/../preview  Pages 1-5     $0.10
```

### Claude API (Anthropic)
```
Model              Rate Limit           Cost
─────────────      ──────────────       ───────────────
Sonnet 4.5         500 RPM / 40k TPM    $3/1M input
                                        $15/1M output
Haiku 4.5          500 RPM / 40k TPM    $0.80/1M input
                                        $4/1M output
```

### Tavily API (Web Search)
```
Endpoint           Rate Limit    Cost
─────────────      ──────────    ────────
/search            ?             $0.01/query
```

---

## Useful SQL Queries

### Find recent assessments
```sql
SELECT linkedin_url, weighted_score, created_at
FROM candidate_assessments
WHERE assessment_type = 'single'
ORDER BY created_at DESC
LIMIT 10;
```

### Check cache hit rate
```sql
SELECT
  COUNT(*) FILTER (WHERE fetched_at > NOW() - INTERVAL '3 days') as fresh,
  COUNT(*) FILTER (WHERE fetched_at <= NOW() - INTERVAL '3 days') as stale,
  COUNT(*) as total
FROM stored_profiles;
```

### Active research sessions
```sql
SELECT session_id, jd_context->>'domain' as domain,
       status, created_at
FROM company_research_sessions
WHERE status = 'in_progress'
ORDER BY created_at DESC;
```

### Top scored candidates
```sql
SELECT full_name, headline, weighted_score
FROM candidate_assessments
WHERE weighted_score >= 8.0
ORDER BY weighted_score DESC
LIMIT 20;
```

---

## Frontend State Management

### Key State Variables (App.js)
```javascript
// Assessment State
singleProfileResults    // Array of single profile results
batchResults            // Array of batch results
savedAssessments        // All saved assessments from DB
weightedRequirements    // Array of requirement objects
generalFitWeight        // Auto-calculated from 100% - sum(weights)

// JD Analyzer State
jdAnalyzerMode          // Boolean: JD analyzer view active
jdText                  // Raw JD input text
activeJD                // Current JD with parsed requirements
jdSearchResults         // CoreSignal results from JD keywords

// Feedback State
drawerOpen              // Map: {linkedin_url: boolean}
activeCandidate         // Currently active candidate
feedbackHistory         // All feedback for candidate
selectedRecruiter       // Current recruiter (Jon, Mary, etc.)
isRecording            // Map: {linkedin_url: boolean}

// Company Research State
companyResearchResults  // Array of discovered companies
researchProgress        // {phase, count, message}
sseConnection          // EventSource for SSE streaming
```

---

## Testing Checklist

### Single Profile
- [ ] Valid LinkedIn URL fetches profile
- [ ] Invalid URL shows error message
- [ ] Cached profile loads faster (<1s)
- [ ] Assessment scores calculate correctly
- [ ] Company enrichment displays (2020+ jobs)
- [ ] Feedback drawer opens/closes
- [ ] Voice notes record and save

### Batch Processing
- [ ] CSV uploads and parses correctly
- [ ] Progress bar updates in real-time
- [ ] All profiles fetch (check completion count)
- [ ] Results sort by weighted score
- [ ] Failed profiles show error state
- [ ] Export CSV works

### Domain Search
- [ ] JD parses correctly (check extracted fields)
- [ ] SSE connection establishes
- [ ] Real-time progress updates show
- [ ] Company cards display with scores
- [ ] Employee samples show (5 per company)
- [ ] "Evaluate More" works
- [ ] Session resume works after days

### Profile Search
- [ ] Natural language query extracts criteria
- [ ] Initial 20 results display
- [ ] "Load More" discovers 100 IDs
- [ ] Progressive loading works
- [ ] Session persists indefinitely

---

**For detailed workflows with ASCII diagrams, see:** [RESEARCH_SESSION_WORKFLOW.md](RESEARCH_SESSION_WORKFLOW.md)

**For codebase architecture, see:** [CLAUDE.md](CLAUDE.md)

**For database schema, see:** [docs/SUPABASE_SCHEMA.sql](docs/SUPABASE_SCHEMA.sql)
