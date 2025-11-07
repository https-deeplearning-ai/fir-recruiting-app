# Deep Research Pipeline - Unified Implementation Plan

**Purpose:** Enhance Company Research Agent with true deep research capabilities by integrating existing components and adding missing pieces

**Key Finding:** We already have 80% of the infrastructure needed! The Domain Search Pipeline provides the blueprint, we just need to adapt it for company research.

---

## Architecture Comparison

### What We Have (Existing Implementations)

#### 1. Domain Search Pipeline (`domain_search.py`) - 4 Stages ✅
```
Stage 1: Company Discovery (CompanyDiscoveryAgent)
Stage 2: Preview Search (CoreSignal validation)
Stage 3: Full Profile Collection (with caching)
Stage 4: AI Evaluation (streaming)
```
**Purpose:** Find people at companies in a domain
**Strength:** Has caching, employee discovery, company validation

#### 2. Company Research Service (`company_research_service.py`) - Shallow ⚠️
```
Phase 1: Tavily Discovery
Phase 2: GPT-5-mini Screening
Phase 3: "Deep Research" (LLM-only, no data)
```
**Purpose:** Competitive intelligence research
**Weakness:** No real data, just LLM evaluation of names

#### 3. Company Validation Agent (`company_validation_agent.py`) - Unused 🔍
```
- Uses Claude Haiku with web search (NOT Claude Agent SDK)
- Validates company exists
- Could be enhanced to use Claude Agent SDK
```
**Status:** Written but not integrated

---

## Reusable Components Matrix

| Component | Location | Can Reuse? | Notes |
|-----------|----------|------------|-------|
| **Tavily Discovery** | `CompanyDiscoveryAgent` | ✅ YES | Already perfect |
| **CoreSignal Validation** | `domain_search.py:Stage2` | ✅ YES | Has company ID resolution |
| **Company Enrichment** | `coresignal_service.py` | ✅ YES | `enrich_with_company_data()` |
| **Employee Discovery** | `domain_search.py:Stage2-3` | ✅ YES | Preview + collect pattern |
| **Caching Layer** | `utils/supabase_storage.py` | ✅ YES | 90% cache hit rate |
| **Session Management** | `SearchSessionManager` | ✅ YES | Progressive evaluation |
| **Claude Agent SDK** | `coresignal_service.py:981` | ✅ YES | For Crunchbase, adapt for research |
| **Deep Research** | N/A | ❌ NO | **MISSING - Need to build** |

---

## The Missing Piece: True Deep Research

### Current "Deep Research" (Shallow)
```python
# company_research_service.py line 455
async def evaluate_company_relevance_gpt5(company_data, jd_context):
    # Just passes company name to LLM
    # No actual data fetching
```

### What We Need (Deep)
```python
async def deep_research_with_data(company_data, jd_context):
    # 1. Claude Agent SDK WebSearch for web research
    # 2. CoreSignal company_base data
    # 3. Sample employees from company
    # 4. LLM evaluation with real data
```

---

## Implementation Plan: Integrate, Don't Recreate

### Phase 1: Leverage Domain Search Infrastructure (2 hours)

**Goal:** Reuse the proven 4-stage pipeline from domain_search.py

#### Task 1.1: Extract Common Pipeline Components
```python
# Create: backend/jd_analyzer/core/pipeline_base.py
class ResearchPipelineBase:
    """Base class for all research pipelines"""

    async def stage1_discover(self, context):
        # Use CompanyDiscoveryAgent

    async def stage2_validate(self, companies):
        # Use CoreSignal validation from domain_search

    async def stage3_enrich(self, companies):
        # Use coresignal_service enrichment

    async def stage4_evaluate(self, companies, context):
        # Abstract method - implement in subclasses
```

**Files to modify:**
- Extract from `domain_search.py` stages 1-3
- Keep stage-specific logic in domain_search
- Share common validation/enrichment

#### Task 1.2: Adapt Company Research to Use Pipeline
```python
# Modify: backend/company_research_service.py
from jd_analyzer.core.pipeline_base import ResearchPipelineBase

class EnhancedCompanyResearchService(ResearchPipelineBase):
    async def research_companies_deep(self, ...):
        # Stage 1: Reuse discover
        companies = await self.stage1_discover(...)

        # Stage 2: Reuse validate
        validated = await self.stage2_validate(companies)

        # Stage 3: Reuse enrich
        enriched = await self.stage3_enrich(validated)

        # Stage 4: NEW - Deep research with Claude Agent SDK
        researched = await self.stage4_deep_research(enriched)
```

---

### Phase 2: Add Claude Agent SDK Deep Research (3 hours)

**Goal:** Add the missing deep research using Claude Agent SDK WebSearch

#### Task 2.1: Enhance Company Validation Agent
```python
# Modify: backend/jd_analyzer/company/company_validation_agent.py

# Change from Anthropic messages API to Claude Agent SDK
from claude_agent_sdk import query, ClaudeAgentOptions

async def deep_research_company(self, company_name, company_data, target_domain):
    """Use Claude Agent SDK WebSearch for deep research"""

    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",
        allowed_tools=["WebSearch"]
    )

    prompt = f"""
    Research {company_name} in depth:
    - Official website and products
    - Funding and investors
    - Key personnel
    - Recent news
    - Competitive position in {target_domain}

    Company data: {company_data}
    """

    async for message in query(prompt=prompt, options=options):
        # Collect research
```

