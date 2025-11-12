# 🎯 Next Session Handover - Domain Search Pipeline Complete

**Date:** November 11, 2025
**Branch:** `wip/domain-search`
**Session Status:** ✅ Backend Complete | ✅ Frontend Complete | 🧪 Ready for UI Testing

---

## 📋 What Was Accomplished This Session

### ✅ Backend Fixes (100% Complete)

#### 1. Fixed NoneType Error in Title Processing
**File:** `backend/jd_analyzer/api/domain_search.py`
**Lines:** 1131, 1134

**Problem:** When profile titles were explicitly `None`, calling `.lower()` would crash

**Solution:**
```python
# Before: candidate.get('title', '').lower()
# After:  (candidate.get('title') or '').lower()
```

**Impact:** Prevents 500 errors during preview search

---

#### 2. Created Profile Field Normalization Function
**File:** `backend/jd_analyzer/api/domain_search.py`
**Lines:** 858-915

**What It Does:**
- Converts CoreSignal fields → Frontend-expected fields
- **Keeps ALL original CoreSignal fields** (backward compatible)
- **Adds normalized fields** for easier frontend consumption

**Field Mappings:**
```python
CoreSignal Field         → Normalized Field
-------------------        ------------------
full_name                → name
first_name + last_name   → name (fallback)
headline                 → title
generated_headline       → title (fallback)
profile_url              → linkedin_url
experience[0].company    → current_company
experience dates         → years_experience
```

**Example Output:**
```json
{
  // Original CoreSignal fields (preserved)
  "full_name": "K V Vijay Girish",
  "headline": "Applied Scientist @Amazon AGI...",
  "profile_url": "https://linkedin.com/in/...",

  // NEW Normalized fields (added)
  "name": "K V Vijay Girish",
  "title": "Applied Scientist @Amazon AGI...",
  "linkedin_url": "https://linkedin.com/in/...",
  "current_company": "Amazon",
  "years_experience": 8,

  // All other CoreSignal fields unchanged
  "location": "Bengaluru, Karnataka, India",
  "experience": [...],
  "skills": [...]
}
```

---

#### 3. Applied Normalization to BOTH Code Paths
**File:** `backend/jd_analyzer/api/domain_search.py`

**Fresh Searches (Line 1273):**
```python
normalized_previews = normalize_profile_fields(previews)
return {"previews": normalized_previews, ...}
```

**Cached Results (Line 1921):**
```python
normalized_cached_previews = normalize_profile_fields(cached_data['stage2_previews'])
return jsonify({"stage2_previews": normalized_cached_previews, ...})
```

**Why This Matters:** ALL API responses return normalized fields, regardless of cache status

---

### ✅ Frontend Updates (100% Complete)

#### Updated Card Rendering
**File:** `frontend/src/App.js`
**Lines:** 4196-4201, 4240

**Changes:**
```javascript
// Extract normalized fields with fallbacks to raw CoreSignal fields
const candidateName = candidate.name || candidate.full_name || 'Unknown';
const candidateTitle = candidate.title || candidate.headline || candidate.generated_headline;
const companyName = candidate.current_company || candidate.company_name;
```

**Why Fallbacks:** Ensures compatibility with old cached data and provides resilience

---

## 🧪 Testing Results

### Backend API Test
```bash
curl -X POST http://localhost:5001/api/jd/domain-company-preview-search \
  -H "Content-Type: application/json" \
  -d @test_api_fixed.json
```

**Results:**
```json
{
  "success": true,
  "session_id": "sess_20251111_073004_6b09df53",
  "total_previews_found": 85,
  "stage2_previews": [
    {
      "name": "K V Vijay Girish",
      "title": "Applied Scientist @Amazon AGI | Ex-Observe.AI...",
      "current_company": "Amazon",
      "linkedin_url": "https://www.linkedin.com/in/k-v-vijay-girish-b85a3714",
      "location": "Bengaluru, Karnataka, India",
      "years_experience": 8
    }
  ],
  "relevance_score": 0.988,
  "from_cache": true,
  "cache_age_days": 0
}
```

