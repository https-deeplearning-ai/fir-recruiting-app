"""
API Endpoints for JD Analyzer

Flask routes for integrating JD analysis into the application.
Add these to your main app.py file.
"""

from flask import request, jsonify
from .jd_parser import JDParser
from .weight_generator import WeightGenerator
from .shortlist_analyzer import ShortlistAnalyzer
from .query_builder import JDToQueryBuilder
from .llm_query_generator import MultiLLMQueryGenerator
from .models import JDRequirements
from .debug_logger import debug_log
from pydantic import ValidationError
import os
import tempfile
import requests
import csv
from io import StringIO

# Initialize services
jd_parser = JDParser()
weight_generator = WeightGenerator()
query_builder = JDToQueryBuilder()
multi_llm_generator = MultiLLMQueryGenerator()


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

            requirements = jd_parser.parse(jd_text)

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
                jd_requirements = jd_parser.parse(jd_text)
            else:
                return jsonify({
                    "success": False,
                    "error": "Must provide either jd_text or jd_requirements"
                }), 400

            # Generate weighted requirements
            weighted_reqs = weight_generator.generate_weighted_requirements(
                jd_requirements,
                num_requirements
            )

            # Calculate general fit weight
            total_custom = sum(req['weight'] for req in weighted_reqs)
            general_fit = 100 - total_custom

            # Generate explanation
            explanation = weight_generator.explain_weights(weighted_reqs)

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
                    jd_requirements = jd_parser.parse(jd_text)
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

            keywords = jd_parser.extract_keywords(jd_text)

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
            requirements = jd_parser.parse(jd_text)

            # Generate weights
            weighted_reqs = weight_generator.generate_weighted_requirements(
                requirements,
                num_requirements
            )

            # Extract keywords
            keywords = jd_parser.extract_keywords(jd_text)

            # Calculate general fit
            total_custom = sum(req['weight'] for req in weighted_reqs)
            general_fit = 100 - total_custom

            return jsonify({
                "success": True,
                "requirements": requirements,
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
                query = query_builder.build_query(jd_requirements)
                query_explanation = query_builder.explain_query(query)

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

            for page in range(1, pages_to_fetch + 1):
                response = requests.post(
                    search_url,
                    json=query,
                    headers=headers,
                    params={"page": page}
                )

                if response.status_code != 200:
                    return jsonify({
                        "success": False,
                        "error": f"CoreSignal API error: {response.status_code}"
                    }), 500

                result = response.json()
                # Preview endpoint returns list of full profile objects
                if isinstance(result, list):
                    profiles.extend(result)
                else:
                    profiles.extend(result.get("hits", []))

                # Stop if we've reached max results
                if len(profiles) >= max_results:
                    profiles = profiles[:max_results]
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
            llm_results = multi_llm_generator.compare_all(jd_requirements)

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
            llm_result = multi_llm_generator.generate_with_claude(jd_requirements)

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
            llm_result = multi_llm_generator.generate_with_gpt5(jd_requirements)

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
            llm_result = multi_llm_generator.generate_with_gemini(jd_requirements)

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
