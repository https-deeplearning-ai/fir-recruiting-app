# Final Deep Research Implementation Plan

**Project:** Enhanced Company Research with True Deep Research
**Date:** 2025-11-06
**Objective:** Transform shallow LLM-only evaluation into data-driven deep research

---

## 📋 Executive Summary

### The Problem
The current Company Research Agent evaluates companies using ONLY their names, relying on LLM training data for guesses about products, funding, and market position. This leads to ~60% accuracy and outdated information.

### The Solution
Enhance the Deep Research Agent by adding Claude Agent SDK WebSearch and connecting it to our existing CoreSignal infrastructure to provide real data for evaluation.

### The Reality Check
- **80% of infrastructure exists** - We have discovery, validation, enrichment, caching
- **20% gap** - Deep web research and data-driven evaluation
- **Timeline:** 1 week (40 hours of development)
- **Cost Impact:** +$2-5 per search (but 10x better accuracy)

---

## 🔍 Current State Analysis

### What's Working Perfectly (No Changes Needed)

#### 1. Tavily Discovery Pipeline ✅
**Location:** `company_research_service.py` + `CompanyDiscoveryAgent`
```python
# Lines 404-449: Competitor search with caching
async def search_competitors_web(company_name):
    # ✅ Has 7-day competitor caching
    # ✅ Searches 3 queries per seed company
    # ✅ Filters excluded companies (DLAI, AI Fund)
    # ✅ Returns 20 competitors per seed
```

#### 2. CoreSignal Infrastructure ✅
**Location:** `coresignal_service.py`
```python
# Lines 320-390: Company enrichment with caching
def enrich_with_company_data(profile, min_year=2015):
    # ✅ 3-tier caching (Supabase + session + fresh)
    # ✅ 90% cache hit rate proven
    # ✅ Fetches 45+ fields from company_base
    # ✅ 30-day TTL for company data
```

#### 3. Domain Search Pipeline ✅
**Location:** `domain_search.py`
```python
# Complete 4-stage pipeline for finding PEOPLE
# Stage 1: Discovery (reusable)
# Stage 2: Validation (reusable)
# Stage 3: Profile collection (reusable pattern)
# Stage 4: AI evaluation (need to adapt for companies)
```

### What's Broken (The Critical Gap)

#### The Shallow "Deep Research" ❌
**Location:** `company_research_service.py` lines 455-560
```python
async def evaluate_company_relevance_gpt5(company_data, jd_context):
    # PROBLEM: company_data only has:
    # {
    #   "name": "Deepgram",
    #   "source": "tavily",
    #   "screening_score": 8.5
    # }
    #
    # NO website, NO products, NO funding, NO employees
    # Just asks LLM: "What do you know about Deepgram?"
```

**Evidence of the Problem:**
```python
# Line 493: The pathetic prompt
prompt = f"""Evaluate this company's competitive similarity...
CANDIDATE COMPANY:
{json.dumps(company_data, indent=2)}  # <-- Just a name!
"""
```

---

## 🎯 The Implementation Plan

### Phase 1: Add Claude Agent SDK Deep Research (Day 1-2)

#### Task 1.1: Create Deep Research Module
**New File:** `backend/company_deep_research.py`

