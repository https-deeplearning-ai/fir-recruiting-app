"""
Enhanced CoreSignal service functions with pagination support.

This module shows how to add pagination to the existing search_profiles_with_endpoint
function to support fetching more than 20 candidates.
"""

import os
import requests
import time
import math
from typing import Dict, Any, List, Optional


def make_coresignal_request_with_retry(url, payload, headers, max_retries=3, timeout=30):
    """
    Make CoreSignal API request with retry logic for 503 errors.

    CoreSignal uses 18 requests/second rate limit and returns 503 for rate limiting.

    Args:
        url: CoreSignal API endpoint URL
        payload: Request payload (query)
        headers: Request headers with API key
        max_retries: Maximum number of retries (default 3)
        timeout: Request timeout in seconds (default 30)

    Returns:
        tuple: (success: bool, response_json: dict/list, error_msg: str)
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)

            if response.status_code == 200:
                return (True, response.json(), None)

            # Retry on 503 (rate limiting)
            if response.status_code == 503 and attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"   ⚠️  Rate limit (503) - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(wait_time)
                continue

            # Return error for non-retryable status codes or max retries reached
            error_body = response.text[:200] if response.text else "No response body"
            return (False, None, f"API error {response.status_code}: {error_body}")

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                print(f"   ⚠️  Timeout - retrying...")
                time.sleep(2)
                continue
            return (False, None, f"Request timeout after {timeout}s")

        except Exception as e:
            if attempt < max_retries:
                print(f"   ⚠️  Error: {e} - retrying...")
                time.sleep(2)
                continue
            return (False, None, f"Request exception: {str(e)}")

    return (False, None, "Max retries exceeded")


def search_profiles_with_endpoint_paginated(
    query: Dict[str, Any],
    endpoint: str = "employee_clean",
    max_results: int = 20,
    page_start: int = 1,
    delay_between_pages: float = 4.0  # Increased from 2.0 to prevent rate limits
) -> Dict[str, Any]:
    """
    Execute custom ES DSL search with PAGINATION support.

    CoreSignal's preview endpoint returns max 20 results per page.
    This function can fetch multiple pages to get up to 100 results.

    Args:
        query: Elasticsearch DSL query dict
        endpoint: CoreSignal endpoint (employee_base, employee_clean, multi_source_employee)
        max_results: Maximum number of results to return (can be > 20)
        page_start: Starting page number (for "Load More" functionality)
        delay_between_pages: Seconds to wait between page requests (rate limit protection)

    Returns:
        Dict with 'success', 'results', 'total', 'pages_fetched', 'has_more'
    """
    api_key = os.getenv("CORESIGNAL_API_KEY")
    if not api_key:
        return {"success": False, "error": "CORESIGNAL_API_KEY not found"}

    headers = {
        "accept": "application/json",
        "apikey": api_key,
        "Content-Type": "application/json"
    }

    # Calculate pagination
    RESULTS_PER_PAGE = 20
    MAX_PAGES = 5  # CoreSignal limits to 5 pages (100 results max)

    total_pages_needed = math.ceil(max_results / RESULTS_PER_PAGE)
    pages_to_fetch = min(total_pages_needed, MAX_PAGES - page_start + 1)

    # Build base URL
    base_url = f"https://api.coresignal.com/cdapi/v2/{endpoint}/search/es_dsl/preview"

    # Remove size from query if present (causes HTTP 422)
    if "size" in query:
        del query["size"]

    all_results = []
    pages_fetched = 0
    total_found = 0

    print(f"🔍 Paginated search on {endpoint}")
    print(f"   Target: {max_results} results")
    print(f"   Starting from page: {page_start}")
    print(f"   Pages to fetch: {pages_to_fetch}")

    for page_num in range(page_start, page_start + pages_to_fetch):
        # Add delay between pages (except for first page)
        if page_num > page_start:
            print(f"   ⏱️  Waiting {delay_between_pages}s before next page (rate limit protection)...")
            time.sleep(delay_between_pages)

        print(f"   📄 Fetching page {page_num}...")

        # Add page parameter to URL
        url_with_page = f"{base_url}?page={page_num}"

        # Use retry logic for 503 errors
        success, data, error_msg = make_coresignal_request_with_retry(
            url=url_with_page,
            payload=query,
            headers=headers,
            max_retries=3,
            timeout=30
        )

        if not success:
            print(f"   ⚠️  Page {page_num} failed: {error_msg}")
            # If first page fails, return error
            if page_num == page_start:
                return {
                    "success": False,
                    "error": f"Search failed: {error_msg}",
                    "details": error_msg
                }
            # Otherwise, return what we have so far
            break

        # Handle response format
        if isinstance(data, list):
            # Preview endpoint returns list of employee IDs/profiles
            page_results = data
            print(f"   ✅ Page {page_num}: {len(page_results)} results")
        else:
            # Should not happen with preview endpoint
            page_results = []
            print(f"   ⚠️  Unexpected response format on page {page_num}")

        all_results.extend(page_results)
        pages_fetched += 1

        # Stop if we have enough results
        if len(all_results) >= max_results:
            all_results = all_results[:max_results]
            print(f"   ✂️  Trimmed to {max_results} results")
            break

        # Stop if page returned less than full page (no more results)
        if len(page_results) < RESULTS_PER_PAGE:
            print(f"   📍 Reached end of results (page {page_num} had {len(page_results)} results)")
            break

    # Calculate if there are more results available
    last_page_fetched = page_start + pages_fetched - 1
    has_more = (
        last_page_fetched < MAX_PAGES and  # Haven't reached API limit
        len(all_results) == pages_fetched * RESULTS_PER_PAGE  # Last page was full
    )

    print(f"   🎯 Total fetched: {len(all_results)} results across {pages_fetched} pages")

    return {
        "success": True,
        "results": all_results,
        "total": len(all_results),
        "endpoint": endpoint,
        "pagination": {
            "pages_fetched": pages_fetched,
            "last_page": last_page_fetched,
            "has_more": has_more,
            "next_page": last_page_fetched + 1 if has_more else None
        }
    }


def fetch_more_previews(
    session_id: str,
    current_count: int,
    additional_count: int = 20
) -> Dict[str, Any]:
    """
    Fetch additional preview candidates for an existing search session.

    This function would be called by a "Load More" button in the UI.

    Args:
        session_id: The domain search session ID
        current_count: How many candidates are already loaded
        additional_count: How many more to fetch (default 20)

    Returns:
        Dict with new previews and pagination info
    """
    # Calculate which page to start from
    current_pages = math.ceil(current_count / 20)
    next_page = current_pages + 1

    if next_page > 5:
        return {
            "success": False,
            "error": "Maximum results reached (100 candidates)",
            "previews": [],
            "has_more": False
        }

    # Load the saved query from session
    # (This would need to be implemented - save query in session storage)
    saved_query = load_query_from_session(session_id)

    if not saved_query:
        return {
            "success": False,
            "error": "Session not found or expired",
            "previews": []
        }

    # Fetch additional pages
    result = search_profiles_with_endpoint_paginated(
        query=saved_query["query"],
        endpoint=saved_query["endpoint"],
        max_results=additional_count,
        page_start=next_page
    )

    if not result["success"]:
        return {
            "success": False,
            "error": result.get("error", "Failed to fetch more results"),
            "previews": []
        }

    return {
        "success": True,
        "previews": result["results"],
        "total_loaded": current_count + len(result["results"]),
        "has_more": result["pagination"]["has_more"],
        "next_page": result["pagination"]["next_page"]
    }


def load_query_from_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load saved query from session storage.

    In production, this would load from:
    - Redis cache
    - Supabase session table
    - Or filesystem (current approach)
    """
    import json
    session_dir = f"/backend/logs/domain_search_sessions/{session_id}"
    query_file = f"{session_dir}/02_preview_query.json"

    if os.path.exists(query_file):
        with open(query_file, 'r') as f:
            data = json.load(f)
            return {
                "query": data.get("query"),
                "endpoint": data.get("input", {}).get("endpoint", "employee_clean")
            }
    return None


