# Query Control & Profile Look-alike Features - Implementation Plan

**Created:** November 4, 2025
**Status:** Planning Phase
**Estimated Time:** 16-25 hours (2-3 weeks part-time)

---

## Overview

Implementation plan for three major features to enhance the JD Analyzer:

1. **Query Regeneration** - Re-run existing queries without re-parsing JD
2. **Query Tweaking** - Simple UI to adjust query parameters (sliders/toggles) + Advanced JSON editor
3. **Profile Look-alike** - Find similar profiles from any candidate card

### User Preferences (from planning session)
- ✅ Priority: Query Regeneration + Simple Tweaking
- ✅ Editor: Both simple mode AND advanced JSON editor
- ✅ Look-alike button: In profile cards
- ✅ Results display: Modal overlay

---

## Phase 1: Query Regeneration Foundation (2-4 hours)

### Backend Changes

**New Endpoint:** `/api/jd/execute-query`

**File:** `backend/jd_analyzer/api_endpoints.py`

```python
@app.route('/api/jd/execute-query', methods=['POST'])
def execute_query():
    """
    Execute a pre-built Elasticsearch DSL query against CoreSignal API.

    Request:
        {
            "query": {...},  # Elasticsearch DSL query
            "preview_limit": 20  # Number of candidates to return
        }

    Response:
        {
            "success": true,
            "profiles": [...],  # Array of candidate profiles
            "total_found": 47,
            "query_used": {...}
        }
    """
    data = request.json
    query = data.get('query')
    preview_limit = data.get('preview_limit', 20)

    # Validate query structure
    if not query or 'query' not in query:
        return jsonify({"success": False, "error": "Invalid query structure"}), 400

    # Execute search
    success, profiles, error_msg = make_coresignal_request_with_retry(
        search_url, {"query": query.get("query")}, headers
    )

    if success:
        return jsonify({
            "success": True,
            "profiles": profiles[:preview_limit],
            "total_found": len(profiles),
            "query_used": query
        })
    else:
        return jsonify({"success": False, "error": error_msg}), 500
```

**New Utility File:** `backend/jd_analyzer/query_executor.py`

```python
class QueryExecutor:
    """Utility class for executing CoreSignal queries"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"

    def execute(self, query, limit=20):
        """Execute query and return profiles"""
        # Reuse existing retry logic
        pass

    def validate_query(self, query):
        """Validate Elasticsearch DSL structure"""
        required_fields = ['query', 'bool']
        # ... validation logic
        pass
```

### Frontend Changes

**File:** `frontend/src/App.js`

**New State Variables:**
```javascript
const [rerunLoading, setRerunLoading] = useState({
  claude: false,
  gpt: false,
  gemini: false
});
const [rerunResults, setRerunResults] = useState({
  claude: null,
  gpt: null,
  gemini: null
});
```

**New Handler:**
```javascript
const handleRerunQuery = async (query, modelName) => {
  setRerunLoading(prev => ({ ...prev, [modelName.toLowerCase()]: true }));

  try {
    const response = await fetch('http://localhost:5001/api/jd/execute-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, preview_limit: 20 })
    });

    const data = await response.json();

    if (data.success) {
      setRerunResults(prev => ({
        ...prev,
        [modelName.toLowerCase()]: data
      }));
      showNotification(`Found ${data.total_found} candidates`, 'success');
    } else {
      showNotification(`Error: ${data.error}`, 'error');
    }
  } catch (error) {
    showNotification('Failed to execute query', 'error');
  } finally {
    setRerunLoading(prev => ({ ...prev, [modelName.toLowerCase()]: false }));
  }
};
```

**UI Addition (in LLM result cards):**
```jsx
{/* After query JSON viewer */}
<div className="query-actions">
  <button
    onClick={() => handleRerunQuery(claudeResult.query, 'Claude')}
    disabled={rerunLoading.claude}
    className="btn-secondary"
  >
    {rerunLoading.claude ? 'Searching...' : '🔄 Re-run Search'}
  </button>
  <button
    onClick={() => navigator.clipboard.writeText(JSON.stringify(claudeResult.query, null, 2))}
    className="btn-secondary"
  >
    📋 Copy Query
  </button>
</div>

{/* Show rerun results if available */}
{rerunResults.claude && (
  <div className="rerun-results">
    <h4>Latest Results ({rerunResults.claude.total_found} candidates)</h4>
    {/* Display candidates */}
  </div>
)}
```

**CSS:** `frontend/src/App.css`
```css
.query-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn-secondary {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-secondary:disabled {
  background: #d6d8db;
  cursor: not-allowed;
}

.rerun-results {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #f8f9fa;
}
```

