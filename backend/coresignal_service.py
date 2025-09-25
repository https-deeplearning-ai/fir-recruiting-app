import requests
import json
import os

class CoreSignalService:
    def __init__(self):
        self.api_key = "zGZEUYUw2Koty9kxPidzCHTce5Wl2vYL"
        self.headers = {
            "accept": "application/json",
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
    
    def fetch_linkedin_profile(self, linkedin_url):
        """
        Fetch LinkedIn profile data from CoreSignal API using LinkedIn URL
        
        Args:
            linkedin_url (str): LinkedIn profile URL
            
        Returns:
            dict: Profile data or error information
        """
        try:
            # Normalize the LinkedIn URL
            normalized_url = self._normalize_linkedin_url(linkedin_url)
            print(f"Original URL: {linkedin_url}")
            print(f"Normalized URL: {normalized_url}")
            
            # Step 1: Search for employee ID using LinkedIn URL
            print("Step 1: Searching for employee ID...")
            
            search_payload = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "websites_linkedin.exact": normalized_url
                                }
                            }
                        ]
                    }
                }
            }
            
            search_response = requests.post(
                "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl", 
                json=search_payload, 
                headers=self.headers
            )
            
            print(f"Search response status: {search_response.status_code}")
            
            if search_response.status_code != 200:
                return {
                    'error': f'Search failed: {search_response.status_code} - {search_response.text}',
                    'success': False
                }
            
            search_results = search_response.json()
            print(f"Search returned {len(search_results)} results")
            
            if not search_results:
                return {
                    'error': 'No employee found with this LinkedIn URL. The profile may not be in the CoreSignal database.',
                    'success': False,
                    'debug_info': {
                        'original_url': linkedin_url,
                        'normalized_url': normalized_url
                    }
                }
            
            print(f"✅ Found employee ID: {search_results[0]}")
            
            # Get the first employee ID
            employee_id = search_results[0]
            
            # Step 2: Fetch the full profile using the employee ID
            print("Step 2: Fetching full profile...")
            
            # Remove Content-Type for GET request
            get_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
            
            profile_response = requests.get(
                f"https://api.coresignal.com/cdapi/v2/employee_clean/collect/{employee_id}", 
                headers=get_headers
            )
            
            print(f"Profile fetch response status: {profile_response.status_code}")
            
            if profile_response.status_code != 200:
                return {
                    'error': f'Profile fetch failed: {profile_response.status_code} - {profile_response.text}',
                    'success': False
                }
            
            profile_data = profile_response.json()
            print("✅ Profile data retrieved successfully!")
            
            return {
                'success': True,
                'profile_data': profile_data,
                'employee_id': employee_id
            }
            
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'success': False
            }
    
    def _normalize_linkedin_url(self, url):
        """
        Normalize LinkedIn URL to handle different formats
        """
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Ensure it starts with https://
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Handle different LinkedIn URL formats
        if 'linkedin.com/in/' in url:
            # Extract the username part
            username = url.split('/in/')[-1].split('?')[0].split('#')[0]
            return f"https://www.linkedin.com/in/{username}"
        
        return url