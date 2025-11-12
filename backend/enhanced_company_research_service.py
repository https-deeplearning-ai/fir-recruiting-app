"""
Enhanced Company Research Service with True Deep Research

This implementation adds:
1. Tavily web search for discovery (existing)
2. Claude Agent SDK WebSearch for deep research (NEW)
3. CoreSignal company validation and ID resolution (NEW)
4. Employee sampling from discovered companies (NEW)
5. Rich data enrichment pipeline (NEW)
"""

import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import re
from anthropic import Anthropic, RateLimitError
from supabase import create_client, Client
from claude_agent_sdk import query, ClaudeAgentOptions
import requests
import time


class EnhancedCompanyResearchService:
    """
    Enhanced Company Research with true deep research capabilities.

    Flow:
    1. Discovery: Tavily web search for broad company discovery
    2. Validation: Claude Agent SDK WebSearch for deep company research
    3. Resolution: CoreSignal validation to get company_ids
    4. Enrichment: Fetch company_base data from CoreSignal
    5. People Discovery: Sample employees from validated companies
    """

    def __init__(self):
        """Initialize service with all required API clients"""
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")

        # Initialize clients
        self.claude_client = Anthropic(api_key=self.anthropic_api_key)

        # Initialize Supabase for caching
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key) if supabase_url else None

        # Track discovered companies
        self.discovered_companies = set()

    async def research_companies_deep(
        self,
        seed_companies: List[str],
        target_domain: str,
        jd_context: Dict[str, Any],
        max_companies: int = 25
    ) -> Dict[str, Any]:
        """
        Main entry point for enhanced deep research pipeline.

        Args:
            seed_companies: List of seed company names
            target_domain: Target industry/domain (e.g., "voice AI")
            jd_context: Job description context
            max_companies: Maximum companies to deeply research

        Returns:
            Dict with discovered, validated, enriched companies and employees
        """
        print(f"\n{'='*80}")
        print(f"🚀 ENHANCED DEEP RESEARCH PIPELINE")
        print(f"{'='*80}\n")

        # Phase 1: Discovery via Tavily
        print("📡 PHASE 1: Discovery via Tavily Web Search")
        discovered = await self._phase1_tavily_discovery(seed_companies, target_domain)
        print(f"   ✅ Discovered {len(discovered)} companies\n")

        # Phase 2: Deep Research via Claude Agent SDK WebSearch
        print("🔍 PHASE 2: Deep Research via Claude Agent SDK WebSearch")
        researched = await self._phase2_claude_websearch_research(
            discovered[:max_companies],
            target_domain,
            jd_context
        )
        print(f"   ✅ Deep researched {len(researched)} companies\n")

        # Phase 3: CoreSignal Validation & ID Resolution
        print("✓ PHASE 3: CoreSignal Validation & ID Resolution")
        validated = await self._phase3_coresignal_validation(researched)
        print(f"   ✅ Validated {len(validated)} companies with CoreSignal IDs\n")

        # Phase 4: Company Data Enrichment
        print("💎 PHASE 4: Company Data Enrichment")
        enriched = await self._phase4_enrich_company_data(validated)
        print(f"   ✅ Enriched {len(enriched)} companies with full data\n")

        # Phase 5: Employee Discovery
        print("👥 PHASE 5: Employee Discovery")
        with_employees = await self._phase5_discover_employees(enriched, target_domain)
        print(f"   ✅ Found employees for {len(with_employees)} companies\n")

        return {
            "success": True,
            "discovered_companies": discovered,
            "researched_companies": researched,
            "validated_companies": validated,
            "enriched_companies": enriched,
            "companies_with_employees": with_employees,
            "summary": self._generate_summary(with_employees, target_domain)
        }

    # ========================================
    # PHASE 1: Tavily Discovery
    # ========================================

    async def _phase1_tavily_discovery(
        self,
        seed_companies: List[str],
        target_domain: str
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Use Tavily to discover companies in the domain.
        """
        if not self.tavily_api_key:
            print("   ⚠️  No Tavily API key, skipping web discovery")
            return []

        companies = []

        # Search for competitors of each seed company
        for seed in seed_companies[:5]:  # Limit to prevent rate limiting
            queries = [
                f"{seed} competitors in {target_domain}",
                f"companies like {seed}",
                f"{seed} alternatives {target_domain}"
            ]

            for query in queries:
                results = await self._search_tavily(query)
                companies.extend(results)
                await asyncio.sleep(0.5)  # Rate limit protection

        # Also do domain-specific searches
        domain_queries = [
            f"top {target_domain} companies 2024 2025",
            f"best {target_domain} startups",
            f"{target_domain} companies series A B C funding"
        ]

        for query in domain_queries:
            results = await self._search_tavily(query)
            companies.extend(results)
            await asyncio.sleep(0.5)

        # Deduplicate
        unique = {}
        for company in companies:
            name = company.get("name", "").lower().strip()
            if name and name not in unique:
                unique[name] = company

        return list(unique.values())

    async def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        """Search Tavily and extract company names."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": 10
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])

                        # Extract companies using Claude
                        companies = await self._extract_companies_from_tavily(results, query)
                        return companies

        except Exception as e:
            print(f"   ⚠️  Tavily search error: {e}")

        return []

    async def _extract_companies_from_tavily(
        self,
        results: List[Dict],
        query: str
    ) -> List[Dict[str, Any]]:
        """Use Claude to extract company names from Tavily results."""
        if not results:
            return []

        # Build context from search results
        context = f"Search query: {query}\n\nSearch results:\n"
        for i, result in enumerate(results[:5], 1):
            context += f"\n{i}. {result.get('title', '')}\n"
            context += f"   {result.get('content', '')[:200]}\n"

        prompt = f"""{context}

Extract ONLY company names from these search results.
Return as JSON array of strings: ["Company1", "Company2", ...]
Only include actual company names, not descriptions."""

        try:
            response = self.claude_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text
            companies_json = re.search(r'\[.*?\]', text, re.DOTALL)

            if companies_json:
                company_names = json.loads(companies_json.group(0))
                return [{"name": name, "source": "tavily", "query": query}
                       for name in company_names if name]

        except Exception as e:
            print(f"   ⚠️  Failed to extract companies: {e}")

        return []

    # ========================================
    # PHASE 2: Claude Agent SDK Deep Research
    # ========================================

    async def _phase2_claude_websearch_research(
        self,
        companies: List[Dict[str, Any]],
        target_domain: str,
        jd_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Use Claude Agent SDK WebSearch for deep company research.
        """
        researched = []

        for company in companies:
            company_name = company.get("name")
            print(f"   🔍 Deep researching: {company_name}")

            research = await self._deep_research_with_websearch(
                company_name,
                target_domain,
                jd_context
            )

            if research:
                company.update(research)
                researched.append(company)

            await asyncio.sleep(1)  # Rate limit protection

        return researched

    async def _deep_research_with_websearch(
        self,
        company_name: str,
        target_domain: str,
        jd_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Use Claude Agent SDK WebSearch to deeply research a company.
        """
        prompt = f"""Research this company in depth for competitive intelligence:

Company: {company_name}
Target Domain: {target_domain}
Context: We're analyzing companies in the {target_domain} space

Please use WebSearch to find:
1. Official company website and description
2. What products/services they offer
3. Their target customers and market position
4. Recent funding information
5. Employee count and growth trajectory
6. Technology stack (if relevant)
7. Key executives and founders
8. Recent news or announcements
9. How they compete in the {target_domain} space

Provide a comprehensive JSON response with all findings."""

        try:
            collected_messages = []
            options = ClaudeAgentOptions(
                model="claude-haiku-4-5-20251001",
                allowed_tools=["WebSearch"]
            )

            # Run async query with timeout
            async def run_search():
                async for message in query(prompt=prompt, options=options):
                    collected_messages.append(message)
                return collected_messages

            messages = await asyncio.wait_for(run_search(), timeout=15.0)

            # Extract structured data from messages
            final_text = " ".join([str(m) for m in messages])

            # Parse JSON from response
            json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
            if json_match:
                research_data = json.loads(json_match.group(0))
                return {
                    "websearch_research": research_data,
                    "researched": True
                }

        except asyncio.TimeoutError:
            print(f"      ⏱️  WebSearch timeout for {company_name}")
        except Exception as e:
            print(f"      ❌ WebSearch error for {company_name}: {e}")

        return None

    # ========================================
    # PHASE 3: CoreSignal Validation
    # ========================================

    async def _phase3_coresignal_validation(
        self,
        companies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: Validate companies exist in CoreSignal and get company_ids.
        """
        validated = []

        for company in companies:
            company_name = company.get("name")
            print(f"   ✓ Validating: {company_name}")

            # Search CoreSignal for this company
            company_id = await self._search_coresignal_company(company_name)

            if company_id:
                company["coresignal_company_id"] = company_id
                company["validated"] = True
                validated.append(company)
                print(f"      ✅ Found CoreSignal ID: {company_id}")
            else:
                print(f"      ❌ Not found in CoreSignal")

        return validated

    async def _search_coresignal_company(
        self,
        company_name: str
    ) -> Optional[int]:
        """
        Search CoreSignal for a company and return its ID.
        """
        if not self.coresignal_api_key:
            return None

        # Clean company name
        clean_name = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation)$', '', company_name, flags=re.I)

        # Search via employee endpoint to find company
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
            }
            # NOTE: preview endpoint does NOT accept "size" parameter
        }

        url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

        try:
            response = requests.post(url, json=query, headers=headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    # Extract company_id from first employee's current job
                    employee = results[0]
                    jobs = employee.get("member_experience_collection", [])
                    for job in jobs:
                        if job.get("date_to") is None:  # Current job
                            company_id = job.get("company_id")
                            if company_id:
                                return company_id

        except Exception as e:
            print(f"      ⚠️  CoreSignal search error: {e}")

        return None

    # ========================================
    # PHASE 4: Company Data Enrichment
    # ========================================

    async def _phase4_enrich_company_data(
        self,
        companies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Phase 4: Enrich validated companies with CoreSignal company_base data.
        """
        enriched = []

        for company in companies:
            company_id = company.get("coresignal_company_id")
            company_name = company.get("name")

            if not company_id:
                continue

            print(f"   💎 Enriching: {company_name} (ID: {company_id})")

            # Check cache first
            cached = await self._get_cached_company_data(company_id)
            if cached:
                company["coresignal_data"] = cached
                enriched.append(company)
                print(f"      ✅ Using cached data")
                continue

            # Fetch fresh data
            company_data = await self._fetch_company_base_data(company_id)

            if company_data:
                company["coresignal_data"] = company_data
                enriched.append(company)

                # Cache for future use
                await self._cache_company_data(company_id, company_data)
                print(f"      ✅ Enriched with {len(company_data)} fields")
            else:
                print(f"      ❌ Failed to enrich")

        return enriched

    async def _fetch_company_base_data(
        self,
        company_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch company_base data from CoreSignal."""
        if not self.coresignal_api_key:
            return None

        headers = {
            "accept": "application/json",
            "apikey": self.coresignal_api_key
        }

        url = f"https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"      ⚠️  Company fetch error: {e}")

        return None

    async def _get_cached_company_data(
        self,
        company_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached company data from Supabase."""
        if not self.supabase:
            return None

        try:
            result = self.supabase.table("company_intelligence_cache").select("enriched_data").eq(
                "company_id", company_id
            ).execute()

            if result.data and len(result.data) > 0:
                # Check freshness (30 days)
                cached_at = result.data[0].get("last_updated")
                if cached_at:
                    cache_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                    if (datetime.now(timezone.utc) - cache_time).days < 30:
                        return result.data[0].get("enriched_data")

        except Exception as e:
            print(f"      ⚠️  Cache lookup error: {e}")

        return None

    async def _cache_company_data(
        self,
        company_id: int,
        company_data: Dict[str, Any]
    ) -> None:
        """Cache company data in Supabase."""
        if not self.supabase:
            return

        try:
            self.supabase.table("company_intelligence_cache").upsert({
                "company_id": company_id,
                "company_name": company_data.get("name"),
                "enriched_data": company_data,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }).execute()

        except Exception as e:
            print(f"      ⚠️  Cache save error: {e}")

    # ========================================
    # PHASE 5: Employee Discovery
    # ========================================

    async def _phase5_discover_employees(
        self,
        companies: List[Dict[str, Any]],
        target_domain: str
    ) -> List[Dict[str, Any]]:
        """
        Phase 5: Discover employees from validated companies.
        """
        companies_with_employees = []

        for company in companies:
            company_id = company.get("coresignal_company_id")
            company_name = company.get("name")

            if not company_id:
                continue

            print(f"   👥 Finding employees at: {company_name}")

            # Sample employees with relevant roles
            employees = await self._sample_company_employees(
                company_id,
                company_name,
                target_domain,
                sample_size=5
            )

            if employees:
                company["sample_employees"] = employees
                company["employee_count"] = len(employees)
                companies_with_employees.append(company)
                print(f"      ✅ Found {len(employees)} relevant employees")
            else:
                print(f"      ❌ No relevant employees found")

        return companies_with_employees

    async def _sample_company_employees(
        self,
        company_id: int,
        company_name: str,
        target_domain: str,
        sample_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sample employees from a company, focusing on domain-relevant roles.
        """
        if not self.coresignal_api_key:
            return []

        # Build query for relevant employees
        role_keywords = self._get_domain_role_keywords(target_domain)

        headers = {
            "accept": "application/json",
            "apikey": self.coresignal_api_key,
            "Content-Type": "application/json"
        }

        # Search for employees at this company with relevant titles
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"member_current_employer_names.keyword": company_name}},
                        {"terms": {"member_current_position_title": role_keywords}}
                    ]
                }
            }
            # NOTE: preview endpoint does NOT accept "size" parameter
        }

        url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

        try:
            response = requests.post(url, json=query, headers=headers, timeout=10)
            if response.status_code == 200:
                employees = response.json()

                # Extract key employee info and limit to sample size
                employee_list = []
                for emp in employees[:sample_size]:  # Limit to desired sample size
                    employee_list.append({
                        "id": emp.get("id"),
                        "name": emp.get("full_name"),
                        "title": emp.get("job_title") or emp.get("title") or (emp.get("headline", "").split(" at ")[0] if emp.get("headline") else "N/A"),
                        "headline": emp.get("headline"),
                        "location": emp.get("location_raw_address") or emp.get("location"),
                        "linkedin_url": emp.get("linkedin_url")
                    })

                return employee_list

        except Exception as e:
            print(f"      ⚠️  Employee search error: {e}")

        return []

    def _get_domain_role_keywords(self, target_domain: str) -> List[str]:
        """Get relevant role keywords for a domain."""
        domain_lower = target_domain.lower()

        # Domain-specific keywords
        if "voice" in domain_lower or "speech" in domain_lower:
            return [
                "voice", "speech", "audio", "asr", "tts",
                "natural language", "conversational ai",
                "engineer", "scientist", "researcher",
                "product", "founder", "cto"
            ]
        elif "ai" in domain_lower or "ml" in domain_lower:
            return [
                "ai", "ml", "machine learning", "artificial intelligence",
                "deep learning", "neural", "llm", "nlp",
                "engineer", "scientist", "researcher",
                "product", "founder", "cto"
            ]
        else:
            # Generic tech roles
            return [
                "engineer", "developer", "architect",
                "product", "manager", "director",
                "founder", "cto", "vp"
            ]

    def _generate_summary(
        self,
        companies: List[Dict[str, Any]],
        target_domain: str
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_companies = len(companies)
        with_employees = len([c for c in companies if c.get("sample_employees")])
        total_employees = sum(c.get("employee_count", 0) for c in companies)

        return {
            "target_domain": target_domain,
            "total_companies_researched": total_companies,
            "companies_with_employees": with_employees,
            "total_employees_found": total_employees,
            "data_completeness": {
                "with_websearch_research": len([c for c in companies if c.get("websearch_research")]),
                "with_coresignal_validation": len([c for c in companies if c.get("validated")]),
                "with_company_data": len([c for c in companies if c.get("coresignal_data")]),
                "with_employees": with_employees
            }
        }


# ========================================
# Example Usage
# ========================================

async def example_usage():
    """Example of how to use the enhanced research service."""

    service = EnhancedCompanyResearchService()

    # Research Voice AI companies
    result = await service.research_companies_deep(
        seed_companies=["Deepgram", "AssemblyAI", "Otter.ai"],
        target_domain="voice AI",
        jd_context={
            "role_title": "Senior ML Engineer",
            "skills": ["speech recognition", "NLP", "Python"],
            "industry": "Voice AI"
        },
        max_companies=10
    )

    print("\n" + "="*80)
    print("📊 RESEARCH RESULTS")
    print("="*80)

    # Show summary
    summary = result["summary"]
    print(f"\nTarget Domain: {summary['target_domain']}")
    print(f"Companies Researched: {summary['total_companies_researched']}")
    print(f"Companies with Employees: {summary['companies_with_employees']}")
    print(f"Total Employees Found: {summary['total_employees_found']}")

    # Show sample company with employees
    companies = result["companies_with_employees"]
    if companies:
        sample = companies[0]
        print(f"\n🏢 Sample Company: {sample['name']}")

        if sample.get("websearch_research"):
            print(f"   Website: {sample['websearch_research'].get('website', 'N/A')}")
            print(f"   Description: {sample['websearch_research'].get('description', 'N/A')}")

        if sample.get("coresignal_data"):
            data = sample["coresignal_data"]
            print(f"   Employees: {data.get('employees_count', 'N/A')}")
            print(f"   Founded: {data.get('founded', 'N/A')}")
            print(f"   Funding: {data.get('last_funding_round_type', 'N/A')}")

        if sample.get("sample_employees"):
            print(f"\n   👥 Sample Employees:")
            for emp in sample["sample_employees"][:3]:
                print(f"      - {emp['name']}: {emp['title']}")

    return result


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())