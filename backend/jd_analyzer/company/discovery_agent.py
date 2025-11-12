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

    async def discover_from_seed(self, company_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find companies similar to a seed company using web search.

        Args:
            company_name: Seed company name
            max_results: Maximum number of companies to return

        Returns:
            List of company dictionaries with 'name' and optional 'website':
            [{"name": "Deepgram", "website": "https://deepgram.com"}, ...]
        """
        query = f"companies like {company_name} competitors alternatives"

        print(f"[DISCOVERY AGENT] Searching for companies like '{company_name}'...")

        try:
            # Tavily search
            results = self.client.search(query, max_results=max_results)

            # Extract company data from search results
            companies = self._extract_companies_from_results(results, company_name)

            print(f"[DISCOVERY AGENT] Found {len(companies)} companies via seed expansion from '{company_name}'")
            return companies

        except Exception as e:
            print(f"[DISCOVERY AGENT] Error searching for companies like '{company_name}': {e}")
            return []

    async def discover_from_domain(self, target_domain: str, context: str = "", max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Find top companies in a domain using web search.

        Args:
            target_domain: Primary industry/domain (e.g., "voice ai", "fintech")
            context: Additional context keywords (e.g., "speech recognition, TTS")
            max_results: Maximum number of companies to return

        Returns:
            List of company dictionaries with 'name' and optional 'website':
            [{"name": "Deepgram", "website": "https://deepgram.com"}, ...]
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

            # Extract company data from search results
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
        max_from_domain: int = 15,
        use_ai_validation: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Orchestrate full company discovery pipeline.

        Args:
            mentioned_companies: Companies explicitly mentioned in JD
            target_domain: Primary industry/domain for discovery
            context: Industry context keywords
            max_per_seed: Max companies to discover per seed company
            max_from_domain: Max companies to discover from domain search
            use_ai_validation: If True, uses Claude to validate company names (slower but more accurate)

        Returns:
            List of discovered companies with metadata:
            [
                {"name": "Company Name", "source": "seed|domain", "confidence": 0.9, "website": "...", ...},
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
        # Do quick search to extract websites for mentioned companies
        for company in mentioned_companies:
            if company and company not in discovered_names:
                # Try to find website via quick Tavily search
                website = None
                try:
                    query = f"{company} official website"
                    search_result = self.client.search(query, max_results=1)
                    if search_result and search_result.get('results'):
                        first_result = search_result['results'][0]
                        url = first_result.get('url', '')
                        # Extract clean domain
                        website = self._extract_website_from_url(url) if url else None
                except Exception as e:
                    print(f"[DISCOVERY AGENT] Could not fetch website for {company}: {e}")
                    website = None

                discovered.append({
                    "name": company,
                    "website": website,
                    "source": "mentioned",
                    "confidence": 1.0
                })
                discovered_names.add(company)

        # Step 2: Seed expansion (find competitors of mentioned companies)
        for seed_company in mentioned_companies[:3]:  # Limit to first 3 to avoid too many API calls
            if not seed_company:
                continue

            seed_companies = await self.discover_from_seed(seed_company, max_per_seed)

            for company_data in seed_companies:
                company_name = company_data.get('name') if isinstance(company_data, dict) else company_data
                if company_name and company_name not in discovered_names:
                    discovered.append({
                        "name": company_name,
                        "website": company_data.get('website') if isinstance(company_data, dict) else None,
                        "source": "seed_expansion",
                        "confidence": 0.8
                    })
                    discovered_names.add(company_name)

        # Step 3: Domain discovery (find companies in the industry)
        if target_domain:
            domain_companies = await self.discover_from_domain(target_domain, context or "", max_from_domain)

            for company_data in domain_companies:
                company_name = company_data.get('name') if isinstance(company_data, dict) else company_data
                if company_name and company_name not in discovered_names:
                    discovered.append({
                        "name": company_name,
                        "website": company_data.get('website') if isinstance(company_data, dict) else None,
                        "source": "domain_discovery",
                        "confidence": 0.7
                    })
                    discovered_names.add(company_name)

        print(f"\n{'='*100}")
        print(f"[DISCOVERY AGENT] Discovery pipeline complete")
        print(f"[DISCOVERY AGENT] Total discovered: {len(discovered)} companies")
        print(f"  - From mentioned: {len([c for c in discovered if c['source'] == 'mentioned'])}")
        print(f"  - From seed expansion: {len([c for c in discovered if c['source'] == 'seed_expansion'])}")
        print(f"  - From domain discovery: {len([c for c in discovered if c['source'] == 'domain_discovery'])}")
        print(f"{'='*100}\n")

        # Optional: AI validation to filter junk company names
        if use_ai_validation and discovered:
            print(f"\n[DISCOVERY AGENT] AI Validation enabled - filtering companies...")

            from .company_validation_agent import CompanyValidationAgent
            validation_agent = CompanyValidationAgent()

            # Skip validation for mentioned companies (user explicitly provided them)
            mentioned_set = set(mentioned_companies)
            to_validate = [c for c in discovered if c['name'] not in mentioned_set]
            keep_without_validation = [c for c in discovered if c['name'] in mentioned_set]

            if to_validate:
                # Extract just names for validation
                names_to_validate = [c['name'] for c in to_validate]

                # Batch validate
                validated_results = await validation_agent.batch_validate(
                    company_names=names_to_validate,
                    target_domain=target_domain,
                    max_concurrent=5
                )

                # Create dict for quick lookup
                validated_names = {v['company_name']: v for v in validated_results}

                # Enrich discovered companies with validation data
                validated_companies = []
                for company in to_validate:
                    company_name = company['name']
                    if company_name in validated_names:
                        validation_data = validated_names[company_name]
                        # Enrich with validation data
                        company['validated'] = True
                        company['relevance_to_domain'] = validation_data.get('relevance_to_domain', 'unknown')
                        if not company.get('website') and validation_data.get('website'):
                            company['website'] = validation_data.get('website')
                        company['description'] = validation_data.get('description')
                        validated_companies.append(company)

                # Combine mentioned companies (kept) + validated companies
                discovered = keep_without_validation + validated_companies

                print(f"[DISCOVERY AGENT] AI Validation complete:")
                print(f"  - Validated: {len(validated_companies)}/{len(to_validate)}")
                print(f"  - Kept (mentioned): {len(keep_without_validation)}")
                print(f"  - Total after validation: {len(discovered)}")

        return discovered

    def _extract_companies_from_results(self, results: Dict[str, Any], context: str) -> List[Dict[str, Any]]:
        """
        Extract company names and websites from Tavily search results.

        Args:
            results: Tavily API response
            context: Search context (seed company or domain)

        Returns:
            List of company dictionaries with 'name' and optional 'website':
            [
                {"name": "Deepgram", "website": "https://deepgram.com"},
                {"name": "AssemblyAI", "website": "https://assemblyai.com"},
                ...
            ]
        """
        companies = {}  # Use dict to deduplicate by name

        # Get results array
        search_results = results.get("results", [])

        for result in search_results:
            content = result.get("content", "")
            title = result.get("title", "")
            url = result.get("url", "")

            # Extract website from URL (only if it's a direct company website)
            website = self._extract_website_from_url(url)

            # Extract company names from content/title
            extracted_names = self._simple_company_extraction(content + " " + title, context)

            for company_name in extracted_names:
                if company_name not in companies:
                    # Only assign website if:
                    # 1. We extracted a website from this result's URL
                    # 2. The company name appears in the URL or title (indicates it's their website)
                    company_website = None
                    if website:
                        name_lower = company_name.lower().replace(' ', '').replace('.', '')
                        url_lower = url.lower().replace(' ', '').replace('.', '')
                        title_lower = title.lower()

                        # Check if company name is in URL or title
                        if name_lower in url_lower or company_name.lower() in title_lower:
                            company_website = website

                    companies[company_name] = {
                        "name": company_name,
                        "website": company_website
                    }

        # Convert to list and apply filters
        companies_list = list(companies.values())

        # Filter by name length
        companies_list = [c for c in companies_list if len(c['name']) > 2 and len(c['name']) < 50]

        # Apply heuristic filter to remove obvious junk
        companies_list = [c for c in companies_list if self._is_likely_company_name(c['name'])]

        return companies_list[:20]  # Limit to top 20

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
            'After', 'Above', 'Below', 'Between', 'Through', 'During', 'Before', 'After',
            # Tech/generic terms often mis-extracted
            'API', 'APIs', 'ASR', 'IVR', 'TTS', 'NLP', 'AI', 'ML', 'Tech', 'Platform', 'Service', 'Services',
            'Software', 'Hardware', 'Cloud', 'Enterprise', 'Solutions', 'System', 'Systems', 'Tool', 'Tools',
            'Voice', 'Speech', 'Text', 'Audio', 'Video', 'Data', 'Analytics', 'Intelligence',
            # Action words
            'Find', 'Search', 'Get', 'Make', 'Build', 'Create', 'Use', 'Try', 'Start', 'Stop',
            'Top', 'Best', 'New', 'Old', 'Good', 'Bad', 'High', 'Low', 'Fast', 'Slow',
            # Misc
            'Alternatives', 'Competitors', 'Similar', 'Like', 'Its', 'Didn', 'Reddit'
        ]

        companies = [c for c in companies if c not in common_words]

        return companies

    def _is_likely_company_name(self, name: str) -> bool:
        """
        Heuristic filter to identify likely valid company names.

        This filters out obvious junk BEFORE expensive AI validation.

        Rules:
        - Must be 2+ characters
        - Must contain at least one letter
        - If single word, must be capitalized or have numbers/special chars
        - Multi-word names are more likely to be real companies

        Args:
            name: Company name to evaluate

        Returns:
            True if likely a real company name
        """
        if not name or len(name) < 2:
            return False

        # Must contain at least one letter
        if not any(c.isalpha() for c in name):
            return False

        # Multi-word names are usually real (e.g., "Hugging Face", "Red Hat")
        word_count = len(name.split())
        if word_count >= 2:
            return True

        # Single word checks
        # - Must start with capital letter
        # - Or contain numbers (e.g., "11x")
        # - Or end with .ai, .com, .io (e.g., "Otter.ai")
        if word_count == 1:
            if not name[0].isupper():
                return False

            # Allow if contains numbers or domain extension
            has_numbers = any(c.isdigit() for c in name)
            has_domain_ext = name.endswith(('.ai', '.com', '.io', '.co'))

            return has_numbers or has_domain_ext or len(name) >= 4

        return True

    def _get_root_domain(self, domain: str) -> str:
        """
        Extract root domain from subdomain.

        Examples:
            console.deepgram.com → deepgram.com
            api.assemblyai.com → assemblyai.com
            www.google.com → google.com

        Args:
            domain: Full domain (may include subdomain)

        Returns:
            Root domain (last 2 parts)
        """
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Split by dots
        parts = domain.split('.')

        # If more than 2 parts (e.g., console.deepgram.com), take last 2
        if len(parts) > 2:
            return '.'.join(parts[-2:])

        return domain

    def _extract_website_from_url(self, url: str) -> Optional[str]:
        """
        Extract company website from Tavily result URL.

        Handles special cases:
        - Crunchbase URLs: crunchbase.com/organization/deepgram → deepgram.com
        - Direct company websites: deepgram.com/about → deepgram.com
        - LinkedIn company pages: linkedin.com/company/deepgram → None (not useful)
        - News/blog sites: techcrunch.com/... → None (not useful)

        Args:
            url: URL from Tavily search result

        Returns:
            Company website URL or None if not a company website
        """
        if not url:
            return None

        import re
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Filter out non-company domains
            excluded_domains = [
                'linkedin.com', 'crunchbase.com', 'techcrunch.com', 'forbes.com',
                'bloomberg.com', 'reuters.com', 'wsj.com', 'nytimes.com',
                'twitter.com', 'facebook.com', 'youtube.com', 'reddit.com',
                'indeed.com', 'glassdoor.com', 'angel.co', 'wellfound.com',
                'g2.com', 'capterra.com', 'ycombinator.com', 'gartner.com',
                'wikipedia.org', 'google.com', 'bing.com'
            ]

            # Check if domain is excluded
            if any(excluded in domain for excluded in excluded_domains):
                # Special case: Extract from Crunchbase organization URLs
                if 'crunchbase.com' in domain:
                    match = re.search(r'/organization/([^/]+)', url)
                    if match:
                        org_slug = match.group(1)
                        # Convert slug to website guess (not always accurate but worth trying)
                        # Example: "deepgram" → "deepgram.com"
                        return f"https://{org_slug}.com"

                return None

            # Return the root domain (console.deepgram.com → deepgram.com)
            domain = domain.replace('www.', '')
            root_domain = self._get_root_domain(domain)
            return f"https://{root_domain}"

        except Exception as e:
            print(f"[DISCOVERY AGENT] Error extracting website from URL '{url}': {e}")
            return None