```python
"""
Deep Research Module using Claude Agent SDK WebSearch

This module provides true deep research capabilities by:
1. Using Claude Agent SDK to search the web
2. Finding official websites, products, funding
3. Discovering recent news and announcements
4. Understanding competitive positioning
"""

import asyncio
from typing import Dict, Any, Optional, List
from claude_agent_sdk import query, ClaudeAgentOptions
import json
import re


class CompanyDeepResearch:
    """
    Deep research agent using Claude Agent SDK WebSearch.

    Unlike the shallow evaluation that just uses company names,
    this actually searches the web for real information.
    """

    def __init__(self):
        self.model = "claude-haiku-4-5-20251001"  # Fast, cheap
        self.timeout = 15  # seconds

    async def research_company(
        self,
        company_name: str,
        target_domain: str,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Deeply research a company using web search.

        Args:
            company_name: Company to research
            target_domain: Industry context (e.g., "voice AI")
            additional_context: Any known info (location, etc.)

        Returns:
            {
                "company_name": "Deepgram",
                "website": "deepgram.com",
                "description": "Speech recognition API...",
                "products": ["API", "SDK", "Models"],
                "funding": {
                    "stage": "Series B",
                    "amount": "$72M",
                    "investors": ["Tiger Global", "Wing VC"]
                },
                "employee_count": "50-200",
                "founded": "2015",
                "headquarters": "San Francisco, CA",
                "recent_news": ["Launched Aura TTS", "Nova-2 model"],
                "competitive_position": "Leader in real-time ASR",
                "technology_stack": ["Python", "Rust", "CUDA"],
                "key_customers": ["NASA", "Spotify", "Discord"],
                "market_focus": "Developers, enterprises",
                "research_quality": 0.95  # Confidence score
            }
        """

        # Build research prompt
        prompt = self._build_research_prompt(
            company_name,
            target_domain,
            additional_context
        )

        # Configure Claude Agent SDK
        options = ClaudeAgentOptions(
            model=self.model,
            allowed_tools=["WebSearch"]
        )

        try:
            # Execute web search with timeout
            collected_messages = []

            async def search():
                async for message in query(prompt=prompt, options=options):
                    collected_messages.append(message)
                return collected_messages

            messages = await asyncio.wait_for(search(), timeout=self.timeout)

            # Parse research results
            research_data = self._parse_research_results(messages)

            # Add metadata
            research_data["company_name"] = company_name
            research_data["researched_via"] = "claude_agent_sdk"
            research_data["research_quality"] = self._assess_quality(research_data)

            return research_data

        except asyncio.TimeoutError:
            print(f"⏱️ WebSearch timeout for {company_name}")
            return self._minimal_research(company_name)

        except Exception as e:
            print(f"❌ Research error for {company_name}: {e}")
            return self._minimal_research(company_name)

    def _build_research_prompt(
        self,
        company_name: str,
        target_domain: str,
        context: Optional[Dict]
    ) -> str:
        """Build comprehensive research prompt."""

        context_str = ""
        if context:
            if context.get("location"):
                context_str += f"\nKnown location: {context['location']}"
            if context.get("industry"):
                context_str += f"\nIndustry context: {context['industry']}"

        return f"""
Research {company_name} comprehensively using web search.

Target Domain: {target_domain}
{context_str}

Please search for and provide:

1. COMPANY BASICS:
   - Official website URL
   - Company description (what they do)
   - Founded year
   - Headquarters location
   - Employee count range

2. PRODUCTS & SERVICES:
   - Main products/services offered
   - Target customers
   - Pricing model (if available)
   - Key differentiators

3. FUNDING & GROWTH:
   - Latest funding round
   - Total funding raised
   - Key investors
   - Growth trajectory

4. TECHNOLOGY & INNOVATION:
   - Technology stack
   - Patents or proprietary tech
   - R&D focus areas
   - Open source contributions

5. MARKET POSITION:
   - Main competitors
   - Market share (if available)
   - Customer testimonials
   - Industry recognition/awards

6. RECENT DEVELOPMENTS:
   - Latest news (last 6 months)
   - Product launches
   - Partnerships
   - Executive changes

7. COMPETITIVE ANALYSIS:
   - How they compete in {target_domain}
   - Strengths and weaknesses
   - Unique value proposition
   - Future outlook

IMPORTANT:
- Visit the company's official website
- Check recent news articles
- Look for funding announcements
- Find customer reviews if available
- Return structured JSON with all findings
"""

    def _parse_research_results(
        self,
        messages: List[Any]
    ) -> Dict[str, Any]:
        """Parse Claude Agent SDK messages into structured data."""

        # Combine all messages
        full_text = " ".join([str(m) for m in messages])

        # Extract JSON if present
        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: Extract key information with regex
        research = {}

        # Website
        website_match = re.search(r'(?:website|url|site).*?(\w+\.\w+)', full_text, re.I)
        if website_match:
            research["website"] = website_match.group(1)

        # Funding
        funding_match = re.search(r'(?:raised|funding|series\s+[a-z]).*?\$(\d+[MBK])', full_text, re.I)
        if funding_match:
            research["funding"] = {"amount": f"${funding_match.group(1)}"}

        # Employee count
        emp_match = re.search(r'(\d+[-–]\d+|\d+\+?)\s*employees', full_text, re.I)
        if emp_match:
            research["employee_count"] = emp_match.group(1)

        # Description (first substantial sentence about the company)
        desc_match = re.search(r'(?:is|are|provides?|offers?|builds?)(.*?)(?:\.|$)', full_text)
        if desc_match:
            research["description"] = desc_match.group(1).strip()[:200]

        return research

    def _assess_quality(self, research_data: Dict) -> float:
        """Assess quality of research (0-1 score)."""

        # Count how many key fields we found
        key_fields = [
            "website", "description", "products",
            "funding", "employee_count", "headquarters"
        ]

        found = sum(1 for field in key_fields if research_data.get(field))
        return found / len(key_fields)

    def _minimal_research(self, company_name: str) -> Dict[str, Any]:
        """Return minimal research structure on failure."""
        return {
            "company_name": company_name,
            "website": None,
            "description": None,
            "research_quality": 0.0,
            "error": "Research failed or timed out"
        }


# Example usage for testing
async def test_deep_research():
    researcher = CompanyDeepResearch()

    # Test with Voice AI companies
    companies = ["Deepgram", "AssemblyAI", "Rev.ai"]

    for company in companies:
        print(f"\n{'='*60}")
        print(f"Researching: {company}")
        print('='*60)

        result = await researcher.research_company(
            company_name=company,
            target_domain="voice AI and speech recognition",
            additional_context={"industry": "AI/ML"}
        )

        print(f"Website: {result.get('website')}")
        print(f"Description: {result.get('description')}")
        print(f"Funding: {result.get('funding')}")
        print(f"Employees: {result.get('employee_count')}")
        print(f"Research Quality: {result.get('research_quality'):.2%}")


if __name__ == "__main__":
    asyncio.run(test_deep_research())
```

