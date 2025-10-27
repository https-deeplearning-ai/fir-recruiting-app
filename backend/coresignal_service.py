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


class CoreSignalService:
    def __init__(self):
        self.api_key = os.getenv("CORESIGNAL_API_KEY")
        if not self.api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable is not set")
        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        # Company data cache to avoid duplicate API calls
        self.company_cache = {}

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
                        'storage_age_days': stored_result.get('cache_age_days', 0)
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
                    'from_storage': False
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

        OPTIMIZATION: Only enriches companies from jobs after min_year (default 2020)
        to save API credits and focus on recent, relevant experience.

        Args:
            profile_data (dict): Employee profile from fetch_linkedin_profile()
            min_year (int): Only enrich companies from jobs starting on or after this year (default: 2020)
            storage_functions (dict): Optional dict with 'get' and 'save' functions for database storage

        Returns:
            dict: Profile with enriched company data + metadata about API calls
        """
        print(f"\n🔍 Enriching profile with detailed company data (jobs from {min_year} onwards)...")

        experiences = profile_data.get('experience', [])
        total_companies = len(experiences)
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

            # OPTIMIZATION: Skip companies from jobs before min_year to save API credits
            start_year = exp.get('date_from_year')
            if start_year:
                try:
                    if int(start_year) < min_year:
                        print(f"   ⏭️  Experience {i}/{total_companies}: {company_name} - Skipped (started {start_year}, before {min_year})")
                        companies_skipped_old += 1
                        exp['company_enriched'] = None
                        continue
                except (ValueError, TypeError):
                    print(f"   ⚠️  Experience {i}/{total_companies}: {company_name} - Invalid start_year: {start_year}")
                    # Continue processing this experience even if year is invalid

            print(f"\n   📊 Experience {i}/{total_companies}: {company_name} (ID: {company_id}, started {start_year or 'unknown'})")

            # Fetch full company data (with storage integration)
            company_result = self.fetch_company_data(company_id, storage_functions=storage_functions)

            if company_result.get('success'):
                company_data = company_result['company_data']
                companies_enriched += 1

                # Add enriched fields to experience
                exp['company_enriched'] = self._extract_company_intelligence(company_data)

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

    def _extract_company_intelligence(self, company_data):
        """
        Extract key intelligence signals from full company profile

        Returns structured company insights optimized for hiring decisions

        IMPORTANT: We store BOTH the raw company data (all 45+ fields) AND
        curated intelligence fields for easy frontend access.
        """
        intelligence = {}

        # Store ALL raw company data for maximum flexibility
        # This ensures we never lose data and can access any field later
        intelligence['raw_data'] = company_data

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
                        print(f"   🔗 Crunchbase URL from company_crunchbase_info_collection: {cb_company_url}")
                        break

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

            # FALLBACK: If we didn't get company URL from crunchbase_info_collection, try to parse from funding round URL
            if not intelligence.get('crunchbase_company_url') and cb_round_url and '/funding_round/' in cb_round_url:
                # Generate company page URL from funding round URL
                # Example: .../funding_round/Nuvocargo-series-b--f6a355f5 -> .../organization/Nuvocargo
                try:
                    company_slug = cb_round_url.split('/funding_round/')[1].split('-series-')[0].split('-seed-')[0].split('-pre-seed-')[0].split('--')[0]
                    intelligence['crunchbase_company_url'] = f"https://www.crunchbase.com/organization/{company_slug}"
                    print(f"   🔗 Crunchbase URL parsed from funding round: {intelligence['crunchbase_company_url']}")
                except:
                    print(f"   ⚠️  Failed to parse Crunchbase company URL from funding round URL")
            elif not intelligence.get('crunchbase_company_url') and cb_round_url:
                # Use funding round URL as fallback if it's already in organization format
                intelligence['crunchbase_company_url'] = cb_round_url

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