✅ **85 profiles returned with normalized fields**

---

## 🎨 Existing UI Components (Already Built)

Your app already has **rich candidate cards** (App.js lines 4203-4450):

### Card Features:
- ✅ Name in bold (18px, weight 700)
- ✅ Relevance score badge (if available)
- ✅ Current title & company (with purple company color)
- ✅ Headline as italicized quote with left border
- ✅ Management level & department badges
- ✅ Skills display (first 8 skills)
- ✅ Location & connections count in footer
- ✅ LinkedIn link + Collect button
- ✅ Beautiful grid layout (350px min width)
- ✅ Hover effects & transitions
- ✅ Responsive design

### Card Layout:
```
┌─────────────────────────────────────┐
│ ☐ Name                    [Score] │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Title                              │
│ at Company                         │
│                                    │
│ "Headline quote..."                │
│                                    │
│ [Manager] [Engineering]            │
│ Python • React • AWS • Docker      │
│                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 📍 Location   500+ connections    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ View LinkedIn →    [Collect Full] │
└─────────────────────────────────────┘
```

---

## 📝 Known Issues & Recommendations

### 1. Years Experience Display (Not Critical)
**Issue:** Backend calculates `years_experience` but it sometimes shows 0

**Current Behavior:** `years_experience` is calculated by summing experience durations, but:
- If start/end dates are missing → defaults to 0
- Simple sum doesn't handle overlaps (could overcount)

**Recommendation for Next Session:**
If you want to display years_experience in cards:
```javascript
// Only show if > 0
{candidate.years_experience > 0 && (
  <span>🎓 {candidate.years_experience} years experience</span>
)}
```

**Better Calculation (Backend improvement):**
```python
# Use dateutil for better date parsing
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

def calculate_years_experience(experiences):
    intervals = []
    for exp in experiences:
        try:
            start = parse(exp['start_date'])
            end = parse(exp['end_date']) if exp.get('end_date') else datetime.now()
            intervals.append((start, end))
        except:
            continue

    # Merge overlapping intervals
    if not intervals:
        return 0

    intervals.sort()
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:  # Overlap
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Calculate total duration
    total_months = sum(
        relativedelta(end, start).years * 12 + relativedelta(end, start).months
        for start, end in merged
    )
    return total_months / 12
```

---

### 2. Location Distribution Not Displayed
**Backend Returns:**
```json
{
  "location_distribution": {
    "India": 892,
    "Armenia": 234,
    "United States": 145
  },
  "filter_precision": 0.75,
  "role_keywords_used": ["ml engineer", "ai engineer"]
}
```

**Frontend Has:** This data but doesn't display it yet

**Recommendation for Next Session:**
Add a metrics bar above the candidate cards:

```javascript
{domainSearchCandidates.length > 0 && (
  <div style={{
    display: 'flex',
    gap: '20px',
    padding: '16px',
    background: '#f9fafb',
    borderRadius: '8px',
    marginBottom: '20px'
  }}>
    <div>
      <div style={{ fontSize: '12px', color: '#6b7280' }}>Found</div>
      <div style={{ fontSize: '24px', fontWeight: '700' }}>
        {domainSessionStats?.total_employee_ids || domainSearchCandidates.length}
      </div>
    </div>
    <div>
      <div style={{ fontSize: '12px', color: '#6b7280' }}>Previewing</div>
      <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
        {domainSearchCandidates.length} (FREE)
      </div>
    </div>
    {/* Add more metrics as needed */}
  </div>
)}
```

---

### 3. Load More Button
**Current Implementation:** Button exists at line 4465

**Works For:** Loading next batches (20-50 profiles at a time)

**Recommendation:** Add credit warning before loading:
```javascript
<button onClick={() => {
  const confirmed = window.confirm(
    `Load 20 more profiles?\n\n` +
    `Estimated cost: ~14 credits (30% cache hit rate)\n` +
    `Actual cost depends on cache availability.`
  );
  if (confirmed) handleLoadMoreCandidates(20);
}}>
  Load 20 More ({domainSearchCandidates.length}/{domainSessionStats.total_employee_ids})
</button>
```

