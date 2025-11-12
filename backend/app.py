import sys
import os

# Add backend directory to sys.path FIRST to allow utils imports
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import DATA_SOURCE_CORESIGNAL, DATA_SOURCE_STORAGE
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from datetime import datetime, timedelta
import calendar
import time
import random
from coresignal_service import CoreSignalService
from dotenv import load_dotenv
import requests
import csv
from io import StringIO
import hashlib

# Load environment variables from .env file
load_dotenv()


def safe_parse_timestamp(timestamp_str):
    """
    Safely parse ISO format timestamps with varying microsecond precision.

    Handles timestamps with 1-6 digit microseconds (e.g., '2025-11-10T19:19:52.69911+00:00')
    by padding microseconds to 6 digits.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        datetime object
    """
    if not timestamp_str:
        return None

    try:
        # Try direct parsing first (fastest path for properly formatted timestamps)
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        # If that fails, fix microsecond precision
        import re

        # Match timestamp with microseconds: YYYY-MM-DDTHH:MM:SS.microseconds+TZ
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)([\+\-]\d{2}:\d{2}|Z)'
        match = re.match(pattern, timestamp_str)

        if match:
            base_time = match.group(1)
            microseconds = match.group(2)
            timezone = match.group(3)

            # Pad or truncate microseconds to exactly 6 digits
            if len(microseconds) < 6:
                microseconds = microseconds.ljust(6, '0')  # Pad with zeros
            elif len(microseconds) > 6:
                microseconds = microseconds[:6]  # Truncate

            # Reconstruct timestamp with fixed microseconds
            fixed_timestamp = f"{base_time}.{microseconds}{timezone}"
            return datetime.fromisoformat(fixed_timestamp.replace('Z', '+00:00'))
        else:
            # No microseconds, try parsing as-is
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Session-based page tracking (resets on server restart)
used_pages_tracker = set()

# Initialize Anthropic client
anthropic_client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")  # Set your API key as environment variable
)

# Initialize services
coresignal_service = CoreSignalService()

# Import extension service (after defining constants)
try:
    from extension_service import ExtensionService
    extension_service = ExtensionService()
except ImportError as e:
    print(f"Warning: Could not import ExtensionService: {e}")
    extension_service = None

# Import JD Analyzer routes
try:
    from jd_analyzer.api.endpoints import register_jd_analyzer_routes, make_coresignal_request_with_retry
    register_jd_analyzer_routes(app)
    print("✓ JD Analyzer routes registered successfully")
except ImportError as e:
    print(f"Warning: Could not import JD Analyzer routes: {e}")
    # Fallback: define retry function here if import fails
    def make_coresignal_request_with_retry(url, payload, headers, max_retries=2, timeout=30):
        """Fallback retry function if JD Analyzer import fails"""
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return (True, response.json(), None)
                if response.status_code == 503 and attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Rate limit (503) - retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return (False, None, f"API error: {response.status_code}")
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return (False, None, str(e))
        return (False, None, "Max retries exceeded")

# Import Domain Search routes (new feature)
try:
    from jd_analyzer.api.domain_search import register_domain_search_routes
    register_domain_search_routes(app)
    print("✓ Domain Search routes registered successfully")
except ImportError as e:
    import traceback
    print(f"Warning: Could not import Domain Search routes: {e}")
    print(f"sys.path: {sys.path[:3]}")  # Debug: show first 3 paths
    traceback.print_exc()

# Import Load More Endpoints for company batching
try:
    from jd_analyzer.api.load_more_endpoint import bp as load_more_bp
    app.register_blueprint(load_more_bp)
    print("✓ Load More endpoints registered successfully")
except ImportError as e:
    print(f"Warning: Could not import Load More endpoints: {e}")

# Import Test Endpoint (temporary)
try:
    from test_endpoints_api import register_test_routes
    register_test_routes(app)
    print("✓ Test endpoint registered successfully")
except ImportError as e:
    print(f"Warning: Could not import test endpoint: {e}")

# CoreSignal API configuration
CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")

# Database configuration - using Supabase REST API
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Import dynamic configuration based on deployment environment
try:
    from config import MAX_CONCURRENT_CALLS, TIMEOUT_SECONDS, BATCH_SIZE, WORKERS
except ImportError:
    # Fallback configuration if config.py not found
    MAX_CONCURRENT_CALLS = 15  # Conservative default
    TIMEOUT_SECONDS = 25       # Safety margin
    BATCH_SIZE = 50            # Default batch size
    WORKERS = 1                # Single worker

def save_candidate_assessment(linkedin_url, full_name, headline, profile_data, assessment_data, assessment_type='single', session_name=None):
    """Save candidate assessment to database using Supabase REST API"""
    return save_to_supabase_api(linkedin_url, full_name, headline, profile_data, assessment_data, assessment_type, session_name)


def save_to_supabase_api(linkedin_url, full_name, headline, profile_data, assessment_data, assessment_type, session_name):
    """Save using Supabase REST API"""
    try:
        # Extract scores
        weighted_score = None
        overall_score = None
        
        if assessment_data:
            if assessment_data.get('weighted_analysis') and assessment_data['weighted_analysis'].get('weighted_score') is not None:
                try:
                    weighted_score = float(assessment_data['weighted_analysis']['weighted_score'])
                except (ValueError, TypeError):
                    weighted_score = None
            elif assessment_data.get('overall_score') is not None:
                try:
                    overall_score = float(assessment_data['overall_score'])
                except (ValueError, TypeError):
                    overall_score = None
        
        # Prepare data for Supabase API
        data = {
            'linkedin_url': linkedin_url,
            'full_name': full_name,
            'headline': headline,
            'profile_data': profile_data,
            'assessment_data': assessment_data,
            'weighted_score': weighted_score,
            'overall_score': overall_score,
            'assessment_type': assessment_type,
            'session_name': session_name
        }
        
        # Make API request to Supabase
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        url = f"{SUPABASE_URL}/rest/v1/candidate_assessments"
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ Saved assessment for {full_name} to database via Supabase API")
            return True
        else:
            print(f"❌ Supabase API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error saving assessment to Supabase API: {str(e)}")
        return False

def load_candidate_assessments(limit=50):
    """Load candidate assessments from database using Supabase REST API"""
    return load_from_supabase_api(limit)


def load_from_supabase_api(limit):
    """Load using Supabase REST API"""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Build query parameters
        params = {
            'select': '*',
            'order': 'weighted_score.desc,overall_score.desc,created_at.desc',
            'limit': str(limit)
        }
        
        url = f"{SUPABASE_URL}/rest/v1/candidate_assessments"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            assessments = response.json()
            print(f"✅ Loaded {len(assessments)} assessments from database via Supabase API")
            return assessments
        else:
            print(f"❌ Supabase API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error loading assessments from Supabase API: {str(e)}")
        return []

# ============================================
# STORAGE FUNCTIONS - SAVE API CREDITS!
# ============================================

def get_stored_profile(linkedin_url):
    """
    Check if profile is stored in database and determine if we should use it

    Smart Freshness Logic:
    - If < 3 days old: Use stored data (SAVE 1 Collect credit!)
    - If 3-90 days old: Use stored data BUT mark for background refresh
    - If > 90 days (3 months) old: FORCE fresh pull from CoreSignal

    Returns: dict with profile_data and metadata, or None if needs fresh pull
    """
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # URL encode the linkedin_url for the query
        import urllib.parse
        encoded_url = urllib.parse.quote(linkedin_url, safe='')

        url = f"{SUPABASE_URL}/rest/v1/stored_profiles?linkedin_url=eq.{encoded_url}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                stored = results[0]
                # Calculate age
                from datetime import datetime, timedelta
                last_fetched = datetime.fromisoformat(stored['last_fetched'].replace('Z', '+00:00'))
                age = datetime.now(last_fetched.tzinfo) - last_fetched
                age_days = age.days

                # FORCE fresh pull if > 90 days (3 months)
                if age_days >= 90:
                    print(f"⚠️ Stored profile is {age_days} days old (>90 days) - FORCING fresh pull")
                    return None

                # Use stored data if < 90 days
                print(f"✅ Using stored profile (age: {age_days} days) - SAVED 1 Collect credit!")

                # Note if it's getting stale (3-90 days)
                if age_days >= 3:
                    print(f"   ℹ️  Note: Profile is {age_days} days old, consider refreshing soon")

                return {
                    'profile_data': stored['profile_data'],
                    'checked_at': stored.get('checked_at'),
                    'last_fetched': stored.get('last_fetched'),  # When WE cached this data
                    'storage_age_days': age_days,
                    'is_stale': age_days >= 3
                }
        return None
    except Exception as e:
        print(f"⚠️ Error checking profile storage: {str(e)}")
        return None

def get_stored_profile_by_employee_id(employee_id):
    """
    Check if profile with this employee_id is stored in database

    This searches through stored profiles to find one matching the employee_id.
    Since employee_id is stored inside profile_data JSONB, we need to query that.

    Returns: dict with profile_data and metadata, or None if not found
    """
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # Query for profiles where profile_data->>'id' matches the employee_id
        # Using JSONB operator ->> to extract 'id' field
        url = f"{SUPABASE_URL}/rest/v1/stored_profiles?profile_data->>id=eq.{employee_id}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                stored = results[0]
                # Calculate age
                from datetime import datetime
                last_fetched = datetime.fromisoformat(stored['last_fetched'].replace('Z', '+00:00'))
                age = datetime.now(last_fetched.tzinfo) - last_fetched
                age_days = age.days

                # FORCE fresh pull if > 90 days (3 months)
                if age_days >= 90:
                    print(f"Stored profile is {age_days} days old (>90 days) - FORCING fresh pull")
                    return None

                # Use stored data if < 90 days
                print(f"Using stored profile (age: {age_days} days) - SAVED 1 Collect credit!")

                return {
                    'profile_data': stored['profile_data'],
                    'checked_at': stored.get('checked_at'),
                    'last_fetched': stored.get('last_fetched'),
                    'storage_age_days': age_days,
                    'is_stale': age_days >= 3
                }
        return None
    except Exception as e:
        print(f"Error checking profile storage by employee_id: {str(e)}")
        return None

def save_stored_profile(linkedin_url, profile_data, checked_at=None):
    """Save profile to storage"""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
        }

        data = {
            'linkedin_url': linkedin_url,
            'profile_data': profile_data,
            'checked_at': checked_at
        }

        url = f"{SUPABASE_URL}/rest/v1/stored_profiles"
        response = requests.post(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            # Get total count of stored profiles
            count_url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=count"
            count_headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Prefer': 'count=exact'
            }
            count_response = requests.get(count_url, headers=count_headers)
            total_count = count_response.headers.get('Content-Range', '0').split('/')[-1] if count_response.status_code == 200 else '?'

            print(f"💾 Saved profile to storage: {linkedin_url}")
            print(f"📊 Total profiles in cache: {total_count}")
            return True
        else:
            print(f"⚠️ Failed to save profile to cache: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"⚠️ Error saving profile to storage: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_stored_company(company_id, freshness_days=30):
    """
    Check if company is stored and fresh (< freshness_days old)
    Returns cached data if fresh, None if needs refresh
    """
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                cached = results[0]
                # Check freshness
                from datetime import datetime, timedelta
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
                        'last_fetched': cached['last_fetched'],  # When WE cached company data
                        'verification_data': verification_data
                    }
                else:
                    print(f"⏰ Stored company too old ({age.days} days) - fetching fresh data")
                    return None
        return None
    except Exception as e:
        print(f"⚠️ Error checking company storage: {str(e)}")
        return None

def save_stored_company(company_id, company_data):
    """Save company to storage"""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
        }

        data = {
            'company_id': company_id,
            'company_data': company_data
        }

        url = f"{SUPABASE_URL}/rest/v1/stored_companies"
        response = requests.post(url, json=data, headers=headers)

        if response.status_code in [200, 201]:
            print(f"💾 Saved company to storage")
            return True
        else:
            print(f"⚠️ Failed to save company to cache: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Error saving company to storage: {str(e)}")
        return False

def get_storage_functions():
    """
    Get storage functions dict for passing to enrichment methods.

    Returns:
        dict: {'get': get_stored_company, 'save': save_stored_company}
    """
    return {
        'get': get_stored_company,
        'save': save_stored_company
    }

