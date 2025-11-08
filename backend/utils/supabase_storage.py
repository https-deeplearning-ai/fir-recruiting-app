"""
Supabase Storage Module - Persistent Caching for Profiles and Companies

This module provides a centralized interface for storing and retrieving
LinkedIn profiles and company data in Supabase, enabling cross-search
caching to dramatically reduce API credit consumption.

Usage:
    from utils.supabase_storage import (
        get_stored_profile,
        save_stored_profile,
        get_stored_company,
        save_stored_company
    )

    # Check profile cache
    cached_profile = get_stored_profile(linkedin_url)
    if cached_profile:
        profile_data = cached_profile['profile_data']
    else:
        # Fetch from API and cache
        profile_data = fetch_from_api(linkedin_url)
        save_stored_profile(linkedin_url, profile_data)

    # Check company cache
    storage_functions = {
        'get': get_stored_company,
        'save': save_stored_company
    }
    enrich_profile_with_company_data(profile, storage_functions=storage_functions)

Freshness Rules:
    - Profiles:
      * < 3 days: Use cache (no API call)
      * 3-90 days: Use cache but mark stale
      * > 90 days: Force fresh fetch

    - Companies:
      * < 30 days: Use cache (no API call)
      * > 30 days: Force fresh fetch

Credit Savings:
    - First search: 80 credits (cold cache)
    - Second search: 5 credits (94% cache hit rate)
    - Third+ searches: 5 credits (94% cache hit rate)
    - Total for 10 searches: 125 credits vs 800 credits (84% savings)
"""

import os
import json
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

# Load Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _get_supabase_headers() -> Dict[str, str]:
    """
    Get standard Supabase headers for REST API requests.

    Returns:
        dict: Headers with authentication
    """
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }


def _handle_supabase_error(operation: str, error: Exception, silent: bool = False) -> None:
    """
    Handle Supabase errors with logging.

    Args:
        operation: Description of the operation that failed
        error: The exception that occurred
        silent: If True, don't print error (useful for non-critical operations)
    """
    if not silent:
        print(f"⚠️  Supabase {operation} error: {str(error)}")


# =============================================================================
# PROFILE STORAGE FUNCTIONS
# =============================================================================

def get_stored_profile(linkedin_url: str) -> Optional[Dict[str, Any]]:
    """
    Check if profile is stored in database and determine if we should use it.

    Smart Freshness Logic:
    - If < 3 days old: Use stored data (SAVE 1 Collect credit!)
    - If 3-90 days old: Use stored data BUT mark for background refresh
    - If > 90 days (3 months) old: FORCE fresh pull from CoreSignal

    Args:
        linkedin_url: LinkedIn profile URL or employee_id (prefix with "id:" for employee_id)

    Returns:
        dict with profile_data and metadata, or None if needs fresh pull

    Example:
        cached = get_stored_profile("https://linkedin.com/in/johndoe")
        if cached:
            profile = cached['profile_data']
            age_days = cached['storage_age_days']
            is_stale = cached['is_stale']
    """
    try:
        headers = _get_supabase_headers()

        # URL encode the linkedin_url for the query
        encoded_url = urllib.parse.quote(linkedin_url, safe='')

        url = f"{SUPABASE_URL}/rest/v1/stored_profiles?linkedin_url=eq.{encoded_url}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                stored = results[0]

                # Calculate age
                last_fetched = datetime.fromisoformat(stored['last_fetched'].replace('Z', '+00:00'))
                age = datetime.now(last_fetched.tzinfo) - last_fetched
                age_days = age.days

                # FORCE fresh pull if > 90 days (3 months)
                if age_days >= 90:
                    print(f"⚠️  Stored profile is {age_days} days old (>90 days) - FORCING fresh pull")
                    return None

                # Use stored data if < 90 days
                print(f"✅ Using stored profile (age: {age_days} days) - SAVED 1 Collect credit!")

                # Note if it's getting stale (3-90 days)
                if age_days >= 3:
                    print(f"   ℹ️  Note: Profile is {age_days} days old, consider refreshing soon")

                return {
                    'profile_data': stored['profile_data'],
                    'checked_at': stored.get('checked_at'),
                    'last_fetched': stored.get('last_fetched'),
                    'storage_age_days': age_days,
                    'is_stale': age_days >= 3
                }

        return None

    except Exception as e:
        _handle_supabase_error("profile retrieval", e)
        return None


