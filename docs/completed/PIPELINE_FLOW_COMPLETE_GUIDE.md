# Complete Pipeline Flow & Session Management Guide

**Created:** November 10, 2025
**Status:** ✅ Post-Fix Documentation
**Purpose:** Comprehensive guide to data flow, session tracking, credit optimization, and UI representation

---

## 🎯 Executive Summary

**Pipeline:** 4-Stage Progressive Search (Company Discovery → Preview Search → Full Collection → AI Evaluation)
**Credit Model:** Pay-per-profile (1 credit each), Preview is FREE
**Caching:** 3-day freshness, 90-day reuse, Supabase-backed
**Session Storage:** Dual system (File logs + Supabase tables)

---

## 📊 STAGE-BY-STAGE FLOW

### **Stage 1: Company Discovery** (0 Credits)

#### **INPUT:**
```json
{
  "jd_requirements": {
    "target_domain": "voice ai",
    "role_title": "Senior ML Engineer",
    "mentioned_companies": ["Observe.AI", "Krisp"],
    "technical_skills": ["Python", "PyTorch"],
    "location": "San Francisco, USA"
  }
}
```

#### **PROCESS:**
1. **Web Search** (Tavily API)
   - Domain-specific: "voice ai companies G2"
   - Seed expansion: "Observe.AI competitors"
   - Generates up to 6 search queries, executes top 5

2. **AI Screening** (GPT-5-mini)
   - Batch: 20 companies at a time
   - Filters: Relevance, size, exclude list
   - Ranks by domain fit score

3. **CoreSignal ID Lookup** (4-tier strategy)
   - Tier 1: Direct from company_crunchbase_info
   - Tier 2a: Tavily search for Crunchbase URL
   - Tier 2b: Claude Agent WebSearch validation
   - Tier 3: Heuristic slug generation

#### **OUTPUT:**
```json
{
  "companies_discovered": 50,
  "companies_with_ids": 45,
  "match_rate": 0.90,
  "companies": [
    {
      "name": "Observe.AI",
      "coresignal_company_id": 11209012,
      "coresignal_searchable": true,
      "lookup_tier": 1,
      "website": "https://observe.ai",
      "discovered_via": "Web Search",
      "domain_fit_score": 0.95
    }
  ]
}
```

#### **STORED IN:**
- **Files:** `01_company_discovery.json`, `01_company_ids.json`
- **Supabase:** `cached_searches` table (90-day TTL)
- **Session Metadata:**
  ```json
  {
    "stage1_results": {
      "companies_discovered": 50,
      "companies_with_ids": 45,
      "match_rate": 0.90,
      "excluded_companies": ["DLAI", "AI Fund"]
    }
  }
  ```

#### **CREDITS USED:** 0 (Company lookups are free)

---

### **Stage 2: Preview Search** ⭐ (0 Credits - FREE!)

#### **INPUT:**
```json
{
  "companies": [
    {"name": "Observe.AI", "coresignal_company_id": 11209012},
    {"name": "Krisp", "coresignal_company_id": 21473726}
  ],
  "role_keywords": ["ml engineer", "ai engineer", "research scientist"],
  "location": "San Francisco, USA",
  "endpoint": "employee_base",
  "max_previews": 100
}
```

#### **PROCESS:**

**Step 1: Build Experience-Based Query** (✅ JUST FIXED)
```json
{
  "query": {
    "bool": {
      "must": [{
        "nested": {
          "path": "experience",
          "query": {
            "bool": {
              "must": [
                {
                  "term": {"experience.company_id": 11209012}
                },
                {
                  "query_string": {
                    "query": "\"ml engineer\" OR \"ai engineer\" OR \"research scientist\"",
                    "default_field": "experience.title",
                    "default_operator": "OR"  // ← CRITICAL FIX!
                  }
                }
              ]
            }
          }
        }
      }]
    }
  }
}
```

**Step 2: Search for Employee IDs** (FREE)
- API: `/employee_base/search/es_dsl`
- Returns: Up to 1,000 employee IDs
- Cost: 0 credits

**Step 3: Preview Endpoint** (FREE)
- API: `/employee_base/search/es_dsl/preview`
- Returns: First 100 profiles
- Cost: 0 credits (preview is always free!)

**Step 4: Cache Preview Profiles**
- Save to `stored_profiles` table
- Cache key: `"id:{employee_id}"`
- Freshness: <3 days (reuse), >90 days (refresh)

