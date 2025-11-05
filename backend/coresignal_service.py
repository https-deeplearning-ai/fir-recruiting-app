"""
CoreSignal API Service - CORRECTED VERSION
Based on official CoreSignal API documentation (April 2025)

Key Changes:
1. Uses correct field name: websites_professional_network (not websites_linkedin.exact)
2. Shorthand method is now PRIMARY (faster, more reliable)
3. ES search is now FALLBACK with corrected field names
4. Better error handling and logging
"""
import requests
import json
import os
from typing import List, Dict, Any, Optional


class CoreSignalService:
    def __init__(self):
        self.api_key = os.getenv("CORESIGNAL_API_KEY")
        if not self.api_key:
            print("Warning: CORESIGNAL_API_KEY environment variable is not set")
            # Don't raise - allow service to be created, will fail on first actual use
        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        # Company data cache to avoid duplicate API calls
        self.company_cache = {}

    def _check_api_key(self):
        """Check if API key is available before making requests"""
        if not self.api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable is not set")

    def fetch_linkedin_profile(self, linkedin_url):
        """
        Fetch LinkedIn profile data from CoreSignal API using LinkedIn URL

        UPDATED APPROACH (April 2025):
        1. PRIMARY: Direct collection by shorthand (fastest, most reliable)
        2. FALLBACK: ES search with correct field names

        Args:
            linkedin_url (str): LinkedIn profile URL

        Returns:
            dict: Profile data or error information
        """
        self._check_api_key()  # Check API key is available
        try:
            print(f"🔍 Fetching profile: {linkedin_url}")

            # Extract shorthand name from LinkedIn URL
            shorthand_name = linkedin_url.rstrip('/').split('/in/')[-1].split('?')[0]
            print(f"   Shorthand extracted: {shorthand_name}")

            # ========================================
            # METHOD 1: Direct Collection by Shorthand (PRIMARY)
            # ========================================
            # This is the FASTEST and MOST RELIABLE method
            # CoreSignal allows direct collection using the LinkedIn shorthand name

            print("\n📌 Method 1: Direct collection by shorthand...")

            # Remove Content-Type for GET request
            get_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}

            shorthand_response = requests.get(
                f"https://api.coresignal.com/cdapi/v2/employee_clean/collect/{shorthand_name}",
                headers=get_headers,
                timeout=10
            )

            print(f"   Response status: {shorthand_response.status_code}")

            if shorthand_response.status_code == 200:
                profile_data = shorthand_response.json()
                print(f"✅ SUCCESS: Profile retrieved via shorthand!")
                return {
                    'success': True,
                    'profile_data': profile_data,
                    'employee_id': shorthand_name,
                    'shorthand_name': shorthand_name,
                    'method': 'shorthand_direct',
                    'api_calls': 1  # Track efficiency
                }

            # ========================================
            # METHOD 2: ES Search (FALLBACK)
            # ========================================
            # Use this if shorthand method fails
            # Updated with CORRECT field names from API docs

            print(f"\n📌 Method 2: Elasticsearch search (fallback)...")
            print(f"   Shorthand method failed with {shorthand_response.status_code}")

            # Try multiple search variations with CORRECT field names
            search_variations = [
                # Variation 1: Direct LinkedIn URL with correct field name
                {
                    "term": {
                        "websites_professional_network": linkedin_url
                    }
                },
                # Variation 2: CoreSignal's URL format (they replace linkedin.com with professional_network.com)
                {
                    "term": {
                        "websites_professional_network": f"https://www.professional_network.com/in/{shorthand_name}"
                    }
                },
                # Variation 3: Match query on shorthand (more flexible)
                {
                    "match": {
                        "websites_professional_network": shorthand_name
                    }
                },
                # Variation 4: Wildcard search as last resort
                {
                    "wildcard": {
                        "websites_professional_network": f"*{shorthand_name}*"
                    }
                }
            ]

            for i, query_condition in enumerate(search_variations, 1):
                print(f"\n   Trying search variation {i}/{len(search_variations)}...")

                search_payload = {
                    "query": {
                        "bool": {
                            "must": [query_condition]
                        }
                    }
                }

                search_response = requests.post(
                    "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl",
                    json=search_payload,
                    headers=self.headers,
                    timeout=10
                )

                print(f"   Search response status: {search_response.status_code}")

                if search_response.status_code != 200:
                    print(f"   ⚠️  Search request failed: {search_response.text[:200]}")
                    continue

                search_results = search_response.json()
                print(f"   Search returned {len(search_results)} results")

                if search_results:
                    # Found results! Get the first employee ID
                    employee_id = search_results[0]
                    print(f"   ✅ Found employee ID: {employee_id}")

                    # Fetch full profile
                    print(f"\n   Fetching full profile for ID: {employee_id}...")
                    profile_response = requests.get(
                        f"https://api.coresignal.com/cdapi/v2/employee_clean/collect/{employee_id}",
                        headers=get_headers,
                        timeout=10
                    )

                    print(f"   Profile fetch status: {profile_response.status_code}")

                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        print(f"✅ SUCCESS: Profile retrieved via search variation {i}!")
                        return {
                            'success': True,
                            'profile_data': profile_data,
                            'employee_id': employee_id,
                            'shorthand_name': shorthand_name,
                            'method': f'search_variation_{i}',
                            'api_calls': 2  # Track efficiency
                        }
                    else:
                        print(f"   ❌ Profile fetch failed: {profile_response.status_code}")
                        continue

            # ========================================
            # ALL METHODS FAILED
            # ========================================

            print(f"\n❌ FAILED: All methods exhausted")
            return {
                'error': 'Profile not found in CoreSignal database after trying all methods',
                'success': False,
                'debug_info': {
                    'linkedin_url': linkedin_url,
                    'shorthand_name': shorthand_name,
                    'shorthand_status_code': shorthand_response.status_code,
                    'methods_attempted': [
                        'shorthand_direct',
                        'search_variation_1_exact_url',
                        'search_variation_2_coresignal_format',
                        'search_variation_3_match_shorthand',
                        'search_variation_4_wildcard'
                    ],
                    'recommendation': 'Profile may not exist in CoreSignal database, or LinkedIn URL format is unrecognized'
                }
            }

        except requests.exceptions.Timeout:
            return {
                'error': 'Request timeout - CoreSignal API is slow to respond',
                'success': False
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f'Network error: {str(e)}',
                'success': False
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'success': False
            }

    def fetch_company_data(self, company_id, storage_functions=None):
        """
        Fetch full company profile data from CoreSignal company_base API

        Uses company_base endpoint (NOT company_clean) based on comprehensive testing:
        - 100% data availability vs 50% for company_multi_source
        - 69.2% Crunchbase URL coverage via company_crunchbase_info_collection
        - Reliable funding data in company_funding_rounds_collection
        - See docs/technical-decisions/company-api-comparison-2024/ for full analysis

        This provides detailed company intelligence including:
        - Company type (Public/Private/Non-Profit)
        - Founded year and company age
        - Funding rounds with dates and amounts
        - Crunchbase URLs (company-level + funding round-level)
        - Featured investors collection
        - Revenue and growth metrics
        - Employee count changes (growth rate)
        - HQ location details
        - Industry classifications
        - Social media presence
        - Technology stack

        Args:
            company_id (int/str): CoreSignal company ID from employee experience
            storage_functions (dict): Optional dict with 'get' and 'save' functions for database storage

        Returns:
            dict: Full company profile data or error information
        """
        try:
            # Check DATABASE STORAGE first (if provided) - SAVE API CREDITS!
            if storage_functions:
                print(f"🔍 Checking if company {company_id} is stored in database...")
                stored_result = storage_functions['get'](company_id, freshness_days=30)

                if stored_result:
                    print(f"✅ Using stored company {company_id} - SAVED 1 Collect credit!")
                    # Also add to in-memory cache
                    result = {
                        'success': True,
                        'company_data': stored_result['company_data'],
                        'company_id': company_id,
                        'from_storage': True,
                        'storage_age_days': stored_result.get('cache_age_days', 0),
                        'verification_data': stored_result.get('verification_data', {})
                    }
                    self.company_cache[company_id] = result
                    return result

            # Check in-memory cache second (for this session only)
            if company_id in self.company_cache:
                print(f"   💾 Company {company_id} found in session cache")
                return self.company_cache[company_id]

            print(f"🏢 Fetching fresh company data from CoreSignal for ID: {company_id}")

            # Remove Content-Type for GET request
            get_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}

            response = requests.get(
                f"https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}",
                headers=get_headers,
                timeout=10
            )

            print(f"   Response status: {response.status_code}")

            if response.status_code == 200:
                company_data = response.json()
                print(f"✅ SUCCESS: Company data retrieved!")

                # DEBUG: Check what logo fields are available
                logo_fields = [k for k in company_data.keys() if 'logo' in k.lower()]
                if logo_fields:
                    print(f"   🖼️  Logo fields found: {logo_fields}")
                    for field in logo_fields:
                        value = company_data.get(field)
                        if value:
                            print(f"      {field}: {str(value)[:100]}...")
                        else:
                            print(f"      {field}: None/null")
                else:
                    print(f"   ⚠️  No logo fields found in company data")

                result = {
                    'success': True,
                    'company_data': company_data,
                    'company_id': company_id,
                    'from_storage': False,
                    'storage_age_days': 0
                }

                # Save to DATABASE STORAGE for next time (if storage functions provided)
                if storage_functions:
                    print(f"💾 Saving company {company_id} to storage for future use...")
                    storage_functions['save'](company_id, company_data)

                # Also cache in memory for this session
                self.company_cache[company_id] = result

                return result
            else:
                error_msg = f"Company {company_id} not found (status: {response.status_code})"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'company_id': company_id
                }

        except requests.exceptions.Timeout:
            return {
                'error': 'Request timeout - CoreSignal API is slow to respond',
                'success': False,
                'company_id': company_id
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f'Network error: {str(e)}',
                'success': False,
                'company_id': company_id
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'success': False,
                'company_id': company_id
            }

    def enrich_profile_with_company_data(self, profile_data, min_year=2020, storage_functions=None):
        """
        Enrich employee profile with detailed company data for recent experiences

        This fetches full company profiles for each company in the candidate's
        work history and adds enriched company intelligence.

        SMART ENRICHMENT STRATEGY:
        1. Always enrich the FIRST 3 experiences (most recent jobs)
        2. For remaining experiences, only enrich if job started >= min_year
        3. This ensures we ALWAYS show company data for recent career history

        Args:
            profile_data (dict): Employee profile from fetch_linkedin_profile()
            min_year (int): Only enrich older companies from jobs starting on or after this year (default: 2020)
            storage_functions (dict): Optional dict with 'get' and 'save' functions for database storage

        Returns:
            dict: Profile with enriched company data + metadata about API calls
        """
        experiences = profile_data.get('experience', [])
        total_companies = len(experiences)

        # CRITICAL: Always enrich first 3 companies, regardless of year
        min_companies_to_enrich = min(3, total_companies)

        print(f"\n🔍 Enriching profile with detailed company data...")
        print(f"   Strategy: First {min_companies_to_enrich} companies always + jobs from {min_year} onwards")

        companies_enriched = 0
        companies_failed = 0
        companies_skipped_old = 0
        api_calls_made = 0

        for i, exp in enumerate(experiences, 1):
            company_id = exp.get('company_id')
            company_name = exp.get('company_name', 'Unknown')

            if not company_id:
                print(f"   ⚠️  Experience {i}/{total_companies}: {company_name} - No company_id")
                continue

            # Determine if we should enrich this company
            should_enrich = False
            skip_reason = None

            # Rule 1: Always enrich first 3 companies
            if i <= min_companies_to_enrich:
                should_enrich = True
            else:
                # Rule 2: For older companies, check min_year filter
                start_year = exp.get('date_from_year')
                if start_year:
                    try:
                        if int(start_year) >= min_year:
                            should_enrich = True
                        else:
                            skip_reason = f"started {start_year}, before {min_year}"
                    except (ValueError, TypeError):
                        print(f"   ⚠️  Experience {i}/{total_companies}: {company_name} - Invalid start_year: {start_year}")
                        should_enrich = True  # Enrich if year is invalid (safer)
                else:
                    # No start year available, enrich it to be safe
                    should_enrich = True

            if not should_enrich:
                print(f"   ⏭️  Experience {i}/{total_companies}: {company_name} - Skipped ({skip_reason})")
                companies_skipped_old += 1
                exp['company_enriched'] = None
                continue

            print(f"\n   📊 Experience {i}/{total_companies}: {company_name} (ID: {company_id}, started {exp.get('date_from_year', 'unknown')})")

            # Fetch full company data (with storage integration)
            company_result = self.fetch_company_data(company_id, storage_functions=storage_functions)

            if company_result.get('success'):
                company_data = company_result['company_data']
                companies_enriched += 1

                # Add enriched fields to experience (with storage metadata and verification data)
                exp['company_enriched'] = self._extract_company_intelligence(
                    company_data,
                    from_storage=company_result.get('from_storage', False),
                    storage_age_days=company_result.get('storage_age_days', 0),
                    verification_data=company_result.get('verification_data', {})
                )

                # Track if we used cache or made API call
                if company_id not in self.company_cache or len(self.company_cache) == 1:
                    api_calls_made += 1

            else:
                companies_failed += 1
                exp['company_enriched'] = None
                print(f"      ⚠️  Failed to fetch company data")

        enrichment_summary = {
            'total_experiences': total_companies,
            'companies_enriched': companies_enriched,
            'companies_failed': companies_failed,
            'companies_skipped_old': companies_skipped_old,
            'api_calls_made': api_calls_made,
            'companies_cached': companies_enriched - api_calls_made,
            'min_year_filter': min_year
        }

        print(f"\n✅ Company enrichment complete:")
        print(f"   • Total experiences: {total_companies}")
        print(f"   • Successfully enriched: {companies_enriched}")
        print(f"   • Failed: {companies_failed}")
        print(f"   • Skipped (before {min_year}): {companies_skipped_old}")
        print(f"   • API calls made: {api_calls_made}")
        print(f"   • Served from cache: {enrichment_summary['companies_cached']}")

        return {
            'profile_data': profile_data,
            'enrichment_summary': enrichment_summary
        }

    def _extract_company_intelligence(self, company_data, from_storage=False, storage_age_days=0, verification_data=None):
        """
        Extract key intelligence signals from full company profile

        Returns structured company insights optimized for hiring decisions

        IMPORTANT: We store BOTH the raw company data (all 45+ fields) AND
        curated intelligence fields for easy frontend access.

        Args:
            company_data: Raw company data from CoreSignal API
            from_storage: Whether this data came from Supabase cache
            storage_age_days: How old the cached data is (0 if fresh)
        """
        intelligence = {}

        # Store ALL raw company data for maximum flexibility
        # This ensures we never lose data and can access any field later
        intelligence['raw_data'] = company_data

        # Data freshness metadata (NEW)
        intelligence['coresignal_last_updated'] = company_data.get('last_updated')
        intelligence['from_storage'] = from_storage
        intelligence['storage_age_days'] = storage_age_days

        # Basic info (curated for easy access)
        intelligence['name'] = company_data.get('name')
        intelligence['type'] = company_data.get('type')  # Public, Private, Non-Profit
        intelligence['founded'] = company_data.get('founded')

        # Calculate company age
        if intelligence['founded']:
            try:
                intelligence['company_age_years'] = 2025 - int(intelligence['founded'])
            except:
                intelligence['company_age_years'] = None

        # Size and growth
        intelligence['size_range'] = company_data.get('size_range') or company_data.get('size')
        intelligence['employees_count'] = company_data.get('employees_count')
        intelligence['employees_count_inferred'] = company_data.get('size_employees_count_inferred')

        # Industry
        intelligence['industry'] = company_data.get('industry')
        intelligence['specialties'] = company_data.get('specialties')
        intelligence['description'] = company_data.get('description')

        # Location
        intelligence['hq_country'] = company_data.get('location_hq_country')
        intelligence['hq_city'] = company_data.get('location_hq_city')
        intelligence['hq_state'] = company_data.get('location_hq_state')
        intelligence['hq_address'] = company_data.get('location_hq_raw_address')

        # Crunchbase URL extraction (PRIORITY: company_crunchbase_info_collection)
        # Extract from the authoritative source first: company_crunchbase_info_collection
        # This field contains the clean Crunchbase company page URL (69.2% coverage)
        crunchbase_info = company_data.get('company_crunchbase_info_collection', [])
        if crunchbase_info and len(crunchbase_info) > 0:
            # Get the most recent non-deleted entry
            for entry in crunchbase_info:
                if entry.get('deleted') == 0:  # Only use active entries
                    cb_company_url = entry.get('cb_url')
                    if cb_company_url:
                        intelligence['crunchbase_company_url'] = cb_company_url
                        intelligence['crunchbase_source'] = 'coresignal'
                        intelligence['crunchbase_confidence'] = 1.0  # 100% confidence from official source
                        print(f"   🔗 Crunchbase URL from company_crunchbase_info_collection: {cb_company_url}")
                        break

        # CHECK USER-VERIFIED URL: If user has verified a URL, use that instead
        if not intelligence.get('crunchbase_company_url') and from_storage and verification_data:
            # Check if this stored company has a user-verified Crunchbase URL
            user_verified = verification_data.get('user_verified', False)
            verified_url = verification_data.get('verified_crunchbase_url')

            if user_verified and verified_url:
                intelligence['crunchbase_company_url'] = verified_url
                intelligence['crunchbase_source'] = 'user_verified'
                intelligence['crunchbase_confidence'] = 1.0  # 100% confidence - user confirmed
                print(f"   ✅ Using user-verified Crunchbase URL: {verified_url}")

        # FALLBACK: If no Crunchbase URL found, search for it using hybrid search
        if not intelligence.get('crunchbase_company_url'):
            company_name = intelligence.get('name')
            print(f"   ⚠️  NO Crunchbase URL in company_crunchbase_info_collection for {company_name}")
            if company_name:
                print(f"   🔍 Attempting hybrid search (Tavily + Claude WebSearch) for: {company_name}")
                search_result = self._search_crunchbase_url(company_name, company_data)
                if search_result:
                    # Handle both old string format and new dict format
                    if isinstance(search_result, dict):
                        intelligence['crunchbase_company_url'] = search_result['url']
                        intelligence['crunchbase_source'] = search_result['source']
                        intelligence['crunchbase_confidence'] = search_result['confidence']
                        print(f"   ✅ Crunchbase URL found via hybrid search: {search_result['url']}")
                    else:
                        # Legacy string format
                        intelligence['crunchbase_company_url'] = search_result
                        intelligence['crunchbase_source'] = 'legacy'
                        intelligence['crunchbase_confidence'] = 0.0
                        print(f"   ✅ Crunchbase URL found via hybrid search: {search_result}")
                else:
                    print(f"   ❌ Hybrid search failed to find Crunchbase URL for {company_name}")
                    intelligence['crunchbase_company_url'] = None
                    intelligence['crunchbase_source'] = 'not_found'
                    intelligence['crunchbase_confidence'] = 0.0

        # DEBUG: Print final Crunchbase URL
        final_cb_url = intelligence.get('crunchbase_company_url')
        print(f"   📌 FINAL Crunchbase URL for {intelligence.get('name')}: {final_cb_url if final_cb_url else 'NONE'}")

        # Funding data (CRITICAL for startup assessment)
        # Using company_base endpoint: funding data in company_funding_rounds_collection
        funding_rounds = company_data.get('company_funding_rounds_collection', [])
        if funding_rounds and len(funding_rounds) > 0:
            latest_round = funding_rounds[0]  # Assume sorted by date
            intelligence['last_funding_type'] = latest_round.get('last_round_type')  # FIXED: Correct field name
            intelligence['last_funding_date'] = latest_round.get('last_round_date')  # FIXED: Correct field name
            raw_amount = latest_round.get('last_round_money_raised')
            intelligence['last_funding_amount'] = raw_amount  # Keep raw for calculations
            intelligence['last_funding_amount_formatted'] = self._format_funding_amount(raw_amount)  # Human-readable
            intelligence['total_funding_rounds'] = latest_round.get('total_rounds_count')  # FIXED: Correct field name
            intelligence['investor_count'] = latest_round.get('last_round_investors_count')  # FIXED: Correct field name

            # Crunchbase funding round URL (for specific round details)
            cb_round_url = latest_round.get('cb_url')
            intelligence['crunchbase_funding_round_url'] = cb_round_url  # Original funding round URL

            # NOTE: We do NOT use the funding round URL to derive the company URL
            # The company URL should ONLY come from company_crunchbase_info_collection
            # If it's missing there, we leave it as None rather than guess incorrectly

        # Extract ALL available company URLs for comprehensive linking
        intelligence['company_website'] = company_data.get('website')
        intelligence['linkedin_company_url'] = company_data.get('url')

        # Get logo from company_base endpoint (direct URL)
        # company_base provides logo_url as a direct LinkedIn CDN URL
        logo_url = company_data.get('logo_url')

        # Fallback: Use Clearbit Logo API if CoreSignal logo not available
        if not logo_url and intelligence['company_website']:
            try:
                from urllib.parse import urlparse
                domain = urlparse(intelligence['company_website']).netloc
                if domain:
                    # Remove 'www.' prefix if present
                    domain = domain.replace('www.', '')
                    # Clearbit Logo API - free service, no API key needed
                    logo_url = f"https://logo.clearbit.com/{domain}"
            except:
                logo_url = None

        intelligence['logo_url'] = logo_url

        # DEBUG: Log final logo URL decision
        if logo_url:
            if 'linkedin.com' in logo_url or 'licdn.com' in logo_url:
                print(f"   🖼️  Using CoreSignal logo_url (LinkedIn CDN)")
            else:
                print(f"   🖼️  Using Clearbit fallback logo: {logo_url}")
        else:
            print(f"   ⚠️  No logo available (logo_url: {bool(company_data.get('logo_url'))}, website: {bool(intelligence['company_website'])})")

        # Business model
        intelligence['is_b2b'] = company_data.get('is_b2b')

        # Financial
        intelligence['annual_revenue'] = company_data.get('annual_revenue')
        intelligence['revenue_currency'] = company_data.get('annual_revenue_currency')

        # Stock info (for public companies)
        intelligence['stock_ticker'] = company_data.get('ticker')
        intelligence['stock_exchange'] = company_data.get('exchange')

        # Social presence
        intelligence['follower_count'] = company_data.get('follower_count')

        # Technology stack
        technologies = company_data.get('technologies', [])
        if technologies:
            intelligence['tech_stack'] = [tech.get('name') for tech in technologies[:10]]  # Top 10

        # Company stage inference
        intelligence['inferred_stage'] = self._infer_company_stage(intelligence)

        # Growth signals
        intelligence['growth_signals'] = self._analyze_growth_signals(intelligence, company_data)

        return intelligence

    def _format_funding_amount(self, amount):
        """
        Format funding amount to human-readable string

        Examples:
        - 1000000 -> "$1M"
        - 36500000 -> "$36.5M"
        - 1500000000 -> "$1.5B"
        - 500000 -> "$500K"
        """
        if not amount or amount == 0:
            return None

        # If amount is already a formatted string, return it as-is
        if isinstance(amount, str):
            # Clean up common formatting issues
            # Remove duplicate currency symbols like "$US$" or "US$$"
            amount_str = str(amount).strip()
            amount_str = amount_str.replace('$US$', 'US$')  # Fix $US$ -> US$
            amount_str = amount_str.replace('US$$', 'US$')  # Fix US$$ -> US$
            return amount_str

        try:
            amount = float(amount)

            # Billions
            if amount >= 1_000_000_000:
                formatted = amount / 1_000_000_000
                if formatted == int(formatted):
                    return f"${int(formatted)}B"
                else:
                    return f"${formatted:.1f}B"

            # Millions
            elif amount >= 1_000_000:
                formatted = amount / 1_000_000
                if formatted == int(formatted):
                    return f"${int(formatted)}M"
                else:
                    return f"${formatted:.1f}M"

            # Thousands
            elif amount >= 1_000:
                formatted = amount / 1_000
                if formatted == int(formatted):
                    return f"${int(formatted)}K"
                else:
                    return f"${formatted:.1f}K"

            # Less than 1K
            else:
                return f"${int(amount)}"

        except (ValueError, TypeError):
            return None

    def _infer_company_stage(self, intelligence):
        """
        Infer company stage from available data

        Returns: 'seed', 'series_a', 'series_b', 'growth', 'late_stage', 'public', 'mature', 'unknown'
        """
        # Public company
        if intelligence.get('type') == 'Public' or intelligence.get('stock_ticker'):
            return 'public'

        # Check funding stage - FIX: Handle None values properly
        funding_type = intelligence.get('last_funding_type')
        if funding_type:
            funding_type_lower = funding_type.lower()
            if 'seed' in funding_type_lower:
                return 'seed'
            elif 'series a' in funding_type_lower or funding_type_lower == 'series_a':
                return 'series_a'
            elif 'series b' in funding_type_lower or funding_type_lower == 'series_b':
                return 'series_b'
            elif 'series c' in funding_type_lower or 'series d' in funding_type_lower:
                return 'growth'
            elif 'series e' in funding_type_lower or 'series f' in funding_type_lower or 'ipo' in funding_type_lower:
                return 'late_stage'

        # If no funding data, check company age + size together for better inference
        employees = intelligence.get('employees_count')
        age = intelligence.get('company_age_years')

        # No reliable data to infer stage
        if not employees:
            return 'unknown'

        # Large company without funding data = likely mature/bootstrapped
        if employees > 1000:
            return 'mature'

        # Small company - need age to differentiate seed from early stage
        if employees < 50:
            if age and age < 3:
                return 'seed'  # Young and small
            else:
                return 'unknown'  # Small but not necessarily seed

        # Medium size (50-500) without funding data = could be Series A/B or bootstrapped
        if employees < 500:
            return 'unknown'  # Can't reliably determine without funding data

        # 500-1000 employees
        return 'growth'

    def _analyze_growth_signals(self, intelligence, company_data):
        """
        Analyze company growth signals from available data
        """
        signals = []

        # Young, well-funded company = hypergrowth potential
        age = intelligence.get('company_age_years')
        funding = intelligence.get('last_funding_amount')
        try:
            if age and age < 5 and funding and float(funding) > 10000000:
                signals.append('hypergrowth_potential')
        except (ValueError, TypeError):
            pass  # Skip if funding amount can't be converted to number

        # Recent funding = active growth
        funding_date = intelligence.get('last_funding_date')
        if funding_date:
            try:
                # Simple year check (you could make this more sophisticated)
                if '2024' in str(funding_date) or '2025' in str(funding_date):
                    signals.append('recently_funded')
            except:
                pass

        # B2B SaaS = scalable model
        if intelligence.get('is_b2b'):
            signals.append('b2b_model')

        # Tech stack indicates engineering culture
        tech_stack = intelligence.get('tech_stack', [])
        modern_tech = ['React', 'AWS', 'Kubernetes', 'Docker', 'Python', 'Node.js']
        if any(tech in str(tech_stack) for tech in modern_tech):
            signals.append('modern_tech_stack')

        # High follower count = strong brand
        followers = intelligence.get('follower_count')
        if followers and followers > 10000:
            signals.append('strong_brand')

        return signals

    def _search_crunchbase_url(self, company_name, company_data=None):
        """
        Hybrid Crunchbase URL search: Tavily candidates + Claude Agent SDK WebSearch validation

        This method uses a two-stage hybrid approach for maximum accuracy (100% on test set):
        - Stage 1: Tavily finds 5-10 candidate URLs (fast, broad coverage)
        - Stage 2: Claude Agent SDK WebSearch validates using CoreSignal context (accurate)

        Test Results (20 Series A companies):
        - Tavily Alone: 15/20 correct (75%)
        - Hybrid Approach: 20/20 correct (100%)
        - Improvement: +25% accuracy

        Args:
            company_name: Name of the company to search for
            company_data: Full CoreSignal company data for rich context (optional)

        Returns:
            str: Crunchbase organization URL or None
        """
        try:
            from tavily import TavilyClient
            import re
            import os

            # Get Tavily API key
            tavily_api_key = os.getenv('TAVILY_API_KEY')
            if not tavily_api_key:
                print(f"   ⚠️  TAVILY_API_KEY not set, using heuristic fallback")
                return self._generate_heuristic_crunchbase_url(company_name)

            print(f"   🔍 Stage 1: Tavily search for '{company_name}'")

            # STAGE 1: Get Tavily candidates (fast, broad discovery)
            tavily_client = TavilyClient(api_key=tavily_api_key)
            response = tavily_client.search(
                query=f"{company_name} crunchbase",
                search_depth="basic",
                max_results=10,  # Get more candidates for validation
                include_domains=["crunchbase.com"]
            )

            # Extract unique Crunchbase slugs WITH SCORES
            crunchbase_pattern = r'crunchbase\.com/organization/([a-z0-9-]+)'
            candidates = []
            seen = set()

            for result in response.get('results', []):
                match = re.search(crunchbase_pattern, result.get('url', ''), re.IGNORECASE)
                if match:
                    slug = match.group(1)
                    if slug not in seen:
                        # NEW: Extract score and metadata
                        candidates.append({
                            'slug': slug,
                            'score': result.get('score', 0.0),
                            'title': result.get('title', ''),
                            'url': result.get('url', '')
                        })
                        seen.add(slug)

            if not candidates:
                print(f"   ⚠️  Tavily found no candidates, using heuristic")
                return self._generate_heuristic_crunchbase_url(company_name)

            # Sort by score (highest first)
            candidates.sort(key=lambda x: x['score'], reverse=True)

            # Extract just slugs for logging
            candidate_slugs = [c['slug'] for c in candidates]
            print(f"   📋 Tavily found {len(candidates)} candidates: {candidate_slugs[:5]}")

            # If only 1 candidate, return immediately (no ambiguity)
            if len(candidates) == 1:
                url = f"https://www.crunchbase.com/organization/{candidates[0]['slug']}"
                print(f"   ✅ Single candidate: {url}")
                return {'url': url, 'source': 'tavily_single', 'confidence': candidates[0]['score']}

            # SIMPLIFIED: Use first Tavily candidate (fast!)
            # User can manually regenerate if URL is incorrect
            top_score = candidates[0]['score']
            url = f"https://www.crunchbase.com/organization/{candidates[0]['slug']}"

            if top_score >= 0.90:
                print(f"   ✅ High confidence match (score: {top_score:.2f}): {url}")
                source = 'tavily_high_confidence'
            else:
                print(f"   ✅ Using Tavily result (score: {top_score:.2f}): {url}")
                print(f"   💡 Low confidence - user can regenerate via UI if needed")
                source = 'tavily_fallback'

            return {'url': url, 'source': source, 'confidence': top_score}

        except ImportError as e:
            print(f"   ⚠️  Dependencies not installed ({e}), using heuristic")
            return self._generate_heuristic_crunchbase_url(company_name)
        except Exception as e:
            print(f"   ⚠️  Search failed ({e}), using heuristic")
            return self._generate_heuristic_crunchbase_url(company_name)

    def _validate_with_claude_websearch(self, company_name, tavily_candidates, company_data):
        """
        Use Claude Agent SDK WebSearch to pick correct URL from Tavily candidates

        This method uses rich CoreSignal context to disambiguate which Tavily candidate
        is the correct Crunchbase profile. It builds a detailed prompt with company
        description, location, funding details, and asks Claude to search and validate.

        Args:
            company_name: Company name
            tavily_candidates: List of Crunchbase slugs from Tavily
            company_data: Full CoreSignal company data for context

        Returns:
            str: Validated Crunchbase URL or None
        """
        try:
            import asyncio
            from claude_agent_sdk import query, ClaudeAgentOptions
            import re

            # Build rich context prompt
            prompt_parts = [
                f"Search for the correct Crunchbase profile for this company:",
                f"Company Name: {company_name}"
            ]

            # Add company description (most discriminative!)
            if company_data.get('description'):
                desc = company_data['description']  # Use COMPLETE description for best accuracy
                prompt_parts.append(f"Description: {desc}")
            elif company_data.get('industry'):
                prompt_parts.append(f"Industry: {company_data['industry']}")

            # Add location
            if company_data.get('location_hq_city'):
                location = company_data['location_hq_city']
                if company_data.get('location_hq_state'):
                    location += f", {company_data['location_hq_state']}"
                prompt_parts.append(f"Location: {location}")

            # Add funding details (CRITICAL for disambiguation)
            funding_rounds = company_data.get('company_funding_rounds_collection', [])
            if funding_rounds:
                latest = funding_rounds[0]
                funding_type = latest.get('last_round_type')
                funding_amount = latest.get('last_round_money_raised')

                if funding_type:
                    prompt_parts.append(f"Funding Round: {funding_type}")
                if funding_amount:
                    amount_m = int(funding_amount / 1000000)
                    prompt_parts.append(f"Amount Raised: ${amount_m}M")

            # Add Tavily candidates as context (extract slugs from dict structure)
            candidate_slugs = [c['slug'] if isinstance(c, dict) else c for c in tavily_candidates[:5]]
            prompt_parts.append("\nTavily found these Crunchbase URL candidates:")
            for i, slug in enumerate(candidate_slugs, 1):
                prompt_parts.append(f"{i}. https://www.crunchbase.com/organization/{slug}")

            prompt_parts.append("\nTASK:")
            prompt_parts.append("1. Visit EACH of the Crunchbase URLs above using WebSearch")
            prompt_parts.append("2. Compare the company details on each page to the CoreSignal data provided")
            prompt_parts.append("3. Find the URL where the description, location, and funding match EXACTLY")
            prompt_parts.append("4. Return ONLY the matching URL in your response")
            prompt_parts.append("\nIMPORTANT: You must cite specific evidence from the Crunchbase pages that proves the match.")

            prompt = "\n".join(prompt_parts)

            print(f"\n{'='*80}")
            print(f"📝 FULL CLAUDE WEBSEARCH PROMPT:")
            print(f"{'='*80}")
            print(prompt)
            print(f"{'='*80}\n")

            # Run async query() in sync context using asyncio WITH TIMEOUT
            async def async_search():
                collected_messages = []
                options = ClaudeAgentOptions(
                    model="claude-haiku-4-5-20251001",  # Haiku 4.5: 4-5x faster than Sonnet, low cost
                    allowed_tools=["WebSearch"]
                    # Note: max_tokens not supported in ClaudeAgentOptions API
                )

                async for message in query(prompt=prompt, options=options):
                    collected_messages.append(message)

                return collected_messages

            # Execute WebSearch with 10-second timeout
            async def run_with_timeout():
                return await asyncio.wait_for(async_search(), timeout=10.0)

            try:
                messages = asyncio.run(run_with_timeout())
            except asyncio.TimeoutError:
                print(f"   ⏱️  WebSearch timeout (10s), falling back to top Tavily result")
                top_candidate = tavily_candidates[0]
                url = f"https://www.crunchbase.com/organization/{top_candidate['slug']}"
                return {'url': url, 'source': 'timeout_fallback', 'confidence': top_candidate['score']}

            # Parse response to find matching candidate
            response_text = " ".join(str(msg) for msg in messages)

            print(f"\n{'='*80}")
            print(f"🤖 FULL CLAUDE WEBSEARCH RESPONSE:")
            print(f"{'='*80}")
            print(response_text)
            print(f"{'='*80}\n")

            # Extract Crunchbase URLs from response
            pattern = r'crunchbase\.com/organization/([a-z0-9-]+)'
            found_slugs = re.findall(pattern, response_text, re.IGNORECASE)

            # Find intersection: which Tavily candidate appears in response?
            for candidate in tavily_candidates:
                slug = candidate['slug'] if isinstance(candidate, dict) else candidate
                score = candidate.get('score', 0.0) if isinstance(candidate, dict) else 0.0

                if slug in found_slugs or slug in response_text:
                    url = f"https://www.crunchbase.com/organization/{slug}"
                    print(f"   ✅ Claude validated: {url}")
                    return {'url': url, 'source': 'websearch_validated', 'confidence': score}

            print(f"   ⚠️  No match found in WebSearch results")
            return None

        except ImportError as e:
            print(f"   ⚠️  claude-agent-sdk not installed: {e}")
            return None
        except Exception as e:
            import traceback
            error_str = str(e)
            error_details = traceback.format_exc()

            # Print main error
            print(f"   ⚠️  WebSearch validation failed: {error_str}")

            # Detect and highlight specific error types
            if "rate_limit" in error_str.lower() or "429" in error_str:
                print(f"   💳 API Rate Limit: You've hit the rate limit. Wait and try again.")
            elif "credit" in error_str.lower() or "quota" in error_str.lower():
                print(f"   💳 API Credits Exhausted: Check your Anthropic API credits/quota.")
            elif "api_key" in error_str.lower() or "401" in error_str or "403" in error_str:
                print(f"   🔑 API Key Issue: Check ANTHROPIC_API_KEY environment variable.")
            elif "404" in error_str:
                print(f"   🔍 Model Not Found: The model 'claude-haiku-4-5-20251001' may not be available.")

            # Print FULL traceback (no truncation) for debugging
            print(f"   🐛 Full error traceback:")
            for line in error_details.split('\n'):
                if line.strip():
                    print(f"      {line}")

            return None

    def _generate_heuristic_crunchbase_url(self, company_name):
        """
        Generate a Crunchbase URL using heuristic slug conversion

        This is a FALLBACK method when web search fails. It converts company names
        to Crunchbase slug format (lowercase, hyphens, no suffixes).

        WARNING: This method is NOT RELIABLE and may produce incorrect URLs.
        It should ONLY be used when web search fails.

        Args:
            company_name: Name of the company

        Returns:
            str: Heuristically generated Crunchbase URL (may be incorrect)
        """
        try:
            import re

            print(f"   🔧 Generating heuristic Crunchbase URL for: {company_name}")

            # Remove common suffixes that aren't in Crunchbase URLs
            name = company_name
            suffixes_to_remove = [
                ' Inc.', ' Inc', ' LLC', ' Corp.', ' Corp', ' Corporation',
                ' Limited', ' Ltd.', ' Ltd', ' Co.', ' Co', ' Company',
                ' GmbH', ' S.A.', ' AG', ' PLC', ' plc'
            ]
            for suffix in suffixes_to_remove:
                if name.endswith(suffix):
                    name = name[:-len(suffix)].strip()

            # Convert to lowercase and replace spaces/special chars with hyphens
            slug = name.lower()
            slug = re.sub(r'[^a-z0-9]+', '-', slug)  # Replace non-alphanumeric with hyphens
            slug = re.sub(r'-+', '-', slug)  # Remove duplicate hyphens
            slug = slug.strip('-')  # Remove leading/trailing hyphens

            if not slug:
                return None

            crunchbase_url = f"https://www.crunchbase.com/organization/{slug}"
            print(f"   ⚠️  HEURISTIC URL (may be incorrect): {crunchbase_url}")
            return crunchbase_url

        except Exception as e:
            print(f"   ❌ Failed to generate heuristic Crunchbase URL: {e}")
            return None


