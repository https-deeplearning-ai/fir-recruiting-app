from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from datetime import datetime
import calendar
import time
import random
import uuid
import threading
from coresignal_service import CoreSignalService
from dotenv import load_dotenv
import requests
import csv
from io import StringIO

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')

# Configure CORS
CORS(app)

# Session-based page tracking (resets on server restart)
used_pages_tracker = set()

# Job tracking system for background processing
job_tracker = {}
job_lock = threading.Lock()

# Database-based job persistence
def load_job_tracker():
    """Load job tracker from database"""
    try:
        # Query database for active jobs
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/job_tracker",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            jobs_data = response.json()
            job_dict = {}
            for job in jobs_data:
                job_dict[job['job_id']] = {
                    'status': job['status'],
                    'progress': job['progress'],
                    'total': job['total'],
                    'completed': job['completed'],
                    'failed': job['failed'],
                    'results': job.get('results', []),
                    'error': job.get('error'),
                    'started_at': job.get('started_at', time.time())
                }
            return job_dict
    except Exception as e:
        print(f"⚠️ Error loading job tracker from database: {e}")
    return {}

def save_job_tracker():
    """Save job tracker to database"""
    try:
        # Clear existing jobs first
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/job_tracker",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
        )
        
        # Insert current jobs
        for job_id, job_data in job_tracker.items():
            job_record = {
                "job_id": job_id,
                "status": job_data['status'],
                "progress": job_data['progress'],
                "total": job_data['total'],
                "completed": job_data['completed'],
                "failed": job_data['failed'],
                "results": job_data.get('results', []),
                "error": job_data.get('error'),
                "started_at": job_data.get('started_at', time.time())
            }
            
            requests.post(
                f"{SUPABASE_URL}/rest/v1/job_tracker",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                },
                json=job_record
            )
    except Exception as e:
        print(f"⚠️ Error saving job tracker to database: {e}")

# Load existing jobs on startup
job_tracker = load_job_tracker()
print(f"📋 Loaded {len(job_tracker)} existing jobs from database")

# Initialize Anthropic client
anthropic_client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")  # Set your API key as environment variable
)

# Initialize CoreSignal service
coresignal_service = CoreSignalService()

# CoreSignal API configuration
CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY", "zGZEUYUw2Koty9kxPidzCHTce5Wl2vYL")

# Load valid input values for intelligent search
script_dir = os.path.dirname(os.path.abspath(__file__))
input_values_path = os.path.join(script_dir, 'input_values.json')
try:
    with open(input_values_path, 'r') as f:
        VALID_INPUT_VALUES = json.load(f)
    print("✅ Loaded input values for intelligent search")
except Exception as e:
    print(f"⚠️ Warning: Could not load input_values.json: {e}")
    VALID_INPUT_VALUES = {}

# Database configuration - using Supabase REST API
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://csikerdodixcqzfweiao.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzaWtlcmRvZGl4Y3F6ZndlaWFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk3ODEzMzMsImV4cCI6MjA3NTM1NzMzM30.5oDke2YAeabah-3o_lwxss-or6EzkkcaTA7sPvfsid4")

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
            model="claude-3-7-sonnet-20250219",
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
    
    try:
        # Use the /preview endpoint with page parameter (max page=5)
        url = f"https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview?page={page}"
        
        print(f"📄 Fetching page {page}...")
        
        response = requests.post(url, json=query, headers=headers)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
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
            error_text = response.text
            print(f"   ❌ Error: {response.status_code} - {error_text}")
            return {"success": False, "error": f"API error {response.status_code}: {error_text}"}
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "error": str(e)}

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
        headline = profile.get('headline', '')
        location = profile.get('location_raw_address', '')
        job_title = profile.get('job_title', '')
        
        writer.writerow([profile_url, first_name, last_name, full_name, headline, location, job_title])
    
    return output.getvalue()

