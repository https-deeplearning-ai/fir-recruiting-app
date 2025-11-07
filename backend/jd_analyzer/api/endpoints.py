"""
API Endpoints for JD Analyzer

Flask routes for integrating JD analysis into the application.
Add these to your main app.py file.
"""

from flask import request, jsonify
from jd_analyzer.core.jd_parser import JDParser
from jd_analyzer.core.weight_generator import WeightGenerator
from jd_analyzer.core.shortlist_analyzer import ShortlistAnalyzer
from jd_analyzer.query.query_builder import JDToQueryBuilder
from jd_analyzer.query.llm_query_generator import MultiLLMQueryGenerator
from jd_analyzer.core.models import JDRequirements
from jd_analyzer.utils.debug_logger import debug_log
from pydantic import ValidationError
import os
import tempfile
import requests
import csv
from io import StringIO
import logging
import sys
import time

# Configure comprehensive logging for JD Analyzer
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/jd_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

# Lazy initialization - services created on first use to avoid import-time failures
_jd_parser = None
_weight_generator = None
_query_builder = None
_multi_llm_generator = None

def get_jd_parser():
    """Lazy initialize JD Parser"""
    global _jd_parser
    if _jd_parser is None:
        _jd_parser = JDParser()
    return _jd_parser

def get_weight_generator():
    """Lazy initialize Weight Generator"""
    global _weight_generator
    if _weight_generator is None:
        _weight_generator = WeightGenerator()
    return _weight_generator

def get_query_builder():
    """Lazy initialize Query Builder"""
    global _query_builder
    if _query_builder is None:
        _query_builder = JDToQueryBuilder()
    return _query_builder

def get_multi_llm_generator():
    """Lazy initialize Multi-LLM Generator"""
    global _multi_llm_generator
    if _multi_llm_generator is None:
        _multi_llm_generator = MultiLLMQueryGenerator()
    return _multi_llm_generator


