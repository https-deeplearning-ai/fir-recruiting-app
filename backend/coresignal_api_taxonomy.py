"""
CoreSignal API Taxonomy Reference

This file documents the correct field structures, nested paths, and query types
for different CoreSignal API endpoints. Critical for building correct ES DSL queries.

Last Updated: 2025-11-05
Sources: CoreSignal official documentation, API testing, codebase analysis
"""

# ==============================================================================
# QUICK REFERENCE - ENDPOINT SELECTION
# ==============================================================================

# Use this table to quickly decide which endpoint to use
ENDPOINT_SELECTOR = {
    "need_full_linkedin_profile": "employee_base",  # 100+ fields
    "need_cleaned_normalized_data": "employee_clean",  # Normalized
    "need_multi_source_enrichment": "multi_source_employee",  # Richer
    "need_company_intelligence": "company_base",  # 45+ fields
    "need_basic_company_info": "company_clean",  # 10 fields
}

# Response format quick reference - CRITICAL for workflow design
RESPONSE_FORMATS = {
    "employee_base/search/es_dsl/preview": "full_profile_objects[]",  # Returns enriched profiles!
    "employee_base/search/es_dsl": "employee_ids[]",  # Returns IDs only
    "company_base/search/es_dsl": "company_ids[]",  # Two-step required!
    "company_base/collect/{id}": "full_company_object",  # Full data
    "employee_clean/search/es_dsl/preview": "full_profile_objects[]",
    "employee_clean/collect/{id}": "full_profile_object",
}

# Authentication headers - CRITICAL
AUTHENTICATION = {
    "header_name": "apikey",  # NOT "Authorization: Bearer"!
    "header_format": {"accept": "application/json", "apikey": "YOUR_API_KEY", "Content-Type": "application/json"},
    "common_mistake": "Using 'Authorization: Bearer' will cause 401 errors"
}

# Rate limiting
RATE_LIMITS = {
    "requests_per_second": 18,
    "recommended_concurrent": 15,  # Leave headroom
    "timeout_recommendation": 10  # seconds
}

# ==============================================================================
# EMPLOYEE APIs
# ==============================================================================

