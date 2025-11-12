# Session Progress: UI Integration for Domain Search

**Date:** November 11, 2025
**Status:** ✅ Backend Complete | 🔄 Frontend Pending
**Branch:** wip/domain-search

---

## ✅ COMPLETED: Backend Fixes

### Issue 1: Fixed NoneType Error in Title Fields
**Location:** `domain_search.py:1131, 1134`
**Fix:** Changed `.get('title', '').lower()` to `(candidate.get('title') or '').lower()`
**Impact:** Prevents crash when title is explicitly None

### Issue 2: Added Profile Field Normalization
**Location:** `domain_search.py:858-915` (new function `normalize_profile_fields()`)
**What it does:**
- Converts CoreSignal fields → Frontend fields
- `full_name` → `name`
- `headline` → `title`
- `profile_url` → `linkedin_url`
- Calculates `current_company` from experience
- Calculates `years_experience` from experience history

### Issue 3: Applied Normalization to BOTH Code Paths
**Locations:**
- Fresh search: `domain_search.py:1273`
- Cached results: `domain_search.py:1921`

**Impact:** ALL API responses now include normalized fields, regardless of cache status

### Test Results:
```
✅ BACKEND API TEST - NORMALIZED FIELDS
Total profiles: 85
From cache: True

First Candidate - Normalized Fields:
  name: K V Vijay Girish
  title: Applied Scientist @Amazon AGI | Ex-Observe.AI...
  company: Amazon
  location: Bengaluru, Karnataka, India
  years_exp: 0
  linkedin_url: https://www.linkedin.com/in/k-v-vijay-girish-b85a3714
```

---

## 🔄 PENDING: Frontend Implementation

### Phase 2: Update React State (30 min)

**File:** `frontend/src/App.js`

**Current state structure is outdated.** Need to update around lines 162-175 to match backend response:

```javascript
const [domainSearchResults, setDomainSearchResults] = useState({
  session_id: null,
  status: 'idle',

  // Stage 1: Company Discovery
  stage1_companies: [],
  companies_discovered: 0,

  // Stage 2: Preview (100 FREE profiles)
  stage2_previews: [],
  total_previews_found: 0,
  relevance_score: 0.0,
  location_distribution: {},
  filter_precision: 0.0,
  role_keywords_used: [],
  search_method: 'experience_based',

  // Stage 3: Full Collection
  stage3_profiles: [],
  profiles_offset: 100,
  credits_used: 0,
  cache_stats: {cached: 0, fetched: 0, failed: 0}
});
```

**Also update handler (~line 2150):**
```javascript
const handleDomainSearch = async (jdRequirements) => {
  // ... existing code ...
  const data = await response.json();

  setDomainSearchResults({
    session_id: data.session_id,
    status: 'stage2_complete',
    stage1_companies: data.stage1_companies || [],
    stage2_previews: data.stage2_previews || [],
    total_previews_found: data.total_previews_found || 0,
    relevance_score: data.relevance_score || 0,
    location_distribution: data.location_distribution || {},
    filter_precision: data.filter_precision || 0,
    role_keywords_used: data.role_keywords_used || [],
    search_method: data.search_method || 'experience_based',
    profiles_offset: 100,
    credits_used: 0
  });
};
```

---

### Phase 3: Create UI Components (2.5 hours)

#### Component 1: PreviewCard.js
**File:** `frontend/src/components/DomainSearch/PreviewCard.js` (NEW)

