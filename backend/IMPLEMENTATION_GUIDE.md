# Deep Research Implementation Guide

## 🏗️ Architecture Overview

### System Components

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend  │────▶│   Backend API    │────▶│  Deep Research  │
│   (React)   │     │    (Flask)       │     │    Module       │
└─────────────┘     └──────────────────┘     └─────────────────┘
                             │                        │
                             ▼                        ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │   Supabase DB    │     │  External APIs  │
                    │    (Caching)     │     │  - Claude SDK   │
                    └──────────────────┘     │  - CoreSignal   │
                                             │  - Tavily       │
                                             └─────────────────┘
```

---

## 🔄 Backend Flow

### Main Orchestration
**File:** `company_research_service.py`
**Function:** `research_companies_for_jd()` (line 107)

```python
async def research_companies_for_jd(jd_id, jd_data, config):
    # 1. Create session (line 126)
    await self._create_research_session(jd_id, jd_data, config)

    # 2. Extract signals (line 129)
    jd_context = self._extract_jd_signals(jd_data)

    # 3. Discover companies (line 148)
    discovered = await self.discover_companies(
        seed_companies, jd_context, config, jd_id
    )

    # 4. Screen companies (line 181)
    screened = await self._screen_companies(discovered, jd_context, jd_id)

    # 5. Deep research (line 188) ← NEW IMPLEMENTATION
    evaluated = await self._deep_research_companies(screened[:25], jd_context, jd_id)

    # 6. Categorize (line 191)
    categorized = self.categorize_companies(evaluated, jd_context)

    # 7. Save & return (lines 194-235)
    await self._save_companies(jd_id, categorized)
    return results
