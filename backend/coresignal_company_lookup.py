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
        limit: int = 20,
        max_pages: int = 5,
        check_exact_match_first: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for companies by name using CoreSignal API with pagination support.

        CoreSignal Pagination:
        - Use ?page=N query parameter (NOT from/size in body)
        - Returns 20 results per page
        - Max 5 pages = 100 results total
        - Stops early if exact match found (saves API calls)

        Args:
            company_name: Company name to search for
            limit: Maximum number of results to return (default 20)
            max_pages: Number of pages to search (1-5, default 5 for 100 results)
            check_exact_match_first: If True, stops when exact match found

        Returns:
            List of company data dictionaries with company_id, name, website, etc.
        """
        # Use /preview endpoint with page query parameter
        base_search_url = f"{self.base_url}/cdapi/v2/company_base/search/es_dsl/preview"

        # Build search query
        wildcard_pattern = f"*{company_name.lower().replace(' ', '*')}*"

        payload = {
            "query": {
                "bool": {
                    "should": [
                        {"term": {"name.exact": company_name}},
                        {"wildcard": {"name": {"value": wildcard_pattern, "case_insensitive": True}}},
                        {"match": {"name": {"query": company_name, "operator": "and"}}}
                    ],
                    "minimum_should_match": 1
                }
            }
        }

        all_results = []
        pages_fetched = 0

        for page in range(1, max_pages + 1):
            # Add page as URL query parameter (NOT in body)
            search_url = f"{base_search_url}?page={page}"

            try:
                response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)
                pages_fetched += 1

                if page == 1:
                    print(f"[COMPANY LOOKUP] Search '{company_name}': Status {response.status_code}")

                if response.status_code != 200:
                    print(f"[COMPANY LOOKUP] Error on page {page}: {response.text[:200]}")
                    break

                companies = response.json()

                if not companies:
                    print(f"[COMPANY LOOKUP] No results on page {page}, stopping")
                    break

                if page == 1:
                    print(f"[COMPANY LOOKUP] Found {len(companies)} results on page 1")
                elif page > 1:
                    print(f"[COMPANY LOOKUP] Page {page}: +{len(companies)} results")

                # Extract fields and check for exact match
                for company in companies:
                    result = {
                        "company_id": company.get("id"),
                        "name": company.get("name"),
                        "website": company.get("website"),
                        "location": company.get("headquarters_country_parsed"),
                        "industry": company.get("industry"),
                        "employee_count": None,  # Not in preview response
                        "founded": None,  # Not in preview response
                        "score": company.get("_score", 1.0)
                    }
                    all_results.append(result)

                    # OPTIMIZATION: Stop early if exact match found
                    if check_exact_match_first and result['name'] and result['name'].lower() == company_name.lower():
                        print(f"[COMPANY LOOKUP] ✅ Exact match found on page {page}: '{result['name']}' (saved {max_pages - page} page(s))")
                        return [result]  # Return immediately

                # Stop if we got fewer results than expected (last page)
                if len(companies) < 20:
                    print(f"[COMPANY LOOKUP] Page {page} returned {len(companies)} results (< 20), stopping")
                    break

            except requests.exceptions.RequestException as e:
                print(f"[CORESIGNAL LOOKUP] Error on page {page}: {e}")
                break

        print(f"[COMPANY LOOKUP] Pagination complete: {pages_fetched} page(s), {len(all_results)} total results")

        if limit and limit < len(all_results):
            return all_results[:limit]

        return all_results

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

    def lookup_by_company_clean(
        self,
        company_name: str,
        website: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        TIER 4: Fallback to company_clean endpoint.

        company_clean may have different company coverage than company_base.
        Use as last resort when company_base returns 0 results across all tiers.

        IMPORTANT: Uses /preview endpoint (0 credits) instead of /collect (1 credit).
        We only need the company ID - future agent will /collect the full data.

        Args:
            company_name: Company name to search
            website: Optional website for better matching

        Returns:
            Company data with company_id, data_source='company_clean'
        """
        # Use /preview endpoint - returns basic data without /collect call (0 credits)
        search_url = f"{self.base_url}/cdapi/v2/company_clean/search/es_dsl/preview"

        # Build query (similar to company_base)
        wildcard_pattern = f"*{company_name.lower().replace(' ', '*')}*"

        payload = {
            "query": {
                "bool": {
                    "should": [
                        {"term": {"name.exact": company_name}},
                        {"wildcard": {"name": {"value": wildcard_pattern, "case_insensitive": True}}},
                        {"match": {"name": {"query": company_name, "operator": "and"}}}
                    ],
                    "minimum_should_match": 1
                }
            }
        }

        # Add website filter if available
        if website:
            cleaned_website = website.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            payload["query"]["bool"]["should"].insert(0, {
                "term": {"websites_main": cleaned_website}
            })

        try:
            print(f"[COMPANY LOOKUP] 🔍 Tier 4: Trying company_clean fallback...")
            response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)

            print(f"[COMPANY LOOKUP] company_clean search: Status {response.status_code}")

            if response.status_code != 200:
                print(f"[COMPANY LOOKUP] company_clean error: {response.text[:200]}")
                return None

            companies = response.json()  # /preview returns full objects (basic fields)

            if not companies:
                print(f"[COMPANY LOOKUP] company_clean: No results")
                return None

            print(f"[COMPANY LOOKUP] company_clean: Found {len(companies)} companies")

            # Check first result for exact or fuzzy match
            first_company = companies[0]
            matched_name = first_company.get('name', '')

            # Check for exact name match
            if matched_name.lower() == company_name.lower():
                print(f"[COMPANY LOOKUP] ✅ company_clean exact match: {matched_name}")
                return {
                    "company_id": first_company.get('id'),
                    "name": matched_name,
                    "website": first_company.get('website'),
                    "confidence": 0.95,  # Exact match
                    "data_source": "company_clean",
                    "note": "Found in company_clean (0 credits - ID only, future agent will /collect)"
                }

            # Fuzzy match - use STRICT Levenshtein distance (no substring matching)
            # to avoid false positives like "Krisp" → "Krispy Kreme"
            distance = self._levenshtein_distance(company_name.lower(), matched_name.lower())
            max_len = max(len(company_name), len(matched_name))
            similarity = 1.0 - (distance / max_len) if max_len > 0 else 0.0

            # Require very high similarity (0.90+) for Tier 4 fuzzy matches
            if similarity >= 0.90:
                print(f"[COMPANY LOOKUP] company_clean fuzzy match: {matched_name} (similarity={similarity:.2f})")
                return {
                    "company_id": first_company.get('id'),
                    "name": matched_name,
                    "website": first_company.get('website'),
                    "confidence": round(similarity, 2),
                    "data_source": "company_clean",
                    "note": "Found in company_clean (0 credits - ID only, future agent will /collect)"
                }
            else:
                print(f"[COMPANY LOOKUP] company_clean rejected: {matched_name} (similarity={similarity:.2f} < 0.90 threshold)")

        except Exception as e:
            print(f"[COMPANY LOOKUP] company_clean exception: {e}")
            return None

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

    def lookup_with_fallback(
        self,
        company_name: str,
        website: Optional[str] = None,
        confidence_threshold: float = 0.85,
        use_company_clean_fallback: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Four-tier lookup strategy: Website → Name → Fuzzy → company_clean.

        This is the recommended method for company lookups as it maximizes
        match rate while avoiding false positives.

        Tier 1: Website exact match (company_base, 90% success when website available)
        Tier 2: Name exact match (company_base, 40-50% success)
        Tier 3: Conservative fuzzy match (company_base, threshold 0.85+, +5-10% coverage)
        Tier 4: company_clean fallback (different company coverage)

        Args:
            company_name: Company name to look up
            website: Optional company website for Tier 1 lookup
            confidence_threshold: Minimum confidence for fuzzy match (default 0.85)
            use_company_clean_fallback: Enable Tier 4 fallback to company_clean (default True)

        Returns:
            Company data with ID, confidence, lookup_method, and tier, or None if no match
        """
        print(f"\n[COMPANY LOOKUP] Starting three-tier lookup for: {company_name}")
        print(f"[COMPANY LOOKUP] Website: {website if website else 'Not provided'}")

        # TIER 1: Website Exact Match (Highest Priority)
        if website:
            print(f"[COMPANY LOOKUP] 🔍 Tier 1: Trying website filter lookup...")
            result = self.lookup_by_website_filter(website)
            if result:
                result['lookup_method'] = 'website_filter'
                result['tier'] = 1
                print(f"[COMPANY LOOKUP] ✅ Tier 1 SUCCESS via website filter")
                return result

            print(f"[COMPANY LOOKUP] 🔍 Tier 1: Trying website ES DSL lookup...")
            result = self.get_by_website(website)
            if result:
                result['lookup_method'] = 'website_esdsl'
                result['tier'] = 1
                print(f"[COMPANY LOOKUP] ✅ Tier 1 SUCCESS via website ES DSL")
                return result

            print(f"[COMPANY LOOKUP] ❌ Tier 1 FAILED - No website match")

        # TIER 2: Name Exact Match
        print(f"[COMPANY LOOKUP] 🔍 Tier 2: Trying name exact match...")
        results = self.search_company_by_name(company_name, limit=5)

        if results:
            # Check if any result is an exact name match
            for result in results:
                if result.get('name', '').lower() == company_name.lower():
                    result['lookup_method'] = 'name_exact'
                    result['tier'] = 2
                    result['confidence'] = 0.95
                    print(f"[COMPANY LOOKUP] ✅ Tier 2 SUCCESS via exact name match")
                    return result

            print(f"[COMPANY LOOKUP] ❌ Tier 2 FAILED - No exact name match")

        # TIER 3: Conservative Fuzzy Match
        print(f"[COMPANY LOOKUP] 🔍 Tier 3: Trying conservative fuzzy match (threshold={confidence_threshold})...")
        result = self.get_best_match(company_name, confidence_threshold)

        if result:
            result['lookup_method'] = 'fuzzy_match'
            result['tier'] = 3
            print(f"[COMPANY LOOKUP] ✅ Tier 3 SUCCESS via fuzzy match (confidence={result.get('confidence')})")
            return result

        print(f"[COMPANY LOOKUP] ❌ Tiers 1-3 FAILED (company_base) - No match found for '{company_name}'")

        # TIER 4: company_clean Fallback (Different Company Coverage)
        if use_company_clean_fallback:
            result = self.lookup_by_company_clean(company_name, website)
            if result:
                result['tier'] = 4
                result['lookup_method'] = 'company_clean_fallback'
                print(f"[COMPANY LOOKUP] ✅ Tier 4 SUCCESS via company_clean (confidence={result.get('confidence')})")
                return result

        print(f"[COMPANY LOOKUP] ❌ ALL TIERS EXHAUSTED - No match found for '{company_name}'")
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

    def lookup_by_website_filter(self, website: str) -> Optional[Dict[str, Any]]:
        """
        Look up company using CoreSignal's /filter endpoint with exact_website parameter.

        This is a simpler endpoint than ES DSL and may be more reliable for website matching.
        Tries multiple URL variations (http/https, www/no-www).

        Args:
            website: Company website URL (e.g., "https://deepgram.com", "deepgram.com")

        Returns:
            Company data with ID and confidence, or None if not found
        """
        # Clean and normalize website URL
        cleaned_website = website.lower().strip()
        cleaned_website = cleaned_website.replace('https://', '').replace('http://', '')
        cleaned_website = cleaned_website.replace('www.', '').rstrip('/')

        # Try multiple URL variations
        url_variations = [
            f"https://{cleaned_website}",
            f"http://{cleaned_website}",
            f"https://www.{cleaned_website}",
            cleaned_website
        ]

        print(f"[COMPANY LOOKUP] Trying website filter lookup for: {cleaned_website}")

        for url_variant in url_variations:
            try:
                # Use the /filter endpoint with exact_website parameter
                filter_url = f"{self.base_url}/cdapi/v2/company_base/search/filter"
                params = {"exact_website": url_variant}

                response = requests.get(filter_url, params=params, headers=self.headers, timeout=10)

                if response.status_code != 200:
                    continue  # Try next variation

                companies = response.json()

                if companies and len(companies) > 0:
                    # Found at least one company
                    company_data = companies[0]  # Take first result (exact match)

                    print(f"[COMPANY LOOKUP] ✅ Found via website filter: ID={company_data.get('id')}, Name={company_data.get('name')}")

                    return {
                        "company_id": company_data.get("id"),
                        "name": company_data.get("name"),
                        "website": cleaned_website,
                        "confidence": 1.0,  # Exact match via website
                        "employee_count": company_data.get("employees_count"),
                        "location": company_data.get("location"),
                        "industry": company_data.get("industry")
                    }

            except requests.exceptions.RequestException as e:
                print(f"[COMPANY LOOKUP] Error with variant '{url_variant}': {e}")
                continue  # Try next variation

        print(f"[COMPANY LOOKUP] ❌ No match found via website filter for: {cleaned_website}")
        return None

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
