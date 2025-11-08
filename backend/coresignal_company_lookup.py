"""
CoreSignal Company ID Lookup Service

Maps company names to CoreSignal company_ids for employee search.
Uses CoreSignal Company Search API to find matching companies.
"""

import os
import requests
from typing import Optional, Dict, Any, List
import time


class CoreSignalCompanyLookup:
    """
    Service for looking up CoreSignal company IDs by company name.

    Uses the CoreSignal Company Search API to find companies and extract their IDs.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoreSignal company lookup service.

        Args:
            api_key: Optional CoreSignal API key, defaults to env var
        """
        self.api_key = api_key or os.getenv("CORESIGNAL_API_KEY")
        if not self.api_key:
            raise ValueError("CORESIGNAL_API_KEY not found in environment variables")

        self.base_url = "https://api.coresignal.com"
        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def search_company_by_name(
        self,
        company_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for companies by name using CoreSignal API (two-step workflow).

        Step 1: Search endpoint returns company IDs
        Step 2: Collect endpoint fetches full data for those IDs

        Args:
            company_name: Company name to search for
            limit: Maximum number of results to return

        Returns:
            List of company data dictionaries with company_id, name, website, etc.
        """
        # STEP 1: Search for company IDs
        search_url = f"{self.base_url}/cdapi/v2/company_base/search/es_dsl"

        # Build search query using wildcard for fuzzy matching
        # Use lowercase wildcard pattern for better matching
        wildcard_pattern = f"*{company_name.lower().replace(' ', '*')}*"

        payload = {
            "query": {
                "bool": {
                    "should": [
                        # Try exact match first (highest priority)
                        {
                            "term": {
                                "name.exact": company_name
                            }
                        },
                        # Try wildcard match on lowercase
                        {
                            "wildcard": {
                                "name": {
                                    "value": wildcard_pattern,
                                    "case_insensitive": True
                                }
                            }
                        },
                        # Try match query (tokenized search)
                        {
                            "match": {
                                "name": {
                                    "query": company_name,
                                    "operator": "and"
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1,
                    # Filter to US companies only
                    "filter": [
                        {
                            "term": {
                                "country": "United States"
                            }
                        }
                    ]
                }
            }
        }

        try:
            # Search returns a list of company IDs
            response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)

            # DEBUG: Log response status
            print(f"[COMPANY LOOKUP] Search '{company_name}': Status {response.status_code}")

            if response.status_code != 200:
                print(f"[COMPANY LOOKUP] Error response: {response.text[:200]}")
                return []

            response.raise_for_status()

            company_ids = response.json()  # List of integers

            # DEBUG: Log results
            print(f"[COMPANY LOOKUP] Found {len(company_ids) if isinstance(company_ids, list) else 0} IDs for '{company_name}'")

            if not company_ids:
                return []

            # Take only top N results
            company_ids = company_ids[:limit]

            # STEP 2: Fetch full data for each company ID
            companies = []
            for company_id in company_ids:
                company_data = self._fetch_company_by_id(company_id)
                if company_data:
                    companies.append(company_data)

            return companies

        except requests.exceptions.RequestException as e:
            print(f"[CORESIGNAL LOOKUP] Error searching for company '{company_name}': {e}")
            return []

    def _fetch_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch full company data by ID using the collect endpoint.

        Args:
            company_id: CoreSignal company ID

        Returns:
            Company data dictionary or None if fetch fails
        """
        collect_url = f"{self.base_url}/cdapi/v2/company_base/collect/{company_id}"

        try:
            response = requests.get(collect_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract relevant fields
            return {
                "company_id": data.get("id"),
                "name": data.get("name"),
                "website": data.get("website"),
                "location": data.get("location"),
                "industry": data.get("industry"),
                "employee_count": data.get("employees_count"),
                "founded": data.get("founded"),
                "score": 1.0  # No relevance score from collect endpoint
            }

        except requests.exceptions.RequestException as e:
            print(f"[CORESIGNAL LOOKUP] Error fetching company ID {company_id}: {e}")
            return None

    def get_best_match(
        self,
        company_name: str,
        confidence_threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best matching company ID for a company name.

        Args:
            company_name: Company name to look up
            confidence_threshold: Minimum confidence score (0-1) for a match

        Returns:
            Dictionary with company_id, name, and confidence score, or None if no good match
        """
        results = self.search_company_by_name(company_name, limit=5)

        if not results:
            return None

        # Get the best match (highest score)
        best_match = results[0]

        # Calculate confidence based on name similarity and score
        name_similarity = self._calculate_name_similarity(
            company_name.lower(),
            best_match["name"].lower() if best_match["name"] else ""
        )

        # Normalize score (CoreSignal scores are typically 0-10+)
        normalized_score = min(best_match.get("score", 0) / 10.0, 1.0)

        # Combined confidence: 70% name similarity, 30% search score
        confidence = (name_similarity * 0.7) + (normalized_score * 0.3)

        if confidence >= confidence_threshold:
            return {
                "company_id": best_match["company_id"],
                "name": best_match["name"],
                "website": best_match.get("website"),
                "confidence": round(confidence, 2),
                "employee_count": best_match.get("employee_count")
            }

        return None

    def batch_lookup(
        self,
        company_names: List[str],
        confidence_threshold: float = 0.8,
        delay_between_requests: float = 0.1
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Look up multiple companies in batch.

        Args:
            company_names: List of company names to look up
            confidence_threshold: Minimum confidence for matches
            delay_between_requests: Delay in seconds between API calls

        Returns:
            Dictionary mapping company names to their CoreSignal data (or None if no match)
        """
        results = {}

        for company_name in company_names:
            match = self.get_best_match(company_name, confidence_threshold)
            results[company_name] = match

            # Rate limiting
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)

        return results

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate simple similarity score between two company names.

        Uses a basic approach:
        - Exact match: 1.0
        - Name1 contains name2 or vice versa: 0.9
        - Levenshtein distance-based: 0.0-0.8

        Args:
            name1: First company name (lowercase)
            name2: Second company name (lowercase)

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if not name1 or not name2:
            return 0.0

        # Exact match
        if name1 == name2:
            return 1.0

        # Substring match
        if name1 in name2 or name2 in name1:
            return 0.9

        # Simple Levenshtein distance
        distance = self._levenshtein_distance(name1, name2)
        max_len = max(len(name1), len(name2))

        # Normalize: 1.0 = identical, 0.0 = completely different
        if max_len == 0:
            return 0.0

        similarity = 1.0 - (distance / max_len)
        return max(0.0, min(similarity, 0.8))  # Cap at 0.8 for non-exact matches

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def get_by_website(self, website: str) -> Optional[Dict[str, Any]]:
        """
        Look up company by exact website domain (most reliable method).

        Uses CoreSignal's website.exact field for precise matching with caching.

        Args:
            website: Company website domain (e.g., "vena.io", "floqast.com")

        Returns:
            Company data with ID, or None if not found
        """
        # Clean website (remove http://, https://, www.)
        cleaned_website = website.lower().strip()
        cleaned_website = cleaned_website.replace('https://', '').replace('http://', '')
        cleaned_website = cleaned_website.replace('www.', '').rstrip('/')

        # CHECK CACHE FIRST
        cache_result = self._check_cache(cleaned_website)
        if cache_result == "NO_MATCH":
            print(f"[COMPANY LOOKUP] ❌ Cache: {cleaned_website} (previously failed)")
            return None
        if cache_result:
            print(f"[COMPANY LOOKUP] ✅ Cache hit: {cleaned_website}")
            return cache_result

        # CACHE MISS - call API
        # Build ES DSL query for exact website match
        search_url = f"{self.base_url}/cdapi/v2/company_base/search/es_dsl"

        payload = {
            "query": {
                "term": {
                    "website.exact": cleaned_website
                }
            }
        }

        try:
            print(f"[COMPANY LOOKUP] Searching by website: {cleaned_website}")

            response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)

            if response.status_code != 200:
                print(f"[COMPANY LOOKUP] Website search failed: {response.status_code}")
                self._store_in_cache(cleaned_website, None, success=False)
                return None

            company_ids = response.json()  # List of IDs

            if not company_ids:
                print(f"[COMPANY LOOKUP] No companies found for website: {cleaned_website}")
                self._store_in_cache(cleaned_website, None, success=False)
                return None

            # Get first result (should be exact match)
            company_id = company_ids[0]

            # Fetch full company data
            company_data = self._fetch_company_by_id(company_id)

            if company_data:
                print(f"[COMPANY LOOKUP] ✅ Found via website: ID={company_id}, Name={company_data.get('name')}")
                result = {
                    "company_id": company_data["company_id"],
                    "name": company_data["name"],
                    "website": cleaned_website,
                    "confidence": 1.0,  # Exact match via website
                    "employee_count": company_data.get("employee_count")
                }
                self._store_in_cache(cleaned_website, result, success=True)
                return result

            self._store_in_cache(cleaned_website, None, success=False)
            return None

        except Exception as e:
            print(f"[COMPANY LOOKUP] Error in website lookup: {e}")
            self._store_in_cache(cleaned_website, None, success=False)
            return None

    def _check_cache(self, website: str):
        """Check Supabase cache for previous website lookup"""
        try:
            import os
            import requests

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                return None

            url = f"{supabase_url}/rest/v1/company_lookup_cache"
            params = {"website": f"eq.{website}", "select": "*"}
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)

            if response.status_code == 200:
                results = response.json()
                if results:
                    cached = results[0]

                    # Update last_used_at timestamp
                    self._touch_cache(website)

                    if cached['lookup_successful']:
                        return {
                            "company_id": cached['company_id'],
                            "name": cached['company_name'],
                            "website": website,
                            "confidence": float(cached['confidence']),
                            "employee_count": cached['employee_count']
                        }
                    else:
                        # Cached negative result (lookup previously failed)
                        return "NO_MATCH"

            return None

        except Exception as e:
            print(f"[CACHE] Error checking cache: {e}")
            return None

    def _store_in_cache(self, website: str, result: Optional[Dict], success: bool):
        """Store lookup result in Supabase cache"""
        try:
            import os
            import requests

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                return

            cache_data = {
                "website": website,
                "lookup_successful": success
            }

            if success and result:
                cache_data.update({
                    "company_id": result['company_id'],
                    "company_name": result['name'],
                    "confidence": result['confidence'],
                    "employee_count": result.get('employee_count')
                })

            url = f"{supabase_url}/rest/v1/company_lookup_cache"
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }

            requests.post(url, json=cache_data, headers=headers, timeout=5)

            if success and result:
                print(f"[CACHE] Stored: {website} → ✅ ID {result.get('company_id')}")
            else:
                print(f"[CACHE] Stored: {website} → ❌ no match")

        except Exception as e:
            print(f"[CACHE] Error storing in cache: {e}")

    def _touch_cache(self, website: str):
        """Update last_used_at timestamp (silent fail)"""
        try:
            import os
            import requests

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                return

            url = f"{supabase_url}/rest/v1/company_lookup_cache"
            params = {"website": f"eq.{website}"}
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }

            # Trigger will auto-update last_used_at
            requests.patch(url, params=params, json={}, headers=headers, timeout=5)

        except:
            pass  # Silent fail for touch operation