EMPLOYEE_BASE = {
    "endpoint": "/cdapi/v2/employee_base",
    "description": "Base employee data from LinkedIn (100+ fields)",
    "search_endpoint": "/cdapi/v2/employee_base/search/es_dsl/preview",
    "collect_endpoint": "/cdapi/v2/employee_base/collect/{employee_id}",

    # CRITICAL: Preview endpoint returns enriched profiles (not just IDs)
    "preview_returns": "enriched_profiles",  # Not just IDs!
    "search_returns": "employee_ids_only",  # Non-preview returns IDs

    "fields": {
        # Top-level fields
        "id": {"type": "integer", "description": "CoreSignal employee ID", "coverage": "100%"},
        "full_name": {"type": "string", "description": "Full name", "coverage": "100%"},
        "profile_url": {"type": "string", "description": "LinkedIn profile URL", "coverage": "100%"},
        "headline": {"type": "string", "description": "User-set headline (may be stale)", "coverage": "~80%"},
        "generated_headline": {"type": "string", "description": "Auto-generated headline (fresh, updated)", "coverage": "~95%"},
        "location": {"type": "string", "description": "City/region (e.g., 'San Francisco Bay Area')", "coverage": "~85%"},
        "country": {"type": "string", "description": "CRITICAL: Use this for country filtering (e.g., 'United States')", "coverage": "~90%", "query_type": "term"},
        "connections_count": {"type": "integer", "description": "LinkedIn connections count", "coverage": "~70%"},
        "follower_count": {"type": "integer", "description": "LinkedIn followers count", "coverage": "~60%"},
        "skills": {"type": "array", "description": "Array of skill names", "coverage": "~75%"},
        "websites_professional_network": {"type": "string", "description": "LinkedIn URL for search", "coverage": "100%"},

        # Nested: Work Experience (CRITICAL for company searches)
        "experience": {
            "type": "nested",
            "path": "experience",
            "description": "Array of work experiences",
            "fields": {
                "company_name": {"type": "string", "query_type": "match", "note": "CRITICAL: Use 'match' not 'wildcard' on /preview"},
                "company_id": {"type": "integer", "query_type": "term", "note": "Preferred for precise matching"},
                "company_url": {"type": "string", "description": "LinkedIn company page URL"},
                "company_website": {"type": "string", "description": "Company website"},
                "company_logo_url": {"type": "string", "description": "Company logo URL"},
                "company_shorthand_name": {"type": "string", "description": "Short company name"},
                "title": {"type": "string", "description": "Job title"},
                "description": {"type": "text", "description": "Job description"},
                "location": {"type": "string", "description": "Job location"},
                "date_from": {"type": "date", "description": "Start date"},
                "date_to": {"type": "date", "description": "End date (null if current)"},
                "date_from_year": {"type": "integer", "description": "Start year"},
                "date_from_month": {"type": "integer", "description": "Start month"},
                "is_current": {"type": "boolean", "description": "Currently employed here"}
            },
            "query_notes": {
                "company_name": "Use 'match' query type, NOT 'wildcard'. Wildcard returns 0 results on /preview endpoint.",
                "company_id": "Use 'term' query for exact ID match. Preferred over name matching.",
                "nested_required": "ALWAYS wrap experience queries in 'nested' query with path='experience'"
            }
        }
    },

    "query_examples": {
        "by_company_name": {
            "description": "Search for employees by company name (use 'match' not 'wildcard')",
            "query": {
                "nested": {
                    "path": "experience",
                    "query": {
                        "match": {
                            "experience.company_name": "Deepgram"
                        }
                    }
                }
            }
        },
        "by_company_id": {
            "description": "Search for employees by company ID (preferred, precise)",
            "query": {
                "nested": {
                    "path": "experience",
                    "query": {
                        "term": {
                            "experience.company_id": 6761084
                        }
                    }
                }
            }
        },
        "by_location_and_company": {
            "description": "Combined location + company filter (hybrid ID + name)",
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "country": "United States"  # CRITICAL: 'country' not 'location_country'
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    # ID-based filter (if available)
                                    {
                                        "nested": {
                                            "path": "experience",
                                            "query": {
                                                "term": {
                                                    "experience.company_id": 6761084
                                                }
                                            }
                                        }
                                    },
                                    # Name-based fallback
                                    {
                                        "nested": {
                                            "path": "experience",
                                            "query": {
                                                "bool": {
                                                    "should": [
                                                        {"match": {"experience.company_name": "Deepgram"}},
                                                        {"match": {"experience.company_name": "deepgram"}}
                                                    ],
                                                    "minimum_should_match": 1
                                                }
                                            }
                                        }
                                    }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            }
        },
        "by_job_title": {
            "description": "Search by current or past job titles",
            "query": {
                "bool": {
                    "should": [
                        # Current title
                        {"wildcard": {"active_experience_title": "*engineer*"}},
                        # Past titles
                        {
                            "nested": {
                                "path": "experience",
                                "query": {
                                    "wildcard": {
                                        "experience.title": "*engineer*"
                                    }
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }
    },

    "common_pitfalls": [
        "Using 'wildcard' instead of 'match' for company names on /preview endpoint (returns 0 results)",
        "Using 'location_country' instead of 'country' for country filtering",
        "Forgetting to wrap experience queries in 'nested' query block",
        "Not providing 'path': 'experience' in nested queries",
        "Using /search/es_dsl when you need full profiles (use /preview instead)"
    ]
}

EMPLOYEE_CLEAN = {
    "endpoint": "/v2/employee_clean",
    "description": "Cleaned/normalized employee data (verified structure)",
    "search_endpoint": "/v2/employee_clean/search/es_dsl/preview",
    "collect_endpoint": "/v2/employee_clean/collect/{employee_id}",
    "collect_by_shorthand": "/v2/employee_clean/collect/{shorthand_name}",  # Alternative

    "fields": {
        # Top-level fields (verified from coresignal_service.py usage)
        "id": {"type": "integer", "description": "CoreSignal employee ID"},
        "name": {"type": "string", "description": "Full name"},
        "url": {"type": "string", "description": "LinkedIn profile URL"},
        "title": {"type": "string", "description": "Current job title"},
        "headline": {"type": "string", "description": "LinkedIn headline"},
        "generated_headline": {"type": "string", "description": "Auto-generated headline"},
        "location": {"type": "string", "description": "Location string"},
        "experience": {"type": "array", "description": "Work history array (similar to employee_base)"},
        "websites_professional_network": {"type": "string", "description": "LinkedIn URL for search"},
    },

    "differences_from_employee_base": {
        "data_quality": "Cleaned and normalized (better for matching)",
        "field_names": "Some field names differ (e.g., 'name' vs 'full_name')",
        "use_case": "Use when data consistency is more important than richness"
    },

    "query_notes": {
        "status": "Partially documented - same query patterns as employee_base",
        "nested_queries": "Experience queries still require 'nested' wrapper"
    }
}

MULTI_SOURCE_EMPLOYEE = {
    "endpoint": "/cdapi/v2/multi_source_employee",
    "description": "Enhanced employee data from multiple sources (LinkedIn + others)",
    "search_endpoint": "/cdapi/v2/multi_source_employee/search/es_dsl",
    "collect_endpoint": "/cdapi/v2/multi_source_employee/collect/{employee_id}",

    "fields": {
        # Richer data structure with additional fields
        # Full documentation in: backend/jd_analyzer/docs/CORESIGNAL_FIELD_REFERENCE.md (484 lines)
        "note": "See CORESIGNAL_FIELD_REFERENCE.md for complete 6-tier field priority documentation",
        "tier1_company": "company_name, company_id, company_url, company_website",
        "tier2_location": "location, country, company_location",
        "tier3_role": "title, active_experience_title, headline",
        "tier4_funding": "company_funding_rounds (nested)",
        "tier5_seniority": "seniority_level, management_level",
        "tier6_skills": "skills array, technologies"
    },

    "query_notes": {
        "status": "Field structure documented, workflow needs verification",
        "search_behavior": "TODO: Test if /search returns IDs or full profiles",
        "collect_workflow": "TODO: Verify if two-step workflow required"
    },

    "reference_docs": "backend/jd_analyzer/docs/CORESIGNAL_FIELD_REFERENCE.md"
}

# ==============================================================================
# COMPANY APIs
# ==============================================================================

COMPANY_BASE = {
    "endpoint": "/cdapi/v2/company_base",
    "description": "Base company data (45+ fields, richer than company_clean)",
    "search_endpoint": "/cdapi/v2/company_base/search/es_dsl",
    "collect_endpoint": "/cdapi/v2/company_base/collect/{company_id}",

    # CRITICAL: Search returns IDs only (not full profiles)
    "search_returns": "company_ids_only",  # List[int]
    "workflow_required": "two_step",  # Must: search (IDs) → collect (full data)

    "fields": {
        # === BASIC INFO ===
        "id": {"type": "integer", "description": "CoreSignal company ID", "coverage": "100%"},
        "name": {"type": "string", "description": "Company name", "coverage": "100%"},
        "type": {"type": "string", "description": "Public/Private/Non-Profit", "coverage": "~80%"},
        "founded": {"type": "integer", "description": "Year founded", "coverage": "~70%"},
        "description": {"type": "text", "description": "Company description", "coverage": "~85%"},

        # === SIZE & EMPLOYEES ===
        "size_range": {"type": "string", "description": "Employee size range (e.g., '51-200')", "coverage": "~75%"},
        "size": {"type": "string", "description": "Alternative size field", "coverage": "~75%"},
        "employees_count": {"type": "integer", "description": "Exact employee count", "coverage": "~50%"},
        "size_employees_count_inferred": {"type": "integer", "description": "Inferred employee count", "coverage": "~70%"},

        # === INDUSTRY ===
        "industry": {"type": "string", "description": "Primary industry", "coverage": "~80%"},
        "specialties": {"type": "array", "description": "Array of specialties", "coverage": "~60%"},

        # === LOCATION (HQ) ===
        "location_hq_country": {"type": "string", "description": "HQ country", "coverage": "~85%"},
        "location_hq_city": {"type": "string", "description": "HQ city", "coverage": "~80%"},
        "location_hq_state": {"type": "string", "description": "HQ state/province", "coverage": "~75%"},
        "location_hq_raw_address": {"type": "string", "description": "Full HQ address", "coverage": "~70%"},

        # === CRUNCHBASE (CRITICAL for startup intelligence) ===
        "company_crunchbase_info_collection": {
            "type": "nested_array",
            "description": "Crunchbase company profile info (69.2% coverage)",
            "fields": {
                "cb_url": {"type": "string", "description": "Crunchbase company URL", "coverage": "69.2%"},
                "deleted": {"type": "integer", "description": "0=active, 1=deleted", "coverage": "100%"}
            },
            "note": "First entry with deleted=0 is the authoritative Crunchbase URL"
        },

        # === FUNDING (CRITICAL for startup assessment) ===
        "company_funding_rounds_collection": {
            "type": "nested_array",
            "description": "Funding rounds data (high coverage for funded companies)",
            "fields": {
                "last_round_type": {"type": "string", "description": "Latest funding type (Seed/Series A/B/C)", "examples": ["Seed", "Series A", "Series B"]},
                "last_round_date": {"type": "date", "description": "Latest funding date"},
                "last_round_money_raised": {"type": "float", "description": "Amount raised (in USD)", "note": "Format: 1000000 = $1M"},
                "total_rounds_count": {"type": "integer", "description": "Total number of funding rounds"},
                "last_round_investors_count": {"type": "integer", "description": "Number of investors in last round"},
                "cb_url": {"type": "string", "description": "Crunchbase funding round URL (NOT company URL)"}
            },
            "note": "Array sorted by date, first entry is latest round"
        },

        # === URLs & BRANDING ===
        "website": {"type": "string", "description": "Company website", "coverage": "~85%"},
        "url": {"type": "string", "description": "LinkedIn company page URL", "coverage": "~95%"},
        "logo_url": {"type": "string", "description": "Company logo URL (LinkedIn CDN)", "coverage": "~70%"},

        # === FINANCIAL ===
        "is_b2b": {"type": "boolean", "description": "B2B business model indicator", "coverage": "~40%"},
        "annual_revenue": {"type": "float", "description": "Annual revenue", "coverage": "~20%"},
        "annual_revenue_currency": {"type": "string", "description": "Revenue currency code", "coverage": "~20%"},

        # === STOCK INFO (for public companies) ===
        "ticker": {"type": "string", "description": "Stock ticker symbol", "coverage": "~5%"},
        "exchange": {"type": "string", "description": "Stock exchange", "coverage": "~5%"},

        # === SOCIAL PRESENCE ===
        "follower_count": {"type": "integer", "description": "LinkedIn follower count", "coverage": "~80%"},

        # === TECHNOLOGY STACK ===
        "technologies": {
            "type": "nested_array",
            "description": "Array of technology objects",
            "fields": {
                "name": {"type": "string", "description": "Technology name"}
            },
            "coverage": "~50%",
            "note": "Extract top 10 for display: [tech['name'] for tech in technologies[:10]]"
        },

        # === METADATA ===
        "last_updated": {"type": "timestamp", "description": "When CoreSignal last updated this data", "coverage": "100%"}
    },

    "query_examples": {
        "by_name": {
            "description": "Search for companies by name",
            "query": {
                "query_string": {
                    "query": "Google",
                    "default_field": "name",
                    "default_operator": "and"
                }
            }
        },
        "by_funding_stage": {
            "description": "Search for Series A companies (requires collect workflow)",
            "note": "Search returns IDs only. Must collect full data to filter by funding.",
            "workflow": "1. Search by name/industry → 2. Collect full data → 3. Filter by last_round_type"
        }
    },

    "workflow": {
        "step1": "Search returns company IDs: POST /search/es_dsl",
        "step2": "Collect full data: GET /collect/{company_id}",
        "example": "See coresignal_company_lookup.py for implementation",
        "note": "Two-step workflow required for full company profiles. Cache results to save API credits."
    },

    "common_pitfalls": [
        "Expecting full profiles from /search endpoint (only returns IDs)",
        "Not caching company data (wastes API credits on repeated lookups)",
        "Using funding round cb_url as company URL (they're different!)",
        "Not checking deleted=0 in crunchbase_info_collection"
    ]
}

COMPANY_CLEAN = {
    "endpoint": "/v2/company_clean",
    "description": "Cleaned company data (limited fields, ~10 vs 45+ in company_base)",
    "search_endpoint": "/v2/company_clean/search/es_dsl/preview",
    "collect_endpoint": "/v2/company_clean/collect/{company_id}",

    "fields": {
        # Limited field set compared to company_base
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "website": {"type": "string"},
        "location": {"type": "string"},
        "industry": {"type": "string"},
        "employees_count": {"type": "integer"},
        "description": {"type": "text"},
        "logo_url": {"type": "string"},
        "url": {"type": "string"}
        # Missing: funding data, crunchbase URLs, financial data, tech stack
    },

    "notes": "Prefer company_base for richer data (45+ vs ~10 fields). Only use company_clean if you need basic info and want to save API credits.",

    "comparison_to_company_base": {
        "pros": ["Simpler structure", "Faster queries", "Lower API cost"],
        "cons": ["No funding data", "No Crunchbase URLs", "No financial metrics", "No tech stack"]
    }
}

MULTI_SOURCE_COMPANY = {
    "endpoint": "/cdapi/v2/multi_source_company",
    "description": "Enhanced company data from multiple sources",
    "status": "Not currently used in codebase",

    "fields": {
        # TODO: Document when needed
        "note": "Prefer company_base for now. Evaluate multi_source_company if you need enrichment beyond LinkedIn."
    }
}

# ==============================================================================
# COMPARISON TABLES
# ==============================================================================

EMPLOYEE_API_COMPARISON = {
    "employee_base": {
        "pros": ["100+ fields", "Preview returns full profiles", "Most comprehensive"],
        "cons": ["Larger response size", "Slightly slower"],
        "use_when": "You need full LinkedIn profile data with all details"
    },
    "employee_clean": {
        "pros": ["Cleaned/normalized", "Good for matching", "Can search by shorthand name"],
        "cons": ["Fewer fields", "Different field names"],
        "use_when": "Data consistency is more important than richness"
    },
    "multi_source_employee": {
        "pros": ["Multiple data sources", "Richest data", "Additional fields"],
        "cons": ["More complex structure", "Higher API cost", "Workflow unclear"],
        "use_when": "You need enrichment beyond LinkedIn (use with caution)"
    }
}

COMPANY_API_COMPARISON = {
    "company_base": {
        "pros": ["45+ fields", "Funding data", "69.2% Crunchbase coverage", "Tech stack", "Financial data"],
        "cons": ["Two-step workflow required", "Larger response size"],
        "use_when": "You need detailed company intelligence (RECOMMENDED)",
        "fields_count": "45+"
    },
    "company_clean": {
        "pros": ["Simple structure", "Single-step", "Basic info"],
        "cons": ["Only ~10 fields", "No funding data", "No Crunchbase URLs"],
        "use_when": "You only need basic company info and want to minimize API costs",
        "fields_count": "~10"
    },
    "multi_source_company": {
        "pros": ["Multiple sources", "Potential for richer data"],
        "cons": ["Unclear benefits over company_base", "Not tested"],
        "use_when": "Evaluate if company_base is insufficient",
        "fields_count": "Unknown"
    }
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_employee_company_query(endpoint: str, company_name: str = None, company_id: int = None):
    """
    Build correct company filter query for employee search.

    Args:
        endpoint: 'employee_base', 'employee_clean', or 'multi_source_employee'
        company_name: Company name to search for
        company_id: Company ID to search for (preferred if available)

    Returns:
        Dict: ES DSL query fragment
    """
    if endpoint == "employee_base":
        if company_id:
            # ID-based search (exact match, preferred)
            return {
                "nested": {
                    "path": "experience",
                    "query": {
                        "term": {
                            "experience.company_id": company_id
                        }
                    }
                }
            }
        elif company_name:
            # Name-based search (use 'match' not 'wildcard')
            return {
                "nested": {
                    "path": "experience",
                    "query": {
                        "match": {
                            "experience.company_name": company_name
                        }
                    }
                }
            }

    elif endpoint == "employee_clean":
        # Same structure as employee_base
        if company_id:
            return {
                "nested": {
                    "path": "experience",
                    "query": {
                        "term": {
                            "experience.company_id": company_id
                        }
                    }
                }
            }
        elif company_name:
            return {
                "nested": {
                    "path": "experience",
                    "query": {
                        "match": {
                            "experience.company_name": company_name
                        }
                    }
                }
            }

    elif endpoint == "multi_source_employee":
        # TODO: Verify structure matches employee_base
        raise NotImplementedError("multi_source_employee structure needs verification")

    else:
        raise ValueError(f"Unknown endpoint: {endpoint}")


def get_location_query(endpoint: str, country: str):
    """
    Build correct location filter query.

    Args:
        endpoint: API endpoint name
        country: Country name

    Returns:
        Dict: ES DSL query fragment
    """
    if endpoint == "employee_base":
        return {
            "term": {
                "country": country  # CRITICAL: 'country' not 'location_country'
            }
        }
    elif endpoint == "employee_clean":
        # Same field name
        return {
            "term": {
                "country": country
            }
        }
    else:
        # TODO: Add other endpoints
        raise NotImplementedError(f"Location query for {endpoint} not yet documented")


def get_funding_stage_filter(company_data: dict, stages: list) -> bool:
    """
    Filter companies by funding stage.

    Args:
        company_data: Full company data from company_base/collect
        stages: List of funding stages (e.g., ['Seed', 'Series A'])

    Returns:
        bool: True if company matches any stage
    """
    funding_rounds = company_data.get('company_funding_rounds_collection', [])
    if not funding_rounds:
        return False

    latest_round = funding_rounds[0]
    last_round_type = latest_round.get('last_round_type')

    return last_round_type in stages


# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    # Example: Build query for Deepgram employees in the US
    from pprint import pprint

    print("=" * 80)
    print("EXAMPLE 1: Hybrid Query (ID + Name) for Deepgram Employees in US")
    print("=" * 80)

    # This is the recommended pattern: try ID first, fall back to name
    query = {
        "query": {
            "bool": {
                "must": [
                    # Location filter (CRITICAL: use 'country')
                    {"term": {"country": "United States"}},
                    # Company filter (hybrid: ID + name)
                    {
                        "bool": {
                            "should": [
                                # ID-based (if available)
                                {
                                    "nested": {
                                        "path": "experience",
                                        "query": {
                                            "term": {
                                                "experience.company_id": 6761084
                                            }
                                        }
                                    }
                                },
                                # Name-based fallback
                                {
                                    "nested": {
                                        "path": "experience",
                                        "query": {
                                            "bool": {
                                                "should": [
                                                    {"match": {"experience.company_name": "Deepgram"}},
                                                    {"match": {"experience.company_name": "deepgram"}}
                                                ],
                                                "minimum_should_match": 1
                                            }
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }
    }

    pprint(query)

    print("\n" + "=" * 80)
    print("EXAMPLE 2: Company Search Workflow (Two-Step)")
    print("=" * 80)
    print("""
    Step 1: Search for company ID
    POST /cdapi/v2/company_base/search/es_dsl
    {
        "query": {
            "query_string": {
                "query": "Deepgram",
                "default_field": "name",
                "default_operator": "and"
            }
        }
    }
    Response: [6761084]  # Company IDs only!

    Step 2: Collect full company data
    GET /cdapi/v2/company_base/collect/6761084
    Response: {...}  # Full 45+ fields including funding data
    """)

    print("\n" + "=" * 80)
    print("COMMON MISTAKES TO AVOID")
    print("=" * 80)
    print("""
    ❌ WRONG: Using 'wildcard' for company name on /preview
    {'wildcard': {'experience.company_name': '*Deepgram*'}}  # Returns 0 results!

    ✅ CORRECT: Using 'match' for company name
    {'match': {'experience.company_name': 'Deepgram'}}  # Works!

    ❌ WRONG: Using 'location_country' for filtering
    {'term': {'location_country': 'United States'}}  # Field doesn't exist!

    ✅ CORRECT: Using 'country' for filtering
    {'term': {'country': 'United States'}}  # Works!

    ❌ WRONG: Expecting full profiles from /search
    POST /cdapi/v2/company_base/search/es_dsl  # Returns IDs only!

    ✅ CORRECT: Two-step workflow for companies
    1. POST /search/es_dsl → [company_ids]
    2. GET /collect/{company_id} → full_data
    """)

    print("\n" + "=" * 80)
    print("QUICK REFERENCE LOADED")
    print("=" * 80)
    print("Use ENDPOINT_SELECTOR to choose the right API")
    print("Use RESPONSE_FORMATS to understand what each endpoint returns")
    print("Use EMPLOYEE_API_COMPARISON and COMPANY_API_COMPARISON for detailed comparisons")
