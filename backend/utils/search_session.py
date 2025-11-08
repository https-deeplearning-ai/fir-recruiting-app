"""
Search Session Manager - Company Batching and Progressive Loading

This module manages search sessions for the domain search pipeline,
enabling progressive loading with company batching to overcome
CoreSignal's 100-result limit while maintaining search quality.

Key Features:
    - Company batching (5 companies per batch)
    - Indefinite session persistence (manual cleanup only)
    - Progressive ID discovery with deduplication
    - Integration with existing Supabase caching
    - Session management and listing

Usage:
    from utils.search_session import SearchSessionManager

    # Create session with company batches
    manager = SearchSessionManager()
    session_data = manager.create_session(
        search_query=query,
        companies=companies,
        batch_size=5
    )

    # Get next batch for progressive loading
    next_batch = manager.get_next_batch(session_id)

    # Add discovered IDs
    manager.add_discovered_ids(session_id, employee_ids)
"""

import os
import json
import time
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class SearchSessionManager:
    """
    Manages search sessions with company batching and progressive loading.
    Sessions persist indefinitely until manually cleared.
    """

    def __init__(self):
        """Initialize with Supabase connection settings."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.table_name = "search_sessions"

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables required")

    def _get_headers(self) -> Dict[str, str]:
        """Get standard Supabase headers for REST API requests."""
        return {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'  # Return created/updated data
        }

    def _handle_error(self, operation: str, error: Exception, silent: bool = False) -> None:
        """Handle errors with logging."""
        if not silent:
            print(f"⚠️  SearchSession {operation} error: {str(error)}")

    def split_companies_into_batches(self, companies: List[str],
                                    batch_size: int = 5) -> List[List[str]]:
        """
        Split companies into smaller batches for diverse results.

        Args:
            companies: List of all companies to search
            batch_size: Number of companies per batch (default 5)

        Returns:
            List of company batches
        """
        batches = []
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            batches.append(batch)

        return batches

    def create_session(self, search_query: Dict, companies: List[str],
                      batch_size: int = 5) -> Dict[str, Any]:
        """
        Create a new search session with company batches.

        Args:
            search_query: Original CoreSignal query parameters
            companies: List of all companies to search
            batch_size: Number of companies per batch (default 5)

        Returns:
            Session details including session_id and first batch
        """
        try:
            # Generate unique session ID
            session_id = f"search_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Split companies into batches
            company_batches = self.split_companies_into_batches(companies, batch_size)

            # Create session record
            session_data = {
                "session_id": session_id,
                "search_query": json.dumps(search_query),
                "company_batches": json.dumps(company_batches),
                "discovered_ids": [],
                "profiles_fetched": [],
                "total_discovered": 0,
                "batch_index": 0,
                "employee_ids": [],  # NEW: List of all employee IDs from search (up to 1000)
                "profiles_offset": 0,  # NEW: Current offset for profile pagination
                "total_employee_ids": 0,  # NEW: Total count of employee IDs for progress tracking
                "is_active": True,
                "last_accessed": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Insert into Supabase
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            response = requests.post(url, json=session_data, headers=self._get_headers())

            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create session: {response.text}")

            print(f"✅ Created search session: {session_id}")
            print(f"   Total batches: {len(company_batches)} ({len(companies)} companies)")

            return {
                "session_id": session_id,
                "first_batch": company_batches[0] if company_batches else [],
                "total_batches": len(company_batches),
                "batch_size": batch_size
            }

        except Exception as e:
            self._handle_error("create_session", e)
            raise

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Search session identifier

        Returns:
            Session data or None if not found
        """
        try:
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {'session_id': f'eq.{session_id}'}

            response = requests.get(url, params=params, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0]

            return None

        except Exception as e:
            self._handle_error("get_session", e, silent=True)
            return None

    def update_session(self, session_id: str, updates: Dict) -> bool:
        """
        Update session data.

        Args:
            session_id: Session to update
            updates: Fields to update

        Returns:
            True if successful
        """
        try:
            # Always update the updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()

            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {'session_id': f'eq.{session_id}'}

            response = requests.patch(url, params=params, json=updates,
                                     headers=self._get_headers())

            return response.status_code in [200, 204]

        except Exception as e:
            self._handle_error("update_session", e)
            return False

    def get_next_batch(self, session_id: str) -> Optional[List[str]]:
        """
        Get the next company batch for progressive loading.

        Args:
            session_id: Search session identifier

        Returns:
            List of company names for next batch, or None if no more
        """
        try:
            session = self.get_session(session_id)
            if not session or not session.get('is_active'):
                return None

            company_batches = json.loads(session['company_batches'])
            current_index = session.get('batch_index', 0)

            # Check if we have more batches
            if current_index >= len(company_batches) - 1:
                print(f"ℹ️  No more batches for session {session_id}")
                return None

            # Get next batch and update index
            next_index = current_index + 1
            next_batch = company_batches[next_index]

            # Update session
            self.update_session(session_id, {
                'batch_index': next_index,
                'last_accessed': datetime.utcnow().isoformat()
            })

            print(f"📦 Retrieved batch {next_index + 1}/{len(company_batches)}: {next_batch}")

            return next_batch

        except Exception as e:
            self._handle_error("get_next_batch", e)
            return None

    def add_discovered_ids(self, session_id: str, employee_ids: List[int]) -> bool:
        """
        Add newly discovered employee IDs to session.
        Handles deduplication automatically.

        Args:
            session_id: Search session identifier
            employee_ids: List of employee IDs to add

        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Get existing IDs
            existing_ids = set(session.get('discovered_ids', []))

            # Add new IDs (deduped)
            new_ids = [id for id in employee_ids if id not in existing_ids]
            all_ids = list(existing_ids) + new_ids

            # Update session
            success = self.update_session(session_id, {
                'discovered_ids': all_ids,
                'total_discovered': len(all_ids),
                'last_accessed': datetime.utcnow().isoformat()
            })

            if success:
                print(f"✅ Added {len(new_ids)} new IDs to session (total: {len(all_ids)})")

            return success

        except Exception as e:
            self._handle_error("add_discovered_ids", e)
            return False

    def mark_profiles_fetched(self, session_id: str, employee_ids: List[int]) -> bool:
        """
        Mark employee IDs as having their profiles fetched.

        Args:
            session_id: Search session identifier
            employee_ids: List of employee IDs that were fetched

        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Get existing fetched IDs
            existing_fetched = set(session.get('profiles_fetched', []))

            # Add newly fetched IDs
            all_fetched = list(existing_fetched.union(set(employee_ids)))

            # Update session
            return self.update_session(session_id, {
                'profiles_fetched': all_fetched,
                'last_accessed': datetime.utcnow().isoformat()
            })

        except Exception as e:
            self._handle_error("mark_profiles_fetched", e)
            return False

    def store_employee_ids(self, session_id: str, employee_ids: List[int]) -> bool:
        """
        Store the complete list of employee IDs from search (up to 1000).

        This enables the search/collect pattern where we:
        1. Get all IDs upfront (this method)
        2. Fetch profiles in batches of 20 (use get_next_profile_batch_info)

        Args:
            session_id: Search session identifier
            employee_ids: List of all employee IDs from search

        Returns:
            True if successful
        """
        try:
            success = self.update_session(session_id, {
                'employee_ids': employee_ids,
                'total_employee_ids': len(employee_ids),
                'profiles_offset': 0,  # Reset offset when storing new IDs
                'last_accessed': datetime.utcnow().isoformat()
            })

            if success:
                print(f"✅ Stored {len(employee_ids)} employee IDs in session")

            return success

        except Exception as e:
            self._handle_error("store_employee_ids", e)
            return False

    def get_next_profile_batch_info(self, session_id: str, batch_size: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get information about the next batch of profiles to fetch.

        Returns the employee IDs for the next batch and pagination metadata.

        Args:
            session_id: Search session identifier
            batch_size: Number of profiles per batch (default: 20)

        Returns:
            Dict with 'employee_ids', 'start_index', 'end_index', 'remaining'
            or None if no more profiles to fetch
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return None

            all_employee_ids = session.get('employee_ids', [])
            current_offset = session.get('profiles_offset', 0)

            # Check if we have more profiles to fetch
            if current_offset >= len(all_employee_ids):
                print(f"ℹ️  No more profiles to fetch for session {session_id}")
                return None

            # Calculate batch slice
            end_index = min(current_offset + batch_size, len(all_employee_ids))
            batch_ids = all_employee_ids[current_offset:end_index]
            remaining = len(all_employee_ids) - end_index

            return {
                'employee_ids': batch_ids,
                'start_index': current_offset,
                'end_index': end_index,
                'remaining': remaining,
                'total': len(all_employee_ids),
                'batch_size': len(batch_ids)
            }

        except Exception as e:
            self._handle_error("get_next_profile_batch_info", e)
            return None

    def increment_profiles_offset(self, session_id: str, increment: int = 20) -> bool:
        """
        Increment the profiles_offset after fetching a batch.

        Args:
            session_id: Search session identifier
            increment: Number of profiles fetched (default: 20)

        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            new_offset = session.get('profiles_offset', 0) + increment

            success = self.update_session(session_id, {
                'profiles_offset': new_offset,
                'last_accessed': datetime.utcnow().isoformat()
            })

            if success:
                print(f"✅ Incremented profiles_offset to {new_offset}")

            return success

        except Exception as e:
            self._handle_error("increment_profiles_offset", e)
            return False

    def list_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all active search sessions sorted by last accessed.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        try:
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {
                'is_active': 'eq.true',
                'order': 'last_accessed.desc',
                'limit': str(limit)
            }

            response = requests.get(url, params=params, headers=self._get_headers())

            if response.status_code != 200:
                return []

            sessions = []
            for row in response.json():
                query = json.loads(row['search_query'])
                company_batches = json.loads(row['company_batches'])

                # Create summary
                sessions.append({
                    'session_id': row['session_id'],
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed'],
                    'total_discovered': row.get('total_discovered', 0),
                    'profiles_fetched': len(row.get('profiles_fetched', [])),
                    'batch_index': row.get('batch_index', 0),
                    'total_batches': len(company_batches),
                    'query_summary': self._create_query_summary(query, company_batches)
                })

            return sessions

        except Exception as e:
            self._handle_error("list_active_sessions", e)
            return []

    def clear_session(self, session_id: str) -> bool:
        """
        Soft delete a session (mark as inactive).

        Args:
            session_id: Session to clear

        Returns:
            True if successful
        """
        try:
            success = self.update_session(session_id, {
                'is_active': False
            })

            if success:
                print(f"✅ Cleared session: {session_id}")

            return success

        except Exception as e:
            self._handle_error("clear_session", e)
            return False

    def clear_all_sessions(self) -> int:
        """
        Clear all active sessions.

        Returns:
            Number of sessions cleared
        """
        try:
            # Get all active sessions
            active_sessions = self.list_active_sessions(limit=1000)
            cleared_count = 0

            for session in active_sessions:
                if self.clear_session(session['session_id']):
                    cleared_count += 1

            print(f"✅ Cleared {cleared_count} sessions")
            return cleared_count

        except Exception as e:
            self._handle_error("clear_all_sessions", e)
            return 0

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session statistics
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return {}

            company_batches = json.loads(session['company_batches'])
            discovered_ids = session.get('discovered_ids', [])
            profiles_fetched = session.get('profiles_fetched', [])

            return {
                'session_id': session_id,
                'is_active': session.get('is_active', False),
                'created_at': session['created_at'],
                'last_accessed': session.get('last_accessed'),
                'total_companies': sum(len(batch) for batch in company_batches),
                'batches_completed': session.get('batch_index', 0) + 1,
                'total_batches': len(company_batches),
                'discovered_ids': len(discovered_ids),
                'profiles_fetched': len(profiles_fetched),
                'profiles_remaining': len(discovered_ids) - len(profiles_fetched),
                'completion_percentage': round((len(profiles_fetched) / len(discovered_ids) * 100), 1)
                                       if discovered_ids else 0
            }

        except Exception as e:
            self._handle_error("get_session_stats", e)
            return {}

    def _create_query_summary(self, query: Dict, company_batches: List) -> str:
        """Create a human-readable summary of the search query."""
        try:
            # Extract key information
            companies = [c for batch in company_batches[:3] for c in batch][:5]
            companies_str = ', '.join(companies[:3])
            if len(companies) > 3:
                companies_str += f" (+{len(companies) - 3} more)"

            # Build summary
            summary_parts = []
            if companies_str:
                summary_parts.append(f"Companies: {companies_str}")

            # Add more query details if available
            if isinstance(query, dict):
                if 'role' in query:
                    summary_parts.append(f"Role: {query['role']}")
                if 'location' in query:
                    summary_parts.append(f"Location: {query['location']}")

            return " | ".join(summary_parts) if summary_parts else "Search session"

        except:
            return "Search session"


# Export main class
__all__ = ['SearchSessionManager']