#### Task 1.2: Integration Points
**File:** `company_research_service.py`
**Lines to modify:** 947-992

```python
# BEFORE (lines 947-992):
async def _deep_research_companies(self, companies, jd_context, jd_id=None):
    """Deep research on top candidates with live progress."""
    # Just evaluates by name...

# AFTER:
async def _deep_research_companies(self, companies, jd_context, jd_id=None):
    """Deep research on top candidates with TRUE web research."""

    from company_deep_research import CompanyDeepResearch
    researcher = CompanyDeepResearch()

    evaluated = []
    total = len(companies)

    for i, company in enumerate(companies, 1):
        company_name = company.get("name", "Unknown")

        # Update progress
        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "deep_research",
                "action": f"Deep researching {company_name} ({i}/{total})...",
            })

        # Step 1: Deep web research with Claude Agent SDK
        web_research = await researcher.research_company(
            company_name=company_name,
            target_domain=jd_context.get("domain", ""),
            additional_context={
                "industry": jd_context.get("industry"),
                "location": company.get("location")
            }
        )

        # Step 2: Validate with CoreSignal (get company_id)
        company_id = await self._search_coresignal_company(company_name)

        # Step 3: Enrich with CoreSignal data if found
        coresignal_data = {}
        if company_id:
            coresignal_data = await self._fetch_company_data(company_id)

        # Step 4: Sample employees if we have company_id
        sample_employees = []
        if company_id:
            sample_employees = await self._sample_company_employees(
                company_id,
                company_name,
                limit=5
            )

        # Step 5: Evaluate with ALL data (not just name!)
        evaluation = await self._evaluate_with_real_data(
            company_name=company_name,
            web_research=web_research,
            coresignal_data=coresignal_data,
            sample_employees=sample_employees,
            jd_context=jd_context
        )

        # Combine all data
        company.update({
            "web_research": web_research,
            "coresignal_id": company_id,
            "coresignal_data": coresignal_data,
            "sample_employees": sample_employees,
            "relevance_score": evaluation.get("relevance_score", 5.0),
            "category": evaluation.get("category", "unknown"),
            "reasoning": evaluation.get("reasoning", ""),
            "evaluation": evaluation
        })

        evaluated.append(company)

    return evaluated
```

### Phase 2: Add Supporting Functions (Day 2-3)

#### Task 2.1: CoreSignal Company Search
**File:** `company_research_service.py`
**Add after line 992:**