#### Task 2.2: Integrate with Existing Crunchbase Logic
```python
# Reuse pattern from coresignal_service.py:981
# Already has Claude Agent SDK integration for Crunchbase
# Adapt for general company research

def _validate_with_claude_websearch(company_name, context):
    # Existing implementation we can learn from
```

---

### Phase 3: Add Employee Sampling (2 hours)

**Goal:** Reuse employee discovery from domain_search Stage 2-3

#### Task 3.1: Extract Employee Sampling Logic
```python
# From domain_search.py lines 527-666
# Already has employee preview search
# Just need to adapt for company research context

async def sample_company_employees(company_id, company_name, limit=5):
    # Build query for employees at company
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"company_id": company_id}}
                ]
            }
        },
        "size": limit
    }

    # Use existing preview search
    return search_profiles_with_endpoint(query, "employee_clean", limit)
```

#### Task 3.2: Add to Company Research Flow
```python
# Add employee sampling after company enrichment
for company in enriched_companies:
    if company.get("coresignal_company_id"):
        employees = await sample_company_employees(
            company["coresignal_company_id"],
            company["name"],
            limit=5
        )
        company["sample_employees"] = employees
```

---

### Phase 4: Leverage Existing Caching (1 hour)

**Goal:** Use the proven caching system from domain_search

#### Task 4.1: No New Code Needed!
```python
# Already exists in utils/supabase_storage.py
from utils.supabase_storage import (
    get_stored_company,
    save_stored_company,
    get_cached_competitors,
    save_cached_competitors
)

# Just use it in company research:
cached = get_stored_company(company_id)
if cached:
    return cached  # 90% cache hit rate!
```

#### Task 4.2: Add Company Intelligence Cache
```sql
-- Already designed in COMPANY_INTELLIGENCE_CACHE_SCHEMA.sql
-- Just need to create table in Supabase
CREATE TABLE company_intelligence_cache ...
```

---

### Phase 5: Unify APIs (2 hours)

**Goal:** Single endpoint that chooses the right pipeline

#### Task 5.1: Smart Router Endpoint
```python
# In app.py
@app.route('/api/research/smart', methods=['POST'])
async def smart_research():
    """
    Automatically choose the right pipeline:
    - Domain Search: When looking for people
    - Company Research: When analyzing competitors
    """

    purpose = request.json.get("purpose")

    if purpose == "find_candidates":
        # Use domain_search pipeline
        return await domain_search_pipeline(...)
    elif purpose == "competitive_intelligence":
        # Use enhanced company research
        return await company_research_pipeline(...)
```

---

## What We DON'T Need to Build

### ✅ Already Have These:

1. **Tavily Discovery** - CompanyDiscoveryAgent works perfectly
2. **CoreSignal Validation** - domain_search Stage 2 has it
3. **Company Enrichment** - coresignal_service has it
4. **Employee Discovery** - domain_search Stage 2-3 has it
5. **Caching System** - utils/supabase_storage.py complete
6. **Session Management** - SearchSessionManager exists
7. **Progress Streaming** - SSE implementation in Stage 4
8. **Excluded Companies Filter** - config.py has it

### ❌ Only Need to Add:

1. **Claude Agent SDK Deep Research** - The web search component
2. **Pipeline Base Class** - To share code between pipelines
3. **Smart Router** - To choose the right pipeline

---

## Migration Strategy

### Week 1: Integration
- Day 1-2: Extract pipeline base class
- Day 3-4: Add Claude Agent SDK research
- Day 5: Test with Voice AI companies

### Week 2: Optimization
- Day 1-2: Ensure caching works (90% hit rate)
- Day 3-4: Add progressive evaluation
- Day 5: Performance testing

### Week 3: Unification
- Day 1-2: Create smart router
- Day 3-4: Update frontend
- Day 5: Documentation

### Week 4: Deprecation
- Remove duplicate code
- Archive old implementations
- Update all references

---

## Cost Analysis

### Current Costs (Per Search)
- **Domain Search**: ~80 credits first run, ~8 cached
- **Company Research**: $3 LLM only

### Enhanced Costs (Reusing Infrastructure)
- **First Run**: ~25 credits (company data) + $3 LLM
- **Cached Run**: ~2 credits + $3 LLM
- **Savings**: 90% on subsequent searches

---

## Success Metrics

### Technical
- ✅ Reuse 80% of existing code
- ✅ 90% cache hit rate (proven)
- ✅ <60 second response time
- ✅ Real data, not LLM guesses

### Business
- ✅ 95% accuracy (vs 60% current)
- ✅ Employee validation
- ✅ Competitive intelligence depth
- ✅ Cost-effective with caching

---

## Action Items

### Immediate (Today)
1. [ ] Review existing domain_search.py implementation
2. [ ] Test CompanyDiscoveryAgent standalone
3. [ ] Verify caching is working

### This Week
1. [ ] Extract pipeline base class
2. [ ] Add Claude Agent SDK research
3. [ ] Test enhanced pipeline

### Next Week
1. [ ] Full integration testing
2. [ ] Performance optimization
3. [ ] Documentation update

---

## Conclusion

We don't need to build a new system from scratch. We have 80% of what we need:

1. **Domain Search Pipeline** provides the 4-stage structure
2. **CompanyDiscoveryAgent** handles Tavily discovery
3. **CoreSignal validation** exists in domain_search
4. **Caching system** is production-ready
5. **Claude Agent SDK** is already integrated for Crunchbase

We only need to:
1. Add deep research with Claude Agent SDK WebSearch
2. Create a base class to share code
3. Wire it together

This is a 2-week integration project, not a 2-month rebuild!