---

## Phase 2: Simple Query Tweaking (4-6 hours)

### New Component: `frontend/src/components/QueryTweaker.js`

```jsx
import React, { useState, useEffect } from 'react';

const QueryTweaker = ({ originalQuery, onExecute }) => {
  const [modifiedQuery, setModifiedQuery] = useState(originalQuery);
  const [minimumMatch, setMinimumMatch] = useState(
    originalQuery?.query?.bool?.minimum_should_match || 3
  );
  const [enabledClauses, setEnabledClauses] = useState({});

  useEffect(() => {
    // Initialize enabled clauses
    const shouldClauses = originalQuery?.query?.bool?.should || [];
    const initial = {};
    shouldClauses.forEach((clause, idx) => {
      initial[idx] = true;
    });
    setEnabledClauses(initial);
  }, [originalQuery]);

  const handleMinimumMatchChange = (value) => {
    setMinimumMatch(value);
    updateQuery({ minimumMatch: value });
  };

  const handleClauseToggle = (clauseIndex) => {
    setEnabledClauses(prev => ({
      ...prev,
      [clauseIndex]: !prev[clauseIndex]
    }));
    updateQuery({ toggledClause: clauseIndex });
  };

  const updateQuery = ({ minimumMatch: newMatch, toggledClause }) => {
    const query = { ...originalQuery };

    // Update minimum_should_match
    if (newMatch !== undefined) {
      query.query.bool.minimum_should_match = newMatch;
    }

    // Filter enabled clauses
    const allClauses = originalQuery.query.bool.should || [];
    query.query.bool.should = allClauses.filter((_, idx) =>
      enabledClauses[idx] !== false
    );

    setModifiedQuery(query);
  };

  const getClauseLabel = (clause) => {
    // Extract human-readable label from clause
    if (clause.wildcard) {
      const field = Object.keys(clause.wildcard)[0];
      const value = clause.wildcard[field];
      return `${field}: ${value}`;
    }
    if (clause.term) {
      const field = Object.keys(clause.term)[0];
      const value = clause.term[field];
      return `${field}: ${value}`;
    }
    return JSON.stringify(clause).substring(0, 50);
  };

  return (
    <div className="query-tweaker">
      <h4>Adjust Query Parameters</h4>

      {/* Minimum Match Slider */}
      <div className="tweak-control">
        <label>
          Minimum Match: {minimumMatch}
          <span className="help-text">
            (How many criteria must match)
          </span>
        </label>
        <input
          type="range"
          min="1"
          max={originalQuery?.query?.bool?.should?.length || 15}
          value={minimumMatch}
          onChange={(e) => handleMinimumMatchChange(parseInt(e.target.value))}
        />
      </div>

      {/* Clause Toggles */}
      <div className="tweak-control">
        <label>Active Search Criteria:</label>
        <div className="clause-toggles">
          {originalQuery?.query?.bool?.should?.map((clause, idx) => (
            <div key={idx} className="clause-toggle">
              <input
                type="checkbox"
                checked={enabledClauses[idx]}
                onChange={() => handleClauseToggle(idx)}
              />
              <span>{getClauseLabel(clause)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="tweak-actions">
        <button
          onClick={() => onExecute(modifiedQuery)}
          className="btn-primary"
        >
          Apply Changes
        </button>
        <button
          onClick={() => {
            setModifiedQuery(originalQuery);
            setMinimumMatch(originalQuery.query.bool.minimum_should_match);
          }}
          className="btn-secondary"
        >
          Reset to Original
        </button>
      </div>

      {/* Preview Diff */}
      <details className="query-diff">
        <summary>View Modified Query</summary>
        <pre>{JSON.stringify(modifiedQuery, null, 2)}</pre>
      </details>
    </div>
  );
};

export default QueryTweaker;
```

**CSS:** `frontend/src/components/QueryTweaker.css`
```css
.query-tweaker {
  margin: 20px 0;
  padding: 20px;
  border: 2px solid #007bff;
  border-radius: 8px;
  background: #f8f9fa;
}

.tweak-control {
  margin-bottom: 20px;
}

.tweak-control label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
}

.help-text {
  font-size: 0.9em;
  color: #6c757d;
  font-weight: normal;
}

input[type="range"] {
  width: 100%;
  height: 8px;
}

.clause-toggles {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.clause-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.clause-toggle input[type="checkbox"] {
  width: 20px;
  height: 20px;
}

.tweak-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.query-diff {
  margin-top: 20px;
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.query-diff pre {
  font-size: 0.85em;
  overflow-x: auto;
}
```

---

