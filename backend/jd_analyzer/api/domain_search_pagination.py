"""
Domain Search Pagination Enhancement

Adds "Load More" functionality to fetch candidates beyond the initial 20.
This module can be integrated into the existing domain_search.py.
"""

import json
import os
import time
import math
from typing import Dict, Any, List, Optional
from pathlib import Path


class DomainSearchPagination:
    """Handles pagination for domain search preview candidates."""

    RESULTS_PER_PAGE = 20
    MAX_PAGES = 5  # CoreSignal limit
    MAX_TOTAL_RESULTS = 100
    RATE_LIMIT_DELAY = 4.0  # Seconds between pages (increased from 2.0 to prevent rate limits)

    def __init__(self, session_id: str):
        """
        Initialize pagination handler for a domain search session.

        Args:
            session_id: The domain search session ID
        """
        self.session_id = session_id
        self.session_dir = Path(f"logs/domain_search_sessions/{session_id}")

    def save_pagination_state(self, query: Dict, endpoint: str, current_page: int, total_fetched: int):
        """
        Save pagination state to session storage.

        Args:
            query: The CoreSignal query being used
            endpoint: The CoreSignal endpoint
            current_page: Last page fetched
            total_fetched: Total candidates fetched so far
        """
        state = {
            "session_id": self.session_id,
            "query": query,
            "endpoint": endpoint,
            "pagination": {
                "last_page_fetched": current_page,
                "total_fetched": total_fetched,
                "timestamp": time.time()
            }
        }

        # Save to session directory
        pagination_file = self.session_dir / "pagination_state.json"
        pagination_file.parent.mkdir(parents=True, exist_ok=True)

        with open(pagination_file, 'w') as f:
            json.dump(state, f, indent=2)

        return state

    def load_pagination_state(self) -> Optional[Dict]:
        """
        Load saved pagination state from session.

        Returns:
            Saved state dict or None if not found
        """
        pagination_file = self.session_dir / "pagination_state.json"

        if pagination_file.exists():
            with open(pagination_file, 'r') as f:
                return json.load(f)
        return None

    def fetch_next_page(self, api_key: str) -> Dict[str, Any]:
        """
        Fetch the next page of results for this session.

        Args:
            api_key: CoreSignal API key

        Returns:
            Dict with new candidates and pagination info
        """
        # Load saved state
        state = self.load_pagination_state()
        if not state:
            return {
                "success": False,
                "error": "No pagination state found. Please run initial search first.",
                "candidates": []
            }

        query = state["query"]
        endpoint = state["endpoint"]
        last_page = state["pagination"]["last_page_fetched"]
        total_fetched = state["pagination"]["total_fetched"]

        # Check if we've reached limits
        next_page = last_page + 1
        if next_page > self.MAX_PAGES:
            return {
                "success": False,
                "error": f"Maximum page limit reached ({self.MAX_PAGES} pages, {self.MAX_TOTAL_RESULTS} candidates)",
                "candidates": [],
                "has_more": False
            }

        if total_fetched >= self.MAX_TOTAL_RESULTS:
            return {
                "success": False,
                "error": f"Maximum result limit reached ({self.MAX_TOTAL_RESULTS} candidates)",
                "candidates": [],
                "has_more": False
            }

        # Fetch next page
        print(f"\n📄 Fetching page {next_page} for session {self.session_id}")
        print(f"   Current total: {total_fetched} candidates")

        import requests

        headers = {
            "accept": "application/json",
            "apikey": api_key,
            "Content-Type": "application/json"
        }

        url = f"https://api.coresignal.com/cdapi/v2/{endpoint}/search/es_dsl/preview?page={next_page}"

        try:
            response = requests.post(url, json=query, headers=headers, timeout=30)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API request failed: HTTP {response.status_code}",
                    "candidates": []
                }

            candidates = response.json()

            # Update pagination state
            new_total = total_fetched + len(candidates)
            self.save_pagination_state(query, endpoint, next_page, new_total)

            # Check if there are more pages
            has_more = (
                len(candidates) == self.RESULTS_PER_PAGE and
                next_page < self.MAX_PAGES and
                new_total < self.MAX_TOTAL_RESULTS
            )

            print(f"   ✅ Fetched {len(candidates)} more candidates")
            print(f"   📊 New total: {new_total} candidates")

            return {
                "success": True,
                "candidates": candidates,
                "page_fetched": next_page,
                "total_fetched": new_total,
                "has_more": has_more,
                "remaining_pages": self.MAX_PAGES - next_page if has_more else 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch page: {str(e)}",
                "candidates": []
            }


