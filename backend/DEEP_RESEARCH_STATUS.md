# Deep Research Pipeline - Current Status & Improvement Focus

**Date:** 2025-11-06
**Status:** 80% Complete Infrastructure, 20% Missing Deep Research

---

## 🟢 What We Already Have (COMPLETE & WORKING)

### ✅ Phase 1: Discovery (100% Complete)

**Implementation:** `CompanyDiscoveryAgent` + `company_research_service.py`
```python
# Already Working:
- Tavily web search for company discovery ✅
- Competitor expansion from seed companies ✅
- Domain-based discovery (G2, Capterra, etc.) ✅
- Deduplication & filtering ✅
- Excluded companies filter (DLAI, AI Fund) ✅
- Competitor caching (7-day freshness) ✅
```

**Status:** This phase is PERFECT. No changes needed.

### ✅ Phase 2: CoreSignal Validation (100% Complete)

**Implementation:** `domain_search.py` Stage 2
```python
# Already Working:
- Company name → CoreSignal company_id resolution ✅
- Fuzzy name matching ✅
- Employee preview search ✅
- Query building for specific domains ✅
```

**Status:** Fully functional for finding people at companies.

### ✅ Phase 3: Data Enrichment (100% Complete)

**Implementation:** `coresignal_service.py` + caching system
```python
# Already Working:
- Company_base data fetching (45+ fields) ✅
- 3-tier caching system ✅
  - Supabase persistent storage (30-day TTL)
  - Session memory cache
  - Fresh API calls when needed
- Profile enrichment with company data ✅
- 90% cache hit rate on repeat searches ✅
- Credit optimization (2015+ filter) ✅
```

**Status:** Production-ready with proven 90% cache efficiency.

### ✅ Phase 4: Employee Discovery (100% Complete)

**Implementation:** `domain_search.py` Stages 2-3
```python
# Already Working:
- Find employees at discovered companies ✅
- Full profile collection ✅
- Company enrichment for each employee ✅
- Streaming progress updates ✅
- Session-based storage ✅
```

**Status:** Works perfectly for the Domain Search use case.

### ✅ Phase 5: AI Evaluation (100% Complete for Domain Search)

**Implementation:** `domain_search.py` Stage 4
```python
# Already Working:
- Claude Sonnet 4.5 evaluation ✅
- Streaming SSE for real-time updates ✅
- Scoring rubrics (Domain Fit, Experience Match) ✅
- Recommendations (STRONG_FIT, GOOD_FIT, etc.) ✅
```

**Status:** Complete for evaluating PEOPLE, not for evaluating COMPANIES.

---

## 🔴 What's Missing (The 20% Gap)

### ❌ Deep Company Research (0% Complete)

**Current Problem:** `company_research_service.py` line 455-560
```python
async def evaluate_company_relevance_gpt5():
    # Just passes company NAME to LLM
    # No web research
    # No actual data fetching
    # LLM guesses based on training data
```

**What We Need:**
```python
async def deep_research_company_with_real_data():
    # 1. Claude Agent SDK WebSearch for deep web research ❌
    # 2. Fetch actual company data from CoreSignal ❌
    # 3. Sample employees to validate domain expertise ❌
    # 4. Evaluate with REAL DATA not guesses ❌
```

### ❌ Claude Agent SDK Integration (Partial - 10% Complete)

**Current State:**
- ✅ Installed: `claude-agent-sdk==0.1.5`
- ✅ Used for: Crunchbase URL validation ONLY (`coresignal_service.py:981`)
- ❌ NOT used for: General company research
- ❌ NOT used for: Competitive analysis
- ❌ NOT used for: Product/service discovery

**What We Need:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def deep_research_with_websearch(company_name):
    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",
        allowed_tools=["WebSearch"]
    )

    # Research products, funding, news, competition
    # Not just Crunchbase URLs!