## Phase 3: Advanced JSON Editor (2-4 hours)

### Install Dependencies

```bash
cd frontend
npm install @monaco-editor/react
```

### New Component: `frontend/src/components/AdvancedQueryEditor.js`

```jsx
import React, { useState } from 'react';
import Editor from '@monaco-editor/react';

const AdvancedQueryEditor = ({ originalQuery, onExecute }) => {
  const [queryText, setQueryText] = useState(
    JSON.stringify(originalQuery, null, 2)
  );
  const [validationError, setValidationError] = useState(null);

  const validateQuery = () => {
    try {
      const parsed = JSON.parse(queryText);

      // Check required structure
      if (!parsed.query) {
        throw new Error('Missing "query" field');
      }
      if (!parsed.query.bool) {
        throw new Error('Missing "query.bool" structure');
      }

      setValidationError(null);
      return parsed;
    } catch (error) {
      setValidationError(error.message);
      return null;
    }
  };

  const handleExecute = () => {
    const validated = validateQuery();
    if (validated) {
      onExecute(validated);
    }
  };

  return (
    <div className="advanced-query-editor">
      <h4>Advanced Query Editor</h4>
      <p className="warning-text">
        ⚠️ Edit with caution - invalid queries may return 0 results
      </p>

      <Editor
        height="400px"
        defaultLanguage="json"
        value={queryText}
        onChange={(value) => setQueryText(value)}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on'
        }}
      />

      {validationError && (
        <div className="validation-error">
          ❌ {validationError}
        </div>
      )}

      <div className="editor-actions">
        <button onClick={validateQuery} className="btn-secondary">
          Validate JSON
        </button>
        <button onClick={handleExecute} className="btn-primary">
          Execute Query
        </button>
        <button
          onClick={() => setQueryText(JSON.stringify(originalQuery, null, 2))}
          className="btn-secondary"
        >
          Reset to Original
        </button>
      </div>
    </div>
  );
};

export default AdvancedQueryEditor;
```

**Integration in App.js:**
```jsx
import QueryTweaker from './components/QueryTweaker';
import AdvancedQueryEditor from './components/AdvancedQueryEditor';

// State
const [advancedEditorMode, setAdvancedEditorMode] = useState(false);

// UI
<div className="query-editing-section">
  <div className="mode-toggle">
    <button
      className={!advancedEditorMode ? 'active' : ''}
      onClick={() => setAdvancedEditorMode(false)}
    >
      Simple Mode
    </button>
    <button
      className={advancedEditorMode ? 'active' : ''}
      onClick={() => setAdvancedEditorMode(true)}
    >
      Advanced Editor
    </button>
  </div>

  {advancedEditorMode ? (
    <AdvancedQueryEditor
      originalQuery={claudeResult.query}
      onExecute={(query) => handleRerunQuery(query, 'Claude')}
    />
  ) : (
    <QueryTweaker
      originalQuery={claudeResult.query}
      onExecute={(query) => handleRerunQuery(query, 'Claude')}
    />
  )}
</div>
```

---

## Phase 4: Profile Look-alike Feature (6-8 hours)

### Backend Implementation

**New File:** `backend/jd_analyzer/lookalike_generator.py`

```python
from typing import Dict, Any, List

class LookalikeQueryGenerator:
    """Generate queries to find profiles similar to a given profile"""

    def __init__(self):
        self.logger = None  # TODO: Add logging

    def generate_from_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from profile and build Elasticsearch DSL query.

        Args:
            profile_data: Profile object from CoreSignal API

        Returns:
            Elasticsearch DSL query optimized for finding similar profiles
        """
        should_clauses = []

        # Extract title keywords
        title = profile_data.get('active_experience_title', '')
        title_keywords = self._extract_title_keywords(title)
        for keyword in title_keywords:
            should_clauses.append({
                "wildcard": {"active_experience_title": f"*{keyword.lower()}*"}
            })

        # Extract top 5 skills
        skills = profile_data.get('inferred_skills', [])[:5]
        for skill in skills:
            should_clauses.append({
                "term": {"inferred_skills": skill}
            })

        # Match industry
        industry = profile_data.get('company_industry')
        if industry:
            should_clauses.append({
                "term": {"company_industry": industry}
            })

        # Match location (state-level for flexibility)
        location_state = profile_data.get('location_state')
        if location_state:
            should_clauses.append({
                "term": {"location_state": location_state}
            })

        # Match experience range (±2 years)
        experience_months = profile_data.get('total_experience_duration_months')
        if experience_months:
            should_clauses.append({
                "range": {
                    "total_experience_duration_months": {
                        "gte": max(0, experience_months - 24),
                        "lte": experience_months + 24
                    }
                }
            })

        # Match company size (same bracket)
        company_size = profile_data.get('company_employees_count')
        if company_size:
            bracket_min, bracket_max = self._get_size_bracket(company_size)
            should_clauses.append({
                "range": {
                    "company_employees_count": {
                        "gte": bracket_min,
                        "lte": bracket_max
                    }
                }
            })

        # Match seniority level
        seniority = profile_data.get('active_experience_management_level')
        if seniority:
            should_clauses.append({
                "term": {"active_experience_management_level": seniority}
            })

        # Build query
        query = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": max(3, len(should_clauses) // 3)
                }
            }
        }

        return query

    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from job title"""
        # Remove common words
        stop_words = {'at', 'the', 'of', 'and', 'in', 'for', 'to', 'a', 'an'}
        words = title.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:5]  # Top 5 keywords

    def _get_size_bracket(self, size: int) -> tuple:
        """Get company size bracket (startup, growth, enterprise)"""
        if size < 50:
            return (1, 50)
        elif size < 200:
            return (50, 200)
        elif size < 1000:
            return (200, 1000)
        elif size < 5000:
            return (1000, 5000)
        else:
            return (5000, 50000)
```

