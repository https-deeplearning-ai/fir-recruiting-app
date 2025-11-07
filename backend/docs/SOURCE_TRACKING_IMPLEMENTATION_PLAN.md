# Source Tracking & Real-Time Streaming Implementation Plan

## Overview
Add transparency to company research by tracking and displaying the sources (Tavily URLs, search queries) where companies were discovered. Users will see clickable source links and real-time updates as research progresses.

## Current State Analysis

### What Already Exists
**Backend (`company_research_service.py`):**
- ✅ Tavily URLs are fetched during discovery (line 785)
- ✅ Source fields are created: `source_url`, `source_query`, `source_result_rank`
- ✅ `discovered_via` field shows discovery method
- ❌ BUT: Source URLs are NOT saved to database
- ❌ BUT: Source URLs are NOT included in streaming updates
- ❌ BUT: Source URLs are NOT displayed in frontend

**Database (`target_companies` table):**
- ✅ Has `discovered_via` column
- ❌ Missing: `source_url` column
- ❌ Missing: `source_query` column
- ❌ Missing: `source_result_rank` column

**Frontend (`App.js`):**
- ✅ Shows `discovered_via` badge on company cards
- ❌ Does not display source URLs
- ❌ Does not show search queries used

### Data Flow
```
Tavily Search
    ↓
Discovery (source_url created in memory)
    ↓
Streaming (source_url NOT included)
    ↓
Database (source_url NOT saved)
    ↓
Frontend (source_url never received)
```

---

## Implementation Plan

## Phase 1: Database Schema Update

### 1.1 Add Source Columns to Supabase
**Table:** `target_companies`

**SQL Migration:**
```sql
-- Add source tracking columns
ALTER TABLE target_companies
ADD COLUMN IF NOT EXISTS source_url TEXT,
ADD COLUMN IF NOT EXISTS source_query TEXT,
ADD COLUMN IF NOT EXISTS source_result_rank INTEGER;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_target_companies_source_url ON target_companies(source_url);
```

**Execute in Supabase SQL Editor:**
1. Go to Supabase Dashboard → SQL Editor
2. Paste above SQL
3. Run migration
4. Verify columns exist: `SELECT * FROM target_companies LIMIT 1;`

---

## Phase 2: Backend - Persist Sources

### 2.1 Update `_save_companies()` Method
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/backend/company_research_service.py`

**Location:** Lines 972-991

**Current code:**
```python
data = {
    "jd_id": jd_id,
    "company_name": company.get("name"),
    "company_id": company.get("company_id"),
    "relevance_score": company.get("relevance_score"),
    "relevance_reasoning": company.get("reasoning"),
    "category": db_category,
    "discovered_via": company.get("discovered_via"),
    "company_data": company.get("company_data"),
    "gpt5_analysis": company.get("gpt5_analysis")
}
```

**Add these lines:**
```python
data = {
    "jd_id": jd_id,
    "company_name": company.get("name"),
    "company_id": company.get("company_id"),
    "relevance_score": company.get("relevance_score"),
    "relevance_reasoning": company.get("reasoning"),
    "category": db_category,
    "discovered_via": company.get("discovered_via"),
    "company_data": company.get("company_data"),
    "gpt5_analysis": company.get("gpt5_analysis"),
    # NEW: Add source tracking fields
    "source_url": company.get("source_url"),
    "source_query": company.get("source_query"),
    "source_result_rank": company.get("source_result_rank")
}
```

---

## Phase 3: Backend - Stream Sources to Frontend

### 3.1 Update Discovery Phase Streaming
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/backend/company_research_service.py`

**Location:** Lines 155-171

**Current code:**
```python
discovered_objects = [
    {
        "name": c.get("name") or c.get("company_name"),
        "discovered_via": c.get("discovered_via", "unknown"),
        "company_id": c.get("company_id")
    }
    for c in discovered[:100] if c.get("name") or c.get("company_name")
]
```

**Change to:**
```python
discovered_objects = [
    {
        "name": c.get("name") or c.get("company_name"),
        "discovered_via": c.get("discovered_via", "unknown"),
        "company_id": c.get("company_id"),
        # NEW: Add source fields for UI display
        "source_url": c.get("source_url"),
        "source_query": c.get("source_query"),
        "source_result_rank": c.get("source_result_rank")
    }
    for c in discovered[:100] if c.get("name") or c.get("company_name")
]
```