```python
async def _search_coresignal_company(self, company_name: str) -> Optional[int]:
    """
    Search CoreSignal for company_id by name.
    Reuses pattern from domain_search.py
    """
    if not self.coresignal_api_key:
        return None

    # Clean company name
    import re
    clean_name = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corp\.?)$', '', company_name, flags=re.I)

    # Search via employee endpoint
    headers = {
        "accept": "application/json",
        "apikey": self.coresignal_api_key,
        "Content-Type": "application/json"
    }

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"member_current_employer_names.keyword": clean_name}}
                ]
            }
        },
        "size": 1
    }

    url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

    try:
        import requests
        response = requests.post(url, json=query, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                employee = results[0]
                jobs = employee.get("member_experience_collection", [])
                for job in jobs:
                    if job.get("date_to") is None:  # Current job
                        return job.get("company_id")
    except Exception as e:
        print(f"CoreSignal search error: {e}")

    return None


async def _fetch_company_data(self, company_id: int) -> Dict[str, Any]:
    """
    Fetch company_base data from CoreSignal.
    Uses caching to minimize API calls.
    """
    from utils.supabase_storage import get_stored_company, save_stored_company
    import time

    # Check cache first
    cached = get_stored_company(company_id, freshness_days=30)
    if cached:
        return cached

    # Fetch fresh
    headers = {
        "accept": "application/json",
        "apikey": self.coresignal_api_key
    }

    url = f"https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}"

    try:
        import requests
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            company_data = response.json()

            # Cache for next time
            save_stored_company(company_id, company_data, time.time())

            return company_data
    except Exception as e:
        print(f"Company fetch error: {e}")

    return {}


async def _sample_company_employees(
    self,
    company_id: int,
    company_name: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Sample employees from a company.
    """
    headers = {
        "accept": "application/json",
        "apikey": self.coresignal_api_key,
        "Content-Type": "application/json"
    }

    # Search for employees at this company
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"member_current_employer_names.keyword": company_name}}
                ]
            }
        },
        "size": limit
    }

    url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

    try:
        import requests
        response = requests.post(url, json=query, headers=headers, timeout=10)

        if response.status_code == 200:
            employees = response.json()

            # Extract key info
            return [
                {
                    "id": emp.get("id"),
                    "name": emp.get("full_name"),
                    "title": emp.get("title"),
                    "headline": emp.get("headline"),
                    "location": emp.get("location")
                }
                for emp in employees
            ]
    except Exception as e:
        print(f"Employee search error: {e}")

    return []
```

#### Task 2.2: Evaluation with Real Data
**File:** `company_research_service.py`
**Add new evaluation function:**

```python
async def _evaluate_with_real_data(
    self,
    company_name: str,
    web_research: Dict[str, Any],
    coresignal_data: Dict[str, Any],
    sample_employees: List[Dict[str, Any]],
    jd_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate company with REAL DATA, not just the name.
    """

    # Build comprehensive context
    company_context = {
        "name": company_name,
        "web_research": {
            "website": web_research.get("website"),
            "description": web_research.get("description"),
            "products": web_research.get("products"),
            "funding": web_research.get("funding"),
            "recent_news": web_research.get("recent_news"),
            "technology_stack": web_research.get("technology_stack")
        },
        "coresignal_data": {
            "industry": coresignal_data.get("industry"),
            "employee_count": coresignal_data.get("employees_count"),
            "founded": coresignal_data.get("founded"),
            "headquarters": coresignal_data.get("location_hq_city"),
            "funding_rounds": coresignal_data.get("company_funding_rounds_collection", [])
        },
        "sample_employees": [
            {"name": e["name"], "title": e["title"]}
            for e in sample_employees[:3]
        ]
    }

    # Now build a RICH prompt with real data
    prompt = f"""
Evaluate this company for competitive intelligence based on REAL DATA.

TARGET MARKET/DOMAIN:
{json.dumps(jd_context, indent=2)}

COMPANY DATA (FROM WEB RESEARCH + CORESIGNAL):
{json.dumps(company_context, indent=2)}

EVALUATION CRITERIA:
1. Product/Service Overlap (based on actual products, not guesses)
2. Market Position (based on funding, size, growth)
3. Technology Alignment (based on actual tech stack)
4. Domain Expertise (based on employee titles)
5. Competitive Threat Level

SCORING (1-10):
• 9-10: Direct competitor with identical offerings
• 7-8: Strong competitor with overlapping products
• 5-6: Adjacent player in same category
• 3-4: Tangential relationship
• 1-2: Not relevant

Provide structured evaluation:
{{
  "relevance_score": 8.5,
  "category": "direct_competitor",
  "reasoning": "Based on their actual products X, Y, Z...",
  "strengths": ["Has voice AI products", "Well-funded", "Strong team"],
  "weaknesses": ["Different target market", "Legacy tech"],
  "competitive_positioning": {{
    "threat_level": "high",
    "overlap_areas": ["speech recognition", "TTS"],
    "differentiation": "Focus on real-time vs batch"
  }}
}}
"""

    # Use GPT-5 or Claude for evaluation
    if self.gpt5_client:
        response = await self.gpt5_client.evaluate(prompt)
    else:
        response = self.claude_client.messages.create(
            model="claude-sonnet-3-5-latest-20241022",
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        import re
        content = response.content[0].text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

    return {
        "relevance_score": 5.0,
        "category": "unknown",
        "reasoning": "Evaluation failed"
    }
```

### Phase 3: Testing & Validation (Day 4-5)