**New Endpoint:** `backend/jd_analyzer/api_endpoints.py`

```python
from .lookalike_generator import LookalikeQueryGenerator

lookalike_generator = LookalikeQueryGenerator()

@app.route('/api/jd/find-similar-profiles', methods=['POST'])
def find_similar_profiles():
    """
    Find profiles similar to a given profile.

    Request:
        {
            "profile_data": {...},  # Full profile object
            "limit": 20
        }

    Response:
        {
            "success": true,
            "source_profile": {...},
            "similar_profiles": [...],
            "total_found": 47,
            "query_used": {...}
        }
    """
    data = request.json
    profile_data = data.get('profile_data')
    limit = data.get('limit', 20)

    if not profile_data:
        return jsonify({"success": False, "error": "No profile data provided"}), 400

    # Generate look-alike query
    query = lookalike_generator.generate_from_profile(profile_data)

    # Execute search
    coresignal_api_key = os.getenv("CORESIGNAL_API_KEY")
    search_url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
    headers = {
        "accept": "application/json",
        "apikey": coresignal_api_key,
        "Content-Type": "application/json"
    }

    success, profiles, error_msg = make_coresignal_request_with_retry(
        search_url, {"query": query.get("query")}, headers
    )

    if success:
        # Filter out the source profile
        source_id = profile_data.get('id')
        filtered_profiles = [p for p in profiles if p.get('id') != source_id]

        return jsonify({
            "success": True,
            "source_profile": profile_data,
            "similar_profiles": filtered_profiles[:limit],
            "total_found": len(filtered_profiles),
            "query_used": query
        })
    else:
        return jsonify({"success": False, "error": error_msg}), 500
```

### Frontend Implementation

**New Component:** `frontend/src/components/LookalikeModal.js`

```jsx
import React from 'react';
import './LookalikeModal.css';

const LookalikeModal = ({ isOpen, sourceProfile, similarProfiles, onClose, onViewProfile }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="lookalike-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Profiles Similar to {sourceProfile?.full_name}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Source Profile Reference */}
          <div className="source-profile-card">
            <h3>Reference Profile</h3>
            <div className="profile-summary">
              <strong>{sourceProfile?.full_name}</strong>
              <p>{sourceProfile?.headline || sourceProfile?.generated_headline}</p>
              <p className="profile-location">
                {sourceProfile?.company_name} • {sourceProfile?.location_full}
              </p>
            </div>
          </div>

          {/* Similar Profiles List */}
          <div className="similar-profiles-section">
            <h3>Found {similarProfiles?.length} Similar Profiles</h3>
            <div className="similar-profiles-list">
              {similarProfiles?.map((profile, idx) => (
                <div key={profile.id || idx} className="similar-profile-card">
                  <div className="profile-info">
                    <h4>{profile.full_name}</h4>
                    <p className="profile-title">
                      {profile.active_experience_title || 'N/A'}
                    </p>
                    <p className="profile-company">
                      {profile.company_name} • {profile.location_full}
                    </p>
                    <div className="profile-skills">
                      {profile.inferred_skills?.slice(0, 3).map((skill, i) => (
                        <span key={i} className="skill-tag">{skill}</span>
                      ))}
                    </div>
                  </div>
                  <div className="profile-actions">
                    <button
                      onClick={() => onViewProfile(profile)}
                      className="btn-primary-sm"
                    >
                      View Profile
                    </button>
                    <a
                      href={profile.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary-sm"
                    >
                      LinkedIn →
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default LookalikeModal;
```