```javascript
import React from 'react';
import './PreviewCard.css';

const PreviewCard = ({ candidate, onSelect }) => {
  const {
    name,
    title,
    current_company,
    location,
    experience = [],
    years_experience = 0,
    linkedin_url
  } = candidate;

  // Find domain company from experience
  const domainCompany = experience.find(exp =>
    exp.company_name && (
      exp.company_name.toLowerCase().includes('observe') ||
      exp.company_name.toLowerCase().includes('krisp') ||
      exp.company_name.toLowerCase().includes('otter')
    )
  );

  return (
    <div className="preview-card">
      <div className="preview-card-header">
        <input
          type="checkbox"
          className="candidate-checkbox"
          onChange={(e) => onSelect(e.target.checked)}
        />
        <h3 className="candidate-name">{name}</h3>
        <button className="btn-quick-view">Quick View</button>
      </div>

      <div className="preview-card-body">
        <p className="candidate-title">{title}</p>
        <p className="candidate-company">at {current_company}</p>

        <div className="candidate-meta">
          <span>📍 {location}</span>
          <span>•</span>
          <span>🎓 {years_experience} years</span>
        </div>

        {domainCompany && (
          <div className="domain-badge">
            🏢 {domainCompany.company_name}
            ({domainCompany.start_date?.slice(0, 4)} - {domainCompany.end_date?.slice(0, 4) || 'present'})
          </div>
        )}
      </div>

      <div className="preview-card-actions">
        <button className="btn-select">✓ Select</button>
        <button className="btn-reject">✗ Reject</button>
        <button className="btn-save">📋 Save</button>
      </div>
    </div>
  );
};

export default PreviewCard;
```

#### Component 2: PreviewCard.css
**File:** `frontend/src/components/DomainSearch/PreviewCard.css` (NEW)

```css
.preview-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: white;
  transition: box-shadow 0.2s;
}

.preview-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.preview-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.candidate-checkbox {
  width: 20px;
  height: 20px;
}

.candidate-name {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.btn-quick-view {
  padding: 6px 12px;
  font-size: 14px;
  border: 1px solid #6366f1;
  background: white;
  color: #6366f1;
  border-radius: 4px;
  cursor: pointer;
}

.preview-card-body {
  margin-bottom: 12px;
}

.candidate-title {
  font-size: 14px;
  color: #666;
  margin: 4px 0;
}

.candidate-company {
  font-size: 14px;
  color: #333;
  margin: 4px 0;
}

.candidate-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #999;
  margin: 8px 0;
}

.domain-badge {
  display: inline-block;
  padding: 4px 8px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 8px;
}

.preview-card-actions {
  display: flex;
  gap: 8px;
}

.preview-card-actions button {
  flex: 1;
  padding: 8px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-select {
  color: #22c55e;
  border-color: #22c55e !important;
}

.btn-reject {
  color: #ef4444;
  border-color: #ef4444 !important;
}

.btn-save {
  color: #6366f1;
  border-color: #6366f1 !important;
}
```

#### Component 3: PreviewDashboard.js
**File:** `frontend/src/components/DomainSearch/PreviewDashboard.js` (NEW)

```javascript
import React from 'react';
import PreviewCard from './PreviewCard';
import './PreviewDashboard.css';

const PreviewDashboard = ({ searchResults, onSelectCandidate, onLoadMore }) => {
  const {
    stage2_previews = [],
    total_previews_found = 0,
    relevance_score = 0,
    location_distribution = {},
    filter_precision = 0,
    role_keywords_used = [],
    profiles_offset = 100
  } = searchResults;

  const topLocations = Object.entries(location_distribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  const hasMore = profiles_offset < total_previews_found;

  return (
    <div className="preview-dashboard">
      {/* Metrics Bar */}
      <div className="metrics-bar">
        <div className="metric">
          <span className="metric-label">Found</span>
          <span className="metric-value">{total_previews_found.toLocaleString()}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Previewing</span>
          <span className="metric-value">{stage2_previews.length} (FREE)</span>
        </div>
        <div className="metric">
          <span className="metric-label">Relevance</span>
          <span className="metric-value">{(relevance_score * 100).toFixed(0)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Role Match</span>
          <span className="metric-value">{(filter_precision * 100).toFixed(0)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Top Locations</span>
          <span className="metric-value">
            {topLocations.map(([loc, count]) => `${loc} (${count})`).join(', ')}
          </span>
        </div>
      </div>

      {/* Role Keywords */}
      {role_keywords_used.length > 0 && (
        <div className="role-keywords">
          <strong>Target Roles:</strong>{' '}
          {role_keywords_used.slice(0, 5).map((keyword, idx) => (
            <span key={idx} className="keyword-badge">{keyword}</span>
          ))}
        </div>
      )}

      {/* Preview Cards */}
      <div className="preview-cards-grid">
        {stage2_previews.map((candidate, idx) => (
          <PreviewCard
            key={candidate.linkedin_url || idx}
            candidate={candidate}
            onSelect={() => onSelectCandidate(candidate)}
          />
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div className="load-more-section">
          <p>Showing {stage2_previews.length} of {total_previews_found.toLocaleString()} candidates</p>
          <button className="btn-load-more" onClick={onLoadMore}>
            Load More Profiles ({Math.min(50, total_previews_found - profiles_offset)} more)
          </button>
          <p className="credit-warning">
            ⚠️ Loading more will use CoreSignal credits (1 per NEW profile)
          </p>
        </div>
      )}
    </div>
  );
};

export default PreviewDashboard;
```