async def enhanced_stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    session_logger,
    enable_pagination: bool = True
) -> Dict[str, Any]:
    """
    Enhanced Stage 2 with pagination support.

    This is a drop-in replacement for the existing stage2_preview_search
    that adds pagination capabilities.

    Args:
        companies: Discovered companies
        jd_requirements: JD requirements
        endpoint: CoreSignal endpoint
        max_previews: Initial candidates to fetch (can be > 20 with pagination)
        session_logger: Session logger
        enable_pagination: Whether to enable multi-page fetching

    Returns:
        Enhanced results with pagination info
    """
    from coresignal_service import search_profiles_with_endpoint
    import os

    print("\n" + "="*80)
    print("STAGE 2: Enhanced Preview Search (with Pagination)")
    print("="*80)

    # Build query (existing logic)
    role_keywords = ["engineer", "developer", "architect", "product", "manager", "founder"]

    # Import the build function (would be from existing code)
    from domain_search import build_domain_company_query

    query = build_domain_company_query(
        companies=companies,
        role_keywords=role_keywords,
        location="United States",
        require_current_role=False
    )

    api_key = os.getenv("CORESIGNAL_API_KEY")
    if not api_key:
        return {"success": False, "error": "API key not found"}

    all_candidates = []
    pages_to_fetch = math.ceil(min(max_previews, 100) / 20) if enable_pagination else 1

    print(f"📊 Pagination Plan:")
    print(f"   Target candidates: {max_previews}")
    print(f"   Pages needed: {pages_to_fetch}")
    print(f"   Pagination enabled: {enable_pagination}")

    # Initialize pagination handler
    session_id = session_logger.session_id if hasattr(session_logger, 'session_id') else "default"
    pagination = DomainSearchPagination(session_id)

    # Fetch pages
    for page_num in range(1, pages_to_fetch + 1):
        if page_num > 1:
            print(f"   ⏱️  Rate limit delay: {DomainSearchPagination.RATE_LIMIT_DELAY}s")
            time.sleep(DomainSearchPagination.RATE_LIMIT_DELAY)

        print(f"\n📄 Fetching page {page_num}/{pages_to_fetch}")

        # For first page, use existing function
        if page_num == 1:
            result = search_profiles_with_endpoint(
                query=query,
                endpoint=endpoint,
                max_results=20
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error"),
                    "previews": []
                }

            candidates = result.get("results", [])
            all_candidates.extend(candidates)

            # Save pagination state for potential "Load More"
            pagination.save_pagination_state(query, endpoint, 1, len(candidates))

        else:
            # Fetch additional pages
            result = pagination.fetch_next_page(api_key)

            if not result.get("success"):
                print(f"   ⚠️  Failed to fetch page {page_num}: {result.get('error')}")
                break  # Return what we have so far

            candidates = result.get("candidates", [])
            all_candidates.extend(candidates)

        print(f"   ✅ Page {page_num}: {len(candidates)} candidates")

        # Stop if we have enough
        if len(all_candidates) >= max_previews:
            all_candidates = all_candidates[:max_previews]
            print(f"   ✂️  Trimmed to {max_previews} candidates")
            break

    # Calculate pagination info
    has_more = (
        len(all_candidates) == pages_to_fetch * 20 and  # All pages were full
        pages_to_fetch < 5 and  # Haven't hit API limit
        len(all_candidates) < 100  # Haven't hit our limit
    )

    print(f"\n📊 Preview Search Results:")
    print(f"   Total candidates: {len(all_candidates)}")
    print(f"   Pages fetched: {min(pages_to_fetch, page_num)}")
    print(f"   Has more available: {has_more}")

    return {
        "previews": all_candidates,
        "total_found": len(all_candidates),
        "pagination": {
            "session_id": session_id,
            "pages_fetched": min(pages_to_fetch, page_num),
            "has_more": has_more,
            "can_load_more": has_more,
            "max_available": min(100, pages_to_fetch * 20)  # Estimate
        },
        "relevance_score": calculate_relevance(all_candidates, companies)
    }


