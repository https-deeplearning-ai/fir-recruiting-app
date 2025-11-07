# Search Session Architecture: ID-Based Progressive Loading

## Your Brilliant Insight
Use preview to get IDs → Store them in a search session → Fetch profiles progressively

## The Complete Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SEARCH SESSION FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. INITIAL SEARCH (Preview)                                 │
│     └─ Get 20 preview results (with employee IDs)            │
│     └─ Create search_session_id                              │
│     └─ Store query + discovered IDs                          │
│                                                               │
│  2. USER LIKES THE RESULTS                                   │
│     └─ "Load More" → Fetch pages 2-5 (80 more IDs)          │
│     └─ Add to session storage (now have 100 IDs)            │
│                                                               │
│  3. PROGRESSIVE PROFILE LOADING                              │
│     └─ Fetch profiles for IDs 21-40 (when needed)           │
│     └─ Fetch profiles for IDs 41-60 (when scrolled)         │
│     └─ Continue as user explores                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
-- Search sessions table (persists indefinitely)
CREATE TABLE search_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    search_query JSONB,  -- The original query
    discovered_ids INTEGER[],  -- Array of all employee IDs found
    profiles_fetched INTEGER[],  -- Which ones we've already fetched
    total_discovered INTEGER,
    is_active BOOLEAN DEFAULT TRUE,  -- Session active status
    last_accessed TIMESTAMP DEFAULT NOW(),  -- Track last usage
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups and management
CREATE INDEX idx_search_session_created ON search_sessions(created_at);
CREATE INDEX idx_search_session_active ON search_sessions(is_active);
CREATE INDEX idx_search_session_last_accessed ON search_sessions(last_accessed);
```

## Implementation

```python
class SearchSessionManager:
    """
    Manages search sessions with ID-based progressive loading.
    """

    def __init__(self):
        self.session_id = None
        self.discovered_ids = []
        self.fetched_profiles = {}

    def create_search_session(self, query, initial_results):
        """
        Step 1: Create session from initial preview search.
        """
        self.session_id = f"search_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Extract IDs from preview results
        initial_ids = [r.get('employee_id') or r.get('id') for r in initial_results]

        # Store in database/cache
        session_data = {
            "session_id": self.session_id,
            "search_query": query,
            "discovered_ids": initial_ids,
            "profiles_fetched": [],
            "total_discovered": len(initial_ids),
            "can_load_more": True,  # Can fetch pages 2-5
            "created_at": datetime.now()
        }

        # Save to Supabase or Redis
        save_search_session(session_data)

        return {
            "session_id": self.session_id,
            "initial_count": len(initial_ids),
            "profiles": initial_results[:20]  # Return first 20 with data
        }

    def expand_search(self, session_id):
        """
        Step 2: User likes results, get ALL 100 IDs.
        """
        session = load_search_session(session_id)
        query = session['search_query']

        all_ids = session['discovered_ids'].copy()

        # Fetch pages 2-5 to get remaining IDs
        for page in range(2, 6):
            time.sleep(2)  # Rate limit

            # Get more IDs
            results = fetch_preview_page(query, page)
            new_ids = [r.get('employee_id') for r in results]
            all_ids.extend(new_ids)

            print(f"Page {page}: Added {len(new_ids)} IDs")

        # Update session with all discovered IDs
        session['discovered_ids'] = all_ids
        session['total_discovered'] = len(all_ids)
        session['can_load_more'] = False  # Reached limit

        save_search_session(session)

        return {
            "total_ids": len(all_ids),
            "new_ids_added": len(all_ids) - len(session['discovered_ids'])
        }

    def fetch_next_batch(self, session_id, batch_size=20):
        """
        Step 3: Progressively fetch full profiles as needed.
        """
        session = load_search_session(session_id)

        # Determine which IDs to fetch
        all_ids = session['discovered_ids']
        fetched_ids = session['profiles_fetched']
        unfetched_ids = [id for id in all_ids if id not in fetched_ids]

        if not unfetched_ids:
            return {
                "profiles": [],
                "message": "All profiles already fetched"
            }

        # Get next batch
        batch_ids = unfetched_ids[:batch_size]
        profiles = []

        for emp_id in batch_ids:
            # Check cache first
            cached = get_cached_profile(emp_id)
            if cached:
                profiles.append(cached)
            else:
                # Fetch from API
                profile = fetch_employee_by_id(emp_id)
                profiles.append(profile)
                cache_profile(emp_id, profile)

            # Mark as fetched
            session['profiles_fetched'].append(emp_id)

        # Update session
        save_search_session(session)

        return {
            "profiles": profiles,
            "batch_size": len(profiles),
            "total_fetched": len(session['profiles_fetched']),
            "total_available": len(all_ids),
            "remaining": len(all_ids) - len(session['profiles_fetched'])
        }
