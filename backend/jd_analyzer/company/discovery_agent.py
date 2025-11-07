"""
Company Discovery Agent

Discovers companies using Tavily web search based on:
1. Mentioned companies (seed expansion)
2. Target domain (industry-based discovery)
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from tavily import TavilyClient


class CompanyDiscoveryAgent:
    """
    Agent for discovering companies via web search.

    Uses Tavily API to:
    - Find competitors of seed companies
    - Discover top companies in a domain
    - Expand from mentioned companies
    """

    def __init__(self, tavily_api_key: Optional[str] = None):
        """
        Initialize Company Discovery Agent.

        Args:
            tavily_api_key: Optional API key, defaults to env var
        """
        api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")

        self.client = TavilyClient(api_key=api_key)

    async def discover_from_seed(self, company_name: str, max_results: int = 10) -> List[str]:
        """
        Find companies similar to a seed company using web search.

        Args:
            company_name: Seed company name
            max_results: Maximum number of companies to return

        Returns:
            List of company names discovered via "companies like X" search
        """
        query = f"companies like {company_name} competitors alternatives"

        print(f"[DISCOVERY AGENT] Searching for companies like '{company_name}'...")

        try:
            # Tavily search
            results = self.client.search(query, max_results=max_results)

            # Extract company names from search results
            companies = self._extract_companies_from_results(results, company_name)

            print(f"[DISCOVERY AGENT] Found {len(companies)} companies via seed expansion from '{company_name}'")
            return companies

        except Exception as e:
            print(f"[DISCOVERY AGENT] Error searching for companies like '{company_name}': {e}")
            return []

    async def discover_from_domain(self, target_domain: str, context: str = "", max_results: int = 15) -> List[str]:
        """
        Find top companies in a domain using web search.

        Args:
            target_domain: Primary industry/domain (e.g., "voice ai", "fintech")
            context: Additional context keywords (e.g., "speech recognition, TTS")
            max_results: Maximum number of companies to return

        Returns:
            List of company names discovered via domain search
        """
        # Build search query with domain + context
        if context:
            query = f"{target_domain} companies {context}"
        else:
            query = f"{target_domain} companies directory list"

        print(f"[DISCOVERY AGENT] Searching for companies in domain '{target_domain}'...")

        try:
            # Tavily search
            results = self.client.search(query, max_results=max_results)

            # Extract company names from search results
            companies = self._extract_companies_from_results(results, target_domain)

            print(f"[DISCOVERY AGENT] Found {len(companies)} companies via domain search for '{target_domain}'")
            return companies

        except Exception as e:
            print(f"[DISCOVERY AGENT] Error searching for '{target_domain}' companies: {e}")
            return []

    async def discover_companies(
        self,
        mentioned_companies: List[str],
        target_domain: Optional[str] = None,
        context: Optional[str] = None,
        max_per_seed: int = 8,
        max_from_domain: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Orchestrate full company discovery pipeline.

        Args:
            mentioned_companies: Companies explicitly mentioned in JD
            target_domain: Primary industry/domain for discovery
            context: Industry context keywords
            max_per_seed: Max companies to discover per seed company
            max_from_domain: Max companies to discover from domain search

        Returns:
            List of discovered companies with metadata:
            [
                {"name": "Company Name", "source": "seed|domain", "confidence": 0.9},
                ...
            ]
        """
        discovered = []
        discovered_names = set()  # For deduplication

        print(f"\n{'='*100}")
        print(f"[DISCOVERY AGENT] Starting company discovery pipeline")
        print(f"[DISCOVERY AGENT] Input:")
        print(f"  - mentioned_companies: {mentioned_companies}")
        print(f"  - target_domain: {target_domain}")
        print(f"  - context: {context}")
        print(f"{'='*100}\n")

        # Step 1: Add mentioned companies (highest confidence)
        for company in mentioned_companies:
            if company and company not in discovered_names:
                discovered.append({
                    "name": company,
                    "source": "mentioned",
                    "confidence": 1.0
                })
                discovered_names.add(company)

        # Step 2: Seed expansion (find competitors of mentioned companies)
        for seed_company in mentioned_companies[:3]:  # Limit to first 3 to avoid too many API calls
            if not seed_company:
                continue

            seed_companies = await self.discover_from_seed(seed_company, max_per_seed)

            for company in seed_companies:
                if company and company not in discovered_names:
                    discovered.append({
                        "name": company,
                        "source": "seed_expansion",
                        "confidence": 0.8
                    })
                    discovered_names.add(company)

        # Step 3: Domain discovery (find companies in the industry)
        if target_domain:
            domain_companies = await self.discover_from_domain(target_domain, context or "", max_from_domain)

            for company in domain_companies:
                if company and company not in discovered_names:
                    discovered.append({
                        "name": company,
                        "source": "domain_discovery",
                        "confidence": 0.7
                    })
                    discovered_names.add(company)

        print(f"\n{'='*100}")
        print(f"[DISCOVERY AGENT] Discovery pipeline complete")
        print(f"[DISCOVERY AGENT] Total discovered: {len(discovered)} companies")
        print(f"  - From mentioned: {len([c for c in discovered if c['source'] == 'mentioned'])}")
        print(f"  - From seed expansion: {len([c for c in discovered if c['source'] == 'seed_expansion'])}")
        print(f"  - From domain discovery: {len([c for c in discovered if c['source'] == 'domain_discovery'])}")
        print(f"{'='*100}\n")

        return discovered

    def _extract_companies_from_results(self, results: Dict[str, Any], context: str) -> List[str]:
        """
        Extract company names from Tavily search results.

        Args:
            results: Tavily API response
            context: Search context (seed company or domain)

        Returns:
            List of company names extracted from search results
        """
        companies = []

        # Get results array
        search_results = results.get("results", [])

        for result in search_results:
            content = result.get("content", "")
            title = result.get("title", "")
            url = result.get("url", "")

            # Extract company names from content/title
            # This is a simple extraction - can be enhanced with NER/LLM in the future
            extracted = self._simple_company_extraction(content + " " + title, context)
            companies.extend(extracted)

        # Deduplicate and clean
        companies = list(set(companies))
        companies = [c for c in companies if len(c) > 2 and len(c) < 50]  # Filter out junk

        return companies[:20]  # Limit to top 20

    def _simple_company_extraction(self, text: str, context: str) -> List[str]:
        """
        Simple heuristic-based company name extraction.

        NOTE: This is a basic implementation. In production, this could be
        enhanced with:
        - Named Entity Recognition (NER)
        - LLM-based extraction (Claude Haiku for speed)
        - Pattern matching with known company name formats

        Args:
            text: Text to extract from
            context: Search context

        Returns:
            List of extracted company names
        """
        import re

        companies = []

        # Pattern 1: Capitalized words including multi-word names (likely company names)
        # Example: "Deepgram", "AssemblyAI", "Otter.ai", "Hugging Face", "Red Hat", "JPMorgan Chase", "Meta AI"
        # Updated to capture:
        # - Multi-word names with spaces: "Hugging Face"
        # - Mixed-case compounds: "JPMorgan", "LinkedIn"
        # - All-caps acronyms: "IBM", "AI"
        pattern1 = r'\b([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*(?:\.ai|\.com|\.io)?)\b'
        matches1 = re.findall(pattern1, text)
        companies.extend(matches1)

        # Pattern 2: After "like", "including", "such as"
        # Example: "companies like Deepgram, AssemblyAI, Hugging Face"
        # Updated to handle multi-word company names correctly
        pattern2 = r'(?:like|including|such as)\s+([A-Z][a-zA-Z\s,&]+?)(?:\.|\s+and\s+[A-Z]|$)'
        matches2 = re.findall(pattern2, text)
        for match in matches2:
            # Split by comma only (not " and ") to preserve multi-word names
            # "Hugging Face, Red Hat" → ["Hugging Face", "Red Hat"] ✓
            parts = [p.strip() for p in match.split(',')]
            companies.extend([p for p in parts if len(p) > 2 and p not in ['and', 'or', 'the']])

        # Pattern 3: Before ".com", ".ai", ".io" (domain names)
        pattern3 = r'([A-Z][a-zA-Z]+?)(?:\.com|\.ai|\.io)'
        matches3 = re.findall(pattern3, text)
        companies.extend(matches3)

        # Clean up and filter out common English words
        companies = [c.strip() for c in companies if c.strip()]

        # Expanded list of common words to exclude
        common_words = [
            'The', 'A', 'An', 'And', 'Or', 'But', 'For', 'At', 'By', 'In', 'On', 'To', 'Of',
            'We', 'Our', 'They', 'This', 'That', 'These', 'Those', 'As', 'Is', 'Are', 'Was', 'Were',
            'Experience', 'Candidates', 'Companies', 'Engineers', 'Work', 'Team', 'Role', 'Position',
            'Looking', 'Seeking', 'Need', 'Want', 'Must', 'Should', 'Will', 'Can', 'May',
            'About', 'What', 'Who', 'When', 'Where', 'Why', 'How', 'Which', 'While', 'Since',
            'All', 'Both', 'Each', 'Every', 'Some', 'Any', 'Many', 'Much', 'Few', 'Several',
            'Have', 'Has', 'Had', 'Do', 'Does', 'Did', 'With', 'From', 'Into', 'During', 'Before',
            'After', 'Above', 'Below', 'Between', 'Through', 'During', 'Before', 'After'
        ]

        companies = [c for c in companies if c not in common_words]

        return companies
