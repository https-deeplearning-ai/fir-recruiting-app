"""
Test Script: CoreSignal Multi-Source Employee API Evaluation
==============================================================

Purpose: Evaluate whether multi-source employee API can replace the current
         two-step flow (employee_clean + company_base enrichment)

Current Flow:
    1. Fetch employee via employee_clean/collect/{shorthand} (1 credit)
    2. Fetch each company via company_base/collect/{company_id} (N credits)
    Total: 1 + N credits per candidate

Hypothesis:
    Multi-source employee API includes enriched company data embedded in
    work experience, potentially eliminating need for separate company calls.

Test Plan:
    1. Fetch employee data via multi-source API
    2. Analyze embedded company data in work experiences
    3. Compare with current employee_clean + company_base flow
    4. Evaluate cost vs benefit tradeoff
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MultiSourceTester:
    def __init__(self):
        self.api_key = os.getenv("CORESIGNAL_API_KEY")
        if not self.api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable is not set")

        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key
        }

        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Track test statistics
        self.stats = {
            'profiles_tested': 0,
            'profiles_success': 0,
            'profiles_failed': 0,
            'companies_found': 0,
            'companies_with_funding': 0,
            'companies_with_crunchbase': 0,
            'companies_with_logos': 0
        }

    def fetch_multi_source_employee(self, linkedin_url):
        """
        Fetch employee profile using multi-source API

        Endpoint: /v2/employee_multi_source/collect/{shorthand}
        Cost: 2 Collect credits (per CoreSignal docs)

        Returns:
            dict: Full multi-source employee data or error info
        """
        try:
            print(f"\n{'='*80}")
            print(f"Testing Multi-Source Employee API")
            print(f"{'='*80}")
            print(f"LinkedIn URL: {linkedin_url}")

            # Extract shorthand from LinkedIn URL
            shorthand = linkedin_url.rstrip('/').split('/in/')[-1].split('?')[0]
            print(f"Shorthand: {shorthand}")

            # Call multi-source API
            url = f"https://api.coresignal.com/cdapi/v2/employee_multi_source/collect/{shorthand}"

            print(f"\n📡 Calling: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: Multi-source profile retrieved")

                # Save raw response
                filename = f"multi_source_{shorthand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = self.results_dir / filename
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"💾 Saved to: {filepath}")

                self.stats['profiles_success'] += 1
                return {
                    'success': True,
                    'data': data,
                    'shorthand': shorthand,
                    'saved_to': str(filepath)
                }
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                self.stats['profiles_failed'] += 1
                return {
                    'success': False,
                    'error': f"Status {response.status_code}",
                    'response': response.text
                }

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            self.stats['profiles_failed'] += 1
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.stats['profiles_tested'] += 1

    def analyze_company_data(self, employee_data):
        """
        Analyze embedded company data in multi-source employee profile

        Focus Areas:
            1. Company metadata (name, type, size, industry, location)
            2. Funding data (rounds, dates, amounts)
            3. Crunchbase URLs
            4. Company logos
            5. Additional enrichment (revenue, stock ticker, social URLs)

        Args:
            employee_data: Full multi-source employee response

        Returns:
            dict: Analysis summary with coverage statistics
        """
        print(f"\n{'='*80}")
        print(f"Analyzing Embedded Company Data")
        print(f"{'='*80}")

        experiences = employee_data.get('experience', [])
        total_companies = len(experiences)

        print(f"Total Work Experiences: {total_companies}")

        if not experiences:
            print("⚠️  No work experiences found")
            return {
                'total_companies': 0,
                'companies_analyzed': []
            }

        companies_analyzed = []

        for i, exp in enumerate(experiences, 1):
            print(f"\n{'-'*80}")
            print(f"Experience #{i}: {exp.get('position_title', 'Unknown')} at {exp.get('company_name', 'Unknown')}")
            print(f"{'-'*80}")

            company_analysis = {
                'experience_index': i,
                'position_title': exp.get('position_title'),
                'company_name': exp.get('company_name'),
                'date_from': exp.get('date_from'),
                'date_to': exp.get('date_to'),
                'is_current': exp.get('is_working'),

                # Company metadata
                'has_company_type': bool(exp.get('company_type')),
                'has_company_founded': bool(exp.get('company_founded_year')),
                'has_company_size': bool(exp.get('company_size_range')),
                'has_company_industry': bool(exp.get('company_industry')),
                'has_company_location': bool(exp.get('company_hq_full_address')),

                # Funding data (CRITICAL)
                'has_funding_date': bool(exp.get('company_last_funding_round_date')),
                'has_funding_amount': bool(exp.get('company_last_funding_round_amount_raised')),
                'funding_date': exp.get('company_last_funding_round_date'),
                'funding_amount': exp.get('company_last_funding_round_amount_raised'),

                # Crunchbase URL (CRITICAL - known issue)
                'has_crunchbase_url': bool(exp.get('company_crunchbase_url')),
                'crunchbase_url': exp.get('company_crunchbase_url'),

                # Company logo (CRITICAL for UI)
                'has_logo': bool(exp.get('company_logo_url')),
                'logo_url': exp.get('company_logo_url'),

                # Additional enrichment
                'has_linkedin_url': bool(exp.get('company_linkedin_url')),
                'has_website': bool(exp.get('company_website')),
                'has_stock_ticker': bool(exp.get('company_stock_ticker')),
                'has_revenue': bool(exp.get('company_annual_revenue_source_1')),

                # Raw data for reference
                'raw_company_fields': {k: v for k, v in exp.items() if k.startswith('company_')}
            }

            # Print analysis
            print(f"  Company Type: {exp.get('company_type') or 'N/A'}")
            print(f"  Founded: {exp.get('company_founded_year') or 'N/A'}")
            print(f"  Size: {exp.get('company_size_range') or 'N/A'}")
            print(f"  Industry: {exp.get('company_industry') or 'N/A'}")
            location = exp.get('company_hq_full_address') or 'N/A'
            print(f"  Location: {location[:60] if location != 'N/A' else location}...")

            print(f"\n  🔍 FUNDING DATA:")
            if company_analysis['has_funding_date'] or company_analysis['has_funding_amount']:
                print(f"    ✅ Funding Date: {exp.get('company_last_funding_round_date', 'N/A')}")
                print(f"    ✅ Funding Amount: {exp.get('company_last_funding_round_amount_raised', 'N/A')}")
                self.stats['companies_with_funding'] += 1
            else:
                print(f"    ❌ No funding data")

            print(f"\n  🔗 CRUNCHBASE URL:")
            if company_analysis['has_crunchbase_url']:
                print(f"    ✅ {exp.get('company_crunchbase_url')}")
                self.stats['companies_with_crunchbase'] += 1
            else:
                print(f"    ❌ Not available")

            print(f"\n  🖼️  COMPANY LOGO:")
            if company_analysis['has_logo']:
                print(f"    ✅ {exp.get('company_logo_url', '')[:60]}...")
                self.stats['companies_with_logos'] += 1
            else:
                print(f"    ❌ Not available")

            print(f"\n  📊 ADDITIONAL:")
            print(f"    LinkedIn: {'✅' if company_analysis['has_linkedin_url'] else '❌'}")
            print(f"    Website: {'✅' if company_analysis['has_website'] else '❌'}")
            print(f"    Stock Ticker: {'✅' if company_analysis['has_stock_ticker'] else '❌'}")
            print(f"    Revenue: {'✅' if company_analysis['has_revenue'] else '❌'}")

            companies_analyzed.append(company_analysis)
            self.stats['companies_found'] += 1

        # Calculate coverage statistics
        coverage = {
            'total_companies': total_companies,
            'funding_coverage_pct': (self.stats['companies_with_funding'] / total_companies * 100) if total_companies > 0 else 0,
            'crunchbase_coverage_pct': (self.stats['companies_with_crunchbase'] / total_companies * 100) if total_companies > 0 else 0,
            'logo_coverage_pct': (self.stats['companies_with_logos'] / total_companies * 100) if total_companies > 0 else 0,
            'companies_analyzed': companies_analyzed
        }

        print(f"\n{'='*80}")
        print(f"COVERAGE SUMMARY")
        print(f"{'='*80}")
        print(f"  Total Companies: {total_companies}")
        print(f"  Funding Data: {self.stats['companies_with_funding']}/{total_companies} ({coverage['funding_coverage_pct']:.1f}%)")
        print(f"  Crunchbase URLs: {self.stats['companies_with_crunchbase']}/{total_companies} ({coverage['crunchbase_coverage_pct']:.1f}%)")
        print(f"  Company Logos: {self.stats['companies_with_logos']}/{total_companies} ({coverage['logo_coverage_pct']:.1f}%)")

        return coverage

    def run_test(self, linkedin_urls):
        """
        Run complete multi-source evaluation for list of LinkedIn profiles

        Args:
            linkedin_urls: List of LinkedIn profile URLs to test
        """
        print(f"\n{'#'*80}")
        print(f"# Multi-Source Employee API Evaluation")
        print(f"{'#'*80}")
        print(f"Testing {len(linkedin_urls)} profiles\n")

        all_results = []

        for url in linkedin_urls:
            # Fetch multi-source profile
            result = self.fetch_multi_source_employee(url)

            if result['success']:
                # Analyze embedded company data
                coverage = self.analyze_company_data(result['data'])
                result['company_coverage'] = coverage

            all_results.append(result)

        # Print final statistics
        print(f"\n{'#'*80}")
        print(f"# FINAL STATISTICS")
        print(f"{'#'*80}")
        print(f"Profiles Tested: {self.stats['profiles_tested']}")
        print(f"Profiles Success: {self.stats['profiles_success']}")
        print(f"Profiles Failed: {self.stats['profiles_failed']}")
        print(f"\nCompanies Found: {self.stats['companies_found']}")
        print(f"Companies with Funding: {self.stats['companies_with_funding']} ({self.stats['companies_with_funding']/self.stats['companies_found']*100:.1f}%)")
        print(f"Companies with Crunchbase: {self.stats['companies_with_crunchbase']} ({self.stats['companies_with_crunchbase']/self.stats['companies_found']*100:.1f}%)")
        print(f"Companies with Logos: {self.stats['companies_with_logos']} ({self.stats['companies_with_logos']/self.stats['companies_found']*100:.1f}%)")

        # Save summary
        summary_file = self.results_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'statistics': self.stats,
                'results': all_results
            }, f, indent=2)

        print(f"\n💾 Summary saved to: {summary_file}")

        return all_results


if __name__ == "__main__":
    """
    Test with 3-5 LinkedIn profiles from Series A companies

    Suggested test cases:
    1. Recent Series A startup founder (2024-2025 funding)
    2. Executive at established Series A company
    3. Engineer at early-stage startup
    4. Mix of US and international companies
    5. Both technical and non-technical roles
    """

    test_profiles = [
        # Test Profile 1: Dario Amodei (Anthropic CEO) - AI company, Series C+
        "https://www.linkedin.com/in/dario-amodei-3934934/",

        # Test Profile 2: Aravind Srinivas (Perplexity CEO) - AI search, Series B ($20B valuation)
        "https://www.linkedin.com/in/aravind-srinivas-16051987/",

        # Test Profile 3: Ivan Zhao (Notion CEO) - Productivity software, Series C ($10B+ valuation)
        "https://www.linkedin.com/in/ivanhzhao/",

        # Test Profile 4: Dylan Field (Figma CEO) - Design tools, mature startup
        "https://www.linkedin.com/in/dylanfield/"
    ]

    if not test_profiles:
        print("⚠️  No test profiles provided!")
        print("Please add LinkedIn URLs to the test_profiles list")
        exit(1)

    tester = MultiSourceTester()
    tester.run_test(test_profiles)
