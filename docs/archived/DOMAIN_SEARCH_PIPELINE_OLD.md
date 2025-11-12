# Domain Search Pipeline - Complete Technical Documentation

**Version:** 2.0
**Last Updated:** 2025-11-05
**Status:** Production (with Persistent Caching)

---

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DOMAIN SEARCH PIPELINE (4 STAGES)                    │
│                                                                           │
│  Frontend → Flask API → Session Logger → Supabase Cache → CoreSignal API│
│                                                                           │
│  Session ID: sess_20251105_a1b2c3d4                                      │
│  Log Directory: backend/logs/domain_search_sessions/sess_20251105_...   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 STAGE-BY-STAGE FLOW

### STAGE 1: COMPANY DISCOVERY

**File:** `domain_search.py` (lines 152-258)
**API Endpoint:** `/api/jd/domain-company-preview-search` (POST)

```
INPUT:
  ├─ target_domain: "voice ai"
  ├─ mentioned_companies: ["Deepgram", "OpenAI"]
  └─ competitor_context: "speech recognition, TTS"

PROCESS:
  ├─ CompanyDiscoveryAgent.discover_companies()
  │   ├─ Method 1: Seed Expansion (up to 15 seed companies × 3 searches)
  │   │   ├─ Tavily Search: "{company} competitors"
  │   │   ├─ Tavily Search: "companies like {company}"
  │   │   └─ Tavily Search: "{company} alternatives"
  │   │
  │   └─ Method 2: Domain Search (6 queries → top 5 executed)
  │       ├─ Priority: Domain (G2/Capterra) > Seed > Industry > Generic
  │       └─ Sources: G2, Capterra, Gartner, Crunchbase, ProductHunt
  │
  ├─ Deduplication & Normalization
  └─ Confidence Scoring (mentioned=1.0, seed=0.8, domain=0.6)

OUTPUT (typical: 30-100 companies):
  ├─ company_name: "Deepgram"
  ├─ source: "mentioned" | "seed_expansion" | "domain_discovery"
  ├─ confidence: 0.6 - 1.0
  └─ context: "Real-time speech recognition API..."

LOGGING:
  ├─ 01_company_discovery.json (structured data)
  ├─ 01_company_discovery_debug.txt (human-readable)
  └─ Metrics: total_count, by_source breakdown, duration

INTERMEDIATE CHECKS:
  ✓ Excluded companies filter (DLAI, AI Fund)
  ✓ Multi-word company name extraction (regex fix for "Hugging Face")
  ✓ Duplicate detection across sources
  ✓ Confidence threshold validation

CREDITS: 0 (only web search, no CoreSignal calls)
```

---

### STAGE 2: PREVIEW SEARCH

**File:** `domain_search.py` (lines 511-666)
**API Endpoint:** `/api/jd/domain-company-preview-search` (POST) - same as Stage 1

```
INPUT:
  ├─ discovered_companies: [30-100 company names]
  ├─ jd_requirements: {role_title, seniority, skills, ...}
  ├─ endpoint: "employee_clean" (preferred for data uniformity)
  └─ max_previews: 20

PROCESS:
  ├─ CoreSignal Company Lookup (get company_ids)
  │   ├─ For each company name → search CoreSignal API
  │   ├─ Generate name variations (remove Inc/LLC, lowercase, etc.)
  │   └─ Find best match by fuzzy name matching
  │
  ├─ Build CoreSignal Search Query
  │   ├─ Filter: company_id IN [resolved company IDs]
  │   ├─ Filter: current_position_title ~ role_title (if specified)
  │   └─ Filter: management_level = seniority (if specified)
  │
  ├─ Execute Preview Search (limit: max_previews)
  │   └─ CoreSignal API: /v2/employee_clean/search/es_dsl/preview
  │
  └─ Extract Preview Data (minimal fields)
      ├─ employee_id (required for Stage 3)
      ├─ full_name
      ├─ headline / generated_headline
      └─ current_company_name

OUTPUT (typical: 20 candidates):
  ├─ employee_id: 12345678
  ├─ full_name: "John Doe"
  ├─ headline: "Senior ML Engineer at Deepgram"
  └─ current_company: "Deepgram"

LOGGING:
  ├─ 02_preview_search.json (structured data)
  ├─ 02_preview_analysis.txt (human-readable analysis)
  ├─ Query details, company resolution success rate
  └─ Metrics: candidates_found, companies_with_matches, duration

INTERMEDIATE CHECKS:
  ✓ Company ID resolution validation (fuzzy matching)
  ✓ Query syntax validation (employee_clean vs employee_base differences)
  ✓ Preview result count check (warn if < expected)
  ✓ Employee ID extraction (required for Stage 3)

CREDITS: 0 (preview endpoint is free)
```