### 3.2 Update Deep Research Phase Streaming
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/backend/company_research_service.py`

**Location:** Lines 906-951 (in `_deep_research_companies` method)

**Find the streaming update (around line 930):**
```python
await self._update_session_status(jd_id, "running", {
    "phase": "deep_research",
    "action": f"Evaluating {company_name} ({i+1}/{len(companies)})...",
    "current_company": company_name,
    "current_index": i,
    "total": len(companies)
})
```

**Add source info:**
```python
await self._update_session_status(jd_id, "running", {
    "phase": "deep_research",
    "action": f"Evaluating {company_name} ({i+1}/{len(companies)})...",
    "current_company": company_name,
    "current_index": i,
    "total": len(companies),
    # NEW: Stream current source being evaluated
    "current_company_source": company.get("source_url"),
    "current_company_query": company.get("source_query")
})
```

---

## Phase 4: Frontend - Display Sources

### 4.1 Update Discovered Companies Display
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.js`

**Location:** Lines 3576-3626 (Discovered Companies section)

**Find the mapping code:**
```jsx
{discoveredCompanies.map((company, idx) => (
  <div key={idx} className="discovered-company-item">
    <span className="company-name">{company.name}</span>
    {company.discovered_via && (
      <span className={`badge badge-${company.discovered_via}`}>
        {company.discovered_via.replace(/_/g, ' ')}
      </span>
    )}
  </div>
))}
```

**Add source link:**
```jsx
{discoveredCompanies.map((company, idx) => (
  <div key={idx} className="discovered-company-item">
    <span className="company-name">{company.name}</span>
    {company.discovered_via && (
      <span className={`badge badge-${company.discovered_via}`}>
        {company.discovered_via.replace(/_/g, ' ')}
      </span>
    )}
    {/* NEW: Add source link */}
    {company.source_url && (
      <a
        href={company.source_url}
        target="_blank"
        rel="noopener noreferrer"
        className="source-link"
        title={company.source_query || 'View source'}
      >
        📄 Source
      </a>
    )}
  </div>
))}
```

### 4.2 Update Evaluated Companies Display
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.js`

**Location:** Lines 3842-3875 (Company cards by category)

**Find the company card JSX:**
```jsx
<div className="company-result-card" key={idx}>
  <div className="company-header">
    <h4>{company.company_name}</h4>
    <div className="relevance-badge">
      {company.relevance_score}/10
    </div>
  </div>
  <p className="reasoning">{company.relevance_reasoning}</p>
  {/* ... other fields ... */}
