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
import json
import re
import os
from datetime import datetime

# Import Claude Agent SDK
try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("Warning: claude-agent-sdk not found. Using mock for development.")
    # Mock for development if SDK not available
    class ClaudeAgentOptions:
        def __init__(self, **kwargs):
            pass

    async def query(prompt, options):
        yield {"content": "Mock research data"}


class CompanyDeepResearch:
    """
    Deep research agent using Claude Agent SDK WebSearch.

    Unlike the shallow evaluation that just uses company names,
    this actually searches the web for real information.
    """

    def __init__(self):
        self.model = "claude-haiku-4-5-20251015"  # Fast, cheap, good quality
        self.timeout = 15  # seconds
        # API key is read from ANTHROPIC_API_KEY environment variable by Claude SDK

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

        print(f"🔍 Deep researching {company_name} for {target_domain}...")

        # Build research prompt
        prompt = self._build_research_prompt(
            company_name,
            target_domain,
            additional_context
        )

        # Configure Claude Agent SDK
        # NOTE: API key is read from ANTHROPIC_API_KEY environment variable automatically
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
            research_data["research_timestamp"] = datetime.now().isoformat()
            research_data["research_quality"] = self._assess_quality(research_data)

            print(f"✅ Research complete for {company_name} (quality: {research_data['research_quality']:.0%})")
            return research_data

        except asyncio.TimeoutError:
            print(f"⏱️ WebSearch timeout for {company_name}")
            return self._minimal_research(company_name, "Research timed out")

        except Exception as e:
            print(f"❌ Research error for {company_name}: {e}")
            return self._minimal_research(company_name, str(e))

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
            if context.get("seed_companies"):
                context_str += f"\nComparing to: {', '.join(context['seed_companies'][:3])}"

        return f"""
Research {company_name} comprehensively using web search.

Target Domain: {target_domain}
{context_str}

IMPORTANT: Use WebSearch to find current, accurate information about this company.

Please search for and provide structured information:

1. COMPANY BASICS:
   - Official website URL (search for "{company_name} official website")
   - Company description (what they actually do)
   - Founded year
   - Headquarters location
   - Employee count range

2. PRODUCTS & SERVICES:
   - Main products/services offered
   - Target customers
   - Pricing model (if available)
   - Key differentiators

3. FUNDING & GROWTH:
   - Latest funding round (search for "{company_name} funding raised")
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

6. RECENT DEVELOPMENTS (last 6 months):
   - Latest news (search for "{company_name} news 2025")
   - Product launches
   - Partnerships
   - Executive changes

7. COMPETITIVE ANALYSIS for {target_domain}:
   - How they compete in this domain
   - Strengths and weaknesses
   - Unique value proposition
   - Future outlook

Return the findings in this JSON structure:
{{
  "website": "example.com",
  "description": "What the company does",
  "products": ["Product 1", "Product 2"],
  "funding": {{
    "stage": "Series B",
    "amount": "$50M",
    "date": "2024",
    "investors": ["Investor 1", "Investor 2"]
  }},
  "employee_count": "50-200",
  "founded": "2020",
  "headquarters": "San Francisco, CA",
  "recent_news": ["News item 1", "News item 2"],
  "competitive_position": "Market leader in X",
  "technology_stack": ["Tech 1", "Tech 2"],
  "key_customers": ["Customer 1", "Customer 2"],
  "market_focus": "Target market description"
}}
"""

    def _parse_research_results(
        self,
        messages: List[Any]
    ) -> Dict[str, Any]:
        """Parse Claude Agent SDK messages into structured data."""

        # Combine all messages
        full_text = " ".join([str(m) for m in messages])

        # Try to extract JSON first
        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', full_text, re.DOTALL)

        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                # If it looks like our expected structure, use it
                if any(key in data for key in ["website", "description", "products", "funding"]):
                    return data
            except json.JSONDecodeError:
                continue

        # Fallback: Extract key information with regex
        research = {}

        # Website
        website_patterns = [
            r'(?:website|url|site)[:\s]*(?:https?://)?([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)',
            r'(?:Visit|Check out|See)[:\s]*(?:https?://)?([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)',
            r'([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)(?:\s+is\s+their\s+website)',
        ]
        for pattern in website_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                research["website"] = match.group(1).lower().strip()
                break

        # Description
        desc_patterns = [
            r'(?:is|are|provides?|offers?|builds?|develops?)\s+([^.]{20,200})',
            r'(?:company\s+that|platform\s+that|service\s+that)\s+([^.]{20,200})',
        ]
        for pattern in desc_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                research["description"] = match.group(1).strip()
                break

        # Funding
        funding_patterns = [
            r'(?:raised|funding|series\s+[a-z])[^$]*\$(\d+(?:\.\d+)?[MBK])',
            r'\$(\d+(?:\.\d+)?[MBK])\s*(?:in\s+funding|raised|investment)',
        ]
        for pattern in funding_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                research["funding"] = {"amount": f"${match.group(1)}"}

                # Try to find stage
                stage_match = re.search(r'Series\s+([A-E])|seed|pre-?seed', full_text, re.I)
                if stage_match:
                    research["funding"]["stage"] = stage_match.group(0)
                break

        # Employee count
        emp_patterns = [
            r'(\d+[-–]\d+|\d+\+?)\s*(?:employees|people|team)',
            r'(?:team\s+of|staff\s+of)\s*(\d+[-–]\d+|\d+)',
        ]
        for pattern in emp_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                research["employee_count"] = match.group(1)
                break

        # Founded year
        year_patterns = [
            r'(?:founded|established|started)\s+(?:in\s+)?(\d{4})',
            r'(?:since|from)\s+(\d{4})',
        ]
        for pattern in year_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                year = int(match.group(1))
                if 1990 <= year <= 2025:  # Reasonable bounds
                    research["founded"] = str(year)
                    break

        # Products
        products = []
        product_patterns = [
            r'(?:products?|services?|offerings?|solutions?)(?:\s+include)?[:\s]+([^.]+)',
            r'(?:offers?|provides?|builds?)\s+([^.]+?)\s+(?:and|for)',
        ]
        for pattern in product_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                # Split by commas or "and"
                items = re.split(r',|\sand\s', match.group(1))
                products.extend([item.strip() for item in items if len(item.strip()) > 3])
                if products:
                    research["products"] = products[:5]  # Limit to 5
                    break

        # Recent news
        news = []
        news_patterns = [
            r'(?:recently|just|announced|launched)\s+([^.]+)',
            r'(?:news|announcement|development)[:\s]+([^.]+)',
        ]
        for pattern in news_patterns:
            matches = re.findall(pattern, full_text, re.I)
            for match in matches[:3]:  # Limit to 3 news items
                news.append(match.strip())
        if news:
            research["recent_news"] = news

        # Headquarters/Location
        location_patterns = [
            r'(?:headquartered?|based|located)\s+(?:in\s+)?([A-Za-z\s]+,\s*[A-Z]{2})',
            r'(?:offices?\s+in|from)\s+([A-Za-z\s]+,\s*[A-Z]{2})',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, full_text, re.I)
            if match:
                research["headquarters"] = match.group(1).strip()
                break

        return research

    def _assess_quality(self, research_data: Dict) -> float:
        """Assess quality of research (0-1 score)."""

        # Key fields and their weights
        field_weights = {
            "website": 0.2,
            "description": 0.2,
            "products": 0.15,
            "funding": 0.15,
            "employee_count": 0.1,
            "founded": 0.05,
            "headquarters": 0.05,
            "recent_news": 0.05,
            "technology_stack": 0.025,
            "key_customers": 0.025
        }

        total_score = 0
        for field, weight in field_weights.items():
            if research_data.get(field):
                # Check if field has substantial content
                value = research_data[field]
                if isinstance(value, str) and len(value) > 5:
                    total_score += weight
                elif isinstance(value, list) and len(value) > 0:
                    total_score += weight
                elif isinstance(value, dict) and len(value) > 0:
                    total_score += weight

        return min(total_score, 1.0)  # Cap at 1.0

    def _minimal_research(self, company_name: str, error_msg: str = "") -> Dict[str, Any]:
        """Return minimal research structure on failure."""
        return {
            "company_name": company_name,
            "website": None,
            "description": None,
            "products": [],
            "funding": {},
            "employee_count": None,
            "founded": None,
            "headquarters": None,
            "recent_news": [],
            "research_quality": 0.0,
            "error": error_msg or "Research failed",
            "researched_via": "claude_agent_sdk_failed",
            "research_timestamp": datetime.now().isoformat()
        }