---

### STAGE 3: FULL PROFILE COLLECTION (WITH CACHING) ✨

**File:** `domain_search.py` (lines 668-924)
**API Endpoint:** `/api/jd/domain-collect-profiles` (POST)

```
INPUT:
  ├─ employee_ids: [12345678, 87654321, ...] (from Stage 2)
  └─ min_year: 2020 (only enrich companies from 2020+)

PROCESS (for each employee_id):
  ┌─────────────────────────────────────────────────────────────────┐
  │ ❶ PROFILE FETCH WITH CACHE CHECK                                │
  │                                                                  │
  │  cache_key = f"id:{employee_id}"                                │
  │  cached_profile = get_stored_profile(cache_key)                 │
  │                                                                  │
  │  IF cached_profile EXISTS:                                      │
  │    ├─ Check age (stored < 90 days ago?)                         │
  │    │   ├─ < 3 days: USE CACHE (fresh) ✅                        │
  │    │   ├─ 3-90 days: USE CACHE (mark stale, consider refresh)   │
  │    │   └─ > 90 days: FORCE FRESH FETCH (too old) ⚠️             │
  │    └─ Log: "Using stored profile (age: X days) - SAVED 1 credit"│
  │                                                                  │
  │  ELSE:                                                           │
  │    ├─ CoreSignal API call: /v2/employee_clean/collect/{id}      │
  │    ├─ save_stored_profile(cache_key, profile_data, timestamp)   │
  │    └─ Log: "Fetched and cached profile - 1 CREDIT USED"         │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ ❷ COMPANY ENRICHMENT WITH CACHE                                 │
  │                                                                  │
  │  FOR EACH work_experience in profile:                           │
  │    ├─ Filter: start_year >= min_year (2020+)  ← CREDIT SAVER   │
  │    ├─ Filter: First 3 companies (most recent)                   │
  │    │                                                             │
  │    ├─ cache_check = get_stored_company(company_id)              │
  │    │   ├─ IF cached & age < 30 days:                            │
  │    │   │   └─ USE CACHE - SAVED 1 credit ✅                     │
  │    │   │                                                         │
  │    │   └─ ELSE:                                                 │
  │    │       ├─ CoreSignal API: /v2/company_base/collect/{id}     │
  │    │       ├─ save_stored_company(company_id, company_data)     │
  │    │       └─ 1 CREDIT USED                                     │
  │    │                                                             │
  │    └─ Extract: funding, growth, Crunchbase URL, etc.            │
  └─────────────────────────────────────────────────────────────────┘

OUTPUT (for each profile):
  ├─ profile_data: {full_name, headline, work_experience[], ...}
  ├─ enrichment_summary:
  │   ├─ companies_enriched: 3
  │   ├─ api_calls_made: 1 (if 2 were cached)
  │   ├─ companies_cached: 2
  │   └─ companies_skipped_old: 15 (pre-2020)
  │
  └─ cache_info:  ✨ NEW ✨
      ├─ profile_from_cache: true/false
      ├─ profile_cache_age_days: 5
      ├─ companies_from_cache: 2
      └─ companies_fetched: 1

LOGGING:
  ├─ 03_full_profiles.json (structured data with cache stats)
  ├─ 03_collection_progress.jsonl (streaming, 1 line per profile)
  ├─ 03_collection_summary.txt:
  │     CACHE PERFORMANCE:  ✨ NEW SECTION ✨
  │       Profiles from cache: 18/20 (90%)
  │       Profiles fetched: 2/20 (10%)
  │       Companies from cache: 54/60 (90%)
  │       Companies fetched: 6/60 (10%)
  │       Credits saved: 72/80 (90%)
  │       Credits used: 8 (vs 80 without cache)
  │
  └─ Per-profile enrichment details

INTERMEDIATE CHECKS:
  ✓ Cache freshness validation (3/90 days profiles, 30 days companies)
  ✓ Profile fetch success/failure tracking
  ✓ Company enrichment filter (2020+, first 3, valid years)
  ✓ API rate limiting: 18 req/sec → throttle to 10 req/sec (0.1s sleep)
  ✓ Enrichment summary validation (companies_enriched count)
  ✓ JSONL progress logging (event: profile_collected/profile_failed)

CREDITS (COLD CACHE - First Search):
  ├─ Profile fetches: 20 profiles × 1 credit = 20 credits
  └─ Company fetches: ~60 companies × 1 credit = 60 credits
  TOTAL: ~80 credits ($16)

CREDITS (WARM CACHE - Second Search):
  ├─ Profile fetches: 2 profiles × 1 credit = 2 credits (90% cache hit)
  └─ Company fetches: ~6 companies × 1 credit = 6 credits (90% cache hit)
  TOTAL: ~8 credits ($1.60)
  SAVINGS: 72 credits ($14.40) - 90% reduction! 🎉
```