**Integration in App.js:**

```jsx
import LookalikeModal from './components/LookalikeModal';

// State
const [lookalikeModalOpen, setLookalikeModalOpen] = useState(false);
const [lookalikeSourceProfile, setLookalikeSourceProfile] = useState(null);
const [lookalikeResults, setLookalikeResults] = useState([]);
const [lookalikeLoading, setLookalikeLoading] = useState(false);

// Handler
const handleFindSimilar = async (profile) => {
  setLookalikeLoading(true);
  setLookalikeSourceProfile(profile);

  try {
    const response = await fetch('http://localhost:5001/api/jd/find-similar-profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_data: profile, limit: 20 })
    });

    const data = await response.json();

    if (data.success) {
      setLookalikeResults(data.similar_profiles);
      setLookalikeModalOpen(true);
      showNotification(`Found ${data.total_found} similar profiles`, 'success');
    } else {
      showNotification(`Error: ${data.error}`, 'error');
    }
  } catch (error) {
    showNotification('Failed to find similar profiles', 'error');
  } finally {
    setLookalikeLoading(false);
  }
};

// UI - Add button to profile cards
<button
  onClick={() => handleFindSimilar(candidate)}
  disabled={lookalikeLoading}
  className="find-similar-btn"
>
  {lookalikeLoading ? 'Searching...' : '🔍 Find Similar'}
</button>

// Modal
<LookalikeModal
  isOpen={lookalikeModalOpen}
  sourceProfile={lookalikeSourceProfile}
  similarProfiles={lookalikeResults}
  onClose={() => setLookalikeModalOpen(false)}
  onViewProfile={(profile) => {
    // Handle viewing profile details
    console.log('View profile:', profile);
  }}
/>
```

---

## Phase 5: Additional Features (Optional)

### Query History (Supabase Storage)

**Table Schema:**
```sql
CREATE TABLE query_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  query JSONB NOT NULL,
  query_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  executed_count INTEGER DEFAULT 1,
  last_executed TIMESTAMP DEFAULT NOW()
);
```

**Endpoint:** `/api/jd/save-query`, `/api/jd/get-query-history`

### Query Templates

**Predefined Templates:**
```javascript
const QUERY_TEMPLATES = {
  'software-engineers-bay-area': {
    name: 'Software Engineers in Bay Area',
    query: {...}
  },
  'senior-managers-series-a': {
    name: 'Senior Managers at Series A',
    query: {...}
  }
};
```

---

## Testing Plan

### Unit Tests
- [ ] Query validation logic
- [ ] Look-alike feature extraction
- [ ] Query modification (tweaker)

### Integration Tests
- [ ] Query regeneration end-to-end
- [ ] Look-alike search with real profiles
- [ ] Advanced editor with various query structures

### Manual Testing
- [ ] Tweak queries and verify results change appropriately
- [ ] Find similar profiles for different seniority levels
- [ ] Test advanced editor with invalid JSON
- [ ] Verify modal UX (open/close/navigation)

---

## Success Metrics

- [ ] Query regeneration reduces time by 50% (no JD re-parsing)
- [ ] Query tweaking improves relevance (user feedback)
- [ ] Look-alike finds 15+ similar profiles per request
- [ ] Advanced editor has <5% error rate
- [ ] No performance degradation (CoreSignal rate limits respected)

---

## Risk Mitigation

### Query Validation
- Backend validates structure before execution
- Frontend shows preview count before full search
- "Undo" button to revert changes

### Rate Limiting
- Throttle re-run requests (max 3 per minute per user)
- Cache results for 5 minutes
- Show warning if too many requests

### Error Handling
- Graceful fallback for invalid queries
- Clear error messages
- Automatic retry with relaxed constraints for 0-result queries

---

## Implementation Schedule

**Week 1:**
- Days 1-2: Query Regeneration
- Days 3-4: Simple Query Tweaking
- Day 5: Testing & Bug Fixes

**Week 2:**
- Days 1-2: Advanced JSON Editor
- Days 3-5: Profile Look-alike Feature

**Week 3:**
- Days 1-2: Query History & Templates
- Days 3-5: Final Testing, Documentation, Polish

---

## Notes

- All features maintain existing sequential execution (no 503 errors)
- UI maintains consistency with current JD Analyzer design
- Backend reuses existing CoreSignal retry logic
- Frontend uses existing notification system
- No database schema changes required (except optional query history)

---

**Status:** Ready for implementation upon approval
**Next Step:** Begin Phase 1 (Query Regeneration)