**Step 5: Store ALL Employee IDs in Session**
```python
# Supabase search_sessions table
session_manager.store_employee_ids(
    session_id=session_id,
    employee_ids=[1234, 5678, ...],  # Up to 1000 IDs
    profiles_offset=100  # Pagination cursor
)
```

#### **OUTPUT:**
```json
{
  "session_id": "sess_20251110_155000_abc123",
  "total_previews_found": 1511,  // Total available
  "stage2_previews": [  // First 100 (FREE)
    {
      "name": "John Doe",
      "title": "Senior ML Engineer",
      "current_company": "Observe.AI",
      "location": "Bangalore, India",
      "experience": [
        {
          "company_name": "Observe.AI",
          "title": "ML Engineer",
          "start_date": "2020-01-01",
          "end_date": null
        }
      ],
      "years_experience": 8.5,
      "domain_company_experience": true
    }
  ],
  "relevance_score": 0.99,
  "location_distribution": {
    "India": 892,
    "Armenia": 234,
    "United States": 145,
    "Other": 240
  },
  "filter_precision": 0.75,
  "role_keywords_used": ["ml engineer", "ai engineer", "research scientist"],
  "search_method": "experience_based"
}
```

#### **STORED IN:**

**Files:**
- `02_preview_query.json` - The ES DSL query sent to CoreSignal
- `02_preview_results.json` - All 100 preview profiles
- `02_preview_analysis.txt` - Quality metrics text report

**Supabase:**
```sql
-- search_sessions table
{
  "session_id": "sess_20251110_155000_abc123",
  "employee_ids": [1234, 5678, ..., 9012],  // ALL 1511 IDs
  "profiles_offset": 100,  // Current pagination position
  "jd_context": {...},  // For "Evaluate More" button
  "company_batches": [[batch1], [batch2]],  // 5-company progressive search
  "status": "stage2_complete"
}

-- stored_profiles table (Cache)
{
  "cache_key": "id:1234567",
  "profile_data": {...},  // Full CoreSignal profile
  "cached_at": "2025-11-10T15:50:00Z",
  "last_accessed": "2025-11-10T15:50:00Z",
  "access_count": 1
}
```

**Session Metadata:**
```json
{
  "stage2_results": {
    "search_method": "experience_based",
    "total_employee_ids": 1511,
    "previews_fetched": 100,
    "relevance_score": 0.99,
    "location_distribution": {...},
    "filter_precision": 0.75,
    "role_keywords_used": ["ml engineer", "ai engineer"],
    "cache_stats": {
      "cached": 3,
      "fetched": 97,
      "failed": 0
    }
  }
}
```

#### **CREDITS USED:** 0 (Preview is FREE! 🎉)

#### **VALUE TO USER:**
- ✅ See 100 candidates for free
- ✅ Validate search quality before paying
- ✅ Filter/sort/select best candidates
- ✅ Only pay for profiles you want

---

### **Stage 3: Full Profile Collection** (1 Credit Each)

#### **INPUT:**
```json
{
  "session_id": "sess_20251110_155000_abc123",
  "start_index": 100,  // Pagination (0=first 100, 100=next 100, etc.)
  "count": 50  // How many to collect
}
```

#### **PROCESS:**

**Step 1: Load Employee IDs from Session**
```python
# Get next batch from stored IDs
employee_ids = session_manager.get_employee_ids(session_id)
batch_ids = employee_ids[start_index:start_index+count]  // [100:150]
```

**Step 2: Check Cache First** (Credit Savings!)
```python
cached_profiles = []
new_ids = []

for employee_id in batch_ids:
    cached = supabase_cache.get_profile(employee_id)

    if cached and cached['age_days'] < 3:
        # ✅ Recent cache (< 3 days) - Use for FREE
        cached_profiles.append(cached['profile_data'])
    elif cached and cached['age_days'] < 90:
        # ✅ Stale cache (< 90 days) - Reuse for FREE
        cached_profiles.append(cached['profile_data'])
    else:
        # ❌ No cache or too old (> 90 days) - Collect (1 credit)
        new_ids.append(employee_id)
```

**Step 3: Collect New Profiles** (1 Credit Each)
```python
# API: /employee_base/collect/{employee_id}
for employee_id in new_ids:
    profile = coresignal_api.collect(employee_id)  // 1 credit
    supabase_cache.cache_profile(employee_id, profile)
    new_profiles.append(profile)
```