```

---

## 🎯 The Focus: Enhancing Deep Research Agent

**YES, we are 100% aligned!** The improvements are focused on fixing the Deep Research Agent.

### Current "Deep Research" Flow (Shallow)
```
1. Tavily discovers company names ✅
2. GPT-5-mini screens by name ✅
3. GPT-5/Claude evaluates by NAME ONLY ❌ (This is the problem!)
```

### Enhanced Deep Research Flow (What We're Building)
```
1. Tavily discovers company names ✅ (Keep as-is)
2. Claude Agent SDK researches each company ❌ (ADD THIS)
3. CoreSignal validates & enriches ✅ (Reuse existing)
4. Sample employees from companies ✅ (Reuse existing)
5. Evaluate with REAL DATA ❌ (ENHANCE THIS)
```

---

## 📊 Implementation Progress

| Component | Status | Notes |
|-----------|--------|-------|
| **Tavily Discovery** | ✅ 100% | No changes needed |
| **CoreSignal Validation** | ✅ 100% | Reuse from domain_search |
| **Company Enrichment** | ✅ 100% | Reuse caching system |
| **Employee Sampling** | ✅ 100% | Reuse from domain_search |
| **Caching System** | ✅ 100% | 90% hit rate proven |
| **Claude Agent SDK Setup** | ✅ 100% | Already installed |
| **Claude Agent SDK for Crunchbase** | ✅ 100% | Working example exists |
| **Claude Agent SDK for Deep Research** | ❌ 0% | **NEED TO BUILD** |
| **Evaluation with Real Data** | ❌ 0% | **NEED TO BUILD** |

---

## 📝 Plan Updates Needed?

### The Plan is Still Valid But Needs Minor Updates:

1. **DEEP_RESEARCH_PLAN.md** - Current and accurate
   - ✅ Correctly identifies reusable components
   - ✅ Correctly identifies the gap (deep research)
   - ⚠️ Could emphasize that 80% is ALREADY DONE

2. **backend/PLAN.md** - Outdated, focuses on caching
   - ✅ Caching is COMPLETE
   - ❌ Doesn't mention deep research improvements
   - Should be archived or updated

3. **IMPLEMENTATION_COMPLETE.md** - Accurate for Domain Search
   - ✅ Domain Search pipeline is complete
   - ❌ Doesn't cover Company Research enhancements
   - Should note that it's complete for PEOPLE not COMPANIES

---

## 🚀 Next Steps (The 20% We Need to Build)

### Priority 1: Add Claude Agent SDK Deep Research (3-4 hours)
```python
# Create: enhanced_company_research.py
async def deep_research_with_websearch(company_name, domain):
    """
    Use Claude Agent SDK to deeply research a company
    - Find official website
    - Discover products/services
    - Get recent news
    - Understand market position
    """
```

### Priority 2: Connect to Existing Infrastructure (2 hours)
```python
# Modify: company_research_service.py
async def _deep_research_companies():
    # OLD: Just LLM evaluation

    # NEW:
    for company in companies:
        # 1. Deep research with Claude Agent SDK
        web_research = await deep_research_with_websearch(company)

        # 2. Validate with CoreSignal (reuse existing)
        company_id = await validate_company(company)

        # 3. Enrich with data (reuse existing)
        company_data = await enrich_company(company_id)

        # 4. Sample employees (reuse existing)
        employees = await sample_employees(company_id)

        # 5. Evaluate with REAL DATA
        evaluation = await evaluate_with_data(
            web_research + company_data + employees
        )
```

### Priority 3: Test & Optimize (2 hours)
- Test with Voice AI companies
- Verify caching works (should be 90% hits)
- Ensure < 60 second response time

---

## 💡 Key Insight

**We don't need to rebuild everything!** We have:
- ✅ 80% of infrastructure complete and tested
- ✅ Proven patterns from Domain Search
- ✅ Working caching with 90% efficiency
- ✅ All the plumbing ready

**We only need to:**
- ❌ Add Claude Agent SDK for deep web research (not just Crunchbase)
- ❌ Connect it to the existing pipeline
- ❌ Evaluate companies with real data instead of LLM guesses

This is a **1-week enhancement**, not a rebuild!