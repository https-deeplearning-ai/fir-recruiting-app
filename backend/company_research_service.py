"""
Company Research Service
Discovers and evaluates companies for recruiting based on job requirements.
Uses multi-method discovery and AI-powered scoring.
"""

import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from anthropic import Anthropic
from supabase import create_client, Client
from gpt5_client import GPT5Client
from config import EXCLUDED_COMPANIES, is_excluded_company


class CompanyResearchConfig:
    """Configuration for company research"""

    # Discovery settings
    MAX_COMPANIES_TO_RESEARCH = 100
    MAX_WEB_SEARCHES = 10
    MIN_COMPANY_SIZE = 10
    MAX_DISCOVERY_TIME_SECONDS = 120

    # Scoring settings
    MIN_RELEVANCE_SCORE = 5.0
    COMPETITOR_SCORE_BOOST = 2.0

    # GPT-5 settings
    USE_GPT5 = True
    GPT5_BATCH_SIZE = 20  # Companies per batch

    # Fallback settings
    FALLBACK_TO_CLAUDE = True
    CLAUDE_MODEL = "claude-haiku-4-5-20251001"

    # API settings
    USE_TAVILY = True
    TAVILY_BASE_URL = "https://api.tavily.com/search"

    # Authoritative Sources for Competitive Intelligence
    # Prioritized list of trusted company directories and comparison sites
    AUTHORITATIVE_SOURCES = {
        "tier1_software": [
            "g2.com",           # Software reviews with alternatives/competitors
            "capterra.com",     # Software directory with comparisons
            "producthunt.com",  # Tech product discovery
            "alternativeto.net" # "Similar to X" recommendations
        ],
        "tier2_market_research": [
            "gartner.com",      # Industry reports and Magic Quadrants
            "forrester.com",    # Market analysis
            "cbinsights.com",   # Startup intelligence
            "crunchbase.com"    # Company data and similar companies
        ],
        "tier3_tech_specific": [
            "builtwith.com",    # Tech stack overlaps
            "stackshare.io",    # Technology comparisons
            "github.com"        # Open source project clustering
        ],
        "tier4_news": [
            "techcrunch.com",   # Startup coverage
            "venturebeat.com",  # Tech industry news
            "forbes.com"        # Forbes lists (Cloud 100, AI 50)
        ]
    }

    # Use case mode: "competitive_intelligence" or "recruiting"
    USE_CASE_MODE = "competitive_intelligence"  # Changed from recruiting to competitive analysis