**Step 4: Enrich with Company Data** (2020+ only, saves 60-80% credits)
```python
# Only fetch company data for recent jobs (2020+)
for profile in all_profiles:
    for exp in profile['experience']:
        if exp['start_year'] >= 2020:
            company_data = get_company_data(exp['company_id'])  // 1 credit per company
            exp['company_intelligence'] = company_data
```

**Step 5: Update Session Pagination**
```python
session_manager.increment_profiles_offset(session_id, count)
# profiles_offset: 100 → 150
```

#### **OUTPUT:**
```json
{
  "profiles": [
    {
      "id": 1234567,
      "name": "John Doe",
      "title": "Senior ML Engineer",
      "headline": "Building AI systems at scale",
      "location": "Bangalore, India",
      "experience": [
        {
          "title": "Senior ML Engineer",
          "company_name": "Observe.AI",
          "company_id": 11209012,
          "start_date": "2020-01-01",
          "end_date": null,
          "description": "Led ML team...",
          "company_intelligence": {  // ← Enriched!
            "industry": "Voice AI",
            "employee_count": 273,
            "funding_total": "$125M",
            "last_funding_date": "2023-05-15",
            "growth_signals": ["Rapid hiring", "Series C"]
          }
        },
        {
          "title": "ML Engineer",
          "company_name": "Google",
          "company_id": 98765,
          "start_date": "2018-01-01",
          "end_date": "2019-12-31",
          "description": "Worked on Search..."
          // No company_intelligence (pre-2020)
        }
      ],
      "education": [...],
      "skills": [...],
      "total_experience_years": 8.5,
      "domain_company_years": 4.5
    }
  ],
  "cache_stats": {
    "cached": 12,  // ✅ FREE (from cache)
    "fetched": 38,  // ❌ 38 credits used
    "failed": 0
  },
  "credits_used": 38,
  "estimated_savings": "💾 Saved 12 credits by using cached profiles"
}
```

#### **STORED IN:**

**Files:**
- `03_full_profiles.json` - All collected profiles
- `03_collection_progress.jsonl` - Line-by-line progress log
- `03_collection_summary.txt` - Credits used, cache hit rate

**Supabase:**
```sql
-- stored_profiles updated with new profiles
-- stored_companies cached for 2020+ jobs
-- search_sessions.profiles_offset updated to 150
```

#### **CREDITS USED:**
- **New profiles:** 1 credit each
- **Cached profiles:** 0 credits (FREE reuse!)
- **Company data:** 1 credit per unique company (2020+ only)

#### **VALUE TO USER:**
- ✅ Only pay for what you collect
- ✅ Cache reduces repeat costs
- ✅ Progressive loading (collect 10, review, collect 20 more)
- ✅ 2020+ company filter saves 60-80% on enrichment

---

### **Stage 4: AI Evaluation** (0 CoreSignal Credits)

#### **INPUT:**
```json
{
  "profiles": [/* Full profiles from Stage 3 */],
  "jd_requirements": {
    "must_have": ["5+ years ML", "Python", "LLMs"],
    "nice_to_have": ["Voice AI experience"],
    "domain": "voice ai",
    "role_title": "Senior ML Engineer"
  },
  "weighted_requirements": [
    {"requirement": "Voice AI Expertise", "weight": 35},
    {"requirement": "ML Infrastructure", "weight": 25},
    {"requirement": "0→1 Product Leadership", "weight": 20}
  ]
}
```

#### **PROCESS:**
1. **Claude Sonnet 4.5 Evaluation**
   - Temperature: 0.1 (consistency)
   - Analyzes each profile against JD requirements
   - Scores: domain_fit (1-10), experience_match (1-10), overall_fit (1-10)

2. **Weighted Scoring**
   ```python
   weighted_score = (
       (voice_ai_score * 0.35) +
       (ml_infrastructure_score * 0.25) +
       (product_leadership_score * 0.20) +
       (general_fit * 0.20)
   )
   ```

3. **Ranking & Recommendations**
   - Sort by weighted_score (descending)
   - Generate "Why this candidate" summary
   - Flag concerns/gaps