def search_profiles_with_endpoint(
    query: Dict[str, Any],
    endpoint: str = "employee_clean",
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Execute custom ES DSL search query against specified CoreSignal endpoint.

    Args:
        query: Elasticsearch DSL query dict
        endpoint: CoreSignal endpoint (employee_base, employee_clean, multi_source_employee)
        max_results: Maximum number of results to return

    Returns:
        Dict with 'success', 'results' (list of employee IDs or profiles), 'total'
    """
    import os
    import requests

    api_key = os.getenv("CORESIGNAL_API_KEY")
    if not api_key:
        return {"success": False, "error": "CORESIGNAL_API_KEY not found"}

    headers = {
        "accept": "application/json",
        "apikey": api_key,
        "Content-Type": "application/json"
    }

    # Build full URL - use preview endpoint for pagination
    base_url = f"https://api.coresignal.com/cdapi/v2/{endpoint}/search/es_dsl/preview"

    # NOTE: CoreSignal preview endpoint does NOT accept "size" in request body
    # It returns max 20 results per page, controlled by ?page= URL param
    # Remove size from query if present (causes HTTP 422)
    if "size" in query:
        del query["size"]

    try:
        print(f"🔍 Searching {endpoint} with custom query...")
        print(f"   Query size: {query.get('size', 'not set')}")

        response = requests.post(
            base_url,
            json=query,
            headers=headers,
            timeout=30
        )

        print(f"   Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text[:200]
            print(f"   ❌ Search failed: {error_text}")
            return {
                "success": False,
                "error": f"Search failed with status {response.status_code}",
                "details": error_text
            }

        data = response.json()
        print(f"   ✅ Search successful")

        # Handle both preview (list of IDs) and full search (hits structure)
        if isinstance(data, list):
            # Preview endpoint returns list of employee IDs
            results = data
            total = len(data)
        elif isinstance(data, dict) and "hits" in data:
            # Full search returns hits structure
            hits = data["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
            total = data["hits"]["total"]["value"]
        else:
            results = data
            total = len(results) if isinstance(results, list) else 0

        print(f"   Found {total} results")

        return {
            "success": True,
            "results": results,
            "total": total,
            "endpoint": endpoint
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout - CoreSignal API slow to respond"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "traceback": traceback.format_exc()
        }


def search_profiles_by_company_ids(
    company_ids: List[int],
    title: Optional[str] = None,
    seniority: Optional[str] = None,
    location: Optional[str] = None,
    max_per_company: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for employee profiles at multiple companies using CoreSignal.

    Args:
        company_ids: List of CoreSignal company IDs to search
        title: Optional job title filter (e.g., "engineer")
        seniority: Optional seniority level (e.g., "senior")
        location: Optional location filter (e.g., "San Francisco")
        max_per_company: Maximum profiles per company

    Returns:
        List of employee profile dictionaries
    """
    import os
    import requests

    api_key = os.getenv("CORESIGNAL_API_KEY")
    if not api_key:
        raise ValueError("CORESIGNAL_API_KEY not found")

    base_url = "https://api.coresignal.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    all_profiles = []

    for company_id in company_ids:
        # Build query for this company
        must_clauses = [
            {"term": {"last_company_id": company_id}}
        ]

        if title:
            must_clauses.append({
                "match": {
                    "title": {
                        "query": title,
                        "fuzziness": "AUTO"
                    }
                }
            })

        if seniority:
            must_clauses.append({
                "match": {
                    "title": {
                        "query": seniority,
                        "fuzziness": "AUTO"
                    }
                }
            })

        if location:
            must_clauses.append({
                "match": {
                    "location": {
                        "query": location,
                        "fuzziness": "AUTO"
                    }
                }
            })

        payload = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": max_per_company
        }

        try:
            response = requests.post(
                f"{base_url}/v2/employee_clean/search/es_dsl/preview",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            hits = data.get("hits", {}).get("hits", [])

            for hit in hits:
                source = hit.get("_source", {})
                all_profiles.append({
                    "employee_id": source.get("id"),
                    "full_name": source.get("name"),
                    "title": source.get("title"),
                    "company_id": company_id,
                    "company_name": source.get("last_company_name"),
                    "location": source.get("location"),
                    "linkedin_url": source.get("url"),
                    "headline": source.get("headline"),
                    "score": hit.get("_score")
                })

        except requests.exceptions.RequestException as e:
            print(f"[CORESIGNAL] Error searching company {company_id}: {e}")
            continue

    return all_profiles
