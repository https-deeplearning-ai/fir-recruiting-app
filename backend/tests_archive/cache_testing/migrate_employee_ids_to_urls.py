#!/usr/bin/env python3
"""
Migrate profiles from stored_profiles_by_employee_id to stored_profiles
Uses actual LinkedIn URLs (profile_url) as the key instead of "id:xxxxx"

This maximizes cache coverage - same profile can be looked up by both:
- employee_id (domain search workflow)
- linkedin_url (single/batch assessment workflow)
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

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
print("MIGRATE EMPLOYEE IDs TO LINKEDIN URLs")
print("="*80)
print()
print("Purpose: Copy profiles from stored_profiles_by_employee_id to stored_profiles")
print("         using actual LinkedIn URLs as keys (not 'id:xxxxx')")
print()
print("="*80)
print()

# Statistics
stats = {
    'total': 0,
    'inserted': 0,
    'duplicates': 0,
    'no_url': 0,
    'errors': 0
}

# Step 1: Fetch all profiles from stored_profiles_by_employee_id
print("📥 Step 1: Fetching profiles from stored_profiles_by_employee_id...")
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"❌ Error fetching profiles: {response.status_code}")
    print(response.text)
    exit(1)

profiles = response.json()
stats['total'] = len(profiles)
print(f"✅ Fetched {stats['total']} profiles")
print()

# Step 2: Fetch existing URLs from stored_profiles (to check for duplicates)
print("📥 Step 2: Fetching existing URLs from stored_profiles...")
url = f"{SUPABASE_URL}/rest/v1/stored_profiles?select=linkedin_url"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"❌ Error fetching existing profiles: {response.status_code}")
    exit(1)

existing_profiles = response.json()
existing_urls = set(p['linkedin_url'] for p in existing_profiles)
print(f"✅ Found {len(existing_urls)} existing profiles in stored_profiles")
print()

# Step 3: Process each profile
print("🔄 Step 3: Migrating profiles...")
print("-"*80)
print()

for i, profile in enumerate(profiles, 1):
    employee_id = profile.get('employee_id')
    profile_data = profile.get('profile_data', {})
    last_fetched = profile.get('last_fetched')
    checked_at = profile.get('checked_at')

    # Extract LinkedIn URL from profile_data
    linkedin_url = profile_data.get('profile_url')
    name = profile_data.get('full_name', 'Unknown')

    # Validate LinkedIn URL
    if not linkedin_url:
        stats['no_url'] += 1
        print(f"[{i}/{stats['total']}] Employee ID {employee_id} ({name}) - ⚠️  NO URL (skipped)")
        continue

    # Check if already exists
    if linkedin_url in existing_urls:
        stats['duplicates'] += 1
        print(f"[{i}/{stats['total']}] Employee ID {employee_id} ({name}) - ⏭️  ALREADY EXISTS (skipped)")
        continue

    # Prepare data for insertion
    insert_data = {
        'linkedin_url': linkedin_url,
        'profile_data': profile_data,
        'last_fetched': last_fetched,
        'checked_at': checked_at
    }

    # Insert into stored_profiles
    try:
        url = f"{SUPABASE_URL}/rest/v1/stored_profiles"
        insert_headers = {**headers, 'Prefer': 'resolution=merge-duplicates'}
        response = requests.post(url, json=insert_data, headers=insert_headers, timeout=10)

        if response.status_code in [200, 201]:
            stats['inserted'] += 1
            # Truncate URL for display
            display_url = linkedin_url[:60] + "..." if len(linkedin_url) > 60 else linkedin_url
            print(f"[{i}/{stats['total']}] Employee ID {employee_id} → {display_url} ✅ INSERTED")

            # Add to existing_urls to prevent duplicates in this run
            existing_urls.add(linkedin_url)

            # Rate limiting (be nice to Supabase)
            if i % 50 == 0:
                print(f"   ⏸️  Pausing for rate limit... ({stats['inserted']} inserted so far)")
                time.sleep(1)
        else:
            stats['errors'] += 1
            print(f"[{i}/{stats['total']}] Employee ID {employee_id} - ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text[:100]}")

    except Exception as e:
        stats['errors'] += 1
        print(f"[{i}/{stats['total']}] Employee ID {employee_id} - ❌ EXCEPTION: {str(e)}")

print()
print("="*80)
print("📊 MIGRATION COMPLETE")
print("="*80)
print()
print(f"Total profiles processed:  {stats['total']}")
print(f"✅ Successfully inserted:  {stats['inserted']}")
print(f"⏭️  Already existed:        {stats['duplicates']}")
print(f"⚠️  No LinkedIn URL:        {stats['no_url']}")
print(f"❌ Errors:                 {stats['errors']}")
print()

# Calculate final counts
final_stored_profiles = len(existing_urls)  # Original + newly added
print(f"📈 Final Cache Coverage:")
print(f"   stored_profiles table:              {final_stored_profiles} profiles (by LinkedIn URL)")
print(f"   stored_profiles_by_employee_id:     {stats['total']} profiles (by employee ID)")
print(f"   Overlap (in both tables):           ~{stats['inserted']} profiles")
print()

# Calculate value
api_credits_saved = stats['inserted']
cost_savings = api_credits_saved * 0.50
print(f"💰 Additional API Credit Savings:")
print(f"   {api_credits_saved} profiles now cached by URL = ${cost_savings:.2f} saved")
print()

print("="*80)
print("✅ Migration successful!")
print()
print("Next steps:")
print("1. Test single profile assessment with one of these LinkedIn URLs")
print("2. Verify cache hit in logs")
print("3. Enjoy unified cache coverage!")
print("="*80)
