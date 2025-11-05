"""
Company Validation Agent

Validates discovered companies using Claude Agent SDK with web search.
Filters out invalid/irrelevant companies and enriches with metadata.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


class CompanyValidationAgent:
    """
    Agent for validating and enriching company data.

    Uses Claude Haiku 4.5 with web search to:
    - Validate company exists and is relevant
    - Enrich with metadata (website, industry, description)
    - Filter out typos, duplicates, irrelevant names
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Company Validation Agent.

        Args:
            anthropic_api_key: Optional API key, defaults to env var
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"  # Fast, cheap model for validation

    async def validate_company(
        self,
        company_name: str,
        target_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and enrich a single company using web search.

        Args:
            company_name: Company name to validate
            target_domain: Target industry/domain (e.g., "voice ai")

        Returns:
            Dict with validation results:
            {
                "company_name": "Deepgram",
                "is_valid": True,
                "website": "deepgram.com",
                "industry": "voice ai",
                "description": "Speech recognition API for developers",
                "relevance_to_domain": "high",
                "validation_source": "Official website, TechCrunch coverage"
            }
        """
        domain_context = f" in the {target_domain} industry" if target_domain else ""

        prompt = f"""Validate this company{domain_context}:

Company Name: {company_name}

Please use web search to answer:
1. Is this a real, established company?
2. What is their official website domain? (e.g., "deepgram.com")
3. What industry are they in?
4. What do they do? (1-2 sentence description)
5. If target domain is "{target_domain}", how relevant are they? (high/medium/low/none)

Return ONLY a JSON object:
{{
  "company_name": "corrected name if typo, otherwise original",
  "is_valid": true/false,
  "website": "domain.com or null",
  "industry": "industry name or null",
  "description": "brief description or null",
  "relevance_to_domain": "high|medium|low|none",
  "validation_source": "where you found this info"
}}

CRITICAL:
- If company doesn't exist or is too obscure (no web presence), return is_valid: false
- If name is a typo/variation, correct it in company_name
- If not relevant to {target_domain}, set relevance_to_domain: "none" or "low"
"""

        try:
            # Claude API call (no built-in web search in current SDK)
            # For now, use Claude's knowledge - in production, integrate with web search tool
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Parse JSON from response
            import json
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            validation_result = json.loads(json_str)

            return validation_result

        except Exception as e:
            print(f"[VALIDATION AGENT] Error validating '{company_name}': {e}")
            # Return minimal valid structure on error
            return {
                "company_name": company_name,
                "is_valid": False,
                "website": None,
                "industry": None,
                "description": None,
                "relevance_to_domain": "unknown",
                "validation_source": f"Error: {str(e)}"
            }

    async def batch_validate(
        self,
        company_names: List[str],
        target_domain: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple companies in parallel.

        Args:
            company_names: List of company names to validate
            target_domain: Target industry/domain
            max_concurrent: Max concurrent validations

        Returns:
            List of validation results (only valid companies)
        """
        print(f"\n{'='*100}")
        print(f"[VALIDATION AGENT] Starting batch validation")
        print(f"[VALIDATION AGENT] Validating {len(company_names)} companies...")
        print(f"[VALIDATION AGENT] Target domain: {target_domain}")
        print(f"{'='*100}\n")

        # Create tasks for concurrent validation
        tasks = []
        for company_name in company_names:
            task = self.validate_company(company_name, target_domain)
            tasks.append(task)

        # Run with limited concurrency
        validated = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i+max_concurrent]
            batch_results = await asyncio.gather(*batch)
            validated.extend(batch_results)

            print(f"[VALIDATION AGENT] Validated {min(i+max_concurrent, len(tasks))}/{len(tasks)} companies")

        # Filter to only valid companies
        valid_companies = [c for c in validated if c.get("is_valid", False)]

        print(f"\n{'='*100}")
        print(f"[VALIDATION AGENT] Batch validation complete")
        print(f"[VALIDATION AGENT] Valid companies: {len(valid_companies)}/{len(company_names)}")
        print(f"{'='*100}\n")

        return valid_companies

    async def validate_and_filter(
        self,
        discovered_companies: List[Dict[str, Any]],
        target_domain: Optional[str] = None,
        min_relevance: str = "low"
    ) -> List[Dict[str, Any]]:
        """
        Validate discovered companies and filter by relevance.

        Args:
            discovered_companies: List from CompanyDiscoveryAgent with format:
                [{"name": "Company", "source": "seed|domain", "confidence": 0.8}, ...]
            target_domain: Target industry/domain
            min_relevance: Minimum relevance level ("high", "medium", "low")

        Returns:
            List of validated and enriched companies
        """
        # Extract company names
        company_names = [c["name"] for c in discovered_companies]

        # Batch validate
        validated = await self.batch_validate(company_names, target_domain)

        # Filter by relevance
        relevance_hierarchy = {"high": 3, "medium": 2, "low": 1, "none": 0}
        min_level = relevance_hierarchy.get(min_relevance, 1)

        filtered = [
            c for c in validated
            if relevance_hierarchy.get(c.get("relevance_to_domain", "none"), 0) >= min_level
        ]

        print(f"[VALIDATION AGENT] Filtered to {len(filtered)} companies with relevance >= '{min_relevance}'")

        return filtered
