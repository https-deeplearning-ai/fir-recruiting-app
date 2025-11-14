#!/usr/bin/env python3
"""
Verify company cache data integrity
Check that company IDs and names are correctly mapped
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("="*80)
print("COMPANY CACHE VERIFICATION")
print("="*80)
print()

# =============================================================================
# 1. Check company_id_cache table (name → ID mappings)
# =============================================================================
print("📊 Table 1: company_id_cache (name → coresignal_id mappings)")
print("-"*80)

url = f"{SUPABASE_URL}/rest/v1/company_lookup_cache?select=*&limit=10"
response = requests.get(url, headers=headers, timeout=10)

if response.status_code == 200:
    cache_entries = response.json()
    print(f"✅ Found {len(cache_entries)} entries (showing sample)")
    print()

    for i, entry in enumerate(cache_entries[:5], 1):
        company_name = entry.get('company_name')
        coresignal_id = entry.get('coresignal_id')
        lookup_tier = entry.get('lookup_tier')
        hit_count = entry.get('hit_count', 0)

        print(f"{i}. {company_name}")
        print(f"   → CoreSignal ID: {coresignal_id}")
        print(f"   → Lookup tier: {lookup_tier}")
        print(f"   → Cache hits: {hit_count}")
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")

print()

# =============================================================================
# 2. Check stored_companies table (full company data)
# =============================================================================
print("📊 Table 2: stored_companies (full company data by ID)")
print("-"*80)

url = f"{SUPABASE_URL}/rest/v1/stored_companies?select=*&limit=10"
response = requests.get(url, headers=headers, timeout=10)

if response.status_code == 200:
    companies = response.json()
    print(f"✅ Found {len(companies)} stored companies (showing sample)")
    print()

    for i, company in enumerate(companies[:5], 1):
        company_id = company.get('company_id')
        company_data = company.get('company_data', {})

        # Extract company name from company_data
        company_name = company_data.get('name', 'N/A')
        website = company_data.get('website', 'N/A')

        print(f"{i}. Company ID: {company_id}")
        print(f"   → Name: {company_name}")
        print(f"   → Website: {website}")
        print(f"   → Data keys: {len(company_data)} fields")
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")

print()

# =============================================================================
# 3. Cross-reference check
# =============================================================================
print("🔍 Cross-Reference Check")
print("-"*80)
print("Checking if company_lookup_cache IDs exist in stored_companies...")
print()

# Re-fetch cache_entries if needed
url_cache = f"{SUPABASE_URL}/rest/v1/company_lookup_cache?select=*&limit=10"
r_cache = requests.get(url_cache, headers=headers, timeout=10)
cache_entries = r_cache.json() if r_cache.status_code == 200 else []

if r_cache.status_code == 200 and cache_entries:
    # Get all company IDs from stored_companies
    url = f"{SUPABASE_URL}/rest/v1/stored_companies?select=company_id"
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        stored_ids = {c['company_id'] for c in response.json()}

        # Check first 5 cache entries
        for entry in cache_entries[:5]:
            cache_name = entry.get('company_name')
            cache_id = entry.get('coresignal_id')

            if cache_id in stored_ids:
                print(f"✅ {cache_name} (ID: {cache_id}) - FOUND in stored_companies")
            else:
                print(f"⚠️  {cache_name} (ID: {cache_id}) - NOT in stored_companies (not fetched yet)")

print()
print("="*80)
print("📈 SUMMARY")
print("="*80)
print()

# Count totals
url1 = f"{SUPABASE_URL}/rest/v1/company_lookup_cache?select=coresignal_id"
r1 = requests.get(url1, headers=headers, timeout=10)
total_cache = len(r1.json()) if r1.status_code == 200 else 0

url2 = f"{SUPABASE_URL}/rest/v1/stored_companies?select=company_id"
r2 = requests.get(url2, headers=headers, timeout=10)
total_stored = len(r2.json()) if r2.status_code == 200 else 0

print(f"company_lookup_cache entries:  {total_cache}")
print(f"stored_companies entries:  {total_stored}")
print()

if total_cache > total_stored:
    diff = total_cache - total_stored
    print(f"ℹ️  {diff} companies have IDs cached but not full data yet")
    print("   (This is normal - IDs are cached during discovery,")
    print("    full data is cached during profile enrichment)")
elif total_stored > total_cache:
    print("⚠️  More stored companies than cached IDs (unexpected)")
else:
    print("✅ Cache counts match!")

print()
print("="*80)
print("✅ Verification complete!")
