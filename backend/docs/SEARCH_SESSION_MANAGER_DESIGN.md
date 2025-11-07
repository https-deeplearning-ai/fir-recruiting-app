# SearchSessionManager Class Design

## Purpose
Manages search sessions for progressive loading with company batching, maintaining state across multiple API calls while integrating with existing Supabase caching infrastructure.

## Class Location
`backend/utils/search_session.py`

## Dependencies
```python
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from supabase import Client
from backend.utils.supabase_storage import get_supabase_client
```

## Class Structure

```python
class SearchSessionManager:
    """
    Manages search sessions with company batching and progressive loading.
    Sessions persist indefinitely until manually cleared.
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize with Supabase client."""
        self.supabase = supabase_client or get_supabase_client()
        self.table_name = "search_sessions"

    # Core Methods
    def create_session(self, search_query: Dict, companies: List[str],
                      batch_size: int = 5) -> Dict[str, Any]
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]
    def update_session(self, session_id: str, updates: Dict) -> bool
    def get_next_batch(self, session_id: str) -> Optional[List[str]]
    def add_discovered_ids(self, session_id: str, employee_ids: List[int]) -> bool
    def mark_profiles_fetched(self, session_id: str, employee_ids: List[int]) -> bool

    # Session Management
    def list_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]
    def clear_session(self, session_id: str) -> bool
    def clear_all_sessions(self) -> int

    # Utility Methods
    def split_companies_into_batches(self, companies: List[str],
                                    batch_size: int = 5) -> List[List[str]]
    def get_session_stats(self, session_id: str) -> Dict[str, Any]
    def update_last_accessed(self, session_id: str) -> None
```

## Method Implementations

### 1. create_session
```python
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
        "is_active": True,
        "last_accessed": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Insert into Supabase
    result = self.supabase.table(self.table_name).insert(session_data).execute()

    return {
        "session_id": session_id,
        "first_batch": company_batches[0] if company_batches else [],
        "total_batches": len(company_batches),
        "batch_size": batch_size
    }
```

### 2. get_next_batch
```python
def get_next_batch(self, session_id: str) -> Optional[List[str]]:
    """
    Get the next company batch for progressive loading.

    Args:
        session_id: Search session identifier

    Returns:
        List of company names for next batch, or None if no more
    """
    session = self.get_session(session_id)
    if not session or not session['is_active']:
        return None

    company_batches = json.loads(session['company_batches'])
    current_index = session['batch_index']

    # Check if we have more batches
    if current_index >= len(company_batches) - 1:
        return None  # No more batches

    # Get next batch and update index
    next_index = current_index + 1
    next_batch = company_batches[next_index]

    # Update session
    self.update_session(session_id, {
        'batch_index': next_index,
        'last_accessed': datetime.utcnow().isoformat()
    })

    return next_batch
```

### 3. add_discovered_ids
```python
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
    session = self.get_session(session_id)
    if not session:
        return False

    # Get existing IDs
    existing_ids = set(session.get('discovered_ids', []))

    # Add new IDs (deduped)
    new_ids = [id for id in employee_ids if id not in existing_ids]
    all_ids = list(existing_ids) + new_ids

    # Update session
    return self.update_session(session_id, {
        'discovered_ids': all_ids,
        'total_discovered': len(all_ids),
        'last_accessed': datetime.utcnow().isoformat()
    })
```

### 4. list_active_sessions
```python
def list_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all active search sessions sorted by last accessed.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session summaries
    """
    result = self.supabase.table(self.table_name)\
        .select("*")\
        .eq('is_active', True)\
        .order('last_accessed', desc=True)\
        .limit(limit)\
        .execute()

    sessions = []
    for row in result.data:
        query = json.loads(row['search_query'])
        company_batches = json.loads(row['company_batches'])

        # Create summary
        sessions.append({
            'session_id': row['session_id'],
            'created_at': row['created_at'],
            'last_accessed': row['last_accessed'],
            'total_discovered': row['total_discovered'],
            'profiles_fetched': len(row.get('profiles_fetched', [])),
            'batch_index': row['batch_index'],
            'total_batches': len(company_batches),
            'query_summary': self._create_query_summary(query)
        })

    return sessions
```

### 5. clear_session
```python
def clear_session(self, session_id: str) -> bool:
    """
    Soft delete a session (mark as inactive).

    Args:
        session_id: Session to clear

    Returns:
        True if successful
    """
    return self.update_session(session_id, {
        'is_active': False,
        'updated_at': datetime.utcnow().isoformat()
    })
```

## Integration Points

### 1. With Stage 2 Preview Search
```python
# In domain_search.py Stage 2
from backend.utils.search_session import SearchSessionManager

def stage2_preview_search(jd_requirements, companies):
    session_manager = SearchSessionManager()

    # Create session with company batches
    session_data = session_manager.create_session(
        search_query=build_query(jd_requirements),
        companies=companies,
        batch_size=5
    )

    # Execute first batch
    first_batch_companies = session_data['first_batch']
    results = execute_preview_search(first_batch_companies, jd_requirements)

    # Store discovered IDs
    employee_ids = [r['employee_id'] for r in results]
    session_manager.add_discovered_ids(session_data['session_id'], employee_ids)

    return {
        'session_id': session_data['session_id'],
        'profiles': results,
        'total_batches': session_data['total_batches']
    }
```