def extract_profile_summary(profile_data):
    """Extract key information from LinkedIn profile for analysis"""
    try:
        # Basic info
        full_name = profile_data.get('full_name', 'N/A')
        headline = profile_data.get('headline', 'N/A')
        location = profile_data.get('location', 'N/A')
        industry = profile_data.get('industry', 'N/A')
        
        # Experience
        experiences = profile_data.get('experience', [])
        current_roles = [exp for exp in experiences if exp.get('is_current', 0) == 1]
        
        # Calculate total experience years without double-counting overlaps
        def to_date(year: int, month: int, is_end: bool) -> datetime:
            """Create a datetime at start or end of given month/year."""
            month = max(1, min(12, month)) if month else (12 if is_end else 1)
            if is_end:
                last_day = calendar.monthrange(year, month)[1]
                return datetime(year, month, last_day)
            return datetime(year, month, 1)

        # Build normalized intervals (start, end) in datetime
        intervals = []
        now = datetime.now()
        for exp in experiences:
            start_year = exp.get('date_from_year')
            end_year = exp.get('date_to_year')
            if not start_year:
                continue  # cannot use this interval without a start year

            start_month = exp.get('date_from_month') or 1
            # If current role, use 'now' as the end date
            is_current = bool(exp.get('is_current')) or exp.get('is_current', 0) == 1
            if is_current:
                end_dt = now
            elif end_year:
                end_month = exp.get('date_to_month') or 12
                end_dt = to_date(int(end_year), int(end_month), is_end=True)
            else:
                # No end given and not flagged current; assume ongoing
                end_dt = now

            start_dt = to_date(int(start_year), int(start_month), is_end=False)
            if end_dt <= start_dt:
                continue
            intervals.append((start_dt, end_dt))

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
            'experiences': experiences
        }
    except Exception as e:
        return {'error': f'Error processing profile: {str(e)}'}

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
    
    base_prompt = f"""
You are an objective, evidence-first hiring assessor. You will read the provided LinkedIn profile JSON and the hiring criteria. Be strict and conservative. Please also check the company that the candidate has worked at, and make inferences based on the company's size, stage, and industry.

Profile Summary:
- Name: {profile_summary.get('full_name', 'N/A')}
- Location: {profile_summary.get('location', 'N/A')}
- Industry: {profile_summary.get('industry', 'N/A')}
- Total Years of Experience: {profile_summary.get('total_experience_years', 0)}
- Number of Positions: {profile_summary.get('total_experiences', 0)}
- Current Roles: {[role.get('title', 'N/A') + ' at ' + role.get('company_name', 'N/A') for role in profile_summary.get('current_roles', [])]}
- Experiences: {profile_summary.get('experiences', [])}

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
    """Fetch LinkedIn profile data from CoreSignal API using LinkedIn URL"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        linkedin_url = data.get('linkedin_url')
        
        if not linkedin_url:
            return jsonify({'error': 'LinkedIn URL is required'}), 400
        
        # Validate LinkedIn URL format
        if not linkedin_url.startswith('https://www.linkedin.com/in/'):
            return jsonify({'error': 'Invalid LinkedIn URL format. Please use: https://www.linkedin.com/in/username'}), 400
        
        # Fetch profile data from CoreSignal
        result = coresignal_service.fetch_linkedin_profile(linkedin_url)
        
        if not result['success']:
            error_response = {'error': result['error']}
            if 'debug_info' in result:
                error_response['debug_info'] = result['debug_info']
            return jsonify(error_response), 400
        
        return jsonify({
            'success': True,
            'profile_data': result['profile_data'],
            'employee_id': result['employee_id']
        })
        
    except Exception as e:
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
                model="claude-3-7-sonnet-20250219",
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
                cleaned_response = cleaned_response[7:].strip()  # Remove ```json and strip whitespace
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:].strip()   # Remove ``` and strip whitespace
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3].strip()  # Remove trailing ``` and strip whitespace
            
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