def generate_search_cache_key(jd_requirements, endpoint):
    """
    Generate a cache key from search parameters
    Uses MD5 hash of normalized search criteria
    """
    import hashlib

    # Normalize the search parameters
    cache_data = {
        'target_domain': jd_requirements.get('target_domain', ''),
        'mentioned_companies': sorted(jd_requirements.get('mentioned_companies', [])),  # Sort for consistency
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
                from datetime import datetime, timedelta
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

def process_user_prompt_for_search(user_prompt: str) -> dict:
    """Process user prompt using Anthropic to extract search criteria"""
    try:
        # Get tech-related industries
        tech_industries = [ind for ind in VALID_INPUT_VALUES.get('company_industry', []) if any(keyword in ind for keyword in [
            'Technology', 'Software', 'IT ', 'Computer', 'Internet', 'Data', 'Mobile', 'Desktop', 'Embedded', 'Blockchain'
        ])]
        
        management_levels_str = json.dumps(VALID_INPUT_VALUES.get('management_level', []), indent=2)
        departments_str = json.dumps(VALID_INPUT_VALUES.get('department', []), indent=2)
        tech_industries_str = json.dumps(tech_industries, indent=2)
        all_industries_str = json.dumps(VALID_INPUT_VALUES.get('company_industry', []), indent=2)
        total_industries = len(VALID_INPUT_VALUES.get('company_industry', []))
        
        system_prompt = f"""You are an expert at extracting MINIMUM REQUIREMENTS from user prompts for LinkedIn profile searches and mapping them to valid Coresignal database values.

CRITICAL: 
1. Extract ONLY the absolute minimum requirements that MUST be met
2. You MUST use ONLY exact values from the provided lists - DO NOT make up or modify values
3. If user mentions an industry, find the closest matching value from the exact list
4. These will be used as hard filters - candidates must meet ALL requirements
5. **LOCATION CRITICAL**: If user specifies a city/region (like "San Francisco", "Bay Area", "New York", "Seattle"), preserve the EXACT city/region name in must_have_location. Only use "United States" if no specific location is mentioned.

===== VALID FIELD VALUES (USE ONLY THESE) =====

**management_level:** (Choose from ONLY these {len(VALID_INPUT_VALUES.get('management_level', []))} exact values)
{management_levels_str}

**department:** (Choose from ONLY these {len(VALID_INPUT_VALUES.get('department', []))} exact values)
{departments_str}

**company_industry:** (Choose from ONLY these {total_industries} exact values)

TECHNOLOGY-RELATED INDUSTRIES (most common for tech searches):
{tech_industries_str}

ALL AVAILABLE INDUSTRIES (full list - search this for non-tech):
{all_industries_str}

LOCATION EXAMPLES:
- "Find me people in San Francisco" → "must_have_location": "San Francisco"
- "Find me Bay Area engineers" → "must_have_location": "San Francisco Bay Area"  
- "Find me New York developers" → "must_have_location": "New York"
- "Find me US-based candidates" → "must_have_location": "United States"

Return a JSON object with ONLY minimum requirements:
{{
    "must_have_location": "United States",
    "must_have_industries": ["Technology, Information and Internet", "Software Development"],
    "must_have_role_titles": ["CTO", "Director", "VP", "Head", "Lead", "Chief"],
    "must_have_management_levels": ["C-Level", "Director", "VP"],
    "must_have_departments": null,
    "must_have_skills_in_headline": ["AI", "ML", "Machine Learning"],
    "must_have_experience_years": 5,
    "explanation": "Brief explanation of extracted criteria"
}}"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Updated to Claude Sonnet 4.5 - best for coding and complex agents
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON from response
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
        
        return json.loads(json_str)
        
    except Exception as e:
        print(f"Error processing user prompt: {e}")
        return {}

def build_intelligent_elasticsearch_query(criteria: dict) -> dict:
    """Build Elasticsearch DSL query from extracted criteria"""
    must_conditions = []
    
    # Always include working status - use match instead of term for compatibility
    must_conditions.append({"match": {"is_working": 1}})
    
    # Location
    if criteria.get("must_have_location"):
        location = criteria["must_have_location"]
        location_conditions = []
        
        if location.lower() in ["united states", "us", "usa", "america"]:
            location_conditions.append({"term": {"location_country": "United States"}})
            location_conditions.append({"term": {"location_country": "US"}})
            location_conditions.append({"term": {"location_country": "USA"}})
        else:
            # Handle specific location variations for better matching
            location_lower = location.lower()
            
            # Bay Area variations
            if "bay area" in location_lower or "san francisco" in location_lower:
                bay_area_variations = [
                    "*bay area*", "*san francisco*", "*sf bay*", "*silicon valley*",
                    "*palo alto*", "*mountain view*", "*sunnyvale*", "*cupertino*",
                    "*menlo park*", "*redwood city*", "*fremont*", "*hayward*",
                    "*oakland*", "*berkeley*", "*san mateo*", "*foster city*"
                ]
                for variation in bay_area_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # New York variations
            elif "new york" in location_lower or "nyc" in location_lower:
                ny_variations = [
                    "*new york*", "*nyc*", "*manhattan*", "*brooklyn*", "*queens*",
                    "*bronx*", "*staten island*", "*long island*"
                ]
                for variation in ny_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # Los Angeles variations
            elif "los angeles" in location_lower or "la" in location_lower:
                la_variations = [
                    "*los angeles*", "*la*", "*hollywood*", "*beverly hills*",
                    "*santa monica*", "*venice*", "*west hollywood*", "*pasadena*"
                ]
                for variation in la_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # Seattle variations
            elif "seattle" in location_lower:
                seattle_variations = [
                    "*seattle*", "*bellevue*", "*redmond*", "*kirkland*"
                ]
                for variation in seattle_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # Boston variations
            elif "boston" in location_lower:
                boston_variations = [
                    "*boston*", "*cambridge*", "*somerville*", "*brookline*"
                ]
                for variation in boston_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # Austin variations
            elif "austin" in location_lower:
                austin_variations = [
                    "*austin*", "*round rock*", "*cedar park*"
                ]
                for variation in austin_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            # Chicago variations
            elif "chicago" in location_lower:
                chicago_variations = [
                    "*chicago*", "*evanston*", "*oak park*"
                ]
                for variation in chicago_variations:
                    location_conditions.append({"wildcard": {"location_raw_address": variation}})
                    location_conditions.append({"wildcard": {"location_country": variation}})
            else:
                # For other locations, use wildcard with the original location
                location_conditions.append({"wildcard": {"location_raw_address": f"*{location.lower()}*"}})
                location_conditions.append({"wildcard": {"location_country": f"*{location.lower()}*"}})
        
        if location_conditions:
            must_conditions.append({
                "bool": {"should": location_conditions, "minimum_should_match": 1}
            })
    
    # Industry
    if criteria.get("must_have_industries"):
        industry_conditions = []
        for industry in criteria["must_have_industries"]:
            industry_conditions.append({
                "nested": {
                    "path": "experience",
                    "query": {"term": {"experience.company_industry.exact": industry}}
                }
            })
        
        if industry_conditions:
            must_conditions.append({
                "bool": {"should": industry_conditions, "minimum_should_match": 1}
            })
    
    # Role titles
    if criteria.get("must_have_role_titles"):
        role_conditions = []
        for role in criteria["must_have_role_titles"]:
            role_conditions.append({"wildcard": {"job_title": f"*{role.lower()}*"}})
        
        if role_conditions:
            must_conditions.append({
                "bool": {"should": role_conditions, "minimum_should_match": 1}
            })
    
    # Management levels
    if criteria.get("must_have_management_levels") and not criteria.get("must_have_role_titles"):
        mgmt_conditions = []
        for level in criteria["must_have_management_levels"]:
            mgmt_conditions.append({"term": {"management_level": level}})
        
        if mgmt_conditions:
            must_conditions.append({
                "bool": {"should": mgmt_conditions, "minimum_should_match": 1}
            })
    
    # Skills in headline
    if criteria.get("must_have_skills_in_headline"):
        skill_conditions = []
        for skill in criteria["must_have_skills_in_headline"][:3]:
            skill_conditions.append({"wildcard": {"headline": f"*{skill.lower()}*"}})
            skill_conditions.append({"term": {"skills": skill}})
        
        if skill_conditions:
            must_conditions.append({
                "bool": {"should": skill_conditions, "minimum_should_match": 1}
            })
    
    # Experience years
    if criteria.get("must_have_experience_years"):
        must_conditions.append({
            "range": {
                "total_experience_duration_months": {
                    "gte": criteria["must_have_experience_years"] * 12
                }
            }
        })
    
    query = {
        "query": {"bool": {"must": must_conditions}},
        "sort": ["_score"]
    }
    
    return query

def search_coresignal_profiles_preview(criteria: dict, page: int = 1) -> dict:
    """
    Search for profiles using Coresignal API /preview endpoint.
    Returns full profile objects. Limited to pages 1-5.
    """
    headers = {
        "accept": "application/json",
        "apikey": CORESIGNAL_API_KEY,
        "Content-Type": "application/json"
    }
    
    query = build_intelligent_elasticsearch_query(criteria)
    
    # Debug: Print the actual query being sent
    print(f"🔍 DEBUG: Elasticsearch query being sent:")
    print(json.dumps(query, indent=2))
    
    # Use the /preview endpoint with page parameter (max page=5)
    url = f"https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page={page}"

    print(f"📄 Fetching page {page}...")

    # Use retry logic for 503 rate limit errors
    success, data, error_msg = make_coresignal_request_with_retry(
        url=url,
        payload=query,
        headers=headers,
        max_retries=3,  # Increased retries for better reliability
        timeout=30
    )

    if success:
        # /preview returns full profile objects
        results = data if isinstance(data, list) else []
        print(f"   ✅ Got {len(results)} full profiles from page {page}")

        return {
            "success": True,
            "results": results,
            "page": page,
            "total_found": len(results)
        }
    else:
        print(f"   ❌ Error: {error_msg}")
        return {"success": False, "error": error_msg}

def convert_search_results_to_csv(results: list) -> str:
    """Convert search results to CSV format for batch processing"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Profile URL', 'First Name', 'Last Name', 'Full Name', 'Headline', 'Location', 'Current Title'])
    
    # Write data
    for profile in results:
        profile_url = profile.get('websites_linkedin', '')
        full_name = profile.get('full_name', '')
        first_name = profile.get('name_first', '')
        last_name = profile.get('name_last', '')
        # Use generated_headline (fresh, auto-updated) over headline (stale, manually-set)
        headline = profile.get('generated_headline') or profile.get('headline', '')
        location = profile.get('location_raw_address', '')
        job_title = profile.get('job_title', '')
        
        writer.writerow([profile_url, first_name, last_name, full_name, headline, location, job_title])
    
    return output.getvalue()

def extract_profile_summary(profile_data):
    """Extract key information from LinkedIn profile for analysis"""
    try:
        # Basic info
        full_name = profile_data.get('full_name', 'N/A')
        # Use generated_headline (fresh, auto-updated) over headline (stale, manually-set)
        headline = profile_data.get('generated_headline') or profile_data.get('headline')

        # Experience
        experiences = profile_data.get('experience', [])

        # If no headline, fallback to most recent job title
        if not headline:
            if experiences and len(experiences) > 0:
                most_recent = experiences[0]
                title = most_recent.get('title', '')
                company = most_recent.get('company_name', '')
                if title and company:
                    headline = f"{title} at {company}"
                elif title:
                    headline = title

        # Final fallback
        if not headline:
            headline = 'N/A'

        location = profile_data.get('location', 'N/A')
        industry = profile_data.get('industry', 'N/A')
        current_roles = [exp for exp in experiences if exp.get('is_current', 0) == 1]
        
        # Calculate total experience years without double-counting overlaps
        def to_date(year: int, month: int, is_end: bool) -> datetime:
            """Create a datetime at start or end of given month/year."""
            # Ensure year and month are integers
            year = int(year) if year else datetime.now().year
            month = int(month) if month else (12 if is_end else 1)
            month = max(1, min(12, month))
            if is_end:
                last_day = calendar.monthrange(year, month)[1]
                return datetime(year, month, last_day)
            return datetime(year, month, 1)

        # Build normalized intervals (start, end) in datetime
        intervals = []
        now = datetime.now()
        for exp in experiences:
            try:
                start_year = exp.get('date_from_year')
                end_year = exp.get('date_to_year')
                if not start_year:
                    continue  # cannot use this interval without a start year

                start_month = exp.get('date_from_month')
                start_month = int(start_month) if start_month else 1

                # If current role, use 'now' as the end date
                is_current = bool(exp.get('is_current')) or exp.get('is_current', 0) == 1
                if is_current:
                    end_dt = now
                elif end_year:
                    end_month = exp.get('date_to_month')
                    end_month = int(end_month) if end_month else 12
                    end_dt = to_date(int(end_year), end_month, is_end=True)
                else:
                    # No end given and not flagged current; assume ongoing
                    end_dt = now

                start_dt = to_date(int(start_year), start_month, is_end=False)
                if end_dt <= start_dt:
                    continue
                intervals.append((start_dt, end_dt))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Skipping experience with invalid dates: {e}")
                continue

        # Merge overlapping intervals
        intervals.sort(key=lambda x: x[0])
        merged = []
        for interval in intervals:
            if not merged or interval[0] > merged[-1][1]:
                merged.append([interval[0], interval[1]])
            else:
                # extend the last interval
                merged[-1][1] = max(merged[-1][1], interval[1])

        # Sum total months across merged intervals
        def months_between(a: datetime, b: datetime) -> int:
            return (b.year - a.year) * 12 + (b.month - a.month) + (1 if b.day >= a.day else 0)

        total_months = sum(months_between(s, e) for s, e in merged)
        total_years = round(total_months / 12.0, 1)
        
        # Certifications
        certifications = profile_data.get('certifications', [])
        cert_titles = [cert.get('title', '') for cert in certifications]
        
        # Recommendations
        recommendations = profile_data.get('recommendations', [])
        rec_count = len(recommendations)
        
        # Connections
        connections_count = profile_data.get('connections_count', 0)
        
        # Map CoreSignal's last_updated to checked_at for frontend freshness badge
        checked_at = profile_data.get('last_updated') or profile_data.get('checked_at')

        return {
            'full_name': full_name,
            'headline': headline,
            'location': location,
            'industry': industry,
            'current_roles': current_roles,
            'total_experience_years': total_years,
            'certifications': cert_titles,
            'recommendations_count': rec_count,
            'connections_count': connections_count,
            'total_experiences': len(experiences),
            'experiences': experiences,
            'checked_at': checked_at  # CoreSignal's last scrape timestamp for freshness badge
        }
    except Exception as e:
        return {'error': f'Error processing profile: {str(e)}'}

def format_company_intelligence(experiences):
    """Format enriched company intelligence for Claude's assessment"""
    if not experiences:
        return "No experience data available"

    formatted = []
    for i, exp in enumerate(experiences, 1):
        title = exp.get('title', 'Unknown Role')
        company_name = exp.get('company_name', 'Unknown Company')
        date_from = exp.get('date_from', 'Unknown')
        date_to = exp.get('date_to') or 'Present'
        duration = exp.get('duration', 'Unknown duration')

        # Basic company info (always available)
        company_info = []
        if exp.get('company_employees_count'):
            company_info.append(f"{exp['company_employees_count']} employees")
        elif exp.get('company_size'):
            company_info.append(exp['company_size'])

        if exp.get('company_industry'):
            company_info.append(exp['company_industry'])

        # Enriched company intelligence (if available)
        enriched = exp.get('company_enriched')
        if enriched:
            # Company stage and type
            stage_info = []
            if enriched.get('type'):
                stage_info.append(enriched['type'])
            if enriched.get('inferred_stage'):
                stage_info.append(f"{enriched['inferred_stage'].replace('_', ' ').title()} stage")
            if enriched.get('company_age_years'):
                stage_info.append(f"{enriched['company_age_years']} years old")

            if stage_info:
                company_info.append(" | ".join(stage_info))

            # Funding signals
            funding_info = []
            if enriched.get('last_funding_type'):
                funding_info.append(f"Last round: {enriched['last_funding_type']}")
            if enriched.get('last_funding_amount'):
                try:
                    amount = float(enriched['last_funding_amount'])
                    if amount >= 1000000:
                        funding_info.append(f"${amount/1000000:.1f}M raised")
                    else:
                        funding_info.append(f"${amount:,} raised")
                except (ValueError, TypeError):
                    # If amount can't be converted to number, skip it
                    pass
            if enriched.get('total_funding_rounds'):
                funding_info.append(f"{enriched['total_funding_rounds']} total rounds")

            if funding_info:
                company_info.append(" | ".join(funding_info))

            # Business model & location
            extra_info = []
            if enriched.get('is_b2b'):
                extra_info.append("B2B")
            if enriched.get('hq_city'):
                hq = enriched['hq_city']
                if enriched.get('hq_state'):
                    hq += f", {enriched['hq_state']}"
                extra_info.append(f"HQ: {hq}")

            if extra_info:
                company_info.append(" | ".join(extra_info))

            # Growth signals
            if enriched.get('growth_signals'):
                signals = enriched['growth_signals']
                signal_labels = {
                    'hypergrowth_potential': '🚀 Hypergrowth',
                    'recently_funded': '💰 Recently Funded',
                    'b2b_model': '🏢 B2B',
                    'modern_tech_stack': '⚙️ Modern Tech',
                    'strong_brand': '⭐ Strong Brand'
                }
                signal_tags = [signal_labels.get(s, s) for s in signals]
                if signal_tags:
                    company_info.append("Signals: " + ", ".join(signal_tags))

        # Format the experience entry
        company_context = f"\n    Company Context: {' | '.join(company_info)}" if company_info else ""
        formatted.append(
            f"{i}. {title} at {company_name}\n"
            f"    Duration: {date_from} - {date_to} ({duration})"
            f"{company_context}"
        )

    return "\n\n".join(formatted)

def generate_assessment_prompt(profile_summary, user_prompt, weighted_requirements):
    """Generate the prompt for Claude to assess the LinkedIn profile"""

    # Build weighted requirements section
    weighted_section = ""
    total_user_weight = sum(req.get('weight', 0) for req in weighted_requirements) if weighted_requirements else 0
    general_fit_weight = max(0, 100 - total_user_weight)

    if weighted_requirements or general_fit_weight > 0:
        weighted_section = f"""

WEIGHTED ASSESSMENT CRITERIA:
The following criteria should be weighted according to the specified percentages in your overall assessment:

"""
        for req in weighted_requirements or []:
            if req.get('weight', 0) > 0:
                weighted_section += f"- {req.get('text', '')}: {req.get('weight', 0)}% weight\n"

        if general_fit_weight > 0:
            weighted_section += f"- General Fit: {general_fit_weight}% weight\n"

        weighted_section += f"""
Please ensure your assessment reflects these weightings. For example, if "Startup Experience" has 40% weight,
spend 40% of your analysis on evaluating startup experience and its relevance to the role.
"""

    # Format work history with detailed company intelligence
    experiences_formatted = format_company_intelligence(profile_summary.get('experiences', []))

    # Check if we have enriched company data
    has_enriched_data = any(exp.get('company_enriched') for exp in profile_summary.get('experiences', []))

    company_analysis_guidance = ""
    if has_enriched_data:
        company_analysis_guidance = """

COMPANY INTELLIGENCE ANALYSIS:
Each experience includes detailed company intelligence (type, stage, funding, growth signals, etc.).
Use this data to make sophisticated assessments:

1. STARTUP EXPERIENCE VALIDATION:
   - Look for companies with "Seed", "Series A/B" stage indicators
   - Check employee counts (< 100 = early-stage, 100-500 = growth, 500+ = mature)
   - Identify hypergrowth signals (recent funding, young companies with large raises)

2. SCALE EXPERIENCE ASSESSMENT:
   - Analyze career trajectory through company sizes (e.g., 20 → 100 → 500 employees)
   - Identify if candidate rode company growth vs. joined mature companies
   - Consider if they were promoted during company scaling phases

3. COMPANY QUALITY SIGNALS:
   - Well-funded companies (large raises, multiple rounds) = credible experience
   - B2B companies = different skill sets vs. B2C
   - Public companies = established processes and scale
   - Modern tech stack = engineering culture indicator

4. STRATEGIC DECISION-MAKING:
   - Assess if candidate joined companies at smart inflection points (before growth)
   - Consider geographic choices (moved to SF Bay Area for startup = signal)
   - Evaluate company failures vs. successes in their history

BE SPECIFIC in your analysis - cite actual company data like "joined at 45 employees, grew to 200 during tenure"
or "Series B company with $50M raised indicates significant validation".
"""

    base_prompt = f"""
You are an objective, evidence-first hiring assessor. You will read the provided LinkedIn profile data and the hiring criteria. Be strict and conservative.

Profile Summary:
- Name: {profile_summary.get('full_name', 'N/A')}
- Location: {profile_summary.get('location', 'N/A')}
- Industry: {profile_summary.get('industry', 'N/A')}
- Total Years of Experience: {profile_summary.get('total_experience_years', 0)}
- Number of Positions: {profile_summary.get('total_experiences', 0)}

DETAILED WORK HISTORY WITH COMPANY INTELLIGENCE:
{experiences_formatted}{company_analysis_guidance}

Please provide a comprehensive assessment with the following scoring criteria:

SCORING RUBRIC (1-10 scale):
- 9-10: Exceptional fit - meets all key requirements for the role, strong evidence of success
- 7-8: Good fit - minor gaps but demonstrates strong potential and relevant experience
- 5-6: Moderate fit - some significant gaps but shows potential with development
- 3-4: Poor fit - major gaps, better suited for different roles, significant concerns
- 1-2: Not recommended - fundamental mismatches, lacks basic requirements

BINARY RECOMMENDATION:
- "recommend": true if you would recommend reaching out for this specific role (6+ score)
- "recommend": false if the candidate is not suitable/not strong enough for this role (1-5 score)

Please provide:
1. An overall profile strength score (1-10) based on fit for the specific role
2. Key strengths (in relation to the user's prompt and weighted criteria) identified
3. Key weaknesses (in relation to the user's prompt and weighted criteria) identified
4. Career trajectory analysis (in relation to the user's prompt and weighted criteria)
5. Binary recommendation (true/false) for reaching out
6. Weighted analysis with individual scores for each requirement:
   - For each weighted requirement, provide a score (1-10) and detailed analysis
   - Calculate a weighted score based on the individual scores and their weights
   - Include general fit score and weight for the remaining percentage
   - The weighted score should align with your overall score

Assessment Criteria: {user_prompt}{weighted_section}

Please format your response as JSON with the following structure:
{{
    "overall_score": <number 1-10>,
    "recommend": <boolean true/false>,
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "career_trajectory": "analysis of career progression",
    "weighted_analysis": {{
        "requirements": [
            {{
                "requirement": "requirement text",
                "weight": <percentage>,
                "score": <number 1-10>,
                "analysis": "detailed analysis of this specific requirement"
            }}
        ],
        "weighted_score": <calculated weighted score 1-10>,
        "general_fit_score": <score for general fit 1-10>,
        "general_fit_weight": <percentage for general fit>,
        "general_fit_analysis": "detailed analysis of general fit"
    }}
}}
"""
    
    return base_prompt

@app.route('/fetch-profile', methods=['POST'])
def fetch_profile():
    """Fetch LinkedIn profile data from CoreSignal API with optional company enrichment"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        linkedin_url = data.get('linkedin_url')
        enrich_companies = data.get('enrich_companies', True)  # Default to True for detailed company data
        force_refresh = data.get('force_refresh', False)  # NEW: Allow forcing fresh data pull

        if not linkedin_url:
            return jsonify({'error': 'LinkedIn URL is required'}), 400

        # Validate LinkedIn URL format
        if not linkedin_url.startswith('https://www.linkedin.com/in/'):
            return jsonify({'error': 'Invalid LinkedIn URL format. Please use: https://www.linkedin.com/in/username'}), 400

        # ============================================
        # CHECK STORAGE FIRST - SAVE API CREDITS!
        # ============================================
        # Skip storage check if user requests force refresh
        if force_refresh:
            print("🔄 FORCE REFRESH requested - bypassing storage and fetching fresh data...")
            stored_result = None
        else:
            print("🔍 Checking if profile is stored in database...")
            stored_result = get_stored_profile(linkedin_url)

        if stored_result:
            # Found stored profile! Use it and save 1 Collect credit
            print(f"✅ Using stored profile (saves 1 Collect credit!)")
            profile_data = stored_result['profile_data']
            storage_age_days = stored_result.get('storage_age_days', 0)
            checked_at = stored_result.get('checked_at')
            last_fetched = stored_result.get('last_fetched')  # When WE cached this
            # Build result dict for cached profile (for response building later)
            result = {
                'success': True,
                'method': DATA_SOURCE_STORAGE,
                'data_source': DATA_SOURCE_STORAGE,
                'is_fresh': False,
                'storage_age_days': storage_age_days
            }
        else:
            # Not in storage or too old (>90 days) - fetch fresh from CoreSignal
            print("📦 Fetching fresh profile from CoreSignal...")
            result = coresignal_service.fetch_linkedin_profile(linkedin_url)

            if not result['success']:
                error_response = {'error': result['error']}
                if 'debug_info' in result:
                    error_response['debug_info'] = result['debug_info']
                return jsonify(error_response), 400

            profile_data = result['profile_data']
            checked_at = profile_data.get('checked_at')
            last_fetched = None  # Fresh from API, not from cache
            storage_age_days = 0  # Fresh from API

            # Save to storage for next time
            print("💾 Saving profile to storage for future use...")
            save_stored_profile(linkedin_url, profile_data, checked_at)

        # OPTIONAL: Enrich with detailed company data
        enrichment_summary = None
        if enrich_companies:
            print("🏢 Enriching profile with detailed company data...")
            # Changed min_year to 2015 to show tooltips for more companies
            # Pass storage functions to save API credits on company enrichment
            storage_functions = {
                'get': get_stored_company,
                'save': save_stored_company
            }
            enrichment_result = coresignal_service.enrich_profile_with_company_data(
                profile_data,
                min_year=2015,
                storage_functions=storage_functions
            )
            profile_data = enrichment_result['profile_data']
            enrichment_summary = enrichment_result['enrichment_summary']
            print(f"✅ Company enrichment complete: {enrichment_summary['companies_enriched']} companies enriched, {enrichment_summary['api_calls_made']} API calls made")

        # Extract profile summary for frontend display
        profile_summary = extract_profile_summary(profile_data)

        response_data = {
            'success': True,
            'profile_data': profile_data,
            'profile_summary': profile_summary,  # Add profile summary for frontend
            'data_source': result.get('method', result.get('data_source', DATA_SOURCE_CORESIGNAL)),
            'is_fresh': result.get('is_fresh', False)
        }

        # Add last_fetched timestamp if available (when loaded from cache)
        if last_fetched:
            response_data['last_fetched'] = last_fetched

        # Add employee_id if available (from CoreSignal)
        if 'employee_id' in result:
            response_data['employee_id'] = result['employee_id']

        # Add enrichment summary if company data was fetched
        if enrichment_summary:
            response_data['enrichment_summary'] = enrichment_summary

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full traceback to console
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/fetch-profile-by-id/<employee_id>', methods=['GET'])
def fetch_profile_by_id(employee_id):
    """Fetch full profile data by CoreSignal employee ID"""
    try:
        print(f"Fetching profile for employee ID: {employee_id}")

        # Check storage first to save API credits
        # Try to find by employee_id in existing stored profiles
        stored_result = get_stored_profile_by_employee_id(employee_id)

        if stored_result:
            print(f"Using stored profile for employee ID {employee_id} (saves 1 Collect credit!)")
            profile_data = stored_result['profile_data']
            storage_age_days = stored_result.get('storage_age_days', 0)

            # Enrich with company data (logos, funding, etc.)
            print(f"Enriching cached profile with company data...")
            storage_functions = get_storage_functions()
            enriched_result = coresignal_service.enrich_profile_with_company_data(
                profile_data,
                storage_functions=storage_functions
            )

            # Extract profile_data and enrichment_summary from result
            enriched_profile = enriched_result['profile_data']
            enrichment_summary = enriched_result['enrichment_summary']

            # Extract profile summary
            profile_summary = extract_profile_summary(enriched_profile)

            return jsonify({
                'success': True,
                'profile': enriched_profile,
                'profile_summary': profile_summary,
                'enrichment_summary': enrichment_summary,
                'data_source': DATA_SOURCE_STORAGE,
                'storage_age_days': storage_age_days
            })

        # Not in storage - fetch from CoreSignal
        print(f"Fetching fresh profile from CoreSignal for ID {employee_id}...")
        result = coresignal_service.fetch_profile_by_id(employee_id)

        if not result['success']:
            return jsonify({'error': result['error']}), 400

        profile_data = result['profile_data']

        # Enrich with company data (logos, funding, etc.)
        print(f"Enriching profile with company data...")
        storage_functions = get_storage_functions()
        enriched_result = coresignal_service.enrich_profile_with_company_data(
            profile_data,
            storage_functions=storage_functions
        )

        # Extract profile_data and enrichment_summary from result
        enriched_profile = enriched_result['profile_data']
        enrichment_summary = enriched_result['enrichment_summary']

        # Save to storage for next time (if we can extract LinkedIn URL)
        linkedin_url = None
        if 'url' in enriched_profile:
            linkedin_url = enriched_profile['url']
        elif 'websites_professional_network' in enriched_profile and enriched_profile['websites_professional_network']:
            linkedin_url = enriched_profile['websites_professional_network'][0] if isinstance(enriched_profile['websites_professional_network'], list) else enriched_profile['websites_professional_network']

        if linkedin_url:
            print(f"Saving enriched profile to storage for future use...")
            checked_at = enriched_profile.get('checked_at')
            save_stored_profile(linkedin_url, enriched_profile, checked_at)

        # Extract profile summary
        profile_summary = extract_profile_summary(enriched_profile)

        return jsonify({
            'success': True,
            'profile': enriched_profile,
            'profile_summary': profile_summary,
            'enrichment_summary': enrichment_summary,
            'data_source': DATA_SOURCE_CORESIGNAL,
            'employee_id': employee_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/assess-profile', methods=['POST'])
def assess_profile():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        profile_data = data.get('profile_data')
        user_prompt = data.get('user_prompt', 'Provide a general professional assessment')
        weighted_requirements = data.get('weighted_requirements', [])
        
        if not profile_data:
            return jsonify({'error': 'Profile data is required'}), 400
        
        # Extract key information from profile
        profile_summary = extract_profile_summary(profile_data)
        
        if 'error' in profile_summary:
            return jsonify(profile_summary), 400
        
        # Generate assessment prompt
        assessment_prompt = generate_assessment_prompt(profile_summary, user_prompt, weighted_requirements)
        
        # Call Claude API
        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Updated to Claude Sonnet 4.5 - best for coding and complex agents
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": assessment_prompt
                    }
                ]
            )
            
            # Parse Claude's response
            claude_response = message.content[0].text
            print(f"Claude response: {claude_response[:200]}...")  # Debug: show first 200 chars
            
            # Clean the response by removing markdown code blocks
            cleaned_response = claude_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            # Try to parse as JSON, fallback to plain text if it fails
            try:
                assessment_result = json.loads(cleaned_response)
                # Ensure all expected fields exist
                if 'overall_score' not in assessment_result:
                    assessment_result['overall_score'] = "N/A"
                if 'recommend' not in assessment_result:
                    assessment_result['recommend'] = False
                if 'strengths' not in assessment_result:
                    assessment_result['strengths'] = []
                if 'weaknesses' not in assessment_result:
                    assessment_result['weaknesses'] = []
                if 'career_trajectory' not in assessment_result:
                    assessment_result['career_trajectory'] = "N/A"
                if 'detailed_analysis' not in assessment_result:
                    assessment_result['detailed_analysis'] = claude_response
            except json.JSONDecodeError:
                assessment_result = {
                    "overall_score": "N/A",
                    "recommend": False,
                    "strengths": [],
                    "weaknesses": [],
                    "career_trajectory": "N/A",
                    "detailed_analysis": cleaned_response
                }
            
            print(f"Final assessment result: {assessment_result}")  # Debug: show final result
            
            return jsonify({
                'success': True,
                'profile_summary': profile_summary,
                'assessment': assessment_result
            })
            
        except Exception as e:
            return jsonify({'error': f'Error calling Claude API: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

async def fetch_single_profile_async(session, url):
    """Fetch a single profile asynchronously"""
    try:
        # Use CoreSignal service to fetch profile
        coresignal_service = CoreSignalService()
        profile_data = coresignal_service.fetch_linkedin_profile(url)
        
        if profile_data and profile_data.get('success', False):
            return {
                'url': url,
                'success': True,
                'profile_data': profile_data,
                'error': None
            }
        else:
            error_msg = profile_data.get('error', 'Profile not found in CoreSignal database') if profile_data else 'No response from CoreSignal'
            return {
                'url': url,
                'success': False,
                'error': error_msg,
                'profile_data': profile_data  # Keep the error response for debugging
            }
    except Exception as e:
        return {
            'url': url,
            'success': False,
            'error': f'Error fetching profile: {str(e)}',
            'profile_data': None
        }

async def fetch_profiles_batch_async(urls):
    """Fetch multiple profiles in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_single_profile_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'success': False,
                    'error': f'Exception occurred: {str(result)}',
                    'profile_data': None
                })
            else:
                processed_results.append(result)
        
        return processed_results