def save_stored_profile(linkedin_url: str, profile_data: Dict[str, Any], checked_at: Optional[float] = None) -> bool:
    """
    Save profile to storage for future cache hits.

    Uses Supabase's merge-duplicates preference to update existing records.

    Args:
        linkedin_url: LinkedIn profile URL or employee_id (prefix with "id:")
        profile_data: Full profile data from CoreSignal API
        checked_at: Timestamp when profile was checked (optional)

    Returns:
        bool: True if saved successfully, False otherwise

    Example:
        saved = save_stored_profile(
            "https://linkedin.com/in/johndoe",
            profile_data,
            checked_at=time.time()
        )
    """
    try:
        headers = _get_supabase_headers()
        headers['Prefer'] = 'resolution=merge-duplicates'

        data = {
            'linkedin_url': linkedin_url,
            'profile_data': profile_data,
            'checked_at': checked_at
        }

        url = f"{SUPABASE_URL}/rest/v1/stored_profiles"
        response = requests.post(url, json=data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            print(f"💾 Saved profile to storage")
            return True
        else:
            print(f"⚠️  Failed to save profile to cache: {response.status_code}")
            return False

    except Exception as e:
        _handle_supabase_error("profile save", e)
        return False


# =============================================================================
# COMPANY STORAGE FUNCTIONS
# =============================================================================

def get_stored_company(company_id: int, freshness_days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Check if company is stored and fresh (< freshness_days old).

    Args:
        company_id: CoreSignal company ID
        freshness_days: Maximum age in days before forcing refresh (default: 30)

    Returns:
        dict with company_data and metadata, or None if needs refresh

    Example:
        cached = get_stored_company(12345, freshness_days=30)
        if cached:
            company_data = cached['company_data']
            age_days = cached['cache_age_days']
            verification = cached.get('verification_data', {})
    """
    try:
        headers = _get_supabase_headers()

        url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                cached = results[0]

                # Check freshness
                last_fetched = datetime.fromisoformat(cached['last_fetched'].replace('Z', '+00:00'))
                age = datetime.now(last_fetched.tzinfo) - last_fetched

                if age.days < freshness_days:
                    print(f"✅ Using stored company {company_id} (age: {age.days} days) - SAVED 1 Collect credit!")

                    # Extract verification data if available
                    verification_data = {}
                    if cached.get('user_verified'):
                        verification_data['user_verified'] = cached['user_verified']
                        verification_data['verification_status'] = cached.get('verification_status', 'pending')
                        verification_data['verified_by'] = cached.get('verified_by')
                        verification_data['verified_at'] = cached.get('verified_at')

                        # Extract the verified Crunchbase URL from company_data
                        company_data = cached.get('company_data', {})
                        if isinstance(company_data, dict):
                            verified_url = company_data.get('crunchbase_company_url')
                            if verified_url:
                                verification_data['verified_crunchbase_url'] = verified_url
                                print(f"   ✅ Found user-verified Crunchbase URL: {verified_url}")

                    return {
                        'company_data': cached['company_data'],
                        'cache_age_days': age.days,
                        'last_fetched': cached['last_fetched'],
                        'verification_data': verification_data
                    }
                else:
                    print(f"⏰ Stored company too old ({age.days} days) - fetching fresh data")
                    return None

        return None

    except Exception as e:
        _handle_supabase_error("company retrieval", e)
        return None


def save_stored_company(company_id: int, company_data: Dict[str, Any]) -> bool:
    """
    Save company to storage for future cache hits.

    Uses Supabase's merge-duplicates preference to update existing records.

    Args:
        company_id: CoreSignal company ID
        company_data: Full company data from CoreSignal API

    Returns:
        bool: True if saved successfully, False otherwise

    Example:
        saved = save_stored_company(12345, company_data)
    """
    try:
        headers = _get_supabase_headers()
        headers['Prefer'] = 'resolution=merge-duplicates'

        data = {
            'company_id': company_id,
            'company_data': company_data
        }

        url = f"{SUPABASE_URL}/rest/v1/stored_companies"
        response = requests.post(url, json=data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            print(f"💾 Saved company to storage")
            return True
        else:
            print(f"⚠️  Failed to save company to cache: {response.status_code}")
            return False

    except Exception as e:
        _handle_supabase_error("company save", e)
        return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_storage_functions() -> Dict[str, callable]:
    """
    Get storage functions dict for passing to enrichment methods.

    Returns:
        dict: {'get': get_stored_company, 'save': save_stored_company}

    Example:
        storage_functions = get_storage_functions()
        enriched = service.enrich_profile_with_company_data(
            profile,
            storage_functions=storage_functions
        )
    """
    return {
        'get': get_stored_company,
        'save': save_stored_company
    }


def check_storage_health() -> Dict[str, Any]:
    """
    Check if Supabase storage is accessible and configured correctly.

    Returns:
        dict: Status information about storage health

    Example:
        health = check_storage_health()
        if health['status'] == 'healthy':
            print("Storage is operational")
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return {
                'status': 'error',
                'message': 'SUPABASE_URL or SUPABASE_KEY not configured'
            }

        headers = _get_supabase_headers()

        # Try to query stored_profiles table (just count)
        url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=count&limit=1"
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'Supabase storage is operational',
                'url': SUPABASE_URL
            }
        else:
            return {
                'status': 'error',
                'message': f'Supabase returned {response.status_code}',
                'url': SUPABASE_URL
            }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Connection failed: {str(e)}',
            'url': SUPABASE_URL
        }