@app.route('/batch-fetch-profiles', methods=['POST'])
def batch_fetch_profiles():
    """Fetch multiple LinkedIn profiles in parallel"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        candidates = data.get('candidates', [])
        
        if not candidates:
            return jsonify({'error': 'No candidates provided'}), 400
        
        if not isinstance(candidates, list):
            return jsonify({'error': 'Candidates must be provided as a list'}), 400
        
        # Limit batch size to prevent overwhelming the API
        if len(candidates) > 50:
            return jsonify({'error': 'Batch size cannot exceed 50 URLs'}), 400
        
        print(f"Processing batch of {len(candidates)} LinkedIn URLs...")
        print("Received candidates:", candidates)
        
        # Extract URLs for profile fetching
        linkedin_urls = [candidate['url'] for candidate in candidates]
        
        # Run the async batch processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(fetch_profiles_batch_async(linkedin_urls))
        finally:
            loop.close()
        
        # Add CSV names to results
        for i, result in enumerate(results):
            if i < len(candidates):
                result['csv_name'] = candidates[i]['fullName']
                result['csv_first_name'] = candidates[i]['firstName']
                result['csv_last_name'] = candidates[i]['lastName']
        
        # Count successful and failed results
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        
        print(f"Batch processing complete: {successful} successful, {failed} failed")
        
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
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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
        
        # Call Anthropic API with minimal retry (new API key has higher rate limits)
        max_retries = 3
        retry_delay = 2  # Short delay for retries
        
        for attempt in range(max_retries):
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                break  # Success, exit retry loop
            except Exception as api_error:
                error_str = str(api_error)
                # Check if it's a rate limit error (429)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay  # Fixed short delay instead of exponential
                        print(f"⚠️ Rate limit hit for {profile_data.get('full_name', 'Unknown')}. Retrying in {wait_time} seconds (attempt {attempt + 2}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ Rate limit persists after {max_retries} attempts for {profile_data.get('full_name', 'Unknown')}")
                        raise api_error
                else:
                    # Not a rate limit error, raise immediately
                    raise api_error
        
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

async def assess_single_profile_async(session, profile_data, user_prompt, weighted_requirements):
    """Assess a single profile asynchronously using thread pool"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, 
            assess_single_profile_sync, 
            profile_data, 
            user_prompt, 
            weighted_requirements
        )
    return result

async def assess_profiles_batch_async(profiles_data, user_prompt, weighted_requirements):
    """Assess multiple profiles in parallel with rate limit batching (5 at a time)"""
    async with aiohttp.ClientSession() as session:
        # Create tasks for all profiles that were successfully fetched
        assessment_tasks = []
        profile_mapping = {}  # Map task index to profile_result
        
        for i, profile_result in enumerate(profiles_data):
            if profile_result.get('success') and profile_result.get('profile_data'):
                # Extract the actual profile data from the nested structure
                profile_data = profile_result['profile_data']
                
                if isinstance(profile_data, dict) and 'profile_data' in profile_data:
                    # CoreSignal returns nested structure
                    actual_profile_data = profile_data['profile_data']
                else:
                    # Direct profile data
                    actual_profile_data = profile_data
                
                print(f"Profile {i}: {actual_profile_data.get('full_name', 'Unknown')} - {profile_result.get('url', 'No URL')}")
                
                task = assess_single_profile_async(session, actual_profile_data, user_prompt, weighted_requirements)
                assessment_tasks.append(task)
                profile_mapping[len(assessment_tasks) - 1] = profile_result
            else:
                # For failed profiles, add None to maintain index mapping
                print(f"Profile {i}: Skipping failed profile - {profile_result.get('url', 'No URL')}")
                assessment_tasks.append(None)
                profile_mapping[len(assessment_tasks) - 1] = profile_result
        
        print(f"Created {len([t for t in assessment_tasks if t is not None])} assessment tasks")
        
        # Execute tasks in PARALLEL (new API has higher rate limits)
        if assessment_tasks:
            # Filter out None tasks and execute the real ones in parallel
            real_tasks = [task for task in assessment_tasks if task is not None]
            if real_tasks:
                print(f"🚀 Starting parallel AI assessments ({len(real_tasks)} total)...")
                
                # Execute all tasks in parallel
                try:
                    assessment_results = await asyncio.gather(*real_tasks, return_exceptions=True)
                    
                    # Handle any exceptions that occurred
                    processed_results = []
                    for i, result in enumerate(assessment_results):
                        if isinstance(result, Exception):
                            print(f"❌ Assessment task {i+1} failed: {result}")
                            processed_results.append({
                                'success': False,
                                'assessment': None,
                                'profile_summary': None,
                                'error': str(result)
                            })
                        else:
                            processed_results.append(result)
                    
                    assessment_results = processed_results
                    print("✅ All parallel assessments completed!")
                except Exception as e:
                    print(f"❌ Error in parallel assessment execution: {e}")
                    assessment_results = [{
                        'success': False,
                        'assessment': None,
                        'profile_summary': None,
                        'error': str(e)
                    } for _ in real_tasks]
            else:
                assessment_results = []
        else:
            assessment_results = []
        
        # Map results back to original profile order
        results = []
        task_index = 0
        for i, profile_result in enumerate(profiles_data):
            if assessment_tasks[i] is not None:
                # This profile had an assessment task
                if task_index < len(assessment_results):
                    assessment_result = assessment_results[task_index]
                    
                    # Handle exceptions
                    if isinstance(assessment_result, Exception):
                        print(f"❌ Assessment task failed with exception: {assessment_result}")
                        assessment_result = {
                            'success': False,
                            'assessment': None,
                            'profile_summary': None,
                            'error': f'Assessment task failed: {str(assessment_result)}'
                        }
                    
                    # Combine profile data with assessment
                    combined_result = {
                        'url': profile_result['url'],
                        'success': profile_result['success'],
                        'profile_data': profile_result['profile_data'],
                        'assessment': assessment_result.get('assessment'),
                        'profile_summary': assessment_result.get('profile_summary'),
                        'assessment_error': assessment_result.get('error')
                    }
                    results.append(combined_result)
                    task_index += 1
                else:
                    # This shouldn't happen, but handle gracefully
                    results.append({
                        'url': profile_result['url'],
                        'success': False,
                        'profile_data': profile_result['profile_data'],
                        'assessment': None,
                        'profile_summary': None,
                        'assessment_error': 'Assessment result not found'
                    })
            else:
                # Failed profile - no assessment, but create a structured response with N/A scores
                results.append({
                    'url': profile_result['url'],
                    'success': False,
                    'profile_data': None,
                    'assessment': {
                        'overall_score': 'N/A',
                        'recommend': False,
                        'strengths': [],
                        'weaknesses': [],
                        'career_trajectory': 'Profile not found in CoreSignal database',
                        'detailed_analysis': 'Unable to assess - LinkedIn profile not found in our database',
                        'weighted_analysis': {
                            'requirements': [],
                            'weighted_score': 'N/A',
                            'general_fit_score': 'N/A',
                            'general_fit_weight': 0,
                            'general_fit_analysis': 'Profile not found'
                        }
                    },
                    'profile_summary': None,
                    'assessment_error': 'Profile not found'
                })
        
        return results