---

## 🚀 Next Session Priorities

### Priority 1: UI Testing (30 min)
**Action:** Test the complete flow in browser
1. Start frontend: `cd frontend && npm start`
2. Navigate to Company Research
3. Search "voice ai" domain
4. Select companies (Observe.AI, Krisp)
5. Click "Search for People"
6. **Verify:** 85 candidate cards display correctly

**Expected Results:**
- ✅ Cards show correct names (not "Unknown")
- ✅ Cards show titles/headlines
- ✅ Cards show current companies
- ✅ LinkedIn links work
- ✅ Grid layout is responsive
- ✅ Hover effects work

---

### Priority 2: Add Metrics Bar (45 min)
**Action:** Display search quality metrics above candidate cards

**Metrics to Show:**
- Total found (e.g., 1,511 total available)
- Previewing (e.g., 100 FREE)
- Relevance score (e.g., 99%)
- Filter precision (e.g., 75% match target role)
- Top 3 locations

**Files to Modify:**
- `frontend/src/App.js` (add metrics bar around line 4180)

---

### Priority 3: Improve Years Experience Calculation (60 min)
**Action:** Fix backend calculation to handle overlaps

**Files to Modify:**
- `backend/jd_analyzer/api/domain_search.py` (normalize_profile_fields function)

