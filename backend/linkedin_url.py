import requests
import json
import os
import gzip
import time

API_KEY = "zGZEUYUw2Koty9kxPidzCHTce5Wl2vYL"

# Create files directory
os.makedirs("files", exist_ok=True)

# LinkedIn URL to search for
linkedin_url = "https://www.linkedin.com/in/adityakalro"

headers = {
    "accept": "application/json",
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

print(f"Searching for profile: {linkedin_url}")

# Step 1: Use the correct Elasticsearch DSL endpoint to search by LinkedIn URL
print("Step 1: Searching for employee ID using Elasticsearch DSL...")

# The correct field name is 'websites_linkedin' 
search_payload = {
    "query": {
        "bool": {
            "must": [
                {
                    "term": {
                        "websites_linkedin.exact": linkedin_url
                    }
                }
            ]
        }
    }
}

# Use the correct search endpoint
search_response = requests.post("https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl", 
                               json=search_payload, headers=headers)

if search_response.status_code == 200:
    search_results = search_response.json()
    print(f"✅ Search successful! Found {len(search_results)} results")
    
    if search_results:
        # The search returns employee IDs directly as integers
        employee_id = search_results[0]
        print(f"Found employee ID: {employee_id}")
        print("Note: Search returns employee IDs directly, not full objects")
    else:
        print("❌ No employee found with this LinkedIn URL")
        exit(1)
else:
    print(f"❌ Search error: {search_response.status_code} - {search_response.text}")
    exit(1)

# Step 2: Fetch the full profile using the employee ID
print("\nStep 2: Fetching full profile...")

# Remove Content-Type for GET request if it exists
if "Content-Type" in headers:
    headers.pop("Content-Type")

profile_response = requests.get(f"https://api.coresignal.com/cdapi/v2/employee_clean/collect/{employee_id}", 
                               headers=headers)

if profile_response.status_code == 200:
    profile_data = profile_response.json()
    print("✅ Profile data retrieved successfully!")
    
    # Save the profile data
    clean_filename = f"profile_{linkedin_url.split('/')[-1]}.json"
    clean_path = os.path.join("files", clean_filename)
    
    with open(clean_path, 'w') as f:
        json.dump(profile_data, f, indent=2)
    
    print(f"✅ Profile saved to: {clean_path}")
    
    # Show some key information
    print("\nProfile Summary:")
    print(f"Name: {profile_data.get('full_name', 'N/A')}")
    print(f"Headline: {profile_data.get('headline', 'N/A')}")
    print(f"Location: {profile_data.get('location', 'N/A')}")
    print(f"Profile URL: {profile_data.get('websites_linkedin', 'N/A')}")
    print(f"Connections: {profile_data.get('connections_count', 'N/A')}")
    print(f"Experience Count: {profile_data.get('experience_count', 'N/A')}")
    
    # Show first few lines of full data
    print(f"\nFull profile data (first 1000 characters):")
    print(json.dumps(profile_data, indent=2)[:1000] + "...")
    
else:
    print(f"❌ Error fetching profile: {profile_response.status_code} - {profile_response.text}")
    exit(1)