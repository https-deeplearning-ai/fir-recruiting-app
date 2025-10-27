"""
Extension Service
Handles all Chrome extension API operations including list management,
quick profile adds, and assessment triggers.
"""

import requests
import os
from datetime import datetime
from typing import List, Dict, Optional

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class ExtensionService:
    """Service for Chrome extension operations"""

    def __init__(self):
        self.headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

    # ==================== LIST MANAGEMENT ====================

    def get_lists(self, recruiter_name: str) -> List[Dict]:
        """Get all lists for a recruiter"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/recruiter_lists"
            params = {
                'recruiter_name': f'eq.{recruiter_name}',
                'is_active': 'eq.true',
                'order': 'created_at.desc'
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.ok:
                return response.json()
            else:
                print(f"Failed to get lists: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting lists: {e}")
            return []

    def create_list(self, recruiter_name: str, list_name: str, job_template_id: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict]:
        """Create a new list"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/recruiter_lists"

            data = {
                'recruiter_name': recruiter_name,
                'list_name': list_name,
                'description': description,
                'job_template_id': job_template_id
            }

            headers = {
                **self.headers,
                'Prefer': 'return=representation'
            }

            response = requests.post(url, json=data, headers=headers)

            if response.ok:
                result = response.json()
                return result[0] if result else None
            else:
                print(f"Failed to create list: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating list: {e}")
            return None

    def update_list(self, list_id: str, updates: Dict) -> bool:
        """Update a list"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/recruiter_lists"
            params = {'id': f'eq.{list_id}'}

            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()

            response = requests.patch(url, json=updates, headers=self.headers, params=params)

            return response.ok
        except Exception as e:
            print(f"Error updating list: {e}")
            return False

    def delete_list(self, list_id: str) -> bool:
        """Soft delete a list (set is_active = false)"""
        return self.update_list(list_id, {'is_active': False})

    def get_list_stats(self, list_id: str) -> Optional[Dict]:
        """Get statistics for a list"""
        try:
            # Get the list
            list_url = f"{SUPABASE_URL}/rest/v1/recruiter_lists"
            list_params = {'id': f'eq.{list_id}'}

            list_response = requests.get(list_url, headers=self.headers, params=list_params)

            if not list_response.ok:
                return None

            lists = list_response.json()
            if not lists:
                return None

            list_data = lists[0]

            # Get profile stats
            profiles_url = f"{SUPABASE_URL}/rest/v1/extension_profiles"
            profiles_params = {'list_id': f'eq.{list_id}'}

            profiles_response = requests.get(profiles_url, headers=self.headers, params=profiles_params)

            if profiles_response.ok:
                profiles = profiles_response.json()

                # Calculate stats
                total = len(profiles)
                assessed = sum(1 for p in profiles if p.get('assessed'))
                exported = sum(1 for p in profiles if p.get('exported_to_recruiter'))

                scores = [p.get('assessment_score') for p in profiles if p.get('assessment_score')]
                avg_score = sum(scores) / len(scores) if scores else None

                # Score distribution
                score_dist = {
                    '90-100': sum(1 for s in scores if 90 <= s <= 100),
                    '80-89': sum(1 for s in scores if 80 <= s < 90),
                    '70-79': sum(1 for s in scores if 70 <= s < 80),
                    '60-69': sum(1 for s in scores if 60 <= s < 70),
                    '<60': sum(1 for s in scores if s < 60)
                }

                return {
                    'list_id': list_id,
                    'list_name': list_data.get('list_name'),
                    'total_profiles': total,
                    'assessed': assessed,
                    'pending_assessment': total - assessed,
                    'exported': exported,
                    'avg_score': round(avg_score, 1) if avg_score else None,
                    'score_distribution': score_dist,
                    'job_template_id': list_data.get('job_template_id')
                }

            return None
        except Exception as e:
            print(f"Error getting list stats: {e}")
            return None

    # ==================== PROFILE MANAGEMENT ====================

    def add_profile(self, profile_data: Dict) -> Optional[Dict]:
        """Add a profile to a list (quick bookmark)"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/extension_profiles"

            # Prepare data
            data = {
                'linkedin_url': profile_data.get('linkedin_url'),
                'name': profile_data.get('name'),
                'headline': profile_data.get('headline'),
                'current_company': profile_data.get('current_company'),
                'current_title': profile_data.get('current_title'),
                'location': profile_data.get('location'),
                'profile_picture_url': profile_data.get('profile_picture_url'),
                'list_id': profile_data.get('list_id'),
                'added_by': profile_data.get('added_by'),
                'needs_full_fetch': True,  # Always true for extension adds
                'assessed': False  # Not assessed yet
            }

            headers = {
                **self.headers,
                'Prefer': 'return=representation'
            }

            # Try to insert
            response = requests.post(url, json=data, headers=headers)

            if response.ok:
                result = response.json()
                profile = result[0] if result else None

                # Update list counts
                if profile and profile_data.get('list_id'):
                    self._update_list_counts(profile_data.get('list_id'))

                return profile
            else:
                # Check if duplicate
                if 'duplicate' in response.text.lower() or response.status_code == 409:
                    # Try to update existing
                    return self._update_existing_profile(profile_data)
                else:
                    print(f"Failed to add profile: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error adding profile: {e}")
            return None

    def _update_existing_profile(self, profile_data: Dict) -> Optional[Dict]:
        """Update an existing profile if duplicate"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/extension_profiles"

            # Update with new data
            updates = {}
            if profile_data.get('name'):
                updates['name'] = profile_data['name']
            if profile_data.get('headline'):
                updates['headline'] = profile_data['headline']
            if profile_data.get('current_company'):
                updates['current_company'] = profile_data['current_company']
            if profile_data.get('current_title'):
                updates['current_title'] = profile_data['current_title']
            if profile_data.get('list_id'):
                updates['list_id'] = profile_data['list_id']

            params = {'linkedin_url': f'eq.{profile_data["linkedin_url"]}'}
            headers = {**self.headers, 'Prefer': 'return=representation'}

            response = requests.patch(url, json=updates, headers=headers, params=params)

            if response.ok:
                result = response.json()
                return result[0] if result else None

            return None
        except Exception as e:
            print(f"Error updating existing profile: {e}")
            return None

    def get_profiles_in_list(self, list_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all profiles in a list with optional filters"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/extension_profiles"

            params = {
                'list_id': f'eq.{list_id}',
                'order': 'added_at.desc'
            }

            # Apply filters
            if filters:
                if filters.get('assessed') is not None:
                    params['assessed'] = f'eq.{filters["assessed"]}'
                if filters.get('min_score'):
                    params['assessment_score'] = f'gte.{filters["min_score"]}'
                if filters.get('status'):
                    params['status'] = f'eq.{filters["status"]}'

            response = requests.get(url, headers=self.headers, params=params)

            if response.ok:
                return response.json()
            else:
                print(f"Failed to get profiles: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting profiles: {e}")
            return []

    def update_profile(self, profile_id: str, updates: Dict) -> bool:
        """Update a profile"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/extension_profiles"
            params = {'id': f'eq.{profile_id}'}

            response = requests.patch(url, json=updates, headers=self.headers, params=params)

            return response.ok
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    def update_profile_status(self, profile_id: str, status: str) -> bool:
        """Update profile status"""
        return self.update_profile(profile_id, {'status': status})

    def link_assessment(self, profile_id: str, assessment_id: str, assessment_score: float) -> bool:
        """Link a profile to its assessment"""
        updates = {
            'assessed': True,
            'assessment_id': assessment_id,
            'assessment_score': assessment_score
        }
        return self.update_profile(profile_id, updates)

    def mark_exported(self, profile_ids: List[str]) -> bool:
        """Mark profiles as exported to LinkedIn Recruiter"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/extension_profiles"

            updates = {
                'exported_to_recruiter': True,
                'exported_at': datetime.utcnow().isoformat(),
                'status': 'exported'
            }

            # Update each profile
            for profile_id in profile_ids:
                params = {'id': f'eq.{profile_id}'}
                response = requests.patch(url, json=updates, headers=self.headers, params=params)
                if not response.ok:
                    print(f"Failed to mark profile {profile_id} as exported")

            return True
        except Exception as e:
            print(f"Error marking profiles as exported: {e}")
            return False

    # ==================== UTILITY FUNCTIONS ====================

    def _update_list_counts(self, list_id: str):
        """Update profile and assessed counts for a list"""
        try:
            # Call the stored procedure
            url = f"{SUPABASE_URL}/rest/v1/rpc/update_list_counts"
            data = {'list_uuid': list_id}

            response = requests.post(url, json=data, headers=self.headers)

            if not response.ok:
                print(f"Failed to update list counts: {response.status_code}")
        except Exception as e:
            print(f"Error updating list counts: {e}")

    def record_export(self, export_data: Dict) -> Optional[Dict]:
        """Record a CSV export to LinkedIn Recruiter"""
        try:
            url = f"{SUPABASE_URL}/rest/v1/recruiter_exports"

            headers = {
                **self.headers,
                'Prefer': 'return=representation'
            }

            response = requests.post(url, json=export_data, headers=headers)

            if response.ok:
                result = response.json()
                return result[0] if result else None
            else:
                print(f"Failed to record export: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error recording export: {e}")
            return None