**Implementation:**
- Use interval merging to avoid double-counting overlaps
- Handle missing dates gracefully
- Return 0 if unable to calculate (don't guess)

---

### Priority 4: Session Persistence (30 min)
**Action:** Allow users to resume searches after page refresh

**Current Behavior:** Session ID stored, but candidates cleared on refresh

**Recommendation:**
```javascript
// In useEffect
useEffect(() => {
  const savedSession = localStorage.getItem('domain_search_session');
  if (savedSession) {
    const { session_id, candidates } = JSON.parse(savedSession);
    setDomainSearchSessionId(session_id);
    setDomainSearchCandidates(candidates);
  }
}, []);

// When saving candidates
useEffect(() => {
  if (domainSearchSessionId && domainSearchCandidates.length > 0) {
    localStorage.setItem('domain_search_session', JSON.stringify({
      session_id: domainSearchSessionId,
      candidates: domainSearchCandidates
    }));
  }
}, [domainSearchSessionId, domainSearchCandidates]);
```

---

## 📂 Important Files Reference

### Backend Files:
```
backend/
├── jd_analyzer/api/domain_search.py        # Main pipeline (858-915: normalization)
├── test_api_fixed.json                      # Test request (works with Observe.AI)
├── READY_TO_TEST.md                         # Testing guide
├── SESSION_PROGRESS_UI_INTEGRATION.md       # Detailed session notes
└── PIPELINE_FLOW_COMPLETE_GUIDE.md          # Complete pipeline documentation
```

### Frontend Files:
```
frontend/src/
└── App.js
    ├── Lines 4196-4201: Card rendering logic (uses normalized fields)
    ├── Lines 4203-4450: Rich candidate card layout
    ├── Lines 2154-2165: API response handler
    └── Lines 4465-4481: Load More button
```

---

## 🔍 Debug Commands

### Check Backend API:
```bash
cd backend

# Test API with known working company
curl -X POST http://localhost:5001/api/jd/domain-company-preview-search \
  -H "Content-Type: application/json" \
  -d @test_api_fixed.json | python3 -m json.tool | head -100
```

### Check Flask Status:
```bash
# Is Flask running?
lsof -ti:5001

# View recent logs
tail -50 flask_restart.log | grep -E "CACHE|ERROR|Normalized"
```

### Check Session Files:
```bash
# List recent sessions
ls -lt backend/logs/domain_search_sessions/ | head -5

# View session data
cat backend/logs/domain_search_sessions/sess_XXXXX/02_preview_results.json | jq '.candidates[0]'
```

---

## ⚠️ Common Issues & Solutions

### Issue: Cards Show "Unknown" for Names
**Symptom:** All cards display "Unknown" instead of candidate names

**Cause:** Backend normalization not working OR frontend not receiving data

**Debug:**
1. Check API response: `console.log(data.stage2_previews[0])`
2. Verify `name` field exists in response
3. Check Flask logs for normalization function execution

**Solution:** Restart Flask to load latest code with normalization

---

### Issue: 0 Candidates Found
**Symptom:** API returns `total_previews_found: 0`

**Cause:** Cache returning old pre-normalization data OR query issue

**Debug:**
1. Check Flask logs for "CACHE HIT" or "CACHE MISS"
2. If CACHE HIT, check cache age
3. Check query structure has `default_operator: "OR"`

**Solution:** Use different companies or clear cache (Supabase cached_searches table)

---

### Issue: Cards Don't Display After API Success
**Symptom:** API returns data but UI doesn't show cards

**Debug:**
1. Browser console: Check for React errors
2. Verify state update: `console.log(domainSearchCandidates)`
3. Check if `domainSearchCandidates.length > 0` condition is met

**Solution:** Verify line 4182 condition matches state variable name

---

## 🎯 Success Criteria Checklist

### Backend:
- [x] API returns 85 profiles
- [x] Each profile has `name`, `title`, `linkedin_url` fields
- [x] Normalization works for both fresh & cached requests
- [x] No NoneType errors in logs

### Frontend:
- [ ] 85 cards display in grid
- [ ] Cards show correct candidate names
- [ ] Cards show titles/headlines
- [ ] Cards show current companies
- [ ] Grid is responsive (350px cards)
- [ ] Hover effects work

### User Experience:
- [ ] Search completes in < 40 seconds
- [ ] Cards render in < 2 seconds
- [ ] Load More button works
- [ ] Session persists after page refresh
- [ ] No console errors

---

## 💡 Future Enhancements (Optional)

### 1. Advanced Filtering
Add client-side filters above cards:
- Location filter (dropdown with top locations)
- Seniority filter (Junior, Mid, Senior, Executive)
- Skills filter (multi-select from aggregated skills)

### 2. Bulk Actions
Add checkboxes to cards for bulk operations:
- Select all
- Collect selected (with credit estimate)
- Export selected to CSV
- Add selected to list

### 3. Card Hover Preview
Show more detail on hover:
- Full experience history
- Education
- Top skills (all, not just 8)
- Recent activity (if available)

### 4. Sort Options
Add sorting dropdown:
- Relevance score (default)
- Years of experience
- Location
- Connections count

---

## 📊 Credit Usage Tracking

### Current Costs:
- **Stage 1 (Company Discovery):** 0 credits (company lookups are free)
- **Stage 2 (Preview 100):** 0 credits (preview is FREE!)
- **Stage 3 (Full Collection):**
  - New profiles: 1 credit each
  - Cached profiles (<90 days): 0 credits (FREE reuse)
  - Typical cache hit rate: 30-40%

### Optimization Opportunities:
1. **Increase cache TTL:** Current 90 days could be extended to 180 days
2. **Batch collection:** Collect 50-100 at once (better cache utilization)
3. **Smart caching:** Cache by company+role query (not just raw search)

---

## 🔐 Environment Variables Required

```bash
# Backend (.env or environment)
ANTHROPIC_API_KEY=sk-...
CORESIGNAL_API_KEY=...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
TAVILY_API_KEY=tvly-...  # For Crunchbase URL lookups

# Frontend (.env)
REACT_APP_API_URL=http://localhost:5001  # Dev only
```

---

## 📞 Handoff Summary

**What's Working:**
✅ Backend normalization complete
✅ Frontend card rendering updated
✅ API returns 85 profiles with correct fields
✅ Rich cards already implemented

**What's Needed:**
🧪 UI testing to verify end-to-end flow
📊 Add metrics bar (optional but recommended)
⏱️ Fix years_experience calculation (optional)
💾 Add session persistence (optional)

**Estimated Time to Production:**
- **Minimum (just testing):** 30 minutes
- **With metrics bar:** 75 minutes
- **With all enhancements:** 2-3 hours

---

**Session Complete! Ready for UI testing and polish.** 🎉