def calculate_relevance(candidates: List[Dict], companies: List[Dict]) -> float:
    """Calculate what percentage of candidates have domain experience."""
    if not candidates:
        return 0.0

    domain_matches = 0
    company_names = [c['name'].lower() for c in companies]

    for candidate in candidates:
        if has_domain_experience(candidate, company_names):
            domain_matches += 1

    return domain_matches / len(candidates)


def has_domain_experience(candidate: Dict, company_names: List[str]) -> bool:
    """Check if candidate has experience at domain companies."""
    experiences = candidate.get('experience', []) if isinstance(candidate, dict) else []

    for exp in experiences:
        company = exp.get('company_name', '').lower()
        if any(domain_company in company for domain_company in company_names):
            return True
    return False


# API Endpoint for "Load More" functionality
async def load_more_previews(session_id: str, api_key: str) -> Dict[str, Any]:
    """
    API endpoint handler for loading more preview candidates.

    This would be called when user clicks "Load More" button.

    Args:
        session_id: The domain search session ID
        api_key: CoreSignal API key

    Returns:
        Additional candidates with pagination info
    """
    print(f"\n🔄 Load More Request for session: {session_id}")

    pagination = DomainSearchPagination(session_id)
    state = pagination.load_pagination_state()

    if not state:
        return {
            "success": False,
            "error": "Session not found or expired",
            "candidates": []
        }

    # Check session age (expire after 1 hour)
    age = time.time() - state["pagination"]["timestamp"]
    if age > 3600:
        return {
            "success": False,
            "error": "Session expired (>1 hour old)",
            "candidates": []
        }

    # Add rate limit protection
    time.sleep(DomainSearchPagination.RATE_LIMIT_DELAY)

    # Fetch next page
    result = pagination.fetch_next_page(api_key)

    if result.get("success"):
        print(f"   ✅ Loaded {len(result['candidates'])} more candidates")
        print(f"   📊 Total now: {result['total_fetched']} candidates")
    else:
        print(f"   ❌ Failed: {result.get('error')}")

    return result


# Example usage
if __name__ == "__main__":
    # Test the enhanced preview search with pagination

    # Mock session logger
    class MockLogger:
        def __init__(self):
            self.session_id = "test_" + str(int(time.time()))

        def log_json(self, filename, data):
            pass

    # Mock companies from Stage 1
    test_companies = [
        {"id": 123, "name": "Deepgram"},
        {"id": 456, "name": "AssemblyAI"},
        {"id": 789, "name": "Otter.ai"}
    ]

    # Mock JD requirements
    test_jd = {
        "role_title": "ML Engineer",
        "seniority_level": "senior",
        "target_domain": "voice ai"
    }

    print("="*80)
    print("PAGINATION TEST: Fetch 60 candidates (3 pages)")
    print("="*80)

    # This would fetch 3 pages (60 candidates)
    import asyncio

    async def test():
        result = await enhanced_stage2_preview_search(
            companies=test_companies,
            jd_requirements=test_jd,
            endpoint="employee_clean",
            max_previews=60,  # Request 60 (will fetch 3 pages)
            session_logger=MockLogger(),
            enable_pagination=True
        )

        if result.get("previews"):
            print(f"\n✅ Test successful!")
            print(f"   Fetched: {len(result['previews'])} candidates")
            print(f"   Can load more: {result['pagination']['can_load_more']}")

    # Run test
    # asyncio.run(test())