def assess_single_profile_sync(profile_data, user_prompt, weighted_requirements):
    """Assess a single profile synchronously (to be run in thread pool)"""
    try:
        print(f"Starting assessment for profile: {profile_data.get('full_name', 'Unknown')}")
        
        # Generate profile summary
        profile_summary = extract_profile_summary(profile_data)
        
        if 'error' in profile_summary:
            print(f"Error extracting profile summary: {profile_summary['error']}")
            return {
                'success': False,
                'assessment': None,
                'profile_summary': None,
                'error': f"Profile summary error: {profile_summary['error']}"
            }
        
        # Generate assessment prompt
        prompt = generate_assessment_prompt(profile_summary, user_prompt, weighted_requirements)
        
        print(f"Calling Anthropic API for {profile_data.get('full_name', 'Unknown')}...")
        
        # Call Anthropic API with timeout protection
        try:
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Updated to Claude Sonnet 4.5 - best for coding and complex agents
                max_tokens=4000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as api_error:
            print(f"❌ API error for {profile_data.get('full_name', 'Unknown')}: {str(api_error)}")
            return {
                'success': False,
                'assessment': None,
                'profile_summary': None,
                'error': f'API error: {str(api_error)}'
            }
        
        # Parse the response
        response_text = response.content[0].text
        
        # Clean the response by removing markdown code blocks
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # Remove ```json
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # Remove ```
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # Remove trailing ```
        cleaned_response = cleaned_response.strip()
        
        try:
            assessment_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            assessment_data = {
                "overall_score": "N/A",
                "recommend": False,
                "strengths": [],
                "weaknesses": [],
                "career_trajectory": "N/A",
                "detailed_analysis": cleaned_response
            }
        
        print(f"✅ Assessment completed successfully for {profile_data.get('full_name', 'Unknown')}")
        return {
            'success': True,
            'assessment': assessment_data,
            'profile_summary': profile_summary,
            'error': None
        }
    except Exception as e:
        print(f"❌ Assessment failed for {profile_data.get('full_name', 'Unknown')}: {str(e)}")
        return {
            'success': False,
            'assessment': None,
            'profile_summary': None,
            'error': f'Error assessing profile: {str(e)}'
        }

