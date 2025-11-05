"""
Comparison Tool: Multi-Source vs Current Flow (employee_clean + company_base)
==============================================================================

Purpose: Side-by-side comparison of data from:
         - Multi-source employee API (single call, 2 credits)
         - Current flow: employee_clean + company_base (multiple calls, 1+N credits)

Comparison Areas:
    1. Employee data completeness
    2. Company data richness
    3. Funding data availability and freshness
    4. Crunchbase URL coverage
    5. Company logo availability
    6. Total API cost per candidate
"""

import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import coresignal_service
sys.path.append(str(Path(__file__).parent.parent))
from coresignal_service import CoreSignalService


class APIComparator:
    def __init__(self):
        self.api_key = os.getenv("CORESIGNAL_API_KEY")
        if not self.api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable is not set")

        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key
        }

        # Use existing CoreSignalService for current flow
        self.coresignal = CoreSignalService()

        self.results_dir = Path(__file__).parent / "comparisons"
        self.results_dir.mkdir(exist_ok=True)

    def fetch_multi_source(self, linkedin_url):
        """Fetch via multi-source employee API"""
        try:
            shorthand = linkedin_url.rstrip('/').split('/in/')[-1].split('?')[0]
            url = f"https://api.coresignal.com/cdapi/v2/employee_multi_source/collect/{shorthand}"

            print(f"\n📡 Fetching multi-source: {shorthand}")
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                print(f"  ✅ Multi-source: SUCCESS")
                return {
                    'success': True,
                    'data': response.json(),
                    'api_calls': 1,
                    'credits_used': 2  # Multi-source costs 2 credits per docs
                }
            else:
                print(f"  ❌ Multi-source: FAILED ({response.status_code})")
                return {
                    'success': False,
                    'error': f"Status {response.status_code}",
                    'api_calls': 1,
                    'credits_used': 2
                }
        except Exception as e:
            print(f"  ❌ Multi-source: EXCEPTION ({e})")
            return {
                'success': False,
                'error': str(e),
                'api_calls': 1,
                'credits_used': 2
            }

    def fetch_current_flow(self, linkedin_url, min_year=2020):
        """Fetch via current flow: employee_clean + company_base"""
        try:
            print(f"\n📡 Fetching current flow (employee_clean + company_base)")

            # Step 1: Fetch employee profile
            employee_result = self.coresignal.fetch_linkedin_profile(linkedin_url)

            if not employee_result.get('success'):
                print(f"  ❌ Employee fetch: FAILED")
                return {
                    'success': False,
                    'error': 'Employee fetch failed',
                    'api_calls': employee_result.get('api_calls', 1),
                    'credits_used': 1
                }

            print(f"  ✅ Employee fetch: SUCCESS ({employee_result.get('api_calls', 1)} calls)")

            profile_data = employee_result['profile_data']
            api_calls = employee_result.get('api_calls', 1)
            credits_used = 1  # employee_clean costs 1 credit

            # Step 2: Enrich with company data (2020+ companies only)
            print(f"  📊 Enriching company data (jobs from {min_year}+)...")

            enrichment_result = self.coresignal.enrich_profile_with_company_data(
                profile_data,
                min_year=min_year
            )

            enrichment_summary = enrichment_result['enrichment_summary']
            api_calls += enrichment_summary['api_calls_made']
            credits_used += enrichment_summary['api_calls_made']

            print(f"  ✅ Company enrichment: {enrichment_summary['companies_enriched']} companies")
            print(f"  📊 Total API calls: {api_calls}")
            print(f"  💰 Total credits: {credits_used}")

            return {
                'success': True,
                'data': enrichment_result['profile_data'],
                'enrichment_summary': enrichment_summary,
                'api_calls': api_calls,
                'credits_used': credits_used
            }

        except Exception as e:
            print(f"  ❌ Current flow: EXCEPTION ({e})")
            return {
                'success': False,
                'error': str(e),
                'api_calls': 0,
                'credits_used': 0
            }

    def compare_employee_data(self, multi_source_data, current_flow_data):
        """Compare employee-level data completeness"""
        comparison = {
            'field': [],
            'multi_source': [],
            'current_flow': [],
            'winner': []
        }

        fields_to_check = [
            'full_name',
            'headline',
            'location',
            'experience',  # Count
            'education',   # Count
            'skills',      # Count
            'certifications',  # Count
            'summary'
        ]

        for field in fields_to_check:
            ms_value = multi_source_data.get(field)
            cf_value = current_flow_data.get(field)

            # For array fields, compare counts
            if isinstance(ms_value, list):
                ms_display = f"{len(ms_value)} items"
                cf_display = f"{len(cf_value) if cf_value else 0} items"
                winner = "Multi" if len(ms_value) > (len(cf_value) if cf_value else 0) else ("Current" if cf_value and len(cf_value) > len(ms_value) else "Tie")
            else:
                ms_display = "✅ Present" if ms_value else "❌ Missing"
                cf_display = "✅ Present" if cf_value else "❌ Missing"
                winner = "Multi" if ms_value and not cf_value else ("Current" if cf_value and not ms_value else "Tie")

            comparison['field'].append(field)
            comparison['multi_source'].append(ms_display)
            comparison['current_flow'].append(cf_display)
            comparison['winner'].append(winner)

        return comparison

    def compare_company_data(self, multi_source_data, current_flow_data):
        """Compare company-level data for work experiences"""

        ms_experiences = multi_source_data.get('experience', [])
        cf_experiences = current_flow_data.get('experience', [])

        comparison = {
            'total_companies': min(len(ms_experiences), len(cf_experiences)),
            'companies': []
        }

        print(f"\n{'='*80}")
        print(f"COMPANY DATA COMPARISON")
        print(f"{'='*80}")

        for i in range(comparison['total_companies']):
            ms_exp = ms_experiences[i] if i < len(ms_experiences) else {}
            cf_exp = cf_experiences[i] if i < len(cf_experiences) else {}

            company_name = ms_exp.get('company_name') or cf_exp.get('company_name', 'Unknown')

            print(f"\nCompany #{i+1}: {company_name}")
            print(f"{'-'*80}")

            # Extract company intelligence from current flow
            cf_company_intelligence = cf_exp.get('company_enriched') or {}

            company_comparison = {
                'company_name': company_name,
                'position': ms_exp.get('position_title') or cf_exp.get('title'),

                # Company metadata
                'multi_source': {
                    'has_type': bool(ms_exp.get('company_type')),
                    'has_founded': bool(ms_exp.get('company_founded_year')),
                    'has_size': bool(ms_exp.get('company_size_range')),
                    'has_industry': bool(ms_exp.get('company_industry')),
                    'has_location': bool(ms_exp.get('company_hq_full_address')),

                    # Funding (CRITICAL)
                    'has_funding': bool(ms_exp.get('company_last_funding_round_date')),
                    'funding_date': ms_exp.get('company_last_funding_round_date'),
                    'funding_amount': ms_exp.get('company_last_funding_round_amount_raised'),

                    # Crunchbase URL (CRITICAL)
                    'has_crunchbase_url': bool(ms_exp.get('company_crunchbase_url')),
                    'crunchbase_url': ms_exp.get('company_crunchbase_url'),

                    # Company logo (CRITICAL for UI)
                    'has_logo': bool(ms_exp.get('company_logo_url')),
                    'logo_url': ms_exp.get('company_logo_url')
                },

                'current_flow': {
                    'has_type': bool(cf_company_intelligence.get('type')),
                    'has_founded': bool(cf_company_intelligence.get('founded')),
                    'has_size': bool(cf_company_intelligence.get('size_range')),
                    'has_industry': bool(cf_company_intelligence.get('industry')),
                    'has_location': bool(cf_company_intelligence.get('hq_country')),

                    # Funding (CRITICAL)
                    'has_funding': bool(cf_company_intelligence.get('last_funding_type')),
                    'funding_date': cf_company_intelligence.get('last_funding_date'),
                    'funding_amount': cf_company_intelligence.get('last_funding_amount_formatted'),

                    # Crunchbase URL (CRITICAL)
                    'has_crunchbase_url': bool(cf_company_intelligence.get('crunchbase_company_url')),
                    'crunchbase_url': cf_company_intelligence.get('crunchbase_company_url'),

                    # Company logo (CRITICAL for UI)
                    'has_logo': bool(cf_company_intelligence.get('logo_url')),
                    'logo_url': cf_company_intelligence.get('logo_url')
                }
            }

            # Print comparison
            print(f"  Funding Data:")
            print(f"    Multi-Source: {'✅' if company_comparison['multi_source']['has_funding'] else '❌'} {company_comparison['multi_source']['funding_date'] or 'N/A'}")
            print(f"    Current Flow: {'✅' if company_comparison['current_flow']['has_funding'] else '❌'} {company_comparison['current_flow']['funding_date'] or 'N/A'}")

            print(f"\n  Crunchbase URL:")
            print(f"    Multi-Source: {'✅' if company_comparison['multi_source']['has_crunchbase_url'] else '❌'}")
            print(f"    Current Flow: {'✅' if company_comparison['current_flow']['has_crunchbase_url'] else '❌'}")

            print(f"\n  Company Logo:")
            print(f"    Multi-Source: {'✅' if company_comparison['multi_source']['has_logo'] else '❌'}")
            print(f"    Current Flow: {'✅' if company_comparison['current_flow']['has_logo'] else '❌'}")

            comparison['companies'].append(company_comparison)

        return comparison

    def calculate_cost_benefit(self, multi_source_result, current_flow_result, company_comparison):
        """Calculate cost-benefit analysis"""

        print(f"\n{'='*80}")
        print(f"COST-BENEFIT ANALYSIS")
        print(f"{'='*80}")

        # Multi-source costs
        ms_credits = multi_source_result['credits_used']
        ms_calls = multi_source_result['api_calls']

        # Current flow costs
        cf_credits = current_flow_result['credits_used']
        cf_calls = current_flow_result['api_calls']

        # Calculate savings
        credit_savings = cf_credits - ms_credits
        credit_savings_pct = (credit_savings / cf_credits * 100) if cf_credits > 0 else 0

        print(f"\nAPI Costs:")
        print(f"  Multi-Source:  {ms_calls} API calls, {ms_credits} credits")
        print(f"  Current Flow:  {cf_calls} API calls, {cf_credits} credits")
        print(f"  Savings:       {credit_savings} credits ({credit_savings_pct:.1f}%)")

        # Calculate data completeness scores
        ms_score = 0
        cf_score = 0

        for company in company_comparison['companies']:
            # Funding data (40 points)
            if company['multi_source']['has_funding']:
                ms_score += 40
            if company['current_flow']['has_funding']:
                cf_score += 40

            # Crunchbase URL (40 points - CRITICAL)
            if company['multi_source']['has_crunchbase_url']:
                ms_score += 40
            if company['current_flow']['has_crunchbase_url']:
                cf_score += 40

            # Company logo (20 points)
            if company['multi_source']['has_logo']:
                ms_score += 20
            if company['current_flow']['has_logo']:
                cf_score += 20

        total_companies = len(company_comparison['companies'])
        ms_score = (ms_score / (total_companies * 100) * 100) if total_companies > 0 else 0
        cf_score = (cf_score / (total_companies * 100) * 100) if total_companies > 0 else 0

        print(f"\nData Completeness Scores (0-100):")
        print(f"  Multi-Source:  {ms_score:.1f}%")
        print(f"  Current Flow:  {cf_score:.1f}%")

        # Final recommendation
        print(f"\n{'='*80}")
        print(f"RECOMMENDATION")
        print(f"{'='*80}")

        if ms_score >= cf_score * 0.9 and credit_savings_pct >= 50:
            recommendation = "✅ Switch to Multi-Source (comparable data, significant cost savings)"
        elif ms_score >= cf_score and credit_savings_pct >= 30:
            recommendation = "✅ Switch to Multi-Source (equal or better data, cost savings)"
        elif cf_score > ms_score * 1.2:
            recommendation = "❌ Keep Current Flow (significantly better data)"
        else:
            recommendation = "⚠️  Hybrid Approach (use multi-source, supplement with company_base for critical gaps)"

        print(f"\n{recommendation}")

        return {
            'multi_source_credits': ms_credits,
            'current_flow_credits': cf_credits,
            'credit_savings': credit_savings,
            'credit_savings_pct': credit_savings_pct,
            'multi_source_score': ms_score,
            'current_flow_score': cf_score,
            'recommendation': recommendation
        }

    def run_comparison(self, linkedin_url):
        """Run complete comparison for a single profile"""

        print(f"\n{'#'*80}")
        print(f"# API COMPARISON: Multi-Source vs Current Flow")
        print(f"{'#'*80}")
        print(f"LinkedIn URL: {linkedin_url}\n")

        # Fetch via both methods
        multi_source_result = self.fetch_multi_source(linkedin_url)
        current_flow_result = self.fetch_current_flow(linkedin_url)

        if not multi_source_result['success'] or not current_flow_result['success']:
            print("\n❌ One or both API calls failed. Cannot complete comparison.")
            return None

        # Compare employee data
        print(f"\n{'='*80}")
        print(f"EMPLOYEE DATA COMPARISON")
        print(f"{'='*80}")
        employee_comparison = self.compare_employee_data(
            multi_source_result['data'],
            current_flow_result['data']
        )

        for i in range(len(employee_comparison['field'])):
            print(f"  {employee_comparison['field'][i]:<20} | Multi: {employee_comparison['multi_source'][i]:<15} | Current: {employee_comparison['current_flow'][i]:<15} | Winner: {employee_comparison['winner'][i]}")

        # Compare company data
        company_comparison = self.compare_company_data(
            multi_source_result['data'],
            current_flow_result['data']
        )

        # Cost-benefit analysis
        cost_benefit = self.calculate_cost_benefit(
            multi_source_result,
            current_flow_result,
            company_comparison
        )

        # Save comparison report
        shorthand = linkedin_url.rstrip('/').split('/in/')[-1].split('?')[0]
        report_file = self.results_dir / f"comparison_{shorthand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump({
                'linkedin_url': linkedin_url,
                'test_date': datetime.now().isoformat(),
                'employee_comparison': employee_comparison,
                'company_comparison': company_comparison,
                'cost_benefit': cost_benefit,
                'raw_data': {
                    'multi_source': multi_source_result['data'],
                    'current_flow': current_flow_result['data']
                }
            }, f, indent=2)

        print(f"\n💾 Comparison report saved to: {report_file}")

        return {
            'employee_comparison': employee_comparison,
            'company_comparison': company_comparison,
            'cost_benefit': cost_benefit,
            'report_file': str(report_file)
        }


if __name__ == "__main__":
    """
    Run side-by-side comparison for a single LinkedIn profile

    Usage:
        python compare_api_responses.py <linkedin_url>
    """

    if len(sys.argv) < 2:
        print("Usage: python compare_api_responses.py <linkedin_url>")
        print("Example: python compare_api_responses.py https://www.linkedin.com/in/firstname-lastname/")
        exit(1)

    linkedin_url = sys.argv[1]

    comparator = APIComparator()
    comparator.run_comparison(linkedin_url)