</div>
```

**Add source footer:**
```jsx
<div className="company-result-card" key={idx}>
  <div className="company-header">
    <h4>{company.company_name}</h4>
    <div className="relevance-badge">
      {company.relevance_score}/10
    </div>
  </div>
  <p className="reasoning">{company.relevance_reasoning}</p>
  {/* ... other fields ... */}

  {/* NEW: Add source information */}
  {company.source_url && (
    <div className="company-card-footer">
      <div className="source-info">
        <strong>Source:</strong>{' '}
        <a
          href={company.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="source-link-inline"
        >
          {company.source_query || 'Web search result'}
        </a>
        {company.source_result_rank && (
          <span className="source-rank">#{company.source_result_rank}</span>
        )}
      </div>
    </div>
  )}
</div>
```

### 4.3 Add Real-Time Source Display During Research
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.js`

**Location:** Lines 3335-3380 (Server-Sent Events handler)

**Find the progress display section (around line 3520):**
```jsx
{companyResearchStatus && companyResearchStatus.status === 'running' && (
  <div className="research-progress">
    <div className="progress-bar">
      <div
        className="progress-fill"
        style={{width: `${companyResearchStatus.progress_percentage || 0}%`}}
      />
    </div>
    <div className="progress-text">
      {companyResearchStatus.search_config?.current_action || 'Processing...'}
    </div>
  </div>
)}
```

**Add live source display:**
```jsx
{companyResearchStatus && companyResearchStatus.status === 'running' && (
  <div className="research-progress">
    <div className="progress-bar">
      <div
        className="progress-fill"
        style={{width: `${companyResearchStatus.progress_percentage || 0}%`}}
      />
    </div>
    <div className="progress-text">
      {companyResearchStatus.search_config?.current_action || 'Processing...'}
    </div>

    {/* NEW: Show current source being evaluated */}
    {companyResearchStatus.search_config?.current_company_source && (
      <div className="current-evaluation-source">
        <span className="source-label">Evaluating from:</span>{' '}
        <a
          href={companyResearchStatus.search_config.current_company_source}
          target="_blank"
          rel="noopener noreferrer"
          className="live-source-link"
        >
          {companyResearchStatus.search_config.current_company || 'Source'}
        </a>
      </div>
    )}
  </div>
)}
```

---

## Phase 5: CSS Styling

### 5.1 Add Source Link Styles
**File:** `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.css`

**Append to end of file:**
```css
/* ============================================
   Source Tracking Styles
   ============================================ */

/* Source link in discovered companies list */
.source-link {
  color: #667eea;
  text-decoration: none;
  font-size: 0.85em;
  margin-left: 8px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.source-link:hover {
  background-color: #f0f0ff;
  text-decoration: underline;
}

/* Source info in company cards */
.company-card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.source-info {
  font-size: 0.9em;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}

.source-link-inline {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.source-link-inline:hover {
  text-decoration: underline;
}

.source-rank {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: 600;
  color: #4b5563;
}

/* Live source display during research */
.current-evaluation-source {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 3px solid #3b82f6;
  padding: 10px 14px;
  margin-top: 10px;
  border-radius: 4px;
  font-size: 0.9em;
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-label {
  font-weight: 600;
  color: #1e40af;
}

.live-source-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.live-source-link:hover {
  text-decoration: underline;
}
```

---

## Testing Checklist

### Backend Testing
- [ ] Run SQL migration in Supabase
- [ ] Verify columns exist: `source_url`, `source_query`, `source_result_rank`
- [ ] Start company research for a JD
- [ ] Check database after completion:
  ```sql
  SELECT company_name, source_url, source_query, source_result_rank
  FROM target_companies
  ORDER BY created_at DESC
  LIMIT 10;
  ```
- [ ] Verify URLs are populated

### Streaming Testing
- [ ] Start company research
- [ ] Open browser DevTools → Network → EventStream
- [ ] Watch for `current_company_source` in SSE messages
- [ ] Verify source URLs appear in real-time

### Frontend Testing
- [ ] Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
- [ ] Start company research
- [ ] Check "Discovered Companies" section:
  - [ ] Each company shows "📄 Source" link
  - [ ] Clicking link opens Tavily URL in new tab
- [ ] Check "Evaluated Companies" cards:
  - [ ] Footer shows "Source: [search query]"
  - [ ] Source rank (#1, #2, etc.) displayed
  - [ ] Clicking source opens URL
- [ ] Check live progress section:
  - [ ] "Evaluating from: [Source]" appears during deep research
  - [ ] Source link is clickable

### Edge Cases
- [ ] Companies without sources (should not show broken links)
- [ ] Companies from seed expansion (discovered_via = "seed_expansion")
- [ ] Multiple companies from same source URL
- [ ] Very long source queries (should truncate gracefully)

---

## Benefits

**User Benefits:**
1. **Transparency** - See exactly where data comes from
2. **Verification** - Click through to validate research quality
3. **Trust** - Build confidence in AI-generated insights
4. **Real-time** - Watch sources as they're discovered
5. **Learning** - Understand how research queries work

**Developer Benefits:**
1. **Debugging** - Identify bad Tavily results quickly
2. **Quality Control** - Audit source quality
3. **Improvement** - Refine search queries based on results

---

## File Locations Reference

**Backend:**
- `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/backend/company_research_service.py`
  - Line 785: Source URL creation
  - Lines 972-991: Database save method
  - Lines 155-171: Discovery streaming
  - Lines 906-951: Deep research streaming

**Frontend:**
- `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.js`
  - Lines 3576-3626: Discovered companies display
  - Lines 3842-3875: Evaluated companies display
  - Lines 3335-3380: SSE event handler
  - Lines 3520+: Progress display

- `/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/frontend/src/App.css`
  - Append new styles at end

**Database:**
- Supabase Dashboard → SQL Editor
- Table: `target_companies`

---

## Rollback Plan

If issues occur:

1. **Database:** Columns are nullable, can remove later:
   ```sql
   ALTER TABLE target_companies
   DROP COLUMN IF EXISTS source_url,
   DROP COLUMN IF EXISTS source_query,
   DROP COLUMN IF EXISTS source_result_rank;
   ```

2. **Backend:** Remove added fields from code (backward compatible)

3. **Frontend:** Remove source display elements (backward compatible)

---

## Estimated Implementation Time

- **Phase 1 (Database):** 5 minutes
- **Phase 2 (Backend persist):** 10 minutes
- **Phase 3 (Backend streaming):** 15 minutes
- **Phase 4 (Frontend display):** 30 minutes
- **Phase 5 (CSS):** 10 minutes
- **Testing:** 20 minutes

**Total:** ~1.5 hours

---

## Success Criteria

✅ **Implementation Complete When:**
1. New database columns exist and are populated
2. Source URLs stream in real-time during research
3. Discovered companies show clickable source links
4. Evaluated companies show source in footer
5. Live evaluation shows current source being analyzed
6. All links open in new tab and work correctly
7. Styling matches existing UI design

---

## Notes for Next Claude Code Session

- Read this document first
- Start with Phase 1 (database schema)
- Test each phase before moving to next
- Use hard browser refresh to see frontend changes
- Check browser DevTools for SSE messages
- Verify database after backend changes

**Key Insight:** Source data already exists in memory during discovery but is not persisted or displayed. This implementation closes that gap.
