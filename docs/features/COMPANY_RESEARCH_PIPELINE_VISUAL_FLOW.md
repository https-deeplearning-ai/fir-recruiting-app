# Company Research Pipeline - Visual Flow Guide

**Complete End-to-End Flow with API Calls, Data Structures, and Timing**

**Version:** 2.0 (Enriched Companies with GPT-5 Scoring)
**Last Updated:** November 11, 2025
**Status:** Production

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Stage 1: User Input & JD Parsing](#2-stage-1-user-input--jd-parsing)
3. [Stage 2: Company Discovery](#3-stage-2-company-discovery)
4. [Stage 3: GPT-5-mini Screening (NEW)](#4-stage-3-gpt-5-mini-screening-new)
5. [Stage 4: Sample Employee Fetching (NEW)](#5-stage-4-sample-employee-fetching-new)
6. [Stage 5: Enriched UI Display (NEW)](#6-stage-5-enriched-ui-display-new)
7. [Stage 6: Employee Search](#7-stage-6-employee-search)
8. [Data Structures Reference](#8-data-structures-reference)
9. [Cost & Performance Analysis](#9-cost--performance-analysis)
10. [Cache Strategy](#10-cache-strategy)

---

## 1. High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPANY RESEARCH PIPELINE V2.0                        │
│                    (Enriched with GPT-5 Scoring)                         │
└─────────────────────────────────────────────────────────────────────────┘

USER INPUT (JD Text)
       ↓
┌──────────────────┐
│  Stage 1: Parse  │  ⏱️  3-5s    💰 $0.10
│                  │  Claude Sonnet 4.5
│  Extract:        │  - Role requirements
│  - Requirements  │  - Industry keywords
│  - Keywords      │  - Company examples
└────────┬─────────┘
         ↓
┌────────────────────────┐
│  Stage 2: Discovery    │  ⏱️  30-45s  💰 $20
│                        │  Multi-method search
│  Method 1: Seed        │  - Tavily API
│    Expansion (15 co's) │  - CoreSignal lookups
│  Method 2: Web Search  │
│    (6 queries, top 5)  │
│                        │
│  Result: ~100 cos      │
└───────────┬────────────┘
            ↓
┌─────────────────────────────┐
│  Stage 3: GPT-5 Screening   │  ⏱️  10-15s  💰 $5  ✨ NEW
│         (Batch)             │  GPT-5-mini
│                             │
│  Input: 100 companies       │  - Tavily descriptions
│  Batch Size: 20 at a time  │  - CoreSignal metadata
│  Output: relevance_score    │  - Industry, size, location
│         (1-10 scale)        │
│                             │
│  Result: Scored companies   │
└──────────────┬──────────────┘
               ↓
┌──────────────────────────────┐
│  Stage 4: Sample Employees   │  ⏱️  30-40s  💰 $15  ✨ NEW
│         (Proof of Talent)    │  CoreSignal employee_clean
│                              │
│  For each company:           │  - 3-5 employees per co
│  - Query employee_clean      │  - Name, title, location
│  - Fetch 3-5 profiles        │  - Proof of talent pool
│                              │
│  Result: Companies with      │
│          sample employees    │
└─────────────┬────────────────┘
              ↓
┌──────────────────────────────────┐
│  Stage 5: Enriched UI Display    │  ⏱️  Instant  💰 $0  ✨ NEW
│                                  │  React rendering
│  Features:                       │
│  ✓ Relevance score badges        │  - 8+ = Green
│  ✓ Metadata pills                │  - 7-8 = Orange
│  ✓ Industry, employee count      │  - 6-7 = Red
│  ✓ Expandable employee sections  │  - <6 = Gray
│  ✓ Filter pills (8+, 7-8, 6-7)  │
│                                  │
│  User Action: Select companies   │
└─────────────┬────────────────────┘
              ↓
┌──────────────────────────────┐
│  Stage 6: Employee Search     │  ⏱️  3-6s    💰 $5
│         (Domain Search)       │  ES DSL query (FIXED)
│                               │
│  Build Query:                 │  - Company filter (MUST)
│  - Company IDs (MUST)         │  - Role filter (SHOULD)
│  - Role keywords (SHOULD) ✨  │  - Location (SHOULD)
│  - Location (SHOULD)          │
│                               │
│  CoreSignal Search:           │  - employee_clean endpoint
│  - Returns 50-500 candidates │  - Sorted by relevance
│                               │
│  Result: Rich candidate cards │
└───────────────────────────────┘

TOTAL PIPELINE:
⏱️  Time: 70-100 seconds
💰 Cost: ~$40 per session
🔄 Cache: 48 hours (makes repeat runs $0)
```

---

## 2. Stage 1: User Input & JD Parsing

### 2.1 User Flow

```
┌─────────────────────────────────────────────┐
│  Frontend: App.js (Company Research View)   │
└─────────────────────────────────────────────┘

User pastes JD text into textarea
         ↓
Clicks "Start Company Research" button
         ↓
Frontend calls: POST /research-companies

Request Payload:
{
  "jd_text": "We're hiring a Senior ML Engineer...",
  "jd_data": null,  // Will be parsed by backend
  "config": {
    "discovery_methods": ["seed_expansion", "web_search"],
    "max_companies": 100
  },
  "force_refresh": false  // Set to true to bypass cache
}
```

### 2.2 Backend Processing

**File:** `backend/app.py` (line 2991)

```python
@app.route('/research-companies', methods=['POST'])
async def research_companies():
    # Step 1: Extract JD requirements
    if not jd_data:
        jd_parser = JDParser(claude_client)
        jd_requirements = jd_parser.parse(jd_text)
        jd_data = jd_requirements.dict()

    # Step 2: Create research session
    jd_id = f"jd_{hash(jd_text)[:16]}"

    # Step 3: Check cache
    cache_path = Path(f"./research-companies/{jd_id}/results/results.json")
    if cache_path.exists() and not force_refresh:
        # Return cached results
        return cached_results

    # Step 4: Start research pipeline
    service = CompanyResearchService(...)
    results = await service.research_companies_for_jd(jd_data, jd_id)

    return {
        "session_id": jd_id,
        "discovered_companies": results['discovered_objects'],  # Enriched!
        "screened_companies": results['screened_companies'],
        "evaluated_companies": results['evaluated_companies']
    }
```

### 2.3 JD Parsing Output

**Data Structure: `JDRequirements`**

```json
{
  "role_title": "Senior ML Engineer",
  "seniority_level": "senior",
  "must_have": [
    "5+ years ML experience",
    "Python, PyTorch",
    "LLM experience"
  ],
  "nice_to_have": [
    "Voice AI experience",
    "Real-time systems"
  ],
  "technical_skills": ["Python", "PyTorch", "LLMs", "Voice AI"],
  "domain_expertise": ["NLP", "Speech Recognition"],
  "experience_years": {
    "minimum": 5,
    "preferred": 8
  },
  "location": "San Francisco Bay Area",
  "company_keywords": ["Otter.ai", "Deepgram", "AssemblyAI"],
  "industry_keywords": ["Voice AI", "Real-time Communication"],
  "excluded_companies": ["DLAI", "AI Fund"]  // User's own companies
}
```

**Timing:** 3-5 seconds
**Cost:** $0.10 (Claude Sonnet 4.5, ~2K tokens)

---

## 3. Stage 2: Company Discovery

### 3.1 Discovery Architecture

```
┌────────────────────────────────────────────────────────────────┐
│           COMPANY DISCOVERY (Multi-Method)                     │
└────────────────────────────────────────────────────────────────┘

INPUT: JD Requirements
       ↓
┌──────────────────────────────────────┐
│  Method 1: Seed Expansion            │  70% of results
│                                      │
│  Seeds: Up to 15 mentioned companies│  (e.g., "Otter.ai", "Deepgram")
│  Filter: Exclude user's companies   │  (DLAI, AI Fund)
│                                      │
│  For each seed (15 companies):      │
│    Tavily Search 1: "{seed} competitors"
│    Tavily Search 2: "companies like {seed}"
│    Tavily Search 3: "{seed} alternatives"
│                                      │
│  Extract from results:               │
│    - Company names                   │
│    - Descriptions (Tavily)           │
│    - Source URLs                     │
│                                      │
│  Deduplicate by name                 │
│                                      │
│  Result: ~70 companies               │
└─────────────┬────────────────────────┘
              │
              │  PARALLEL
              │
┌─────────────┴────────────────────────┐
│  Method 2: Web Search                │  30% of results
│                                      │
│  Generate 6 queries:                 │
│    - 2 domain-specific (G2, Capterra)│
│    - 3 seed-based                    │
│    - 1 generic fallback              │
│                                      │
│  Priority ranking:                   │
│    1. Domain (G2/Capterra)           │
│    2. Top 3 seed companies           │
│    3. Industry keywords              │
│    4. Generic fallback               │
│                                      │
│  Execute top 5 queries (cost limit)  │
│                                      │
│  Extract company names from:         │
│    - Authoritative sources           │
│    - Article headings                │
│    - Comparison tables               │
│                                      │
│  Result: ~30 companies               │
└──────────────┬───────────────────────┘
               ↓
         MERGE & DEDUPE
               ↓
    ~100 Unique Companies
               ↓
┌──────────────────────────────────────┐
│  CoreSignal Company ID Lookup        │  Batch
│                                      │
│  For each company:                   │
│    POST /v2/company_base/search/     │
│         exact_name_match             │
│                                      │
│    Returns: coresignal_company_id    │
│                                      │
│  Store:                              │
│    - Company name                    │
│    - CoreSignal ID                   │
│    - Tavily description              │
│    - Source URL                      │
│                                      │
│  Result: 100 companies with IDs      │
└──────────────────────────────────────┘
```

### 3.2 Discovery Code Flow

**File:** `backend/company_research_service.py` (line 83)

```python
async def research_companies_for_jd(self, jd_context, jd_id):
    # Phase 1: Discovery
    discovered = []

    # Method 1: Seed Expansion (up to 15 seeds)
    mentioned_companies = jd_context.get('company_keywords', [])
    excluded_companies = jd_context.get('excluded_companies', [])

    # Filter seeds (remove excluded companies BEFORE expansion)
    valid_seeds = [c for c in mentioned_companies
                   if not is_excluded_company(c)][:15]

    for seed in valid_seeds:
        # 3 Tavily searches per seed
        queries = [
            f"{seed} competitors",
            f"companies like {seed}",
            f"{seed} alternatives"
        ]

        for query in queries:
            results = tavily_client.search(query, max_results=10)
            companies = extract_companies_from_results(results)

            # Filter excluded companies again
            companies = [c for c in companies
                        if not is_excluded_company(c['name'])]

            discovered.extend(companies)

    # Method 2: Web Search (6 queries, execute top 5)
    web_queries = generate_web_queries(jd_context, valid_seeds)
    web_queries_ranked = rank_queries(web_queries)[:5]

    for query in web_queries_ranked:
        results = tavily_client.search(query, max_results=10)
        companies = extract_companies_from_results(results)
        companies = [c for c in companies
                    if not is_excluded_company(c['name'])]
        discovered.extend(companies)

    # Deduplicate by name (case-insensitive)
    discovered = deduplicate_by_name(discovered)

    print(f"[DISCOVERY] Found {len(discovered)} unique companies")

    # Lookup CoreSignal IDs
    for company in discovered:
        coresignal_id = await lookup_company_id(company['name'])
        company['coresignal_id'] = coresignal_id
        company['coresignal_data'] = await fetch_company_base(coresignal_id)

    return discovered  # ~100 companies
```

### 3.3 Discovery Data Structure

```json
{
  "name": "Loom",
  "discovered_via": "seed_expansion",
  "source_query": "Kumospace competitors",
  "source_url": "https://www.g2.com/products/kumospace/competitors",
  "source_result_rank": 3,

  // Tavily enrichment
  "description": "Loom is async video messaging for work...",
  "website": "https://www.loom.com",

  // CoreSignal enrichment
  "coresignal_id": 12345678,
  "coresignal_data": {
    "name": "Loom",
    "industry": "Software Development",
    "size": "201-500 employees",
    "founded": 2016,
    "location_hq_city": "San Francisco",
    "location_hq_country": "United States",
    "website": "loom.com",
    // ... 40+ more fields
  }
}
```

**Timing:** 30-45 seconds
**Cost:** ~$20 (Tavily searches + CoreSignal lookups)

---

## 4. Stage 3: GPT-5-mini Screening (NEW)

### 4.1 Screening Architecture

```
┌───────────────────────────────────────────────────────────────┐
│           GPT-5-MINI BATCH SCREENING (NEW)                    │
└───────────────────────────────────────────────────────────────┘

INPUT: 100 discovered companies (with enriched data)
       ↓
┌──────────────────────────────────────┐
│  Batch Processing (20 companies)     │
│                                      │
│  Batch 1: Companies 0-19             │
│  Batch 2: Companies 20-39            │
│  Batch 3: Companies 40-59            │
│  Batch 4: Companies 60-79            │
│  Batch 5: Companies 80-99            │
└──────────────┬───────────────────────┘
               ↓
      For each batch:
               ↓
┌──────────────────────────────────────┐
│  Build Screening Prompt              │
│                                      │
│  Context:                            │
│    - JD requirements (must-have,     │
│      nice-to-have, domain)           │
│    - Target role, seniority          │
│    - Location preferences            │
│                                      │
│  For each company in batch:          │
│    - Name                            │
│    - Description (Tavily)            │
│    - Industry (CoreSignal)           │
│    - Employee count (CoreSignal)     │
│    - Location (CoreSignal)           │
│    - Founded year                    │
│                                      │
│  Task:                               │
│    "Rate relevance 1-10 for finding  │
│     candidates matching this JD"     │
└──────────────┬───────────────────────┘
               ↓
       GPT-5-mini API Call
               ↓
┌──────────────────────────────────────┐
│  Parse Response (JSON)               │
│                                      │
│  Output per company:                 │
│  {                                   │
│    "company_name": "Loom",           │
│    "relevance_score": 8.5,           │
│    "reasoning": "Strong match..."    │
│  }                                   │
└──────────────┬───────────────────────┘
               ↓
    Aggregate all batches
               ↓
┌──────────────────────────────────────┐
│  Attach Scores to Companies          │
│                                      │
│  For each company:                   │
│    company['relevance_score'] = 8.5  │
│    company['screening_score'] = 8.5  │
│    company['scored_by'] = 'gpt5_mini'│
│    company['reasoning'] = "..."      │
└──────────────┬───────────────────────┘
               ↓
    Sort by relevance_score (desc)
               ↓
  100 Scored Companies (8.5 → 3.2)
```

### 4.2 Screening Code Flow

**File:** `backend/company_research_service.py` (line 165)

```python
async def research_companies_for_jd(self, jd_context, jd_id):
    # ... after discovery phase (100 companies)

    # Phase 2: Batch Screening (NEW)
    await self._update_session_status(jd_id, "running", {
        "phase": "screening",
        "action": f"Scoring {len(discovered)} companies for relevance..."
    })

    print(f"\n{'='*80}")
    print(f"[SCREENING] Starting GPT-5-mini batch screening on {len(discovered)} companies...")
    print(f"{'='*80}\n")

    # Call GPT-5-mini screening
    screening_scores = await self.batch_screen_companies_gpt5(
        discovered,
        jd_context
    )

    # Attach scores to company objects
    for i, company in enumerate(discovered):
        company['relevance_score'] = screening_scores[i] if i < len(screening_scores) else 5.0
        company['screening_score'] = company['relevance_score']  # Alias
        company['scored_by'] = 'gpt5_mini'

    # Sort by score (highest first)
    discovered_sorted = sorted(
        discovered,
        key=lambda c: c.get('relevance_score', 0),
        reverse=True
    )

    print(f"[SCREENING] Completed! Score range: {min(screening_scores):.1f} - {max(screening_scores):.1f}")
    print(f"[SCREENING] Top 10 companies:")
    for i, c in enumerate(discovered_sorted[:10], 1):
        print(f"  {i}. {c['name']} - Score: {c['relevance_score']:.1f}")

    return discovered_sorted
```

### 4.3 Screening Prompt Template

**File:** `backend/gpt5_client.py` (line 89)

```python
SCREENING_PROMPT = """
You are evaluating companies for their relevance in finding candidates for a job.

JOB REQUIREMENTS:
- Role: {role_title}
- Seniority: {seniority_level}
- Must-Have: {must_have}
- Nice-to-Have: {nice_to_have}
- Domain: {domain_expertise}
- Location: {location}

COMPANIES TO EVALUATE (Batch {batch_num}):

{company_list}

For each company, provide:
1. Relevance Score (1-10): How likely this company has matching candidates
   - 9-10: Perfect match (e.g., direct competitors in same domain)
   - 7-8: Strong match (e.g., similar tech stack, adjacent market)
   - 5-6: Moderate match (e.g., same industry, different product)
   - 3-4: Weak match (e.g., some overlap but distant)
   - 1-2: Poor match (e.g., unrelated industry)

2. Brief Reasoning (1 sentence)

Output JSON:
[
  {
    "company_name": "...",
    "relevance_score": 8.5,
    "reasoning": "..."
  },
  ...
]
"""
```

### 4.4 Screening Output

**Data Structure: Enriched Company with Score**

```json
{
  "name": "Loom",
  "discovered_via": "seed_expansion",

  // Discovery data (Stage 2)
  "description": "Async video messaging for work",
  "coresignal_id": 12345678,
  "industry": "Software Development",
  "employees_count": 350,
  "location_hq_city": "San Francisco",
  "founded": 2016,

  // Screening data (Stage 3) - NEW
  "relevance_score": 8.5,
  "screening_score": 8.5,
  "scored_by": "gpt5_mini",
  "reasoning": "Strong match - real-time communication platform with ML infra, likely has voice AI engineers"
}
```

**Timing:** 10-15 seconds (5 batches × 2-3s per batch)
**Cost:** ~$5 (GPT-5-mini, 100 companies × 200 tokens = 20K tokens)

---

## 5. Stage 4: Sample Employee Fetching (NEW)

### 5.1 Employee Sampling Architecture

```
┌───────────────────────────────────────────────────────────────┐
│         SAMPLE EMPLOYEE FETCHING (Proof of Talent)            │
└───────────────────────────────────────────────────────────────┘

INPUT: 100 scored companies
       ↓
For each company (sequential):
       ↓
┌──────────────────────────────────────┐
│  Build Employee Search Query         │
│                                      │
│  Query Type 1 (Preferred):           │
│    Use CoreSignal company_id         │
│    {                                 │
│      "query": {                      │
│        "nested": {                   │
│          "path": "experience",       │
│          "query": {                  │
│            "term": {                 │
│              "experience.company_id":│
│                12345678              │
│            }                         │
│          }                           │
│        }                             │
│      },                              │
│      "size": 5                       │
│    }                                 │
│                                      │
│  Query Type 2 (Fallback):            │
│    Use company name (if no ID)       │
│    {                                 │
│      "query": {                      │
│        "nested": {                   │
│          "path": "experience",       │
│          "query": {                  │
│            "match": {                │
│              "experience.company_name"│
│                : "Loom"              │
│            }                         │
│          }                           │
│        }                             │
│      },                              │
│      "size": 5                       │
│    }                                 │
└──────────────┬───────────────────────┘
               ↓
    POST /v2/employee_clean/search/
           es_dsl/preview?page=1
               ↓
┌──────────────────────────────────────┐
│  Parse Response                      │
│                                      │
│  Extract for each employee:          │
│    - ID                              │
│    - Name                            │
│    - Title (current)                 │
│    - Headline (generated)            │
│    - Location                        │
│                                      │
│  Sample Size: 3-5 employees          │
└──────────────┬───────────────────────┘
               ↓
    Attach to company object
               ↓
┌──────────────────────────────────────┐
│  company['sample_employees'] = [     │
│    {                                 │
│      "id": 87654321,                 │
│      "name": "Jane Doe",             │
│      "title": "ML Engineer",         │
│      "headline": "ML Engineer at     │
│                   Loom",             │
│      "location": "San Francisco, CA" │
│    },                                │
│    ...                               │
│  ]                                   │
│                                      │
│  company['sample_employees_count']   │
│    = 5                               │
└──────────────────────────────────────┘

Repeat for all 100 companies
       ↓
 100 Companies with Sample Employees
```

### 5.2 Employee Sampling Code Flow

**File:** `backend/company_research_service.py` (line 1633)

```python
async def _add_sample_employees_to_companies(
    self,
    companies: List[Dict[str, Any]],
    jd_context: Dict[str, Any],
    jd_id: Optional[str] = None,
    limit_per_company: int = 5
) -> List[Dict[str, Any]]:
    """
    Add sample employees to each company using employee_clean preview.
    """
    headers = {
        "accept": "application/json",
        "apikey": self.coresignal_api_key,
        "Content-Type": "application/json"
    }

    import requests

    await self._update_session_status(jd_id, "running", {
        "phase": "employee_sampling",
        "action": f"Fetching sample employees for {len(companies)} companies..."
    })

    print(f"\n{'='*80}")
    print(f"[EMPLOYEE SAMPLING] Fetching 3-5 employees per company...")
    print(f"{'='*80}\n")

    for i, company in enumerate(companies, 1):
        company_name = company.get("name") or company.get("company_name")
        coresignal_id = company.get("coresignal_id") or company.get("coresignal_company_id")

        if not company_name:
            company['sample_employees'] = []
            continue

        try:
            # Build query - prefer company ID, fallback to name
            if coresignal_id:
                query = {
                    "query": {
                        "nested": {
                            "path": "experience",
                            "query": {
                                "term": {
                                    "experience.company_id": coresignal_id
                                }
                            }
                        }
                    },
                    "size": limit_per_company
                }
            else:
                # Fallback to company name matching
                query = {
                    "query": {
                        "nested": {
                            "path": "experience",
                            "query": {
                                "match": {
                                    "experience.company_name": company_name
                                }
                            }
                        }
                    },
                    "size": limit_per_company
                }

            url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

            response = requests.post(url, json=query, headers=headers, timeout=10)

            if response.status_code == 200:
                employees = response.json()

                company['sample_employees'] = [
                    {
                        "id": emp.get("id"),
                        "name": emp.get("name") or emp.get("full_name"),
                        "title": emp.get("title") or emp.get("headline", "").split(" at ")[0] if emp.get("headline") else "N/A",
                        "headline": emp.get("headline") or emp.get("generated_headline"),
                        "location": emp.get("location")
                    }
                    for emp in employees[:limit_per_company]
                ]

                company['sample_employees_count'] = len(company['sample_employees'])

                if len(company['sample_employees']) > 0:
                    print(f"  [{i}/{len(companies)}] ✓ {company_name}: {len(company['sample_employees'])} employees")
                else:
                    print(f"  [{i}/{len(companies)}] ○ {company_name}: No employees found")
            else:
                company['sample_employees'] = []
                company['sample_employees_count'] = 0
                print(f"  [{i}/{len(companies)}] ✗ {company_name}: API error {response.status_code}")

        except Exception as e:
            company['sample_employees'] = []
            company['sample_employees_count'] = 0
            print(f"  [{i}/{len(companies)}] ✗ {company_name}: Exception - {str(e)[:50]}")

        # Rate limiting (avoid overwhelming CoreSignal API)
        await asyncio.sleep(0.3)  # 300ms between requests

    print(f"\n[EMPLOYEE SAMPLING] Completed!")
    successful = len([c for c in companies if c.get('sample_employees_count', 0) > 0])
    print(f"  ✓ {successful}/{len(companies)} companies have sample employees")

    return companies
```

### 5.3 Employee Sampling Output

**Data Structure: Company with Sample Employees**

```json
{
  "name": "Loom",
  "relevance_score": 8.5,
  "industry": "Software Development",
  "employees_count": 350,

  // Employee sampling data (Stage 4) - NEW
  "sample_employees": [
    {
      "id": 87654321,
      "name": "Jane Doe",
      "title": "Senior ML Engineer",
      "headline": "Senior ML Engineer at Loom | Voice AI | Real-time Systems",
      "location": "San Francisco, CA"
    },
    {
      "id": 87654322,
      "name": "John Smith",
      "title": "AI Research Scientist",
      "headline": "AI Research Scientist at Loom | NLP | Speech Recognition",
      "location": "Remote"
    },
    {
      "id": 87654323,
      "name": "Alice Johnson",
      "title": "ML Infrastructure Engineer",
      "headline": "ML Infrastructure Engineer at Loom | Python | PyTorch",
      "location": "New York, NY"
    }
  ],
  "sample_employees_count": 3
}
```

**Timing:** 30-40 seconds (100 companies × 0.3s + API latency)
**Cost:** ~$15 (100 companies × 1 search × $0.15)

---

## 6. Stage 5: Enriched UI Display (NEW)

### 6.1 Frontend Rendering

```
┌───────────────────────────────────────────────────────────────┐
│                   ENRICHED UI DISPLAY (NEW)                   │
└───────────────────────────────────────────────────────────────┘

BACKEND RESPONSE:
{
  "session_id": "jd_a80e3eb3f1aa41da",
  "discovered_companies": [  // 100 companies, sorted by relevance_score
    {
      "name": "Loom",
      "relevance_score": 8.5,
      "industry": "Software Development",
      "employees_count": 350,
      "sample_employees": [...],
      "sample_employees_count": 3
    },
    ...
  ]
}
       ↓
FRONTEND: App.js (line 3665)
       ↓
┌──────────────────────────────────────┐
│  Parse Response                      │
│                                      │
│  setState:                           │
│    setDiscoveredCompanies(           │
│      response.discovered_companies   │
│    )                                 │
│    setCompanySessionId(session_id)   │
│    setCompanyScoreFilter('all')      │
└──────────────┬───────────────────────┘
               ↓
         RENDER UI
               ↓
┌──────────────────────────────────────┐
│  Filter Pills Section                │
│                                      │
│  [All (100)] [8+ (25)] [7-8 (35)]   │
│  [6-7 (30)] [<6 (10)]                │
│                                      │
│  User clicks filter → updates state  │
└──────────────┬───────────────────────┘
               ↓
    filteredCompanies = discoveredCompanies
      .filter(c => matchesScoreFilter(c))
               ↓
┌──────────────────────────────────────┐
│  Company List (Checkboxes)           │
│                                      │
│  For each company:                   │
│    ┌─────────────────────────────┐  │
│    │ ☐ #1 [8.5] Loom             │  │
│    │    🏢 Software Development  │  │
│    │    👥 350 employees         │  │
│    │                             │  │
│    │    👥 Sample Employees (3)  │  │
│    │    ▼ Click to expand        │  │
│    │                             │  │
│    │    [Expanded View]          │  │
│    │    - Jane Doe              │  │
│    │      Senior ML Engineer     │  │
│    │      📍 San Francisco, CA  │  │
│    │                             │  │
│    │    - John Smith            │  │
│    │      AI Research Scientist │  │
│    │      📍 Remote             │  │
│    │                             │  │
│    │    - Alice Johnson         │  │
│    │      ML Infra Engineer     │  │
│    │      📍 New York, NY       │  │
│    └─────────────────────────────┘  │
│                                      │
│    ┌─────────────────────────────┐  │
│    │ ☐ #2 [8.2] Miro             │  │
│    │    🏢 Collaboration Tools   │  │
│    │    👥 1.2K employees        │  │
│    │    ...                      │  │
│    └─────────────────────────────┘  │
└──────────────┬───────────────────────┘
               ↓
  User selects 3-5 companies
               ↓
┌──────────────────────────────────────┐
│  "Search for People" Button          │
│                                      │
│  onClick:                            │
│    - Clear previous search results   │
│    - Pass selected companies to      │
│      employee search (Stage 6)       │
└──────────────────────────────────────┘
```

### 6.2 UI Component Code

**File:** `frontend/src/App.js` (line 4055)

```javascript
// Filter pills
<div className="discovered-filters">
  <span className="filter-label">Filter by Score:</span>
  <button
    className={`filter-pill ${companyScoreFilter === 'all' ? 'active' : ''}`}
    onClick={() => setCompanyScoreFilter('all')}
  >
    All ({discoveredCompanies.length})
  </button>
  <button
    className={`filter-pill ${companyScoreFilter === '8+' ? 'active' : ''}`}
    onClick={() => setCompanyScoreFilter('8+')}
  >
    8+ ({discoveredCompanies.filter(c => (c.relevance_score || 0) >= 8).length})
  </button>
  {/* More filter buttons */}
</div>

// Company list
{filteredCompanies.map((company, idx) => {
  const companyName = company.name || company.company_name;

  return (
    <div key={idx} className="discovered-item-container">
      <div className="discovered-item">
        <input
          type="checkbox"
          checked={selectedCompanies.includes(company)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedCompanies([...selectedCompanies, company]);
            } else {
              setSelectedCompanies(selectedCompanies.filter(c => c !== company));
            }
          }}
        />

        <span className="discovered-rank">#{idx + 1}</span>

        {/* Relevance Score Badge */}
        {company.relevance_score && (
          <span className={`discovered-score-badge score-${getScoreBracket(company.relevance_score)}`}>
            {company.relevance_score.toFixed(1)}
          </span>
        )}

        <span className="discovered-name">{companyName || 'Unknown'}</span>

        {/* Metadata Pills */}
        {company.industry && (
          <span className="discovered-metadata-pill industry">
            🏢 {company.industry}
          </span>
        )}
        {company.employees_count && (
          <span className="discovered-metadata-pill size">
            👥 {formatEmployeeCount(company.employees_count)} employees
          </span>
        )}
      </div>

      {/* Sample Employees Section */}
      {company.sample_employees && company.sample_employees.length > 0 && (
        <details className="discovered-employees-section">
          <summary className="discovered-employees-summary">
            👥 Sample Employees ({company.sample_employees.length})
          </summary>
          <div className="discovered-employees-list">
            {company.sample_employees.map((emp, empIdx) => (
              <div key={empIdx} className="discovered-employee">
                <div className="employee-name">{emp.name || 'Unknown'}</div>
                <div className="employee-title">{emp.title || 'N/A'}</div>
                {emp.location && (
                  <div className="employee-location">📍 {emp.location}</div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
})}
```

### 6.3 UI Styling

**File:** `frontend/src/App.css` (appended)

```css
/* Relevance Score Badge Colors */
.discovered-score-badge.score-high {
  background-color: #10b981; /* Green - 8+ */
  color: white;
}

.discovered-score-badge.score-medium-high {
  background-color: #f59e0b; /* Orange - 7-8 */
  color: white;
}

.discovered-score-badge.score-medium {
  background-color: #f97316; /* Red-Orange - 6-7 */
  color: white;
}

.discovered-score-badge.score-low {
  background-color: #ef4444; /* Red - <6 */
  color: white;
}

/* Filter Pills */
.filter-pill {
  padding: 6px 12px;
  border-radius: 16px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-pill.active {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

/* Metadata Pills */
.discovered-metadata-pill.industry {
  background-color: #f3e8ff;
  color: #6b21a8;
  border: 1px solid #d8b4fe;
}

.discovered-metadata-pill.size {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

/* Employee Section */
.discovered-employees-section {
  border-top: 1px solid #f3f4f6;
  padding: 0;
}

.discovered-employees-section[open] {
  padding: 12px 14px;
  background-color: #fafafa;
}

.discovered-employee {
  padding: 8px 12px;
  border-left: 3px solid #6366f1;
  background: white;
  border-radius: 4px;
  margin-bottom: 8px;
}
```

**Timing:** Instant (client-side rendering)
**Cost:** $0

---

## 7. Stage 6: Employee Search

### 7.1 Employee Search Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   EMPLOYEE SEARCH (Domain Search)             │
└───────────────────────────────────────────────────────────────┘

USER ACTION: Selects 3-5 companies, clicks "Search for People"
       ↓
FRONTEND: App.js (line 4205)
       ↓
┌──────────────────────────────────────┐
│  Build Request Payload               │
│                                      │
│  {                                   │
│    "companies": [                    │
│      {                               │
│        "name": "Loom",               │
│        "coresignal_company_id":      │
│          12345678                    │
│      },                              │
│      ...                             │
│    ],                                │
│    "role_keywords": [                │
│      "ml engineer",                  │
│      "ai engineer",                  │
│      "voice ai"                      │
│    ],                                │
│    "location": "San Francisco",      │
│    "location_required": false,       │
│    "target_role_required": false     │
│  }                                   │
└──────────────┬───────────────────────┘
               ↓
POST /api/jd/search-candidates
               ↓
BACKEND: jd_analyzer/api/endpoints.py (line 468)
               ↓
┌──────────────────────────────────────┐
│  Build ES DSL Query (FIXED)          │
│                                      │
│  Nested Query Structure:             │
│                                      │
│  {                                   │
│    "query": {                        │
│      "bool": {                       │
│        "must": [                     │
│          {                           │
│            "nested": {               │
│              "path": "experience",   │
│              "query": {              │
│                "bool": {             │
│                  "must": [           │
│                    {  // Company     │
│                      "bool": {       │
│                        "should": [   │
│                          {"term": {  │
│                            "experience│
│                            .company_id│
│                            ": 12345678│
│                          }},          │
│                          ...         │
│                        ],            │
│                        "minimum_     │
│                         should_match"│
│                         : 1          │
│                      }               │
│                    }                 │
│                  ],                  │
│                  "should": [         │
│                    {  // Role ✨ NEW│
│                      "query_string": │
│                        {             │
│                        "query":      │
│                         "\"ml eng\" │
│                          OR \"ai eng│
│                          \"",        │
│                        "default_field│
│                         ": "exp.title│
│                         "            │
│                      }               │
│                    }                 │
│                  ],                  │
│                  "minimum_should_    │
│                   match": 0  ✨ NEW │
│                }                     │
│              }                       │
│            }                         │
│          }                           │
│        ],                            │
│        "should": [                   │
│          {  // Location              │
│            "term": {                 │
│              "location_country":     │
│                "San Francisco"       │
│            }                         │
│          }                           │
│        ]                             │
│      }                               │
│    },                                │
│    "size": 20,  // 20 per page      │
│    "_source": ["id", "name", ...]   │
│  }                                   │
│                                      │
│  KEY FIX (Nov 11, 2025):             │
│    - Company filter in MUST (req'd) │
│    - Role filter in SHOULD (boost)  │
│    - minimum_should_match: 0        │
│                                      │
│  Result: Returns ALL employees at   │
│          companies, role matches    │
│          scored higher               │
└──────────────┬───────────────────────┘
               ↓
POST /v2/employee_clean/search/es_dsl/preview
       (Pages 1-5, 20 results each)
               ↓
┌──────────────────────────────────────┐
│  Fetch Multiple Pages                │
│                                      │
│  Page 1: 20 candidates               │
│  Page 2: 20 candidates               │
│  Page 3: 20 candidates               │
│  Page 4: 20 candidates               │
│  Page 5: 20 candidates               │
│                                      │
│  Total: Up to 100 candidates         │
└──────────────┬───────────────────────┘
               ↓
  Deduplicate by employee ID
               ↓
┌──────────────────────────────────────┐
│  Enrich with Company Data            │
│                                      │
│  For each candidate:                 │
│    - Parse work experience           │
│    - Find matching company in        │
│      experience history              │
│    - Attach company enriched data    │
│      (from Stage 2 discovery)        │
└──────────────┬───────────────────────┘
               ↓
  Return 50-100 candidates
               ↓
FRONTEND: Render Rich Candidate Cards
```

### 7.2 ES DSL Query Fix (Critical)

**File:** `backend/jd_analyzer/api/domain_search.py` (line 587)

**BEFORE (BUGGY):**
```python
nested_must = [company_query]

# WRONG: Always adds role to MUST, making it required
if role_query_string:
    role_filter = {
        "query_string": {
            "query": role_query_string,
            "default_field": "experience.title"
        }
    }
    nested_must.append(role_filter)  # ❌ ALWAYS REQUIRED!

nested_bool = {"must": nested_must}
```

**Result:** Query requires BOTH company AND exact role match → 0 results

---

**AFTER (FIXED):**
```python
nested_must = [company_query]
nested_should = []

# Add role query: MUST if required, SHOULD (boost) if optional
if role_query_string:
    role_filter = {
        "query_string": {
            "query": role_query_string,
            "default_field": "experience.title",
            "default_operator": "OR"
        }
    }

    if require_target_role:
        # Role is REQUIRED - add to must
        nested_must.append(role_filter)
        print(f"   🔒 Role REQUIRED: Must match one of the role keywords")
    else:
        # Role is OPTIONAL - add to should (boosts score but not required)
        nested_should.append(role_filter)
        print(f"   ⭐ Role BOOST: Matching role keywords boosts score (optional)")

# Build nested query with proper must/should structure
nested_bool = {"must": nested_must}
if nested_should:
    nested_bool["should"] = nested_should
    nested_bool["minimum_should_match"] = 0  # Should clauses are optional
```

**Result:** Query requires ONLY company match, role provides score boost → 50-500 results ✅

---

### 7.3 Employee Search Output

**Data Structure: Rich Candidate Card**

```json
{
  "id": 87654321,
  "name": "Jane Doe",
  "title": "Senior ML Engineer",
  "headline": "Senior ML Engineer at Loom | Voice AI | Real-time Systems",
  "generated_headline": "Senior ML Engineer with 6 years experience in Voice AI",
  "location": "San Francisco, CA",
  "location_country": "United States",

  "experience": [
    {
      "company_id": 12345678,
      "company_name": "Loom",
      "title": "Senior ML Engineer",
      "date_from": "2021-03-01",
      "date_to": null,  // Current

      // Enriched company data (from Stage 2)
      "company_enriched": {
        "name": "Loom",
        "industry": "Software Development",
        "employees_count": 350,
        "founded": 2016,
        "relevance_score": 8.5,
        "description": "Async video messaging for work",
        "crunchbase_url": "https://www.crunchbase.com/organization/loom"
      }
    },
    {
      "company_id": 11111111,
      "company_name": "Google",
      "title": "ML Engineer",
      "date_from": "2018-06-01",
      "date_to": "2021-02-28"
    }
  ],

  "education": [
    {
      "degree": "MS Computer Science",
      "school": "Stanford University",
      "year": 2018
    }
  ],

  "skills": ["Python", "PyTorch", "Voice AI", "NLP"]
}
```

**Timing:** 3-6 seconds
**Cost:** ~$5 (5 pages × $1 per page)

---

## 8. Data Structures Reference

### 8.1 Discovery Phase Output

```json
{
  "name": "Loom",
  "discovered_via": "seed_expansion",
  "source_query": "Kumospace competitors",
  "source_url": "https://www.g2.com/...",
  "source_result_rank": 3,

  // Tavily enrichment
  "description": "Async video messaging for work...",
  "website": "https://www.loom.com",

  // CoreSignal enrichment
  "coresignal_id": 12345678,
  "coresignal_data": {
    "name": "Loom",
    "industry": "Software Development",
    "size": "201-500 employees",
    "employees_count": 350,
    "founded": 2016,
    "location_hq_city": "San Francisco",
    "location_hq_country": "United States",
    "website": "loom.com"
  }
}
```

### 8.2 Screening Phase Output (adds to above)

```json
{
  // ... all discovery fields ...

  // Screening enrichment (NEW)
  "relevance_score": 8.5,
  "screening_score": 8.5,
  "scored_by": "gpt5_mini",
  "reasoning": "Strong match - real-time communication platform..."
}
```

### 8.3 Employee Sampling Output (adds to above)

```json
{
  // ... all discovery + screening fields ...

  // Employee sampling enrichment (NEW)
  "sample_employees": [
    {
      "id": 87654321,
      "name": "Jane Doe",
      "title": "Senior ML Engineer",
      "headline": "Senior ML Engineer at Loom | Voice AI",
      "location": "San Francisco, CA"
    }
  ],
  "sample_employees_count": 3
}
```

### 8.4 Final API Response

```json
{
  "session_id": "jd_a80e3eb3f1aa41da",

  "discovered_companies": [  // All 100, sorted by relevance_score
    {
      "name": "Loom",
      "relevance_score": 8.5,
      "industry": "Software Development",
      "employees_count": 350,
      "sample_employees": [...],
      "sample_employees_count": 3,
      // ... all other fields
    },
    {
      "name": "Miro",
      "relevance_score": 8.2,
      // ...
    },
    // ... 98 more companies
  ],

  "screened_companies": [  // Alias for discovered_companies (legacy)
    // Same as above
  ],

  "evaluation_progress": {
    "evaluated_count": 100,
    "remaining_count": 0
  },

  "cache_info": {
    "from_cache": false,
    "cache_age_hours": 0,
    "created_at": "2025-11-11T20:57:25Z"
  }
}
```

---

## 9. Cost & Performance Analysis

### 9.1 Per-Stage Breakdown

| Stage | Component | Time | Cost | Cacheable |
|-------|-----------|------|------|-----------|
| 1 | JD Parsing | 3-5s | $0.10 | No (varies per JD) |
| 2 | Discovery | 30-45s | $20 | Yes (48h) |
| 2a | - Seed Expansion | 15-20s | $10 | Yes |
| 2b | - Web Search | 10-15s | $5 | Yes |
| 2c | - CoreSignal Lookups | 5-10s | $5 | Yes |
| 3 | GPT-5 Screening ✨ | 10-15s | $5 | Yes (48h) |
| 4 | Employee Sampling ✨ | 30-40s | $15 | Yes (48h) |
| 5 | UI Display | <1s | $0 | N/A |
| 6 | Employee Search | 3-6s | $5 | No (varies per selection) |

**Total Pipeline (Stages 1-5):** 70-100 seconds, ~$40
**Total with Employee Search (Stages 1-6):** 75-110 seconds, ~$45

### 9.2 Cache Effectiveness

**48-Hour Session Cache:**
- First run: $40
- Repeat runs (within 48h): $0
- Savings: 100%

**Typical Usage Pattern:**
- User creates research session: $40
- User refines company selection (3-5 times): $0 × 4 = $0
- User runs employee search (5 times): $5 × 5 = $25
- **Total session cost: $65** (vs $240 without cache)
- **Savings: 73%**

---

## 10. Cache Strategy

### 10.1 Cache Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                       CACHE STRATEGY                          │
└───────────────────────────────────────────────────────────────┘

JD Text
   ↓
Hash JD Requirements (deterministic)
   ↓
jd_id = "jd_a80e3eb3f1aa41da"
   ↓
Cache Path: ./research-companies/jd_a80e3eb3f1aa41da/results/
   ├── results.json (full response)
   ├── discovered_companies.json
   ├── metadata.json (cache age, created_at)
   └── logs/
       ├── 01_discovery.log
       ├── 02_screening.log
       ├── 03_sampling.log
       └── session.log

Cache Lifetime: 48 hours
Cache Key: Hash of normalized JD requirements (excludes whitespace)
Cache Invalidation: Manual (force_refresh: true) or 48h expiry
```

### 10.2 Cache Hit Flow

```
POST /research-companies
   ↓
Check cache: ./research-companies/{jd_id}/results/results.json
   ↓
File exists? → Yes
   ↓
Check age: created_at + 48h > now?
   ↓
Valid? → Yes
   ↓
Return cached results with metadata:
{
  "from_cache": true,
  "cache_age_hours": 12.5,
  "created_at": "2025-11-11T08:00:00Z",
  "discovered_companies": [...]
}
   ↓
Frontend displays orange banner:
  "📦 Cached research results (12.5 hours old)"
  [🔄 Refresh with Latest Data]
```

### 10.3 Cache Miss Flow

```
POST /research-companies
   ↓
Check cache: ./research-companies/{jd_id}/results/results.json
   ↓
File exists? → No (or expired, or force_refresh=true)
   ↓
Run full pipeline (Stages 1-4): 70-100s, $40
   ↓
Save results to cache:
  - results.json
  - metadata.json
  - logs/
   ↓
Return results with metadata:
{
  "from_cache": false,
  "cache_age_hours": 0,
  "created_at": "2025-11-11T20:57:25Z",
  "discovered_companies": [...]
}
```

### 10.4 Force Refresh

```
User clicks "🔄 Refresh with Latest Data" button
   ↓
POST /research-companies
{
  "jd_text": "...",
  "force_refresh": true  ← Bypass cache
}
   ↓
Backend ignores cache, runs full pipeline
   ↓
Overwrites cache with fresh results
   ↓
Return new results
```

---

## 11. Summary: Complete Flow Recap

**User Journey:**

1. **Paste JD** → Claude parses requirements (5s, $0.10)
2. **Discovery** → Tavily + CoreSignal find 100 companies (40s, $20)
3. **Screening** → GPT-5-mini scores relevance (15s, $5) ✨ NEW
4. **Sampling** → Fetch 3-5 employees per company (35s, $15) ✨ NEW
5. **Display** → Enriched UI with scores, metadata, employees (<1s, $0) ✨ NEW
6. **Select** → User picks 3-5 companies from top-scored list
7. **Search** → ES DSL query (FIXED) finds 50-500 candidates (5s, $5) ✨ FIXED
8. **Review** → Rich candidate cards with company enrichment

**Total Time:** 75-110 seconds
**Total Cost:** $45 (first run), $5 (cached runs)
**Cache Lifetime:** 48 hours

**Key Improvements (Nov 11, 2025):**
- ✅ GPT-5-mini relevance scoring (1-10 scale)
- ✅ Sample employee fetching (proof of talent pool)
- ✅ Enriched UI (score badges, metadata pills, expandable employees)
- ✅ Filter pills (8+, 7-8, 6-7, <6)
- ✅ ES DSL query fix (role in SHOULD, not MUST) → 0 results → 50-500 results
- ✅ Cache management UI (orange banner + refresh button)

---

**Document Version:** 2.0
**Created:** November 11, 2025
**Last Updated:** November 11, 2025
**Author:** Claude Code
**Status:** Production-Ready
