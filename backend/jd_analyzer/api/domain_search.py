"""
Domain Company-Based Candidate Search API

New endpoints for progressive candidate filtering:
1. Domain company discovery (use existing CompanyDiscoveryAgent)
2. Preview search (20 candidates to test quality)
3. Full profile collection (if quality is good)
4. AI evaluation (Gemini + Claude)

All stages have comprehensive logging with JSON + TXT outputs.
"""

import os
import asyncio
import time
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify

# Adjust sys.path to allow imports from backend directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import existing agents
from jd_analyzer.company.discovery_agent import CompanyDiscoveryAgent
from jd_analyzer.company.company_validation_agent import CompanyValidationAgent

# Import logging utility
from utils.session_logger import SessionLogger, format_company_list, format_preview_analysis

# Import CoreSignal service (will use for preview search)
from coresignal_service import search_profiles_with_endpoint

# Create Blueprint
domain_search_bp = Blueprint('domain_search', __name__)


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

    # AI Validation: Use Claude to intelligently filter companies
    print(f"\n🤖 Validating companies with AI (Claude Haiku 4.5)...")
    validation_agent = CompanyValidationAgent()
    validated_companies = await validation_agent.validate_and_filter(
        discovered_companies=companies,
        target_domain=target_domain,
        min_relevance="low"  # Accept low/medium/high relevance
    )

    # Transform validated companies: rename 'company_name' to 'name' for compatibility
    for company in validated_companies:
        if 'company_name' in company and 'name' not in company:
            company['name'] = company['company_name']

    removed_count = len(companies) - len(validated_companies)
    print(f"   ✅ Validated: {len(validated_companies)} companies ({removed_count} rejected by AI)")

    validation_duration = time.time() - start_time
    print(f"\n✓ Stage 1 Complete ({validation_duration:.1f}s)")
    print(f"  Discovered: {len(companies)} companies")
    print(f"  AI Validated: {len(validated_companies)} companies")
    print(f"  Log: {session_logger.session_dir}/01_company_discovery.json")

    return validated_companies


# ========================================
# STAGE 2: Preview Search (20 Candidates)
# ========================================

def build_domain_company_query(
    companies: List[Dict[str, Any]],
    role_keywords: List[str],
    location: str = "United States"
) -> Dict[str, Any]:
    """
    Build Elasticsearch DSL query for candidates who worked at domain companies.

    Args:
        companies: List of company dicts with 'name' field
        role_keywords: Basic role keywords (engineer, founder, CEO, product)
        location: Location filter (default: United States)

    Returns:
        Elasticsearch DSL query dict
    """
    # Extract company names
    company_names = [c['name'] for c in companies]

    # Build nested query for experience.company_name
    company_filters = []
    for company_name in company_names:
        # Wildcard match (case-insensitive)
        company_filters.append({
            "wildcard": {"experience.company_name": f"*{company_name.lower()}*"}
        })

    # Build role filters
    role_filters = []
    for keyword in role_keywords:
        role_filters.append({
            "wildcard": {"active_experience_title": f"*{keyword.lower()}*"}
        })

    # Build full query
    query = {
        "query": {
            "bool": {
                "must": [
                    # Location filter
                    {"term": {"location_country": location}},

                    # Company experience filter (nested query)
                    {
                        "nested": {
                            "path": "experience",
                            "query": {
                                "bool": {
                                    "should": company_filters,
                                    "minimum_should_match": 1
                                }
                            }
                        }
                    },

                    # Basic role match
                    {
                        "bool": {
                            "should": role_filters,
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }
    }

    return query


async def stage2_preview_search(
    companies: List[Dict[str, Any]],
    jd_requirements: Dict[str, Any],
    endpoint: str,
    max_previews: int,
    session_logger: SessionLogger
) -> Dict[str, Any]:
    """
    Stage 2: Preview search to test query quality.

    Args:
        companies: Discovered companies from Stage 1
        jd_requirements: Parsed JD requirements
        endpoint: CoreSignal endpoint (employee_base, employee_clean, multi_source_employee)
        max_previews: Number of previews to fetch (default: 20)
        session_logger: Session logger

    Returns:
        Dict with previews, relevance_score, etc.
    """
    print("\n" + "="*80)
    print("STAGE 2: Preview Search")
    print("="*80)

    start_time = time.time()

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

    print(f"Companies: {len(companies)}")
    print(f"Role Keywords: {role_keywords}")
    print(f"Endpoint: {endpoint}")

    # Build query
    query = build_domain_company_query(companies, role_keywords)

    # Log query
    query_log_data = {
        "stage": "preview_search_query",
        "input": {
            "endpoint": endpoint,
            "num_companies": len(companies),
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
            "error": error_msg
        }

    # Parse results
    previews = search_result.get('results', [])
    print(f"   ✅ Found {len(previews)} preview candidates")

    # Analyze relevance: Check how many have domain company experience
    domain_match_count = 0
    company_names_lower = [c['name'].lower() for c in companies]

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

    return {
        "previews": previews,
        "relevance_score": relevance_score,
        "total_found": len(previews)
    }


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


# Register blueprint in app.py
def register_domain_search_routes(app):
    """Register domain search blueprint with Flask app."""
    app.register_blueprint(domain_search_bp)
    print("✓ Domain Search routes registered successfully")