#### Component 4: PreviewDashboard.css
**File:** `frontend/src/components/DomainSearch/PreviewDashboard.css` (NEW)

```css
.preview-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.metrics-bar {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.metric {
  flex: 1;
  min-width: 150px;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.metric-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.role-keywords {
  margin-bottom: 20px;
  padding: 12px;
  background: #fef3c7;
  border-radius: 8px;
}

.keyword-badge {
  display: inline-block;
  padding: 4px 12px;
  background: white;
  border: 1px solid #fbbf24;
  border-radius: 16px;
  font-size: 13px;
  margin: 4px;
}

.preview-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

.load-more-section {
  text-align: center;
  padding: 20px;
  border-top: 2px solid #e0e0e0;
}

.btn-load-more {
  padding: 12px 24px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin: 10px 0;
}

.btn-load-more:hover {
  background: #4f46e5;
}

.credit-warning {
  font-size: 13px;
  color: #ef4444;
  margin-top: 8px;
}
```

---

### Phase 4: Integration (60 min)

**File:** `frontend/src/App.js`

**Step 1: Import PreviewDashboard** (line ~8)
```javascript
import PreviewDashboard from './components/DomainSearch/PreviewDashboard';
```

**Step 2: Add JSX rendering** (around line 4000+, in your domain search results section)
```javascript
{domainSearchResults.stage2_previews.length > 0 && (
  <PreviewDashboard
    searchResults={domainSearchResults}
    onSelectCandidate={(candidate) => {
      console.log('Selected candidate:', candidate);
      // TODO: Add to selection list
    }}
    onLoadMore={async () => {
      const response = await fetch('/api/jd/load-more', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          session_id: domainSearchResults.session_id,
          count: 50
        })
      });
      const data = await response.json();

      setDomainSearchResults(prev => ({
        ...prev,
        stage3_profiles: [...prev.stage3_profiles, ...data.profiles],
        profiles_offset: prev.profiles_offset + data.profiles.length,
        credits_used: prev.credits_used + data.credits_used,
        cache_stats: data.cache_stats
      }));
    }}
  />
)}
```

---

## 📝 Next Steps

1. **Update React state in App.js** (~30 min)
2. **Create PreviewCard component** (~45 min)
3. **Create PreviewDashboard component** (~90 min)
4. **Integrate into App.js** (~60 min)
5. **Test end-to-end** (~30 min)

**Total Time:** ~4 hours of frontend work

---

## 🧪 Testing Checklist

After frontend implementation:

- [ ] API returns 85 profiles with normalized fields
- [ ] PreviewDashboard displays metrics bar correctly
- [ ] 85 PreviewCard components render in grid
- [ ] Domain badges show for candidates with experience at target companies
- [ ] Load More button appears at bottom
- [ ] Clicking Load More fetches next batch
- [ ] Credit warning displays before loading
- [ ] Session persists across page refresh

---

**Session Complete!**
Backend is fully functional. Frontend components are ready to be implemented.