# Example usage
if __name__ == "__main__":
    # Test pagination with a simple query
    test_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"experience.company_name": "OpenAI"}}
                ]
            }
        }
    }

    # Fetch first 40 results (2 pages)
    print("\n" + "="*80)
    print("TEST: Fetching 40 results (2 pages)")
    print("="*80)

    result = search_profiles_with_endpoint_paginated(
        query=test_query,
        endpoint="employee_clean",
        max_results=40
    )

    if result["success"]:
        print(f"\n✅ Success!")
        print(f"   Results: {result['total']}")
        print(f"   Pages fetched: {result['pagination']['pages_fetched']}")
        print(f"   Has more: {result['pagination']['has_more']}")
    else:
        print(f"\n❌ Failed: {result['error']}")

    # Simulate "Load More" - fetch next 20
    if result["success"] and result["pagination"]["has_more"]:
        print("\n" + "="*80)
        print("TEST: Load More (next 20 results)")
        print("="*80)

        more_results = search_profiles_with_endpoint_paginated(
            query=test_query,
            endpoint="employee_clean",
            max_results=20,
            page_start=result["pagination"]["next_page"]
        )

        if more_results["success"]:
            print(f"\n✅ Loaded more!")
            print(f"   Additional results: {more_results['total']}")
            print(f"   Total now: {result['total'] + more_results['total']}")
        else:
            print(f"\n❌ Load more failed: {more_results['error']}")