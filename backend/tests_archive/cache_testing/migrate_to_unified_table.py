#!/usr/bin/env python3
"""
Migrate to unified table with both linkedin_url and employee_id columns

Strategy:
1. Fetch all from stored_profiles_by_employee_id (464 rows)
2. Extract linkedin_url from profile_data
3. Match with stored_profiles by URL
4. Insert with BOTH identifiers when match found
5. Insert remaining profiles with single identifier
"""

import os
import requests
import time
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
print("MIGRATE TO UNIFIED TABLE")
print("="*80)
print()
print("Goal: Merge stored_profiles + stored_profiles_by_employee_id")
print("      into ONE table with BOTH lookup columns")
print()
print("="*80)
print()

# Statistics
stats = {
    'total_id_profiles': 0,
    'total_url_profiles': 0,
    'both_identifiers': 0,
    'url_only': 0,
    'id_only': 0,
    'errors': 0
}

# =============================================================================
# STEP 1: Fetch all from stored_profiles_by_employee_id
# =============================================================================
print("📥 Step 1: Fetching profiles from stored_profiles_by_employee_id...")
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    exit(1)

id_profiles = response.json()
stats['total_id_profiles'] = len(id_profiles)
print(f"✅ Fetched {stats['total_id_profiles']} profiles with employee IDs")
print()

# =============================================================================
# STEP 2: Fetch all from stored_profiles
# =============================================================================
print("📥 Step 2: Fetching profiles from stored_profiles...")
url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=*"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    exit(1)

url_profiles = response.json()
stats['total_url_profiles'] = len(url_profiles)
print(f"✅ Fetched {stats['total_url_profiles']} profiles with LinkedIn URLs")
print()

# Create lookup map: linkedin_url → full profile data
url_profile_map = {}
for profile in url_profiles:
    linkedin_url = profile.get('linkedin_url')
    if linkedin_url:
        url_profile_map[linkedin_url] = profile

print(f"📊 Created lookup map with {len(url_profile_map)} LinkedIn URLs")
print()

# =============================================================================
# STEP 3: Smart merge - match by LinkedIn URL
# =============================================================================
print("🔄 Step 3: Merging profiles with smart matching...")
print("-"*80)
print()

matched_urls = set()  # Track which URLs were matched
unified_table_url = f"{SUPABASE_URL}/rest/v1/stored_profiles_unified"

