#!/usr/bin/env python3
"""
Show actual field names in stored profile data
"""

import os
import requests
import json
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
print("FIELD NAME ANALYSIS: What fields does CoreSignal actually return?")
print("="*80)
print()

# Get ONE sample profile
url = f"{SUPABASE_URL}/rest/v1/stored_profiles_by_employee_id?select=*&limit=1"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    exit(1)

profiles = response.json()

if not profiles:
    print("❌ No profiles found in table")
    exit(1)

profile = profiles[0]
employee_id = profile.get('employee_id')
profile_data = profile.get('profile_data', {})

print(f"📋 Profile ID: {employee_id}")
print(f"📊 Total fields: {len(profile_data)}")
print()
print("="*80)
print("ALL FIELD NAMES:")
print("="*80)

# Show all keys alphabetically
for i, key in enumerate(sorted(profile_data.keys()), 1):
    value = profile_data[key]

    # Show sample value (truncated)
    if value is None:
        sample = "null"
    elif isinstance(value, (str, int, float, bool)):
        sample = str(value)[:60]
    elif isinstance(value, list):
        sample = f"[array with {len(value)} items]"
    elif isinstance(value, dict):
        sample = f"{{object with {len(value)} keys}}"
    else:
        sample = type(value).__name__

    print(f"{i:3}. {key:40} = {sample}")

print()
print("="*80)
print("LOOKING FOR NAME/URL FIELDS:")
print("="*80)

# Search for fields that might contain name or URL
name_candidates = []
url_candidates = []

for key in profile_data.keys():
    key_lower = key.lower()
    value = profile_data[key]

    # Check for name-like fields
    if 'name' in key_lower and value:
        name_candidates.append((key, value))

    # Check for url/website fields
    if any(term in key_lower for term in ['url', 'website', 'linkedin', 'link']):
        url_candidates.append((key, value))

print("\n🔍 Potential NAME fields:")
if name_candidates:
    for key, value in name_candidates:
        print(f"   {key}: {str(value)[:80]}")
else:
    print("   ❌ No fields with 'name' found")

print("\n🔍 Potential URL/LinkedIn fields:")
if url_candidates:
    for key, value in url_candidates:
        sample = str(value)[:80] if not isinstance(value, list) else f"[{len(value)} items] {str(value[0])[:60] if value else 'empty'}"
        print(f"   {key}: {sample}")
else:
    print("   ❌ No fields with 'url' or 'website' found")

print()
print("="*80)
print("✅ Analysis complete!")
