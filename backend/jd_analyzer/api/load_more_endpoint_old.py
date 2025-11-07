"""
Load More Candidates API Endpoint with Company Batching

This module adds the /api/jd/domain-load-more-previews endpoint
to enable progressive loading with company batching using SearchSessionManager.
"""

from flask import Blueprint, request, jsonify
import os
import sys
import time
import json
import asyncio
from typing import Dict, Any
from pathlib import Path

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.search_session import SearchSessionManager
from jd_analyzer.api.domain_search import stage2_preview_search
from jd_analyzer.api.session_logger import SessionLogger

# Create blueprint
bp = Blueprint('domain_load_more', __name__, url_prefix='/api/jd')


@bp.route('/domain-load-more-previews', methods=['POST'])
def load_more_previews():
    """
    Load additional preview candidates using company batching.

    This endpoint uses SearchSessionManager to load the next batch of companies
    and fetch candidates progressively, maintaining search quality.

    Request JSON:
    {
        "session_id": "search_abc123",
        "count": 100,  // How many more to load (20/40/100)
        "mode": "company_batch"  // or "seniority_variation" (future)
    }

    Response JSON:
    {
        "success": true,
        "new_profiles": [...],  // New candidates discovered
        "total_discovered": 200,
        "batch_index": 2,
        "remaining_batches": 3,
        "cache_stats": {
            "hits": 85,
            "misses": 15
        },
        "session_stats": {
            "total_discovered": 200,
            "batches_completed": 2,
            "total_batches": 5
        }
    }

    Error Response:
    {
        "success": false,
        "error": "Session not found or no more batches available"
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        count = data.get('count', 100)  # Default to 100 more
        mode = data.get('mode', 'company_batch')

        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400

        print(f"\n📥 Load More Request:")
        print(f"   Session: {session_id}")
        print(f"   Mode: {mode}")
        print(f"   Requesting: {count} more candidates")

        # Load session state
        session_dir = Path(f"logs/domain_search_sessions/{session_id}")
        state_file = session_dir / "pagination_state.json"

        if not state_file.exists():
            # Try loading from Stage 2 preview query
            query_file = session_dir / "02_preview_query.json"
            if not query_file.exists():
                return jsonify({
                    "success": False,
                    "error": "Session not found or expired. Please run a new search."
                }), 404

            # Initialize pagination state from preview query
            import json
            with open(query_file, 'r') as f:
                query_data = json.load(f)

            state = {
                "query": query_data.get("query"),
                "endpoint": query_data.get("input", {}).get("endpoint", "employee_clean"),
                "current_page": 1,
                "total_fetched": current_count,
                "timestamp": time.time()
            }

            # Save initial state
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        else:
            # Load existing state
            import json
            with open(state_file, 'r') as f:
                state = json.load(f)

        # Check session age (expire after 1 hour)
        age = time.time() - state.get("timestamp", 0)
        if age > 3600:
            return jsonify({
                "success": False,
                "error": "Session expired (older than 1 hour). Please run a new search."
            }), 410

        # Calculate next page
        current_page = state.get("current_page", 1)
        next_page = current_page + 1

        # Check limits
        MAX_PAGES = 5  # CoreSignal limit
        MAX_TOTAL = 100  # Our limit

        if next_page > MAX_PAGES:
            return jsonify({
                "success": False,
                "error": f"Maximum pages reached ({MAX_PAGES} pages, {MAX_PAGES * 20} candidates max)",
                "pagination": {
                    "has_more": False,
                    "reason": "api_limit"
                }
            }), 429

        if state.get("total_fetched", 0) >= MAX_TOTAL:
            return jsonify({
                "success": False,
                "error": f"Maximum candidates reached ({MAX_TOTAL} candidates)",
                "pagination": {
                    "has_more": False,
                    "reason": "app_limit"
                }
            }), 429

        # Fetch next page from CoreSignal
        api_key = os.getenv("CORESIGNAL_API_KEY")
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API configuration error"
            }), 500

        # Rate limit protection
        print(f"   ⏱️  Rate limit delay: 2 seconds...")
        time.sleep(2)

        # Make API request
        import requests

        query = state.get("query")
        endpoint = state.get("endpoint", "employee_clean")

        headers = {
            "accept": "application/json",
            "apikey": api_key,
            "Content-Type": "application/json"
        }

        url = f"https://api.coresignal.com/cdapi/v2/{endpoint}/search/es_dsl/preview?page={next_page}"

        print(f"   📡 Fetching page {next_page} from CoreSignal...")

        try:
            response = requests.post(
                url,
                json=query,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                print(f"   ❌ API error: HTTP {response.status_code}")
                return jsonify({
                    "success": False,
                    "error": f"CoreSignal API error: {response.status_code}"
                }), 502

            candidates = response.json()
            print(f"   ✅ Fetched {len(candidates)} candidates from page {next_page}")

            # Update state
            new_total = state.get("total_fetched", current_count) + len(candidates)
            state["current_page"] = next_page
            state["total_fetched"] = new_total
            state["timestamp"] = time.time()

            # Save updated state
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)

            # Check if more pages available
            has_more = (
                len(candidates) == 20 and  # Full page
                next_page < MAX_PAGES and  # Within API limit
                new_total < MAX_TOTAL  # Within our limit
            )

            # Calculate how many more can be loaded
            can_load_next = 0
            if has_more:
                remaining_api = (MAX_PAGES - next_page) * 20
                remaining_app = MAX_TOTAL - new_total
                can_load_next = min(20, remaining_api, remaining_app)

            print(f"   📊 New total: {new_total} candidates")
            print(f"   📄 Pages loaded: {next_page}")
            print(f"   ➡️  Has more: {has_more}")

            return jsonify({
                "success": True,
                "candidates": candidates,
                "pagination": {
                    "new_total": new_total,
                    "has_more": has_more,
                    "max_available": min(MAX_TOTAL, MAX_PAGES * 20),
                    "pages_loaded": next_page,
                    "can_load_count": can_load_next,
                    "remaining_pages": MAX_PAGES - next_page if has_more else 0
                }
            })

        except requests.exceptions.Timeout:
            return jsonify({
                "success": False,
                "error": "CoreSignal API timeout (>30s)"
            }), 504

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to fetch candidates: {str(e)}"
            }), 500

    except Exception as e:
        import traceback
        print(f"❌ Load more endpoint error: {e}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# UI Component Example (React)
UI_COMPONENT_EXAMPLE = """
// LoadMoreButton.jsx
import React, { useState } from 'react';