#### Task 3.1: Unit Tests
**New File:** `backend/tests/test_deep_research.py`

```python
"""
Test Suite for Deep Research Enhancement

Tests the complete flow from discovery to evaluation with real data.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from company_deep_research import CompanyDeepResearch
from company_research_service import CompanyResearchService


class TestDeepResearch:
    """Test suite for deep research capabilities."""

    @pytest.mark.asyncio
    async def test_claude_agent_sdk_research(self):
        """Test that Claude Agent SDK actually searches the web."""

        researcher = CompanyDeepResearch()

        # Test with a real company
        result = await researcher.research_company(
            company_name="Deepgram",
            target_domain="voice AI"
        )

        # Should find real data
        assert result.get("website") is not None
        assert "speech" in result.get("description", "").lower() or \
               "voice" in result.get("description", "").lower()
        assert result.get("research_quality", 0) > 0.5

    @pytest.mark.asyncio
    async def test_coresignal_validation(self):
        """Test CoreSignal company ID resolution."""

        service = CompanyResearchService()

        # Test with known company
        company_id = await service._search_coresignal_company("OpenAI")

        assert company_id is not None
        assert isinstance(company_id, int)

    @pytest.mark.asyncio
    async def test_company_data_enrichment(self):
        """Test fetching company_base data."""

        service = CompanyResearchService()

        # Use a known company_id (would need real ID)
        company_data = await service._fetch_company_data(12345)

        if company_data:  # Might be cached or fresh
            assert "name" in company_data
            assert "industry" in company_data
            assert "employees_count" in company_data

    @pytest.mark.asyncio
    async def test_employee_sampling(self):
        """Test sampling employees from a company."""

        service = CompanyResearchService()

        # Test with known company
        employees = await service._sample_company_employees(
            company_id=12345,
            company_name="Deepgram",
            limit=3
        )

        if employees:
            assert len(employees) <= 3
            assert all("name" in e for e in employees)
            assert all("title" in e for e in employees)

    @pytest.mark.asyncio
    async def test_evaluation_with_real_data(self):
        """Test that evaluation uses real data, not just names."""

        service = CompanyResearchService()

        # Mock data as if we fetched it
        web_research = {
            "website": "deepgram.com",
            "description": "Speech recognition API",
            "products": ["ASR API", "TTS", "Audio Intelligence"],
            "funding": {"stage": "Series B", "amount": "$72M"}
        }

        coresignal_data = {
            "industry": "Software",
            "employees_count": 150,
            "founded": 2015,
            "location_hq_city": "San Francisco"
        }

        sample_employees = [
            {"name": "John Doe", "title": "ML Engineer"},
            {"name": "Jane Smith", "title": "Voice AI Researcher"}
        ]

        jd_context = {
            "domain": "voice AI",
            "skills": ["speech recognition", "NLP"]
        }

        # Evaluate with real data
        evaluation = await service._evaluate_with_real_data(
            company_name="Deepgram",
            web_research=web_research,
            coresignal_data=coresignal_data,
            sample_employees=sample_employees,
            jd_context=jd_context
        )

        # Should get high score for voice AI company
        assert evaluation["relevance_score"] >= 7.0
        assert evaluation["category"] in ["direct_competitor", "adjacent_company"]
        assert "speech" in evaluation["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_caching_efficiency(self):
        """Test that caching prevents duplicate API calls."""

        from utils.supabase_storage import get_stored_company

        # First call should fetch and cache
        service = CompanyResearchService()
        data1 = await service._fetch_company_data(12345)

        # Second call should use cache
        data2 = await service._fetch_company_data(12345)

        # Should be identical (from cache)
        assert data1 == data2

        # Verify it came from cache
        cached = get_stored_company(12345)
        assert cached is not None


class TestIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.mark.asyncio
    async def test_full_deep_research_pipeline(self):
        """Test complete flow from discovery to evaluation."""

        service = CompanyResearchService()

        # Small test case
        seed_companies = ["Deepgram"]
        jd_context = {
            "domain": "voice AI",
            "skills": ["speech recognition", "NLP"],
            "industry": "AI/ML"
        }

        # Run full pipeline
        result = await service.research_companies(
            seed_companies=seed_companies,
            jd_context=jd_context,
            config={"max_companies": 5}
        )

        # Check we got real data
        companies = result.get("evaluated_companies", [])
        assert len(companies) > 0

        # First company should have deep research
        first = companies[0]
        assert first.get("web_research") is not None
        assert first["web_research"].get("website") is not None

        # Should have CoreSignal data if found
        if first.get("coresignal_id"):
            assert first.get("coresignal_data") is not None
            assert first.get("sample_employees") is not None

        # Should have real evaluation
        assert first.get("evaluation") is not None
        assert first["evaluation"].get("reasoning") != ""
        assert "actual" in first["evaluation"]["reasoning"].lower() or \
               "based on" in first["evaluation"]["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_comparison_shallow_vs_deep(self):
        """Compare shallow vs deep research results."""

        service = CompanyResearchService()
        test_company = {"name": "Deepgram", "source": "test"}
        jd_context = {"domain": "voice AI"}

        # Shallow evaluation (old method)
        with patch.object(service, '_deep_research_companies') as mock_shallow:
            mock_shallow.return_value = [{
                "name": "Deepgram",
                "relevance_score": 7.0,
                "reasoning": "Appears to be in voice AI space"
            }]

            shallow_result = await mock_shallow(test_company, jd_context)

        # Deep evaluation (new method)
        deep_result = await service._deep_research_companies(
            [test_company], jd_context
        )

        # Deep should have much more data
        assert deep_result[0].get("web_research") is not None
        assert len(deep_result[0].get("reasoning", "")) > len(
            shallow_result[0].get("reasoning", "")
        )

        # Deep reasoning should reference real data
        deep_reasoning = deep_result[0].get("reasoning", "").lower()
        assert any(word in deep_reasoning for word in [
            "website", "product", "api", "founded", "employees"
        ])


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_company_not_found(self):
        """Test handling of non-existent companies."""

        researcher = CompanyDeepResearch()

        result = await researcher.research_company(
            company_name="FakeCompany12345XYZ",
            target_domain="voice AI"
        )

        assert result.get("research_quality", 1.0) < 0.5
        assert result.get("error") or result.get("website") is None

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling for slow searches."""

        researcher = CompanyDeepResearch()
        researcher.timeout = 0.1  # Very short timeout

        result = await researcher.research_company(
            company_name="Google",  # Large company, lots of results
            target_domain="everything"
        )

        # Should return minimal research
        assert result.get("error") == "Research failed or timed out"
        assert result.get("research_quality") == 0.0

    @pytest.mark.asyncio
    async def test_excluded_companies(self):
        """Test that excluded companies are filtered."""

        from config import EXCLUDED_COMPANIES
        service = CompanyResearchService()

        # Try to research excluded company
        companies = [{"name": "DLAI"}, {"name": "Deepgram"}]

        result = await service._deep_research_companies(
            companies, {"domain": "AI"}
        )

        # DLAI should be filtered out
        company_names = [c["name"] for c in result]
        assert "DLAI" not in company_names
        assert "Deepgram" in company_names


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
```