# ==============================================================================
# Domain Search Caching Functions
# ==============================================================================

def generate_search_cache_key(jd_requirements, endpoint):
    """
    Generate a cache key from search parameters
    Uses MD5 hash of normalized search criteria
    """
    import hashlib

    # Normalize mentioned_companies to extract just names
    # (handles both old format: strings, and new format: dicts with IDs)
    mentioned_companies_raw = jd_requirements.get('mentioned_companies', [])
    company_names = []
    for item in mentioned_companies_raw:
        if isinstance(item, str):
            company_names.append(item)
        elif isinstance(item, dict):
            # Extract name from dict
            name = item.get('name', item.get('company_name', str(item)))
            company_names.append(name)
        else:
            company_names.append(str(item))

    # Normalize the search parameters
    cache_data = {
        'target_domain': jd_requirements.get('target_domain', ''),
        'mentioned_companies': sorted(company_names),  # Sort names for consistency
        'endpoint': endpoint
    }

    # Create hash
    cache_string = json.dumps(cache_data, sort_keys=True)
    cache_key = hashlib.md5(cache_string.encode()).hexdigest()
    return cache_key

def get_cached_search_results(cache_key, freshness_days=7):
    """
    Check if search results are cached and fresh
    Returns cached data if fresh, None if needs refresh
    """
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        url = f"{SUPABASE_URL}/rest/v1/cached_searches?cache_key=eq.{cache_key}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                cached = results[0]
                # Check freshness
                from datetime import datetime, timedelta, timezone
                last_fetched = datetime.fromisoformat(cached['created_at'].replace('Z', '+00:00'))
                age = datetime.now(last_fetched.tzinfo) - last_fetched

                if age.days < freshness_days:
                    print(f"✅ Using cached search results (age: {age.days} days) - SAVED API credits!")
                    return {
                        'stage1_companies': cached['stage1_companies'],
                        'stage2_previews': cached['stage2_previews'],
                        'session_id': cached.get('session_id'),
                        'from_cache': True,
                        'cache_age_days': age.days
                    }
                else:
                    print(f"⚠️ Cached search is {age.days} days old (>7 days) - fetching fresh results")
        return None
    except Exception as e:
        print(f"⚠️ Error checking cached search: {str(e)}")
        return None