---

### STAGE 4: AI EVALUATION (STREAMING TO FRONTEND)

**File:** `domain_search.py` (lines 928-1162)
**API Endpoint:** `/api/jd/domain-evaluate-stream` (POST)

```
INPUT:
  ├─ collected_profiles: [20 enriched profiles from Stage 3]
  └─ jd_requirements: {must_have, nice_to_have, domain, seniority, ...}

PROCESS (for each profile):
  ├─ Build Evaluation Prompt
  │   ├─ JD Requirements (must-have, nice-to-have, seniority)
  │   ├─ Profile Summary (experience, skills, companies)
  │   └─ Evaluation Criteria (domain fit, seniority match, trajectory)
  │
  ├─ Claude Sonnet 4.5 API Call
  │   ├─ Temperature: 0.1 (deterministic)
  │   ├─ Max tokens: 2000
  │   └─ Structured output: {overall_score, reasoning, red_flags, ...}
  │
  └─ Stream Progress via SSE (Server-Sent Events)
      ├─ yield f"data: {json.dumps({'event': 'profile_start', ...})}\n\n"
      ├─ yield f"data: {json.dumps({'event': 'profile_complete', ...})}\n\n"
      └─ Frontend updates UI in real-time ✨

OUTPUT (for each profile):
  ├─ overall_score: 8.5 / 10
  ├─ domain_fit_score: 9 / 10
  ├─ seniority_match: "excellent"
  ├─ reasoning: "Strong voice AI background at Deepgram..."
  ├─ red_flags: ["No management experience"]
  └─ recommendation: "strong_yes"

LOGGING:
  ├─ 04_ai_evaluation.json (all evaluations)
  ├─ 04_evaluation_summary.txt:
  │     TOP CANDIDATES (sorted by score):
  │       1. John Doe (9.2/10) - Deepgram → AssemblyAI
  │       2. Jane Smith (8.7/10) - OpenAI → Hugging Face
  │
  └─ Statistics: avg_score, top 5, distribution

INTERMEDIATE CHECKS:
  ✓ LLM response parsing validation (JSON extraction)
  ✓ Score range validation (1-10)
  ✓ Streaming event format validation
  ✓ Error handling for API failures (retry logic)

CREDITS: ~$0.15 per profile × 20 = ~$3.00 (Claude Sonnet 4.5)
```

