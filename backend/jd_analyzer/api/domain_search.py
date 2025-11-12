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
from coresignal_service import (
    search_profiles_with_endpoint,
    search_profiles_full,
    collect_profiles_batch,
    CoreSignalService
)

# Import CoreSignal company lookup for company ID resolution
from coresignal_company_lookup import CoreSignalCompanyLookup

# Import company research service for relevance screening
from company_research_service import CompanyResearchService

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
    mentioned_companies_raw = jd_requirements.get('mentioned_companies', [])
    competitor_context = jd_requirements.get('competitor_context', '')

    # Normalize mentioned_companies to handle both old format (strings) and new format (objects with IDs)
    mentioned_companies = []
    for item in mentioned_companies_raw:
        if isinstance(item, str):
            # Old format: just a string
            mentioned_companies.append(item)
        elif isinstance(item, dict):
            # New format: object with name and optionally coresignal_company_id
            mentioned_companies.append(item.get('name', item.get('company_name', str(item))))
        else:
            mentioned_companies.append(str(item))

    print(f"Domain: {target_domain}")
    print(f"Mentioned Companies: {mentioned_companies} ({len(mentioned_companies_raw)} with potential IDs)")
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

    # CoreSignal Company ID Lookup (or preserve IDs from frontend)
    print(f"\n🔍 Looking up CoreSignal company IDs...")

    # First, check if any companies came with IDs from frontend (mentioned_companies_raw)
    frontend_ids = {}
    for item in mentioned_companies_raw:
        if isinstance(item, dict) and 'coresignal_company_id' in item:
            company_name = item.get('name', item.get('company_name', ''))
            if company_name:
                frontend_ids[company_name.lower()] = {
                    'company_id': item['coresignal_company_id'],
                    'confidence': item.get('coresignal_confidence', 1.0)
                }
                print(f"   💾 {company_name}: Using ID from frontend (ID={item['coresignal_company_id']})")

    company_lookup = CoreSignalCompanyLookup()

    companies_with_ids = []
    companies_without_ids = []

    for company in validated_companies:
        company_name = company.get('name', company.get('company_name', ''))

        if not company_name:
            companies_without_ids.append(company)
            continue

        # Check if ID was provided by frontend first
        frontend_id = frontend_ids.get(company_name.lower())
        if frontend_id:
            # Use ID from frontend (already looked up during company research)
            company['coresignal_company_id'] = frontend_id['company_id']
            company['coresignal_confidence'] = frontend_id['confidence']
            company['coresignal_searchable'] = True
            company['id_source'] = 'frontend'
            companies_with_ids.append(company)
            continue

        # Look up company ID - try website first (more reliable), then name
        website = company.get('website')
        if website:
            # Use website.exact field for precise matching (much more reliable)
            match = company_lookup.get_by_website(website)
            if match:
                print(f"   🌐 Using website lookup for {company_name}: {website}")
        else:
            match = None

        # Fall back to name-based search if no website or website lookup failed
        if not match:
            match = company_lookup.get_best_match(company_name, confidence_threshold=0.75)

        if match:
            # Enrich company with CoreSignal data
            company['coresignal_company_id'] = match['company_id']
            company['coresignal_confidence'] = match['confidence']
            company['coresignal_searchable'] = True
            company['id_source'] = 'lookup'
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

    # ========================================
    # NEW: Screen companies for relevance using GPT-5-mini
    # ========================================
    print(f"\n{'='*80}")
    print(f"🎯 SCREENING {len(validated_companies)} COMPANIES FOR RELEVANCE")
    print(f"{'='*80}\n")

    screening_start_time = time.time()

    try:
        # Create instance of CompanyResearchService
        research_service = CompanyResearchService()

        # Call async screening method with Claude Haiku + web search
        # Note: screen_companies_with_haiku modifies companies in-place
        await research_service.screen_companies_with_haiku(
            validated_companies,
            jd_requirements,
            jd_id=None  # No session tracking for this endpoint
        )

        # Companies are now screened in-place with relevance_score, screening_reasoning, scored_by
        # Sort by relevance score (highest first)
        sorted_companies = sorted(
            validated_companies,
            key=lambda c: c.get('relevance_score', 0),
            reverse=True
        )

        # Log top 10 companies with scores
        print(f"\n🏆 TOP 10 COMPANIES BY RELEVANCE:")
        for i, company in enumerate(sorted_companies[:10], 1):
            score = company.get('relevance_score', 0)
            reasoning = company.get('screening_reasoning', 'N/A')  # FIXED: Haiku uses screening_reasoning
            print(f"  {i}. {company['name']} - Score: {score}/10")
            print(f"     {reasoning}\n")

        screening_duration = time.time() - screening_start_time
        print(f"✓ Screening Complete ({screening_duration:.1f}s)")
        print(f"  Companies sorted by relevance score")

        # Log screening results
        screening_log_data = {
            "stage": "company_screening",
            "total_companies": len(sorted_companies),
            "top_10_companies": [
                {
                    "rank": i + 1,
                    "name": c['name'],
                    "relevance_score": c.get('relevance_score', 0),
                    "screening_reasoning": c.get('screening_reasoning', 'N/A'),  # FIXED: field name
                    "scored_by": c.get('scored_by', 'N/A')  # Include how it was scored
                }
                for i, c in enumerate(sorted_companies[:10])
            ],
            "screening_duration_seconds": round(screening_duration, 1),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        session_logger.log_json("01_company_screening.json", screening_log_data)

        # Return sorted companies
        return sorted_companies

    except Exception as e:
        print(f"⚠️ Warning: Company screening failed: {e}")
        print(f"   Falling back to unscreened companies")
        import traceback
        traceback.print_exc()

        # Fallback: return validated companies without screening
        return validated_companies


# ========================================
# STAGE 2: Preview Search (20 Candidates)
# ========================================

def build_experience_based_query(
    companies: List[Dict[str, Any]],
    role_keywords: List[str],
    location: Optional[str] = None,
    require_location: bool = False,
    require_target_role: bool = True,
    endpoint: str = 'employee_base'
) -> Dict[str, Any]:
    """
    Build query searching employee EXPERIENCE HISTORY (not just current employer).

    This finds anyone who has EVER worked at these companies using nested experience field.
    Proven to find 1,500+ candidates vs 0 with current-employer-only approach.

    Args:
        companies: List of company dicts with 'coresignal_company_id'
        role_keywords: Precise role keywords from JD (e.g., ["ML Engineer", "AI Research Scientist"])
        location: Optional location from JD (used as boost, not requirement)
        require_location: If True, makes location required (not recommended - eliminates global remote teams)
        require_target_role: If True, requires role match in experience (recommended for precision)
        endpoint: 'employee_base' (default) or 'employee_clean'

    Returns:
        CoreSignal ES DSL query with nested experience structure
    """
    print(f"\n📋 Building EXPERIENCE-BASED query for {len(companies)} companies")
    print(f"   (Searches work HISTORY, not just current employer)")

    # Build experience company filters (prefer ID for precision, fallback to name for flexibility)
    experience_company_filters = []

    for company in companies:
        company_id = company.get('coresignal_company_id')
        company_name = company.get('name', 'Unknown')

        if company_id:
            # Prefer company ID (precise)
            print(f"   - {company_name} (ID: {company_id})")
            experience_company_filters.append({
                "term": {"experience.company_id": company_id}
            })
        elif company_name and company_name != 'Unknown':
            # Fallback to company name with match_phrase (flexible, handles variations)
            print(f"   - {company_name} (using name match)")
            experience_company_filters.append({
                "match_phrase": {"experience.company_name": company_name}
            })

    if not experience_company_filters:
        print("[WARNING] No valid companies for experience search!")
        return {"query": {"match_all": {}}}

    print(f"\n✅ Created {len(experience_company_filters)} experience filters")

    # Build role query string (much simpler with OR operators)
    # ALWAYS build role query when keywords exist (not dependent on require_target_role flag)
    role_query_string = None
    if role_keywords:
        # Filter out overly broad terms
        filtered_keywords = [k for k in role_keywords if k.lower() not in ['mid', 'senior', 'junior', 'staff', 'principal']]

        if filtered_keywords:
            # Build query_string with OR operators - much simpler!
            # Wrap multi-word phrases in quotes for exact matching
            quoted_keywords = []
            for keyword in filtered_keywords:
                if ' ' in keyword:
                    quoted_keywords.append(f'"{keyword}"')
                else:
                    quoted_keywords.append(keyword)

            role_query_string = ' OR '.join(quoted_keywords)
            if require_target_role:
                print(f"   Target roles: {role_query_string} (REQUIRED in experience)")
            else:
                print(f"   Target roles: {role_query_string} (OPTIONAL boost in experience)")

    # Build nested query structure
    must_clauses = []

    # Build nested experience query with company + optional role
    # SIMPLIFIED: For single company, use direct match. For multiple, use bool/should.
    if len(experience_company_filters) == 1:
        # Single company: use direct match (no bool wrapper)
        company_query = experience_company_filters[0]
    else:
        # Multiple companies: use bool/should structure
        company_query = {
            "bool": {
                "should": experience_company_filters,
                "minimum_should_match": 1
            }
        }

    nested_must = [company_query]
    nested_should = []

    # Add role query: MUST if required, SHOULD (boost) if optional
    if role_query_string:
        role_filter = {
            "query_string": {
                "query": role_query_string,
                "default_field": "experience.title",
                "default_operator": "OR"  # CRITICAL: Without this, ALL keywords must match simultaneously
            }
        }

        if require_target_role:
            # Role is REQUIRED - add to must
            nested_must.append(role_filter)
            print(f"   🔒 Role REQUIRED: Must match one of the role keywords")
        else:
            # Role is OPTIONAL - add to should (boosts score but not required)
            nested_should.append(role_filter)
            print(f"   ⭐ Role BOOST: Matching role keywords boosts score (optional)")

    # Build nested query with proper must/should structure
    nested_bool = {"must": nested_must}
    if nested_should:
        nested_bool["should"] = nested_should
        nested_bool["minimum_should_match"] = 0  # Should clauses are optional

    must_clauses.append({
        "nested": {
            "path": "experience",
            "query": {
                "bool": nested_bool
            }
        }
    })

    # Build final query - keep it simple!
    query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    # Add location outside nested query if needed (optional boost only)
    if location and not require_location:
        location_field = "location" if endpoint == 'employee_base' else "location_country"
        query["query"]["bool"]["should"] = [{"term": {location_field: location}}]
        query["query"]["bool"]["minimum_should_match"] = 0
        print(f"   📍 Location BOOST: {location} (optional)")
    elif location and require_location:
        location_field = "location" if endpoint == 'employee_base' else "location_country"
        must_clauses.append({"term": {location_field: location}})
        print(f"   🔒 Location REQUIRED: {location}")
    else:
        print(f"   🌍 Location: Worldwide (no filter)")

    return query


def extract_precise_role_keywords(
    role_title: str,
    domain: str = "",
    technical_skills: List[str] = None,
    seniority: str = ""
) -> List[str]:
    """
    Extract precise role keywords from JD requirements.

    Instead of generic ["engineer", "manager", "director"], generate
    domain-specific role variations.

    Examples:
        Input: role_title="Senior ML Engineer", domain="voice ai"
        Output: ["ml engineer", "machine learning engineer", "ai engineer",
                 "research scientist", "voice ai engineer"]

    Args:
        role_title: Role from JD (e.g., "Senior ML Engineer")
        domain: Target domain (e.g., "voice ai")
        technical_skills: Skills from JD (e.g., ["Python", "PyTorch"])
        seniority: Seniority level (e.g., "senior")

    Returns:
        List of precise role keywords
    """
    keywords = []
    technical_skills = technical_skills or []

    # Handle None or empty role_title
    if not role_title:
        role_title = ""

    # Remove seniority prefixes to get base role
    base_role = role_title.lower()
    for level in ['senior', 'junior', 'staff', 'principal', 'lead', 'mid-level', 'entry', 'chief']:
        base_role = base_role.replace(level, '').strip()

    # Add exact role
    if base_role:
        keywords.append(base_role)

    # Add common variations
    role_variations = {
        "ml engineer": ["machine learning engineer", "ai engineer", "ml researcher"],
        "machine learning engineer": ["ml engineer", "ai engineer", "research scientist"],
        "data scientist": ["research scientist", "ml scientist", "ai scientist"],
        "research scientist": ["ml researcher", "ai researcher", "research engineer"],
        "software engineer": ["backend engineer", "full stack engineer", "platform engineer"],
        "product manager": ["technical product manager", "ai product manager"],
        "cto": ["chief technology officer", "vp engineering", "engineering director"],
        "ceo": ["chief executive officer", "founder", "co-founder"],
    }

    if base_role in role_variations:
        keywords.extend(role_variations[base_role])

    # Add domain-specific roles
    if domain:
        domain_lower = domain.lower()
        if "ai" in domain_lower or "ml" in domain_lower:
            keywords.extend(["ai engineer", "machine learning", "research scientist"])
        if "voice" in domain_lower or "speech" in domain_lower:
            keywords.extend(["voice ai", "speech recognition", "nlp engineer"])
        if "computer vision" in domain_lower or "cv" in domain_lower:
            keywords.extend(["computer vision", "cv engineer", "perception engineer"])
        if "nlp" in domain_lower or "natural language" in domain_lower:
            keywords.extend(["nlp", "natural language processing", "nlp engineer"])

    # Add keywords from technical skills
    skill_to_role = {
        "pytorch": "ml engineer",
        "tensorflow": "ml engineer",
        "nlp": "nlp engineer",
        "natural language processing": "nlp engineer",
        "computer vision": "cv engineer",
        "speech": "speech engineer",
        "voice": "voice ai engineer",
        "deep learning": "ml engineer",
        "llm": "ai engineer",
        "large language model": "ai engineer"
    }

    for skill in technical_skills:
        skill_lower = skill.lower()
        for skill_keyword, role in skill_to_role.items():
            if skill_keyword in skill_lower and role not in keywords:
                keywords.append(role)

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        k_clean = k.strip()
        if k_clean and k_clean not in seen:
            seen.add(k_clean)
            unique_keywords.append(k_clean)

    return unique_keywords


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
    # SIMPLE TEST MODE - Set to True to test if company IDs work at all
    SIMPLE_TEST_MODE = False  # Toggle this to debug employee search

    if SIMPLE_TEST_MODE:
        # SIMPLIFIED QUERY: Just company IDs, no role/location filters
        company_ids = [c.get('coresignal_company_id') for c in companies if c.get('coresignal_company_id')]

        if company_ids:
            print(f"\n{'='*80}")
            print(f"🧪 SIMPLE TEST MODE ACTIVE")
            print(f"   Testing {len(company_ids)} companies with IDs (no other filters)")
            print(f"   Company IDs: {company_ids[:5]}{'...' if len(company_ids) > 5 else ''}")
            print(f"{'='*80}\n")

            # Dead simple query - just match company IDs
            query = {
                "query": {
                    "terms": {"last_company_id": company_ids}
                }
            }
            return query
        else:
            print(f"⚠️  SIMPLE TEST MODE: No company IDs found! Falling back to full query...")

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

    # Add location as REQUIRED filter (not optional)
    if location:
        must_clauses.append({"term": {"location_country": location}})

    # Build "should" clause for optional boosting
    should_clause = []

    # If not requiring current role, add role filters as a "should" for boosting
    if not require_current_role and role_filters:
        should_clause.extend(role_filters)

    # Add should clause to query if we have any
    if should_clause:
        query["query"]["bool"]["should"] = should_clause
        query["query"]["bool"]["minimum_should_match"] = 0  # Don't require any should matches

    return query


def normalize_profile_fields(profiles):
    """
    Normalize CoreSignal profile fields to frontend-expected format.

    CoreSignal uses: full_name, headline, first_name, last_name, profile_url
    Frontend expects: name, title, linkedin_url, current_company, years_experience

    This function adds normalized fields while keeping all original fields.
    """
    from datetime import datetime

    normalized_previews = []
    for profile in profiles:
        normalized = profile.copy()  # Keep all original fields

        # Normalize name field
        if not normalized.get('name'):
            normalized['name'] = profile.get('full_name') or \
                                f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or None

        # Normalize title field (use headline as title)
        if not normalized.get('title'):
            normalized['title'] = profile.get('headline') or None

        # Normalize linkedin_url field
        if not normalized.get('linkedin_url'):
            normalized['linkedin_url'] = profile.get('profile_url') or None

        # Calculate current_company from most recent experience
        if not normalized.get('current_company') and profile.get('experience'):
            experiences = profile.get('experience', [])
            if experiences:
                # Find most recent non-ended experience
                current_exp = next((exp for exp in experiences if not exp.get('end_date')), None)
                if current_exp:
                    normalized['current_company'] = current_exp.get('company_name')
                elif experiences:  # Fallback to most recent
                    normalized['current_company'] = experiences[0].get('company_name')

        # Calculate years_experience if not present
        if not normalized.get('years_experience') and profile.get('experience'):
            # Simple calculation: sum of all experience durations
            total_years = 0
            for exp in profile.get('experience', []):
                start = exp.get('start_date')
                end = exp.get('end_date') or datetime.now().strftime('%Y-%m')
                if start:
                    try:
                        start_year = int(start[:4])
                        end_year = int(end[:4])
                        total_years += (end_year - start_year)
                    except:
                        pass
            normalized['years_experience'] = total_years

        normalized_previews.append(normalized)

    return normalized_previews


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
        # Build company name to full object mapping to preserve IDs
        company_map = {c.get('name', c.get('company_name', '')): c for c in companies}
        company_names = list(company_map.keys())

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
        # Map batch names back to full company objects (preserves IDs!)
        first_batch_names = session_data['first_batch']
        companies_to_search = [company_map.get(name, {'name': name}) for name in first_batch_names]

        print(f"✅ Created session: {current_session_id}")
        print(f"   Total batches: {session_data['total_batches']}")
        print(f"   First batch: {first_batch_names}")
        print(f"   Companies with IDs: {sum(1 for c in companies_to_search if 'coresignal_company_id' in c)}/{len(companies_to_search)}")

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

    # Extract JD requirements for precise role matching
    role_title = jd_requirements.get('role_title', '')
    seniority = jd_requirements.get('seniority_level', '')
    domain = jd_requirements.get('target_domain', '')
    technical_skills = jd_requirements.get('technical_skills', [])
    location = jd_requirements.get('location', None)

    # Feature flag for experience-based search (can be disabled via env var for rollback)
    use_experience_based_search = os.getenv('USE_EXPERIENCE_BASED_SEARCH', 'true').lower() == 'true'

    # Extract precise role keywords from JD
    if use_experience_based_search:
        precise_role_keywords = extract_precise_role_keywords(
            role_title=role_title,
            domain=domain,
            technical_skills=technical_skills,
            seniority=seniority
        )
        print(f"\n{'='*80}")
        print(f"🎯 EXPERIENCE-BASED SEARCH ACTIVE")
        print(f"   Companies: {len(companies_to_search)} (batch)")
        print(f"   Precise Role Keywords: {precise_role_keywords[:5]}{'...' if len(precise_role_keywords) > 5 else ''}")
        print(f"   Location: {location or 'Worldwide'} (optional)")
        print(f"   Endpoint: {endpoint}")
        print(f"{'='*80}")
    else:
        # Fallback to generic keywords (old method)
        precise_role_keywords = [
            "engineer", "developer", "architect",  # Technical roles
            "product", "manager", "director",       # Mid-level roles
            "founder", "lead"                        # Startup roles
        ]
        if role_title:
            precise_role_keywords.extend(role_title.lower().split())
        if seniority:
            precise_role_keywords.append(seniority.lower())
        precise_role_keywords = list(set(precise_role_keywords))
        print(f"\n⚠️  Using CURRENT EMPLOYER search (old method)")
        print(f"   Companies: {len(companies_to_search)} (batch)")
        print(f"   Role Keywords: {precise_role_keywords}")
        print(f"   Location: United States (required)")

    # Build query using selected method
    if use_experience_based_search:
        query = build_experience_based_query(
            companies=companies_to_search,
            role_keywords=precise_role_keywords,
            location=location,  # From JD, optional
            require_location=False,  # Make location optional (boost, not requirement)
            require_target_role=False,  # Make role optional (boost, not requirement) - matches handover success
            endpoint=endpoint
        )
        search_method = "experience_based"
    else:
        query = build_domain_company_query(
            companies=companies_to_search,
            role_keywords=precise_role_keywords,
            location="United States",
            require_current_role=False
        )
        search_method = "current_employer"

    # Log query with comprehensive metadata
    query_log_data = {
        "stage": "preview_search_query",
        "session_id": current_session_id,
        "search_method": search_method,
        "input": {
            "endpoint": endpoint,
            "num_companies": len(companies_to_search),
            "batch_companies": [c['name'] for c in companies_to_search],
            "role_keywords": precise_role_keywords,
            "location": location or "Worldwide",
            "location_required": False if use_experience_based_search else True,
            "target_role_required": True if use_experience_based_search else False
        },
        "query": query,
        "duration_seconds": round(time.time() - start_time, 2)
    }
    session_logger.log_json("02_preview_query.json", query_log_data)

    # Execute search via CoreSignal API using search/collect pattern
    # STEP 1: Search for employee IDs (up to 1000)
    print(f"\n📡 Step 1: Searching for employee IDs (max: 1000)...")
    search_result = search_profiles_full(
        query=query,
        endpoint=endpoint,
        max_results=1000  # Get up to 1000 IDs
    )

    if not search_result.get('success'):
        error_msg = search_result.get('error', 'Unknown error')
        print(f"   ❌ CoreSignal search failed: {error_msg}")
        duration = time.time() - start_time
        return {
            "previews": [],
            "relevance_score": 0.0,
            "total_found": 0,
            "session_id": current_session_id,
            "error": error_msg
        }

    # Get employee IDs from search
    employee_ids = search_result.get('employee_ids', [])
    total_found = search_result.get('total_found', len(employee_ids))
    print(f"   ✅ Search successful: Found {len(employee_ids)} employee IDs (total available: {total_found})")

    # STEP 2: Store all employee IDs in session for pagination
    if employee_ids and current_session_id:
        session_manager.store_employee_ids(current_session_id, employee_ids)
        print(f"   📊 Stored {len(employee_ids)} IDs in session for progressive loading")

    # STEP 3: Collect first batch of profiles (with caching)
    print(f"\n📡 Step 2: Collecting first {max_previews} profiles (with caching)...")

    # Get storage functions for profile caching
    from utils.supabase_storage import get_stored_profile, save_stored_profile
    storage_functions = {
        'get': get_stored_profile,
        'save': save_stored_profile
    }

    batch_result = collect_profiles_batch(
        employee_ids=employee_ids,
        start_index=0,
        batch_size=max_previews,
        storage_functions=storage_functions
    )

    if not batch_result.get('success'):
        error_msg = batch_result.get('error', 'Failed to collect profiles')
        print(f"   ❌ Profile collection failed: {error_msg}")
        duration = time.time() - start_time
        return {
            "previews": [],
            "relevance_score": 0.0,
            "total_found": len(employee_ids),
            "session_id": current_session_id,
            "error": error_msg
        }

    # Get collected profiles
    previews = batch_result.get('profiles', [])
    cache_stats = batch_result.get('cache_stats', {})

    print(f"   ✅ Collected {len(previews)} profiles")
    print(f"   📊 Cache stats: {cache_stats['cached']} cached, {cache_stats['fetched']} fetched, {cache_stats['failed']} failed")

    # Update profiles_offset in session for next load
    if current_session_id and len(previews) > 0:
        session_manager.increment_profiles_offset(current_session_id, len(previews))

    duration = time.time() - start_time

    # Analyze relevance: Check how many have domain company experience
    domain_match_count = 0
    company_names_lower = [c['name'].lower() for c in companies_to_search if c.get('name')]

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

    # Analyze location distribution for transparency
    location_distribution = {}
    for candidate in previews:
        if isinstance(candidate, dict):
            loc = candidate.get('location', 'Unknown')
            location_distribution[loc] = location_distribution.get(loc, 0) + 1

    # Sort by count (descending)
    location_distribution = dict(sorted(location_distribution.items(), key=lambda x: x[1], reverse=True))

    # Calculate filter precision (how many match target role)
    role_match_count = 0
    if use_experience_based_search and precise_role_keywords:
        for candidate in previews:
            if isinstance(candidate, dict):
                # Check current title (handle None explicitly)
                current_title = (candidate.get('title') or '').lower()
                # Check experience titles (handle None explicitly)
                experiences = candidate.get('experience', [])
                exp_titles = [(exp.get('title') or '').lower() for exp in experiences]
                all_titles = [current_title] + exp_titles

                # Check if any title matches our keywords
                for title in all_titles:
                    if any(keyword.lower() in title for keyword in precise_role_keywords[:5]):  # Check first 5 keywords
                        role_match_count += 1
                        break

    filter_precision = role_match_count / len(previews) if previews else 0.0

    # Print location distribution
    print(f"\n   📍 Location Distribution:")
    for loc, count in list(location_distribution.items())[:5]:  # Top 5 locations
        print(f"      - {loc}: {count} ({count/len(previews)*100:.0f}%)")

    print(f"\n   🎯 Filter Precision: {role_match_count}/{len(previews)} ({filter_precision*100:.0f}%) match target role")

    # Prepare comprehensive results log
    results_log_data = {
        "stage": "preview_results",
        "search_method": search_method,
        "candidates": previews,
        "total_candidates": len(previews),
        "total_employee_ids_found": len(employee_ids),  # Raw search results
        "relevance_score": relevance_score,
        "filter_precision": filter_precision,
        "duration_seconds": round(duration, 2),
        "location_distribution": location_distribution,
        "role_keywords_used": precise_role_keywords,
        "cache_stats": cache_stats,
        "search_config": {
            "location_filter": location or "Worldwide",
            "location_required": False if use_experience_based_search else True,
            "target_role_required": True if use_experience_based_search else False,
            "endpoint": endpoint
        }
    }
    session_logger.log_json("02_preview_results.json", results_log_data)

    # Prepare analysis text
    analysis_text = f"""PREVIEW SEARCH QUALITY ANALYSIS
{"="*50}
Search Method: {search_method}
Total Candidates: {len(previews)}
Total Employee IDs Found: {len(employee_ids)}
Endpoint Used: {endpoint}

Query Configuration:
  Companies Targeted: {len(companies_to_search)}
  Role Keywords: {', '.join(precise_role_keywords[:10])}
  Location: {location or 'Worldwide'}
  Location Required: {False if use_experience_based_search else True}
  Target Role Required: {True if use_experience_based_search else False}

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

    # Normalize profile fields for frontend compatibility using shared function
    normalized_previews = normalize_profile_fields(previews)

    return {
        "previews": normalized_previews,
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
# STREAMING GENERATOR FOR STAGE 1-2
# ========================================

def stage1_and_stage2_stream(
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    top_level_companies: List[Dict[str, Any]],
    cache_key: str
) -> Generator[str, None, None]:
    """
    Streaming generator for Stage 1 (Company Discovery) and Stage 2 (Preview Search).
    Yields SSE progress events throughout the pipeline.

    Args:
        jd_requirements: Parsed JD requirements
        endpoint: CoreSignal endpoint to use
        max_previews: Max number of previews to fetch
        top_level_companies: Pre-selected companies (if any)
        cache_key: Cache key for this search

    Yields:
        SSE formatted strings with progress updates and final results
    """
    try:
        # Create session logger
        session_logger = SessionLogger()

        # Update metadata
        session_logger.update_session_status("running", {
            "jd_requirements": jd_requirements,
            "endpoint": endpoint,
            "max_previews": max_previews
        })

        # Send initial event
        event_data = json.dumps({'event': 'search_start', 'session_id': session_logger.session_id})
        yield f"data: {event_data}\n\n"

        # Stage 1: Company Discovery
        pre_selected_companies = top_level_companies if top_level_companies else []

        if pre_selected_companies:
            # Using pre-selected companies (skip Stage 1)
            companies = pre_selected_companies
            with_ids = sum(1 for c in companies if isinstance(c, dict) and c.get('coresignal_company_id'))

            event_data = json.dumps({'event': 'stage1_skipped', 'reason': 'pre_selected', 'count': len(companies), 'with_ids': with_ids})
            yield f"data: {event_data}\n\n"
        else:
            # Run Stage 1 discovery
            event_data = json.dumps({'event': 'stage1_start', 'message': 'Discovering companies...'})
            yield f"data: {event_data}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            companies = loop.run_until_complete(
                stage1_discover_companies(jd_requirements, session_logger)
            )
            loop.close()

            # Emit stage1_complete with screening results (companies are now sorted by relevance)
            event_data = json.dumps({
                'event': 'stage1_complete',
                'companies_found': len(companies),
                'companies': [c.get('name', 'Unknown') for c in companies[:10]],
                'top_scores': [round(c.get('relevance_score', 0), 1) for c in companies[:10]]
            })
            yield f"data: {event_data}\n\n"

        # Stage 2: Preview Search
        event_data = json.dumps({'event': 'stage2_start', 'message': 'Searching for candidates...', 'companies': len(companies)})
        yield f"data: {event_data}\n\n"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stage2_results = loop.run_until_complete(
            stage2_preview_search(companies, jd_requirements, endpoint, max_previews, session_logger)
        )
        loop.close()

        event_data = json.dumps({'event': 'stage2_progress', 'message': 'Normalizing profile fields...'})
        yield f"data: {event_data}\n\n"

        # Save to cache
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

        # Send completion event with full results
        event_data = json.dumps({'event': 'stage2_complete', 'candidates_found': stage2_results['total_found']})
        yield f"data: {event_data}\n\n"

        # Build final response
        response_data = {
            "event": "search_complete",
            "success": True,
            "session_id": session_logger.session_id,
            "stage1_companies": companies,
            "stage2_previews": stage2_results['previews'],
            "relevance_score": stage2_results['relevance_score'],
            "total_companies_discovered": len(companies),
            "total_previews_found": stage2_results['total_found'],
            "session_stats": stage2_results['session_stats'],
            "log_directory": str(session_logger.session_dir)
        }

        # Send final result
        event_data = json.dumps(response_data)
        yield f"data: {event_data}\n\n"

    except Exception as e:
        error_event = {
            "event": "error",
            "error": str(e),
            "traceback": __import__('traceback').format_exc()
        }
        event_data = json.dumps(error_event)
        yield f"data: {event_data}\n\n"


# ========================================
# API ENDPOINT
# ========================================

@domain_search_bp.route('/api/jd/domain-company-preview-search', methods=['POST'])
def domain_company_preview_search():
    """
    Combined endpoint for Stage 1 + Stage 2: Company discovery + Preview search.

    Supports both JSON response (default) and SSE streaming (opt-in).

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
        "max_previews": 20,              // Optional, default: 20
        "stream": false                  // Optional, default: false. Set true for SSE streaming
    }

    Response (JSON mode):
    {
        "success": true,
        "session_id": "sess_20251104_223456_abc123",
        "stage1_companies": [...],  // Sorted by relevance_score (highest first)
        "stage2_previews": [...],
        "relevance_score": 0.70,
        "log_directory": "backend/logs/domain_search_sessions/sess_..."
    }

    Note: stage1_companies now includes relevance_score and relevance_reasoning fields from GPT-5-mini screening.

    Response (SSE mode):
    Server-Sent Events stream with progress updates:
    - search_start: Search initiated
    - stage1_start: Company discovery started
    - stage1_complete: Companies discovered and sorted by relevance (includes top_scores array)
    - stage2_start: Candidate search started
    - stage2_progress: Search progress updates
    - stage2_complete: Candidates found
    - search_complete: Final results (full response data)

    Note: Stage 1 now includes AI-powered relevance screening with GPT-5-mini.
    Companies are automatically sorted by relevance score (1-10) before Stage 2.
    """
    try:
        data = request.get_json()

        # Extract inputs
        jd_requirements = data.get('jd_requirements', {})
        endpoint = data.get('endpoint', 'employee_clean')
        max_previews = data.get('max_previews', 100)  # Increased from 20 to 100 for experience-based search
        stream_mode = data.get('stream', False)  # Support SSE streaming
        bypass_cache = data.get('bypass_cache', False)  # NEW: Support cache bypass for refresh

        # IMPORTANT: Merge top-level mentioned_companies (from company selection UI)
        # into jd_requirements.mentioned_companies (from JD analysis)
        # This preserves company IDs from the frontend
        top_level_companies = data.get('mentioned_companies', [])
        if top_level_companies:
            # Get existing companies from JD analysis (if any)
            existing_companies = jd_requirements.get('mentioned_companies', [])

            # Merge: prioritize top-level (from UI) over JD analysis
            # Top-level companies may have CoreSignal IDs attached
            if isinstance(existing_companies, list):
                # Combine both sources, with top-level taking precedence
                jd_requirements['mentioned_companies'] = top_level_companies + existing_companies
                print(f"📋 Merged companies: {len(top_level_companies)} from UI + {len(existing_companies)} from JD")
            else:
                jd_requirements['mentioned_companies'] = top_level_companies
                print(f"📋 Using {len(top_level_companies)} companies from UI selection")

        # Validate inputs
        if not jd_requirements:
            return jsonify({"success": False, "error": "jd_requirements is required"}), 400

        # Check cache first to save API credits (unless bypass requested)
        cache_key = generate_search_cache_key(jd_requirements, endpoint)

        if bypass_cache:
            print(f"\n{'='*80}")
            print(f"🔄 CACHE BYPASS REQUESTED - Running fresh search")
            print(f"{'='*80}\n")
            cached_data = None
        else:
            cached_data = get_cached_search_results(cache_key, freshness_days=7)

        # If streaming mode requested and cache miss, use SSE streaming
        if stream_mode and not cached_data:
            print(f"\n{'='*80}")
            print(f"🔄 STREAMING MODE - Will send SSE progress events")
            print(f"{'='*80}\n")

            return Response(
                stream_with_context(
                    stage1_and_stage2_stream(
                        jd_requirements,
                        endpoint,
                        max_previews,
                        top_level_companies,
                        cache_key
                    )
                ),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )

        if cached_data:
            # Return cached results immediately - save API credits!
            print(f"\n{'='*80}")
            print(f"🎯 CACHE HIT! Using cached search results (age: {cached_data['cache_age_days']} days)")
            print(f"💰 SAVED API credits by avoiding duplicate search!")
            print(f"{'='*80}\n")

            # Normalize cached profile fields for frontend compatibility
            normalized_cached_previews = normalize_profile_fields(cached_data['stage2_previews'])

            return jsonify({
                "success": True,
                "session_id": cached_data.get('session_id', 'cached'),
                "stage1_companies": cached_data['stage1_companies'],
                "stage2_previews": normalized_cached_previews,
                "relevance_score": 0.0,  # Could be stored in cache if needed
                "total_companies_discovered": len(cached_data['stage1_companies']),
                "total_previews_found": len(normalized_cached_previews),
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

        # Stage 1: Discover companies (skip if companies are pre-selected)
        # Check if companies are pre-selected from company research UI
        pre_selected_companies = top_level_companies if top_level_companies else []

        if pre_selected_companies:
            # Companies already selected by user - use directly (trust user selection)
            companies = pre_selected_companies
            print(f"\n{'='*80}")
            print(f"✅ USING {len(companies)} PRE-SELECTED COMPANIES (SKIPPING STAGE 1)")
            print(f"   Companies: {[c.get('name', c.get('company_name', 'Unknown')) for c in companies[:5]]}")
            if len(companies) > 5:
                print(f"   ... and {len(companies) - 5} more")

            # Check how many have CoreSignal IDs
            with_ids = sum(1 for c in companies if isinstance(c, dict) and c.get('coresignal_company_id'))
            print(f"   Companies with CoreSignal IDs: {with_ids}/{len(companies)}")
            print(f"{'='*80}\n")
        else:
            # Run Stage 1 discovery for new search
            print(f"\n📋 No pre-selected companies - running full discovery pipeline")
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

        # Build response
        response_data = {
            "success": True,
            "session_id": session_logger.session_id,
            "stage1_companies": companies,
            "stage2_previews": stage2_results['previews'],
            "relevance_score": stage2_results['relevance_score'],
            "total_companies_discovered": len(companies),
            "total_previews_found": stage2_results['total_found'],
            "session_stats": stage2_results['session_stats'],  # Required by frontend
            "log_directory": str(session_logger.session_dir)
        }

        # DEBUG: Log what we're sending to frontend
        print(f"\n{'='*80}")
        print(f"📤 SENDING TO FRONTEND:")
        print(f"   Session ID: {response_data['session_id']}")
        print(f"   Candidates: {len(response_data['stage2_previews'])} profiles")
        print(f"   Session Stats: {response_data['session_stats']}")
        print(f"   First candidate: {response_data['stage2_previews'][0]['full_name'] if response_data['stage2_previews'] else 'N/A'}")
        print(f"{'='*80}\n")

        return jsonify(response_data)

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
    Load more candidate profiles from stored employee IDs.

    Uses the search/collect pattern: employee IDs were retrieved upfront,
    now we fetch profiles in batches of 20 with intelligent caching.

    Request Body:
    {
        "session_id": "search_...",
        "count": 20
    }

    Response:
    {
        "success": true,
        "new_profiles": [...],           # 20 new profiles
        "cache_stats": {...},            # Cache hit/miss stats
        "pagination": {
            "current_offset": 40,
            "remaining_profiles": 960,
            "total_profiles": 1000
        }
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        count = data.get('count', 20)

        if not session_id:
            return jsonify({"success": False, "error": "session_id is required"}), 400

        print(f"\n{'='*80}")
        print(f"LOAD MORE PROFILES REQUEST")
        print(f"{'='*80}")
        print(f"Session ID: {session_id}")
        print(f"Requested count: {count}")

        # Get session from manager
        session_manager = SearchSessionManager()
        session = session_manager.get_session(session_id)

        if not session:
            return jsonify({"success": False, "error": "Session not found or expired"}), 404

        # Get next batch of profile IDs to fetch
        batch_info = session_manager.get_next_profile_batch_info(session_id, batch_size=count)

        if not batch_info:
            # No more profiles to fetch
            print(f"✓ All profiles fetched for session {session_id}")
            return jsonify({
                "success": True,
                "new_profiles": [],
                "cache_stats": {"cached": 0, "fetched": 0, "failed": 0},
                "pagination": {
                    "current_offset": session.get('profiles_offset', 0),
                    "remaining_profiles": 0,
                    "total_profiles": session.get('total_employee_ids', 0)
                },
                "message": "No more profiles available"
            })

        employee_ids_to_fetch = batch_info['employee_ids']
        start_index = batch_info['start_index']
        remaining = batch_info['remaining']
        total = batch_info['total']

        print(f"📊 Batch info:")
        print(f"   Start index: {start_index}")
        print(f"   Fetching: {len(employee_ids_to_fetch)} profiles")
        print(f"   Remaining after this batch: {remaining}")
        print(f"   Total IDs in session: {total}")

        # Get storage functions for profile caching
        from utils.supabase_storage import get_stored_profile, save_stored_profile
        storage_functions = {
            'get': get_stored_profile,
            'save': save_stored_profile
        }

        # Collect profiles with caching
        print(f"\n📡 Collecting {len(employee_ids_to_fetch)} profiles (with caching)...")
        batch_result = collect_profiles_batch(
            employee_ids=employee_ids_to_fetch,
            start_index=0,  # Already sliced in batch_info
            batch_size=len(employee_ids_to_fetch),
            storage_functions=storage_functions
        )

        if not batch_result.get('success'):
            error_msg = batch_result.get('error', 'Failed to collect profiles')
            print(f"❌ Profile collection failed: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500

        new_profiles = batch_result.get('profiles', [])
        cache_stats = batch_result.get('cache_stats', {})

        print(f"✅ Collected {len(new_profiles)} profiles")
        print(f"📊 Cache stats: {cache_stats['cached']} cached, {cache_stats['fetched']} fetched, {cache_stats['failed']} failed")

        # Update profiles_offset in session
        if len(new_profiles) > 0:
            session_manager.increment_profiles_offset(session_id, len(new_profiles))
            new_offset = session.get('profiles_offset', 0) + len(new_profiles)
        else:
            new_offset = session.get('profiles_offset', 0)

        # Prepare response
        response_data = {
            "success": True,
            "new_profiles": new_profiles,
            "cache_stats": cache_stats,
            "pagination": {
                "current_offset": new_offset,
                "remaining_profiles": remaining,
                "total_profiles": total,
                "profiles_fetched": len(new_profiles)
            }
        }

        print(f"✓ Load more complete: returned {len(new_profiles)} profiles")
        print(f"  Progress: {new_offset}/{total} profiles fetched ({remaining} remaining)")

        return jsonify(response_data)

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