# Example usage for testing
async def test_deep_research():
    """Test the deep research functionality."""

    researcher = CompanyDeepResearch()

    # Test with Voice AI companies
    test_companies = [
        ("Deepgram", "voice AI and speech recognition"),
        ("AssemblyAI", "voice AI and transcription"),
        ("Rev.ai", "speech-to-text services")
    ]

    print("\n" + "="*60)
    print("DEEP RESEARCH TEST")
    print("="*60)

    for company_name, domain in test_companies:
        print(f"\n{'='*60}")
        print(f"Researching: {company_name}")
        print('='*60)

        result = await researcher.research_company(
            company_name=company_name,
            target_domain=domain,
            additional_context={
                "industry": "AI/ML",
                "seed_companies": ["OpenAI", "Anthropic"]
            }
        )

        # Display results
        print(f"\n📊 Research Results for {company_name}:")
        print(f"  Website: {result.get('website', 'Not found')}")
        print(f"  Description: {result.get('description', 'Not found')[:100]}...")

        if result.get('funding'):
            print(f"  Funding: {result['funding'].get('amount', 'Unknown')} "
                  f"({result['funding'].get('stage', 'Unknown stage')})")

        print(f"  Employees: {result.get('employee_count', 'Unknown')}")
        print(f"  Founded: {result.get('founded', 'Unknown')}")
        print(f"  HQ: {result.get('headquarters', 'Unknown')}")

        if result.get('products'):
            print(f"  Products: {', '.join(result['products'][:3])}")

        if result.get('recent_news'):
            print(f"  Recent News: {result['recent_news'][0][:80]}...")

        print(f"  Research Quality: {result.get('research_quality', 0):.0%}")

        if result.get('error'):
            print(f"  ⚠️ Error: {result['error']}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_deep_research())