def save_search_results(cache_key, stage1_companies, stage2_previews, session_id, jd_requirements, endpoint):
    """Save search results to cache"""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
        }

        data = {
            'cache_key': cache_key,
            'stage1_companies': stage1_companies,
            'stage2_previews': stage2_previews,
            'session_id': session_id,
            'search_params': {
                'jd_requirements': jd_requirements,
                'endpoint': endpoint
            }
        }

        url = f"{SUPABASE_URL}/rest/v1/cached_searches"
        response = requests.post(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            print(f"💾 Saved search results to cache")
            return True
        else:
            print(f"⚠️ Failed to save search to cache: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Error saving search to cache: {str(e)}")
        return False


# ==============================================================================
# Company Discovery Caching Functions (for Rate Limit Optimization)
# ==============================================================================

def get_cached_competitors(seed_company: str, freshness_days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Check if competitor discovery results are cached for a seed company.

    This caching prevents redundant Claude API calls when discovering competitors
    for commonly mentioned seed companies (e.g., Google, Meta, OpenAI).

    Args:
        seed_company: The company name we searched competitors for
        freshness_days: Maximum age in days before forcing refresh (default: 7)

    Returns:
        dict with discovered_companies list, or None if needs refresh

    Example:
        cached = get_cached_competitors("Google", freshness_days=7)
        if cached:
            competitors = cached['discovered_companies']
            print(f"Found {len(competitors)} cached competitors - saved 3 Claude API calls!")
    """
    try:
        headers = _get_supabase_headers()

        # Normalize to lowercase for case-insensitive matching
        normalized_seed = seed_company.lower()
        encoded_seed = urllib.parse.quote(normalized_seed, safe='')

        url = f"{SUPABASE_URL}/rest/v1/company_discovery_cache?seed_company=eq.{encoded_seed}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                cached = results[0]

                # Check freshness
                expires_at = datetime.fromisoformat(cached['expires_at'].replace('Z', '+00:00'))

                if datetime.now(expires_at.tzinfo) < expires_at:
                    created_at = datetime.fromisoformat(cached['created_at'].replace('Z', '+00:00'))
                    age = datetime.now(created_at.tzinfo) - created_at

                    print(f"   ✅ Cache hit for '{seed_company}' - {len(cached['discovered_companies'])} companies (age: {age.days} days)")
                    print(f"      SAVED 3 Claude API calls!")

                    return {
                        'discovered_companies': cached['discovered_companies'],
                        'search_queries': cached['search_queries'],
                        'cache_age_days': age.days
                    }
                else:
                    print(f"   ⏰ Cache expired for '{seed_company}' - refreshing")
                    # Delete expired cache entry
                    delete_url = f"{SUPABASE_URL}/rest/v1/company_discovery_cache?seed_company=eq.{encoded_seed}"
                    requests.delete(delete_url, headers=headers, timeout=5)

        print(f"   🔍 Cache miss for '{seed_company}' - running fresh discovery")
        return None

    except Exception as e:
        _handle_supabase_error("competitor cache retrieval", e, silent=True)
        return None


def save_cached_competitors(seed_company: str, discovered_companies: list, search_queries: list) -> bool:
    """
    Save competitor discovery results to cache.

    Args:
        seed_company: The company name we searched competitors for
        discovered_companies: List of discovered competitor companies
        search_queries: The 3 queries used for discovery (for debugging)

    Returns:
        bool: True if saved successfully, False otherwise

    Example:
        saved = save_cached_competitors(
            "Google",
            [{"name": "Microsoft", ...}, {"name": "Meta", ...}],
            ["Google competitors", "companies like Google", "Google alternatives"]
        )
    """
    try:
        headers = _get_supabase_headers()
        headers['Prefer'] = 'resolution=merge-duplicates'

        # Normalize to lowercase for case-insensitive matching
        normalized_seed = seed_company.lower()

        data = {
            'seed_company': normalized_seed,
            'discovered_companies': discovered_companies,
            'search_queries': search_queries,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }

        url = f"{SUPABASE_URL}/rest/v1/company_discovery_cache"
        response = requests.post(url, json=data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            print(f"   💾 Cached {len(discovered_companies)} competitors for '{seed_company}'")
            return True
        else:
            print(f"   ⚠️  Failed to cache competitors: {response.status_code}")
            return False

    except Exception as e:
        _handle_supabase_error("competitor cache save", e, silent=True)
        return False
