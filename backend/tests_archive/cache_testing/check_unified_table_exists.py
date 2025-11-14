#!/usr/bin/env python3
"""
Check if stored_profiles_unified table exists
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

print("="*80)
print("CHECKING IF UNIFIED TABLE EXISTS")
print("="*80)
print()

url = f"{SUPABASE_URL}/rest/v1/stored_profiles_unified?select=id&limit=1"

try:
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code == 200:
        print("✅ Table stored_profiles_unified EXISTS!")
        print()
        print("You can proceed with migration:")
        print("   python3 migrate_to_unified_table.py")
        print()
        exit(0)

    elif response.status_code == 404 or 'relation' in response.text:
        print("❌ Table stored_profiles_unified DOES NOT EXIST")
        print()
        print("="*80)
        print("ACTION REQUIRED: Create the table in Supabase")
        print("="*80)
        print()
        print("Steps:")
        print("1. Go to: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Click 'SQL Editor' in the left sidebar")
        print("4. Click 'New Query'")
        print("5. Copy and paste the contents of:")
        print("   backend/MIGRATION_UNIFIED_TABLE.sql")
        print("6. Click 'Run' to execute the SQL")
        print("7. Re-run this script to verify")
        print()
        print("="*80)
        exit(1)

    else:
        print(f"⚠️  Unknown response: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
