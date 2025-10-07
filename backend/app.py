from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from datetime import datetime
import calendar
from coresignal_service import CoreSignalService
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Anthropic client
anthropic_client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")  # Set your API key as environment variable
)

# Initialize CoreSignal service
coresignal_service = CoreSignalService()

# Database configuration - using Supabase REST API
SUPABASE_URL = "https://csikerdodixcqzfweiao.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzaWtlcmRvZGl4Y3F6ZndlaWFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk3ODEzMzMsImV4cCI6MjA3NTM1NzMzM30.5oDke2YAeabah-3o_lwxss-or6EzkkcaTA7sPvfsid4"

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
        
        # Call Anthropic API
        response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
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
    """Assess multiple profiles in parallel"""
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
        
        print(f"Created {len([t for t in assessment_tasks if t is not None])} parallel assessment tasks")
        
        # Execute all tasks in parallel
        if assessment_tasks:
            # Filter out None tasks and execute the real ones in parallel
            real_tasks = [task for task in assessment_tasks if task is not None]
            if real_tasks:
                print("🚀 Starting parallel AI assessments...")
                assessment_results = await asyncio.gather(*real_tasks, return_exceptions=True)
                print("✅ All parallel assessments completed!")
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
        
        # Limit batch size to prevent overwhelming the API
        if len(candidates) > 20:  # Reduced limit for AI assessment
            return jsonify({'error': 'Batch size cannot exceed 20 candidates for AI assessment'}), 400
        
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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)