def make_coresignal_request_with_retry(url, payload, headers, max_retries=2, timeout=30):
    """
    Make CoreSignal API request with retry logic for 503 errors.

    CoreSignal uses 18 requests/second rate limit and returns 503 (not 429) for rate limiting.

    Args:
        url: CoreSignal API endpoint URL
        payload: Request payload (query)
        headers: Request headers with API key
        max_retries: Maximum number of retries (default 2)
        timeout: Request timeout in seconds (default 30)

    Returns:
        tuple: (success: bool, response_json: dict/list, error_msg: str)
    """
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"CoreSignal API request (attempt {attempt + 1}/{max_retries + 1})")
            logger.debug(f"Request payload: {payload}")

            response = requests.post(url, json=payload, headers=headers, timeout=timeout)

            if response.status_code == 200:
                logger.info(f"CoreSignal API success (status 200)")
                return (True, response.json(), None)

            # Log error details
            error_body = response.text[:500] if response.text else "No response body"
            logger.error(f"CoreSignal API error: status={response.status_code}, body={error_body}")

            # Retry on 503 (rate limiting)
            if response.status_code == 503 and attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                logger.warning(f"Rate limit (503) - retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            # Return error for non-retryable status codes or max retries reached
            return (False, None, f"CoreSignal API error: {response.status_code} - {error_body}")

        except requests.exceptions.Timeout:
            logger.error(f"CoreSignal API timeout after {timeout}s")
            if attempt < max_retries:
                logger.warning(f"Retrying after timeout...")
                time.sleep(2)
                continue
            return (False, None, f"Request timeout after {timeout}s")

        except Exception as e:
            logger.exception(f"CoreSignal API exception: {str(e)}")
            return (False, None, f"Request exception: {str(e)}")

    return (False, None, "Max retries exceeded")


def register_jd_analyzer_routes(app):
    """
    Register JD analyzer routes with Flask app.

    Usage in app.py:
        from jd_analyzer.api_endpoints import register_jd_analyzer_routes
        register_jd_analyzer_routes(app)
    """

    @app.route('/api/jd/parse', methods=['POST'])
    def parse_jd():
        """
        Parse job description and extract structured requirements.

        Request:
            {
                "jd_text": "full job description text..."
            }

        Response:
            {
                "success": true,
                "requirements": {
                    "role_title": "...",
                    "seniority_level": "...",
                    "must_have": [...],
                    "nice_to_have": [...],
                    "technical_skills": [...],
                    "domain_expertise": [...],
                    "experience_years": {...},
                    "location": "...",
                    "implicit_criteria": {...}
                }
            }
        """
        try:
            data = request.json
            jd_text = data.get('jd_text', '')

            if not jd_text:
                return jsonify({
                    "success": False,
                    "error": "No job description text provided"
                }), 400

            # ============= DEBUG LOGGING =============
            print(f"\n{'='*100}")
            print(f"[JD PARSER INPUT] Received JD text (length={len(jd_text)} chars)")
            print(f"[JD PARSER INPUT] First 300 chars:")
            print(f"{jd_text[:300]}...")
            print(f"{'='*100}\n")
            # =========================================

            requirements = get_jd_parser().parse(jd_text)

            # ============= DEBUG LOGGING =============
            print(f"\n{'='*100}")
            print(f"[JD PARSER OUTPUT] Extracted requirements:")
            print(f"  - role_title: {requirements.role_title}")
            print(f"  - seniority_level: {requirements.seniority_level}")
            print(f"  - domain_expertise: {requirements.domain_expertise}")
            print(f"  - technical_skills: {requirements.technical_skills[:5] if len(requirements.technical_skills) > 5 else requirements.technical_skills}")
            print(f"  - location: {requirements.location}")
            print(f"{'='*100}\n")
            # =========================================

            return jsonify({
                "success": True,
                "requirements": requirements.model_dump()  # Convert Pydantic model to dict
            })

        except Exception as e:
            print(f"[JD PARSER ERROR] {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/generate-weights', methods=['POST'])
    def generate_weights():
        """
        Generate weighted requirements for assessment from JD.

        Request:
            {
                "jd_text": "full job description text...",
                "num_requirements": 5  // optional, 1-5
            }

        OR:

            {
                "jd_requirements": {...},  // from /api/jd/parse
                "num_requirements": 5
            }

        Response:
            {
                "success": true,
                "weighted_requirements": [
                    {
                        "requirement": "Voice AI Expertise",
                        "weight": 35,
                        "description": "...",
                        "scoring_criteria": "..."
                    },
                    ...
                ],
                "general_fit_weight": 15,
                "explanation": "markdown formatted explanation"
            }
        """
        try:
            data = request.json
            num_requirements = data.get('num_requirements', 5)

            # Validate num_requirements
            if not (1 <= num_requirements <= 5):
                return jsonify({
                    "success": False,
                    "error": "num_requirements must be between 1 and 5"
                }), 400

            # Check if we have pre-parsed requirements or need to parse JD
            if 'jd_requirements' in data:
                jd_requirements = data['jd_requirements']
            elif 'jd_text' in data:
                jd_text = data['jd_text']
                if not jd_text:
                    return jsonify({
                        "success": False,
                        "error": "No job description provided"
                    }), 400
                jd_requirements = get_jd_parser().parse(jd_text)
            else:
                return jsonify({
                    "success": False,
                    "error": "Must provide either jd_text or jd_requirements"
                }), 400

            # Generate weighted requirements (convert Pydantic model to dict if needed)
            jd_requirements_dict = jd_requirements.model_dump() if hasattr(jd_requirements, 'model_dump') else jd_requirements
            weighted_reqs = get_weight_generator().generate_weighted_requirements(
                jd_requirements_dict,
                num_requirements
            )

            # Calculate general fit weight
            total_custom = sum(req['weight'] for req in weighted_reqs)
            general_fit = 100 - total_custom

            # Generate explanation
            explanation = get_weight_generator().explain_weights(weighted_reqs)

            return jsonify({
                "success": True,
                "weighted_requirements": weighted_reqs,
                "general_fit_weight": general_fit,
                "explanation": explanation
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/analyze-shortlist', methods=['POST'])
    def analyze_shortlist():
        """
        Analyze a candidate shortlist to discover implicit criteria.

        Request (multipart/form-data):
            - csv_file: CSV file with columns [Profile URL, Current Title, Current Company, Location]
            - jd_text: Optional job description for gap analysis

        Response:
            {
                "success": true,
                "analysis": {
                    "total_candidates": 68,
                    "location_distribution": {...},
                    "seniority_distribution": {...},
                    "top_companies": [...],
                    "implicit_criteria": {...}
                },
                "gaps": {...},  // if jd_text provided
                "report": "markdown formatted report"
            }
        """
        try:
            # Check if CSV file is provided
            if 'csv_file' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No CSV file provided"
                }), 400

            csv_file = request.files['csv_file']

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_file:
                csv_content = csv_file.read().decode('utf-8')
                temp_file.write(csv_content)
                temp_path = temp_file.name

            try:
                # Analyze shortlist
                analyzer = ShortlistAnalyzer(temp_path)
                analyzer.load_candidates()
                analysis = analyzer.analyze_patterns()

                # Optional: compare to JD if provided
                jd_text = request.form.get('jd_text')
                gaps = None
                if jd_text:
                    jd_requirements = get_jd_parser().parse(jd_text)
                    gaps = analyzer.compare_to_jd(jd_requirements)
                    report = analyzer.generate_report(jd_requirements)
                else:
                    report = analyzer.generate_report()

                return jsonify({
                    "success": True,
                    "analysis": analysis,
                    "gaps": gaps,
                    "report": report
                })

            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/extract-keywords', methods=['POST'])
    def extract_keywords():
        """
        Extract keywords from JD for search queries.

        Request:
            {
                "jd_text": "full job description text..."
            }

        Response:
            {
                "success": true,
                "keywords": ["keyword1", "keyword2", ...]
            }
        """
        try:
            data = request.json
            jd_text = data.get('jd_text', '')

            if not jd_text:
                return jsonify({
                    "success": False,
                    "error": "No job description text provided"
                }), 400

            keywords = get_jd_parser().extract_keywords(jd_text)

            return jsonify({
                "success": True,
                "keywords": keywords
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/full-analysis', methods=['POST'])
    def full_jd_analysis():
        """
        Complete JD analysis: parse + generate weights + extract keywords.

        Request:
            {
                "jd_text": "full job description text...",
                "num_requirements": 5  // optional
            }

        Response:
            {
                "success": true,
                "requirements": {...},
                "weighted_requirements": [...],
                "keywords": [...],
                "general_fit_weight": 15
            }
        """
        try:
            data = request.json
            jd_text = data.get('jd_text', '')
            num_requirements = data.get('num_requirements', 5)

            if not jd_text:
                return jsonify({
                    "success": False,
                    "error": "No job description text provided"
                }), 400

            # Parse JD
            requirements = get_jd_parser().parse(jd_text)

            # Generate weights (convert Pydantic model to dict)
            weighted_reqs = get_weight_generator().generate_weighted_requirements(
                requirements.model_dump() if hasattr(requirements, 'model_dump') else requirements,
                num_requirements
            )

            # Extract keywords
            keywords = get_jd_parser().extract_keywords(jd_text)

            # Calculate general fit
            total_custom = sum(req['weight'] for req in weighted_reqs)
            general_fit = 100 - total_custom

            return jsonify({
                "success": True,
                "requirements": requirements.model_dump(),  # Convert Pydantic model to dict
                "weighted_requirements": weighted_reqs,
                "keywords": keywords,
                "general_fit_weight": general_fit
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/search-candidates', methods=['POST'])
    def search_candidates():
        """
        Search CoreSignal for candidates matching JD requirements.

        Request:
            {
                "jd_requirements": {...},  // from /api/jd/parse
                "max_results": 100  // optional, default 100
            }

        Response:
            {
                "success": true,
                "query": {...},  // Generated ES DSL query
                "query_explanation": "...",  // Human-readable explanation
                "profiles": [...],  // List of matching profiles
                "total_found": 47,
                "csv_data": "..."  // CSV string for download
            }
        """
        try:
            data = request.json
            jd_requirements = data.get('jd_requirements')
            raw_query = data.get('query')  # Accept pre-generated query
            max_results = data.get('max_results', 100)

            if not jd_requirements and not raw_query:
                return jsonify({
                    "success": False,
                    "error": "No JD requirements or query provided"
                }), 400

            # Generate Elasticsearch DSL query OR use provided query
            if raw_query:
                query = raw_query
                query_explanation = "Using pre-generated query from LLM"
            else:
                query = get_query_builder().build_query(jd_requirements)
                query_explanation = get_query_builder().explain_query(query)

            # Execute CoreSignal search
            coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
            if not coresignal_api_key:
                return jsonify({
                    "success": False,
                    "error": "CORESIGNAL_API_KEY not configured"
                }), 500

            search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
            headers = {
                "accept": "application/json",
                "apikey": coresignal_api_key,
                "Content-Type": "application/json"
            }

            profiles = []
            pages_to_fetch = min(5, (max_results // 20) + 1)  # Preview API limited to pages 1-5

            logger.info(f"Fetching {pages_to_fetch} pages to get ~{max_results} candidates...")

            for page in range(1, pages_to_fetch + 1):
                # Add delay between page requests to avoid rate limiting
                # Each request takes ~10s, so 2s delay gives CoreSignal's rate limiter breathing room
                if page > 1:
                    time.sleep(2)  # 2s delay between pages to prevent burst rate limit violations

                logger.info(f"Fetching page {page}/{pages_to_fetch}...")

                # Use retry logic for CoreSignal API
                # Note: The preview endpoint doesn't support POST with page param
                # It uses GET with query in URL, so we need to adjust
                success, result, error_msg = make_coresignal_request_with_retry(
                    f"{search_url}?page={page}",
                    query,
                    headers,
                    max_retries=2,
                    timeout=30
                )

                if not success:
                    logger.error(f"Failed to fetch page {page}: {error_msg}")
                    return jsonify({
                        "success": False,
                        "error": error_msg
                    }), 500

                # Preview endpoint returns list of full profile objects
                if isinstance(result, list):
                    profiles.extend(result)
                else:
                    profiles.extend(result.get("hits", []))

                logger.info(f"Page {page} returned {len(result) if isinstance(result, list) else len(result.get('hits', []))} profiles (total: {len(profiles)})")

                # Stop if we've reached max results
                if len(profiles) >= max_results:
                    profiles = profiles[:max_results]
                    logger.info(f"Reached target of {max_results} candidates, stopping pagination")
                    break

            # Generate CSV data
            csv_data = generate_csv_from_profiles(profiles)

            return jsonify({
                "success": True,
                "query": query,
                "query_explanation": query_explanation,
                "profiles": profiles,
                "total_found": len(profiles),
                "csv_data": csv_data
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/compare-llm-queries', methods=['POST'])
    def compare_llm_queries():
        """
        Compare queries generated by Claude Opus 4.1, GPT-5, and Gemini 2.5 Pro,
        then preview candidates from each query.

        Request:
            {
                "jd_requirements": {...},  // from /api/jd/parse
                "preview_limit": 10  // Number of candidates to preview per query
            }

        Response:
            {
                "success": true,
                "comparisons": [
                    {
                        "model": "claude-opus-4-1",
                        "query": {...},
                        "reasoning": "...",
                        "preview_profiles": [...],  // First N matching profiles
                        "total_found": 47,
                        "error": null
                    },
                    {
                        "model": "gpt-5",
                        "query": {...},
                        "reasoning": "...",
                        "preview_profiles": [...],
                        "total_found": 52,
                        "error": null
                    },
                    {
                        "model": "gemini-2.5-pro-latest",
                        "query": {...},
                        "reasoning": "...",
                        "preview_profiles": [...],
                        "total_found": 38,
                        "error": null
                    }
                ]
            }
        """
        try:
            data = request.json
            jd_requirements = data.get('jd_requirements')
            preview_limit = data.get('preview_limit', 10)

            if not jd_requirements:
                return jsonify({
                    "success": False,
                    "error": "No JD requirements provided"
                }), 400

            # Generate queries from all three LLMs (expects dict)
            llm_results = get_multi_llm_generator().compare_all(jd_requirements)

            # Get CoreSignal API key
            coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
            if not coresignal_api_key:
                return jsonify({
                    "success": False,
                    "error": "CORESIGNAL_API_KEY not configured"
                }), 500

            search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl"
            headers = {
                "accept": "application/json",
                "apikey": coresignal_api_key,
                "Content-Type": "application/json"
            }

            # Preview candidates for each query
            comparisons = []
            for llm_result in llm_results:
                if "error" in llm_result:
                    comparisons.append({
                        "model": llm_result.get("model"),
                        "error": llm_result["error"],
                        "query": None,
                        "reasoning": None,
                        "preview_profiles": [],
                        "total_found": 0
                    })
                    continue

                query = llm_result["query"]
                model = llm_result["model"]
                reasoning = llm_result["reasoning"]

                try:
                    # Execute search with this query (only fetch first page for preview)
                    response = requests.post(
                        search_url,
                        json=query,
                        headers=headers,
                        params={"page": 1}
                    )

                    if response.status_code != 200:
                        comparisons.append({
                            "model": model,
                            "query": query,
                            "reasoning": reasoning,
                            "error": f"CoreSignal API error: {response.status_code}",
                            "preview_profiles": [],
                            "total_found": 0
                        })
                        continue

                    result = response.json()
                    # Handle case where result might be a list instead of dict
                    if isinstance(result, dict):
                        all_profiles = result.get("hits", [])
                    elif isinstance(result, list):
                        all_profiles = result
                    else:
                        all_profiles = []
                    preview_profiles = all_profiles[:preview_limit]

                    # Simplify preview profiles (only essential fields)
                    simplified_previews = []
                    for profile in preview_profiles:
                        simplified_previews.append({
                            "full_name": profile.get("full_name", ""),
                            "headline": profile.get("generated_headline") or profile.get("headline") or "",
                            "linkedin_url": profile.get("linkedin_url", ""),
                            "location": profile.get("location_full", ""),
                            "current_title": profile.get("active_experience_title", ""),
                            "total_experience_months": profile.get("total_experience_duration_months", 0)
                        })

                    comparisons.append({
                        "model": model,
                        "query": query,
                        "reasoning": reasoning,
                        "preview_profiles": simplified_previews,
                        "total_found": len(all_profiles),
                        "error": None
                    })

                except Exception as e:
                    comparisons.append({
                        "model": model,
                        "query": query,
                        "reasoning": reasoning,
                        "error": str(e),
                        "preview_profiles": [],
                        "total_found": 0
                    })

            return jsonify({
                "success": True,
                "comparisons": comparisons
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/compare-llm-queries-stream', methods=['POST'])
    def compare_llm_queries_stream():
        """
        Stream query generation results from Claude, GPT, and Gemini SEQUENTIALLY.

        Uses Server-Sent Events (SSE) to stream results as they complete.
        SEQUENTIAL execution (max_workers=1) to avoid CoreSignal 503 rate limit errors.
        Total time: ~15-20s (sum of all 3 LLMs), but provides granular progress updates.

        Request:
            {
                "jd_requirements": {...},  // from /api/jd/parse
                "preview_limit": 10  // Number of candidates to preview per query
            }

        Response: Server-Sent Events stream
            event: progress
            data: {"status": "starting", "message": "Generating queries sequentially..."}

            event: progress
            data: {"model": "Claude Haiku 4.5", "step": "generating_query", "message": "Generating query..."}

            event: progress
            data: {"model": "Claude Haiku 4.5", "step": "searching_coresignal", "message": "Searching CoreSignal..."}

            event: result
            data: {"model": "Claude Haiku 4.5", "query": {...}, "thinking": "...", "total_found": 47, ...}

            event: complete
            data: {"status": "complete", "total_models": 3}
        """
        from flask import Response
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import json
        from queue import Queue

        # Parse request data BEFORE creating generator (Flask request context)
        data = request.json
        jd_requirements = data.get('jd_requirements')
        preview_limit = data.get('preview_limit', 10)

        # Create progress queue for worker-to-generator communication
        progress_queue = Queue()

        def generate():
            try:
                if not jd_requirements:
                    yield f"event: error\ndata: {json.dumps({'error': 'No JD requirements provided'})}\n\n"
                    return

                # Send starting event
                yield f"event: progress\ndata: {json.dumps({'status': 'starting', 'message': 'Generating queries sequentially to avoid rate limits...'})}\n\n"

                # Get CoreSignal API key
                coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
                if not coresignal_api_key:
                    yield f"event: error\ndata: {json.dumps({'error': 'CORESIGNAL_API_KEY not configured'})}\n\n"
                    return

                search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
                headers = {
                    "accept": "application/json",
                    "apikey": coresignal_api_key,
                    "Content-Type": "application/json"
                }

                # Define worker function for sequential execution
                def process_llm(llm_name):
                    """Generate query and preview candidates for one LLM"""
                    start_time = time.time()

                    # Get model display name for progress messages
                    model_names = {"claude": "Claude Haiku 4.5", "gpt": "GPT-4o", "gemini": "Gemini 2.0 Flash"}
                    display_name = model_names.get(llm_name, llm_name)

                    logger.info(f"[{llm_name.upper()}] Starting query generation...")

                    # Send progress: Starting query generation
                    progress_queue.put({
                        "event": "progress",
                        "data": {
                            "model": display_name,
                            "step": "generating_query",
                            "message": f"Generating query with {display_name}..."
                        }
                    })

                    try:
                        # Generate query
                        if llm_name == "claude":
                            llm_result = get_multi_llm_generator().generate_with_claude(jd_requirements)
                        elif llm_name == "gpt":
                            llm_result = get_multi_llm_generator().generate_with_gpt5(jd_requirements)
                        elif llm_name == "gemini":
                            llm_result = get_multi_llm_generator().generate_with_gemini(jd_requirements)
                        else:
                            logger.error(f"[{llm_name.upper()}] Unknown LLM name")
                            return {"model": llm_name, "error": "Unknown LLM"}

                        generation_time = time.time() - start_time
                        logger.info(f"[{llm_name.upper()}] Query generated in {generation_time:.1f}s")

                        if "error" in llm_result:
                            logger.error(f"[{llm_name.upper()}] LLM generation error: {llm_result['error']}")
                            return llm_result

                        # Log query structure for debugging
                        query = llm_result.get("query")
                        must_count = len(query.get("query", {}).get("bool", {}).get("must", []))
                        should_count = len(query.get("query", {}).get("bool", {}).get("should", []))
                        min_match = query.get("query", {}).get("bool", {}).get("minimum_should_match", 0)
                        logger.info(f"[{llm_name.upper()}] Query structure: MUST={must_count}, SHOULD={should_count}, min_match={min_match}")

                        # Log full query for debugging (check for problematic fields)
                        import json
                        query_str = json.dumps(query, indent=2)
                        if 'total_experience_duration_months' in query_str:
                            logger.warning(f"[{llm_name.upper()}] ⚠️  QUERY CONTAINS total_experience_duration_months!")
                        logger.debug(f"[{llm_name.upper()}] Full query:\n{query_str}")

                        # Preview candidates with generated query
                        # Note: CoreSignal multi_source API returns 1000 results by default
                        # The 'size' parameter is NOT supported (causes 422 error)
                        # We slice the results after receiving them
                        payload = {
                            "query": query.get("query")  # Extract nested query object
                        }

                        # Send progress: Starting CoreSignal search
                        progress_queue.put({
                            "event": "progress",
                            "data": {
                                "model": display_name,
                                "step": "searching_coresignal",
                                "message": f"Searching CoreSignal for candidates..."
                            }
                        })

                        logger.info(f"[{llm_name.upper()}] Executing CoreSignal search...")
                        success, profiles, error_msg = make_coresignal_request_with_retry(
                            search_url, payload, headers, max_retries=2, timeout=30
                        )

                        search_time = time.time() - start_time - generation_time
                        total_time = time.time() - start_time

                        if success:
                            logger.info(f"[{llm_name.upper()}] Found {len(profiles)} candidates in {search_time:.1f}s (total {total_time:.1f}s)")
                            return {
                                "model": llm_result.get("model"),
                                "query": query,
                                "thinking": llm_result.get("thinking"),  # Include CoT reasoning
                                "reasoning": llm_result.get("reasoning"),
                                "preview_profiles": profiles[:preview_limit],
                                "total_found": len(profiles),
                                "error": None
                            }
                        else:
                            logger.error(f"[{llm_name.upper()}] CoreSignal search failed: {error_msg}")
                            return {
                                "model": llm_result.get("model"),
                                "query": query,
                                "thinking": llm_result.get("thinking"),
                                "reasoning": llm_result.get("reasoning"),
                                "error": error_msg,
                                "preview_profiles": [],
                                "total_found": 0
                            }

                    except Exception as e:
                        logger.exception(f"[{llm_name.upper()}] Unexpected error: {str(e)}")
                        return {
                            "model": llm_name,
                            "error": str(e),
                            "query": None,
                            "thinking": None,
                            "preview_profiles": [],
                            "total_found": 0
                        }

                # Run all three LLMs with TRUE SEQUENTIAL execution to avoid rate limits
                # max_workers=1 forces one LLM to complete before next starts
                # CoreSignal rate limit: 18 req/s (all employee search endpoints share this quota)
                logger.info("Starting TRULY SEQUENTIAL LLM execution (max_workers=1 - one at a time)...")
                with ThreadPoolExecutor(max_workers=1) as executor:
                    futures = {}

                    # Submit all tasks - executor will run them ONE AT A TIME
                    llm_order = ["claude", "gpt", "gemini"]
                    for llm_name in llm_order:
                        logger.info(f"Submitting {llm_name} task to queue (will execute when previous completes)")
                        futures[executor.submit(process_llm, llm_name)] = llm_name

                    completed_count = 0
                    for future in as_completed(futures):
                        llm_name = futures[future]

                        # Drain progress queue and yield all pending progress events
                        while not progress_queue.empty():
                            progress_msg = progress_queue.get()
                            yield f"event: {progress_msg['event']}\ndata: {json.dumps(progress_msg['data'])}\n\n"

                        result = future.result()
                        completed_count += 1

                        # Stream result as it completes
                        yield f"event: result\ndata: {json.dumps(result)}\n\n"

                        # Send progress update
                        yield f"event: progress\ndata: {json.dumps({'status': 'processing', 'completed': completed_count, 'total': 3})}\n\n"

                # Send completion event
                yield f"event: complete\ndata: {json.dumps({'status': 'complete', 'total_models': 3})}\n\n"

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    @app.route('/api/jd/generate-query-claude', methods=['POST'])
    def generate_query_claude():
        """
        Generate CoreSignal query using Claude Sonnet 4 only.

        Request:
            {
                "jd_requirements": {...},
                "preview_limit": 10
            }

        Response:
            {
                "success": true,
                "model": "Claude Sonnet 4",
                "query": {...},
                "reasoning": "...",
                "preview_profiles": [...],
                "total_found": 47,
                "error": null
            }
        """
        try:
            data = request.json
            jd_requirements = data.get('jd_requirements')
            preview_limit = data.get('preview_limit', 10)

            if not jd_requirements:
                return jsonify({
                    "success": False,
                    "error": "No JD requirements provided"
                }), 400

            # Generate query with Claude
            llm_result = get_multi_llm_generator().generate_with_claude(jd_requirements)

            # Check if LLM generation failed
            if "error" in llm_result:
                return jsonify({
                    "success": True,
                    "model": llm_result.get("model"),
                    "query": None,
                    "reasoning": None,
                    "error": llm_result["error"],
                    "preview_profiles": [],
                    "total_found": 0
                })

            # Get CoreSignal API key
            coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
            if not coresignal_api_key:
                return jsonify({
                    "success": False,
                    "error": "CORESIGNAL_API_KEY not configured"
                }), 500

            query = llm_result["query"]
            model = llm_result["model"]
            reasoning = llm_result["reasoning"]

            # Execute CoreSignal preview search
            try:
                search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
                headers = {
                    "accept": "application/json",
                    "apikey": coresignal_api_key,
                    "Content-Type": "application/json"
                }

                # LOG: Before CoreSignal API call
                debug_log.coresignal_api(
                    f"Searching CoreSignal with {model} query",
                    query=query,
                    page=1
                )

                response = requests.post(
                    search_url,
                    json=query,
                    headers=headers,
                    params={"page": 1}
                )

                if response.status_code != 200:
                    # LOG: CoreSignal API error
                    debug_log.coresignal_api(
                        f"CoreSignal API error",
                        success=False,
                        error_status=response.status_code,
                        error_body=response.text
                    )
                    return jsonify({
                        "success": True,
                        "model": model,
                        "query": query,
                        "reasoning": reasoning,
                        "error": f"CoreSignal API error: {response.status_code}",
                        "preview_profiles": [],
                        "total_found": 0
                    })

                result = response.json()
                # Handle case where result might be a list instead of dict
                if isinstance(result, dict):
                    all_profiles = result.get("hits", [])
                elif isinstance(result, list):
                    all_profiles = result
                else:
                    all_profiles = []
                preview_profiles = all_profiles[:preview_limit]

                # LOG: After CoreSignal success
                first_profile = all_profiles[0] if len(all_profiles) > 0 else None
                debug_log.coresignal_api(
                    f"CoreSignal search successful",
                    success=True,
                    total_found=len(all_profiles),
                    profiles_count=len(preview_profiles),
                    first_profile=first_profile
                )

                # Simplify preview profiles
                simplified_previews = []
                for profile in preview_profiles:
                    simplified_previews.append({
                        "full_name": profile.get("full_name", ""),
                        "headline": profile.get("generated_headline") or profile.get("headline") or "",
                        "linkedin_url": profile.get("linkedin_url", ""),
                        "location": profile.get("location_full", ""),
                        "current_title": profile.get("active_experience_title", ""),
                        "total_experience_months": profile.get("total_experience_duration_months", 0)
                    })

                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "preview_profiles": simplified_previews,
                    "total_found": len(all_profiles),
                    "error": None
                })

            except Exception as e:
                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "error": str(e),
                    "preview_profiles": [],
                    "total_found": 0
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/generate-query-gpt', methods=['POST'])
    def generate_query_gpt():
        """
        Generate CoreSignal query using GPT-4o only.

        Request:
            {
                "jd_requirements": {...},
                "preview_limit": 10
            }

        Response:
            {
                "success": true,
                "model": "GPT-4o",
                "query": {...},
                "reasoning": "...",
                "preview_profiles": [...],
                "total_found": 52,
                "error": null
            }
        """
        try:
            data = request.json
            jd_requirements = data.get('jd_requirements')
            preview_limit = data.get('preview_limit', 10)

            if not jd_requirements:
                return jsonify({
                    "success": False,
                    "error": "No JD requirements provided"
                }), 400

            # Generate query with GPT
            llm_result = get_multi_llm_generator().generate_with_gpt5(jd_requirements)

            # Check if LLM generation failed
            if "error" in llm_result:
                return jsonify({
                    "success": True,
                    "model": llm_result.get("model"),
                    "query": None,
                    "reasoning": None,
                    "error": llm_result["error"],
                    "preview_profiles": [],
                    "total_found": 0
                })

            # Get CoreSignal API key
            coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
            if not coresignal_api_key:
                return jsonify({
                    "success": False,
                    "error": "CORESIGNAL_API_KEY not configured"
                }), 500

            query = llm_result["query"]
            model = llm_result["model"]
            reasoning = llm_result["reasoning"]

            # Execute CoreSignal preview search
            try:
                search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
                headers = {
                    "accept": "application/json",
                    "apikey": coresignal_api_key,
                    "Content-Type": "application/json"
                }

                response = requests.post(
                    search_url,
                    json=query,
                    headers=headers,
                    params={"page": 1}
                )

                if response.status_code != 200:
                    return jsonify({
                        "success": True,
                        "model": model,
                        "query": query,
                        "reasoning": reasoning,
                        "error": f"CoreSignal API error: {response.status_code}",
                        "preview_profiles": [],
                        "total_found": 0
                    })

                result = response.json()
                # Handle case where result might be a list instead of dict
                if isinstance(result, dict):
                    all_profiles = result.get("hits", [])
                elif isinstance(result, list):
                    all_profiles = result
                else:
                    all_profiles = []
                preview_profiles = all_profiles[:preview_limit]

                # Simplify preview profiles
                simplified_previews = []
                for profile in preview_profiles:
                    simplified_previews.append({
                        "full_name": profile.get("full_name", ""),
                        "headline": profile.get("generated_headline") or profile.get("headline") or "",
                        "linkedin_url": profile.get("linkedin_url", ""),
                        "location": profile.get("location_full", ""),
                        "current_title": profile.get("active_experience_title", ""),
                        "total_experience_months": profile.get("total_experience_duration_months", 0)
                    })

                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "preview_profiles": simplified_previews,
                    "total_found": len(all_profiles),
                    "error": None
                })

            except Exception as e:
                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "error": str(e),
                    "preview_profiles": [],
                    "total_found": 0
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/generate-query-gemini', methods=['POST'])
    def generate_query_gemini():
        """
        Generate CoreSignal query using Gemini 2.0 Flash only.

        Request:
            {
                "jd_requirements": {...},
                "preview_limit": 10
            }

        Response:
            {
                "success": true,
                "model": "Gemini 2.0 Flash",
                "query": {...},
                "reasoning": "...",
                "preview_profiles": [...],
                "total_found": 38,
                "error": null
            }
        """
        try:
            data = request.json
            jd_requirements = data.get('jd_requirements')
            preview_limit = data.get('preview_limit', 10)

            if not jd_requirements:
                return jsonify({
                    "success": False,
                    "error": "No JD requirements provided"
                }), 400

            # Generate query with Gemini
            llm_result = get_multi_llm_generator().generate_with_gemini(jd_requirements)

            # Check if LLM generation failed
            if "error" in llm_result:
                return jsonify({
                    "success": True,
                    "model": llm_result.get("model"),
                    "query": None,
                    "reasoning": None,
                    "error": llm_result["error"],
                    "preview_profiles": [],
                    "total_found": 0
                })

            # Get CoreSignal API key
            coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
            if not coresignal_api_key:
                return jsonify({
                    "success": False,
                    "error": "CORESIGNAL_API_KEY not configured"
                }), 500

            query = llm_result["query"]
            model = llm_result["model"]
            reasoning = llm_result["reasoning"]

            # Execute CoreSignal preview search
            try:
                search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
                headers = {
                    "accept": "application/json",
                    "apikey": coresignal_api_key,
                    "Content-Type": "application/json"
                }

                response = requests.post(
                    search_url,
                    json=query,
                    headers=headers,
                    params={"page": 1}
                )

                if response.status_code != 200:
                    return jsonify({
                        "success": True,
                        "model": model,
                        "query": query,
                        "reasoning": reasoning,
                        "error": f"CoreSignal API error: {response.status_code}",
                        "preview_profiles": [],
                        "total_found": 0
                    })

                result = response.json()
                # Handle case where result might be a list instead of dict
                if isinstance(result, dict):
                    all_profiles = result.get("hits", [])
                elif isinstance(result, list):
                    all_profiles = result
                else:
                    all_profiles = []
                preview_profiles = all_profiles[:preview_limit]

                # Simplify preview profiles
                simplified_previews = []
                for profile in preview_profiles:
                    simplified_previews.append({
                        "full_name": profile.get("full_name", ""),
                        "headline": profile.get("generated_headline") or profile.get("headline") or "",
                        "linkedin_url": profile.get("linkedin_url", ""),
                        "location": profile.get("location_full", ""),
                        "current_title": profile.get("active_experience_title", ""),
                        "total_experience_months": profile.get("total_experience_duration_months", 0)
                    })

                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "preview_profiles": simplified_previews,
                    "total_found": len(all_profiles),
                    "error": None
                })

            except Exception as e:
                return jsonify({
                    "success": True,
                    "model": model,
                    "query": query,
                    "reasoning": reasoning,
                    "error": str(e),
                    "preview_profiles": [],
                    "total_found": 0
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/jd/validate-transformation', methods=['POST'])
    def validate_transformation():
        """
        Validate JD → Research payload transformation using GPT-4o with CoT.

        Uses Chain-of-Thought prompting with few-shot examples to ensure
        data integrity between JD parsing and company research payload.

        Request:
            {
                "jd_text": "full job description text...",
                "parsed_requirements": {...},  // from /api/jd/parse
                "research_payload": {...}      // to /research-companies
            }

        Response:
            {
                "success": true,
                "valid": true/false,
                "reasoning": "Step-by-step CoT analysis...",
                "issues": ["issue1", "issue2"],
                "recommendation": "Fix X, Y, Z"
            }
        """
        try:
            from .validation_agent import JDValidationAgent

            data = request.json
            jd_text = data.get('jd_text', '')
            parsed_requirements = data.get('parsed_requirements', {})
            research_payload = data.get('research_payload', {})

            if not jd_text:
                return jsonify({
                    "success": False,
                    "error": "jd_text is required"
                }), 400

            if not parsed_requirements:
                return jsonify({
                    "success": False,
                    "error": "parsed_requirements is required"
                }), 400

            if not research_payload:
                return jsonify({
                    "success": False,
                    "error": "research_payload is required"
                }), 400

            # Run validation
            agent = JDValidationAgent()
            result = agent.validate_transformation(
                jd_text,
                parsed_requirements,
                research_payload
            )

            return jsonify({
                "success": True,
                **result  # Includes: valid, reasoning, issues, recommendation
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


def generate_csv_from_profiles(profiles):
    """
    Generate CSV data from CoreSignal profile results.

    Args:
        profiles: List of CoreSignal employee profiles

    Returns:
        CSV string with columns: Full Name, Headline, LinkedIn URL, Location, Current Company
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Full Name",
        "Headline",
        "LinkedIn URL",
        "Location",
        "Current Company",
        "Current Title",
        "Total Experience (Years)"
    ])

    # Write data rows
    for profile in profiles:
        full_name = profile.get("full_name", "")
        headline = profile.get("generated_headline") or profile.get("headline") or ""
        # Try multiple field names for LinkedIn URL
        linkedin_url = profile.get("linkedin_url") or profile.get("professional_network_url", "")
        location = profile.get("location") or profile.get("location_full", "")
        # Use company_name directly from preview endpoint
        current_company = profile.get("company_name", "")
        current_title = profile.get("current_title") or profile.get("active_experience_title", "")

        writer.writerow([
            full_name,
            headline,
            linkedin_url,
            location,
            current_company,
            current_title,
            ""  # No experience data in preview endpoint
        ])

    return output.getvalue()