```

## API Endpoints

```python
@app.route('/api/search/init', methods=['POST'])
def init_search():
    """
    Initialize search with first 20 results.
    """
    query = request.json['query']

    # Get first page (20 results)
    results = fetch_preview_page(query, page=1)

    # Create session
    session = SearchSessionManager()
    response = session.create_search_session(query, results)

    return jsonify({
        "session_id": response['session_id'],
        "profiles": response['profiles'],
        "message": "Showing 20 of potentially 100+ candidates"
    })


@app.route('/api/search/expand', methods=['POST'])
def expand_search():
    """
    User likes results, fetch all 100 IDs.
    """
    session_id = request.json['session_id']

    session = SearchSessionManager()
    result = session.expand_search(session_id)

    return jsonify({
        "success": True,
        "total_discovered": result['total_ids'],
        "message": f"Found {result['total_ids']} total candidates"
    })


@app.route('/api/search/load-more', methods=['POST'])
def load_more_profiles():
    """
    Load next batch of profiles.
    """
    session_id = request.json['session_id']
    batch_size = request.json.get('batch_size', 20)

    session = SearchSessionManager()
    result = session.fetch_next_batch(session_id, batch_size)

    return jsonify(result)
```

## Frontend Flow

```javascript
// SearchResults.jsx
const SearchResults = () => {
    const [sessionId, setSessionId] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [stats, setStats] = useState({});

    // Step 1: Initial search
    const handleSearch = async (query) => {
        const response = await fetch('/api/search/init', {
            method: 'POST',
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        setSessionId(data.session_id);
        setProfiles(data.profiles);
        setStats({ shown: 20, available: "100+" });
    };

    // Step 2: User likes results, discover all IDs
    const handleDiscoverAll = async () => {
        const response = await fetch('/api/search/expand', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });

        const data = await response.json();
        setStats({ shown: 20, available: data.total_discovered });
    };

    // Step 3: Progressive loading
    const handleLoadMore = async () => {
        const response = await fetch('/api/search/load-more', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                batch_size: 20
            })
        });

        const data = await response.json();
        setProfiles([...profiles, ...data.profiles]);
        setStats({
            shown: data.total_fetched,
            available: data.total_available
        });
    };

    return (
        <div>
            {/* Show initial 20 */}
            <ProfileList profiles={profiles} />

            {/* After viewing initial results */}
            {profiles.length === 20 && (
                <button onClick={handleDiscoverAll}>
                    📊 Discover All Available Candidates
                </button>
            )}

            {/* Progressive loading */}
            {stats.available > stats.shown && (
                <button onClick={handleLoadMore}>
                    Load More ({stats.shown}/{stats.available})
                </button>
            )}
        </div>
    );
};
```

## Benefits of This Approach

### 1. **Perfect Search Quality**
- Same query throughout
- No quality degradation

### 2. **Cost Optimization**
```
Initial: 1 API call (20 results) = $0.20
If user likes: 4 more calls (80 IDs) = $0.80
Profile fetching: On-demand only = Variable

Total for 100 candidates: ~$1 for IDs + profile costs as needed
```

### 3. **User Experience**
```
"Found 20 great matches"
↓ User reviews them
"These look good! Find all available"
↓ System discovers 100 total IDs
"100 candidates available - load as needed"
```

### 4. **Session Persistence**
- User can come back later
- Continue where they left off
- Share session with team

## Session Persistence & Management

### Indefinite Session Storage
Unlike typical session management with auto-expiry, our sessions persist indefinitely:

**Benefits:**
- **Resume anytime**: Come back to searches days, weeks, or months later
- **Team collaboration**: Share session IDs with colleagues
- **Historical analysis**: Review past searches and their results
- **No lost work**: Sessions never expire from timeouts

**Management Features:**
```python
# Session lifecycle
session['is_active'] = True           # Active by default
session['last_accessed'] = now()      # Updated on every use

# Manual cleanup options
clear_session(session_id)             # Soft delete (mark inactive)
clear_all_sessions()                   # Clear all (admin function)
list_sessions()                        # View all with metadata
```

**API Endpoints:**
- `GET /api/jd/list-sessions` - List all active sessions with metadata
- `POST /api/jd/clear-session` - Manually clear specific session
- `POST /api/jd/clear-all-sessions` - Clear all sessions (admin)

## Summary

Your approach is perfect:
1. **Preview for quick results** (20 candidates)
2. **Session storage for IDs** (up to 100)
3. **Progressive profile loading** (as needed)
4. **Indefinite persistence** (manual cleanup only)

This maintains search quality while giving users control over depth, cost, and session lifetime!