---

## 🗄️ SESSION FILE STRUCTURE

```
backend/logs/domain_search_sessions/
└── sess_20251105_a1b2c3d4/
    ├── 00_session_metadata.json          # Session ID, timestamp, status
    │
    ├── 01_company_discovery.json         # STAGE 1 structured output
    ├── 01_company_discovery_debug.txt    # STAGE 1 human-readable
    │
    ├── 02_preview_search.json            # STAGE 2 structured output
    ├── 02_preview_analysis.txt           # STAGE 2 human-readable
    │
    ├── 03_full_profiles.json             # STAGE 3 structured output
    ├── 03_collection_progress.jsonl      # STAGE 3 streaming (1 line per profile)
    ├── 03_collection_summary.txt         # STAGE 3 human-readable + CACHE STATS ✨
    │
    ├── 04_ai_evaluation.json             # STAGE 4 structured output
    └── 04_evaluation_summary.txt         # STAGE 4 human-readable
```

---

## 💾 SUPABASE CACHING LAYER

### Cache Tables

```sql
-- Profile caching (employee_clean data)
TABLE: stored_profiles
├─ linkedin_url (PRIMARY KEY): "id:12345678" or "https://..."
├─ profile_data (JSONB): {full profile from CoreSignal employee_clean}
├─ last_fetched (TIMESTAMP): "2025-11-05T14:30:00Z"
├─ checked_at (FLOAT): 1699200000.123
└─ created_at / updated_at

-- Company caching (company_base data)
TABLE: stored_companies
├─ company_id (PRIMARY KEY): 98765432
├─ company_data (JSONB): {full company data from CoreSignal company_base}
├─ last_fetched (TIMESTAMP): "2025-11-05T14:30:00Z"
├─ user_verified (BOOLEAN): false
├─ verification_status (TEXT): "pending" | "verified" | "rejected"
└─ created_at / updated_at
```

### Freshness Rules

- **Profiles:** < 3 days = fresh | 3-90 days = stale | > 90 days = force refresh
- **Companies:** < 30 days = fresh | > 30 days = force refresh

### Implementation

**Module:** `utils/supabase_storage.py`
**Functions:**
- `get_stored_profile(linkedin_url)` - Check cache with freshness logic
- `save_stored_profile(linkedin_url, profile_data, checked_at)` - Save for future searches
- `get_stored_company(company_id, freshness_days=30)` - Check company cache
- `save_stored_company(company_id, company_data)` - Save company data

---

## 💰 CREDIT CONSUMPTION BREAKDOWN

### Before Caching (All Searches)

```
Stage 1: Company Discovery         →    0 credits (web search only)
Stage 2: Preview Search            →    0 credits (preview endpoint free)
Stage 3: Profile Collection
  ├─ Fetch 20 profiles @ 1 credit  → +20 credits
  └─ Enrich 60 companies @ 1 credit→ +60 credits
Stage 4: AI Evaluation @ $0.15     → ~$3.00
─────────────────────────────────────────────────
TOTAL PER SEARCH: 80 credits ($16) + $3 LLM = $19/search

10 SEARCHES: 800 credits ($160) + $30 LLM = $190 total ❌
```

### After Caching (2nd+ Searches)

```
Stage 1: Company Discovery         →    0 credits
Stage 2: Preview Search            →    0 credits
Stage 3: Profile Collection (90% cache hit)
  ├─ Fetch 2 profiles @ 1 credit   →  +2 credits (18 cached)
  └─ Enrich 6 companies @ 1 credit →  +6 credits (54 cached)
Stage 4: AI Evaluation @ $0.15     → ~$3.00
─────────────────────────────────────────────────
TOTAL PER SEARCH: 8 credits ($1.60) + $3 LLM = $4.60/search

10 SEARCHES:
  - 1st search: 80 credits ($16) + $3 = $19
  - 9 more searches: 72 credits ($14.40) + $27 = $41.40
  - TOTAL: 152 credits ($30.40) + $30 = $60.40 total ✅

SAVINGS: $190 - $60.40 = $129.60 saved (68% reduction) 🎉
```