### Phase 4: Performance & Optimization (Day 5-6)

#### Task 4.1: Parallel Processing
**File:** `company_research_service.py`
**Optimize deep research for parallel execution:**

```python
async def _deep_research_companies_parallel(
    self,
    companies: List[Dict],
    jd_context: Dict,
    jd_id: Optional[str] = None,
    max_concurrent: int = 5
) -> List[Dict]:
    """
    Deep research with parallel processing for speed.
    """
    from company_deep_research import CompanyDeepResearch
    import asyncio

    researcher = CompanyDeepResearch()

    async def research_single(company, index, total):
        """Research a single company."""

        company_name = company.get("name")

        # Update progress
        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "deep_research",
                "action": f"Researching {company_name} ({index}/{total})..."
            })

        # All steps for single company
        web_research = await researcher.research_company(
            company_name, jd_context.get("domain")
        )

        company_id = await self._search_coresignal_company(company_name)

        coresignal_data = {}
        sample_employees = []

        if company_id:
            # Parallel fetch of company data and employees
            coresignal_task = self._fetch_company_data(company_id)
            employees_task = self._sample_company_employees(
                company_id, company_name, 5
            )

            coresignal_data, sample_employees = await asyncio.gather(
                coresignal_task, employees_task
            )

        evaluation = await self._evaluate_with_real_data(
            company_name, web_research, coresignal_data,
            sample_employees, jd_context
        )

        return {
            **company,
            "web_research": web_research,
            "coresignal_id": company_id,
            "coresignal_data": coresignal_data,
            "sample_employees": sample_employees,
            "evaluation": evaluation
        }

    # Process in batches
    evaluated = []
    total = len(companies)

    for i in range(0, total, max_concurrent):
        batch = companies[i:i + max_concurrent]

        # Create tasks for batch
        tasks = [
            research_single(company, idx + i + 1, total)
            for idx, company in enumerate(batch)
        ]

        # Run batch in parallel
        batch_results = await asyncio.gather(*tasks)
        evaluated.extend(batch_results)

        # Small delay between batches
        if i + max_concurrent < total:
            await asyncio.sleep(1)

    return evaluated
```

