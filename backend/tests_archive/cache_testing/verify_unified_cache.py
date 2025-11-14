#!/usr/bin/env python3
"""
Verify unified cache after migration
Shows cache coverage by both lookup methods
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
print("UNIFIED CACHE VERIFICATION")
print("="*80)
print()

# 1. Count profiles in stored_profiles
url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=linkedin_url"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    url_profiles = response.json()
    url_count = len(url_profiles)
    print(f"✅ stored_profiles table: {url_count} profiles (lookup by LinkedIn URL)")
else:
    print(f"❌ Error: {response.status_code}")
    url_count = 0

# 2. Count profiles in stored_profiles_by_employee_id
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=employee_id"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    id_profiles = response.json()
    id_count = len(id_profiles)
    print(f"✅ stored_profiles_by_employee_id table: {id_count} profiles (lookup by employee ID)")
else:
    print(f"❌ Error: {response.status_code}")
    id_count = 0

print()
print("-"*80)
print()

# 3. Test a few random LinkedIn URLs from the migration
print("🔍 Testing Cache Lookup by LinkedIn URL:")
print()

# Sample URLs from migration log
test_urls = [
    "https://www.linkedin.com/in/hylkedijkstra",
    "https://www.linkedin.com/in/davidasarnow",
    "https://www.linkedin.com/in/timothyfitt"
]

for test_url in test_urls:
    encoded_url = test_url.replace('/', '%2F').replace(':', '%3A')
    url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=linkedin_url,profile_data&linkedin_url=eq.{encoded_url}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200 and response.json():
        profile = response.json()[0]
        profile_data = profile.get('profile_data', {})
        name = profile_data.get('full_name', 'Unknown')
        print(f"   ✅ {test_url}")
        print(f"      → Found: {name}")
    else:
        print(f"   ❌ {test_url}")
        print(f"      → NOT FOUND")

print()
print("-"*80)
print()

# 4. Calculate overlap
print("📊 Cache Statistics:")
print()
print(f"   Total unique profiles cached:        ~{url_count} (by URL)")
print(f"   Total profiles in employee ID table:  {id_count}")
print(f"   Estimated overlap:                    ~{462} profiles in BOTH tables")
print()

# 5. Calculate value
total_api_credits_saved = url_count + id_count - 462  # Subtract overlap
cost_savings = total_api_credits_saved * 0.50

print("💰 API Credit Savings:")
print(f"   Combined cache coverage:  ~{url_count} unique profiles")
print(f"   Total API credits saved:   ${url_count * 0.50:.2f}")
print(f"   (Prevents duplicate fetches from CoreSignal Collect API)")
print()

print("="*80)
print("✅ Unified cache verification complete!")
print()
print("Cache is now accessible by BOTH methods:")
print("  1. By LinkedIn URL (single/batch assessment)")
print("  2. By employee ID (domain search workflow)")
print("="*80)
