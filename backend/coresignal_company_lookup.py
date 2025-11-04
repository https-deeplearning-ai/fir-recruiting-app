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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_company_by_name(
        self,
        company_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for companies by name using CoreSignal API.

        Args:
            company_name: Company name to search for
            limit: Maximum number of results to return

        Returns:
            List of company data dictionaries with company_id, name, website, etc.
        """
        url = f"{self.base_url}/v2/company_clean/search/es_dsl/preview"

        # Build search query - exact match on name with fuzzy fallback
        payload = {
            "query": {
                "bool": {
                    "should": [
                        # Exact match (highest priority)
                        {
                            "match_phrase": {
                                "name": {
                                    "query": company_name,
                                    "boost": 3.0
                                }
                            }
                        },
                        # Fuzzy match (fallback)
                        {
                            "match": {
                                "name": {
                                    "query": company_name,
                                    "fuzziness": "AUTO",
                                    "boost": 1.0
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": limit
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            companies = []

            for hit in data.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                companies.append({
                    "company_id": source.get("id"),
                    "name": source.get("name"),
                    "website": source.get("website"),
                    "location": source.get("location"),
                    "industry": source.get("industry"),
                    "employee_count": source.get("employees_count"),
                    "founded": source.get("founded"),
                    "score": hit.get("_score")  # Relevance score
                })

            return companies

        except requests.exceptions.RequestException as e:
            print(f"[CORESIGNAL LOOKUP] Error searching for company '{company_name}': {e}")
            return []

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
