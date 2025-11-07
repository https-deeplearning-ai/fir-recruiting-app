"""
Domain Company-Based Candidate Search API

New endpoints for progressive candidate filtering:
1. Domain company discovery (use existing CompanyDiscoveryAgent)
2. Preview search (20 candidates to test quality)
3. Full profile collection (if quality is good)
4. AI evaluation (Gemini + Claude)

All stages have comprehensive logging with JSON + TXT outputs.

IMPORTANT: CoreSignal API field structures and query types vary by endpoint!
See backend/coresignal_api_taxonomy.py for correct field names and query types.
Key finding: Use 'match' not 'wildcard' for employee_base company searches.
"""

import os
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator
from flask import Blueprint, request, jsonify, Response, stream_with_context
import anthropic

# Adjust sys.path to allow imports from backend directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import existing agents
# Import SearchSessionManager for company batching
from utils.search_session import SearchSessionManager
from jd_analyzer.company.discovery_agent import CompanyDiscoveryAgent
from jd_analyzer.company.company_validation_agent import CompanyValidationAgent

# Import logging utility
from utils.session_logger import SessionLogger, format_company_list, format_preview_analysis

# Import Supabase storage functions for caching
from utils.supabase_storage import (
    get_stored_profile,
    save_stored_profile,
    get_stored_company,
    save_stored_company,
    generate_search_cache_key,
    get_cached_search_results,
    save_search_results
)

# Import CoreSignal service (will use for preview search and profile collection)
from coresignal_service import search_profiles_with_endpoint, CoreSignalService

# Import CoreSignal company lookup for company ID resolution
from coresignal_company_lookup import CoreSignalCompanyLookup

# Import config for credit costs
from config import CORESIGNAL_CREDIT_PER_FETCH, CORESIGNAL_CREDIT_USD

# Initialize Anthropic client for AI evaluation (lazy loading to prevent import crashes)
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
anthropic_client = None

def get_anthropic_client():
    """
    Lazy-load Anthropic client to prevent module import crashes.
    Only raises error when actually needed for a route.
    """
    global anthropic_client
    if anthropic_client is None:
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for this operation")
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    return anthropic_client

# Create Blueprint
domain_search_bp = Blueprint('domain_search', __name__)


# ========================================
# HELPER FUNCTIONS
# ========================================

def normalize_company_name(name: str) -> List[str]:
    """
    Generate multiple search variations for a company name.

    Args:
        name: Original company name

    Returns:
        List of normalized variations for searching
    """
    if not name:
        return []

    variations = []

    # Base name - remove common suffixes
    base = name.strip()
    for suffix in [', Inc.', ', Inc', ' Inc.', ' Inc', ', LLC', ' LLC',
                   ', Corp.', ' Corp.', ' Corporation', ', Ltd.', ' Ltd.',
                   ', Ltd', ' Limited', ' Co.', ', Co.']:
        if base.endswith(suffix):
            base = base[:-len(suffix)].strip()
            break

    # Add variations
    variations.append(base)  # Original without suffix
    variations.append(base.lower())  # Lowercase
    variations.append(base.replace(' ', '').lower())  # No spaces, lowercase (e.g., "Assembly AI" -> "assemblyai")
    variations.append(base.replace('.', '').lower())  # No dots (e.g., "Rev.ai" -> "revai")

    # If the original name is different from base, add it too
    if name != base:
        variations.append(name)
        variations.append(name.lower())

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for v in variations:
        if v and v not in seen:
            seen.add(v)
            unique_variations.append(v)

    return unique_variations


def is_valid_company_name(name: str) -> bool:
    """
    Heuristic filter to remove obvious non-company names.

    Args:
        name: Company name to validate

    Returns:
        True if likely a valid company name
    """
    if not name:
        return False

    # Minimum length
    if len(name) < 2:
        return False

    # Reject generic terms
    invalid_terms = {
        'api', 'apis', 'text', 'cloud', 'automatic', 'alternatives',
        'professional', 'dungeon', 'dragon', 'asr', 'stt', 'tts',
        'speech', 'voice', 'audio', 'language', 'translation',
        'processing', 'software', 'system', 'service', 'platform',
        'technology', 'solution', 'tool', 'application', 'product'
    }

    # Check if the name is just a generic term
    if name.lower().strip() in invalid_terms:
        return False

    # Reject if it's all uppercase and short (likely an acronym that's too generic)
    if name.isupper() and len(name) <= 3:
        return False

    return True


# ========================================
# STAGE 1: Domain Company Discovery
# ========================================