@app.route('/batch-assess-profiles', methods=['POST'])
def batch_assess_profiles():
    """Fetch profiles and assess them with AI in parallel - ENHANCED VERSION"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        candidates = data.get('candidates', [])
        user_prompt = data.get('user_prompt', 'Provide a general professional assessment')
        weighted_requirements = data.get('weighted_requirements', [])
        
        if not candidates:
            return jsonify({'error': 'No candidates provided'}), 400
        
        if not isinstance(candidates, list):
            return jsonify({'error': 'Candidates must be provided as a list'}), 400
        
        # Limit batch size to prevent overwhelming the API
        if len(candidates) > 100:
            return jsonify({'error': 'Batch size cannot exceed 100 candidates for AI assessment'}), 400
        
        print(f"🚀 Processing batch assessment of {len(candidates)} candidates...")
        print("Received candidates:", candidates)
        
        # Extract URLs for profile fetching
        linkedin_urls = [candidate['url'] for candidate in candidates]
        
        # Step 1: Fetch all profiles
        print("Step 1: Fetching profiles...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            profiles_data = loop.run_until_complete(fetch_profiles_batch_async(linkedin_urls))
        finally:
            loop.close()
        
        # Step 2: Process AI assessments with high concurrency
        print("Step 2: Processing AI assessments with high concurrency...")
        print(f"Profiles data before assessment: {[(r.get('url'), r.get('success'), 'has_data' if r.get('profile_data') else 'no_data') for r in profiles_data]}")
        
        # Prepare assessment tasks for high-concurrency processing
        assessment_tasks = []
        profile_mapping = {}  # Map task index to profile_result
        task_index = 0
        
        for i, profile_result in enumerate(profiles_data):
            if profile_result.get('success') and profile_result.get('profile_data'):
                profile_data = profile_result['profile_data']
                
                # Handle nested profile data structure
                if isinstance(profile_data, dict) and 'profile_data' in profile_data:
                    actual_profile_data = profile_data['profile_data']
                else:
                    actual_profile_data = profile_data
                
                print(f"Profile {i}: {actual_profile_data.get('full_name', 'Unknown')} - {profile_result.get('url', 'No URL')}")
                
                # Create assessment task for high-concurrency execution
                def create_assessment_task(profile_data):
                    return lambda: assess_single_profile_sync(profile_data, user_prompt, weighted_requirements)
                
                task = create_assessment_task(actual_profile_data)
                assessment_tasks.append(task)
                profile_mapping[task_index] = profile_result
                task_index += 1
            else:
                print(f"Profile {i}: Skipping failed profile - {profile_result.get('url', 'No URL')}")
                # Add None to maintain index mapping
                assessment_tasks.append(None)
                profile_mapping[task_index] = profile_result
                task_index += 1
        
        print(f"Created {len([t for t in assessment_tasks if t is not None])} assessment tasks for high-concurrency processing")
        
        # Execute assessments with high concurrency using ThreadPoolExecutor
        # Initialize results array with the same length as profiles_data
        results = [None] * len(profiles_data)
        
        if assessment_tasks:
            # Filter out None tasks and keep track of original indices
            real_tasks_with_indices = []
            for i, task in enumerate(assessment_tasks):
                if task is not None:
                    real_tasks_with_indices.append((task, i))
            
            if real_tasks_with_indices:
                print(f"🚀 Starting high-concurrency AI assessments ({len(real_tasks_with_indices)} total)...")
                
                # Use ThreadPoolExecutor with high concurrency
                max_workers = min(len(real_tasks_with_indices), MAX_CONCURRENT_CALLS)
                print(f"🔧 Using {max_workers} parallel workers for {len(real_tasks_with_indices)} AI assessments")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks and keep track of original indices
                    future_to_original_index = {}
                    for task, original_index in real_tasks_with_indices:
                        future = executor.submit(task)
                        future_to_original_index[future] = original_index
                    
                    # Collect results as they complete with progress tracking
                    completed_count = 0
                    total_count = len(future_to_original_index)
                    
                    for future in future_to_original_index:
                        original_index = future_to_original_index[future]
                        try:
                            assessment_result = future.result(timeout=TIMEOUT_SECONDS)
                            profile_result = profile_mapping[original_index]
                            results[original_index] = {
                                'success': assessment_result.get('success', False),
                                'url': profile_result.get('url'),
                                'profile_data': profile_result.get('profile_data'),
                                'profile_summary': assessment_result.get('profile_summary'),
                                'assessment': assessment_result.get('assessment'),
                                'error': assessment_result.get('error')
                            }
                            completed_count += 1
                            print(f"📊 Progress: {completed_count}/{total_count} assessments completed")
                        except Exception as e:
                            print(f"❌ Assessment task failed: {str(e)}")
                            profile_result = profile_mapping[original_index]
                            results[original_index] = {
                                'success': False,
                                'url': profile_result.get('url'),
                                'profile_data': profile_result.get('profile_data'),
                                'profile_summary': None,
                                'assessment': None,
                                'error': str(e)
                            }
                            completed_count += 1
                
                print("✅ All high-concurrency assessments completed!")
        
        # Fill in results for failed profiles (those that weren't processed)
        for i, profile_result in enumerate(profiles_data):
            if results[i] is None:  # This profile wasn't processed (failed to fetch)
                results[i] = {
                    'success': False,
                    'url': profile_result.get('url'),
                    'profile_data': profile_result.get('profile_data'),
                    'profile_summary': None,
                    'assessment': None,
                    'error': profile_result.get('error', 'Profile fetch failed')
                }
        
        # Add CSV names to results to match with candidates
        for i, result in enumerate(results):
            if i < len(candidates):
                result['csv_name'] = candidates[i]['fullName']
                result['csv_first_name'] = candidates[i]['firstName']
                result['csv_last_name'] = candidates[i]['lastName']
                print(f"DEBUG: Result {i} mapped to candidate: {candidates[i]['fullName']} - URL: {result.get('url', 'No URL')}")
        
        # Debug: Print results before sorting
        print("DEBUG: Results before sorting:")
        for i, result in enumerate(results):
            print(f"  {i}: {result.get('csv_name', 'No name')} - Success: {result.get('success', False)} - URL: {result.get('url', 'No URL')}")
        
        # Sort results by weighted score (descending)
        def get_weighted_score(result):
            if result.get('assessment') and result['assessment'].get('weighted_analysis'):
                score = result['assessment']['weighted_analysis'].get('weighted_score', 0)
                # Handle string scores like 'N/A' by converting to 0
                if isinstance(score, str):
                    return 0
                return score
            return 0
        
        results.sort(key=get_weighted_score, reverse=True)
        
        # Debug: Print results after sorting
        print("DEBUG: Results after sorting:")
        for i, result in enumerate(results):
            print(f"  {i}: {result.get('csv_name', 'No name')} - Success: {result.get('success', False)} - URL: {result.get('url', 'No URL')}")
        
        # Count successful and failed results
        successful = sum(1 for r in results if r.get('success', False) and r.get('assessment') and not r.get('error'))
        failed = len(results) - successful
        
        print(f"✅ Batch assessment complete: {successful} successful, {failed} failed")
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            }
        })
        
    except Exception as e:
        print(f"❌ Batch assessment error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/save-assessment', methods=['POST'])
def save_assessment():
    """Save a candidate assessment to the database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        linkedin_url = data.get('linkedin_url')
        full_name = data.get('full_name')
        headline = data.get('headline')
        profile_data = data.get('profile_data')
        assessment_data = data.get('assessment_data')
        assessment_type = data.get('assessment_type', 'single')
        session_name = data.get('session_name')
        
        if not linkedin_url or not full_name or not assessment_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = save_candidate_assessment(
            linkedin_url=linkedin_url,
            full_name=full_name,
            headline=headline,
            profile_data=profile_data,
            assessment_data=assessment_data,
            assessment_type=assessment_type,
            session_name=session_name
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Assessment saved successfully'})
        else:
            return jsonify({'error': 'Failed to save assessment'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/load-assessments', methods=['GET'])
def load_assessments():
    """Load candidate assessments from the database"""
    try:
        limit = request.args.get('limit', 50, type=int)
        assessments = load_candidate_assessments(limit=limit)
        
        return jsonify({
            'success': True,
            'assessments': assessments,
            'count': len(assessments)
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/search-profiles', methods=['POST'])
def search_profiles_endpoint():
    """Search for profiles based on natural language prompt and return CSV"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_prompt = data.get('user_prompt', '')
        limit = data.get('limit', 20)
        
        if not user_prompt:
            return jsonify({'error': 'User prompt is required'}), 400
        
        # Validate limit
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 1
        
        print(f"🔍 Processing search request: {user_prompt[:100]}...")
        
        # Step 1: Process user prompt with Anthropic
        print("🤖 Extracting search criteria with AI...")
        criteria = process_user_prompt_for_search(user_prompt)
        
        if not criteria:
            return jsonify({'error': 'Failed to extract search criteria from prompt'}), 400
        
        print(f"✅ Extracted criteria: {criteria.get('explanation', 'No explanation')}")
        print(f"🔍 DEBUG: Full extracted criteria:")
        print(json.dumps(criteria, indent=2))
        
        # Step 2: Search CoreSignal API using /preview endpoint
        # Limitation: /preview only supports pages 1-5, so max 100 profiles per search
        profiles_per_page = 20
        max_profiles_per_search = 100  # 5 pages × 20 profiles
        
        if limit > max_profiles_per_search:
            print(f"⚠️  Limiting request to {max_profiles_per_search} profiles (API limitation: /preview only supports pages 1-5)")
            limit = max_profiles_per_search
        
        num_pages_needed = min((limit + profiles_per_page - 1) // profiles_per_page, 5)
        
        print(f"🌐 Searching CoreSignal database for {limit} profiles...")
        print(f"   Will fetch {num_pages_needed} page(s) of ~{profiles_per_page} profiles each")
        
        # Track which pages to fetch - avoid already-used pages
        available_pages = [p for p in range(1, 6) if p not in used_pages_tracker]
        
        # If we don't have enough unused pages, reset the tracker
        if len(available_pages) < num_pages_needed:
            print(f"ℹ️  Only {len(available_pages)} unused pages available, resetting tracker...")
            used_pages_tracker.clear()
            available_pages = list(range(1, 6))
        
        # Randomly select pages from available ones
        pages_to_fetch = random.sample(available_pages, min(num_pages_needed, len(available_pages)))
        
        # Mark these pages as used
        for page in pages_to_fetch:
            used_pages_tracker.add(page)
        
        print(f"🎲 Selected random pages: {pages_to_fetch} (session tracker has {len(used_pages_tracker)} used pages)")
        
        all_results = []
        
        # Fetch each page
        for i, page_num in enumerate(pages_to_fetch):
            print(f"📡 API call {i+1}/{num_pages_needed} (page {page_num})...")
            
            # Fetch profiles from this page
            page_result = search_coresignal_profiles_preview(criteria, page_num)
            
            if not page_result.get('success'):
                print(f"⚠️  Page {page_num} failed: {page_result.get('error')}")
                continue
            
            page_profiles = page_result.get('results', [])
            all_results.extend(page_profiles)
            
            print(f"   Total so far: {len(all_results)} profiles")
            
            # Small delay between calls
            if i < num_pages_needed - 1:
                time.sleep(1)
        
        # Limit to requested amount
        results = all_results[:limit]
        
        print(f"🎉 Successfully retrieved {len(results)} profiles from pages: {pages_to_fetch}")
        print(f"📊 Pages used in this session so far: {sorted(used_pages_tracker)}")
        
        # Step 3: Convert to CSV
        print("📄 Converting results to CSV...")
        csv_data = convert_search_results_to_csv(results)
        
        return jsonify({
            'success': True,
            'csv_data': csv_data,
            'total_found': len(results),
            'criteria': criteria
        })
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/save-feedback', methods=['POST'])
def save_feedback():
    """
    Save recruiter feedback (like/dislike/note) for a candidate
    Supports auto-save with debouncing on frontend
    """
    try:
        data = request.get_json()

        linkedin_url = data.get('linkedin_url')
        feedback_type = data.get('feedback_type')  # 'like', 'dislike', 'note'
        feedback_text = data.get('feedback_text', '')  # Optional for like/dislike
        recruiter_name = data.get('recruiter_name', 'Unknown')
        source_tab = data.get('source_tab', 'single')  # Track which tab feedback came from

        if not linkedin_url or not feedback_type:
            return jsonify({'error': 'linkedin_url and feedback_type are required'}), 400

        if feedback_type not in ['like', 'dislike', 'note']:
            return jsonify({'error': 'feedback_type must be like, dislike, or note'}), 400

        if source_tab not in ['single', 'batch', 'search', 'company_research']:
            source_tab = 'single'  # Default to single if invalid

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }

        payload = {
            'candidate_linkedin_url': linkedin_url,
            'feedback_type': feedback_type,
            'feedback_text': feedback_text,
            'recruiter_name': recruiter_name,
            'source_tab': source_tab
        }

        url = f"{SUPABASE_URL}/rest/v1/recruiter_feedback"
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            print(f"✅ Saved {feedback_type} feedback from {recruiter_name} for {linkedin_url}")
            return jsonify({
                'success': True,
                'message': 'Feedback saved successfully',
                'feedback': response.json()[0] if response.json() else payload
            })
        else:
            print(f"❌ Failed to save feedback: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to save feedback', 'details': response.text}), response.status_code

    except Exception as e:
        print(f"❌ Error saving feedback: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get-feedback/<path:linkedin_url>', methods=['GET'])
def get_feedback(linkedin_url):
    """
    Get all feedback for a specific candidate
    Returns array of feedback sorted by created_at DESC
    Optionally filters by source_tab query parameter
    """
    try:
        import urllib.parse
        encoded_url = urllib.parse.quote(linkedin_url, safe='')

        # Get source_tab filter from query parameters (optional)
        source_tab = request.args.get('source_tab', 'single')
        if source_tab not in ['single', 'batch', 'search', 'company_research']:
            source_tab = 'single'  # Default to single if invalid

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # Get feedback for this candidate filtered by source_tab, sorted by newest first
        url = f"{SUPABASE_URL}/rest/v1/recruiter_feedback?candidate_linkedin_url=eq.{encoded_url}&source_tab=eq.{source_tab}&order=created_at.desc"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            feedback_list = response.json()
            print(f"✅ Retrieved {len(feedback_list)} feedback items for {linkedin_url}")
            return jsonify({
                'success': True,
                'feedback': feedback_list
            })
        else:
            print(f"❌ Failed to get feedback: {response.status_code}")
            return jsonify({'error': 'Failed to retrieve feedback'}), response.status_code

    except Exception as e:
        print(f"❌ Error getting feedback: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/clear-feedback', methods=['POST'])
def clear_feedback():
    """
    Clear all feedback for a specific candidate from the current recruiter
    Note: This deletes ALL feedback from ALL recruiters for this candidate
    """
    try:
        data = request.get_json()
        linkedin_url = data.get('linkedin_url')
        recruiter_name = data.get('recruiter_name', 'Unknown')

        if not linkedin_url:
            return jsonify({'error': 'linkedin_url is required'}), 400

        import urllib.parse
        encoded_url = urllib.parse.quote(linkedin_url, safe='')

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # Delete all feedback for this candidate from this recruiter
        url = f"{SUPABASE_URL}/rest/v1/recruiter_feedback?candidate_linkedin_url=eq.{encoded_url}&recruiter_name=eq.{urllib.parse.quote(recruiter_name, safe='')}"
        response = requests.delete(url, headers=headers)

        if response.status_code in [200, 204]:
            print(f"✅ Cleared all feedback from {recruiter_name} for {linkedin_url}")
            return jsonify({
                'success': True,
                'message': 'All feedback cleared successfully'
            })
        else:
            print(f"❌ Failed to clear feedback: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to clear feedback', 'details': response.text}), response.status_code

    except Exception as e:
        print(f"❌ Error clearing feedback: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/regenerate-crunchbase-url', methods=['POST'])
def regenerate_crunchbase_url():
    """
    Manually regenerate Crunchbase URL using Claude Agent SDK WebSearch

    This endpoint uses Claude with WebSearch to validate/correct Crunchbase URLs
    for companies where Tavily returned low-confidence results.

    Expected request body:
    {
        "company_name": "FOX Tech",
        "company_id": 25523180,
        "current_url": "https://www.crunchbase.com/organization/fox-tech"
    }

    Returns:
    {
        "success": true,
        "crunchbase_url": "https://www.crunchbase.com/organization/fox-tech-co",
        "crunchbase_source": "websearch_validated",
        "crunchbase_confidence": 0.95
    }
    """
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        company_id = data.get('company_id')
        current_url = data.get('current_url')
        return_candidates = data.get('return_candidates', False)

        if not company_name:
            return jsonify({'error': 'company_name is required'}), 400

        print(f"\n🔄 Regenerating Crunchbase URL for: {company_name}")
        print(f"   Current URL: {current_url}")
        print(f"   Company ID: {company_id}")

        # Initialize CoreSignal service
        service = CoreSignalService()

        # Fetch company data if company_id provided (for rich context)
        company_data = {}
        if company_id:
            print(f"   📊 Fetching company data for context...")
            company_endpoint = f"https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}"
            response = requests.get(company_endpoint, headers=service.headers, timeout=30)

            if response.status_code == 200:
                company_data = response.json()
                print(f"   ✅ Got company data ({len(company_data)} fields)")
            else:
                print(f"   ⚠️  Could not fetch company data (status {response.status_code})")

        # Step 1: Get Tavily candidates
        print(f"   🔍 Stage 1: Getting Tavily candidates...")
        try:
            from tavily import TavilyClient
            import re

            tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
            response = tavily_client.search(
                query=f"{company_name} crunchbase",
                search_depth="basic",
                max_results=10,
                include_domains=["crunchbase.com"]
            )

            # Extract candidates with scores
            crunchbase_pattern = r'crunchbase\.com/organization/([a-z0-9-]+)'
            candidates = []
            seen = set()

            for result in response.get('results', []):
                match = re.search(crunchbase_pattern, result.get('url', ''), re.IGNORECASE)
                if match:
                    slug = match.group(1)
                    if slug not in seen:
                        candidates.append({
                            'slug': slug,
                            'score': result.get('score', 0.0),
                            'title': result.get('title', ''),
                            'url': result.get('url', '')
                        })
                        seen.add(slug)

            candidates.sort(key=lambda x: x['score'], reverse=True)
            print(f"   📋 Found {len(candidates)} Tavily candidates")

            # Don't fail if no candidates - Claude WebSearch can work standalone
            if not candidates:
                print(f"   ⚠️  No Tavily candidates, will use Claude WebSearch alone")

        except Exception as e:
            print(f"   ⚠️  Tavily search error: {e}, falling back to Claude WebSearch alone")
            candidates = []

        # Step 2: Use Claude WebSearch (validation mode if candidates exist, search mode if not)
        print(f"   🤖 Stage 2: Claude WebSearch {'validation' if candidates else 'search'}...")
        result = service._validate_with_claude_websearch(company_name, candidates, company_data)

        if result and result.get('url'):
            new_url = result['url']
            new_source = result['source']
            new_confidence = result['confidence']
            print(f"   ✅ Regenerated URL: {new_url}")
        elif candidates:
            # Fallback to top Tavily candidate if Claude failed but we have candidates
            print(f"   ⚠️  Claude validation failed, returning top Tavily candidate")
            top = candidates[0]
            new_url = f"https://www.crunchbase.com/organization/{top['slug']}"
            new_source = 'tavily_fallback'
            new_confidence = top['score']
        else:
            # Both Tavily and Claude failed
            print(f"   ❌ Both Tavily and Claude failed to find Crunchbase URL")
            return jsonify({'error': 'Could not find Crunchbase URL for this company'}), 404

        # Step 2.5: If return_candidates=true, return array for user selection
        if return_candidates:
            # Mark which candidate was validated by Claude (if any)
            for candidate in candidates:
                if result and result.get('url'):
                    candidate['validated'] = (result['url'] == f"https://www.crunchbase.com/organization/{candidate['slug']}")
                else:
                    candidate['validated'] = False

            # Build full URLs for all candidates
            for candidate in candidates:
                if not candidate.get('url'):
                    candidate['url'] = f"https://www.crunchbase.com/organization/{candidate['slug']}"

            print(f"   📋 Returning {len(candidates)} candidates for user selection")
            return jsonify({
                'success': True,
                'candidates': candidates[:4],  # Top 4 candidates
                'claude_pick': result.get('url') if result else None
            })

        # Step 3: Update stored company data in Supabase (if company_id provided)
        if company_id:
            print(f"   💾 Updating stored company data in Supabase...")
            try:
                # Fetch current stored company data
                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }

                # Get current company data
                get_url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}"
                response = requests.get(get_url, headers=headers)

                if response.status_code == 200 and response.json():
                    stored_data = response.json()[0]
                    company_data_json = stored_data.get('company_data', {})

                    # Update Crunchbase URL in the intelligence section
                    if 'intelligence' not in company_data_json:
                        company_data_json['intelligence'] = {}

                    intelligence = company_data_json['intelligence']
                    intelligence['crunchbase_company_url'] = new_url
                    intelligence['crunchbase_source'] = new_source
                    intelligence['crunchbase_confidence'] = new_confidence

                    # Update in database
                    patch_url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}"
                    update_response = requests.patch(
                        patch_url,
                        headers=headers,
                        json={'company_data': company_data_json}
                    )

                    if update_response.status_code in [200, 204]:
                        print(f"   ✅ Updated stored company data for company_id {company_id}")
                    else:
                        print(f"   ⚠️  Failed to update company data: {update_response.status_code}")
                else:
                    print(f"   ⚠️  No stored company data found for company_id {company_id}")

            except Exception as e:
                print(f"   ⚠️  Error updating stored data: {e}")
                # Continue anyway - don't fail the whole request

        # Return result
        return jsonify({
            'success': True,
            'crunchbase_url': new_url,
            'crunchbase_source': new_source,
            'crunchbase_confidence': new_confidence,
            'warning': 'Claude validation failed, using top Tavily result' if not result else None
        })

    except Exception as e:
        import traceback
        print(f"❌ Error regenerating URL: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/verify-crunchbase-url', methods=['POST'])
def verify_crunchbase_url():
    """
    Endpoint to handle user verification of Crunchbase URLs.

    Payload:
    {
        "company_id": 12345,
        "is_correct": true/false/null,
        "verification_status": "verified"/"needs_review"/"skipped",
        "corrected_url": "https://..." (optional)
    }
    """
    try:
        data = request.json
        print(f"📥 Received verification request: {data}")

        # Accept both camelCase (companyId) and snake_case (company_id)
        company_id = data.get('companyId') or data.get('company_id')
        is_correct = data.get('isCorrect') if 'isCorrect' in data else data.get('is_correct')
        verification_status = data.get('verificationStatus') or data.get('verification_status', 'pending')
        corrected_url = data.get('correctedUrl') or data.get('corrected_url')

        if not company_id:
            print(f"❌ Missing company_id. Received data: {data}")
            return jsonify({'error': 'company_id is required', 'received': data}), 400

        # Prepare update data
        update_data = {
            'user_verified': is_correct if is_correct is not None else False,
            'verification_status': verification_status,
            'verified_by': 'user',  # Could be parameterized later
            'verified_at': datetime.utcnow().isoformat()
        }

        # CRITICAL: Fetch current company_data to save the verified URL
        # The URL comes from the frontend (which computed it during enrichment)
        verified_url = data.get('crunchbaseUrl') or data.get('crunchbase_url')

        # Fetch current data to get company_data
        get_url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}&select=company_data"
        get_response = requests.get(
            get_url,
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }
        )

        if get_response.status_code == 200 and get_response.json():
            stored_data = get_response.json()[0]
            company_data = stored_data.get('company_data', {})

            # If user clicked "Yes, Correct", save the verified URL to company_data
            if is_correct and verified_url:
                company_data['crunchbase_company_url'] = verified_url
                company_data['crunchbase_source'] = 'user_verified'
                update_data['company_data'] = company_data
                print(f"   💾 Saving user-verified URL to company_data: {verified_url}")

        # If user provided a corrected URL, override with that
        if corrected_url and get_response.status_code == 200 and get_response.json():
            stored_data = get_response.json()[0]
            company_data = stored_data.get('company_data', {})

            # Store original URL before updating
            update_data['original_url'] = company_data.get('crunchbase_company_url')

            # Update company_data with corrected URL
            company_data['crunchbase_company_url'] = corrected_url
            company_data['crunchbase_source'] = 'user_corrected'
            update_data['company_data'] = company_data
            print(f"   💾 Saving user-corrected URL to company_data: {corrected_url}")

        # Update Supabase
        update_url = f"{SUPABASE_URL}/rest/v1/stored_companies?company_id=eq.{company_id}"
        update_response = requests.patch(
            update_url,
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            json=update_data
        )

        if update_response.status_code in [200, 204]:
            print(f"✅ Verified company_id {company_id}: {verification_status}")
            return jsonify({
                'success': True,
                'message': 'Verification saved successfully',
                'company_id': company_id,
                'verification_status': verification_status
            })
        else:
            print(f"⚠️  Failed to update verification: {update_response.status_code}")
            return jsonify({
                'error': 'Failed to save verification',
                'status_code': update_response.status_code
            }), 500

    except Exception as e:
        import traceback
        print(f"❌ Error saving verification: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== CHROME EXTENSION API ENDPOINTS ====================

@app.route('/extension/lists', methods=['GET'])
def get_extension_lists():
    """Get all lists for a recruiter"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    recruiter_name = request.args.get('recruiter_name', 'Unknown')

    lists = extension_service.get_lists(recruiter_name)
    return jsonify(lists)

@app.route('/extension/create-list', methods=['POST'])
def create_extension_list():
    """Create a new list"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    data = request.json
    recruiter_name = data.get('recruiter_name')
    list_name = data.get('list_name')
    job_template_id = data.get('job_template_id')
    description = data.get('description')

    if not recruiter_name or not list_name:
        return jsonify({'error': 'recruiter_name and list_name are required'}), 400

    result = extension_service.create_list(recruiter_name, list_name, job_template_id, description)

    if result:
        return jsonify(result), 201
    else:
        return jsonify({'error': 'Failed to create list'}), 500

@app.route('/extension/lists/<list_id>', methods=['PUT'])
def update_extension_list(list_id):
    """Update a list"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    data = request.json
    success = extension_service.update_list(list_id, data)

    if success:
        return jsonify({'message': 'List updated successfully'})
    else:
        return jsonify({'error': 'Failed to update list'}), 500

@app.route('/extension/lists/<list_id>', methods=['DELETE'])
def delete_extension_list(list_id):
    """Delete (archive) a list"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    success = extension_service.delete_list(list_id)

    if success:
        return jsonify({'message': 'List deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete list'}), 500

@app.route('/extension/lists/<list_id>/stats', methods=['GET'])
def get_list_stats(list_id):
    """Get statistics for a list"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    stats = extension_service.get_list_stats(list_id)

    if stats:
        return jsonify(stats)
    else:
        return jsonify({'error': 'List not found'}), 404

@app.route('/extension/add-profile', methods=['POST'])
def add_profile_to_list():
    """Add a profile to a list (quick bookmark from extension)"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    data = request.json

    # Validate required fields
    if not data.get('linkedin_url'):
        return jsonify({'error': 'linkedin_url is required'}), 400

    if not data.get('list_id'):
        return jsonify({'error': 'list_id is required'}), 400

    result = extension_service.add_profile(data)

    if result:
        return jsonify({
            'message': 'Profile added successfully',
            'profile': result
        }), 201
    else:
        return jsonify({'error': 'Failed to add profile'}), 500

@app.route('/extension/profiles/<list_id>', methods=['GET'])
def get_profiles_in_list(list_id):
    """Get all profiles in a list"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    # Get filter parameters
    filters = {}

    if request.args.get('assessed'):
        filters['assessed'] = request.args.get('assessed').lower() == 'true'

    if request.args.get('min_score'):
        try:
            filters['min_score'] = float(request.args.get('min_score'))
        except ValueError:
            pass

    if request.args.get('status'):
        filters['status'] = request.args.get('status')

    profiles = extension_service.get_profiles_in_list(list_id, filters if filters else None)
    return jsonify(profiles)

@app.route('/extension/profiles/<profile_id>/status', methods=['PUT'])
def update_profile_status(profile_id):
    """Update profile status"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    data = request.json
    status = data.get('status')

    if not status:
        return jsonify({'error': 'status is required'}), 400

    success = extension_service.update_profile_status(profile_id, status)

    if success:
        return jsonify({'message': 'Profile status updated'})
    else:
        return jsonify({'error': 'Failed to update profile status'}), 500

@app.route('/extension/auth', methods=['GET'])
def extension_auth():
    """Simple authentication check for extension"""
    # For now, just check if recruiter_name is provided
    # In production, implement proper authentication
    recruiter_name = request.args.get('recruiter_name')

    if recruiter_name:
        return jsonify({
            'authenticated': True,
            'recruiter_name': recruiter_name
        })
    else:
        return jsonify({
            'authenticated': False,
            'error': 'recruiter_name required'
        }), 401

# ==================== LIST ASSESSMENT & EXPORT ENDPOINTS ====================

@app.route('/lists/<list_id>/assess', methods=['POST'])
def assess_list(list_id):
    """Assess all unassessed profiles in a list using the existing batch assessment engine"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    try:
        data = request.get_json() or {}
        template_id = data.get('template_id')
        enrich_with_company = data.get('enrich_with_company', True)
        force_refresh = data.get('force_refresh', False)

        print(f"🎯 Starting list assessment for list {list_id}")

        # Step 1: Get all unassessed profiles from the list
        profiles = extension_service.get_profiles_in_list(list_id, {'assessed': False})

        if not profiles:
            return jsonify({
                'message': 'No unassessed profiles in list',
                'total': 0,
                'assessed': 0
            })

        print(f"Found {len(profiles)} unassessed profiles")

        # Step 2: Format as candidates array for batch assessment
        candidates = []
        for profile in profiles:
            candidates.append({
                'url': profile['linkedin_url'],
                'name': profile.get('name', '')
            })

        # Step 3: Get weighted requirements (from template if provided)
        weighted_requirements = []
        if template_id:
            # TODO: Fetch template requirements
            # For now, use default requirements
            weighted_requirements = [
                {"requirement": "Relevant technical skills and experience", "weight": 40},
                {"requirement": "Leadership and team collaboration", "weight": 30},
                {"requirement": "Industry knowledge and domain expertise", "weight": 30}
            ]
        else:
            weighted_requirements = [
                {"requirement": "Overall professional fit and experience", "weight": 100}
            ]

        # Step 4: Call the existing batch assessment endpoint internally
        print(f"🚀 Calling batch assessment for {len(candidates)} candidates...")

        # Create internal request data
        batch_data = {
            'candidates': candidates,
            'user_prompt': 'Provide a comprehensive professional assessment',
            'weighted_requirements': weighted_requirements
        }

        # Call batch_assess_profiles function directly
        with app.test_request_context(
            '/batch-assess-profiles',
            method='POST',
            json=batch_data
        ):
            batch_response = batch_assess_profiles()

            if isinstance(batch_response, tuple):
                batch_result = batch_response[0].get_json()
            else:
                batch_result = batch_response.get_json()

        print(f"✅ Batch assessment complete")

        # Step 5: Link assessment results back to extension_profiles
        assessment_results = batch_result.get('results', [])
        linked_count = 0
        scores = []

        for result in assessment_results:
            if result.get('success'):
                linkedin_url = result.get('linkedin_url')
                assessment_data = result.get('assessment')

                # Extract score
                score = None
                if assessment_data and assessment_data.get('weighted_analysis'):
                    score = assessment_data['weighted_analysis'].get('weighted_score')
                elif assessment_data:
                    score = assessment_data.get('overall_score')

                if score:
                    scores.append(score)

                # Find the corresponding profile
                matching_profile = next((p for p in profiles if p['linkedin_url'] == linkedin_url), None)

                if matching_profile:
                    # Find the assessment ID from candidate_assessments table
                    # Query Supabase for the assessment
                    assessment_query_url = f"{SUPABASE_URL}/rest/v1/candidate_assessments"
                    assessment_params = {
                        'linkedin_url': f'eq.{linkedin_url}',
                        'order': 'created_at.desc',
                        'limit': '1'
                    }

                    headers = {
                        'apikey': SUPABASE_KEY,
                        'Authorization': f'Bearer {SUPABASE_KEY}'
                    }

                    assessment_response = requests.get(
                        assessment_query_url,
                        headers=headers,
                        params=assessment_params
                    )

                    if assessment_response.ok:
                        assessments = assessment_response.json()
                        if assessments:
                            assessment_id = assessments[0].get('id')

                            # Link to extension_profiles
                            success = extension_service.link_assessment(
                                matching_profile['id'],
                                assessment_id,
                                score
                            )

                            if success:
                                linked_count += 1

        avg_score = sum(scores) / len(scores) if scores else None

        return jsonify({
            'message': 'List assessment complete',
            'total': len(profiles),
            'assessed': linked_count,
            'failed': len(profiles) - linked_count,
            'avg_score': round(avg_score, 1) if avg_score else None,
            'results': assessment_results
        })

    except Exception as e:
        print(f"❌ Error assessing list: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to assess list: {str(e)}'}), 500

@app.route('/lists/<list_id>/export-csv', methods=['GET'])
def export_list_to_csv(list_id):
    """Export assessed profiles as CSV for LinkedIn Recruiter import"""
    if not extension_service:
        return jsonify({'error': 'Extension service not available'}), 503

    try:
        # Get query parameters
        min_score = request.args.get('min_score', type=float)
        include_notes = request.args.get('include_notes', 'true').lower() == 'true'

        print(f"📤 Exporting list {list_id} to CSV (min_score: {min_score})")

        # Get assessed profiles
        filters = {'assessed': True}
        if min_score:
            filters['min_score'] = min_score

        profiles = extension_service.get_profiles_in_list(list_id, filters)

        if not profiles:
            return jsonify({'error': 'No assessed profiles to export'}), 404

        # Get list info
        stats = extension_service.get_list_stats(list_id)
        list_name = stats.get('list_name', 'candidates') if stats else 'candidates'

        # Generate CSV
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)

        # Header row
        csv_writer.writerow(['first_name', 'last_name', 'email', 'note', 'tags'])

        # Get full assessment data for each profile
        profile_ids = []
        for profile in profiles:
            # Parse name
            name = profile.get('name', '')
            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Email (leave blank - not available from public profiles)
            email = ''

            # Build note with assessment data
            note = ''
            if include_notes and profile.get('assessment_id'):
                # Fetch full assessment
                assessment_url = f"{SUPABASE_URL}/rest/v1/candidate_assessments"
                assessment_params = {'id': f'eq.{profile["assessment_id"]}'}

                headers = {
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}'
                }

                assessment_response = requests.get(
                    assessment_url,
                    headers=headers,
                    params=assessment_params
                )

                if assessment_response.ok:
                    assessments = assessment_response.json()
                    if assessments:
                        assessment = assessments[0].get('assessment_data', {})
                        score = profile.get('assessment_score', 0)

                        # Extract strengths
                        strengths = []
                        if assessment.get('weighted_analysis'):
                            for req in assessment['weighted_analysis'].get('requirements_analysis', []):
                                strengths.append(req.get('analysis', ''))
                        elif assessment.get('strengths'):
                            strengths = assessment['strengths']

                        # Build note
                        note_parts = [
                            f"AI Score: {score}/100"
                        ]

                        if strengths:
                            note_parts.append(f"Strengths: {', '.join(strengths[:3])}")

                        note_parts.append(f"LinkedIn: {profile['linkedin_url']}")
                        note_parts.append(f"Assessed: {datetime.now().strftime('%Y-%m-%d')}")

                        note = '. '.join(note_parts)

            # Tags
            tags = f"{list_name.replace(' ', '-')},{datetime.now().strftime('%Y-Q%q')}"

            # Write row
            csv_writer.writerow([first_name, last_name, email, note, tags])

            profile_ids.append(profile['id'])

        # Mark profiles as exported
        if profile_ids:
            extension_service.mark_exported(profile_ids)

        # Record export
        export_record = {
            'list_id': list_id,
            'exported_by': request.args.get('recruiter_name', 'Unknown'),
            'candidate_count': len(profiles),
            'min_score_filter': min_score,
            'csv_filename': f"{list_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
        extension_service.record_export(export_record)

        # Prepare response
        csv_content = csv_output.getvalue()
        csv_output.close()

        # Create response with CSV download
        response = app.response_class(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={export_record["csv_filename"]}'
            }
        )

        print(f"✅ Exported {len(profiles)} profiles to CSV")

        return response

    except Exception as e:
        print(f"❌ Error exporting to CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to export CSV: {str(e)}'}), 500

# ========================================
# Company Research Endpoints
# ========================================

# Initialize company research service (lazy loading)
company_research_service = None

def get_company_research_service():
    """Lazy load company research service"""
    global company_research_service
    if company_research_service is None:
        try:
            from company_research_service import CompanyResearchService
            company_research_service = CompanyResearchService()
            print("✓ Company Research Service initialized")
        except Exception as e:
            print(f"Warning: Could not initialize Company Research Service: {e}")
    return company_research_service

def generate_jd_cache_key(jd_text):
    """
    Generate a deterministic cache key from JD text.
    Same JD text always produces the same key.
    """
    # Normalize text: lowercase, strip whitespace
    normalized = jd_text.strip().lower()
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))
    # Return first 16 chars of hex digest (sufficient for uniqueness)
    return f"jd_{hash_obj.hexdigest()[:16]}"

@app.route('/research-companies', methods=['POST'])
def research_companies_endpoint():
    """
    Start company research for a job description.

    Request Body:
    {
        "jd_id": "unique_id",  # Optional, will generate if not provided
        "jd_data": {
            "title": "Senior ML Engineer",
            "company": "TechCorp",
            "company_stage": "series_b",
            "requirements": {...},
            "target_companies": {
                "mentioned_companies": ["Stripe", "Square"],
                "industry_context": "fintech"
            }
        },
        "config": {
            "max_companies": 50,
            "min_relevance_score": 5.0,
            "include_competitors": true,
            "use_gpt5_deep_research": true
        }
    }
    """
    try:
        service = get_company_research_service()
        if not service:
            return jsonify({'error': 'Company research service not available'}), 503

        data = request.get_json()

        jd_data = data.get('jd_data')
        config = data.get('config', {})
        jd_text = data.get('jd_text', '')  # Original JD text for cache key
        force_refresh = data.get('force_refresh', False)  # Bypass cache if True

        if not jd_data:
            return jsonify({'error': 'jd_data is required'}), 400

        # Generate JD ID from cache key (if jd_text provided) or use provided ID or UUID
        if jd_text and not data.get('jd_id'):
            jd_id = generate_jd_cache_key(jd_text)
        else:
            import uuid
            jd_id = data.get('jd_id', str(uuid.uuid4()))

        # ============= DEBUG LOGGING =============
        print(f"\n{'='*100}")
        print(f"[RESEARCH REQUEST] Received research request")
        print(f"[RESEARCH REQUEST] JD ID: {jd_id}")
        print(f"[RESEARCH REQUEST] JD Data:")
        print(f"  - title: {jd_data.get('title')}")
        print(f"  - company_stage: {jd_data.get('company_stage')}")
        print(f"  - industries: {jd_data.get('industries')}")
        print(f"  - requirements.domain: {jd_data.get('requirements', {}).get('domain')}")
        print(f"  - requirements.technical_skills: {jd_data.get('requirements', {}).get('technical_skills')}")
        print(f"  - target_companies.mentioned_companies: {jd_data.get('target_companies', {}).get('mentioned_companies')}")
        print(f"  - target_companies.industry_context: {jd_data.get('target_companies', {}).get('industry_context')}")
        print(f"[RESEARCH REQUEST] Config: {config}")
        print(f"{'='*100}\n")
        # =========================================

        # Check for existing session (cache)
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        existing = supabase.table("company_research_sessions").select("*").eq(
            "jd_id", jd_id
        ).execute()

        # Cache hit: Return cached results if available and not expired (unless force_refresh)
        if existing.data and not force_refresh:
            session = existing.data[0]

            # If research is currently running, reject
            if session.get('status') == 'running':
                return jsonify({
                    'success': False,
                    'error': 'Research already in progress for this JD'
                }), 409

            # If research is completed, check cache expiration (48 hours)
            if session.get('status') == 'completed':
                created_at = safe_parse_timestamp(session.get('created_at'))
                cache_age = datetime.now(created_at.tzinfo) - created_at
                # Temporarily reduced from 48 to 1 hour to invalidate old GPT-5 cached results
                cache_ttl = timedelta(hours=1)  # TODO: Increase back to 48 after migration

                if cache_age < cache_ttl:
                    # Cache hit! Return cached results
                    hours_ago = cache_age.total_seconds() / 3600
                    print(f"✅ CACHE HIT: Returning cached research from {hours_ago:.1f} hours ago")

                    return jsonify({
                        'success': True,
                        'session_id': jd_id,
                        'status': 'completed',
                        'from_cache': True,
                        'cache_age_hours': hours_ago,
                        'message': f'Using cached research from {hours_ago:.1f} hours ago'
                    })
                else:
                    print(f"⏰ Cache expired ({cache_age.total_seconds()/3600:.1f} hours old), running fresh research")

        if force_refresh:
            print("🔄 Force refresh requested, bypassing cache")

        # Start async research in background
        async def run_research():
            await service.research_companies_for_jd(jd_id, jd_data, config)

        # Create new event loop for this task
        import threading
        def background_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_research())
            loop.close()

        thread = threading.Thread(target=background_task)
        thread.start()

        return jsonify({
            'success': True,
            'session_id': jd_id,
            'status': 'running',
            'message': 'Company research started in background'
        })

    except Exception as e:
        print(f"Research error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/evaluate-more-companies', methods=['POST'])
def evaluate_more_companies_endpoint():
    """
    Evaluate additional companies from the discovered list.

    Request Body:
    {
        "session_id": "jd_123",
        "start_index": 25,  # Start from company 25
        "count": 25         # Evaluate next 25
    }
    """
    try:
        service = get_company_research_service()
        if not service:
            return jsonify({'error': 'Company research service not available'}), 503

        data = request.get_json()
        session_id = data.get('session_id')
        start_index = data.get('start_index', 25)
        count = data.get('count', 25)

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400

        # Run evaluation in background
        async def run_evaluation():
            return await service.evaluate_additional_companies(session_id, start_index, count)

        # Create new event loop for this task
        import threading
        result_container = {}

        def background_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_evaluation())
            result_container['result'] = result
            loop.close()

        thread = threading.Thread(target=background_task)
        thread.start()
        thread.join()  # Wait for completion (evaluations are faster than discovery)

        return jsonify(result_container.get('result', {'error': 'Evaluation failed'}))

    except Exception as e:
        print(f"Evaluate more error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/research-companies/<jd_id>/status', methods=['GET'])
def get_research_status(jd_id):
    """Get research session status and progress."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        result = supabase.table("company_research_sessions").select("*").eq(
            "jd_id", jd_id
        ).execute()

        if not result.data:
            return jsonify({'error': 'Session not found'}), 404

        session = result.data[0]

        # Calculate progress percentage
        if session['status'] == 'completed':
            progress = 100
        elif session['status'] == 'failed':
            progress = 0
        else:
            # Estimate based on companies evaluated
            total_expected = session.get('max_companies', 50)
            evaluated = session.get('total_evaluated', 0)
            progress = min(int((evaluated / total_expected) * 100), 99)

        session['progress_percentage'] = progress

        return jsonify({
            'success': True,
            'session': session
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/research-companies/<jd_id>/stream', methods=['GET'])
def stream_research_status(jd_id):
    """
    Stream research session status in real-time using Server-Sent Events (SSE).

    This provides much better UX than polling:
    - Updates every 500ms (vs 2 seconds)
    - Shows detailed progress (phase, current action, company being evaluated)
    - Lower server load
    - Professional streaming experience
    """
    from flask import stream_with_context

    @stream_with_context
    def generate():
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Track specific fields instead of entire JSON to detect real changes
        last_status = None
        last_phase = None
        last_action = None
        last_progress = None

        retry_count = 0
        max_retries = 10  # Wait up to 5 seconds for session to be created

        # Send initial connection message
        yield f"data: {json.dumps({'connected': True})}\n\n"

        while True:
            try:
                # Fetch current status
                result = supabase.table("company_research_sessions").select("*").eq(
                    "jd_id", jd_id
                ).execute()

                if not result.data:
                    # Session not found - might be race condition during creation
                    retry_count += 1
                    if retry_count >= max_retries:
                        yield f"data: {json.dumps({'error': 'Session not found after retries'})}\n\n"
                        break
                    # Wait and retry
                    time.sleep(0.5)
                    continue

                session = result.data[0]
                status = session['status']
                search_config = session.get('search_config') or {}
                current_phase = search_config.get('current_phase')
                current_action = search_config.get('current_action')

                # Debug logging
                print(f"[STREAM] JD: {jd_id}, Status: {status}, Phase: {current_phase}, Action: {current_action}")

                # Calculate progress based on phase
                if status == 'failed':
                    progress = 0
                elif status == 'completed' and (current_phase == 'discovery' or not current_phase):
                    # Discovery complete (status=completed, phase=discovery), show 100%
                    progress = 100
                elif status == 'completed':
                    # Evaluation complete
                    progress = 100
                else:
                    phase = current_phase or 'discovery'

                    if phase == 'discovery':
                        # Discovery phase: 0-30%
                        total_discovered = session.get('total_discovered', 0)
                        if total_discovered > 0:
                            # Scale based on discovered companies (target ~100)
                            progress = min(int((total_discovered / 100) * 30), 30)
                        else:
                            progress = 5  # Show some progress even if count not available

                    elif phase == 'screening':
                        # Screening phase: 30-60%
                        total_discovered = session.get('total_discovered', 0)
                        total_screened = len(search_config.get('screened_companies', []))
                        if total_discovered > 0:
                            screening_pct = (total_screened / total_discovered) * 30
                            progress = min(int(30 + screening_pct), 60)
                        else:
                            progress = 45  # Mid-point of screening phase

                    elif phase == 'deep_research' or phase == 'evaluation':
                        # Evaluation phase: 60-100%
                        total_expected = session.get('max_companies', 25)
                        evaluated = session.get('total_evaluated', 0)
                        if total_expected > 0:
                            eval_pct = (evaluated / total_expected) * 40
                            progress = min(int(60 + eval_pct), 99)
                        else:
                            progress = 80  # Near end of evaluation
                    else:
                        # Unknown phase - default to 50%
                        progress = 50

                session['progress_percentage'] = progress

                # CRITICAL FIX: Send update if ANY key field changed (not entire JSON)
                fields_changed = (
                    status != last_status or
                    current_phase != last_phase or
                    current_action != last_action or
                    progress != last_progress
                )

                if fields_changed:
                    print(f"[STREAM] Sending update: status={status}, phase={current_phase}, progress={progress}%")
                    yield f"data: {json.dumps({'success': True, 'session': session})}\n\n"

                    # Update tracking variables
                    last_status = status
                    last_phase = current_phase
                    last_action = current_action
                    last_progress = progress

                # Stop streaming if completed or failed
                if status in ['completed', 'failed']:
                    print(f"[STREAM] Ending stream for status: {status}")
                    break

                # Stream every 2 seconds (reduced from 0.5s to minimize database queries)
                time.sleep(2.0)

            except Exception as e:
                print(f"[STREAM] Error: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'  # Allow CORS for local development
    })


@app.route('/research-companies/<jd_id>/results', methods=['GET'])
def get_research_results(jd_id):
    """Get research results for a JD."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Get query parameters
        min_score = request.args.get('min_score', type=float)
        category = request.args.get('category')
        limit = request.args.get('limit', 500, type=int)  # Increased to show ALL companies

        # Check session status
        session_result = supabase.table("company_research_sessions").select("*").eq(
            "jd_id", jd_id
        ).execute()

        if not session_result.data:
            return jsonify({'error': 'Session not found'}), 404

        session = session_result.data[0]

        if session['status'] not in ['completed', 'running']:
            return jsonify({
                'error': f"Research {session['status']}. Cannot retrieve results."
            }), 400

        # Special handling for discovery complete (status=completed, phase=discovery)
        # Return only discovered companies (no evaluation yet)
        search_config = session.get('search_config') or {}
        current_phase = search_config.get('phase')

        if session['status'] == 'completed' and current_phase == 'discovery':
            discovered_companies_list = search_config.get('discovered_companies_list', [])
            screened_companies = search_config.get('screened_companies', [])
            total_discovered = session.get('total_discovered', len(discovered_companies_list))

            return jsonify({
                'success': True,
                'results': {
                    'discovered_companies': discovered_companies_list[:100],
                    'screened_companies': screened_companies[:100],
                    'companies_by_category': {},  # Empty until evaluation
                    'evaluated_companies': [],  # No evaluated companies yet
                    'summary': {
                        'total_companies': 0,
                        'avg_relevance_score': 0,
                        'top_company': None,
                        'total_discovered': total_discovered,
                        'total_evaluated': 0,
                        'evaluation_progress': {
                            'evaluated_count': 0,
                            'remaining_count': len(screened_companies)
                        }
                    }
                }
            })

        # Build query
        query = supabase.table("target_companies").select("*").eq("jd_id", jd_id)

        if min_score:
            query = query.gte("relevance_score", min_score)

        if category:
            query = query.eq("category", category)

        # Execute query
        result = query.order("relevance_score", desc=True).limit(limit).execute()

        companies = result.data

        # Group by category (include ALL competitive intelligence categories)
        categorized = {
            "direct_competitor": [],
            "adjacent_company": [],
            "same_category": [],      # Competitive intelligence category
            "tangential": [],          # Competitive intelligence category
            "similar_stage": [],       # Legacy category
            "talent_pool": []          # Legacy category
        }

        for company in companies:
            cat = company.get("category", "talent_pool")
            if cat in categorized:
                categorized[cat].append(company)

        # Calculate summary
        total = len(companies)
        avg_score = sum(c.get("relevance_score", 0) for c in companies) / total if total > 0 else 0
        top_company = companies[0]["company_name"] if companies else None

        # Extract discovered and screened companies from session metadata
        search_config = session.get('search_config') or {}
        screened_companies = search_config.get('screened_companies', [])
        discovered_companies_list = search_config.get('discovered_companies_list', [])

        # Get total metrics from session
        total_discovered = session.get('total_discovered', len(discovered_companies_list))
        total_evaluated = session.get('total_evaluated', total)

        return jsonify({
            'success': True,
            'results': {
                'companies_by_category': categorized,
                'discovered_companies': discovered_companies_list[:100],  # All discovered (up to 100) with full objects
                'screened_companies': screened_companies[:100],    # Screened/ranked companies
                'evaluated_companies': companies,                   # Evaluated companies from DB
                'summary': {
                    'total_companies': total,
                    'avg_relevance_score': round(avg_score, 2),
                    'top_company': top_company,
                    'total_discovered': total_discovered,
                    'total_evaluated': total_evaluated,
                    'evaluation_progress': {
                        'evaluated_count': total_evaluated,
                        'remaining_count': len(screened_companies) - total_evaluated
                    }
                }
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/research-companies/<jd_id>/reset', methods=['DELETE', 'POST'])
def reset_research_session(jd_id):
    """Delete/reset a research session to allow fresh start."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Delete the session
        supabase.table("company_research_sessions").delete().eq("jd_id", jd_id).execute()

        print(f"✅ Deleted session: {jd_id}")

        return jsonify({
            'success': True,
            'message': f'Session {jd_id} deleted successfully'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/research-companies/<jd_id>/export-csv', methods=['GET'])
def export_research_csv(jd_id):
    """Export research results as CSV."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Get all companies for this JD
        result = supabase.table("target_companies").select("*").eq(
            "jd_id", jd_id
        ).order("relevance_score", desc=True).execute()

        if not result.data:
            return jsonify({'error': 'No results found'}), 404

        companies = result.data

        # Build CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Company Name',
            'Relevance Score',
            'Category',
            'Industry',
            'Employee Count',
            'Funding Stage',
            'Headquarters',
            'Why Relevant',
            'Discovered Via'
        ])

        # Data rows
        for company in companies:
            writer.writerow([
                company.get('company_name', ''),
                company.get('relevance_score', ''),
                company.get('category', ''),
                company.get('industry', ''),
                company.get('employee_count', ''),
                company.get('funding_stage', ''),
                company.get('headquarters_location', ''),
                company.get('screening_reasoning', ''),  # Fixed: Haiku uses screening_reasoning
                company.get('discovered_via', '')
            ])

        csv_data = output.getvalue()

        return jsonify({
            'success': True,
            'csv_data': csv_data,
            'filename': f'company_research_{jd_id[:8]}.csv'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# COMPANY LISTS ENDPOINTS
# ============================================

@app.route('/company-lists', methods=['POST'])
def save_company_list():
    """Save companies from research results as a reusable list."""
    try:
        data = request.json
        list_name = data.get('list_name')
        description = data.get('description', '')
        jd_title = data.get('jd_title', '')
        jd_session_id = data.get('jd_session_id', '')
        companies = data.get('companies', [])

        if not list_name or not companies:
            return jsonify({'error': 'list_name and companies are required'}), 400

        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Create the list
        list_data = {
            'list_name': list_name,
            'description': description,
            'jd_title': jd_title,
            'jd_session_id': jd_session_id,
            'total_companies': len(companies)
        }

        list_result = supabase.table('company_lists').insert(list_data).execute()

        if not list_result.data:
            return jsonify({'error': 'Failed to create list'}), 500

        list_id = list_result.data[0]['id']

        # Add all companies to the list
        company_items = []
        for company in companies:
            company_items.append({
                'list_id': list_id,
                'company_name': company.get('company_name', ''),
                'company_domain': company.get('company_domain', ''),
                'category': company.get('category', ''),
                'relevance_score': company.get('relevance_score', 0),
                'relevance_reasoning': company.get('screening_reasoning', ''),  # Fixed: read from screening_reasoning
                'industry': company.get('industry', ''),
                'employee_count': company.get('employee_count'),
                'funding_stage': company.get('funding_stage', ''),
                'company_metadata': company  # Store full company object
            })

        # Batch insert companies
        items_result = supabase.table('company_list_items').insert(company_items).execute()

        return jsonify({
            'success': True,
            'list_id': list_id,
            'list_name': list_name,
            'total_companies': len(companies)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/company-lists', methods=['GET'])
def get_company_lists():
    """Get all saved company lists."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        result = supabase.table('company_lists').select('*').order('created_at', desc=True).execute()

        return jsonify({
            'success': True,
            'lists': result.data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/company-lists/<int:list_id>', methods=['GET'])
def get_company_list(list_id):
    """Get a specific company list with all its companies."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Get list metadata
        list_result = supabase.table('company_lists').select('*').eq('id', list_id).execute()

        if not list_result.data:
            return jsonify({'error': 'List not found'}), 404

        # Get all companies in the list
        companies_result = supabase.table('company_list_items').select('*').eq(
            'list_id', list_id
        ).order('relevance_score', desc=True).execute()

        return jsonify({
            'success': True,
            'list': list_result.data[0],
            'companies': companies_result.data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/company-lists/<int:list_id>', methods=['DELETE'])
def delete_company_list(list_id):
    """Delete a company list (cascade deletes all companies in the list)."""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Delete the list (cascade will delete all items)
        result = supabase.table('company_lists').delete().eq('id', list_id).execute()

        return jsonify({
            'success': True,
            'message': 'List deleted successfully'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/', methods=['GET'])
def serve_frontend():
    """Serve the React frontend"""
    try:
        # Try to serve the built React app
        return app.send_static_file('index.html')
    except:
        # Fallback if static files not found
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn AI Assessor</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>LinkedIn AI Assessor</h1>
            <p>Backend is running. Please build and deploy the frontend.</p>
            <p>API endpoints are available at:</p>
            <ul>
                <li>POST /fetch-profile</li>
                <li>POST /assess-profile</li>
                <li>POST /batch-assess-profiles</li>
                <li>POST /search-profiles</li>
                <li>GET /health</li>
            </ul>
        </body>
        </html>
        """

@app.route('/search-by-company-list', methods=['POST'])
def search_by_company_list():
    """
    Search for people at a list of companies using CoreSignal.

    Request Body:
    {
        "company_names": ["Deepgram", "AssemblyAI", "ElevenLabs"],
        "filters": {
            "title": "engineer",  # Optional
            "seniority": "senior",  # Optional
            "location": "San Francisco"  # Optional
        },
        "max_per_company": 20  # Optional, default 20
    }

    Returns:
        {
            "success": true,
            "company_matches": [
                {
                    "company_name": "Deepgram",
                    "coresignal_id": "12345",
                    "confidence": 0.95,
                    "people_found": 15
                },
                ...
            ],
            "total_people": 45,
            "search_time_seconds": 5.2
        }
    """
    try:
        import time
        start_time = time.time()

        data = request.get_json()
        company_names = data.get("company_names", [])
        filters = data.get("filters", {})
        max_per_company = data.get("max_per_company", 20)

        if not company_names:
            return jsonify({'error': 'company_names is required'}), 400

        print(f"\n{'='*100}")
        print(f"[COMPANY SEARCH] Searching for people at {len(company_names)} companies")
        print(f"[COMPANY SEARCH] Filters: {filters}")
        print(f"{'='*100}\n")

        # Step 1: Look up CoreSignal company IDs
        from coresignal_company_lookup import CoreSignalCompanyLookup
        lookup_service = CoreSignalCompanyLookup()

        company_matches = []
        coresignal_company_ids = []

        for company_name in company_names:
            match = lookup_service.get_best_match(company_name, confidence_threshold=0.7)

            if match:
                company_matches.append({
                    "company_name": company_name,
                    "coresignal_name": match["name"],
                    "coresignal_id": match["company_id"],
                    "confidence": match["confidence"],
                    "website": match.get("website"),
                    "employee_count": match.get("employee_count")
                })
                coresignal_company_ids.append(match["company_id"])
                print(f"✓ {company_name} → {match['name']} (ID: {match['company_id']}, confidence: {match['confidence']})")
            else:
                print(f"✗ {company_name} → No match found")
                company_matches.append({
                    "company_name": company_name,
                    "coresignal_id": None,
                    "confidence": 0.0,
                    "error": "No matching company found"
                })

        if not coresignal_company_ids:
            return jsonify({
                'success': False,
                'error': 'No matching companies found in CoreSignal database',
                'company_matches': company_matches
            }), 404

        # Step 2: Search for people at these companies via CoreSignal
        from coresignal_service import search_profiles_by_company_ids

        people = search_profiles_by_company_ids(
            company_ids=coresignal_company_ids,
            title=filters.get("title"),
            seniority=filters.get("seniority"),
            location=filters.get("location"),
            max_per_company=max_per_company
        )

        # Add people_found count to each company match
        for match in company_matches:
            if match.get("coresignal_id"):
                match["people_found"] = len([
                    p for p in people
                    if p.get("company_id") == match["coresignal_id"]
                ])

        search_time = time.time() - start_time

        print(f"\n{'='*100}")
        print(f"[COMPANY SEARCH] Search complete")
        print(f"[COMPANY SEARCH] Companies matched: {len([m for m in company_matches if m.get('coresignal_id')])}/{len(company_names)}")
        print(f"[COMPANY SEARCH] Total people found: {len(people)}")
        print(f"[COMPANY SEARCH] Time: {search_time:.1f}s")
        print(f"{'='*100}\n")

        return jsonify({
            'success': True,
            'company_matches': company_matches,
            'people': people,
            'total_people': len(people),
            'search_time_seconds': round(search_time, 2)
        })

    except Exception as e:
        print(f"[COMPANY SEARCH] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set!")

    app.run(debug=True, host='0.0.0.0', port=5001)
    app.run(debug=True, host='0.0.0.0', port=5001)