### 2. With Load More Endpoint
```python
# In api_endpoints.py
@jd_analyzer_bp.route('/load-more-previews', methods=['POST'])
def load_more_previews():
    data = request.json
    session_id = data['session_id']
    count = data.get('count', 100)

    session_manager = SearchSessionManager()

    # Get next company batch
    next_batch = session_manager.get_next_batch(session_id)
    if not next_batch:
        return jsonify({'message': 'No more batches available'}), 404

    # Get original query from session
    session = session_manager.get_session(session_id)
    query = json.loads(session['search_query'])

    # Execute search with next batch
    results = execute_preview_search(next_batch, query)

    # Add to discovered IDs
    new_ids = [r['employee_id'] for r in results]
    session_manager.add_discovered_ids(session_id, new_ids)

    return jsonify({
        'new_profiles': results,
        'total_discovered': session['total_discovered'] + len(results),
        'batch_index': session['batch_index'] + 1
    })
```

### 3. With Caching Layer
```python
# Integration with existing caching
from backend.utils.supabase_storage import get_stored_profile, store_profile_data

def fetch_profiles_for_session(session_id, count=20):
    """Fetch profiles using session IDs with caching."""
    session_manager = SearchSessionManager()
    session = session_manager.get_session(session_id)

    discovered_ids = session['discovered_ids']
    fetched_ids = session.get('profiles_fetched', [])

    # Get unfetched IDs
    unfetched = [id for id in discovered_ids if id not in fetched_ids][:count]

    profiles = []
    cache_hits = 0

    for emp_id in unfetched:
        # Check cache first
        cache_key = f"id:{emp_id}"
        cached = get_stored_profile(cache_key)

        if cached:
            profiles.append(cached['profile_data'])
            cache_hits += 1
        else:
            # Fetch from API
            profile = fetch_employee_by_id(emp_id)
            profiles.append(profile)

            # Store in cache
            store_profile_data(cache_key, profile)

    # Mark as fetched
    session_manager.mark_profiles_fetched(session_id, unfetched)

    return {
        'profiles': profiles,
        'cache_stats': {
            'hits': cache_hits,
            'misses': len(unfetched) - cache_hits,
            'hit_rate': cache_hits / len(unfetched) if unfetched else 0
        }
    }
```

## Database Schema Requirements

```sql
-- Already defined in COMPANY_BATCHING_CHANGES.md
CREATE TABLE IF NOT EXISTS search_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    search_query JSONB NOT NULL,
    company_batches JSONB NOT NULL,
    discovered_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    profiles_fetched INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    total_discovered INTEGER DEFAULT 0,
    batch_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_accessed TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Error Handling

```python
class SessionNotFoundError(Exception):
    """Raised when session doesn't exist."""
    pass

class SessionInactiveError(Exception):
    """Raised when trying to use inactive session."""
    pass

class BatchExhaustedError(Exception):
    """Raised when no more batches available."""
    pass
```

## Testing Strategy

```python
# test_search_session.py
def test_session_creation():
    """Test creating a new session with company batches."""
    manager = SearchSessionManager()
    companies = ["Google", "Meta", "Apple", "Amazon", "Microsoft",
                "OpenAI", "Anthropic", "Cohere", "Hugging Face", "Stability AI"]

    session = manager.create_session(
        search_query={"role": "engineer"},
        companies=companies,
        batch_size=5
    )

    assert session['total_batches'] == 2
    assert len(session['first_batch']) == 5
    assert session['session_id'].startswith('search_')

def test_progressive_loading():
    """Test getting next batches progressively."""
    manager = SearchSessionManager()
    session_id = "test_session_123"

    # Get first batch
    batch1 = manager.get_next_batch(session_id)
    assert batch1 is not None

    # Get second batch
    batch2 = manager.get_next_batch(session_id)
    assert batch2 is not None
    assert batch2 != batch1

    # No more batches
    batch3 = manager.get_next_batch(session_id)
    assert batch3 is None

def test_deduplication():
    """Test that duplicate IDs are handled."""
    manager = SearchSessionManager()
    session_id = "test_session_456"

    # Add IDs
    manager.add_discovered_ids(session_id, [1, 2, 3])
    manager.add_discovered_ids(session_id, [3, 4, 5])  # 3 is duplicate

    session = manager.get_session(session_id)
    assert session['discovered_ids'] == [1, 2, 3, 4, 5]
    assert session['total_discovered'] == 5
```

## Performance Considerations

1. **Batch Size**: 5 companies per batch balances diversity vs API calls
2. **Deduplication**: Set-based operations for O(1) lookups
3. **Caching**: 90% cache hit rate target maintained
4. **Session Storage**: JSONB columns for flexible query storage
5. **Indexing**: Indexes on session_id, is_active, last_accessed

## Summary

The SearchSessionManager provides:
- Company batching for progressive loading
- Indefinite session persistence with manual cleanup
- Full integration with existing Supabase caching
- Deduplication of discovered employee IDs
- Session management and listing capabilities
- Thread-safe operations for concurrent requests