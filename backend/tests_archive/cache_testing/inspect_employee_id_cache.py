#!/usr/bin/env python3
"""
Inspect stored_profiles_by_employee_id table
Shows sample data to verify migration worked correctly
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
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
print("Inspecting stored_profiles_by_employee_id Table")
print("="*80)
print()

# 1. Get total count (query all IDs and count)
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=employee_id"
response = requests.get(url, headers=headers)
if response.status_code == 200:
    all_profiles = response.json()
    count = len(all_profiles)
    print(f"📊 Total cached profiles: {count}")
else:
    print(f"❌ Error getting count: {response.status_code}")
    exit(1)

print()

# 2. Get 10 sample rows
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*&limit=10&order=created_at.desc"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Error getting data: {response.status_code}")
    exit(1)

profiles = response.json()

print(f"📋 Sample of {len(profiles)} most recent profiles:")
print("-"*80)

for i, profile in enumerate(profiles, 1):
    employee_id = profile.get('employee_id')
    profile_data = profile.get('profile_data', {})
    created_at = profile.get('created_at', 'N/A')
    last_fetched = profile.get('last_fetched', 'N/A')

    # Extract key info from profile_data
    # CoreSignal uses: full_name, headline, profile_url, location (not name, title, url)
    name = profile_data.get('full_name', 'N/A')
    title = profile_data.get('headline', 'N/A')  # CoreSignal uses 'headline' not 'title'

    # Get current company from most recent experience
    experiences = profile_data.get('experience', [])
    company = experiences[0].get('title', 'N/A') if experiences else 'N/A'

    location = profile_data.get('location', 'N/A')
    linkedin_url = profile_data.get('profile_url', 'N/A')  # CoreSignal uses 'profile_url' not 'url'

    # Calculate age
    try:
        if last_fetched and last_fetched != 'N/A':
            last_fetch_dt = datetime.fromisoformat(last_fetched.replace('Z', '+00:00'))
            age_days = (datetime.now(last_fetch_dt.tzinfo) - last_fetch_dt).days
        else:
            age_days = 'N/A'
    except:
        age_days = 'N/A'

    print(f"\n{i}. Employee ID: {employee_id}")
    print(f"   Name: {name}")
    print(f"   Title: {title}")
    print(f"   Company: {company}")
    print(f"   Location: {location}")
    print(f"   LinkedIn: {linkedin_url[:50]}..." if len(str(linkedin_url)) > 50 else f"   LinkedIn: {linkedin_url}")
    print(f"   Cached: {age_days} days ago" if age_days != 'N/A' else f"   Cached: {age_days}")

print()
print("="*80)

# 3. Check for data quality issues
print("\n🔍 Data Quality Checks:")
print("-"*80)

# Check how many have LinkedIn URLs in profile_data
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=profile_data&limit=100"
response = requests.get(url, headers=headers)
if response.status_code == 200:
    sample = response.json()
    with_linkedin_url = 0
    for p in sample:
        profile_data = p.get('profile_data', {})
        # CoreSignal uses 'profile_url' field, not 'url'
        if profile_data.get('profile_url'):
            with_linkedin_url += 1

    print(f"✅ {with_linkedin_url}/{len(sample)} profiles have LinkedIn URL in profile_data ({with_linkedin_url/len(sample)*100:.1f}%)")

# 4. Show oldest vs newest
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=created_at,last_fetched&order=last_fetched.asc&limit=1"
response = requests.get(url, headers=headers)
if response.status_code == 200 and response.json():
    oldest = response.json()[0]
    print(f"📅 Oldest cached profile: {oldest.get('last_fetched', 'N/A')}")

url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=created_at,last_fetched&order=last_fetched.desc&limit=1"
response = requests.get(url, headers=headers)
if response.status_code == 200 and response.json():
    newest = response.json()[0]
    print(f"📅 Newest cached profile: {newest.get('last_fetched', 'N/A')}")

print()
print("="*80)
print("✅ Inspection complete!")