---

## 🧪 COMPREHENSIVE TESTING STRATEGY

### TEST 1: COLD START (First Search - Cache Empty)

**Goal:** Validate pipeline with empty cache

**Setup:**
- Clear Supabase tables: `DELETE FROM stored_profiles; DELETE FROM stored_companies;`
- Prepare test JD: `{"target_domain": "voice ai", "max_previews": 5}`

**Steps:**
1. POST `/api/jd/domain-company-preview-search` (Stages 1+2)
2. Extract employee_ids from response
3. POST `/api/jd/domain-collect-profiles` (Stage 3)
4. POST `/api/jd/domain-evaluate-stream` (Stage 4)

**Expected Results:**
- Stage 1: ~30-50 companies discovered
- Stage 2: ~5 preview candidates found
- Stage 3:
  - Profiles from cache: 0/5 (0%)
  - Companies from cache: 0/15 (0%)
  - Credits used: ~20-25 (5 profiles + 15 companies)
- Supabase:
  - stored_profiles: 5 new rows
  - stored_companies: 15 new rows
- Session logs: 9 files created (00-04 series)
- Cache stats in `03_collection_summary.txt`: "Credits used: 20"

**Validation Checklist:**
- [ ] Check `03_collection_summary.txt` for cache performance section
- [ ] Query Supabase: `SELECT COUNT(*) FROM stored_profiles` → expect 5
- [ ] Query Supabase: `SELECT COUNT(*) FROM stored_companies` → expect ~15
- [ ] Verify `last_fetched` timestamps are recent (within 1 minute)

---

### TEST 2: WARM START (Second Search - Cache Hit)

**Goal:** Validate 90% cache hit rate

**Setup:**
- Use SAME JD as Test 1 (should hit same profiles/companies)
- Run immediately after Test 1 (< 3 days, < 30 days freshness)

**Steps:**
1. POST `/api/jd/domain-company-preview-search` (Stages 1+2)
2. POST `/api/jd/domain-collect-profiles` (Stage 3)

**Expected Results:**
- Stage 3:
  - Profiles from cache: 5/5 (100%) ✅
  - Companies from cache: 14/15 (93%) ✅
  - Credits used: ~1-2 (only 1-2 API calls)
- Console logs:
  - "✅ Using stored profile (age: 0 days) - SAVED 1 Collect credit!" × 5
  - "✅ Using stored company... - SAVED 1 Collect credit!" × 14
- Supabase:
  - stored_profiles: Still 5 rows (no new inserts)
  - stored_companies: Still ~15 rows (maybe 1 new if different company found)

**Validation Checklist:**
- [ ] Check `03_collection_summary.txt`: "Credits saved: 19/20 (95%)"
- [ ] Verify cache_age_days in cache_info is 0
- [ ] Compare credits used: Test 1 (~20) vs Test 2 (~1-2) = 90% savings

---

### TEST 3: CACHE FRESHNESS VALIDATION

**Goal:** Verify freshness rules work correctly

**Scenario A: Profile Staleness (3-90 days)**
- Setup: Manually update `stored_profiles.last_fetched` to 10 days ago
- Expected: Profile used from cache but marked as stale
- Validation: Log shows "Profile is 10 days old, consider refreshing soon"

**Scenario B: Profile Expiration (> 90 days)**
- Setup: Manually update `stored_profiles.last_fetched` to 100 days ago
- Expected: Profile FORCED fresh fetch (cache bypassed)
- Validation: Log shows "FORCING fresh pull" + API call made

**Scenario C: Company Expiration (> 30 days)**
- Setup: Manually update `stored_companies.last_fetched` to 35 days ago
- Expected: Company data fetched fresh (cache bypassed)
- Validation: API call made for that company