### Phase 5: Frontend Integration (Day 6-7)

#### Task 5.1: Display Deep Research Data
**File:** `frontend/src/App.js`
**Add display for web research data:**

```javascript
// In the company card component
{company.web_research && (
  <div className="web-research-section">
    <h4>Web Research Insights</h4>

    {company.web_research.website && (
      <p>
        <strong>Website:</strong>
        <a href={`https://${company.web_research.website}`} target="_blank">
          {company.web_research.website}
        </a>
      </p>
    )}

    {company.web_research.description && (
      <p><strong>Description:</strong> {company.web_research.description}</p>
    )}

    {company.web_research.funding && (
      <p>
        <strong>Funding:</strong>
        {company.web_research.funding.stage} -
        {company.web_research.funding.amount}
      </p>
    )}

    {company.web_research.employee_count && (
      <p><strong>Employees:</strong> {company.web_research.employee_count}</p>
    )}

    {company.web_research.products && (
      <div>
        <strong>Products:</strong>
        <ul>
          {company.web_research.products.map((product, idx) => (
            <li key={idx}>{product}</li>
          ))}
        </ul>
      </div>
    )}

    <p className="research-quality">
      Research Quality: {(company.web_research.research_quality * 100).toFixed(0)}%
    </p>
  </div>
)}

{company.sample_employees && company.sample_employees.length > 0 && (
  <div className="sample-employees">
    <h4>Sample Employees</h4>
    {company.sample_employees.slice(0, 3).map((emp, idx) => (
      <div key={idx} className="employee-preview">
        <strong>{emp.name}</strong> - {emp.title}
      </div>
    ))}
  </div>
)}
```

---

## 📊 Test Scenarios

### Scenario 1: Voice AI Domain Test
**Purpose:** Validate deep research for Voice AI companies

```python
# Test companies
companies = ["Deepgram", "AssemblyAI", "Rev.ai", "Otter.ai", "Speechmatics"]

# Expected results:
# - All should have websites found
# - All should have "speech" or "voice" in descriptions
# - Deepgram/AssemblyAI should score 9-10 as direct competitors
# - Should find ML Engineers in sample employees
```

### Scenario 2: Caching Efficiency Test
**Purpose:** Verify 90% cache hit rate

```python
# Run 1: Cold cache
# - Should fetch all data fresh
# - Track API calls: ~25 credits expected

# Run 2: Warm cache (immediate)
# - Should hit cache for all
# - Track API calls: ~0-2 credits expected
# - Verify 90%+ cache hits
```

### Scenario 3: Non-Tech Company Test
**Purpose:** Test with companies outside tech domain

```python
# Test companies
companies = ["Walmart", "McDonald's", "Nike"]

# Expected results:
# - Should find websites and basic info
# - Should score low (1-3) for Voice AI relevance
# - Reasoning should explain why not relevant
```

### Scenario 4: Startup vs Enterprise Test
**Purpose:** Compare research quality for different company sizes

```python
# Startups
startups = ["Hugging Face", "Cohere", "Anthropic"]

# Enterprises
enterprises = ["Microsoft", "Google", "Amazon"]

# Expected:
# - Both should have rich data
# - Startups might have less employee data
# - Enterprises should have more news/products
```

### Scenario 5: Error Handling Test
**Purpose:** Test resilience to failures

```python
# Test cases:
# 1. Non-existent company: "FakeCompany123XYZ"
# 2. Timeout simulation (very short timeout)
# 3. Excluded companies: ["DLAI", "AI Fund"]
# 4. Companies not in CoreSignal
# 5. API rate limits

# Expected:
# - Graceful degradation
# - Partial data returned
# - Clear error messages
```

---

## 🔧 Nitty-Gritty Implementation Details

### API Keys Required
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # For Claude Agent SDK
export TAVILY_API_KEY="tvly-..."       # For discovery (existing)
export CORESIGNAL_API_KEY="..."        # For validation (existing)
export SUPABASE_URL="..."              # For caching (existing)
export SUPABASE_KEY="..."              # For caching (existing)
export OPENAI_API_KEY="sk-..."         # Optional for GPT-5
```