const LoadMoreButton = ({ sessionId, currentCandidates, onLoadMore }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState(null);

  const handleLoadMore = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/jd/domain-load-more-previews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          current_count: currentCandidates.length,
          load_count: 20
        })
      });

      const data = await response.json();

      if (data.success) {
        // Add new candidates to existing list
        onLoadMore(data.candidates);
        setPagination(data.pagination);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to load more candidates');
    } finally {
      setLoading(false);
    }
  };

  // Don't show button if we've loaded all available
  if (pagination && !pagination.has_more) {
    return (
      <div className="load-more-complete">
        ✅ All available candidates loaded
        ({pagination.new_total} total)
      </div>
    );
  }

  return (
    <div className="load-more-container">
      {error && (
        <div className="error-message">{error}</div>
      )}

      <button
        onClick={handleLoadMore}
        disabled={loading}
        className="load-more-button"
      >
        {loading ? (
          <span>Loading...</span>
        ) : (
          <span>
            Load More Candidates
            {pagination && pagination.can_load_count && (
              <span> (+{pagination.can_load_count})</span>
            )}
          </span>
        )}
      </button>

      {pagination && (
        <div className="pagination-info">
          Showing {currentCandidates.length} of {pagination.max_available} available
          {pagination.remaining_pages > 0 && (
            <span> • {pagination.remaining_pages} more pages available</span>
          )}
        </div>
      )}
    </div>
  );
};

export default LoadMoreButton;
"""

# CSS Styling Example
CSS_EXAMPLE = """
/* Load More Button Styles */
.load-more-container {
  margin: 2rem 0;
  text-align: center;
}

.load-more-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.load-more-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.load-more-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  margin-top: 12px;
  color: #666;
  font-size: 14px;
}

.load-more-complete {
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  color: #0369a1;
  font-weight: 500;
}

.error-message {
  padding: 12px;
  margin-bottom: 16px;
  background: #fee;
  color: #c00;
  border-radius: 6px;
  font-size: 14px;
}
"""


# Integration Instructions
INTEGRATION_GUIDE = """
# Integration Guide: Adding Load More to Domain Search

## Backend Integration

1. Add the endpoint to jd_analyzer/api/endpoints.py:
```python
from .load_more_endpoint import bp as load_more_bp
app.register_blueprint(load_more_bp)
```

2. Update domain_search.py Stage 2 response:
```python
return {
    "stage2_previews": previews[:20],  # Initial 20
    "pagination": {
        "has_more": len(previews) > 20 or total_available > 20,
        "session_id": session_id,
        "total_available": min(100, estimated_total)
    }
}
```

## Frontend Integration

1. Add LoadMoreButton component after preview list
2. Maintain candidates in state
3. Append new candidates when loaded
4. Show loading/error states

## Testing

1. Run initial search (gets 20 candidates)
2. Click "Load More" (gets next 20)
3. Continue until no more available
4. Test error cases (expired session, API limits)
"""

if __name__ == "__main__":
    print(INTEGRATION_GUIDE)