@app.route('/batch-assess-profiles', methods=['POST'])
def batch_assess_profiles():
    """Fetch profiles and assess them with AI in parallel"""
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
        
        # Limit batch size to prevent overwhelming the API and avoid timeouts
        # With new API key, we can handle larger batches with parallel processing
        if len(candidates) > 50:  # Increased batch size with parallel processing
            return jsonify({'error': 'Batch size cannot exceed 50 candidates for AI assessment. Process multiple batches separately.'}), 400
        
        print(f"Processing batch assessment of {len(candidates)} candidates...")
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
        
        # Step 2: Match profiles with candidate names and assess with AI
        print("Step 2: Matching profiles with candidates and assessing with AI...")
        print(f"Profiles data before assessment: {[(r.get('url'), r.get('success'), 'has_data' if r.get('profile_data') else 'no_data') for r in profiles_data]}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            assessment_results = loop.run_until_complete(assess_profiles_batch_async(profiles_data, user_prompt, weighted_requirements))
        finally:
            loop.close()
        
        print(f"Assessment results: {[(r.get('url'), r.get('success'), 'has_assessment' if r.get('assessment') else 'no_assessment', r.get('assessment_error')) for r in assessment_results]}")
        
        # Step 3: Add CSV names to results and sort by weighted score (descending)
        print("Step 3: Adding CSV names and ranking profiles by weighted score...")
        for i, result in enumerate(assessment_results):
            if i < len(candidates):
                result['csv_name'] = candidates[i]['fullName']
                result['csv_first_name'] = candidates[i]['firstName']
                result['csv_last_name'] = candidates[i]['lastName']
        
        def get_weighted_score(result):
            if result.get('assessment') and result['assessment'].get('weighted_analysis'):
                score = result['assessment']['weighted_analysis'].get('weighted_score', 0)
                # Handle string scores like 'N/A' by converting to 0
                if isinstance(score, str):
                    return 0
                return score
            return 0
        
        assessment_results.sort(key=get_weighted_score, reverse=True)
        
        # Count successful and failed results
        # Successful = profile found AND assessment completed successfully
        successful = sum(1 for r in assessment_results if r.get('success', False) and r.get('assessment') and not r.get('assessment_error'))
        # Failed = profile not found OR assessment failed
        failed = len(assessment_results) - successful
        
        print(f"Batch assessment complete: {successful} successful, {failed} failed")
        
        return jsonify({
            'success': True,
            'results': assessment_results,
            'summary': {
                'total': len(assessment_results),
                'successful': successful,
                'failed': failed
            }
        })
        
    except Exception as e:
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

@app.route('/start-batch-assessment', methods=['POST'])
def start_batch_assessment():
    """Start a background batch assessment job and return job_id"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        candidates = data.get('candidates', [])
        user_prompt = data.get('user_prompt', 'Provide a general professional assessment')
        weighted_requirements = data.get('weighted_requirements', [])
        
        if not candidates:
            return jsonify({'error': 'No candidates provided'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        with job_lock:
            job_tracker[job_id] = {
                'status': 'processing',
                'progress': 0,
                'total': len(candidates),
                'completed': 0,
                'failed': 0,
                'results': [],
                'error': None,
                'started_at': time.time()
            }
            save_job_tracker()
            print(f"✅ Created job {job_id} with {len(candidates)} candidates. Total jobs in tracker: {len(job_tracker)}")
        
        # Start background processing
        def process_job():
            try:
                print(f"🚀 Starting background job {job_id} with {len(candidates)} candidates")
                
                # Process ALL candidates in one batch with parallel processing
                print(f"Processing all {len(candidates)} candidates at once for job {job_id}")
                
                # Process all candidates in parallel
                batch_results = process_candidate_batch(candidates, user_prompt, weighted_requirements)
                
                # Update job status
                with job_lock:
                    if job_id in job_tracker:
                        job_tracker[job_id]['results'] = batch_results
                        job_tracker[job_id]['completed'] = len(batch_results)
                        job_tracker[job_id]['progress'] = 100
                        
                        # Count successful vs failed
                        successful = len([r for r in batch_results if r.get('success', False)])
                        failed = len(batch_results) - successful
                        job_tracker[job_id]['failed'] = failed
                        save_job_tracker()
                
                # Mark job as completed
                with job_lock:
                    if job_id in job_tracker:
                        job_tracker[job_id]['status'] = 'completed'
                        job_tracker[job_id]['progress'] = 100
                        save_job_tracker()
                
                print(f"✅ Background job {job_id} completed successfully")
                
            except Exception as e:
                print(f"❌ Background job {job_id} failed: {str(e)}")
                with job_lock:
                    if job_id in job_tracker:
                        job_tracker[job_id]['status'] = 'failed'
                        job_tracker[job_id]['error'] = str(e)
                        save_job_tracker()
        
        # Start the background thread
        thread = threading.Thread(target=process_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Background assessment started'
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/check-job-status/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Check the status of a background job"""
    try:
        # Load job from database to ensure we have the latest state
        current_job_tracker = load_job_tracker()
        
        if job_id not in current_job_tracker:
            print(f"❌ Job {job_id} not found in tracker. Available jobs: {list(current_job_tracker.keys())}")
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = current_job_tracker[job_id].copy()
        print(f"✅ Job {job_id} found. Status: {job_info.get('status')}, Progress: {job_info.get('progress')}%")
        
        return jsonify({
            'success': True,
            'job_info': job_info
        })
        
    except Exception as e:
        print(f"❌ Error checking job status: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get-job-results/<job_id>', methods=['GET'])
def get_job_results(job_id):
    """Get the results of a completed job"""
    try:
        # Load job from database to ensure we have the latest state
        current_job_tracker = load_job_tracker()
        
        if job_id not in current_job_tracker:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = current_job_tracker[job_id]
        
        if job_info['status'] != 'completed':
            return jsonify({'error': 'Job not completed yet'}), 400
        
        results = job_info['results']
        successful = len([r for r in results if r.get('success', False)])
        failed = job_info['failed']
        
        # Clean up old job (optional, to prevent memory leaks)
        # del job_tracker[job_id]
        
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
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def process_candidate_batch(candidates, user_prompt, weighted_requirements):
    """Process a small batch of candidates (extracted from original batch function)"""
    try:
        print(f"Processing batch assessment of {len(candidates)} candidates...")
        print(f"Received candidates: {candidates}")
        
        # Step 1: Fetch all profiles in parallel
        print("Step 1: Fetching profiles...")
        profiles_data = []
        
        for candidate in candidates:
            url = candidate.get('url', '')
            if not url:
                print(f"⚠️ Skipping candidate with no URL: {candidate}")
                profiles_data.append({
                    'success': False,
                    'url': url,
                    'profile_data': None,
                    'error': 'No URL provided'
                })
                continue
            
            print(f"Searching for profile: {url}")
            try:
                # Search for employee ID
                print("Step 1: Searching for employee ID...")
                result = coresignal_service.fetch_linkedin_profile(url)
                
                if not result.get('success', False):
                    print(f"❌ Error fetching profile for {url}: {result.get('error', 'Unknown error')}")
                    profiles_data.append({
                        'success': False,
                        'url': url,
                        'profile_data': None,
                        'error': result.get('error', 'Unknown error')
                    })
                    continue
                
                profile_data = result.get('profile_data')
                employee_id = result.get('employee_id')
                
                if not profile_data:
                    print(f"❌ No profile data found for {url}")
                    profiles_data.append({
                        'success': False,
                        'url': url,
                        'profile_data': None,
                        'error': 'No profile data found'
                    })
                    continue
                
                profiles_data.append({
                    'success': True,
                    'url': url,
                    'profile_data': profile_data,
                    'error': None
                })
                
            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                profiles_data.append({
                    'success': False,
                    'url': url,
                    'profile_data': None,
                    'error': str(e)
                })
        
        # Step 2: Process AI assessments in parallel (new API has higher rate limits)
        print("Step 2: Matching profiles with candidates and assessing with AI...")
        print(f"Profiles data before assessment: {[(p.get('url', 'No URL'), p.get('success', False), 'has_data' if p.get('profile_data') else 'no_data') for p in profiles_data]}")
        
        # Prepare assessment tasks for parallel processing
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
                print(f"DEBUG: Profile data keys: {list(actual_profile_data.keys()) if isinstance(actual_profile_data, dict) else 'Not a dict'}")
                
                # Create assessment task for parallel execution
                # Use a closure to capture the current profile data
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
        
        print(f"Created {len([t for t in assessment_tasks if t is not None])} assessment tasks for parallel processing")
        
        # Execute assessments in parallel using ThreadPoolExecutor
        results = []
        if assessment_tasks:
            # Filter out None tasks
            real_tasks = [task for task in assessment_tasks if task is not None]
            if real_tasks:
                print(f"🚀 Starting parallel AI assessments ({len(real_tasks)} total)...")
                
                # Use ThreadPoolExecutor for parallel processing
                # Dynamic worker count: use the number of candidates as the worker count
                max_workers = min(len(real_tasks), 50)  # Cap at 50 to prevent resource issues
                print(f"🔧 Using {max_workers} parallel workers for {len(real_tasks)} AI assessments")
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_index = {}
                    real_task_index = 0
                    for i, task in enumerate(assessment_tasks):
                        if task is not None:
                            future = executor.submit(task)
                            future_to_index[future] = i
                            real_task_index += 1
                    
                    # Collect results as they complete
                    for future in future_to_index:
                        try:
                            assessment_result = future.result()
                            profile_result = profile_mapping[future_to_index[future]]
                            results.append({
                                'success': assessment_result.get('success', False),
                                'url': profile_result.get('url'),
                                'profile_data': profile_result.get('profile_data'),
                                'profile_summary': assessment_result.get('profile_summary'),
                                'assessment': assessment_result.get('assessment'),
                                'error': assessment_result.get('error')
                            })
                        except Exception as e:
                            print(f"❌ Assessment task failed: {str(e)}")
                            profile_result = profile_mapping[future_to_index[future]]
                            results.append({
                                'success': False,
                                'url': profile_result.get('url'),
                                'profile_data': profile_result.get('profile_data'),
                                'profile_summary': None,
                                'assessment': None,
                                'error': str(e)
                            })
                
                print("✅ All parallel assessments completed!")
            else:
                results = []
        
        # Add results for failed profiles
        for i, profile_result in enumerate(profiles_data):
            if not (profile_result.get('success') and profile_result.get('profile_data')):
                results.append({
                    'success': False,
                    'url': profile_result.get('url'),
                    'profile_data': profile_result.get('profile_data'),
                    'profile_summary': None,
                    'assessment': None,
                    'error': profile_result.get('error', 'Profile fetch failed')
                })
        
        # Add CSV names to results to match with candidates
        for i, result in enumerate(results):
            if i < len(candidates):
                result['csv_name'] = candidates[i]['fullName']
                result['csv_first_name'] = candidates[i]['firstName']
                result['csv_last_name'] = candidates[i]['lastName']
        
        return results
        
    except Exception as e:
        print(f"❌ Error in process_candidate_batch: {str(e)}")
        return [{
            'success': False,
            'url': candidate.get('url', 'Unknown'),
            'profile_summary': None,
            'assessment': None,
            'error': f'Batch processing error: {str(e)}'
        } for candidate in candidates]

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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React app for all non-API routes"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set!")
    
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)