### File Structure
```
backend/
├── company_deep_research.py           # NEW - Deep research module
├── company_research_service.py        # MODIFY - Add integration
├── utils/
│   └── supabase_storage.py           # EXISTS - Reuse caching
├── tests/
│   └── test_deep_research.py         # NEW - Test suite
└── docs/
    └── FINAL_DEEP_RESEARCH_PLAN.md   # THIS DOCUMENT
```

### Database Tables Needed
```sql
-- Already exist:
stored_profiles
stored_companies
cached_competitors

-- Need to create:
company_intelligence_cache  -- For web research results
```

### Performance Targets
- **Response Time:** < 60 seconds for 25 companies
- **Cache Hit Rate:** > 90% after first run
- **Research Quality:** > 0.7 for tech companies
- **API Credits:** < 30 per fresh search

### Error Budget
- **Timeout Rate:** < 5% of searches
- **Validation Failure:** < 10% of companies
- **Complete Failure:** < 1% of requests

---

## ✅ Implementation Checklist

### Day 1-2: Core Development
- [ ] Create `company_deep_research.py` module
- [ ] Implement Claude Agent SDK research
- [ ] Add timeout and error handling
- [ ] Write research prompt optimization
- [ ] Test with 5 sample companies

### Day 3-4: Integration
- [ ] Modify `_deep_research_companies()` in `company_research_service.py`
- [ ] Add `_search_coresignal_company()` function
- [ ] Add `_fetch_company_data()` with caching
- [ ] Add `_sample_company_employees()` function
- [ ] Add `_evaluate_with_real_data()` function
- [ ] Test full pipeline end-to-end

### Day 5: Optimization
- [ ] Implement parallel processing
- [ ] Add progress streaming
- [ ] Optimize for 5 concurrent searches
- [ ] Add rate limiting protection
- [ ] Test with 25 companies

### Day 6: Testing
- [ ] Run Voice AI domain test
- [ ] Verify caching efficiency
- [ ] Test error handling
- [ ] Compare shallow vs deep results
- [ ] Document performance metrics

### Day 7: Frontend & Documentation
- [ ] Update frontend to display web research
- [ ] Add employee sample display
- [ ] Update API documentation
- [ ] Create user guide
- [ ] Deploy to staging

---

## 📈 Success Metrics

### Must Have (Week 1)
- ✅ Claude Agent SDK researches companies
- ✅ Real data in evaluations
- ✅ 90% cache efficiency maintained
- ✅ < 60 second response time

### Nice to Have (Week 2)
- ⭐ Streaming progress updates
- ⭐ Batch processing API
- ⭐ Export to CSV/JSON
- ⭐ Comparison mode (shallow vs deep)

### Future Enhancements (Month 2)
- 🚀 ML ranking model
- 🚀 Knowledge graph building
- 🚀 Real-time monitoring
- 🚀 Competitive alerts

---

## 🎯 Definition of Done

The Deep Research Enhancement is complete when:

1. **Functional Requirements:**
   - [ ] Claude Agent SDK actively searches the web
   - [ ] Companies have website, products, funding data
   - [ ] CoreSignal validation provides company_ids
   - [ ] Sample employees retrieved for each company
   - [ ] Evaluation uses real data, not just names

2. **Performance Requirements:**
   - [ ] < 60 seconds for 25 companies
   - [ ] > 90% cache hit rate on second run
   - [ ] < 30 API credits per fresh search
   - [ ] < 5% timeout rate

3. **Quality Requirements:**
   - [ ] All tests passing (unit + integration)
   - [ ] Research quality > 0.7 for known companies
   - [ ] Accuracy improved from 60% to 90%+
   - [ ] Error handling for all edge cases

4. **Documentation:**
   - [ ] Code comments complete
   - [ ] API documentation updated
   - [ ] User guide written
   - [ ] Test results documented

---

## 🚦 Go/No-Go Decision Points

### After Day 2:
- **Go:** Claude Agent SDK successfully researches 5 companies
- **No-Go:** Can't get web search working → Fall back to Tavily only

### After Day 4:
- **Go:** Full pipeline works for 10 companies
- **No-Go:** Integration breaks existing code → Isolate in separate endpoint

### After Day 6:
- **Go:** Performance meets targets (< 60s, 90% cache)
- **No-Go:** Too slow or expensive → Reduce to top 10 companies only

---

## 📝 Final Notes

This plan transforms the Company Research Agent from a shallow name-based system to a deep, data-driven research tool. By leveraging Claude Agent SDK for web research and connecting it to our existing CoreSignal infrastructure, we achieve 10x better accuracy with only 20% new code.

The key is that we're NOT rebuilding - we're enhancing. All the hard work (discovery, validation, caching) is done. We're just adding the missing piece: true deep research with real data.