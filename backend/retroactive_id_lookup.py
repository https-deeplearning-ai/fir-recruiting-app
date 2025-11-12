#!/usr/bin/env python3
"""
Retroactively Add CoreSignal IDs to Old Sessions

This script:
1. Reads company data from old session files (before ID lookup integration)
2. Looks up CoreSignal IDs using the four-tier strategy
3. Creates `01_company_ids.json` with the results
4. Preserves original session data

Usage:
    python3 retroactive_id_lookup.py <session_id>
    python3 retroactive_id_lookup.py sess_20251108_030844_b4bf34c2
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from coresignal_company_lookup import CoreSignalCompanyLookup


def load_session_companies(session_dir: Path) -> List[Dict[str, Any]]:
    """Load company data from session files."""

    # Try to load from Stage 1 discovery file
    discovery_file = session_dir / "01_company_discovery.json"
    if discovery_file.exists():
        with open(discovery_file, 'r') as f:
            data = json.load(f)
            return data.get('companies', [])

    # Try preview results as fallback
    preview_file = session_dir / "02_preview_results.json"
    if preview_file.exists():
        with open(preview_file, 'r') as f:
            data = json.load(f)
            # Extract company names from preview results
            companies = []
            if 'results' in data:
                for result in data['results']:
                    company_name = result.get('current_company_name') or result.get('company_name')
                    if company_name:
                        companies.append({'name': company_name})
            return companies

    print("❌ No company data found in session")
    return []


def retroactive_lookup(session_id: str):
    """
    Retroactively look up CoreSignal IDs for a session.

    Args:
        session_id: Session ID (e.g., sess_20251108_030844_b4bf34c2)
    """
    # Find session directory
    base_dir = Path(__file__).parent / "logs" / "domain_search_sessions"
    session_dir = base_dir / session_id

    if not session_dir.exists():
        print(f"❌ Session not found: {session_id}")
        print(f"   Expected: {session_dir}")
        return

    print(f"\n{'='*80}")
    print(f"🔍 Retroactive ID Lookup for Session: {session_id}")
    print(f"{'='*80}\n")

    # Check if already has IDs
    ids_file = session_dir / "01_company_ids.json"
    if ids_file.exists():
        print(f"⚠️  Session already has 01_company_ids.json")
        response = input("   Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted.")
            return

    # Load companies
    print(f"📂 Loading company data from session...")
    companies = load_session_companies(session_dir)

    if not companies:
        return

    print(f"   ✅ Found {len(companies)} companies\n")

    # Look up IDs
    print(f"🔍 Looking up CoreSignal company IDs...")
    print(f"{'='*80}\n")

    lookup = CoreSignalCompanyLookup()

    companies_with_ids = []
    companies_without_ids = []
    tier_stats = {1: 0, 2: 0, 3: 0, 4: 0}

    for i, company in enumerate(companies, 1):
        company_name = company.get('name', company.get('company_name', ''))
        website = company.get('website')

        if not company_name:
            companies_without_ids.append(company)
            continue

        print(f"[{i}/{len(companies)}] {company_name}...", end=" ", flush=True)

        # Use four-tier lookup
        match = lookup.lookup_with_fallback(
            company_name=company_name,
            website=website,
            confidence_threshold=0.75,
            use_company_clean_fallback=True
        )

        if match:
            # Store ID and metadata
            company['coresignal_company_id'] = match['company_id']
            company['coresignal_confidence'] = match.get('confidence', 1.0)
            company['coresignal_searchable'] = True
            company['lookup_tier'] = match.get('tier', 0)
            company['lookup_method'] = match.get('lookup_method', 'unknown')

            # Track tier
            tier = match.get('tier', 0)
            if tier in tier_stats:
                tier_stats[tier] += 1

            # Enrich with additional data
            if 'website' in match and not company.get('website'):
                company['website'] = match['website']
            if 'employee_count' in match:
                company['employee_count'] = match['employee_count']

            companies_with_ids.append(company)
            print(f"✅ ID={match['company_id']} (tier {tier})")
        else:
            company['coresignal_searchable'] = False
            companies_without_ids.append(company)
            print(f"❌ No ID")

    # Calculate coverage
    total = len(companies)
    coverage_percent = (len(companies_with_ids) / total * 100) if total else 0

    print(f"\n{'='*80}")
    print(f"📊 Retroactive Lookup Results:")
    print(f"   Searchable (with IDs): {len(companies_with_ids)} companies ({coverage_percent:.1f}%)")
    print(f"   Not searchable (no IDs): {len(companies_without_ids)} companies")
    print(f"\n   Tier Breakdown:")
    print(f"      Tier 1 (Website): {tier_stats[1]} companies")
    print(f"      Tier 2 (Name Exact): {tier_stats[2]} companies")
    print(f"      Tier 3 (Fuzzy): {tier_stats[3]} companies")
    print(f"      Tier 4 (company_clean): {tier_stats[4]} companies")
    print(f"{'='*80}\n")

    # Save to 01_company_ids.json
    output_data = {
        "stage": "retroactive_company_id_lookup",
        "original_session_id": session_id,
        "searchable_companies": companies_with_ids,
        "non_searchable_companies": companies_without_ids,
        "coverage": {
            "with_ids": len(companies_with_ids),
            "without_ids": len(companies_without_ids),
            "percentage": round(coverage_percent, 1)
        },
        "tier_breakdown": tier_stats,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
    }

    with open(ids_file, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved: {ids_file}")
    print(f"\n✅ Retroactive lookup complete!")
    print(f"   Session now has CoreSignal IDs for future use.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 retroactive_id_lookup.py <session_id>")
        print("\nExample:")
        print("  python3 retroactive_id_lookup.py sess_20251108_030844_b4bf34c2")
        print("\nAvailable sessions:")

        base_dir = Path(__file__).parent / "logs" / "domain_search_sessions"
        if base_dir.exists():
            sessions = sorted(base_dir.glob("sess_*"), reverse=True)
            for session in sessions[:10]:
                print(f"  - {session.name}")
        sys.exit(1)

    session_id = sys.argv[1]
    retroactive_lookup(session_id)
