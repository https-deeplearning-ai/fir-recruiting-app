#!/usr/bin/env python3
"""
Check migration status - where did the 464 profiles go?
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
    'Content-Type': 'application/json',
    'Prefer': 'count=exact'
}

print("="*80)
print("MIGRATION STATUS CHECK")
print("="*80)
print()

# 1. Count profiles in OLD table (stored_profiles) with "id:xxxxx" format
print("📊 OLD TABLE: stored_profiles")
print("-"*80)

url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=*&linkedin_url=like.id:%25"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    old_weird_ids = response.json()
    print(f"   'id:xxxxx' entries remaining: {len(old_weird_ids)}")

    if old_weird_ids:
        print(f"\n   Sample IDs:")
        for profile in old_weird_ids[:5]:
            linkedin_url = profile.get('linkedin_url')
            employee_id = linkedin_url[3:] if linkedin_url.startswith('id:') else 'N/A'
            print(f"      - {linkedin_url} (employee_id: {employee_id})")
else:
    print(f"   ❌ Error: {response.status_code}")

print()

# 2. Count profiles in NEW table (stored_profiles_by_employee_id)
print("📊 NEW TABLE: stored_profiles_by_employee_id")
print("-"*80)

url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    new_profiles = response.json()
    print(f"   Total profiles: {len(new_profiles)}")

    if new_profiles:
        print(f"\n   Sample employee IDs:")
        for profile in new_profiles[:5]:
            employee_id = profile.get('employee_id')
            full_name = profile.get('profile_data', {}).get('full_name', 'N/A')
            print(f"      - {employee_id}: {full_name}")
else:
    print(f"   ❌ Error: {response.status_code}")

print()

# 3. Count TOTAL profiles in OLD table (both types)
print("📊 OLD TABLE: Total profiles (all types)")
print("-"*80)

url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=*"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    all_old_profiles = response.json()
    print(f"   Total profiles (all types): {len(all_old_profiles)}")

    # Count by type
    url_based = sum(1 for p in all_old_profiles if not p.get('linkedin_url', '').startswith('id:'))
    id_based = sum(1 for p in all_old_profiles if p.get('linkedin_url', '').startswith('id:'))

    print(f"   - URL-based: {url_based}")
    print(f"   - ID-based ('id:xxxxx'): {id_based}")
else:
    print(f"   ❌ Error: {response.status_code}")

print()
print("="*80)
print("🎯 SUMMARY")
print("="*80)
print()

if len(old_weird_ids) > 0 and len(new_profiles) < len(old_weird_ids):
    print(f"⚠️  MIGRATION INCOMPLETE!")
    print(f"   Expected: {len(old_weird_ids)} profiles to be migrated")
    print(f"   Actual: {len(new_profiles)} profiles in new table")
    print(f"   Missing: {len(old_weird_ids) - len(new_profiles)} profiles")
    print()
    print("💡 Possible reasons:")
    print("   1. Migration SQL was run multiple times and has ON CONFLICT DO NOTHING")
    print("   2. Data was manually deleted from new table")
    print("   3. Migration was run before all 'id:xxxxx' entries were created")
    print("   4. Some 'id:xxxxx' entries have invalid format (non-numeric)")
elif len(new_profiles) == 0:
    print("❌ NEW TABLE IS EMPTY!")
    print("   The migration may not have been run yet")
elif len(new_profiles) == len(old_weird_ids):
    print("✅ MIGRATION COMPLETE!")
    print(f"   All {len(new_profiles)} profiles successfully migrated")
else:
    print(f"📊 Current state:")
    print(f"   Old table 'id:xxxxx' entries: {len(old_weird_ids)}")
    print(f"   New table profiles: {len(new_profiles)}")

print()
print("="*80)
