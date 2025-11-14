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
from datetime import datetime, timedelta, timezone
import re
from anthropic import Anthropic, RateLimitError
from supabase import create_client, Client
from gpt5_client import GPT5Client
from config import EXCLUDED_COMPANIES, is_excluded_company
from company_id_cache_service import CompanyIDCacheService


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
            # PRIORITY: Startup-focused sources first (best for discovery)
            "crunchbase.com",       # Company data and similar companies (HIGHEST PRIORITY)
            "ycombinator.com",      # Y Combinator startup directory (excellent for early-stage)
            "wellfound.com",        # AngelList/Wellfound startup database
            # Market research sources
            "cbinsights.com",       # Startup intelligence
            "gartner.com",          # Industry reports and Magic Quadrants
            "forrester.com"         # Market analysis
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

        # Initialize CoreSignal service for company enrichment
        self.coresignal_service = None
        if self.coresignal_api_key:
            from coresignal_service import CoreSignalService
            self.coresignal_service = CoreSignalService()

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize Company ID Cache Service
        self.cache_service = CompanyIDCacheService(supabase_url, supabase_key)

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
            discovered, cache_metrics = await self.discover_companies(
                jd_context.get("seed_companies", []),
                jd_context,
                config or {},
                jd_id  # Pass jd_id for live updates
            )

            # Phase 2: Claude Haiku Screening with Web Search (CONDITIONAL)
            skip_ai_scoring = config.get('skip_ai_scoring', False)

            if skip_ai_scoring:
                # SKIP AI SCORING - Assign default scores for faster results
                print(f"\n{'='*80}")
                print(f"[SCREENING] ⚡ AI scoring SKIPPED by user")
                print(f"[SCREENING] Assigning default scores to {len(discovered)} companies")
                print(f"{'='*80}\n")

                for company in discovered:
                    company['relevance_score'] = 5.0
                    company['screening_score'] = 5.0
                    company['scored_by'] = 'default_no_ai'
                    company['screening_reasoning'] = (
                        'AI scoring was skipped for faster results. '
                        'This company has not been evaluated by Claude Haiku.'
                    )

                print(f"\n[SCREENING] ✓ Default scores assigned")
                print(f"[SCREENING] {len(discovered)} companies ready for display\n")

            else:
                # FULL AI SCORING - Claude Haiku with web search
                print(f"\n{'='*80}")
                print(f"[SCREENING] Starting Claude Haiku screening with web search on {len(discovered)} companies...")
                print(f"{'='*80}\n")

                # Screen companies one-by-one with Claude Haiku + web search
                await self.screen_companies_with_haiku(
                    discovered,
                    jd_context,
                    jd_id
                )

                # Extract scores for logging
                scores = [c.get('relevance_score', 5.0) for c in discovered]
                print(f"\n[SCREENING] Completed! Score range: {min(scores):.1f} - {max(scores):.1f}")
                print(f"[SCREENING] Top 5 companies:")
                sorted_for_display = sorted(discovered, key=lambda c: c.get('relevance_score', 0), reverse=True)
                for i, c in enumerate(sorted_for_display[:5], 1):
                    print(f"  {i}. {c.get('name')}: {c.get('relevance_score', 0):.1f} - {c.get('screening_reasoning', 'N/A')[:60]}")

            # Phase 3: Sample Employee Fetching (NEW - Proof of talent pool)
            await self._update_session_status(jd_id, "running", {
                "phase": "employee_sampling",
                "action": f"Fetching sample employees for top {min(len(discovered), 50)} companies..."
            })

            print(f"\n{'='*80}")
            print(f"[EMPLOYEE SAMPLING] Fetching sample employees...")
            print(f"{'='*80}\n")

            discovered_with_employees = await self._add_sample_employees_to_companies(
                discovered,
                jd_context,
                jd_id,
                limit_per_company=5
            )

            # Phase 4: Sort by relevance score (highest first)
            discovered_sorted = sorted(
                discovered_with_employees,
                key=lambda c: c.get('relevance_score', 0),
                reverse=True
            )

            print(f"\n[SORTING] Companies sorted by relevance score (highest first)")
            print(f"  Top 5 companies:")
            for i, c in enumerate(discovered_sorted[:5], 1):
                print(f"    {i}. {c.get('name')} - Score: {c.get('relevance_score', 0):.1f}")

            # Update with ALL discovered companies (enriched with scores, metadata, employees)
            company_names = [c.get("name") for c in discovered_sorted[:20]]  # First 20 names
            discovered_objects = [
                {
                    "name": c.get("name") or c.get("company_name"),
                    "discovered_via": c.get("discovered_via", "unknown"),
                    "coresignal_company_id": c.get("coresignal_id"),  # Standardize field name for employee search
                    "coresignal_data": c.get("coresignal_data", {}),
                    "source_url": c.get("source_url"),
                    "source_query": c.get("source_query"),
                    "source_result_rank": c.get("source_result_rank"),
                    # NEW: Relevance scoring
                    "relevance_score": c.get("relevance_score", 5.0),
                    "screening_score": c.get("screening_score", 5.0),
                    "scored_by": c.get("scored_by", "gpt5_mini"),
                    # NEW: Metadata enrichment
                    "industry": c.get("industry"),
                    "employees_count": c.get("employees_count") or c.get("employee_count"),
                    "size_range": c.get("size_range"),
                    "founded": c.get("founded"),
                    "headquarters": c.get("headquarters") or c.get("location_hq_city"),
                    # NEW: Sample employees
                    "sample_employees": c.get("sample_employees", []),
                    "sample_employees_count": len(c.get("sample_employees", []))
                }
                for c in discovered_sorted if c.get("name") or c.get("company_name")
            ]

            # NEW FLOW: Return ALL discovered companies with scores, metadata, and employees
            # Mark session as "completed" (enrichment done, ready to use)
            await self._update_session_status(jd_id, "completed", {
                "phase": "enrichment_complete",
                "action": f"Enrichment complete: {len(discovered_sorted)} companies scored and ready",
                "discovered_companies": company_names,  # Backward compat (names only)
                "discovered_companies_list": discovered_objects,  # Full objects for UI with all enrichments
                "total_discovered": len(discovered_sorted),
                "evaluation_status": "scored",  # All companies have relevance scores
                "jd_context": jd_context,  # Save for future reference
                "cache_metrics": cache_metrics  # NEW: Include cache performance metrics
            })

            # ============= DEBUG LOGGING =============
            print(f"\n{'='*100}")
            print(f"[RESEARCH FLOW] ENRICHMENT COMPLETED for JD ID: {jd_id}")
            print(f"[RESEARCH FLOW] Summary:")
            print(f"  - total_discovered: {len(discovered_sorted)}")
            print(f"  - total_scored: {len(discovered_sorted)}")
            print(f"  - avg_score: {sum(c.get('relevance_score', 0) for c in discovered_sorted) / len(discovered_sorted):.1f}")
            print(f"  - companies_8_plus: {len([c for c in discovered_sorted if c.get('relevance_score', 0) >= 8])}")
            print(f"  - with_employees: {len([c for c in discovered_sorted if c.get('sample_employees')])}")
            print(f"[RESEARCH FLOW] Status: ENRICHED (ready for selection)")
            print(f"{'='*100}\n")
            # =========================================

            # Calculate score distribution for summary
            scores = [c.get('relevance_score', 0) for c in discovered_sorted]
            score_distribution = {
                "8_plus": len([s for s in scores if s >= 8]),
                "7_to_8": len([s for s in scores if 7 <= s < 8]),
                "6_to_7": len([s for s in scores if 6 <= s < 7]),
                "below_6": len([s for s in scores if s < 6])
            }

            # Determine scoring method for metadata
            scored_by = discovered_sorted[0].get('scored_by') if discovered_sorted else None

            return {
                "success": True,
                "session_id": jd_id,
                "status": "enriched",
                "discovered_companies": discovered_objects,  # ALL companies with scores, metadata, employees
                "evaluation_status": "scored",
                "metadata": {
                    "ai_scoring_enabled": not skip_ai_scoring,
                    "scored_by": scored_by,
                    "pipeline_phases": {
                        "discovery": True,
                        "ai_scoring": not skip_ai_scoring,
                        "employee_sampling": True
                    }
                },
                "summary": {
                    "total_discovered": len(discovered_sorted),
                    "total_scored": len(discovered_sorted),
                    "avg_relevance_score": sum(scores) / len(scores) if scores else 0,
                    "score_distribution": score_distribution,
                    "companies_with_employees": len([c for c in discovered_sorted if c.get('sample_employees')]),
                    "message": f"Discovered and enriched {len(discovered_sorted)} companies with relevance scores."
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

            for i, seed in enumerate(filtered_seeds[:5], 1):  # Reduced to 5 to prevent rate limit errors (was 15)
                if jd_id:
                    await self._update_session_status(jd_id, "running", {
                        "phase": "discovery",
                        "action": f"Searching competitors of {seed} ({i}/{min(len(filtered_seeds), 5)})..."
                    })
                competitors = await self.search_competitors_web(seed)
                companies.extend(competitors)

        # Method 2: Direct web search
        if self.config.USE_TAVILY and self.tavily_api_key:
            search_queries = self._generate_search_queries(jd_context)
            # Keep searching until we have 200+ unique companies OR run out of queries
            target_companies = 200
            unique_companies = set()

            for i, query in enumerate(search_queries, 1):
                # Check if we've hit our target
                if len(unique_companies) >= target_companies:
                    print(f"✓ Target reached: {len(unique_companies)} unique companies discovered!")
                    break

                # Extract source name for attribution
                source_name = self._extract_source_from_query(query)

                if jd_id:
                    await self._update_session_status(jd_id, "running", {
                        "phase": "discovery",
                        "action": f"Searching {source_name} ({i}/{len(search_queries)}): {len(unique_companies)} unique so far"
                    })

                web_results = await self._search_web(query)
                batch_companies = await self._extract_companies_from_web(web_results, query)

                # Track unique companies and add source attribution
                for company in batch_companies:
                    company_name = company.get("name", "").strip().lower()
                    if company_name and company_name not in unique_companies:
                        unique_companies.add(company_name)
                        # Add source attribution
                        company["discovered_via"] = source_name
                        company["search_query"] = query
                        companies.append(company)

                print(f"  Query {i} ({source_name}): Found {len(batch_companies)} companies, {len(unique_companies)} unique total")

            print(f"\n{'='*80}")
            print(f"DISCOVERY COMPLETE: {len(unique_companies)} unique companies from {i} queries")
            print(f"{'='*80}\n")

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
        enriched, cache_metrics = await self._enrich_companies(unique_companies[:100])

        # Final update with enriched company count
        if jd_id:
            enriched_names = [c.get('company_name') or c.get('name') for c in enriched if c.get('company_name') or c.get('name')]
            await self._update_session_status(jd_id, "running", {
                "phase": "discovery",
                "action": f"Discovery complete: {len(enriched)} companies ready for screening",
                "discovered_companies": enriched_names,
                "total_discovered": len(enriched)
            })

        return enriched, cache_metrics

    async def search_competitors_web(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Find competitor companies via web search with caching.

        Uses company-level cache to avoid redundant API calls across different JD searches.

        Args:
            company_name: Seed company to find competitors for

        Returns:
            List of competitor company dictionaries
        """
        if not self.config.USE_TAVILY or not self.tavily_api_key:
            return []

        # Import cache functions (only import when needed to avoid circular imports)
        from utils.supabase_storage import get_cached_competitors, save_cached_competitors

        # STEP 1: Check cache first
        cached_result = get_cached_competitors(company_name, freshness_days=7)
        if cached_result:
            # Cache hit - return cached competitors (saves 3 Claude API calls!)
            competitors = cached_result['discovered_companies'][:20]
            # Add source attribution to cached results (if not already present)
            for company in competitors:
                if "discovered_via" not in company:
                    company["discovered_via"] = f"Seed Expansion: {company_name} (cached)"
            return competitors

        # STEP 2: Cache miss - run fresh discovery
        queries = [
            f"{company_name} competitors",
            f"companies like {company_name}",
            f"{company_name} alternatives"
        ]

        competitors = []
        for query in queries:
            results = await self._search_web(query)
            companies = await self._extract_companies_from_web(results, query)
            # Add source attribution for seed expansion
            for company in companies:
                company["discovered_via"] = f"Seed Expansion: {company_name}"
                company["search_query"] = query
            competitors.extend(companies)
            await asyncio.sleep(0.2)  # Add delay to prevent rate limit bursts

        # STEP 3: Save to cache for future searches
        try:
            save_cached_competitors(company_name, competitors, queries)
        except Exception as e:
            print(f"   ⚠️  Failed to cache competitors: {e}")
            # Non-critical - continue even if cache save fails

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

    async def screen_companies_with_haiku(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any],
        jd_id: str
    ) -> None:
        """
        Screen each company with Claude Haiku using Anthropic API web search.
        Modifies companies in-place to add relevance_score.
        """
        import anthropic
        import json
        import re

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        for i, company in enumerate(companies, 1):
            company_name = company.get('name', 'Unknown')

            # Update progress
            await self._update_session_status(jd_id, "running", {
                "phase": "screening",
                "action": f"Company {i}/{len(companies)}: Researching {company_name}..."
            })

            # Build prompt
            must_have = jd_context.get('must_have', [])
            domain = jd_context.get('domain_expertise', [])
            industry = jd_context.get('industry_keywords', [])

            prompt = f"""Evaluate this company for finding candidates matching this job:

JOB REQUIREMENTS:
Role: {jd_context.get('role_title', 'N/A')}
Must-have: {', '.join(must_have[:3]) if must_have else 'N/A'}
Domain: {', '.join(domain) if domain else 'N/A'}
Industry: {', '.join(industry) if industry else 'N/A'}

COMPANY TO EVALUATE:
Name: {company_name}
{f"Industry: {company.get('industry')}" if company.get('industry') else ""}
{f"Size: {company.get('employee_count')} employees" if company.get('employee_count') else ""}
{f"Description: {company.get('description')}" if company.get('description') else ""}

TASK:
Use web search to learn:
- What products/services they build
- Their technology stack
- Whether they match the job's domain/industry

Rate 1-10 for finding matching candidates.
Return ONLY this JSON: {{"score": 8.5, "reasoning": "brief 1-sentence explanation"}}"""

            try:
                # Use Anthropic API with web search tool
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    tools=[{
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }],
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Extract response text
                response_text = ""
                for block in response.content:
                    if block.type == "text":
                        response_text += block.text

                # Parse JSON from response
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)

                data = None
                for json_str in json_matches:
                    try:
                        parsed = json.loads(json_str)
                        if 'score' in parsed and 'reasoning' in parsed:
                            data = parsed
                            break
                    except json.JSONDecodeError:
                        continue

                if not data:
                    raise ValueError(f"No valid JSON found in response. Text: {response_text[:200]}")

                company['relevance_score'] = float(data['score'])
                company['screening_reasoning'] = data['reasoning']
                company['scored_by'] = 'claude_haiku_with_websearch'

                print(f"  [{i}/{len(companies)}] {company_name}: {data['score']:.1f} - {data['reasoning'][:60]}...")

            except Exception as e:
                print(f"  [{i}/{len(companies)}] ✗ {company_name}: Error - {str(e)}")
                import traceback
                traceback.print_exc()
                company['relevance_score'] = 5.0
                company['screening_reasoning'] = f"Error during evaluation: {str(e)}"
                company['scored_by'] = 'error_fallback'

            # Rate limiting between companies
            await asyncio.sleep(1.5)

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
            # Skip companies marked as not relevant or with insufficient data
            if category in ["not_relevant", "insufficient_data"]:
                continue
            # Only add if category exists in our predefined categories
            if category in categorized:
                categorized[category].append(company)
            else:
                # Default to talent_pool for unknown categories
                print(f"⚠️  Unknown category '{category}' for company {company.get('name')}, defaulting to talent_pool")
                categorized["talent_pool"].append(company)

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

    def _extract_source_from_query(self, query: str) -> str:
        """
        Extract human-readable source name from search query.

        Examples:
        - "site:crunchbase.com voice ai" → "Crunchbase"
        - "site:ycombinator.com startups" → "Y Combinator"
        - "(site:g2.com OR site:capterra.com)" → "G2 & Capterra"
        """
        source_mapping = {
            "crunchbase.com": "Crunchbase",
            "ycombinator.com": "Y Combinator",
            "wellfound.com": "Wellfound (AngelList)",
            "g2.com": "G2",
            "capterra.com": "Capterra",
            "producthunt.com": "Product Hunt",
            "alternativeto.net": "AlternativeTo",
            "cbinsights.com": "CB Insights",
            "gartner.com": "Gartner",
            "forrester.com": "Forrester"
        }

        # Check for multi-source queries (e.g., "site:g2.com OR site:capterra.com")
        sources_found = []
        for domain, name in source_mapping.items():
            if domain in query:
                sources_found.append(name)

        if len(sources_found) > 1:
            return " & ".join(sources_found)
        elif len(sources_found) == 1:
            return sources_found[0]
        else:
            return "Web Search"

    def _extract_jd_signals(self, jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key signals from job description."""
        # Try both "domain" (from frontend) and "target_domain" (from JDParser)
        domain = jd_data.get("requirements", {}).get("domain") or \
                 jd_data.get("requirements", {}).get("target_domain", "")

        context = {
            "title": jd_data.get("title", ""),
            "company_stage": jd_data.get("company_stage", "unknown"),
            "industries": jd_data.get("industries", []),
            "seed_companies": jd_data.get("target_companies", {}).get("mentioned_companies", []),
            "excluded_companies": jd_data.get("target_companies", {}).get("excluded_companies", []),
            "key_skills": jd_data.get("requirements", {}).get("technical_skills", []),
            "domain_expertise": domain,
            "team_size_range": jd_data.get("team_size_range", [10, 1000])
        }

        # Add screening fields (if they exist in jd_data directly)
        if "role_title" in jd_data:
            context["role_title"] = jd_data["role_title"]
        if "must_have" in jd_data:
            context["must_have"] = jd_data["must_have"]
        if "industry_keywords" in jd_data:
            context["industry_keywords"] = jd_data["industry_keywords"]

        return context

    def _generate_search_queries(self, jd_context: Dict[str, Any]) -> List[str]:
        """
        Generate high-quality search queries for competitive intelligence.

        Strategy: Multi-source approach to discover 100+ companies
        Priority: Domain > Seed Companies > Industry > Stage
        Target: 10+ queries using ALL authoritative sources
        """
        queries = []

        domain = jd_context.get("domain_expertise", "")
        industry = jd_context.get("industries", [""])[0] if jd_context.get("industries") else ""
        seed_companies = jd_context.get("seed_companies", [])

        # Get ALL authoritative sources (use them all!)
        tier1_sources = self.config.AUTHORITATIVE_SOURCES.get("tier1_software", [])
        tier2_sources = self.config.AUTHORITATIVE_SOURCES.get("tier2_market_research", [])

        # Use domain or fallback to industry
        search_term = domain or industry

        if search_term:
            # QUERY SET 1: Tier 1 Software Sites (G2, Capterra, ProductHunt, AlternativeTo)
            # Use ALL tier1 sources (4 queries)
            for source in tier1_sources:
                queries.append(f"site:{source} \"{search_term}\" alternatives competitors")

            # QUERY SET 2: Tier 2 Market Research Sites (Gartner, Forrester, CB Insights, Crunchbase, YC, Wellfound)
            # Use ALL tier2 sources (6 queries)
            for source in tier2_sources:
                if "ycombinator" in source:
                    # YC-specific query
                    queries.append(f"site:{source} \"{search_term}\" companies startups batch")
                elif "crunchbase" in source:
                    # Crunchbase-specific query
                    queries.append(f"site:{source} \"{search_term}\" similar companies")
                else:
                    queries.append(f"site:{source} \"{search_term}\" companies 2024 2025")

            # QUERY SET 3: Multi-source combo queries (2-3 queries)
            # Combine best sources for broader coverage
            g2_capterra = f"(site:g2.com OR site:capterra.com) \"{search_term}\" alternatives"
            yc_crunchbase = f"(site:ycombinator.com OR site:crunchbase.com) \"{search_term}\" startups"
            queries.extend([g2_capterra, yc_crunchbase])

        # QUERY SET 4: Seed company expansion (if available)
        if seed_companies:
            for seed in seed_companies[:3]:  # Use top 3 seeds
                # YC + Crunchbase for "similar to X" queries
                queries.append(f"(site:ycombinator.com OR site:crunchbase.com) \"companies like {seed}\"")

        # FALLBACK: If no domain/industry, use generic queries
        if not queries:
            queries.extend([
                "site:ycombinator.com tech startups batch 2024",
                "site:crunchbase.com tech companies directory",
                "site:g2.com software companies 2024"
            ])

        # ============= DEBUG LOGGING =============
        print(f"\n{'='*100}")
        print(f"[SEARCH QUERIES] Generated {len(queries)} competitive intelligence queries:")
        for i, q in enumerate(queries[:15], 1):  # Show up to 15 queries
            print(f"  {i}. {q}")
        if len(queries) > 15:
            print(f"  ... and {len(queries) - 15} more queries")
        print(f"[SEARCH QUERIES] Input context:")
        print(f"  - domain: {domain}")
        print(f"  - industry: {industry}")
        print(f"  - seed_companies: {seed_companies[:3]}")
        print(f"[SEARCH QUERIES] Strategy: Multi-source approach using ALL {len(tier1_sources)} tier1 + {len(tier2_sources)} tier2 sources")
        print(f"[SEARCH QUERIES] Target: 100+ companies discovered")
        print(f"{'='*100}\n")
        # =========================================

        return queries[:15]  # Return up to 15 queries for maximum coverage

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

        prompt = f"""Extract actual companies from this web search with as much detail as possible.

TAVILY LLM ANSWER:
{llm_answer}

TOP SEARCH RESULTS:
{results_text}

TASK: Extract ONLY real companies mentioned in the content with rich details.

For each company, extract:
1. name: Company name (required)
2. description: Brief description of what they do (from content/answer)
3. website: Official website URL (from result URLs or mentioned in text)
4. industry: Industry category if mentioned (e.g., "AI/ML", "Fintech", "Healthcare")
5. employee_count_hint: Any size hints if mentioned (e.g., "50-200 employees", "startup", "large enterprise")

RULES:
- Include ONLY actual company names (e.g., "Stripe", "Square", "Adyen")
- EXCLUDE article titles (e.g., "The Best Stripe Alternatives")
- EXCLUDE generic words (e.g., "However", "Best", "Top", "Companies")
- EXCLUDE fragments or person names

Return a JSON array of company objects:
[
  {{
    "name": "Company1",
    "description": "Brief description of what they do",
    "website": "company1.com",
    "industry": "AI/ML",
    "employee_count_hint": "50-200 employees"
  }},
  ...
]

Include as many fields as you can extract. If a field is not available, omit it (don't use null).
If no clear companies are found, return an empty array: []"""

        try:
            # Retry logic for rate limit errors
            max_retries = 3
            retry_count = 0
            response = None

            while retry_count < max_retries:
                try:
                    response = self.claude_client.messages.create(
                        model=self.config.CLAUDE_MODEL,
                        max_tokens=1000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    break  # Success - exit retry loop

                except RateLimitError as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                        print(f"⚠️  Rate limit hit - retry {retry_count}/{max_retries} after {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ Rate limit exceeded after {max_retries} retries")
                        raise  # Give up - propagate error

            # Parse Claude's response
            response_text = response.content[0].text.strip()

            # Extract JSON array from response
            if response_text.startswith("["):
                company_data_list = json.loads(response_text)
            else:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    company_data_list = json.loads(json_match.group(0))
                else:
                    company_data_list = []

            # Convert to enriched company objects with source tracking
            companies = []
            for i, company_data in enumerate(company_data_list, 1):
                # Handle both old format (strings) and new format (objects)
                if isinstance(company_data, str):
                    # Old format: just a name
                    name = company_data
                    enriched_company = {"name": name}
                elif isinstance(company_data, dict):
                    # New format: object with details
                    name = company_data.get('name', '')
                    enriched_company = company_data.copy()
                else:
                    continue

                # Skip if name is invalid or already discovered
                if not name or len(name) <= 2 or name in self.discovered_companies:
                    continue

                # Add source tracking fields
                enriched_company.update({
                    "discovered_via": "web_search_llm",
                    "source_url": search_results[0].get("url") if search_results else None,
                    "source_query": search_query,
                    "source_result_rank": i
                })

                companies.append(enriched_company)
                self.discovered_companies.add(name)

            print(f"✓ Claude extracted {len(companies)} companies from Tavily results")
            # Log enrichment stats
            enriched_count = sum(1 for c in companies if 'description' in c)
            print(f"  {enriched_count}/{len(companies)} companies have descriptions")
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
        """
        Enrich companies with CoreSignal IDs using cache + lookup_with_fallback().

        NEW: Cache-first approach (saves 80%+ API search credits)
        For each discovered company:
        1. Check cache for existing CoreSignal ID (instant, 0 credits)
        2. If cache miss, execute 4-tier lookup:
           - Tier 1: Website exact match (90% success when available)
           - Tier 2: Name exact match with pagination (40-50%)
           - Tier 3: Fuzzy match (5-10%)
           - Tier 4: company_clean fallback (3-5%)
        3. Save result to cache (successful or failed)
        4. For failed searches, don't retry for 7 days

        Expected: 80-90% match rate, 80%+ cache hit rate (after warm-up)
        """
        from coresignal_company_lookup import CoreSignalCompanyLookup

        print(f"\n{'='*80}")
        print(f"🔍 Looking up CoreSignal company IDs for {len(companies)} companies...")
        print(f"{'='*80}\n")

        company_lookup = CoreSignalCompanyLookup()

        companies_with_ids = []
        companies_without_ids = []
        tier_stats = {1: 0, 2: 0, 3: 0, 4: 0}

        # Cache performance tracking
        cache_hits = 0
        cache_misses = 0
        cache_errors = 0

        for company in companies:
            company_name = company.get('name', company.get('company_name', ''))

            if not company_name:
                companies_without_ids.append(company)
                continue

            # Get website if available (from discovery)
            website = company.get('website')

            # ========================================
            # STEP 1: Check cache first
            # ========================================
            try:
                cached = await self.cache_service.get_cached_id(company_name)
            except Exception as e:
                print(f"   [CACHE ERROR] Failed to check cache for {company_name}: {e}")
                cached = None
                cache_errors += 1

            if cached and cached.get('coresignal_id'):
                # ✅ Cache HIT with valid ID
                cache_hits += 1
                company['coresignal_id'] = cached['coresignal_id']
                company['coresignal_confidence'] = cached.get('confidence', 1.0)
                company['coresignal_searchable'] = True
                company['lookup_tier'] = 'cache'  # Mark as from cache
                company['lookup_method'] = 'cache'
                company['cache_hit'] = True
                company['employee_count'] = cached.get('employee_count')

                # Track as cache hit in tier stats (don't count toward specific tiers)
                # Cached entries already found their tier when first discovered

                companies_with_ids.append(company)
                print(f"   ✅ [CACHE HIT] {company_name}: ID={cached['coresignal_id']} (confidence: {cached.get('confidence', '1.0')})")
                continue

            elif cached and not cached.get('lookup_successful'):
                # Cache HIT with failed search - check if retry is allowed
                cached_at_str = cached.get('created_at')  # Use created_at from actual schema
                if cached_at_str:
                    try:
                        cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
                        days_old = (datetime.now(timezone.utc) - cached_at).days

                        if days_old < 7:
                            # Skip - failed recently, don't retry yet
                            cache_hits += 1
                            company['coresignal_searchable'] = False
                            company['cache_hit'] = True
                            company['lookup_method'] = 'cache_failed'
                            companies_without_ids.append(company)
                            print(f"   ⊘ [CACHE HIT - FAILED] {company_name} (searched {days_old} days ago, skipping)")
                            continue
                        else:
                            print(f"   ↻ [CACHE STALE] {company_name} (searched {days_old} days ago, retrying)")
                    except Exception as e:
                        print(f"   [CACHE] Error parsing cached_at: {e}")

            # ========================================
            # STEP 2: Cache MISS - Execute 4-tier lookup
            # ========================================
            cache_misses += 1
            print(f"   ⊗ [CACHE MISS] {company_name} - executing 4-tier lookup...")

            match = company_lookup.lookup_with_fallback(
                company_name=company_name,
                website=website,
                confidence_threshold=0.75,
                use_company_clean_fallback=True
            )

            # ========================================
            # STEP 3: Save result to cache
            # ========================================
            if match:
                # Successful lookup
                company['coresignal_id'] = match['company_id']
                company['coresignal_confidence'] = match.get('confidence', 1.0)
                company['coresignal_searchable'] = True
                company['lookup_tier'] = match.get('tier', 0)
                company['lookup_method'] = match.get('lookup_method', 'unknown')
                company['cache_hit'] = False

                # Track tier statistics
                tier = match.get('tier', 0)
                if tier in tier_stats:
                    tier_stats[tier] += 1

                # Enrich with additional data from match
                if 'website' in match and not company.get('website'):
                    company['website'] = match['website']
                if 'employee_count' in match and match['employee_count']:
                    company['employee_count'] = match['employee_count']
                if 'industry' in match and match['industry'] and not company.get('industry'):
                    company['industry'] = match['industry']
                if 'size_range' in match and match['size_range']:
                    company['size_range'] = match['size_range']
                if 'founded' in match and match['founded']:
                    company['founded'] = match['founded']
                if 'location' in match and match['location']:
                    company['location'] = match['location']

                companies_with_ids.append(company)
                print(f"      ✅ Found: ID={match['company_id']} (tier {tier}, {match.get('lookup_method', 'unknown')})")

                # Save to cache
                try:
                    tier_name = {1: 'website', 2: 'name_exact', 3: 'fuzzy', 4: 'company_clean'}.get(tier, 'unknown')
                    await self.cache_service.save_to_cache(
                        company_name=company_name,
                        coresignal_id=match['company_id'],
                        lookup_tier=tier_name,
                        website=website,
                        metadata={
                            'confidence': match.get('confidence', 1.0),
                            'industry': company.get('industry'),
                            'employee_count': company.get('employee_count')
                        }
                    )
                except Exception as e:
                    print(f"      [CACHE] Error saving to cache: {e}")
                    cache_errors += 1
            else:
                # Failed lookup - save NULL to cache
                company['coresignal_searchable'] = False
                company['cache_hit'] = False
                companies_without_ids.append(company)
                print(f"      ❌ Not found: No CoreSignal ID")

                # Save failed search to cache (prevents retry for 7 days)
                try:
                    await self.cache_service.save_to_cache(
                        company_name=company_name,
                        coresignal_id=None,  # NULL indicates failed search
                        lookup_tier=None,
                        website=website,
                        metadata={'search_failed': True, 'failed_at': datetime.now(timezone.utc).isoformat()}
                    )
                    print(f"      [CACHE] Saved failed search (won't retry for 7 days)")
                except Exception as e:
                    print(f"      [CACHE] Error saving failed search: {e}")
                    cache_errors += 1

        # Calculate and log coverage + cache statistics
        total_companies = len(companies)
        coverage_percent = (len(companies_with_ids) / total_companies * 100) if total_companies else 0

        # Cache performance
        total_cache_ops = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        credits_saved = cache_hits  # Each cache hit = 1 search credit saved

        print(f"\n{'='*80}")
        print(f"📊 CoreSignal ID Lookup Results:")
        print(f"   Searchable (with IDs): {len(companies_with_ids)} companies ({coverage_percent:.1f}%)")
        print(f"   Not searchable (no IDs): {len(companies_without_ids)} companies")
        print(f"\n   Tier Breakdown:")
        print(f"      Tier 1 (Website): {tier_stats[1]} companies")
        print(f"      Tier 2 (Name Exact): {tier_stats[2]} companies")
        print(f"      Tier 3 (Fuzzy): {tier_stats[3]} companies")
        print(f"      Tier 4 (company_clean): {tier_stats[4]} companies")
        print(f"\n💾 Cache Performance:")
        print(f"   Cache Hits: {cache_hits} ({cache_hit_rate:.1f}% hit rate)")
        print(f"   Cache Misses: {cache_misses}")
        print(f"   Cache Errors: {cache_errors}")
        print(f"   💰 Credits Saved: {credits_saved} (~${credits_saved * 0.10:.2f} at $0.10/credit)")
        print(f"{'='*80}\n")

        # Store cache metrics for API response
        cache_metrics = {
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_errors": cache_errors,
            "cache_hit_rate": cache_hit_rate,
            "credits_saved": credits_saved,
            "estimated_cost_saved": credits_saved * 0.10
        }

        # Return ALL companies (with and without IDs) + cache metrics - "No Company Left Behind"
        return companies, cache_metrics

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

            # Use Claude Haiku with web search for screening (modifies in-place)
            await self.screen_companies_with_haiku(batch, jd_context, jd_id)

        # Sort by relevance_score (Haiku adds this field in-place)
        filtered_companies.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

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
        """Deep research on top candidates with TRUE web research and real data."""
        from company_deep_research import CompanyDeepResearch

        researcher = CompanyDeepResearch()

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
                    "action": f"Deep researching {company_name} ({i}/{total})...",
                    "current_company": company_name,
                    "total_evaluated": i
                })

            print(f"\n{'='*60}")
            print(f"DEEP RESEARCH: {company_name} ({i}/{total})")
            print('='*60)

            # Step 1: Deep web research with Claude Agent SDK
            web_research = await researcher.research_company(
                company_name=company_name,
                target_domain=jd_context.get("domain", ""),
                additional_context={
                    "industry": jd_context.get("industry"),
                    "location": company.get("location"),
                    "seed_companies": jd_context.get("seed_companies", [])[:3]
                }
            )

            # Step 2: Validate with CoreSignal (get company_id)
            company_id = await self._search_coresignal_company(company_name)

            # Step 3: Enrich with CoreSignal data if found
            coresignal_data = {}
            if company_id:
                print(f"✅ Found CoreSignal company_id: {company_id}")
                coresignal_data = await self._fetch_company_data(company_id)
            else:
                print(f"⚠️ No CoreSignal company_id found for {company_name}")

            # Step 4: Sample employees if we have company_id
            sample_employees = []
            if company_id:
                sample_employees = await self._sample_company_employees(
                    company_id,
                    company_name,
                    limit=5
                )
                if sample_employees:
                    print(f"👥 Found {len(sample_employees)} sample employees")

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
                "evaluation": evaluation,
                "research_quality": web_research.get("research_quality", 0),
                "deep_research_complete": True
            })

            print(f"📊 Evaluation: Score={evaluation.get('relevance_score', 0)}, "
                  f"Category={evaluation.get('category', 'unknown')}")
            print(f"📝 Research Quality: {web_research.get('research_quality', 0):.0%}")

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
                    "relevance_reasoning": company.get("screening_reasoning") or company.get("reasoning"),  # Try both field names
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

        CRITICAL FIX: Fetch existing search_config from database first to preserve all data
        during phase transitions (prevents data loss of discovered_companies_list).
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

            # CRITICAL FIX: Fetch existing search_config from database FIRST
            # This prevents overwriting existing data (especially discovered_companies_list)
            current_config = {}
            try:
                existing = self.supabase.table("company_research_sessions").select("search_config").eq(
                    "jd_id", jd_id
                ).execute()

                if existing.data and len(existing.data) > 0:
                    existing_config = existing.data[0].get("search_config")
                    if existing_config and isinstance(existing_config, dict):
                        # Start with existing config to preserve all previous data
                        current_config = existing_config.copy()
            except Exception as e:
                # If fetch fails, start with empty config (first-time session)
                print(f"⚠️  Could not fetch existing search_config: {e}")
                current_config = {}

            # Merge new fields into existing config (preserves all previous fields)
            if "phase" in metadata:
                current_config["current_phase"] = metadata["phase"]

            if "action" in metadata:
                current_config["current_action"] = metadata["action"]

            if "discovered_companies" in metadata:
                current_config["discovered_companies"] = metadata["discovered_companies"]

            if "discovered_companies_list" in metadata:
                current_config["discovered_companies_list"] = metadata["discovered_companies_list"]

            if "current_company" in metadata:
                current_config["current_company"] = metadata["current_company"]

            if "screened_companies" in metadata:
                current_config["screened_companies"] = metadata["screened_companies"]

            if "jd_context" in metadata:
                current_config["jd_context"] = metadata["jd_context"]

            # Only update search_config if we added any fields
            if current_config:
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

    # ==================== DEEP RESEARCH ENHANCEMENTS ====================
    # These methods add true deep research capabilities using web search and real data

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
            print(f"✅ Using cached data for company_id {company_id}")
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
                save_stored_company(
                    company_id,
                    company_data,
                    collected_at=time.time(),
                    collection_method="collect"
                )
                print(f"📦 Cached full company data for company_id {company_id}")

                # REVERSE ENRICHMENT: Also cache name→ID mapping
                company_name = company_data.get('name')
                if company_name:
                    try:
                        await self.cache_service.save_to_cache(
                            company_name=company_name,
                            coresignal_id=company_id,
                            lookup_tier='collect_reverse',
                            website=company_data.get('website'),
                            metadata={
                                'confidence': 1.0,  # 100% confidence - from official API
                                'employee_count': company_data.get('employees_count') or company_data.get('employee_count'),
                                'industry': company_data.get('industry')
                            }
                        )
                        print(f"   💾 BONUS: Cached name→ID mapping: '{company_name}' → {company_id}")
                    except Exception as e:
                        print(f"   [CACHE] Error saving reverse mapping: {e}")

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
            }
            # NOTE: preview endpoint does NOT accept "size" parameter
        }

        url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

        try:
            import requests
            response = requests.post(url, json=query, headers=headers, timeout=10)

            if response.status_code == 200:
                employees = response.json()

                # Extract key info and limit to desired size
                return [
                    {
                        "id": emp.get("id"),
                        "name": emp.get("full_name"),
                        "title": emp.get("job_title") or emp.get("title") or (emp.get("headline", "").split(" at ")[0] if emp.get("headline") else "N/A"),
                        "headline": emp.get("headline"),
                        "location": emp.get("location_raw_address") or emp.get("location")
                    }
                    for emp in employees[:limit]  # Limit to first N employees
                ]
        except Exception as e:
            print(f"Employee search error: {e}")

        return []

    async def _add_sample_employees_to_companies(
        self,
        companies: List[Dict[str, Any]],
        jd_context: Dict[str, Any],
        jd_id: Optional[str] = None,
        limit_per_company: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Add sample employees to each company using employee_clean preview.

        Args:
            companies: List of company dictionaries
            jd_context: Job description context for role filtering
            jd_id: Optional session ID for progress updates
            limit_per_company: Number of employees to fetch per company

        Returns:
            Updated companies list with sample_employees field
        """
        headers = {
            "accept": "application/json",
            "apikey": self.coresignal_api_key,
            "Content-Type": "application/json"
        }

        # Extract target role from JD context for filtering
        # Prioritize role_title (specific role) over title (which may include company)
        target_role = (jd_context.get("role_title") or jd_context.get("title", "")).lower()
        role_keywords = ["engineer", "manager", "director", "developer", "scientist", "analyst"]

        # Determine if we should filter by role
        filter_by_role = any(keyword in target_role for keyword in role_keywords)

        import requests

        for i, company in enumerate(companies, 1):
            company_name = company.get("name") or company.get("company_name")
            coresignal_id = company.get("coresignal_id") or company.get("coresignal_company_id")

            if not company_name:
                continue

            # Update progress
            if jd_id and i % 10 == 0:
                await self._update_session_status(jd_id, "running", {
                    "phase": "employee_sampling",
                    "action": f"Fetching employees... {i}/{len(companies)} companies"
                })

            try:
                # Build query with role filtering
                if coresignal_id:
                    # Use company ID for precise matching + role filtering
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "nested": {
                                            "path": "experience",
                                            "query": {
                                                "term": {
                                                    "experience.company_id": coresignal_id
                                                }
                                            }
                                        }
                                    }
                                ],
                                "should": [
                                    {
                                        "match": {
                                            "job_title": target_role  # FIXED: use job_title (the actual field name)
                                        }
                                    }
                                ] if filter_by_role else []
                            }
                        }
                        # NOTE: preview endpoint does NOT accept "size" parameter
                    }
                else:
                    # Fallback to company name matching + role filtering
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "nested": {
                                            "path": "experience",
                                            "query": {
                                                "match": {
                                                    "experience.company_name": company_name
                                                }
                                            }
                                        }
                                    }
                                ],
                                "should": [
                                    {
                                        "match": {
                                            "job_title": target_role  # FIXED: use job_title (the actual field name)
                                        }
                                    }
                                ] if filter_by_role else []
                            }
                        }
                        # NOTE: preview endpoint does NOT accept "size" parameter
                    }

                url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page=1"

                response = requests.post(url, json=query, headers=headers, timeout=10)

                if response.status_code == 200:
                    employees = response.json()

                    # Extract key info and add to company
                    # Preview endpoint returns list directly (not {"employees": [...]})
                    # Also note: the preview endpoint returns fixed ~20 results
                    company['sample_employees'] = [
                        {
                            "id": emp.get("id"),
                            "name": emp.get("full_name") or emp.get("name"),  # preview uses full_name
                            "title": emp.get("job_title") or emp.get("title") or (emp.get("headline", "").split(" at ")[0] if emp.get("headline") else "N/A"),
                            "headline": emp.get("headline"),
                            "location": emp.get("location_raw_address") or emp.get("location")
                        }
                        for emp in employees[:limit_per_company]  # Limit to first N employees
                    ]

                    if len(company['sample_employees']) > 0:
                        print(f"  ✓ {company_name}: {len(company['sample_employees'])} employees")
                else:
                    company['sample_employees'] = []
                    print(f"  ✗ {company_name}: Failed (status {response.status_code})")

            except Exception as e:
                company['sample_employees'] = []
                print(f"  ✗ {company_name}: Error - {str(e)[:50]}")

            # Rate limiting: brief pause between requests
            await asyncio.sleep(0.1)

        return companies

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
        import json

        # Build comprehensive context
        company_context = {
            "name": company_name,
            "web_research": {
                "website": web_research.get("website"),
                "description": web_research.get("description"),
                "products": web_research.get("products"),
                "funding": web_research.get("funding"),
                "recent_news": web_research.get("recent_news"),
                "technology_stack": web_research.get("technology_stack"),
                "key_customers": web_research.get("key_customers"),
                "competitive_position": web_research.get("competitive_position")
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
            try:
                response = await self.gpt5_client.async_client.chat.completions.create(
                    model=self.gpt5_client.get_research_model(),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"GPT-5 evaluation error: {e}")
                # Fall back to Claude

        # Fall back to Claude Sonnet 4.5 (current model as of Nov 2025)
        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # FIXED: Was using old 3.5 model
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
        except Exception as e:
            print(f"Claude evaluation error: {e}")

        return {
            "relevance_score": 5.0,
            "category": "unknown",
            "reasoning": "Evaluation failed"
        }