#### **OUTPUT:**
```json
{
  "evaluated_profiles": [
    {
      "profile": {/* Full profile from Stage 3 */},
      "evaluation": {
        "voice_ai_expertise": {
          "score": 9,
          "analysis": "4 years at Observe.AI building production voice AI systems. Led team of 5 ML engineers. Deep expertise in ASR, NLP."
        },
        "ml_infrastructure": {
          "score": 8,
          "analysis": "Built ML pipelines at scale. Experience with PyTorch, Kubeflow, MLOps best practices."
        },
        "product_leadership": {
          "score": 7,
          "analysis": "Led 0→1 product at Observe.AI. Took feature from ideation to 10M+ users."
        },
        "weighted_score": 8.35,
        "overall_fit": 8,
        "recommendation": "Strong Hire - Excellent voice AI background, proven leadership",
        "concerns": ["Limited experience with LLMs (pre-2023)"]
      }
    }
  ],
  "top_candidates": [/* Top 10 */],
  "evaluation_summary": {
    "total_evaluated": 50,
    "strong_hires": 8,
    "good_fits": 15,
    "weak_fits": 27
  }
}
```

#### **STORED IN:**

**Files:**
- `04_ai_evaluations.json` - All evaluations
- `04_evaluation_summary.txt` - Top candidates report

**Session Metadata:**
```json
{
  "stage4_results": {
    "evaluated_count": 50,
    "top_score": 8.35,
    "strong_hires": 8,
    "evaluation_duration_seconds": 125
  }
}
```

#### **CREDITS USED:** 0 CoreSignal credits (Claude API costs only)

---

## 💰 CREDIT OPTIMIZATION SUMMARY

### **Credit Costs:**
| Stage | Action | Cost | Notes |
|-------|--------|------|-------|
| Stage 1 | Company Discovery | **0 credits** | Company lookups are free |
| Stage 2 | Preview Search (100) | **0 credits** | Preview endpoint is FREE |
| Stage 2 | Store 1000 IDs | **0 credits** | Search returns IDs for free |
| Stage 3 | Collect NEW profile | **1 credit** | Pay per profile |
| Stage 3 | Collect CACHED profile (<90 days) | **0 credits** | FREE reuse! |
| Stage 3 | Company enrichment (2020+) | **1 credit** | Per unique company |
| Stage 4 | AI Evaluation | **0 credits** | Claude API only |

### **Cache Strategy:**
```
Profile Freshness Tiers:
├─ <3 days: Use immediately (100% fresh)
├─ 3-90 days: Reuse (acceptable staleness)
└─ >90 days: Refresh (too stale, 1 credit)

Company Cache:
├─ 2020+ jobs only (saves 60-80% credits)
├─ Deduplicated (same company = 1 credit for all profiles)
└─ Includes funding, growth signals, employee count
```

### **Optimization Best Practices:**

**✅ DO:**
1. **Preview First (FREE)** - Always review 100 candidates before collecting
2. **Batch Small** - Collect 10-20 at a time, review quality
3. **Check Cache** - UI shows "12 cached (free), 8 new (8 credits)"
4. **Progressive Loading** - User controls budget

**❌ DON'T:**
5. **Auto-collect 1000** - Expensive! Show estimate first
6. **Ignore cache** - Massive savings opportunity
7. **Collect without review** - Preview lets you filter first

---

## 🗂️ SESSION INFORMATION ARCHITECTURE

### **Dual Storage System:**

```
File System (logs/domain_search_sessions/sess_XXXXX/)
├─ 00_session_metadata.json      [Session state + all stage results]
├─ 01_company_discovery.json     [50 discovered companies]
├─ 01_company_ids.json           [45 companies with CoreSignal IDs]
├─ 02_preview_query.json         [ES DSL query sent to API]
├─ 02_preview_results.json       [100 preview profiles]
├─ 02_preview_analysis.txt       [Quality metrics report]
├─ 03_full_profiles.json         [Collected full profiles]
├─ 03_collection_progress.jsonl  [Real-time collection log]
├─ 03_collection_summary.txt     [Credits used, cache stats]
├─ 04_ai_evaluations.json        [AI-scored candidates]
└─ 04_evaluation_summary.txt     [Top candidates report]

Supabase (Global)
├─ search_sessions               [Session state + pagination]
│  ├─ session_id (PK)
│  ├─ employee_ids: [1,2,...,1000]
│  ├─ profiles_offset: 100
│  ├─ jd_context: {...}
│  └─ status: "stage2_complete"
├─ stored_profiles               [Profile cache]
│  ├─ cache_key: "id:1234567"
│  ├─ profile_data: {...}
│  ├─ cached_at, last_accessed
│  └─ access_count: 3
├─ stored_companies              [Company cache]
│  ├─ company_id: 11209012
│  ├─ company_data: {...}
│  └─ cached_at
└─ cached_searches               [Result cache]
   ├─ cache_key: MD5(jd_requirements)
   ├─ stage1_companies: [...]
   └─ ttl: 90 days
```