---

### TEST 4: ERROR HANDLING & EDGE CASES

**Goal:** Validate robustness

**Scenario A: Supabase Down**
- Setup: Temporarily disable SUPABASE_URL env var
- Expected: Fall back to API calls (graceful degradation)
- Validation: Warning logged, credits used as if no cache

**Scenario B: Profile Not Found**
- Setup: Use invalid employee_id (99999999)
- Expected: Error logged to `03_collection_progress.jsonl`
- Validation: `{"event": "profile_failed", "error": "Not found"}`

**Scenario C: Rate Limiting**
- Setup: Request 50 profiles (triggers 0.1s sleep)
- Expected: 50 profiles collected in ~5 seconds (10 req/sec)
- Validation: Check duration in `03_collection_summary.txt`

---

### TEST 5: END-TO-END PIPELINE VALIDATION

**Goal:** Validate complete 4-stage flow

**Steps:**
1. Stage 1: Verify 30+ companies discovered
2. Stage 2: Verify 20 preview candidates found
3. Stage 3: Verify all 20 profiles collected + enriched
4. Stage 4: Verify all 20 profiles evaluated with scores

**Critical Checks:**
- [ ] session_id consistent across all stages
- [ ] employee_ids from Stage 2 match Stage 3 collected profiles
- [ ] All 9 session log files created
- [ ] JSON files are valid (parseable)
- [ ] TXT files are human-readable
- [ ] JSONL files have 1 JSON object per line

**Performance Benchmarks:**
- Stage 1: < 30 seconds (company discovery)
- Stage 2: < 5 seconds (preview search)
- Stage 3: < 10 seconds (with cache) or < 60 seconds (without cache)
- Stage 4: < 40 seconds (20 profiles × 2 seconds each)
- **Total: < 2 minutes with cache, < 2.5 minutes without**

---

## 📋 DATA UNIFORMITY

### Endpoint Usage

**Employee Data:** `/v2/employee_clean/collect/{employee_id}`
- Preferred for database storage consistency
- Used in Stage 2 (preview) and Stage 3 (full profile collection)

**Company Data:** `/v2/company_base/collect/{company_id}`
- Provides 45+ fields including logos, funding, growth data
- Used in Stage 3 (company enrichment)

**Rationale:**
- `employee_clean` provides consistent profile structure across searches
- `company_base` has richer data than `company_clean` (critical for intelligence)
- Storing raw JSONB data ensures we never lose fields and can adapt later

---

## 🎯 KEY INSIGHTS

### Cache Hit Rate Targets
- **Profile cache:** 90-100% (same candidates appear in multiple searches)
- **Company cache:** 80-95% (overlap in companies across searches)

### Critical Validations
- Freshness rules enforced (3/90 days profiles, 30 days companies)
- No duplicate API calls within same session
- Cache stats accurate in session logs
- Supabase data integrity (JSONB valid, timestamps correct)

### Performance Benchmarks
- **Cold start:** ~80 credits, ~60 seconds for Stage 3
- **Warm start:** ~8 credits, ~10 seconds for Stage 3
- **10x speedup + 90% cost savings**

### Error Handling
- Supabase down → graceful fallback to API
- Profile not found → logged but doesn't crash
- Rate limiting → 0.1s sleep between requests
- Invalid JSON → caught and logged with details

---

## 📊 Success Metrics

**Cost Efficiency:**
- First search: $19 (baseline)
- Subsequent searches: $4.60 (76% reduction per search)
- 10 searches: $60.40 vs $190 (68% total savings)

**Performance:**
- Cold cache: ~2.5 minutes end-to-end
- Warm cache: ~2 minutes end-to-end
- 20% speed improvement + 90% cache hit rate

**Data Quality:**
- 100% profile collection success rate (with valid employee_ids)
- 95%+ company enrichment success rate
- Zero data loss with JSONB storage

---

**End of Documentation**