```

---

## 🔬 Deep Research Process

### Core Module
**File:** `company_deep_research.py`

#### 1. Main Research Function
```python
async def research_company(
    self,
    company_name: str,
    target_domain: str,
    additional_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Line 46-104: Main entry point for deep research

    Process:
    1. Build research prompt (line 72)
    2. Configure Claude Agent SDK (lines 76-79)
    3. Execute web search with timeout (lines 82-88)
    4. Parse results (line 91)
    5. Add metadata (lines 94-97)
    6. Return enriched data (line 99)
    """
```

#### 2. Research Prompt Construction
```python
def _build_research_prompt(self, company_name, target_domain, context):
    """
    Lines 106-173: Builds comprehensive search prompt

    Searches for:
    - Company basics (website, description)
    - Products & services
    - Funding & growth
    - Technology & innovation
    - Market position
    - Recent developments (last 6 months)
    - Competitive analysis
    """
```

#### 3. Result Parsing
```python
def _parse_research_results(self, messages):
    """
    Lines 175-324: Extracts structured data from search results

    Parsing strategy:
    1. Try JSON extraction first (lines 181-189)
    2. Fallback to regex patterns (lines 192-324)

    Extracts:
    - Website (lines 194-202)
    - Description (lines 204-212)
    - Funding (lines 214-225)
    - Employee count (lines 227-233)
    - Founded year (lines 235-243)
    - Products (lines 245-256)
    - Recent news (lines 258-266)
    - Headquarters (lines 268-275)
    """
```

#### 4. Quality Assessment
```python
def _assess_quality(self, research_data):
    """
    Lines 326-347: Calculates research quality score (0-1)

    Scoring based on field completeness:
    - website: 20% weight
    - description: 20% weight
    - products: 15% weight
    - funding: 15% weight
    - employee_count: 10% weight
    - Other fields: 20% combined
    """
```

---

## 🔗 Integration with Company Research Service

### Modified Deep Research Function
**File:** `company_research_service.py`
**Lines:** 947-1053

```python
async def _deep_research_companies(self, companies, jd_context, jd_id):
    """
    NEW IMPLEMENTATION replacing shallow evaluation

    For each company:
    1. Web research via Claude SDK (lines 992-1000)
    2. CoreSignal validation (line 1003)
    3. Company data enrichment (lines 1006-1009)
    4. Employee sampling (lines 1014-1022)
    5. Evaluation with real data (lines 1025-1031)
    6. Combine all data (lines 1034-1045)
    """

    from company_deep_research import CompanyDeepResearch
    researcher = CompanyDeepResearch()

    for company in companies:
        # Step 1: Deep web research
        web_research = await researcher.research_company(...)

        # Step 2: CoreSignal validation
        company_id = await self._search_coresignal_company(...)

        # Step 3: Enrich if found
        if company_id:
            coresignal_data = await self._fetch_company_data(...)
            sample_employees = await self._sample_company_employees(...)

        # Step 4: Evaluate with ALL data
        evaluation = await self._evaluate_with_real_data(...)

        # Step 5: Combine results
        company.update({
            "web_research": web_research,
            "coresignal_id": company_id,
            "coresignal_data": coresignal_data,
            "sample_employees": sample_employees,
            "research_quality": web_research.get("research_quality", 0)
        })
```

---

## 🔍 Supporting Functions

### 1. CoreSignal Company Search
**Lines:** 1145-1192

```python
async def _search_coresignal_company(self, company_name):
    """
    Finds company_id in CoreSignal database

    Process:
    1. Clean company name (remove suffixes) - line 1155
    2. Build search query - lines 1164-1173
    3. Search via employee endpoint - line 1175
    4. Extract company_id from results - lines 1181-1188
    """
```

### 2. Company Data Fetching
**Lines:** 1194-1231

```python
async def _fetch_company_data(self, company_id):
    """
    Fetches and caches company_base data

    Features:
    - 30-day cache TTL (line 1203)
    - Supabase storage (lines 1199-1200)
    - 45+ fields from company_base endpoint
    """
```

### 3. Employee Sampling
**Lines:** 1233-1283

```python
async def _sample_company_employees(self, company_id, company_name, limit=5):
    """
    Samples employees to verify company expertise

    Returns:
    - Employee names and titles
    - Used for validation, not candidate search
    """
```

### 4. Real Data Evaluation
**Lines:** 1285-1399

```python
async def _evaluate_with_real_data(self, company_name, web_research, coresignal_data, sample_employees, jd_context):
    """
    Evaluates company using ALL collected data

    Builds context with:
    - Web research data (lines 1299-1310)
    - CoreSignal data (lines 1311-1317)
    - Sample employees (lines 1318-1321)

    Evaluation criteria:
    - Product/service overlap
    - Market position
    - Technology alignment
    - Domain expertise
    - Competitive threat level
    """
```

---

## 🌐 API Endpoints

### Main Research Endpoint
**File:** `app.py`
**Lines:** 2893-3027

```python
@app.route('/research-companies', methods=['POST'])
def research_companies_endpoint():
    """
    Starts company research for a job description

    Request body:
    {
        "jd_id": "unique_id",
        "jd_data": {
            "title": "Senior ML Engineer",
            "requirements": {...},
            "target_companies": {...}
        },
        "config": {
            "max_companies": 50,
            "use_gpt5_deep_research": true
        }
    }

    Response:
    {
        "success": true,
        "session_id": "jd_123",
        "status": "running"
    }
    """

    # Check cache (lines 2957-2996)
    # Start async research (lines 3001-3014)
    # Return session ID (lines 3016-3021)
```

### Status Check Endpoint
**Lines:** 3083-3096

```python
@app.route('/research-companies/<jd_id>/status', methods=['GET'])
def get_research_status(jd_id):
    """
    Returns current research status and progress
    Including discovered companies and evaluation progress
    """
```

---

## ⚡ Performance Optimizations

### Caching Strategy

```python
# 1. Company Data Cache (30 days)
cached = get_stored_company(company_id, freshness_days=30)

# 2. Session-based Cache (in memory)
self.cached_companies = {}  # Prevents duplicate API calls

# 3. Competitor Cache (7 days)
cached_competitors = get_cached_competitors(company_name, days=7)
```

### Timeout Management

```python
# Claude Agent SDK: 15 seconds per company
researcher.timeout = 15

# CoreSignal API: 10 seconds
response = requests.get(url, timeout=10)

# Overall research: 60 seconds for 25 companies
```

### Batch Processing

```python
# Current: Sequential (safe but slower)
for company in companies:
    await research_company(company)

# Future: Parallel (faster but needs rate limiting)
tasks = [research_company(c) for c in companies[:5]]
results = await asyncio.gather(*tasks)
```

---

## 🛠️ Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY       # Claude Agent SDK
TAVILY_API_KEY         # Company discovery
CORESIGNAL_API_KEY     # Validation & enrichment
SUPABASE_URL           # Caching database
SUPABASE_KEY           # Caching auth

# Optional
OPENAI_API_KEY         # GPT-5 evaluation fallback
```

### Rate Limits
```python
# Tavily: 1000/month (free tier)
# CoreSignal: Depends on plan
# Claude SDK: Depends on Anthropic tier
# Supabase: 500MB storage (free tier)
```

---

## 🐛 Error Handling

### Graceful Degradation

```python
try:
    # Try Claude Agent SDK
    web_research = await researcher.research_company(...)
except asyncio.TimeoutError:
    # Return minimal research
    web_research = {"error": "timeout", "research_quality": 0}

try:
    # Try CoreSignal
    company_id = await self._search_coresignal_company(...)
except Exception:
    # Continue without validation
    company_id = None

# Always return something
return {
    "web_research": web_research or {},
    "coresignal_id": company_id,
    "relevance_score": 5.0  # Default middle score
}
```

### Logging

```python
# Debug logging throughout
print(f"🔍 Deep researching {company_name}")
print(f"✅ Found CoreSignal ID: {company_id}")
print(f"📊 Evaluation Score: {score}")
print(f"⚠️ No CoreSignal data for {company_name}")
```

---

## 📊 Metrics & Monitoring

### Key Metrics to Track

1. **Research Quality**
   ```python
   average_quality = sum(c["research_quality"] for c in companies) / len(companies)
   # Target: > 0.7 (70%)
   ```

2. **Cache Hit Rate**
   ```python
   cache_hits / total_requests
   # Target: > 0.9 (90%)
   ```

3. **API Costs**
   ```python
   # Per company: ~$0.10
   # 25 companies: ~$2.50
   # With caching: ~$0.25 (90% reduction)
   ```

4. **Response Time**
   ```python
   # Per company: 5-15 seconds
   # 25 companies: 2-3 minutes
   # With parallel: < 1 minute
   ```

---

## 🔧 Troubleshooting

### Common Issues

1. **Claude Agent SDK Import Error**
   ```bash
   # Solution:
   pip install claude-agent-sdk==0.1.5
   ```

2. **Timeout Errors**
   ```python
   # Increase timeout
   researcher.timeout = 30  # 30 seconds
   ```

3. **CoreSignal Not Finding Companies**
   ```python
   # Try variations
   clean_name = company_name.replace(" Inc", "").replace(" LLC", "")
   ```

4. **Cache Not Working**
   ```python
   # Check Supabase connection
   print(os.getenv("SUPABASE_URL"))  # Should not be None
   ```

---

## 🚀 Future Enhancements

### 1. Parallel Processing
```python
# Process 5 companies at once
async def parallel_research(companies):
    semaphore = asyncio.Semaphore(5)
    async with semaphore:
        tasks = [research_company(c) for c in companies]
        return await asyncio.gather(*tasks)
```

### 2. Streaming Updates
```python
# Send progress via Server-Sent Events
def stream_progress():
    yield f"data: {json.dumps({'company': name, 'status': 'researching'})}\n\n"
```

### 3. ML Scoring
```python
# Use embeddings for better relevance scoring
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

---

## 📝 Code Style Guidelines

1. **Async/Await:** All I/O operations should be async
2. **Error Handling:** Always have try/except with fallbacks
3. **Logging:** Use print statements with emojis for clarity
4. **Type Hints:** Use typing for all function signatures
5. **Comments:** Explain WHY, not WHAT

This implementation guide provides the complete technical blueprint for understanding and extending the deep research feature.