async def stage1_discover_companies(
    jd_requirements: Dict[str, Any],
    session_logger: SessionLogger
) -> List[Dict[str, Any]]:
    """
    Stage 1: Discover domain companies using CompanyDiscoveryAgent.

    Args:
        jd_requirements: Parsed JD requirements with domain, mentioned_companies
        session_logger: Session logger for this search

    Returns:
        List of discovered companies with name, source, confidence
    """
    print("\n" + "="*80)
    print("STAGE 1: Domain Company Discovery")
    print("="*80)

    start_time = time.time()

    # Extract discovery inputs from JD
    target_domain = jd_requirements.get('target_domain', jd_requirements.get('domain', ''))
    mentioned_companies = jd_requirements.get('mentioned_companies', [])
    competitor_context = jd_requirements.get('competitor_context', '')

    print(f"Domain: {target_domain}")
    print(f"Mentioned Companies: {mentioned_companies}")
    print(f"Context: {competitor_context}")

    # Initialize discovery agent
    agent = CompanyDiscoveryAgent()

    # Discover companies
    companies = await agent.discover_companies(
        mentioned_companies=mentioned_companies,
        target_domain=target_domain,
        context=competitor_context,
        max_per_seed=5,      # Get 5 competitors per seed company
        max_from_domain=20   # Get 20 from domain search
    )

    duration = time.time() - start_time

    # Prepare structured log data
    log_data = {
        "stage": "company_discovery",
        "input": {
            "target_domain": target_domain,
            "mentioned_companies": mentioned_companies,
            "context": competitor_context
        },
        "output": {
            "companies": companies,
            "total_count": len(companies),
            "by_source": {
                "mentioned": len([c for c in companies if c['source'] == 'mentioned']),
                "seed_expansion": len([c for c in companies if c['source'] == 'seed_expansion']),
                "domain_discovery": len([c for c in companies if c['source'] == 'domain_discovery'])
            }
        },
        "duration_seconds": round(duration, 2)
    }

    # Prepare human-readable debug text
    debug_text = f"""DOMAIN COMPANY DISCOVERY RESULTS
{"="*50}
Domain: {target_domain}
Context: {competitor_context}
Total Found: {len(companies)} companies

BY SOURCE:
  Mentioned (from JD): {log_data['output']['by_source']['mentioned']}
  Seed Expansion: {log_data['output']['by_source']['seed_expansion']}
  Domain Discovery: {log_data['output']['by_source']['domain_discovery']}

FULL LIST (sorted by confidence):
"""

    # Add sorted company list
    sorted_companies = sorted(companies, key=lambda c: c.get('confidence', 0), reverse=True)
    for i, company in enumerate(sorted_companies, 1):
        name = company.get('name', 'Unknown')
        source = company.get('source', 'unknown')
        confidence = company.get('confidence', 0)
        debug_text += f"  {i:2d}. {name:40s} ({source}, {confidence:.2f})\n"

    # Write logs
    session_logger.log_stage(1, "company_discovery", log_data, debug_text)

    # First pass: Heuristic filtering
    print(f"\n📋 Applying heuristic filters...")
    heuristic_filtered = []
    heuristic_rejected = []

    for company in companies:
        name = company.get('name', '')
        if is_valid_company_name(name):
            heuristic_filtered.append(company)
        else:
            heuristic_rejected.append(name)

    print(f"   Heuristic filter: {len(heuristic_filtered)} passed, {len(heuristic_rejected)} rejected")
    if heuristic_rejected:
        print(f"   Rejected terms: {', '.join(heuristic_rejected[:10])}")

    # AI Validation: Use Claude to intelligently filter companies
    print(f"\n🤖 Validating companies with AI (Claude Haiku 4.5)...")
    validation_agent = CompanyValidationAgent()
    validated_companies = await validation_agent.validate_and_filter(
        discovered_companies=heuristic_filtered,  # Only validate companies that passed heuristic filter
        target_domain=target_domain,
        min_relevance="low"  # Accept low/medium/high relevance
    )

    # Transform validated companies: rename 'company_name' to 'name' for compatibility
    for company in validated_companies:
        if 'company_name' in company and 'name' not in company:
            company['name'] = company['company_name']

    removed_count = len(companies) - len(validated_companies)
    print(f"   ✅ Final validation: {len(validated_companies)} companies")
    print(f"   ❌ Total rejected: {removed_count} ({len(heuristic_rejected)} by heuristics, {len(heuristic_filtered) - len(validated_companies)} by AI)")

    # CoreSignal Company ID Lookup
    print(f"\n🔍 Looking up CoreSignal company IDs...")
    company_lookup = CoreSignalCompanyLookup()

    companies_with_ids = []
    companies_without_ids = []

    for company in validated_companies:
        company_name = company.get('name', company.get('company_name', ''))

        if not company_name:
            companies_without_ids.append(company)
            continue

        # Look up company ID with confidence threshold of 0.75
        match = company_lookup.get_best_match(company_name, confidence_threshold=0.75)

        if match:
            # Enrich company with CoreSignal data
            company['coresignal_company_id'] = match['company_id']
            company['coresignal_confidence'] = match['confidence']
            company['coresignal_searchable'] = True
            if match.get('employee_count'):
                company['employee_count'] = match['employee_count']
            if match.get('website'):
                company['website'] = match['website']
            companies_with_ids.append(company)
            print(f"   ✅ {company_name}: ID={match['company_id']} (confidence: {match['confidence']:.2f})")
        else:
            # No match found - mark as not searchable by ID
            company['coresignal_searchable'] = False
            companies_without_ids.append(company)
            print(f"   ❌ {company_name}: No CoreSignal ID found")

    # Calculate searchability coverage
    coverage_percent = (len(companies_with_ids) / len(validated_companies) * 100) if validated_companies else 0

    print(f"\n📊 CoreSignal Coverage:")
    print(f"   Searchable (with IDs): {len(companies_with_ids)} companies")
    print(f"   Not searchable (no IDs): {len(companies_without_ids)} companies")
    print(f"   Coverage: {coverage_percent:.1f}%")

    # Log enhanced company data
    enhanced_log_data = {
        "stage": "company_id_lookup",
        "searchable_companies": companies_with_ids,
        "non_searchable_companies": companies_without_ids,
        "coverage": {
            "with_ids": len(companies_with_ids),
            "without_ids": len(companies_without_ids),
            "percentage": round(coverage_percent, 1)
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    session_logger.log_json("01_company_ids.json", enhanced_log_data)

    validation_duration = time.time() - start_time
    print(f"\n✓ Stage 1 Complete ({validation_duration:.1f}s)")
    print(f"  Discovered: {len(companies)} companies")
    print(f"  AI Validated: {len(validated_companies)} companies")
    print(f"  Searchable: {len(companies_with_ids)} companies")
    print(f"  Log: {session_logger.session_dir}/01_company_discovery.json")

    # Return all validated companies (with and without IDs)
    # The query builder will handle them differently
    return validated_companies


# ========================================
# STAGE 2: Preview Search (20 Candidates)
# ========================================

def build_domain_company_query(
    companies: List[Dict[str, Any]],
    role_keywords: List[str],
    location: str = "United States",
    require_current_role: bool = False
) -> Dict[str, Any]:
    """
    Build Elasticsearch DSL query for candidates who worked at domain companies.

    Args:
        companies: List of company dicts with 'name' field
        role_keywords: Basic role keywords (engineer, founder, CEO, product)
        location: Location filter (default: United States)
        require_current_role: If True, require role keywords in current position (more restrictive)

    Returns:
        Elasticsearch DSL query dict
    """
    # Build company filters - use company IDs when available, fall back to name search
    company_id_filters = []
    company_name_filters = []

    print(f"[DEBUG] Building query for {len(companies)} companies")

    for i, company in enumerate(companies):
        company_name = company.get('name', '')
        company_id = company.get('coresignal_company_id')

        print(f"[DEBUG] Company {i+1}: '{company_name}' (ID: {company_id if company_id else 'None'})")

        if company_id:
            # Use exact company ID match (FAST and PRECISE)
            company_id_filters.append({
                "term": {"last_company_id": company_id}  # Current employer
            })
            print(f"[DEBUG]   Using company ID: {company_id}")
        else:
            # Fall back to name-based search (SLOWER but works for all)
            variations = normalize_company_name(company_name)
            print(f"[DEBUG]   No ID, using name variations: {variations}")

            # CRITICAL: Use 'match' not 'wildcard' for employee_base /preview endpoint
            # See coresignal_api_taxonomy.py for details
            for variant in variations:
                if variant:  # Skip empty strings
                    company_name_filters.append({
                        "match": {"experience.company_name": variant}
                    })

    # Combine both filter types
    company_filters = company_id_filters + company_name_filters

    print(f"[DEBUG] Total filters: {len(company_filters)} (IDs: {len(company_id_filters)}, Names: {len(company_name_filters)})")

    # Build role filters (more selective keywords)
    # Remove overly broad terms like "mid"
    filtered_keywords = []
    for keyword in role_keywords:
        # Skip terms that are too broad
        if keyword.lower() not in ['mid', 'senior', 'junior', 'staff', 'principal']:
            filtered_keywords.append(keyword)

    role_filters = []
    for keyword in filtered_keywords:
        # Search in both current and past titles
        role_filters.append({
            "wildcard": {"active_experience_title": f"*{keyword.lower()}*"}
        })
        # Also search in experience titles (past roles)
        role_filters.append({
            "nested": {
                "path": "experience",
                "query": {
                    "wildcard": {"experience.title": f"*{keyword.lower()}*"}
                }
            }
        })

    # Build the query - combine ID and name searches
    must_clauses = []

    # Build company filter combining both ID and name searches
    if company_filters:
        # Separate ID filters and name filters for different handling
        if company_id_filters and company_name_filters:
            # If we have both types, use should to match either
            must_clauses.append({
                "bool": {
                    "should": [
                        # ID-based search (for current employer)
                        {
                            "bool": {
                                "should": company_id_filters,
                                "minimum_should_match": 1
                            }
                        },
                        # Name-based search (nested for experience history)
                        {
                            "nested": {
                                "path": "experience",
                                "query": {
                                    "bool": {
                                        "should": company_name_filters,
                                        "minimum_should_match": 1
                                    }
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            })
        elif company_id_filters:
            # Only ID filters - use direct term queries
            must_clauses.append({
                "bool": {
                    "should": company_id_filters,
                    "minimum_should_match": 1
                }
            })
        elif company_name_filters:
            # Only name filters - use nested query
            must_clauses.append({
                "nested": {
                    "path": "experience",
                    "query": {
                        "bool": {
                            "should": company_name_filters,
                            "minimum_should_match": 1
                        }
                    }
                }
            })
        else:
            print("[WARNING] No company filters created!")

    # Optionally require role keywords (make it less restrictive)
    if require_current_role and role_filters:
        must_clauses.append({
            "bool": {
                "should": role_filters,
                "minimum_should_match": 1
            }
        })

    query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    # Build "should" clause for optional boosting
    should_clause = []

    # Add location as optional boost (not required)
    if location:
        should_clause.append({"term": {"location_country": location}})

    # If not requiring current role, add role filters as a "should" for boosting
    if not require_current_role and role_filters:
        should_clause.extend(role_filters)

    # Add should clause to query if we have any
    if should_clause:
        query["query"]["bool"]["should"] = should_clause
        query["query"]["bool"]["minimum_should_match"] = 0  # Don't require any should matches

    return query


async def stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    session_logger: SessionLogger,
    create_session: bool = True,
    session_id: Optional[str] = None,
    batch_size: int = 5
) -> Dict[str, Any]:
    """
    Stage 2: Preview search to test query quality with company batching support.

    Args:
        companies: Discovered companies from Stage 1
        jd_requirements: Parsed JD requirements
        endpoint: CoreSignal endpoint (employee_base, employee_clean, multi_source_employee)
        max_previews: Number of previews to fetch (default: 20)
        session_logger: Session logger
        create_session: Whether to create a new search session (default: True)
        session_id: Existing session ID to continue from
        batch_size: Number of companies per batch (default: 5)

    Returns:
        Dict with previews, relevance_score, session_id, etc.
    """
    print("\n" + "="*80)
    print("STAGE 2: Preview Search (with Company Batching)")
    print("="*80)

    start_time = time.time()

    # Initialize session manager
    session_manager = SearchSessionManager()

    # Handle session creation or continuation
    current_session_id = session_id
    companies_to_search = companies

    if create_session and not session_id:
        # Create new session with company batching
        company_names = [c['name'] for c in companies]

        # Build base query for the session
        base_query = {
            "jd_requirements": jd_requirements,
            "endpoint": endpoint,
            "max_previews": max_previews
        }

        session_data = session_manager.create_session(
            search_query=base_query,
            companies=company_names,
            batch_size=batch_size
        )

        current_session_id = session_data['session_id']
        companies_to_search = [{'name': c} for c in session_data['first_batch']]

        print(f"✅ Created session: {current_session_id}")
        print(f"   Total batches: {session_data['total_batches']}")
        print(f"   First batch: {session_data['first_batch']}")

    elif session_id:
        # Continue existing session - get next batch
        next_batch = session_manager.get_next_batch(session_id)
        if not next_batch:
            print(f"⚠️  No more batches available for session {session_id}")
            return {
                "previews": [],
                "relevance_score": 0.0,
                "total_found": 0,
                "session_id": session_id,
                "message": "No more company batches available"
            }

        companies_to_search = [{'name': c} for c in next_batch]
        current_session_id = session_id

    # Extract role keywords from JD
    role_title = jd_requirements.get('role_title', '')
    seniority = jd_requirements.get('seniority_level', '')

    # Build role keywords (broader set - removed ceo/president/executive to avoid over-restriction)
    role_keywords = [
        "engineer", "developer", "architect",  # Technical roles
        "product", "manager", "director",       # Mid-level roles
        "founder", "lead"                        # Startup roles
    ]

    # Add specific role from JD
    if role_title:
        role_keywords.extend(role_title.lower().split())

    # Add seniority
    if seniority:
        role_keywords.append(seniority.lower())

    # Remove duplicates
    role_keywords = list(set(role_keywords))

    print(f"Companies: {len(companies_to_search)} (batch)")
    print(f"Role Keywords: {role_keywords}")
    print(f"Endpoint: {endpoint}")

    # Build query (start with less restrictive version)
    query = build_domain_company_query(
        companies=companies_to_search,
        role_keywords=role_keywords,
        location="United States",
        require_current_role=False  # Don't require current role match initially
    )

    # Log query
    query_log_data = {
        "stage": "preview_search_query",
        "session_id": current_session_id,
        "input": {
            "endpoint": endpoint,
            "num_companies": len(companies_to_search),
            "batch_companies": [c['name'] for c in companies_to_search],
            "role_keywords": role_keywords,
            "location": "United States"
        },
        "query": query,
        "duration_seconds": round(time.time() - start_time, 2)
    }
    session_logger.log_json("02_preview_query.json", query_log_data)

    # Execute search via CoreSignal API
    print(f"\n📡 Executing CoreSignal search...")
    search_result = search_profiles_with_endpoint(
        query=query,
        endpoint=endpoint,
        max_results=max_previews
    )

    duration = time.time() - start_time

    if not search_result.get('success'):
        error_msg = search_result.get('error', 'Unknown error')
        print(f"   ❌ CoreSignal search failed: {error_msg}")
        return {
            "previews": [],
            "relevance_score": 0.0,
            "total_found": 0,
            "session_id": current_session_id,
            "error": error_msg
        }

    # Parse results
    previews = search_result.get('results', [])
    print(f"   ✅ Found {len(previews)} preview candidates")

    # Extract employee IDs and add to session
    if previews and current_session_id:
        employee_ids = []
        for candidate in previews:
            if isinstance(candidate, dict):
                # Try multiple field names based on endpoint format
                # employee_clean uses 'id', employee_base might use 'employee_id' or 'member_id'
                emp_id = None
                for field in ['id', 'employee_id', 'member_id']:
                    if field in candidate and candidate[field]:
                        emp_id = candidate[field]
                        break

                if emp_id:
                    try:
                        # Ensure it's an integer
                        employee_ids.append(int(emp_id))
                    except (ValueError, TypeError):
                        print(f"   ⚠️  Invalid employee ID format: {emp_id}")

        if employee_ids:
            session_manager.add_discovered_ids(current_session_id, employee_ids)
            print(f"   📊 Added {len(employee_ids)} IDs to session")

    # Analyze relevance: Check how many have domain company experience
    domain_match_count = 0
    company_names_lower = [c['name'].lower() for c in companies_to_search]

    for candidate in previews:
        # Check if candidate worked at any domain company
        # Results structure depends on endpoint (IDs vs full profiles)
        if isinstance(candidate, dict):
            # Full profile with experience data
            experiences = candidate.get('experience', [])
            for exp in experiences:
                company_name = exp.get('company_name', '').lower()
                if any(domain_comp in company_name for domain_comp in company_names_lower):
                    domain_match_count += 1
                    break

    relevance_score = domain_match_count / len(previews) if previews else 0.0
    print(f"   📊 Relevance: {domain_match_count}/{len(previews)} ({relevance_score*100:.0f}%) with domain company experience")

    # Prepare results log
    results_log_data = {
        "stage": "preview_results",
        "candidates": previews,
        "total_candidates": len(previews),
        "relevance_score": relevance_score,
        "duration_seconds": round(duration, 2)
    }
    session_logger.log_json("02_preview_results.json", results_log_data)

    # Prepare analysis text
    analysis_text = f"""PREVIEW SEARCH QUALITY ANALYSIS
{"="*50}
Total Candidates: {len(previews)}
Endpoint Used: {endpoint}

Query Configuration:
  Companies Targeted: {len(companies)}
  Role Keywords: {', '.join(role_keywords)}
  Location: United States

RELEVANCE BREAKDOWN:
  (Analysis will be added after CoreSignal integration)

QUALITY SCORE: {relevance_score*100:.0f}%
RECOMMENDATION: (To be determined after integration)
"""
    session_logger.log_text("02_preview_analysis.txt", analysis_text)

    print(f"\n✓ Stage 2 Complete ({duration:.1f}s)")
    print(f"  Found {len(previews)} preview candidates")
    print(f"  Quality Score: {relevance_score*100:.0f}%")
    print(f"  Session ID: {current_session_id}")

    # Get session stats if available
    session_stats = {}
    if current_session_id:
        stats = session_manager.get_session_stats(current_session_id)
        session_stats = {
            "total_discovered": stats.get('discovered_ids', 0),
            "batches_completed": stats.get('batches_completed', 0),
            "total_batches": stats.get('total_batches', 0)
        }

    return {
        "previews": previews,
        "relevance_score": relevance_score,
        "total_found": len(previews),
        "session_id": current_session_id,
        "session_stats": session_stats
    }


async def stage3_collect_full_profiles(
    preview_candidates: List[Dict[str, Any]],
    session_logger: SessionLogger,
    min_year: int = 2020
) -> Dict[str, Any]:
    """
    Stage 3: Collect full LinkedIn profiles for preview candidates.

    This function:
    1. Extracts employee IDs from preview candidates
    2. Fetches full profiles using fetch_linkedin_profile_by_id()
    3. Enriches profiles with company data (2020+ filter)
    4. Logs all progress to session directory

    Args:
        preview_candidates: List of candidate dicts from Stage 2 (each has 'id' field)
        session_logger: Session logger for traceability
        min_year: Only enrich companies from this year onwards (default: 2020)

    Returns:
        Dict with collected profiles, metrics, and failures
    """
    print("\n" + "="*80)
    print("STAGE 3: Full Profile Collection")
    print("="*80)

    start_time = time.time()

    # Initialize CoreSignal service
    service = CoreSignalService()

    # Extract employee IDs from preview candidates
    employee_ids = []
    for candidate in preview_candidates:
        # Preview candidates have 'id' field (employee_id from CoreSignal)
        employee_id = candidate.get('id')
        if employee_id:
            employee_ids.append(employee_id)

    print(f"\nCollecting {len(employee_ids)} full profiles...")

    # Track progress
    collected_profiles = []
    failed_profiles = []

    for i, employee_id in enumerate(employee_ids, 1):
        print(f"\n  [{i}/{len(employee_ids)}] Fetching employee ID: {employee_id}")

        # Log progress to JSONL (streaming log)
        session_logger.log_jsonl("03_collection_progress.jsonl", {
            "event": "profile_fetch_start",
            "employee_id": employee_id,
            "index": i,
            "total": len(employee_ids),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

        # Check cache first (profiles cached by employee_id)
        cache_key = f"id:{employee_id}"
        cached_profile = get_stored_profile(cache_key)

        if cached_profile:
            # Cache hit! Use stored profile
            result = {
                'success': True,
                'profile_data': cached_profile['profile_data'],
                'from_cache': True,
                'cache_age_days': cached_profile['storage_age_days']
            }
            profile = cached_profile['profile_data']
        else:
            # Cache miss - fetch from API
            result = service.fetch_linkedin_profile_by_id(employee_id)

            if result.get('success'):
                profile = result['profile_data']
                # Save to cache for future searches
                save_stored_profile(cache_key, profile, time.time())
                result['from_cache'] = False
            else:
                # Profile fetch failed
                profile = None

        if result.get('success') and profile:
            # Enrich with company data (2020+ only to save API credits)
            print(f"    Enriching with company data (min_year={min_year})...")

            # Pass storage functions for company caching
            storage_functions = {
                'get': get_stored_company,
                'save': save_stored_company
            }
            enriched = service.enrich_profile_with_company_data(
                profile,
                min_year=min_year,
                storage_functions=storage_functions
            )

            collected_profiles.append({
                "employee_id": employee_id,
                "full_name": profile.get('full_name'),
                "headline": profile.get('headline'),
                "generated_headline": profile.get('generated_headline'),
                "profile_data": enriched['profile_data'],
                "enrichment_summary": enriched['enrichment_summary'],
                "cache_info": {
                    "profile_from_cache": result.get('from_cache', False),
                    "profile_cache_age_days": result.get('cache_age_days', 0),
                    "companies_from_cache": enriched['enrichment_summary'].get('companies_cached', 0),
                    "companies_fetched": enriched['enrichment_summary'].get('api_calls_made', 0)
                }
            })

            # Log success to JSONL
            session_logger.log_jsonl("03_collection_progress.jsonl", {
                "event": "profile_collected",
                "employee_id": employee_id,
                "full_name": profile.get('full_name'),
                "companies_enriched": enriched['enrichment_summary']['companies_enriched'],
                "api_calls": enriched['enrichment_summary']['api_calls_made'],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

            print(f"    ✓ Collected and enriched")
        else:
            failed_profiles.append({
                "employee_id": employee_id,
                "error": result.get('error')
            })

            # Log failure to JSONL
            session_logger.log_jsonl("03_collection_progress.jsonl", {
                "event": "profile_failed",
                "employee_id": employee_id,
                "error": result.get('error'),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

            print(f"    ✗ Failed: {result.get('error')}")

        # Rate limiting: 18 req/sec, use 0.1s = 10 req/sec to be safe
        await asyncio.sleep(0.1)

    duration = time.time() - start_time

    # Prepare final Stage 3 results
    stage3_results = {
        "stage": "full_profile_collection",
        "input": {
            "employee_ids": employee_ids,
            "requested_count": len(employee_ids),
            "min_year_filter": min_year
        },
        "output": {
            "collected_count": len(collected_profiles),
            "failed_count": len(failed_profiles),
            "profiles": collected_profiles,
            "failures": failed_profiles
        },
        "metrics": {
            "duration_seconds": round(duration, 2),
            "profiles_per_second": round(len(collected_profiles) / duration, 2) if duration > 0 else 0,
            "total_api_calls": sum(p['enrichment_summary']['api_calls_made'] for p in collected_profiles),
            "total_companies_enriched": sum(p['enrichment_summary']['companies_enriched'] for p in collected_profiles),
            "cache_stats": {
                "profiles_from_cache": sum(1 for p in collected_profiles if p.get('cache_info', {}).get('profile_from_cache', False)),
                "profiles_fetched": sum(1 for p in collected_profiles if not p.get('cache_info', {}).get('profile_from_cache', False)),
                "companies_from_cache": sum(p.get('cache_info', {}).get('companies_from_cache', 0) for p in collected_profiles),
                "companies_fetched": sum(p.get('cache_info', {}).get('companies_fetched', 0) for p in collected_profiles)
            },
            "credit_usage": {
                "profiles_fetched": sum(1 for p in collected_profiles if not p.get('cache_info', {}).get('profile_from_cache', False)),
                "companies_fetched": sum(p.get('cache_info', {}).get('companies_fetched', 0) for p in collected_profiles),
                "profiles_cached": sum(1 for p in collected_profiles if p.get('cache_info', {}).get('profile_from_cache', False)),
                "companies_cached": sum(p.get('cache_info', {}).get('companies_from_cache', 0) for p in collected_profiles),
                "credits_used": sum(1 for p in collected_profiles if not p.get('cache_info', {}).get('profile_from_cache', False)) + sum(p.get('cache_info', {}).get('companies_fetched', 0) for p in collected_profiles),
                "credits_saved": sum(1 for p in collected_profiles if p.get('cache_info', {}).get('profile_from_cache', False)) + sum(p.get('cache_info', {}).get('companies_from_cache', 0) for p in collected_profiles),
                "cost_usd": (sum(1 for p in collected_profiles if not p.get('cache_info', {}).get('profile_from_cache', False)) + sum(p.get('cache_info', {}).get('companies_fetched', 0) for p in collected_profiles)) * CORESIGNAL_CREDIT_USD
            }
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Write final results
    session_logger.log_json("03_full_profiles.json", stage3_results)

    # Write human-readable summary
    summary_lines = []
    summary_lines.append("STAGE 3: FULL PROFILE COLLECTION")
    summary_lines.append("="*60)
    summary_lines.append(f"Session ID: {session_logger.session_id}")
    summary_lines.append(f"Timestamp: {stage3_results['timestamp']}")
    summary_lines.append("")
    summary_lines.append("RESULTS:")
    summary_lines.append(f"  Requested: {len(employee_ids)} profiles")
    summary_lines.append(f"  Collected: {len(collected_profiles)} profiles")
    summary_lines.append(f"  Failed: {len(failed_profiles)} profiles")
    summary_lines.append(f"  Success Rate: {len(collected_profiles)/len(employee_ids)*100:.0f}%" if employee_ids else "  Success Rate: N/A")
    summary_lines.append("")
    summary_lines.append("PERFORMANCE:")
    summary_lines.append(f"  Duration: {duration:.2f}s")
    summary_lines.append(f"  Throughput: {stage3_results['metrics']['profiles_per_second']:.2f} profiles/sec")
    summary_lines.append(f"  Total API Calls: {stage3_results['metrics']['total_api_calls']}")
    summary_lines.append(f"  Companies Enriched: {stage3_results['metrics']['total_companies_enriched']}")
    summary_lines.append("")

    # Cache performance section
    cache_stats = stage3_results['metrics']['cache_stats']
    total_profiles = len(collected_profiles)
    profiles_cached = cache_stats['profiles_from_cache']
    profiles_fetched = cache_stats['profiles_fetched']
    companies_cached = cache_stats['companies_from_cache']
    companies_fetched = cache_stats['companies_fetched']
    total_companies = companies_cached + companies_fetched

    summary_lines.append("CACHE PERFORMANCE:")
    if total_profiles > 0:
        profile_cache_rate = (profiles_cached / total_profiles) * 100
        summary_lines.append(f"  Profiles from cache: {profiles_cached}/{total_profiles} ({profile_cache_rate:.0f}%)")
        summary_lines.append(f"  Profiles fetched: {profiles_fetched}/{total_profiles} ({100-profile_cache_rate:.0f}%)")
    else:
        summary_lines.append(f"  Profiles from cache: 0/0 (0%)")
        summary_lines.append(f"  Profiles fetched: 0/0 (0%)")

    if total_companies > 0:
        company_cache_rate = (companies_cached / total_companies) * 100
        summary_lines.append(f"  Companies from cache: {companies_cached}/{total_companies} ({company_cache_rate:.0f}%)")
        summary_lines.append(f"  Companies fetched: {companies_fetched}/{total_companies} ({100-company_cache_rate:.0f}%)")

        # Calculate credit savings
        # Profile fetch = 1 credit, Company fetch = 1 credit
        credits_used = profiles_fetched + companies_fetched
        credits_saved = profiles_cached + companies_cached
        total_credits_without_cache = profiles_fetched + profiles_cached + companies_fetched + companies_cached

        if total_credits_without_cache > 0:
            savings_pct = (credits_saved / total_credits_without_cache) * 100
            cost_usd = credits_used * CORESIGNAL_CREDIT_USD
            saved_usd = credits_saved * CORESIGNAL_CREDIT_USD
            total_cost_usd = total_credits_without_cache * CORESIGNAL_CREDIT_USD

            summary_lines.append("")
            summary_lines.append("API CREDIT USAGE & COST:")
            summary_lines.append(f"  Credits used: {credits_used} credits (${ cost_usd:.2f} USD)")
            summary_lines.append(f"    - Profiles fetched: {profiles_fetched} credits")
            summary_lines.append(f"    - Companies fetched: {companies_fetched} credits")
            summary_lines.append(f"  Credits saved by cache: {credits_saved} credits (${saved_usd:.2f} USD)")
            summary_lines.append(f"    - Profiles cached: {profiles_cached} credits")
            summary_lines.append(f"    - Companies cached: {companies_cached} credits")
            summary_lines.append(f"  Cache efficiency: {savings_pct:.0f}% savings")
            summary_lines.append(f"  Total session cost: ${cost_usd:.2f} USD (vs ${total_cost_usd:.2f} without cache)")
    else:
        summary_lines.append(f"  Companies from cache: 0/0 (0%)")
        summary_lines.append(f"  Companies fetched: 0/0 (0%)")

    summary_lines.append("")
    summary_lines.append("COLLECTED PROFILES:")
    for i, profile in enumerate(collected_profiles, 1):
        summary_lines.append(f"  {i}. {profile['full_name']}")
        headline = profile.get('generated_headline') or profile.get('headline') or 'N/A'
        summary_lines.append(f"     {headline[:70]}...")
        enrichment = profile['enrichment_summary']
        summary_lines.append(f"     Enriched: {enrichment['companies_enriched']} companies, {enrichment['api_calls_made']} API calls")

    if failed_profiles:
        summary_lines.append("")
        summary_lines.append("FAILED PROFILES:")
        for i, failure in enumerate(failed_profiles, 1):
            summary_lines.append(f"  {i}. ID {failure['employee_id']}: {failure['error']}")

    summary_text = "\n".join(summary_lines)
    session_logger.log_text("03_collection_summary.txt", summary_text)

    print(f"\n✓ Stage 3 Complete ({duration:.1f}s)")
    print(f"  Collected {len(collected_profiles)}/{len(employee_ids)} profiles")
    print(f"  Enriched {stage3_results['metrics']['total_companies_enriched']} companies")
    print(f"  API calls: {stage3_results['metrics']['total_api_calls']}")

    return stage3_results


def stage4_evaluate_candidates_stream(
    collected_profiles: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    session_logger: SessionLogger
) -> Generator[str, None, None]:
    """
    Stage 4: AI Evaluation of collected profiles (STREAMING).

    This function evaluates each candidate profile against JD requirements using
    Claude Sonnet 4.5 and streams progress updates via Server-Sent Events.

    Args:
        collected_profiles: List of profile dicts from Stage 3 (with enrichment)
        jd_requirements: Parsed JD requirements
        session_logger: Session logger for traceability

    Yields:
        SSE formatted strings with evaluation progress and results
    """
    print("\n" + "="*80)
    print("STAGE 4: AI Evaluation (Streaming)")
    print("="*80)

    start_time = time.time()

    # Send initial event
    yield f"data: {json.dumps({'event': 'stage4_start', 'total': len(collected_profiles)})}\n\n"

    # Extract JD context for evaluation
    role_title = jd_requirements.get('role_title', 'Target Role')
    target_domain = jd_requirements.get('target_domain', '')
    must_have = jd_requirements.get('must_have', [])
    nice_to_have = jd_requirements.get('nice_to_have', [])

    # Build evaluation criteria from JD
    criteria_text = f"""
**Target Role:** {role_title}
**Domain:** {target_domain}

**Must-Have Requirements:**
{chr(10).join(f'- {item}' for item in must_have) if must_have else '- Not specified'}

**Nice-to-Have:**
{chr(10).join(f'- {item}' for item in nice_to_have) if nice_to_have else '- Not specified'}
"""

    evaluated_candidates = []
    failed_evaluations = []

    for i, profile in enumerate(collected_profiles, 1):
        candidate_name = profile.get('full_name', 'Unknown')
        employee_id = profile.get('employee_id')

        # Send progress event
        yield f"data: {json.dumps({'event': 'evaluating', 'index': i, 'total': len(collected_profiles), 'name': candidate_name})}\n\n"

        print(f"\n  [{i}/{len(collected_profiles)}] Evaluating: {candidate_name}")

        try:
            # Extract profile data
            profile_data = profile['profile_data']
            headline = profile.get('generated_headline') or profile.get('headline') or 'N/A'

            # Build experience summary
            experience_items = []
            for exp in profile_data.get('experience', [])[:5]:  # Top 5 experiences
                title = exp.get('title', 'N/A')
                company = exp.get('company_name', 'N/A')
                start = exp.get('date_start', 'Unknown')
                end = exp.get('date_end', 'Present')
                experience_items.append(f"- {title} at {company} ({start} - {end})")

            experience_summary = "\n".join(experience_items) if experience_items else "No experience data"

            # Build evaluation prompt
            evaluation_prompt = f"""You are evaluating a candidate for the following role:

{criteria_text}

**Candidate Profile:**
- Name: {candidate_name}
- Headline: {headline}

**Recent Experience:**
{experience_summary}

Please evaluate this candidate on a scale of 1-10 for:
1. **Domain Fit** (0-10): Relevance to {target_domain}
2. **Experience Match** (0-10): Alignment with must-have requirements
3. **Overall Fit** (0-10): Holistic assessment

Provide your evaluation in the following JSON format:
{{
    "domain_fit_score": <0-10>,
    "experience_match_score": <0-10>,
    "overall_fit_score": <0-10>,
    "strengths": ["strength 1", "strength 2"],
    "concerns": ["concern 1", "concern 2"],
    "recommendation": "STRONG_FIT | GOOD_FIT | MODERATE_FIT | WEAK_FIT",
    "summary": "1-2 sentence evaluation summary"
}}"""

            # Call Claude API
            message = get_anthropic_client().messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent evaluation
                messages=[{"role": "user", "content": evaluation_prompt}]
            )

            # Parse Claude's response
            response_text = message.content[0].text

            # Extract JSON from response (handle code blocks)
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

            evaluation = json.loads(json_str)

            # Add to evaluated candidates
            evaluated_candidates.append({
                "employee_id": employee_id,
                "full_name": candidate_name,
                "headline": headline,
                "evaluation": evaluation,
                "profile_summary": {
                    "recent_experience": experience_items[:3]
                }
            })

            # Send success event
            yield f"data: {json.dumps({'event': 'evaluated', 'index': i, 'name': candidate_name, 'overall_score': evaluation.get('overall_fit_score'), 'recommendation': evaluation.get('recommendation')})}\n\n"

            print(f"    ✓ Evaluated: Overall {evaluation.get('overall_fit_score')}/10 - {evaluation.get('recommendation')}")

        except Exception as e:
            error_msg = str(e)
            print(f"    ✗ Evaluation failed: {error_msg}")

            failed_evaluations.append({
                "employee_id": employee_id,
                "full_name": candidate_name,
                "error": error_msg
            })

            # Send error event
            yield f"data: {json.dumps({'event': 'evaluation_error', 'index': i, 'name': candidate_name, 'error': error_msg})}\n\n"

        # Rate limiting for Claude API (50 req/min = 1.2 sec/req)
        time.sleep(1.5)

    duration = time.time() - start_time

    # Sort by overall fit score (descending)
    evaluated_candidates.sort(key=lambda x: x['evaluation'].get('overall_fit_score', 0), reverse=True)

    # Prepare final Stage 4 results
    stage4_results = {
        "stage": "ai_evaluation",
        "input": {
            "candidates_count": len(collected_profiles),
            "jd_criteria": criteria_text
        },
        "output": {
            "evaluated_count": len(evaluated_candidates),
            "failed_count": len(failed_evaluations),
            "evaluations": evaluated_candidates,
            "failures": failed_evaluations
        },
        "metrics": {
            "duration_seconds": round(duration, 2),
            "evaluations_per_minute": round(len(evaluated_candidates) / (duration / 60), 2) if duration > 0 else 0
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Write final results
    session_logger.log_json("04_ai_evaluations.json", stage4_results)

    # Write human-readable summary
    summary_lines = []
    summary_lines.append("STAGE 4: AI EVALUATION")
    summary_lines.append("="*60)
    summary_lines.append(f"Session ID: {session_logger.session_id}")
    summary_lines.append(f"Timestamp: {stage4_results['timestamp']}")
    summary_lines.append("")
    summary_lines.append("RESULTS:")
    summary_lines.append(f"  Candidates Evaluated: {len(evaluated_candidates)}")
    summary_lines.append(f"  Failed: {len(failed_evaluations)}")
    summary_lines.append(f"  Success Rate: {len(evaluated_candidates)/len(collected_profiles)*100:.0f}%" if collected_profiles else "  Success Rate: N/A")
    summary_lines.append("")
    summary_lines.append("PERFORMANCE:")
    summary_lines.append(f"  Duration: {duration:.2f}s")
    summary_lines.append(f"  Throughput: {stage4_results['metrics']['evaluations_per_minute']:.2f} evals/min")
    summary_lines.append("")
    summary_lines.append("TOP CANDIDATES:")

    for i, candidate in enumerate(evaluated_candidates[:10], 1):
        eval_data = candidate['evaluation']
        summary_lines.append(f"\n  {i}. {candidate['full_name']} - {eval_data.get('recommendation', 'N/A')}")
        summary_lines.append(f"     Headline: {candidate.get('headline', 'N/A')[:70]}")
        summary_lines.append(f"     Scores: Domain={eval_data.get('domain_fit_score')}/10, Experience={eval_data.get('experience_match_score')}/10, Overall={eval_data.get('overall_fit_score')}/10")
        summary_lines.append(f"     Summary: {eval_data.get('summary', 'N/A')}")

    if failed_evaluations:
        summary_lines.append("\n\nFAILED EVALUATIONS:")
        for i, failure in enumerate(failed_evaluations, 1):
            summary_lines.append(f"  {i}. {failure['full_name']}: {failure['error']}")

    summary_text = "\n".join(summary_lines)
    session_logger.log_text("04_evaluation_summary.txt", summary_text)

    print(f"\n✓ Stage 4 Complete ({duration:.1f}s)")
    print(f"  Evaluated {len(evaluated_candidates)}/{len(collected_profiles)} candidates")

    # Update session status
    session_logger.update_session_status("stage4_complete", {
        "stage4_evaluated": len(evaluated_candidates),
        "stage4_failed": len(failed_evaluations),
        "stage4_duration": duration
    })

    # Send completion event with full results
    yield f"data: {json.dumps({'event': 'stage4_complete', 'results': stage4_results})}\n\n"


# ========================================
# API ENDPOINT
# ========================================

@domain_search_bp.route('/api/jd/domain-company-preview-search', methods=['POST'])
def domain_company_preview_search():
    """
    Combined endpoint for Stage 1 + Stage 2: Company discovery + Preview search.

    Request Body:
    {
        "jd_requirements": {
            "target_domain": "voice ai",
            "mentioned_companies": ["Deepgram", "AssemblyAI"],
            "competitor_context": "speech recognition, TTS",
            "role_title": "Senior ML Engineer",
            "seniority_level": "senior"
        },
        "endpoint": "employee_clean",  // Optional, default: employee_clean
        "max_previews": 20               // Optional, default: 20
    }

    Response:
    {
        "success": true,
        "session_id": "sess_20251104_223456_abc123",
        "stage1_companies": [...],
        "stage2_previews": [...],
        "relevance_score": 0.70,
        "log_directory": "backend/logs/domain_search_sessions/sess_..."
    }
    """
    try:
        data = request.get_json()

        # Extract inputs
        jd_requirements = data.get('jd_requirements', {})
        endpoint = data.get('endpoint', 'employee_clean')
        max_previews = data.get('max_previews', 20)

        # Validate inputs
        if not jd_requirements:
            return jsonify({"success": False, "error": "jd_requirements is required"}), 400

        # Check cache first to save API credits
        cache_key = generate_search_cache_key(jd_requirements, endpoint)
        cached_data = get_cached_search_results(cache_key, freshness_days=7)

        if cached_data:
            # Return cached results immediately - save API credits!
            print(f"\n{'='*80}")
            print(f"🎯 CACHE HIT! Using cached search results (age: {cached_data['cache_age_days']} days)")
            print(f"💰 SAVED API credits by avoiding duplicate search!")
            print(f"{'='*80}\n")

            return jsonify({
                "success": True,
                "session_id": cached_data.get('session_id', 'cached'),
                "stage1_companies": cached_data['stage1_companies'],
                "stage2_previews": cached_data['stage2_previews'],
                "relevance_score": 0.0,  # Could be stored in cache if needed
                "total_companies_discovered": len(cached_data['stage1_companies']),
                "total_previews_found": len(cached_data['stage2_previews']),
                "from_cache": True,
                "cache_age_days": cached_data['cache_age_days'],
                "log_directory": None  # No new logs for cached results
            })

        # Cache miss - proceed with fresh search
        print(f"\n{'='*80}")
        print(f"⚠️ CACHE MISS - Running fresh search (will save to cache after)")
        print(f"Cache Key: {cache_key}")
        print(f"{'='*80}\n")

        # Create session logger
        session_logger = SessionLogger()

        # Update metadata with input
        session_logger.update_session_status("running", {
            "jd_requirements": jd_requirements,
            "endpoint": endpoint,
            "max_previews": max_previews
        })

        print(f"\n{'='*80}")
        print(f"New Domain Company Search Session: {session_logger.session_id}")
        print(f"Log Directory: {session_logger.session_dir}")
        print(f"{'='*80}\n")

        # Stage 1: Discover companies
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        companies = loop.run_until_complete(
            stage1_discover_companies(jd_requirements, session_logger)
        )
        loop.close()

        # Stage 2: Preview search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stage2_results = loop.run_until_complete(
            stage2_preview_search(companies, jd_requirements, endpoint, max_previews, session_logger)
        )
        loop.close()

        # Save to cache for future requests
        save_search_results(
            cache_key=cache_key,
            stage1_companies=companies,
            stage2_previews=stage2_results['previews'],
            session_id=session_logger.session_id,
            jd_requirements=jd_requirements,
            endpoint=endpoint
        )

        # Update session status
        session_logger.update_session_status("stage2_complete", {
            "companies_discovered": len(companies),
            "previews_found": stage2_results['total_found'],
            "relevance_score": stage2_results['relevance_score']
        })

        # Return response
        return jsonify({
            "success": True,
            "session_id": session_logger.session_id,
            "stage1_companies": companies,
            "stage2_previews": stage2_results['previews'],
            "relevance_score": stage2_results['relevance_score'],
            "total_companies_discovered": len(companies),
            "total_previews_found": stage2_results['total_found'],
            "log_directory": str(session_logger.session_dir)
        })

    except Exception as e:
        print(f"Error in domain company preview search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@domain_search_bp.route('/api/jd/domain-company-evaluate-stream', methods=['POST'])
def domain_company_evaluate_stream():
    """
    Streaming SSE endpoint for Stage 4: AI Evaluation.

    This endpoint resumes from an existing session (after Stage 3) and evaluates
    candidates using Claude AI, streaming progress updates via Server-Sent Events.

    Request Body:
    {
        "session_id": "sess_20251104_223456_abc123",
        "jd_requirements": {...}
    }

    Response:
    Server-Sent Events stream with evaluation progress
    """
    try:
        data = request.get_json()

        # Extract inputs
        session_id = data.get('session_id')
        jd_requirements = data.get('jd_requirements', {})

        # Validate inputs
        if not session_id:
            return jsonify({"success": False, "error": "session_id is required"}), 400

        if not jd_requirements:
            return jsonify({"success": False, "error": "jd_requirements is required"}), 400

        # Load existing session
        session_dir = Path(f"logs/domain_search_sessions/{session_id}")
        if not session_dir.exists():
            return jsonify({"success": False, "error": f"Session {session_id} not found"}), 404

        # Load Stage 3 profiles
        stage3_file = session_dir / "03_full_profiles.json"
        if not stage3_file.exists():
            return jsonify({"success": False, "error": "Stage 3 profiles not found. Run Stage 3 first."}), 400

        with open(stage3_file, 'r') as f:
            stage3_data = json.load(f)

        collected_profiles = stage3_data['output']['profiles']

        if not collected_profiles:
            return jsonify({"success": False, "error": "No profiles to evaluate"}), 400

        print(f"\n{'='*80}")
        print(f"Resuming Session: {session_id}")
        print(f"Evaluating {len(collected_profiles)} candidates")
        print(f"{'='*80}\n")

        # Create session logger (reusing existing session)
        session_logger = SessionLogger(session_id=session_id)

        # Stream Stage 4 evaluation
        def generate():
            try:
                yield from stage4_evaluate_candidates_stream(
                    collected_profiles=collected_profiles,
                    jd_requirements=jd_requirements,
                    session_logger=session_logger
                )
            except Exception as e:
                error_event = {
                    "event": "error",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                print(f"Error in streaming evaluation: {e}")
                import traceback
                traceback.print_exc()

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        print(f"Error in evaluate stream endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@domain_search_bp.route('/api/jd/load-more-previews', methods=['POST'])
def load_more_previews():
    """
    Load more candidate previews from next company batch.

    Request Body:
    {
        "session_id": "search_...",
        "count": 20,
        "mode": "company_batch"
    }

    Response:
    {
        "success": true,
        "new_profiles": [...],
        "session_stats": {...},
        "remaining_batches": 5
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        count = data.get('count', 20)

        if not session_id:
            return jsonify({"success": False, "error": "session_id is required"}), 400

        # Get session from manager
        session_manager = SearchSessionManager()
        session = session_manager.get_session(session_id)

        if not session:
            return jsonify({"success": False, "error": "Session not found or expired"}), 404

        # Get next batch of companies
        next_batch = session_manager.get_next_batch(session_id)

        if not next_batch:
            return jsonify({
                "success": True,
                "new_profiles": [],
                "session_stats": session_manager.get_session_stats(session_id),
                "remaining_batches": 0,
                "message": "No more company batches available"
            })

        # Parse search query from session
        import json as json_lib
        search_query = json_lib.loads(session['search_query'])
        jd_requirements = search_query.get('jd_requirements', {})
        endpoint = search_query.get('endpoint', 'employee_clean')
        max_previews = search_query.get('max_previews', count)

        # Create session logger (reuse existing session directory)
        from utils.session_logger import SessionLogger
        session_logger = SessionLogger(session_id=session_id)

        # Run Stage 2 with next batch
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Convert batch companies to dict format
        companies_to_search = [{'name': c} for c in next_batch]

        stage2_results = loop.run_until_complete(
            stage2_preview_search(
                companies=companies_to_search,
                jd_requirements=jd_requirements,
                endpoint=endpoint,
                max_previews=max_previews,
                session_logger=session_logger,
                create_session=False,  # Don't create new session
                session_id=session_id,  # Continue existing session
                batch_size=5
            )
        )
        loop.close()

        # Get updated session stats
        session_stats = session_manager.get_session_stats(session_id)

        # Calculate remaining batches
        company_batches = json_lib.loads(session['company_batches'])
        current_batch_index = session.get('batch_index', 0)
        remaining_batches = len(company_batches) - current_batch_index - 1

        return jsonify({
            "success": True,
            "new_profiles": stage2_results.get('previews', []),
            "session_stats": session_stats,
            "remaining_batches": remaining_batches,
            "batch_companies": next_batch
        })

    except Exception as e:
        print(f"Error in load-more-previews: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# Register blueprint in app.py
def register_domain_search_routes(app):
    """Register domain search blueprint with Flask app."""
    app.register_blueprint(domain_search_bp)
    print("✓ Domain Search routes registered successfully")