### **Session Lifecycle:**

```
User submits JD
    ↓
session_id = generate_uuid()  // sess_20251110_155000_abc123
    ↓
Create session directory + Supabase row
    ↓
Stage 1: companies → 00_metadata.json (update)
    ↓
Stage 2: employee_ids → Supabase search_sessions
         previews → 02_preview_results.json
         cache → stored_profiles
    ↓
Stage 3: full profiles → 03_full_profiles.json
         cache → stored_profiles + stored_companies
         offset → Supabase (100 → 150 → 200...)
    ↓
Stage 4: evaluations → 04_ai_evaluations.json
    ↓
Session complete (status: "stage4_complete")
    ↓
Session persists for 90 days (cache TTL)
```

---

## 🎨 UI REPRESENTATION RECOMMENDATIONS

### **Stage 2: Preview Dashboard** (100 FREE Candidates)

#### **Top Metrics Bar:**
```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 Search Results                                            │
│                                                              │
│ ✅ 1,511 candidates found                                    │
│ 👀 Previewing: 100 (FREE)                                   │
│ 🎯 Relevance: 99% have domain experience                    │
│ 📍 Locations: 59% India, 15% Armenia, 10% US, 16% Other    │
│ 💼 Role Match: 75% match target keywords                    │
│                                                              │
│ [View All Locations ▼] [Filter by Role ▼]                  │
└──────────────────────────────────────────────────────────────┘
```

#### **Preview Card (Compact):**
```
┌──────────────────────────────────────────────────────────────┐
│ ☐ John Doe                                         [Quick View]│
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ Senior ML Engineer at Observe.AI                            │
│ 📍 Bangalore, India  │  🎓 8.5 years exp                    │
│                                                              │
│ 🏢 Domain Experience: Observe.AI (2020-present)            │
│ 💡 Keywords Match: ml engineer, voice ai, research         │
│                                                              │
│ [✓ Select for Full Evaluation]  [✗ Reject]  [📋 Save]     │
└──────────────────────────────────────────────────────────────┘
```

#### **Selection Actions:**
```
┌──────────────────────────────────────────────────────────────┐
│ Selected: 25 profiles                                        │
│                                                              │
│ 💰 Credit Estimate:                                         │
│   • 10 cached (FREE) ✅                                     │
│   • 15 new (15 credits) 💳                                  │
│                                                              │
│   Estimated Savings: $30 (cache hit rate: 40%)             │
│                                                              │
│ [Collect Selected Profiles (15 credits)] [Cancel]          │
└──────────────────────────────────────────────────────────────┘
```

### **Stage 3: Collection Progress**

```
┌──────────────────────────────────────────────────────────────┐
│ 🔄 Collecting Profiles...                                    │
│                                                              │
│ Progress: ████████████░░░░░░░░ 18/25 (72%)                 │
│                                                              │
│ ✅ Collected: 18  (10 from cache, 8 new)                   │
│ ⏳ Remaining: 7                                             │
│ 💳 Credits Used: 8 / 15 estimated                          │
│                                                              │
│ [Pause] [Cancel]                                            │
└──────────────────────────────────────────────────────────────┘
```

### **Stage 3: Full Profile View**

```
┌──────────────────────────────────────────────────────────────┐
│ John Doe  ━  💾 Cached 2 days ago (FREE)  ━  [Edit]        │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ Senior ML Engineer at Observe.AI                            │
│ 📍 Bangalore, India  │  🎓 8.5 years experience            │
│                                                              │
│ ━━ Work Experience ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                              │
│ 🏢 Observe.AI  │  2020-Present  │  4 years                │
│ Senior ML Engineer                                          │
│ • Built production voice AI systems serving 10M+ users     │
│ • Led team of 5 ML engineers                               │
│ • Improved ASR accuracy from 85% → 93%                     │
│                                                              │
│ Company Intel: 🚀                                           │
│ • Series C, $125M raised                                    │
│ • 273 employees (growing 45% YoY)                          │
│ • Voice AI / Call Center Analytics                         │
│ • Rapid hiring (20 ML roles open)                          │
│                                                              │
│ 🏢 Google  │  2018-2020  │  2 years                       │
│ ML Engineer                                                 │
│ • Worked on Search ranking algorithms                       │
│ (No company data - pre-2020 job)                           │
│                                                              │
│ ━━ Skills ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Python • PyTorch • TensorFlow • NLP • Voice AI • MLOps     │
│                                                              │
│ [✓ Strong Hire] [? Maybe] [✗ Reject] [📋 Add to List]    │
└──────────────────────────────────────────────────────────────┘
```

