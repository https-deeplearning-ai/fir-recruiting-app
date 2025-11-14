#!/usr/bin/env python3
"""
Diagnostic script to check stored_profiles_by_employee_id data quality
Checks for empty/NULL profile_data and examines actual JSONB structure
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables required")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("="*80)
print("DIAGNOSTIC: stored_profiles_by_employee_id Data Quality Check")
print("="*80)
print()

# 1. Get total count
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=count"
response = requests.get(url, headers=headers)
if response.status_code == 200:
    count = len(response.json())
    print(f"📊 Total profiles in table: {count}")
else:
    print(f"❌ Error getting count: {response.status_code}")
    exit(1)

print()

# 2. Get sample profiles to check data quality
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*&limit=10"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Error getting data: {response.status_code}")
    exit(1)

profiles = response.json()

# Data quality statistics
null_profile_data = 0
empty_profile_data = 0
has_name = 0
has_url = 0
has_websites = 0
has_experience = 0

print("🔍 Analyzing profile_data JSONB structure...")
print("-"*80)

for profile in profiles:
    employee_id = profile.get('employee_id')
    profile_data = profile.get('profile_data')

    # Check for NULL
    if profile_data is None:
        null_profile_data += 1
        continue

    # Check for empty object
    if not profile_data or profile_data == {}:
        empty_profile_data += 1
        continue

    # Check for key fields
    if profile_data.get('name'):
        has_name += 1
    if profile_data.get('url'):
        has_url += 1
    if profile_data.get('websites_professional_network'):
        has_websites += 1
    if profile_data.get('experience_collection'):
        has_experience += 1

print(f"\n📈 Data Quality Summary (sample of {len(profiles)} profiles):")
print(f"   NULL profile_data:          {null_profile_data}/{len(profiles)}")
print(f"   Empty profile_data ({{}}):    {empty_profile_data}/{len(profiles)}")
print(f"   Has 'name' field:           {has_name}/{len(profiles)}")
print(f"   Has 'url' field:            {has_url}/{len(profiles)}")
print(f"   Has 'websites' field:       {has_websites}/{len(profiles)}")
print(f"   Has 'experience' field:     {has_experience}/{len(profiles)}")

print("\n" + "="*80)

# 3. Show sample profile structure
if profiles and len(profiles) > 0:
    print("\n📋 Sample Profile Data Structure:")
    print("-"*80)

    for i, profile in enumerate(profiles[:3], 1):
        employee_id = profile.get('employee_id')
        profile_data = profile.get('profile_data')

        print(f"\nProfile {i} (employee_id: {employee_id}):")

        if profile_data is None:
            print("   ❌ profile_data is NULL")
        elif not profile_data or profile_data == {}:
            print("   ❌ profile_data is empty object: {}")
        else:
            # Show keys present
            keys = list(profile_data.keys())
            print(f"   ✅ profile_data has {len(keys)} keys:")
            print(f"      Keys: {', '.join(keys[:10])}")
            if len(keys) > 10:
                print(f"      ... and {len(keys) - 10} more")

            # Show sample values
            print(f"   Sample values:")
            print(f"      name: {profile_data.get('name', 'N/A')}")
            print(f"      url: {profile_data.get('url', 'N/A')}")
            websites = profile_data.get('websites_professional_network', [])
            print(f"      websites: {websites[0] if websites else 'N/A'}")

    print("\n" + "="*80)

# 4. Verdict
print("\n🎯 VERDICT:")
print("-"*80)

if null_profile_data > 0 or empty_profile_data > 0:
    print("❌ ISSUE CONFIRMED: Profile data is NULL or empty")
    print(f"   {null_profile_data + empty_profile_data}/{len(profiles)} profiles have no data")
    print("\n💡 Recommendation: DELETE these broken profiles and re-fetch from CoreSignal")
elif has_name < len(profiles) * 0.8:  # Less than 80% have names
    print("⚠️  PARTIAL DATA: Profiles exist but missing key fields")
    print(f"   Only {has_name}/{len(profiles)} profiles have 'name' field")
    print("\n💡 Recommendation: Investigate field name mismatches or API response format")
else:
    print("✅ DATA LOOKS GOOD: Profiles have expected fields")
    print(f"   {has_name}/{len(profiles)} profiles have 'name' field")
    print(f"   {has_url}/{len(profiles)} profiles have 'url' field")

print("\n" + "="*80)
print("✅ Diagnostic complete!")