class CompanyResearchService:
    """
    Discovers and evaluates companies for recruiting based on job requirements.
    Uses multi-method discovery and AI-powered scoring.
    """

    def __init__(self):
        """Initialize service with API clients"""
        self.config = CompanyResearchConfig()

        # Initialize API clients
        self.gpt5_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.gpt5_client = GPT5Client()

        self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Track discovered companies to avoid duplicates
        self.discovered_companies = set()

    # ========================================
    # Main Orchestration
    # ========================================

    async def research_companies_for_jd(
        self,
        jd_id: str,
        jd_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method for company research.

        Args:
            jd_id: Unique identifier for this JD
            jd_data: Parsed JD with requirements
            config: Optional configuration overrides

        Returns:
            Research results with discovered companies
        """
        try:
            # Create/update research session
            await self._create_research_session(jd_id, jd_data, config)

            # Extract signals from JD
            jd_context = self._extract_jd_signals(jd_data)

            # ============= DEBUG LOGGING =============
            print(f"\n{'='*100}")
            print(f"[RESEARCH FLOW] Starting research for JD ID: {jd_id}")
            print(f"[RESEARCH FLOW] Extracted JD Context:")
            print(f"  - title: {jd_context.get('title')}")
            print(f"  - industries: {jd_context.get('industries')}")
            print(f"  - seed_companies: {jd_context.get('seed_companies')}")
            print(f"  - domain_expertise: {jd_context.get('domain_expertise')}")
            print(f"  - key_skills: {jd_context.get('key_skills')}")
            print(f"{'='*100}\n")
            # =========================================

            # Phase 1: Discovery
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": "Discovering companies via web search and seed expansion..."
            })
            discovered = await self.discover_companies(
                jd_context.get("seed_companies", []),
                jd_context,
                config or {},
                jd_id  # Pass jd_id for live updates
            )

            # Update with discovered companies (store full objects for UI)
            company_names = [c.get("name") for c in discovered[:20]]  # First 20 names
            discovered_objects = [
                {
                    "name": c.get("name") or c.get("company_name"),
                    "discovered_via": c.get("discovered_via", "unknown"),
                    "company_id": c.get("company_id")
                }
                for c in discovered[:100] if c.get("name") or c.get("company_name")
            ]
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Discovered {len(discovered)} companies",
                "discovered_companies": company_names,  # Backward compat (names only)
                "discovered_companies_list": discovered_objects,  # Full objects for UI
                "total_discovered": len(discovered)
            })

            # Phase 2: Screening
            await self._update_session_status(jd_id, "running", {
                "phase": "screening",
                "action": "Screening companies for relevance..."
            })
            screened = await self._screen_companies(discovered, jd_context, jd_id)

            # Phase 3: Deep Research (top candidates only)
            await self._update_session_status(jd_id, "running", {
                "phase": "deep_research",
                "action": "Performing deep research on top candidates..."
            })
            evaluated = await self._deep_research_companies(screened[:25], jd_context, jd_id)

            # Phase 4: Categorization
            categorized = self.categorize_companies(evaluated, jd_context)

            # Phase 5: Save results
            await self._save_companies(jd_id, categorized)

            # Update session as completed (save screened companies for later evaluation)
            total_selected = len([c for c in evaluated if c["relevance_score"] >= 5.0])
            await self._update_session_status(jd_id, "completed", {
                "total_discovered": len(discovered),
                "total_evaluated": len(evaluated),
                "total_selected": total_selected,
                "screened_companies": screened[:100],  # Save for progressive evaluation
                "jd_context": jd_context  # Save for future evaluations
            })

            # ============= DEBUG LOGGING =============
            print(f"\n{'='*100}")
            print(f"[RESEARCH FLOW] Research COMPLETED for JD ID: {jd_id}")
            print(f"[RESEARCH FLOW] Summary:")
            print(f"  - total_discovered: {len(discovered)}")
            print(f"  - total_evaluated: {len(evaluated)}")
            print(f"  - total_selected: {total_selected}")
            print(f"[RESEARCH FLOW] Status updated to: COMPLETED")
            print(f"{'='*100}\n")
            # =========================================

            return {
                "success": True,
                "session_id": jd_id,
                "discovered_companies": discovered[:100],  # All discovered (up to 100)
                "screened_companies": screened[:100],      # Screened/ranked by initial score
                "evaluated_companies": evaluated,          # Top 25 with full evaluation
                "companies": categorized,                  # Backward compatibility
                "companies_by_category": categorized,      # Categorized evaluated companies
                "summary": {
                    **self._generate_summary(categorized),
                    "total_discovered": len(discovered),
                    "total_screened": len(screened),
                    "total_evaluated": len(evaluated),
                    "evaluation_progress": {
                        "evaluated_count": len(evaluated),
                        "remaining_count": len(screened) - len(evaluated)
                    }
                }
            }

        except Exception as e:
            await self._update_session_status(jd_id, "failed", {"error": str(e)})
            raise

    async def evaluate_additional_companies(
        self,
        jd_id: str,
        start_index: int = 25,
        count: int = 25
    ) -> Dict[str, Any]:
        """
        Evaluate additional companies from the screened list.

        Args:
            jd_id: Session ID to continue evaluation
            start_index: Starting index in screened list (default 25)
            count: Number of companies to evaluate (default 25)

        Returns:
            Dict with newly evaluated companies
        """
        try:
            # Retrieve session data
            session_response = self.supabase.table("company_research_sessions").select("*").eq(
                "jd_id", jd_id
            ).execute()

            if not session_response.data or len(session_response.data) == 0:
                raise ValueError(f"Session not found: {jd_id}")

            session = session_response.data[0]
            search_config = session.get("search_config", {})
            screened_companies = search_config.get("screened_companies", [])
            jd_context = search_config.get("jd_context", {})

            if not screened_companies:
                raise ValueError("No screened companies found in session")

            # Get the batch to evaluate
            end_index = min(start_index + count, len(screened_companies))
            batch = screened_companies[start_index:end_index]

            print(f"\n[EVALUATE MORE] Evaluating companies {start_index}-{end_index} of {len(screened_companies)}")

            # Evaluate the batch
            evaluated = await self._deep_research_companies(batch, jd_context, jd_id)

            # Categorize the newly evaluated companies
            categorized = self.categorize_companies(evaluated, jd_context)

            # Save newly evaluated companies
            await self._save_companies(jd_id, categorized)

            # Update session with new progress
            total_evaluated_now = end_index
            await self._update_session_status(jd_id, "completed", {
                "total_evaluated": total_evaluated_now,
                "evaluation_progress": {
                    "evaluated_count": total_evaluated_now,
                    "remaining_count": len(screened_companies) - total_evaluated_now
                }
            })

            return {
                "success": True,
                "session_id": jd_id,
                "evaluated_companies": evaluated,
                "companies_by_category": categorized,
                "evaluation_progress": {
                    "evaluated_count": total_evaluated_now,
                    "total_count": len(screened_companies),
                    "remaining_count": len(screened_companies) - total_evaluated_now
                }
            }

        except Exception as e:
            print(f"[EVALUATE MORE ERROR] {str(e)}")
            raise

    # ========================================
    # Discovery Methods
    # ========================================

    async def discover_companies(
        self,
        seed_companies: List[str],
        jd_context: Dict[str, Any],
        config: Dict[str, Any],
        jd_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-method company discovery pipeline with live progress updates.

        Methods:
        1. Seed expansion (competitors of mentioned companies)
        2. Web search (Tavily)
        """
        companies = []

        # Method 1: Expand seed companies (filter excluded companies first)
        if seed_companies:
            # Filter out excluded companies from seed list
            filtered_seeds = [s for s in seed_companies if not is_excluded_company(s)]

            if len(filtered_seeds) < len(seed_companies):
                excluded_seeds = [s for s in seed_companies if is_excluded_company(s)]
                print(f"\n[EXCLUDED] Removed {len(excluded_seeds)} excluded seed companies: {excluded_seeds}\n")

            for i, seed in enumerate(filtered_seeds[:15], 1):  # Increased from 5 to 15 to capture more competitor signals
                if jd_id:
                    await self._update_session_status(jd_id, "running", {
                        "phase": "discovery",
                        "action": f"Searching competitors of {seed} ({i}/{min(len(filtered_seeds), 15)})..."
                    })
                competitors = await self.search_competitors_web(seed)
                companies.extend(competitors)

        # Method 2: Direct web search
        if self.config.USE_TAVILY and self.tavily_api_key:
            search_queries = self._generate_search_queries(jd_context)
            for i, query in enumerate(search_queries[:5], 1):  # Increased to 5 to leverage multiple seed companies
                if jd_id:
                    await self._update_session_status(jd_id, "running", {
                        "phase": "discovery",
                        "action": f"Web search: \"{query[:50]}...\" ({i}/{min(len(search_queries), 5)})"
                    })
                web_results = await self._search_web(query)
                companies.extend(await self._extract_companies_from_web(web_results, query))

        # Deduplicate
        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Deduplicating {len(companies)} companies..."
            })
        unique_companies = self._deduplicate_companies(companies)

        # Update session with discovered company names for live progress
        if jd_id:
            discovered_names = [c.get('company_name') or c.get('name') for c in unique_companies[:100] if c.get('company_name') or c.get('name')]
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Found {len(unique_companies)} unique companies",
                "discovered_companies": discovered_names[:100],
                "total_discovered": len(unique_companies)
            })

        # Enrich with CoreSignal data
        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Enriching {len(unique_companies[:100])} companies with CoreSignal data..."
            })
        enriched = await self._enrich_companies(unique_companies[:100])

        # Final update with enriched company count
        if jd_id:
            enriched_names = [c.get('company_name') or c.get('name') for c in enriched if c.get('company_name') or c.get('name')]
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Discovery complete: {len(enriched)} companies ready for screening",
                "discovered_companies": enriched_names,
                "total_discovered": len(enriched)
            })

        return enriched

    async def search_competitors_web(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Find competitor companies via web search.

        Args:
            company_name: Seed company to find competitors for

        Returns:
            List of competitor company dictionaries
        """
        if not self.config.USE_TAVILY or not self.tavily_api_key:
            return []

        queries = [
            f"{company_name} competitors",
            f"companies like {company_name}",
            f"{company_name} alternatives"
        ]

        competitors = []
        for query in queries:
            results = await self._search_web(query)
            companies = await self._extract_companies_from_web(results, query)
            competitors.extend(companies)

        return competitors[:20]  # Return top 20

    # ========================================
    # Evaluation Methods
    # ========================================

    async def evaluate_company_relevance_gpt5(
        self,
        company_data: Dict[str, Any],
        jd_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score company relevance using GPT-5.

        Uses GPT-5's automatic reasoning routing for deep analysis.
        """
        if not self.gpt5_client:
            # Fallback to Claude if GPT-5 not available
            return await self.evaluate_company_relevance_claude(company_data, jd_context)

        try:
            return await self.gpt5_client.deep_research(company_data, jd_context)
        except Exception as e:
            print(f"GPT-5 evaluation error: {e}")
            # Fallback to Claude
            if self.config.FALLBACK_TO_CLAUDE:
                return await self.evaluate_company_relevance_claude(company_data, jd_context)
            raise

    async def evaluate_company_relevance_claude(
        self,
        company_data: Dict[str, Any],
        jd_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate company for competitive intelligence using Claude Haiku 4.5.

        Focus: Market overlap, product similarity, competitive positioning
        (NOT recruiting/talent assessment)
        """
        prompt = f"""Evaluate this company's competitive similarity for market intelligence.

TARGET DOMAIN/MARKET:
{json.dumps(jd_context, indent=2)}

CANDIDATE COMPANY:
{json.dumps(company_data, indent=2)}

SCORING RUBRIC (1-10):
• 9-10: DIRECT COMPETITOR - Same product category, same target market, clear competitive overlap
  Example: Both are Voice AI platforms targeting developers

• 7-8: ADJACENT PLAYER - Related product with overlapping use cases, could pivot to compete
  Example: AI platform with voice capabilities vs pure Voice AI

• 5-6: SAME CATEGORY - Broad category match but different specific focus
  Example: Both in AI/ML but one is voice, other is vision

• 3-4: TANGENTIAL - Uses similar tech but different application or market
  Example: Large tech company with minor voice features

• 1-2: NOT RELEVANT - Different industry entirely, no competitive overlap

EVALUATE FOR:
- Product/service similarity (most important)
- Target market overlap
- Competitive positioning
- Technology stack alignment

Provide JSON response:
{{
  "relevance_score": 8.5,
  "category": "direct_competitor|adjacent_company|same_category|tangential",
  "reasoning": "Why this company is/isn't a competitor. Focus on product overlap and market positioning.",
  "competitive_positioning": {{
    "market_overlap": "high|medium|low",
    "product_similarity": "Description of how products compare",
    "differentiation": "Key differences in positioning"
  }},
  "market_intelligence": {{
    "target_customers": "Who they serve",
    "unique_value_prop": "What makes them different",
    "stage_maturity": "early|growth|mature"
  }}
}}

DO NOT include recruiting/hiring/talent fields. This is competitive intelligence, not recruiting."""

        response = self.claude_client.messages.create(
            model=self.config.CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse Claude's response
        content = response.content[0].text

        # Extract JSON from response (Claude may add explanation)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        # Fallback structure if parsing fails
        return {
            "relevance_score": 5.0,
            "category": "talent_pool",
            "reasoning": content[:200],
            "talent_assessment": {},
            "poaching_strategy": {},
            "specific_targets": []
        }

    async def batch_screen_companies_gpt5(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any]
    ) -> List[float]:
        """
        Batch screening with GPT-5-mini.
        Process up to 20 companies per API call for efficiency.
        """
        if not self.gpt5_client:
            # Return default scores if GPT-5 not available
            return [5.0] * len(companies)

        try:
            return await self.gpt5_client.batch_screen(companies, jd_context)
        except Exception as e:
            print(f"Batch screening error: {e}")
            # Return default scores on error
            return [5.0] * len(companies)

    # ========================================
    # Categorization
    # ========================================

    def categorize_companies(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group companies by relationship type.

        Categories (Competitive Intelligence):
        - direct_competitor: Same product/market (score 9-10)
        - adjacent_company: Related product with overlapping use cases (score 7-8)
        - same_category: Broad category match but different focus (score 5-6)
        - tangential: Similar tech but different application (score 3-4)
        - similar_stage: Same growth phase (legacy, for backward compatibility)
        - talent_pool: Known for quality talent (legacy, for backward compatibility)
        """
        categorized = {
            "direct_competitor": [],
            "adjacent_company": [],
            "same_category": [],      # NEW - competitive intelligence category
            "tangential": [],          # NEW - competitive intelligence category
            "similar_stage": [],       # Legacy category (backward compatibility)
            "talent_pool": []          # Legacy category (backward compatibility)
        }

        for company in companies:
            category = company.get("category", "talent_pool")
            # Skip companies marked as not relevant
            if category == "not_relevant":
                continue
            categorized[category].append(company)

        # Sort each category by score
        for category in categorized:
            categorized[category].sort(
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )

        return categorized

    # ========================================
    # Helper Methods
    # ========================================

    def _extract_jd_signals(self, jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key signals from job description."""
        return {
            "title": jd_data.get("title", ""),
            "company_stage": jd_data.get("company_stage", "unknown"),
            "industries": jd_data.get("industries", []),
            "seed_companies": jd_data.get("target_companies", {}).get("mentioned_companies", []),
            "excluded_companies": jd_data.get("target_companies", {}).get("excluded_companies", []),
            "key_skills": jd_data.get("requirements", {}).get("technical_skills", []),
            "domain_expertise": jd_data.get("requirements", {}).get("domain", ""),
            "team_size_range": jd_data.get("team_size_range", [10, 1000])
        }

    def _generate_search_queries(self, jd_context: Dict[str, Any]) -> List[str]:
        """
        Generate high-quality search queries for competitive intelligence.

        Strategy: Domain-first approach using authoritative sources.
        Priority: Domain > Seed Companies > Industry > Stage
        """
        queries = []

        domain = jd_context.get("domain_expertise", "")
        industry = jd_context.get("industries", [""])[0] if jd_context.get("industries") else ""
        seed_companies = jd_context.get("seed_companies", [])

        # Get authoritative source domains
        tier1_sources = self.config.AUTHORITATIVE_SOURCES.get("tier1_software", [])
        tier2_sources = self.config.AUTHORITATIVE_SOURCES.get("tier2_market_research", [])

        # PRIORITY 1: Domain-specific alternatives on G2/Capterra
        if domain:
            # Tier 1: Software comparison sites (best for alternatives/competitors)
            site_filter = " OR ".join([f"site:{s}" for s in tier1_sources[:2]])  # G2 + Capterra
            queries.append(f"({site_filter}) \"{domain}\" alternatives competitors")

            # Tier 2: Market research sites (best for comprehensive lists)
            site_filter_tier2 = " OR ".join([f"site:{s}" for s in tier2_sources[:2]])  # Gartner + Crunchbase
            queries.append(f"({site_filter_tier2}) \"{domain}\" companies directory")

        # PRIORITY 2: Competitor expansion from seed companies (use top 3 for better coverage)
        if seed_companies and len(seed_companies) > 0:
            site_filter = " OR ".join([f"site:{s}" for s in tier1_sources[:3]])
            # Use top 3 seed companies (or all if fewer than 3)
            for seed in seed_companies[:3]:
                queries.append(f"({site_filter}) \"companies like {seed}\" alternatives")

        # PRIORITY 3: Industry-specific search (if domain not available)
        if not domain and industry:
            site_filter = " OR ".join([f"site:{s}" for s in tier2_sources[:2]])
            queries.append(f"({site_filter}) \"{industry}\" companies 2024 2025")

        # FALLBACK: General search without site filter (if nothing else worked)
        if not queries:
            if domain:
                queries.append(f"\"{domain}\" companies directory 2024")
            elif industry:
                queries.append(f"\"{industry}\" companies list 2024")
            else:
                queries.append("tech companies directory 2024")

        # ============= DEBUG LOGGING =============
        print(f"\n{'='*100}")
        print(f"[SEARCH QUERIES] Generated competitive intelligence queries:")
        for i, q in enumerate(queries[:6], 1):
            print(f"  {i}. {q}")
        print(f"[SEARCH QUERIES] Input context:")
        print(f"  - domain: {domain}")
        print(f"  - industry: {industry}")
        print(f"  - seed_companies: {seed_companies[:3]}")  # Show top 3 seeds used
        print(f"[SEARCH QUERIES] Strategy: Domain-first with authoritative sources + top 3 seed companies")
        print(f"{'='*100}\n")
        # =========================================

        return queries[:6]  # Return top 6 queries (2 domain + 3 seed + 1 fallback)

    async def _search_web(self, query: str) -> Dict[str, Any]:
        """Execute web search using Tavily API with enhanced parameters."""
        if not self.tavily_api_key:
            return {"results": [], "answer": None}

        headers = {
            "Content-Type": "application/json"
        }

        # Use Tavily's advanced search with LLM-generated answer
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",  # Better content retrieval (2 credits)
            "max_results": 10,
            "include_answer": True,      # LLM-generated answer
            "include_raw_content": True  # Full page content for better parsing
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.TAVILY_BASE_URL,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Tavily search failed ({response.status}): {error_text}")
                        return {"results": [], "answer": None}
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {"results": [], "answer": None}

    async def _extract_companies_from_web(self, web_results: Dict[str, Any], search_query: str = "") -> List[Dict[str, Any]]:
        """Extract company names using Claude to parse Tavily results intelligently."""

        # Prepare context for Claude
        llm_answer = web_results.get("answer", "")
        search_results = web_results.get("results", [])[:5]  # Top 5 results

        # Build condensed context from search results
        results_text = ""
        for i, result in enumerate(search_results, 1):
            results_text += f"\n{i}. {result.get('title', '')}\n"
            results_text += f"   {result.get('content', '')[:300]}...\n"

        prompt = f"""Extract actual company names from this web search about companies.

TAVILY LLM ANSWER:
{llm_answer}

TOP SEARCH RESULTS:
{results_text}

TASK: Extract ONLY real company names mentioned in the content.

RULES:
- Include ONLY actual company names (e.g., "Stripe", "Square", "Adyen")
- EXCLUDE article titles (e.g., "The Best Stripe Alternatives")
- EXCLUDE generic words (e.g., "However", "Best", "Top", "Companies")
- EXCLUDE fragments (e.g., "Payouts Small", "Tube The")
- EXCLUDE person names unless they're company founders mentioned with their company

Return a JSON array of company names ONLY:
["Company1", "Company2", "Company3", ...]

If no clear company names are found, return an empty array: []"""

        try:
            response = self.claude_client.messages.create(
                model=self.config.CLAUDE_MODEL,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse Claude's response
            response_text = response.content[0].text.strip()

            # Extract JSON array from response
            if response_text.startswith("["):
                company_names = json.loads(response_text)
            else:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    company_names = json.loads(json_match.group(0))
                else:
                    company_names = []

            # Convert to company objects with source tracking
            companies = []
            for i, name in enumerate(company_names, 1):
                if name and len(name) > 2 and name not in self.discovered_companies:
                    companies.append({
                        "name": name,
                        "discovered_via": "web_search_llm",
                        "source_url": search_results[0].get("url") if search_results else None,
                        "source_query": search_query,  # NEW: Track the search query
                        "source_result_rank": i  # NEW: Track which result it came from
                    })
                    self.discovered_companies.add(name)

            print(f"✓ Claude extracted {len(companies)} companies from Tavily results")
            return companies

        except Exception as e:
            print(f"Error extracting companies with Claude: {e}")
            return []

    def _deduplicate_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate companies based on name.
        Also filters out excluded companies (DLAI, Deep Learning.AI, AI Fund).
        """
        seen = set()
        unique = []
        excluded_found = []

        for company in companies:
            name = company.get("name", "").lower().strip()
            if not name:
                continue

            # Check if this company should be excluded
            if is_excluded_company(name):
                if name not in seen:
                    excluded_found.append(company.get("name", ""))
                    seen.add(name)
                continue

            # Add unique, non-excluded companies
            if name not in seen:
                seen.add(name)
                unique.append(company)

        # Log excluded companies for debugging
        if excluded_found:
            print(f"\n[EXCLUDED] Filtered {len(excluded_found)} excluded companies: {excluded_found}\n")

        return unique

    async def _enrich_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich companies with CoreSignal data."""
        enriched = []

        for company in companies:
            # For now, just pass through
            # In future, could search CoreSignal for company data
            enriched.append(company)

        return enriched

    async def _screen_companies(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any],
        jd_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Quick screening using GPT-5-mini with live progress."""
        # Filter out excluded companies before screening
        filtered_companies = []
        excluded_count = 0

        for company in companies:
            company_name = company.get("name", "")
            if is_excluded_company(company_name):
                excluded_count += 1
            else:
                filtered_companies.append(company)

        if excluded_count > 0:
            print(f"\n[SCREENING] Skipped {excluded_count} excluded companies during screening\n")

        total = len(filtered_companies)
        batch_size = 20  # GPT-5-mini processes 20 companies per batch

        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "screening",
                "action": f"Screening {total} companies for relevance...",
                "total_evaluated": 0
            })

        # Process in batches with progress updates
        all_scores = []
        for i in range(0, total, batch_size):
            batch = filtered_companies[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            if jd_id:
                await self._update_session_status(jd_id, "running", {
                    "phase": "screening",
                    "action": f"Screening batch {batch_num}/{total_batches} ({len(batch)} companies)...",
                    "total_evaluated": i
                })

            batch_scores = await self.batch_screen_companies_gpt5(batch, jd_context)
            all_scores.extend(batch_scores)

        # Add scores to filtered companies
        for i, company in enumerate(filtered_companies):
            if i < len(all_scores):
                company["screening_score"] = all_scores[i]

        # Sort by score and return top candidates
        filtered_companies.sort(key=lambda x: x.get("screening_score", 0), reverse=True)

        if jd_id:
            await self._update_session_status(jd_id, "running", {
                "phase": "screening",
                "action": f"Screening complete. Top candidate: {filtered_companies[0].get('name') if filtered_companies else 'None'}",
                "total_evaluated": total
            })

        return filtered_companies

    async def _deep_research_companies(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any],
        jd_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Deep research on top candidates with live progress."""
        # Filter out excluded companies before deep research
        filtered_companies = []
        excluded_count = 0

        for company in companies:
            company_name = company.get("name", "")
            if is_excluded_company(company_name):
                excluded_count += 1
            else:
                filtered_companies.append(company)

        if excluded_count > 0:
            print(f"\n[DEEP RESEARCH] Skipped {excluded_count} excluded companies during deep research\n")

        evaluated = []
        total = len(filtered_companies)

        for i, company in enumerate(filtered_companies, 1):
            company_name = company.get("name", "Unknown")

            # Update status with current company being evaluated
            if jd_id:
                await self._update_session_status(jd_id, "running", {
                    "phase": "deep_research",
                    "action": f"Evaluating {company_name} ({i}/{total})...",
                    "current_company": company_name,
                    "total_evaluated": i
                })

            evaluation = await self.evaluate_company_relevance_gpt5(company, jd_context)

            company["relevance_score"] = evaluation.get("relevance_score", 5.0)
            company["category"] = evaluation.get("category", "talent_pool")
            company["reasoning"] = evaluation.get("reasoning", "")
            company["gpt5_analysis"] = evaluation

            evaluated.append(company)

        return evaluated

    def _map_category_for_db(self, category: str) -> str:
        """
        Map competitive intelligence categories to database-compatible categories.

        Database constraint only allows: direct_competitor, adjacent_company, similar_stage, talent_pool
        New categories map as follows:
        - same_category -> adjacent_company (both are related but not direct)
        - tangential -> similar_stage (loosely related)
        """
        category_mapping = {
            "direct_competitor": "direct_competitor",
            "adjacent_company": "adjacent_company",
            "same_category": "adjacent_company",     # Map to adjacent (related but not direct)
            "tangential": "similar_stage",           # Map to similar_stage (loosely related)
            "similar_stage": "similar_stage",
            "talent_pool": "talent_pool"
        }
        return category_mapping.get(category, "talent_pool")

    async def _save_companies(self, jd_id: str, categorized: Dict[str, List]) -> None:
        """Save discovered companies to database."""
        for category, companies in categorized.items():
            # Map category to database-compatible value
            db_category = self._map_category_for_db(category)

            for company in companies:
                data = {
                    "jd_id": jd_id,
                    "company_name": company.get("name"),
                    "company_id": company.get("company_id"),
                    "relevance_score": company.get("relevance_score"),
                    "relevance_reasoning": company.get("reasoning"),
                    "category": db_category,  # Use mapped category
                    "discovered_via": company.get("discovered_via"),
                    "company_data": company.get("company_data"),
                    "gpt5_analysis": company.get("gpt5_analysis")
                }

                self.supabase.table("target_companies").insert(data).execute()

    async def _create_research_session(
        self,
        jd_id: str,
        jd_data: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> None:
        """Create or update research session."""
        session_data = {
            "jd_id": jd_id,
            "jd_title": jd_data.get("title"),
            "jd_company": jd_data.get("company"),
            "jd_requirements": jd_data.get("requirements"),
            "search_config": config,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        self.supabase.table("company_research_sessions").upsert(session_data).execute()

    async def _update_session_status(
        self,
        jd_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update research session status with detailed progress tracking.

        Enhanced to support real-time streaming:
        - current_phase: discovery, screening, deep_research
        - current_action: Detailed description of what's happening now
        - discovered_companies_list: Names of companies found so far
        - phase_progress: Progress breakdown by phase
        """
        update_data = {"status": status}

        if metadata:
            # Existing metrics
            if "total_discovered" in metadata:
                update_data["total_discovered"] = metadata["total_discovered"]
            if "total_evaluated" in metadata:
                update_data["total_evaluated"] = metadata["total_evaluated"]
            if "total_selected" in metadata:
                update_data["total_selected"] = metadata["total_selected"]
            if "error" in metadata:
                update_data["error_message"] = metadata["error"]

            # NEW: Detailed progress tracking
            if "phase" in metadata:
                # Store in search_config JSONB field (reusing existing field)
                current_config = update_data.get("search_config", {}) or {}
                current_config["current_phase"] = metadata["phase"]
                update_data["search_config"] = current_config

            if "action" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["current_action"] = metadata["action"]
                update_data["search_config"] = current_config

            if "discovered_companies" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["discovered_companies"] = metadata["discovered_companies"]
                update_data["search_config"] = current_config

            if "discovered_companies_list" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["discovered_companies_list"] = metadata["discovered_companies_list"]
                update_data["search_config"] = current_config

            if "current_company" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["current_company"] = metadata["current_company"]
                update_data["search_config"] = current_config

            # NEW: Save screened companies for progressive evaluation
            if "screened_companies" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["screened_companies"] = metadata["screened_companies"]
                update_data["search_config"] = current_config

            # NEW: Save JD context for future evaluations
            if "jd_context" in metadata:
                current_config = update_data.get("search_config", {}) or {}
                current_config["jd_context"] = metadata["jd_context"]
                update_data["search_config"] = current_config

        if status == "completed":
            update_data["completed_at"] = datetime.now().isoformat()

        self.supabase.table("company_research_sessions").update(update_data).eq(
            "jd_id", jd_id
        ).execute()

    def _generate_summary(self, categorized: Dict[str, List]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_companies = sum(len(companies) for companies in categorized.values())

        return {
            "total_companies": total_companies,
            "by_category": {
                cat: len(companies) for cat, companies in categorized.items()
            },
            "top_companies": [
                companies[0]["name"] if companies else None
                for companies in categorized.values()
            ]
        }
