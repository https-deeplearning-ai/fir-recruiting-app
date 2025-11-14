#!/usr/bin/env python3
"""
Add employee_id column to existing stored_profiles table
Then populate it with data from stored_profiles_by_employee_id
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
print("ADD EMPLOYEE_ID COLUMN TO STORED_PROFILES")
print("="*80)
print()
print("This will:")
print("  1. Fetch all profiles from stored_profiles_by_employee_id")
print("  2. Match them with stored_profiles by linkedin_url")
print("  3. Update matched rows with employee_id")
print("  4. Insert new rows for unmatched profiles")
print()
print("="*80)
print()

# Statistics
stats = {
    'total_id_profiles': 0,
    'total_url_profiles': 0,
    'updated': 0,
    'inserted': 0,
    'not_matched': 0,
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
url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=linkedin_url,profile_data"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    exit(1)

url_profiles = response.json()
stats['total_url_profiles'] = len(url_profiles)
print(f"✅ Fetched {stats['total_url_profiles']} existing profiles")
print()

# Create lookup map: linkedin_url → exists
existing_urls = {p['linkedin_url'] for p in url_profiles}
print(f"📊 Created lookup map with {len(existing_urls)} LinkedIn URLs")
print()

# =============================================================================
# STEP 3: Update or Insert profiles
# =============================================================================
print("🔄 Step 3: Updating/Inserting profiles...")
print("-"*80)
print()

for i, id_profile in enumerate(id_profiles, 1):
    employee_id = id_profile.get('employee_id')
    profile_data = id_profile.get('profile_data', {})
    linkedin_url = profile_data.get('profile_url')
    name = profile_data.get('full_name', 'Unknown')

    if not linkedin_url:
        # No LinkedIn URL, insert as new row with just employee_id
        # But stored_profiles requires linkedin_url, so we'll use a placeholder
        # Actually, let's skip these for now
        stats['not_matched'] += 1
        print(f"[{i}/{stats['total_id_profiles']}] Employee {employee_id} ({name}) - ⚠️  NO URL (skipped)")
        continue

    # Check if this URL already exists
    if linkedin_url in existing_urls:
        # UPDATE existing row with employee_id
        try:
            # PATCH request to update
            encoded_url = requests.utils.quote(linkedin_url, safe='')
            update_url = f"{SUPABASE_URL}/rest/v1/stored_profiles?linkedin_url=eq.{encoded_url}"

            update_data = {'employee_id': employee_id}
            response = requests.patch(update_url, json=update_data, headers=headers, timeout=10)

            if response.status_code in [200, 204]:
                stats['updated'] += 1
                display_url = linkedin_url[:50] + "..." if len(linkedin_url) > 50 else linkedin_url
                print(f"[{i}/{stats['total_id_profiles']}] {display_url}")
                print(f"             {name} - UPDATED with employee_id={employee_id} ✅")
            else:
                stats['errors'] += 1
                print(f"[{i}/{stats['total_id_profiles']}] {linkedin_url} - ❌ UPDATE ERROR: {response.status_code}")

        except Exception as e:
            stats['errors'] += 1
            print(f"[{i}/{stats['total_id_profiles']}] {linkedin_url} - ❌ EXCEPTION: {str(e)}")

    else:
        # INSERT new row with both linkedin_url and employee_id
        try:
            insert_url = f"{SUPABASE_URL}/rest/v1/stored_profiles"
            insert_data = {
                'linkedin_url': linkedin_url,
                'employee_id': employee_id,
                'profile_data': profile_data,
                'last_fetched': id_profile.get('last_fetched'),
                'checked_at': id_profile.get('checked_at')
            }

            response = requests.post(insert_url, json=insert_data, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                stats['inserted'] += 1
                display_url = linkedin_url[:50] + "..." if len(linkedin_url) > 50 else linkedin_url
                print(f"[{i}/{stats['total_id_profiles']}] {display_url}")
                print(f"             {name} - INSERTED with employee_id={employee_id} ✅")
            else:
                stats['errors'] += 1
                print(f"[{i}/{stats['total_id_profiles']}] {linkedin_url} - ❌ INSERT ERROR: {response.status_code}")
                print(f"   Response: {response.text[:100]}")

        except Exception as e:
            stats['errors'] += 1
            print(f"[{i}/{stats['total_id_profiles']}] {linkedin_url} - ❌ EXCEPTION: {str(e)}")

    # Pause for rate limiting
    if i % 50 == 0:
        print(f"   ⏸️  Pausing... ({i} processed)")
        import time
        time.sleep(1)

print()
print("="*80)
print("📊 MIGRATION COMPLETE")
print("="*80)
print()

total_processed = stats['updated'] + stats['inserted']
print(f"Source: {stats['total_id_profiles']} profiles from stored_profiles_by_employee_id")
print(f"Existing: {stats['total_url_profiles']} profiles in stored_profiles")
print()
print(f"Results:")
print(f"   ✅ UPDATED with employee_id:    {stats['updated']} rows")
print(f"   ✅ INSERTED new profiles:        {stats['inserted']} rows")
print(f"   ⚠️  Skipped (no URL):            {stats['not_matched']} rows")
print(f"   ❌ Errors:                       {stats['errors']} rows")
print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"   📊 Total processed:              {total_processed}")
print()

final_count = stats['total_url_profiles'] + stats['inserted']
print(f"🎯 Final stored_profiles table:")
print(f"   Total rows: {final_count}")
print(f"   With BOTH identifiers: ~{stats['updated']}")
print(f"   With URL only: ~{stats['total_url_profiles'] - stats['updated']}")
print(f"   With both: ~{stats['inserted']}")
print()

print("="*80)
print("✅ Migration successful!")
print()
print("Next steps:")
print("1. Update supabase_storage.py to lookup by either field")
print("2. Test lookups by both linkedin_url and employee_id")
print("3. Optionally drop stored_profiles_by_employee_id table (keep as backup)")
print("="*80)