### **Stage 4: AI Evaluation Dashboard**

```
┌──────────────────────────────────────────────────────────────┐
│ 🎯 Top Candidates  ━  50 Evaluated  ━  8 Strong Hires      │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                              │
│ 1. John Doe  ━  Score: 8.35/10  ━  [View Profile]          │
│    Senior ML Engineer • Observe.AI                          │
│    ✅ Voice AI Expertise (9/10) ━ 35% weight               │
│    ✅ ML Infrastructure (8/10) ━ 25% weight                │
│    ✅ Product Leadership (7/10) ━ 20% weight               │
│                                                              │
│    💡 Why: 4 years voice AI, led 0→1 products, strong tech │
│    ⚠️  Concern: Limited LLM experience                     │
│                                                              │
│    [Schedule Interview] [Share] [Add to Pipeline]          │
│                                                              │
│ 2. Jane Smith  ━  Score: 8.2/10  ━  [View Profile]         │
│    ...                                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Progressive Budget Control:**

```
┌──────────────────────────────────────────────────────────────┐
│ 💳 Credit Budget Dashboard                                   │
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                              │
│ Today's Usage:                                              │
│ • Stage 2 Preview: 100 profiles (0 credits) ✅             │
│ • Stage 3 Collected: 25 profiles (15 credits) 💳           │
│ • Company Enrichment: 8 companies (8 credits) 💳           │
│                                                              │
│ Total: 23 credits used                                      │
│ Savings: 10 credits (cache hit rate: 40%)                  │
│                                                              │
│ Remaining IDs: 1,486 available to collect                   │
│                                                              │
│ [Load More 50 (~35 credits)] [Custom Batch]               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 WHAT'S NEXT: Pipeline Enhancements

### **Priority 1: Credit Budget Controls**
- [ ] Pre-collection credit estimate modal
- [ ] Daily/weekly credit budget limits
- [ ] Alert when approaching budget threshold
- [ ] Credit usage analytics dashboard

### **Priority 2: Smart Caching UI**
- [ ] Cache age indicator on each card
- [ ] "Refresh stale profiles" batch action
- [ ] Cache hit rate trends over time
- [ ] Estimated savings tracker

### **Priority 3: Progressive Evaluation**
- [ ] Collect 10 → Review → Collect 20 more workflow
- [ ] A/B test: Preview vs Full profile quality
- [ ] Stop/pause/resume collection controls
- [ ] Undo last batch action

### **Priority 4: Session Recovery**
- [ ] Resume interrupted sessions
- [ ] Share session links with team
- [ ] Export session data (CSV, JSON)
- [ ] Archive old sessions (>90 days)

---

## ✅ VERIFICATION CHECKLIST

### **Data Flow:**
- [x] Stage 1 → companies stored in files + Supabase
- [x] Stage 2 → employee_ids (1000+) stored in Supabase search_sessions
- [x] Stage 2 → preview profiles (100) cached in stored_profiles
- [x] Stage 3 → full profiles cached in stored_profiles + stored_companies
- [x] Stage 4 → evaluations stored in files only

### **Credit Optimization:**
- [x] Preview is FREE (0 credits for 100 profiles)
- [x] Cache reuse within 90 days (FREE)
- [x] Company enrichment only 2020+ (60-80% savings)
- [x] Batch collection user-controlled
- [ ] Pre-collection credit estimate shown
- [ ] Daily budget alerts

### **Session Management:**
- [x] Dual storage (files + Supabase)
- [x] Pagination cursor (profiles_offset) updated correctly
- [x] All 1000 employee_ids stored for Load More
- [x] Session persists 90 days
- [ ] Session resume after interruption
- [ ] Session sharing links

---

## 📝 KEY TAKEAWAYS

1. **Preview is FREE** - Always start with 100 preview candidates (0 credits)
2. **Cache Saves Money** - 40% cache hit rate = 40% credit savings
3. **Progressive Loading** - User controls budget (collect 10, review, collect 20 more)
4. **Session Persistence** - All data stored for 90 days (files + Supabase)
5. **2020+ Enrichment** - Company data only for recent jobs (60-80% savings)
6. **1000 IDs Stored** - Can paginate through all results without re-searching

---

**Document Version:** 1.0
**Last Updated:** November 10, 2025
**Next Review:** After user testing and feedback