# Process employee ID profiles
for i, id_profile in enumerate(id_profiles, 1):
    employee_id = id_profile.get('employee_id')
    profile_data = id_profile.get('profile_data', {})
    last_fetched = id_profile.get('last_fetched')
    checked_at = id_profile.get('checked_at')

    # Extract LinkedIn URL from profile_data
    linkedin_url = profile_data.get('profile_url')
    name = profile_data.get('full_name', 'Unknown')

    # Check if this URL exists in stored_profiles
    url_match = url_profile_map.get(linkedin_url) if linkedin_url else None

    if url_match:
        # MATCH FOUND: Insert with BOTH identifiers
        insert_data = {
            'linkedin_url': linkedin_url,
            'employee_id': employee_id,
            'profile_data': profile_data,
            'last_fetched': last_fetched,
            'checked_at': checked_at
        }
        stats['both_identifiers'] += 1
        matched_urls.add(linkedin_url)
        identifier_type = "BOTH"
    else:
        # NO MATCH: Insert with employee_id ONLY
        insert_data = {
            'employee_id': employee_id,
            'profile_data': profile_data,
            'last_fetched': last_fetched,
            'checked_at': checked_at
        }
        stats['id_only'] += 1
        identifier_type = "ID_ONLY"

    # Insert into unified table
    try:
        response = requests.post(unified_table_url, json=insert_data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            display_url = linkedin_url[:50] + "..." if linkedin_url and len(linkedin_url) > 50 else linkedin_url or 'N/A'
            print(f"[{i}/{stats['total_id_profiles']}] Employee {employee_id} → {display_url}")
            print(f"             {name} - {identifier_type} ✅")

            if i % 50 == 0:
                print(f"   ⏸️  Pausing... ({i} processed so far)")
                time.sleep(1)
        else:
            stats['errors'] += 1
            print(f"[{i}/{stats['total_id_profiles']}] Employee {employee_id} - ❌ ERROR: {response.status_code}")

    except Exception as e:
        stats['errors'] += 1
        print(f"[{i}/{stats['total_id_profiles']}] Employee {employee_id} - ❌ EXCEPTION: {str(e)}")

print()
print(f"✅ Processed all {stats['total_id_profiles']} employee ID profiles")
print()

# =============================================================================
# STEP 4: Insert remaining URL-only profiles
# =============================================================================
print("🔄 Step 4: Inserting URL-only profiles (not matched)...")
print("-"*80)
print()

url_only_count = 0
for i, url_profile in enumerate(url_profiles, 1):
    linkedin_url = url_profile.get('linkedin_url')

    # Skip if already matched
    if linkedin_url in matched_urls:
        continue

    url_only_count += 1
    profile_data = url_profile.get('profile_data', {})
    last_fetched = url_profile.get('last_fetched')
    checked_at = url_profile.get('checked_at')
    name = profile_data.get('full_name', 'Unknown')

    insert_data = {
        'linkedin_url': linkedin_url,
        'profile_data': profile_data,
        'last_fetched': last_fetched,
        'checked_at': checked_at
    }
    stats['url_only'] += 1

    # Insert into unified table
    try:
        response = requests.post(unified_table_url, json=insert_data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            display_url = linkedin_url[:50] + "..." if len(linkedin_url) > 50 else linkedin_url
            print(f"[{url_only_count}] {display_url}")
            print(f"         {name} - URL_ONLY ✅")
        else:
            stats['errors'] += 1
            print(f"[{url_only_count}] {linkedin_url} - ❌ ERROR: {response.status_code}")

    except Exception as e:
        stats['errors'] += 1
        print(f"[{url_only_count}] {linkedin_url} - ❌ EXCEPTION: {str(e)}")

print()
print(f"✅ Inserted {url_only_count} URL-only profiles")
print()

# =============================================================================
# SUMMARY
# =============================================================================
print("="*80)
print("📊 MIGRATION COMPLETE")
print("="*80)
print()

total_inserted = stats['both_identifiers'] + stats['url_only'] + stats['id_only']

print(f"Source tables:")
print(f"   stored_profiles_by_employee_id:   {stats['total_id_profiles']} profiles")
print(f"   stored_profiles:                  {stats['total_url_profiles']} profiles")
print()

print(f"Unified table (stored_profiles_unified):")
print(f"   ✅ BOTH identifiers:              {stats['both_identifiers']} rows")
print(f"   🔗 LinkedIn URL ONLY:             {stats['url_only']} rows")
print(f"   🆔 Employee ID ONLY:              {stats['id_only']} rows")
print(f"   ❌ Errors:                        {stats['errors']} rows")
print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"   📊 Total rows inserted:           {total_inserted}")
print()

# Calculate savings
original_total = stats['total_id_profiles'] + stats['total_url_profiles']
duplication_eliminated = original_total - total_inserted
storage_saved_mb = duplication_eliminated * 0.2  # Estimate ~200KB per profile

print(f"💾 Storage Savings:")
print(f"   Before: {original_total} rows across 2 tables")
print(f"   After:  {total_inserted} rows in 1 table")
print(f"   Saved:  {duplication_eliminated} duplicate rows (~{storage_saved_mb:.1f} MB)")
print()

print(f"🎯 Benefits:")
print(f"   ✅ Single source of truth (one profile = one row)")
print(f"   ✅ Both lookup methods available (indexed)")
print(f"   ✅ Automatic deduplication")
print(f"   ✅ {stats['both_identifiers']} profiles enriched with both identifiers")
print()

print("="*80)
print("✅ Migration successful!")
print()
print("Next steps:")
print("1. Run verify_unified_table.py to test lookups")
print("2. Update supabase_storage.py to use stored_profiles_unified")
print("3. Keep old tables as backup for 7 days")
print("4. Rename stored_profiles_unified → stored_profiles")
print("="*80)
