# Iterative People Search with Advanced Filters - Feature Plan

**Feature:** Advanced People Search with Location, Seniority, Department, and Skills Filters
**Feature Request ID:** #3
**Status:** Planning Phase
**Last Updated:** November 12, 2025
**Owner:** Engineering Team

---

## Executive Summary

### Problem Statement

After discovering relevant companies through domain search, users want to find **specific people** at those companies. The current "Search for People" feature has significant limitations:

1. **One-shot search:** Button text changes to "New Search" but requires re-selecting companies
2. **Limited filtering:** Only uses role keywords (optional) and location (optional) from JD
3. **No iterative refinement:** Can't adjust filters after seeing initial results
4. **Unused CoreSignal taxonomy:** Rich filtering capabilities (department, seniority, skills) not exposed
5. **No user control:** Filters are hidden in backend, user can't customize search strategy
6. **Over-recall results:** Fetches anyone who ever worked at target companies (no seniority/department filter)

**Example User Frustration:**
```
User: "I found 13 great voice AI companies. Now I want to find Senior ML Engineers
       (not junior, not managers) in Engineering departments in the Bay Area."

Current System: Returns 100 mixed results (juniors, seniors, sales, marketing,
                all locations) with no way to filter further.

User: "Let me try adding 'location: San Francisco' to the search..."
      → Must re-run entire search from scratch
      → Still gets global results (location is optional boost, not required filter)
```

### Solution

Build an **iterative people search experience** that:

1. **Extracts smart defaults** from JD analysis (location, seniority, role)
2. **Shows filters upfront** for user review and editing before search
3. **Allows filter refinement** after seeing results without re-running API calls
4. **Leverages CoreSignal taxonomy** fully (department, management level, skills)
5. **Provides multiple search strategies** (broad discovery vs. precise targeting)
6. **Saves filter preferences** per company list for repeat use

### Business Value

**User Experience Benefits:**
- 🎯 **Precision:** Find exact candidate profiles (senior engineers, not all levels)
- ⚡ **Speed:** Refine results instantly without re-searching
- 🔄 **Iterative:** Try different filter combinations quickly
- 👁️ **Transparency:** See and control all filters before searching
- 💾 **Reusability:** Save filter combinations for similar searches

**Efficiency Benefits:**
- 💰 **API credit savings:** Fetch only relevant candidates (not 100 mixed results)
- 🚀 **Faster results:** Client-side refinement is instant (<10ms)
- 📊 **Better signal:** Higher quality candidates per API call
- 🎨 **Flexible targeting:** Adjust strategy based on results (too few? broaden filters)

**Use Cases:**
1. **Precise targeting:** "Senior ML Engineers in Bay Area at these 5 companies"
2. **Discovery mode:** "Anyone technical at these 20 companies" (broad search)
3. **Niche roles:** "Principal Engineers with Python skills at Series A AI companies"
4. **Geographic targeting:** "Engineering leaders in Austin, Texas only"
5. **Department-specific:** "Product Managers or Data Scientists at these companies"

---

## Current State Analysis

### Current "Search for People" Flow

**Step 1: Select Companies**
```
User checks boxes next to companies in research results
→ selectedCompanies array populated (company name, domain, CoreSignal ID)
→ "🔍 Search for People at 5 Companies" button appears
```

**Step 2: Click Search Button**
```javascript
// frontend/src/App.js lines 4219-4259
{selectedCompanies.length > 0 && (
  <button onClick={() => {
    setDomainSearchSessionId(null);        // Clear previous session
    setDomainSearchCandidates([]);         // Clear previous results
    handleStartDomainSearch(selectedCompanies);
  }}>
    {domainSearching ? '🔄 Searching...' : '🔍 Search for People...'}
  </button>
)}
```

**Step 3: Backend Search**
```
POST /api/jd/domain-company-preview-search
Body: {
  "jd_requirements": {
    "role_title": "Senior ML Engineer",
    "location": "San Francisco Bay Area",  // Optional boost only
    "seniority_level": "senior",           // Not used in query!
    "technical_skills": ["Python", "PyTorch"]
  },
  "mentioned_companies": [
    {name: "Deepgram", coresignal_id: 3829471},
    {name: "AssemblyAI", coresignal_id: 9876543}
  ],
  "max_previews": 100
}

Query Built (Elasticsearch DSL):
{
  "query": {
    "bool": {
      "must": [
        // ✅ REQUIRED: Company filter (nested experience query)
        {"nested": {
          "path": "experience",
          "query": {"term": {"experience.company_id": 3829471}}
        }}
      ],
      "should": [
        // ⚠️ OPTIONAL: Role keywords (not required)
        {"match": {"experience.title": "ml engineer"}},
        // ⚠️ OPTIONAL: Location boost (not required)
        {"term": {"location": "San Francisco Bay Area"}}
      ],
      "minimum_should_match": 0  // None required!
    }
  }
}

Result: Returns anyone who EVER worked at Deepgram or AssemblyAI
        (juniors, seniors, sales, marketing, all locations)
```

**Step 4: Display Results**
```
domainSearchCandidates populated with ~20-100 profiles
→ Rendered as candidate cards (name, title, headline, location)
→ Button text changes to "🔄 New Search for People"
→ NO FILTERS visible on results
```

**Step 5: User Wants to Refine**
```
Problem: User sees too many irrelevant results
         (juniors when they want seniors, sales when they want engineering)

Current Options:
1. Re-click button → Clears results, runs same search again (no filter changes)
2. Go back to JD, edit requirements, re-run entire pipeline (slow)
3. Manually scan 100 results for relevant candidates (tedious)

Missing: No way to filter results without starting over
```

---

### Current Backend Query Structure

**File:** `backend/jd_analyzer/api/domain_search.py`
**Method:** `build_experience_based_query()` (lines 489-638)

**What's Currently Filtered:**

| Filter Type | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| **Company** | `experience.company_id` or `experience.company_name` | ✅ Required | Works perfectly |
| **Role Keywords** | `experience.title` match | ⚠️ Optional boost | Should be toggleable |
| **Location** | `location` term | ⚠️ Optional boost | Should be toggleable |
| **Seniority** | `active_experience_management_level` | ❌ Not used | Field available but not queried |
| **Department** | `active_experience_department` | ❌ Not used | Field available but not queried |
| **Skills** | `skills` array | ❌ Not used | ~75% coverage, not queried |
| **Experience Years** | Calculated from `experience` array | ❌ Not used | Could filter min/max years |

**Available Flags (Hidden):**
```python
# In build_experience_based_query() - lines 489-500
require_target_role = False      # Hardcoded! No UI control
require_location = False         # Hardcoded! No UI control
boost_companies = False          # Not used
use_seniority_filter = False     # Not used
```

---

### CoreSignal Employee Search API - Complete Taxonomy

**Source:** `backend/coresignal_api_taxonomy.py`

#### **Location Filters**

| Field Name | Query Type | Coverage | Example Values | Notes |
|-----------|-----------|----------|----------------|-------|
| `location` | wildcard | 100% | "San Francisco Bay Area" | ✅ Currently used (optional) |
| `location_country` | term | 100% | "United States" | Could add for country filter |
| `location_state` | term | Variable | "California", "Texas" | Could add for state filter |
| `location_city` | term | Variable | "San Francisco", "Austin" | Could add for city filter |
| `location_raw_address` | text | 100% | Full address string | Could search for keywords |

**Recommendation:** Use `location_country` (required) + `location_state` (optional) for precision

#### **Role/Title Filters**

| Field Name | Query Type | Coverage | Example Values | Notes |
|-----------|-----------|----------|----------------|-------|
| `active_experience_title` | wildcard | 100% | "Senior ML Engineer" | ✅ Currently used |
| `job_title` | wildcard | 100% | Current job title | ✅ Currently used |
| `headline` | wildcard | 100% | LinkedIn headline | ✅ Currently used |
| `generated_headline` | wildcard | Variable | Auto-generated by CoreSignal | More accurate than user headline |
| `experience.title` | wildcard | 100% | Historical titles | ✅ Currently used (nested) |

**Recommendation:** Continue using `experience.title` for flexibility (finds people who had target role)

#### **Seniority Filters**

| Field Name | Query Type | Coverage | Example Values | Notes |
|-----------|-----------|----------|----------------|-------|
| `active_experience_management_level` | term | Variable | "Specialist", "Manager", "Director", "C-level" | ⚠️ "Senior" only 2% (unreliable) |
| `is_decision_maker` | term | Variable | 0 or 1 | Identifies executives/leaders |

**Management Level Values:**
- `"Specialist"` - 74% (most common - ICs)
- `"Manager"` - 14%
- `"Senior"` - 2% (RARE - don't rely on this!)
- `"Director"` - 5%
- `"C-level"` - 3%

**Recommendation:** Use management level for Directors/C-Suite. For "Senior IC" detection, use years of experience + title keywords instead.

#### **Department Filters**

| Field Name | Query Type | Coverage | Example Values | Notes |
|-----------|-----------|----------|----------------|-------|
| `active_experience_department` | term | Variable | See list below | Curated by CoreSignal |

**Department Enum Values (Most Relevant for Tech Recruiting):**
```
"Engineering and Technical"      - Software engineers, ML engineers, data engineers
"Data Science"                   - Data scientists, ML researchers, analysts
"Product Management"             - Product managers, PMs, product leads
"C-Suite"                        - Executives (CEO, CTO, CPO, etc.)
"Operations"                     - DevOps, infrastructure, SRE
"Marketing"                      - Growth, content, demand gen
"Sales"                          - Account execs, SDRs, sales engineers
"Customer Service"               - Support, success, solutions architects
"Information Technology"         - IT, security, systems admin
"Research and Development"       - R&D, scientists, research engineers
"Design"                         - Product designers, UX/UI
"Finance & Accounting"           - Finance, accounting, FP&A
"Human Resources"                - HR, recruiting, people ops
"Business Development"           - Partnerships, BD
"Consulting"                     - Consultants, advisors
```

**Recommendation:** Add department filter as multi-select (can select "Engineering and Technical" + "Data Science")

#### **Skills Filters**

| Field Name | Query Type | Coverage | Example Values | Notes |
|-----------|-----------|----------|----------------|-------|
| `skills` | Array search | ~75% | ["Python", "Machine Learning", "PyTorch"] | Not all profiles have skills |

**Recommendation:** Use as optional refinement (post-search filter), not required (would eliminate 25% of profiles)

---

## Feature Gaps Analysis

### Gap 1: No Pre-Search Filter UI ❌

**Current State:**
- Filters extracted from JD automatically
- User has no visibility or control
- Backend hardcodes `require_target_role = False`, `require_location = False`

**User Impact:**
- "I want to search for engineers only, but I'm getting sales/marketing people"
- "I want Bay Area only, but I'm getting global results"

**Solution:**
- Show extracted filters in UI before clicking "Search for People"
- Allow editing (dropdown for location, checkboxes for department)
- Add toggles: "Role required?" "Location required?"

---

### Gap 2: No Post-Search Refinement ❌

**Current State:**
- Results displayed as flat list
- No filtering UI on results page
- Must re-run entire search to change filters

**User Impact:**
- "I got 100 results but 80 are irrelevant"
- "Let me filter to just Senior level... wait, I can't?"

**Solution:**
- Add filter pills above results
- Client-side filtering (instant, no API calls)
- Filters: Department, Seniority, Years Experience, Skills

---

### Gap 3: No Seniority Filtering ❌

**Current State:**
- JD extracts `seniority_level: "senior"`
- Backend receives it but doesn't use it in query
- Results include all levels (junior, mid, senior, staff, principal)

**User Impact:**
- "JD says 'Senior ML Engineer' but I'm getting junior engineers"
- "Can't filter to just Staff+ level for principal roles"

**Solution:**
- Use `active_experience_management_level` field
- Combine with years of experience calculation
- Infer seniority from title keywords ("Staff Engineer", "Principal")

---

### Gap 4: No Department Filtering ❌

**Current State:**
- Backend doesn't query `active_experience_department` field
- Results include all departments (engineering, sales, marketing, HR)

**User Impact:**
- "I want engineers, not sales engineers"
- "Search returns product managers when I want technical ICs"

**Solution:**
- Add `active_experience_department` to query
- Multi-select: ["Engineering and Technical", "Data Science"]
- Smart defaults from role title (e.g., "ML Engineer" → "Engineering and Technical")

---

### Gap 5: No Search Strategy Toggle ❌

**Current State:**
- Backend hardcodes `require_target_role = False` and `require_location = False`
- Always returns over-broad results (anyone who worked at companies)

**User Impact:**
- "I want precise targeting (Bay Area engineers only) but system returns everyone"
- "Can't control precision vs. recall trade-off"

**Solution:**
- Add "Search Strategy" toggle:
  - 🎯 **Precise:** Require role + location (narrow, high relevance)
  - ⚖️ **Balanced:** Require role, location optional (default)
  - 🌍 **Broad:** All optional (wide discovery)

---

### Gap 6: No Skills Filtering ❌

**Current State:**
- JD extracts `technical_skills: ["Python", "PyTorch", "LLMs"]`
- Backend doesn't query `skills` field (~75% coverage)

**User Impact:**
- "I need Python experts, but results include people without Python"
- "Can't filter to candidates with specific tech stack"

**Solution:**
- Use `skills` field as optional refinement (post-search filter)
- Don't require (would eliminate 25% without skill data)
- Show skill tags on candidate cards for manual review

---

## Implementation Approaches - Detailed Analysis

### Approach A: Smart Defaults with Pre-Search Editing ✅ RECOMMENDED

**Implementation:**

**Phase 1: Extract Filters from JD**
```python
# JD Analyzer already extracts these (jd_parser.py)
jd_requirements = {
  "role_title": "Senior ML Engineer",
  "seniority_level": "senior",
  "location": "San Francisco Bay Area",
  "technical_skills": ["Python", "PyTorch", "LLMs"],
  "target_domain": "voice ai"
}

# NEW: Infer department from role_title
department = infer_department(role_title)  # "ML Engineer" → "Engineering and Technical"
```

**Phase 2: Display in UI (Before "Search for People" Button)**
```jsx
<div className="search-filters-preview">
  <h4>Search Filters (from JD)</h4>

  {/* Location Filter */}
  <div className="filter-row">
    <label>📍 Location</label>
    <input value="San Francisco Bay Area" onChange={...} />
    <label>
      <input type="checkbox" checked={requireLocation} />
      Required (strict filter)
    </label>
  </div>

  {/* Role Filter */}
  <div className="filter-row">
    <label>💼 Role Keywords</label>
    <input value="senior ml engineer, ai engineer" onChange={...} />
    <label>
      <input type="checkbox" checked={requireRole} />
      Required (strict filter)
    </label>
  </div>

  {/* Seniority Filter */}
  <div className="filter-row">
    <label>🎯 Seniority Level</label>
    <select value="senior">
      <option value="">Any</option>
      <option value="senior">Senior IC (5-10 years)</option>
      <option value="staff">Staff+ (10+ years)</option>
      <option value="manager">Manager</option>
      <option value="director">Director+</option>
      <option value="c-level">C-Suite</option>
    </select>
  </div>

  {/* Department Filter */}
  <div className="filter-row">
    <label>🏢 Department</label>
    <MultiSelect
      options={["Engineering and Technical", "Data Science", "Product Management"]}
      selected={["Engineering and Technical"]}
      onChange={...}
    />
  </div>

  {/* Search Strategy */}
  <div className="filter-row">
    <label>🎯 Search Strategy</label>
    <select value="balanced">
      <option value="precise">🎯 Precise (require all filters)</option>
      <option value="balanced">⚖️ Balanced (require role only)</option>
      <option value="broad">🌍 Broad Discovery (all optional)</option>
    </select>
  </div>

  <button onClick={handleStartDomainSearch}>
    🔍 Search for People at 5 Companies
  </button>
</div>
```

**Phase 3: Pass Filters to Backend**
```javascript
// frontend/src/App.js - handleStartDomainSearch()
const response = await fetch('/api/jd/domain-company-preview-search', {
  method: 'POST',
  body: JSON.stringify({
    jd_requirements: {
      role_title: roleFilter,
      location: locationFilter,
      seniority_level: seniorityFilter,
      technical_skills: skillsFilter,
      department: departmentFilter  // NEW
    },
    search_config: {
      require_role: requireRole,      // NEW
      require_location: requireLocation,  // NEW
      search_strategy: searchStrategy     // NEW: "precise" | "balanced" | "broad"
    },
    mentioned_companies: selectedCompanies,
    max_previews: 100
  })
});
```

**Phase 4: Modify Backend Query Builder**
```python
# backend/jd_analyzer/api/domain_search.py
# build_experience_based_query() - lines 489-638

def build_experience_based_query(
    jd_requirements: Dict,
    search_config: Dict,  # NEW parameter
    companies: List[Dict]
):
    # Extract filters
    role_title = jd_requirements.get('role_title')
    location = jd_requirements.get('location')
    seniority_level = jd_requirements.get('seniority_level')
    department = jd_requirements.get('department', [])  # NEW

    # Extract config
    require_role = search_config.get('require_role', False)
    require_location = search_config.get('require_location', False)
    search_strategy = search_config.get('search_strategy', 'balanced')

    # Apply strategy overrides
    if search_strategy == 'precise':
        require_role = True
        require_location = True
    elif search_strategy == 'broad':
        require_role = False
        require_location = False

    # Build query
    query = {
        "query": {
            "bool": {
                "must": [
                    # Company filter (always required)
                    build_company_filter(companies)
                ],
                "should": [],
                "filter": []  # NEW: For hard filters
            }
        }
    }

    # Role filter (required or boost)
    if role_title:
        role_query = build_role_query(role_title)
        if require_role:
            query['query']['bool']['must'].append(role_query)
        else:
            query['query']['bool']['should'].append(role_query)

    # Location filter (required or boost)
    if location:
        location_query = {"term": {"location": location}}
        if require_location:
            query['query']['bool']['must'].append(location_query)
        else:
            query['query']['bool']['should'].append(location_query)

    # Seniority filter (NEW - always applied if specified)
    if seniority_level:
        seniority_query = build_seniority_query(seniority_level)
        query['query']['bool']['filter'].append(seniority_query)

    # Department filter (NEW - always applied if specified)
    if department:
        department_query = {
            "terms": {"active_experience_department": department}
        }
        query['query']['bool']['filter'].append(department_query)

    return query

def build_seniority_query(seniority_level: str) -> Dict:
    """Build seniority filter query."""
    if seniority_level == "senior":
        # Senior IC: 5-10 years OR "Senior" in title
        return {
            "bool": {
                "should": [
                    {"match": {"active_experience_title": "senior"}},
                    {"range": {"experience_years": {"gte": 5, "lte": 10}}}
                ],
                "minimum_should_match": 1
            }
        }
    elif seniority_level == "staff":
        # Staff+: 10+ years OR "Staff"/"Principal" in title
        return {
            "bool": {
                "should": [
                    {"match": {"active_experience_title": "staff principal"}},
                    {"range": {"experience_years": {"gte": 10}}}
                ],
                "minimum_should_match": 1
            }
        }
    elif seniority_level == "manager":
        return {"term": {"active_experience_management_level": "Manager"}}
    elif seniority_level == "director":
        return {"terms": {"active_experience_management_level": ["Director", "C-level"]}}
    elif seniority_level == "c-level":
        return {"term": {"active_experience_management_level": "C-level"}}
    else:
        return {}  # No seniority filter
```

**Pros:**
- ✅ **Minimal user effort:** Filters auto-populated from JD
- ✅ **Transparency:** User sees and can edit before searching
- ✅ **Control:** Toggle precise vs. broad search strategy
- ✅ **Leverages existing JD parsing:** No duplicate data entry
- ✅ **API efficiency:** Fetch only relevant candidates

**Cons:**
- ⚠️ **Requires JD:** Can't use if starting from scratch (company list only)
- ⚠️ **Department inference:** Heuristic mapping may be wrong
- ⚠️ **More UI complexity:** 5+ filter controls to build

**Estimated Effort:** 2-3 days
- Backend query modifications: 4-6 hours
- Frontend filter UI: 6-8 hours
- Testing: 4-6 hours

---

### Approach B: Post-Search Client-Side Refinement ✅ COMPLEMENTARY

**Implementation:**

**After Search Completes, Add Filter Bar:**
```jsx
<div className="candidate-results">
  <h3>Found {domainSearchCandidates.length} candidates</h3>

  {/* NEW: Post-Search Filters */}
  <div className="result-filters">
    <label>🏢 Department:</label>
    <select onChange={(e) => setDepartmentFilter(e.target.value)}>
      <option value="">All Departments</option>
      <option value="Engineering and Technical">Engineering</option>
      <option value="Data Science">Data Science</option>
      <option value="Product Management">Product</option>
      <option value="C-Suite">C-Suite</option>
    </select>

    <label>🎯 Seniority:</label>
    <select onChange={(e) => setSeniorityFilter(e.target.value)}>
      <option value="">All Levels</option>
      <option value="junior">Junior (0-3 years)</option>
      <option value="mid">Mid (3-5 years)</option>
      <option value="senior">Senior (5-10 years)</option>
      <option value="staff">Staff+ (10+ years)</option>
    </select>

    <label>🔧 Has Skills:</label>
    <MultiSelect
      options={extractedSkills}  // From all candidate profiles
      selected={skillsFilter}
      onChange={setSkillsFilter}
    />

    <button onClick={() => clearAllFilters()}>Clear Filters</button>
  </div>

  {/* Filtered Results */}
  <div className="candidates-list">
    {getFilteredCandidates().map(candidate => (
      <CandidateCard key={candidate.id} candidate={candidate} />
    ))}
  </div>

  <p className="filter-stats">
    Showing {getFilteredCandidates().length} of {domainSearchCandidates.length} candidates
  </p>
</div>
```

**Client-Side Filter Logic:**
```javascript
function getFilteredCandidates() {
  let filtered = [...domainSearchCandidates];

  // Department filter
  if (departmentFilter) {
    filtered = filtered.filter(c =>
      c.active_experience_department === departmentFilter
    );
  }

  // Seniority filter
  if (seniorityFilter) {
    filtered = filtered.filter(c => {
      const years = calculateExperienceYears(c.experience);
      if (seniorityFilter === 'junior') return years >= 0 && years < 3;
      if (seniorityFilter === 'mid') return years >= 3 && years < 5;
      if (seniorityFilter === 'senior') return years >= 5 && years < 10;
      if (seniorityFilter === 'staff') return years >= 10;
      return true;
    });
  }

  // Skills filter (AND logic - must have all selected skills)
  if (skillsFilter.length > 0) {
    filtered = filtered.filter(c => {
      const candidateSkills = c.skills || [];
      return skillsFilter.every(skill =>
        candidateSkills.some(s => s.toLowerCase().includes(skill.toLowerCase()))
      );
    });
  }

  return filtered;
}
```

**Pros:**
- ✅ **Instant refinement:** No API calls, <10ms filtering
- ✅ **Experimentation:** Try different combinations freely
- ✅ **No backend changes:** Pure frontend implementation
- ✅ **Additive:** Complements Approach A (pre-search + post-search)

**Cons:**
- ⚠️ **Limited scope:** Can only filter what's already fetched
- ⚠️ **API waste:** Still fetch irrelevant candidates initially
- ⚠️ **Field dependency:** Requires fields to be returned in API response

**Estimated Effort:** 1 day
- Filter UI components: 3-4 hours
- Filter logic: 2-3 hours
- Testing: 2-3 hours

---

### Approach C: Saved Filter Presets 🎯 FUTURE ENHANCEMENT

**Implementation:**

**Allow users to save common filter combinations:**
```jsx
<div className="filter-presets">
  <label>Quick Filters:</label>
  <button onClick={() => applySavedPreset('senior-engineers-bay-area')}>
    👨‍💻 Senior Engineers (Bay Area)
  </button>
  <button onClick={() => applySavedPreset('ml-researchers-remote')}>
    🔬 ML Researchers (Remote)
  </button>
  <button onClick={() => applySavedPreset('eng-leaders-any-location')}>
    🎯 Engineering Leaders (Any Location)
  </button>
  <button onClick={() => saveCurrentAsPreset()}>
    💾 Save Current Filters
  </button>
</div>
```

**Storage:**
```javascript
// localStorage or Supabase table
const presets = {
  'senior-engineers-bay-area': {
    name: "Senior Engineers (Bay Area)",
    filters: {
      location: "San Francisco Bay Area",
      require_location: true,
      role_title: "senior engineer",
      require_role: true,
      seniority_level: "senior",
      department: ["Engineering and Technical"]
    }
  },
  // ...
};
```

**Pros:**
- ✅ **Efficiency:** One-click filter application
- ✅ **Consistency:** Reuse same filters across searches
- ✅ **Sharing:** Could share presets with team

**Cons:**
- ⚠️ **Complexity:** Requires preset management UI
- ⚠️ **Storage:** Need to persist presets (localStorage or DB)

**Estimated Effort:** 1 day (future enhancement)

---

## Recommended Implementation Plan

### Phase 1: Smart Defaults with Pre-Search Editing (Approach A)
**Priority:** HIGH
**Effort:** 2-3 days
**Value:** Maximum API efficiency, user control, transparency

**Deliverables:**
1. Filter preview UI before "Search for People" button
2. Backend query builder modifications
3. Seniority and department filtering
4. Search strategy toggle (Precise/Balanced/Broad)

### Phase 2: Post-Search Client-Side Refinement (Approach B)
**Priority:** HIGH
**Effort:** 1 day
**Value:** Instant refinement, experimentation, better UX

**Deliverables:**
1. Filter bar above results
2. Department, seniority, skills filters
3. Client-side filter logic
4. Filter stats display

### Phase 3: Saved Filter Presets (Approach C)
**Priority:** MEDIUM
**Effort:** 1 day
**Value:** Efficiency for repeat searches

**Deliverables:**
1. Preset management UI
2. Save/load/delete presets
3. Quick-apply buttons
4. Preset sharing (optional)

---

## Technical Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Company Research Completed                          │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│  User has selected companies:                                │
│  ☑ Deepgram (ID: 3829471)                                    │
│  ☑ AssemblyAI (ID: 9876543)                                  │
│  ☑ Otter.ai (ID: 1234567)                                    │
│  ☑ Rev.ai (ID: 7654321)                                      │
│  ☑ Speechmatics (ID: 8888888)                                │
│                                                               │
│  JD Requirements (already extracted):                        │
│  • role_title: "Senior ML Engineer"                          │
│  • location: "San Francisco Bay Area"                        │
│  • seniority_level: "senior"                                 │
│  • technical_skills: ["Python", "PyTorch", "LLMs"]           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: Filter Preview UI (NEW)                             │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│  🔍 Search Filters (Smart Defaults from JD)                  │
│                                                               │
│  📍 Location: [San Francisco Bay Area         ] [Edit]       │
│     ☑ Required (strict filter)                               │
│                                                               │
│  💼 Role: [senior ml engineer, ai engineer    ] [Edit]       │
│     ☑ Required (strict filter)                               │
│                                                               │
│  🎯 Seniority: [Senior IC (5-10 years)  ▼]                   │
│                                                               │
│  🏢 Department: [☑ Engineering ☐ Data Science ☐ Product]     │
│                                                               │
│  📊 Search Strategy: [⚖️ Balanced  ▼]                         │
│     Options: 🎯 Precise | ⚖️ Balanced | 🌍 Broad              │
│                                                               │
│  [ 🔍 Search for People at 5 Companies ]                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                ↓
                POST /api/jd/domain-company-preview-search
                {
                  jd_requirements: {...},
                  search_config: {
                    require_role: true,
                    require_location: true,
                    search_strategy: "balanced"
                  },
                  mentioned_companies: [...]
                }
                ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: Backend Query Builder (MODIFIED)                    │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│  Elasticsearch DSL Query:                                    │
│  {                                                            │
│    "query": {                                                 │
│      "bool": {                                                │
│        "must": [                                              │
│          // Company filter (always required)                 │
│          {"nested": {                                         │
│            "path": "experience",                              │
│            "query": {                                         │
│              "terms": {"experience.company_id": [            │
│                3829471, 9876543, 1234567, 7654321, 8888888   │
│              ]}                                               │
│            }                                                  │
│          }},                                                  │
│                                                               │
│          // Role filter (required if strategy = precise)     │
│          {"match": {                                          │
│            "experience.title": "senior ml engineer"          │
│          }},                                                  │
│                                                               │
│          // Location filter (required if strategy = precise) │
│          {"term": {                                           │
│            "location": "San Francisco Bay Area"              │
│          }}                                                   │
│        ],                                                     │
│        "filter": [                                            │
│          // Seniority filter (NEW)                           │
│          {"bool": {                                           │
│            "should": [                                        │
│              {"match": {                                      │
│                "active_experience_title": "senior"           │
│              }},                                              │
│              {"range": {                                      │
│                "experience_years": {"gte": 5, "lte": 10}     │
│              }}                                               │
│            ],                                                 │
│            "minimum_should_match": 1                          │
│          }},                                                  │
│                                                               │
│          // Department filter (NEW)                          │
│          {"term": {                                           │
│            "active_experience_department":                   │
│              "Engineering and Technical"                     │
│          }}                                                   │
│        ]                                                      │
│      }                                                        │
│    }                                                          │
│  }                                                            │
│                                                               │
│  CoreSignal API Call:                                        │
│  POST /v2/employee_clean/search/es_dsl/preview?page=1        │
│  → Returns ~20-40 matching employees                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: Results Display with Post-Search Filters (NEW)      │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│  🎉 Found 47 candidates                                       │
│                                                               │
│  🔧 Refine Results (client-side, instant):                   │
│  Department: [All ▼]  Seniority: [All ▼]  Skills: [Any ▼]   │
│                                                               │
│  Showing 47 of 47 candidates                                 │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 👤 John Doe                                            │ │
│  │ Senior ML Engineer at Deepgram                         │ │
│  │ 📍 San Francisco, CA                                   │ │
│  │ 🏢 Engineering and Technical                           │ │
│  │ 🎯 8 years experience                                  │ │
│  │ 🔧 Python, PyTorch, LLMs, Voice AI                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 👤 Jane Smith                                          │ │
│  │ Staff AI Engineer at AssemblyAI                        │ │
│  │ 📍 Berkeley, CA                                        │ │
│  │ 🏢 Engineering and Technical                           │ │
│  │ 🎯 12 years experience                                 │ │
│  │ 🔧 Python, TensorFlow, NLP, Speech Recognition        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ... 45 more candidates ...                                  │
│                                                               │
│  [ 🔄 New Search with Different Filters ]                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## UI Mockups (ASCII)

### Mockup 1: Filter Preview (Before Search)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research Results                                       ┃
┃  ────────────────────────────────────────────────────────────   ┃
┃                                                                  ┃
┃  ✓ Selected 5 companies for employee search                     ┃
┃                                                                  ┃
┃  ☑ Deepgram                 (Score: 9.2/10)                     ┃
┃  ☑ AssemblyAI               (Score: 8.8/10)                     ┃
┃  ☑ Otter.ai                 (Score: 8.5/10)                     ┃
┃  ☑ Rev.ai                   (Score: 8.1/10)                     ┃
┃  ☑ Speechmatics             (Score: 7.9/10)                     ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 🔍 Configure Search Filters                                │ ┃ ← NEW
┃  │                                                            │ ┃
┃  │ 📍 Location                                                │ ┃
┃  │ ┌──────────────────────────────────────────┐              │ ┃
┃  │ │ San Francisco Bay Area                    │              │ ┃
┃  │ └──────────────────────────────────────────┘              │ ┃
┃  │ ☑ Required (strict filter)  ⓘ Limits to this location    │ ┃
┃  │                                                            │ ┃
┃  │ 💼 Role Keywords                                           │ ┃
┃  │ ┌──────────────────────────────────────────┐              │ ┃
┃  │ │ senior ml engineer, ai engineer          │              │ ┃
┃  │ └──────────────────────────────────────────┘              │ ┃
┃  │ ☑ Required (strict filter)  ⓘ Must match role title      │ ┃
┃  │                                                            │ ┃
┃  │ 🎯 Seniority Level                                         │ ┃
┃  │ ┌──────────────────────────────────────────┐              │ ┃
┃  │ │ Senior IC (5-10 years)                 ▼ │              │ ┃
┃  │ └──────────────────────────────────────────┘              │ ┃
┃  │                                                            │ ┃
┃  │ 🏢 Department (multi-select)                               │ ┃
┃  │ ☑ Engineering and Technical                                │ ┃
┃  │ ☐ Data Science                                             │ ┃
┃  │ ☐ Product Management                                       │ ┃
┃  │                                                            │ ┃
┃  │ 📊 Search Strategy                                         │ ┃
┃  │ ┌──────────────────────────────────────────┐              │ ┃
┃  │ │ ⚖️ Balanced (require role only)         ▼ │              │ ┃
┃  │ └──────────────────────────────────────────┘              │ ┃
┃  │ Options: 🎯 Precise | ⚖️ Balanced | 🌍 Broad               │ ┃
┃  │                                                            │ ┃
┃  │ [ 🔍 Search for People at 5 Companies ]                   │ ┃
┃  │                                                            │ ┃
┃  │ Estimated: 40-80 candidates matching filters               │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Mockup 2: Results with Post-Search Filters

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Employee Search Results                                        ┃
┃  ────────────────────────────────────────────────────────────   ┃
┃                                                                  ┃
┃  🎉 Found 47 candidates at 5 companies                           ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 🔧 Refine Results (instant filtering)                      │ ┃ ← NEW
┃  │                                                            │ ┃
┃  │ Department: [All ▼]  Seniority: [All ▼]  Skills: [Any ▼] │ ┃
┃  │                                                            │ ┃
┃  │ Showing 47 of 47 candidates  [ Clear Filters ]            │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 👤 John Doe                                                │ ┃
┃  │ Senior ML Engineer at Deepgram                             │ ┃
┃  │ 📍 San Francisco, CA  |  🏢 Engineering  |  🎯 8 yrs       │ ┃
┃  │ "Building real-time voice AI models with PyTorch..."      │ ┃
┃  │ 🔧 Python • PyTorch • LLMs • Voice AI • Real-time Systems │ ┃
┃  │                                                            │ ┃
┃  │ [ View Full Profile ]  [ Add to List ]                    │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 👤 Jane Smith                                              │ ┃
┃  │ Staff AI Engineer at AssemblyAI                            │ ┃
┃  │ 📍 Berkeley, CA  |  🏢 Engineering  |  🎯 12 yrs           │ ┃
┃  │ "Leading speech recognition R&D, NLP expertise..."        │ ┃
┃  │ 🔧 Python • TensorFlow • NLP • Speech Recognition • ASR   │ ┃
┃  │                                                            │ ┃
┃  │ [ View Full Profile ]  [ Add to List ]                    │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ... 45 more candidates ...                                     ┃
┃                                                                  ┃
┃  [ 🔄 New Search with Different Filters ]                       ┃
┃                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Mockup 3: Post-Search Filter Active

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Employee Search Results                                        ┃
┃  ────────────────────────────────────────────────────────────   ┃
┃                                                                  ┃
┃  🎉 Found 47 candidates at 5 companies                           ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 🔧 Refine Results (instant filtering)                      │ ┃
┃  │                                                            │ ┃
┃  │ Department: [Engineering ▼]  Seniority: [Staff+ ▼]        │ ┃ ← FILTERS ACTIVE
┃  │ Skills: [Python, PyTorch ▼]                                │ ┃
┃  │                                                            │ ┃
┃  │ Showing 12 of 47 candidates  [ Clear Filters ]            │ ┃ ← FILTERED COUNT
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ⓘ Filters applied: Engineering dept, Staff+ level, Python+PyTorch ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 👤 Jane Smith                                              │ ┃
┃  │ Staff AI Engineer at AssemblyAI                            │ ┃
┃  │ 📍 Berkeley, CA  |  🏢 Engineering  |  🎯 12 yrs           │ ┃
┃  │ "Leading speech recognition R&D, NLP expertise..."        │ ┃
┃  │ 🔧 Python • PyTorch • TensorFlow • NLP • Speech AI        │ ┃ ← MATCHES
┃  │                                                            │ ┃
┃  │ [ View Full Profile ]  [ Add to List ]                    │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ┌────────────────────────────────────────────────────────────┐ ┃
┃  │ 👤 Alex Chen                                               │ ┃
┃  │ Principal ML Engineer at Otter.ai                          │ ┃
┃  │ 📍 Mountain View, CA  |  🏢 Engineering  |  🎯 14 yrs      │ ┃
┃  │ "Building production ML systems for voice transcription"  │ ┃
┃  │ 🔧 Python • PyTorch • Kubernetes • MLOps • Voice AI       │ ┃ ← MATCHES
┃  │                                                            │ ┃
┃  │ [ View Full Profile ]  [ Add to List ]                    │ ┃
┃  └────────────────────────────────────────────────────────────┘ ┃
┃                                                                  ┃
┃  ... 10 more candidates ...                                     ┃
┃                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Implementation Code Examples

### Frontend: Filter State Management

```javascript
// frontend/src/App.js

// NEW: Filter state variables
const [searchFilters, setSearchFilters] = useState({
  location: '',
  requireLocation: false,
  roleKeywords: '',
  requireRole: false,
  seniorityLevel: '',
  department: [],
  searchStrategy: 'balanced'
});

// NEW: Post-search refinement filters
const [refinementFilters, setRefinementFilters] = useState({
  department: '',
  seniorityLevel: '',
  skills: []
});

// Initialize filters from JD when available
useEffect(() => {
  if (activeJD && activeJD.parsed_requirements) {
    const reqs = activeJD.parsed_requirements;
    setSearchFilters({
      location: reqs.location || '',
      requireLocation: false,
      roleKeywords: extractRoleKeywords(reqs.role_title, reqs.technical_skills),
      requireRole: true,  // Default to requiring role
      seniorityLevel: reqs.seniority_level || '',
      department: inferDepartment(reqs.role_title),
      searchStrategy: 'balanced'
    });
  }
}, [activeJD]);

// Helper: Infer department from role title
function inferDepartment(roleTitle) {
  const title = roleTitle.toLowerCase();
  if (title.includes('engineer') || title.includes('developer')) {
    return ['Engineering and Technical'];
  } else if (title.includes('data scientist') || title.includes('ml')) {
    return ['Data Science'];
  } else if (title.includes('product manager')) {
    return ['Product Management'];
  } else if (title.includes('designer') || title.includes('ux')) {
    return ['Design'];
  }
  return [];
}

// Helper: Extract role keywords
function extractRoleKeywords(roleTitle, skills) {
  const keywords = [roleTitle];
  // Add skill-based role variations
  if (skills.includes('Machine Learning')) {
    keywords.push('ml engineer', 'machine learning engineer');
  }
  return keywords.join(', ');
}
```

### Frontend: Filter Preview UI Component

```javascript
// frontend/src/App.js or new component: SearchFilterPreview.js

function SearchFilterPreview({ filters, onFiltersChange, onSearch, selectedCompanies }) {
  return (
    <div className="search-filter-preview">
      <h4>🔍 Configure Search Filters</h4>
      <p className="filter-hint">
        Smart defaults extracted from job description. Edit as needed.
      </p>

      {/* Location Filter */}
      <div className="filter-row">
        <label>📍 Location</label>
        <input
          type="text"
          value={filters.location}
          onChange={(e) => onFiltersChange({ ...filters, location: e.target.value })}
          placeholder="e.g., San Francisco Bay Area, Remote, United States"
        />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={filters.requireLocation}
            onChange={(e) => onFiltersChange({ ...filters, requireLocation: e.target.checked })}
          />
          Required (strict filter)
          <span className="hint">ⓘ Limits results to this location only</span>
        </label>
      </div>

      {/* Role Keywords Filter */}
      <div className="filter-row">
        <label>💼 Role Keywords</label>
        <input
          type="text"
          value={filters.roleKeywords}
          onChange={(e) => onFiltersChange({ ...filters, roleKeywords: e.target.value })}
          placeholder="e.g., senior ml engineer, ai engineer"
        />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={filters.requireRole}
            onChange={(e) => onFiltersChange({ ...filters, requireRole: e.target.checked })}
          />
          Required (strict filter)
          <span className="hint">ⓘ Must match job title or experience</span>
        </label>
      </div>

      {/* Seniority Filter */}
      <div className="filter-row">
        <label>🎯 Seniority Level</label>
        <select
          value={filters.seniorityLevel}
          onChange={(e) => onFiltersChange({ ...filters, seniorityLevel: e.target.value })}
        >
          <option value="">Any Level</option>
          <option value="junior">Junior (0-3 years)</option>
          <option value="mid">Mid-Level (3-5 years)</option>
          <option value="senior">Senior IC (5-10 years)</option>
          <option value="staff">Staff+ (10+ years)</option>
          <option value="manager">Manager</option>
          <option value="director">Director+</option>
          <option value="c-level">C-Suite</option>
        </select>
      </div>

      {/* Department Filter */}
      <div className="filter-row">
        <label>🏢 Department (multi-select)</label>
        <div className="department-checkboxes">
          {DEPARTMENT_OPTIONS.map(dept => (
            <label key={dept} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.department.includes(dept)}
                onChange={(e) => {
                  const updated = e.target.checked
                    ? [...filters.department, dept]
                    : filters.department.filter(d => d !== dept);
                  onFiltersChange({ ...filters, department: updated });
                }}
              />
              {dept}
            </label>
          ))}
        </div>
      </div>

      {/* Search Strategy */}
      <div className="filter-row">
        <label>📊 Search Strategy</label>
        <select
          value={filters.searchStrategy}
          onChange={(e) => onFiltersChange({ ...filters, searchStrategy: e.target.value })}
        >
          <option value="precise">🎯 Precise (require all filters)</option>
          <option value="balanced">⚖️ Balanced (require role only)</option>
          <option value="broad">🌍 Broad Discovery (all optional)</option>
        </select>
        <p className="strategy-hint">
          {filters.searchStrategy === 'precise' && 'Returns highly relevant candidates (narrower results)'}
          {filters.searchStrategy === 'balanced' && 'Good balance of relevance and coverage (recommended)'}
          {filters.searchStrategy === 'broad' && 'Returns all people at these companies (wider results)'}
        </p>
      </div>

      {/* Search Button */}
      <button className="search-button" onClick={onSearch}>
        🔍 Search for People at {selectedCompanies.length} Companies
      </button>

      <p className="estimate-hint">
        Estimated: 40-80 candidates matching these filters
      </p>
    </div>
  );
}

const DEPARTMENT_OPTIONS = [
  'Engineering and Technical',
  'Data Science',
  'Product Management',
  'C-Suite',
  'Operations',
  'Design',
  'Marketing',
  'Sales'
];
```

### Frontend: Post-Search Refinement Component

```javascript
// frontend/src/App.js or new component: ResultsRefinementFilters.js

function ResultsRefinementFilters({
  candidates,
  filters,
  onFiltersChange,
  onClearFilters
}) {
  const filteredCandidates = getFilteredCandidates(candidates, filters);
  const availableSkills = extractUniqueSkills(candidates);

  return (
    <div className="results-refinement-filters">
      <h4>🔧 Refine Results (instant filtering)</h4>

      <div className="filter-controls">
        {/* Department Filter */}
        <label>
          Department:
          <select
            value={filters.department}
            onChange={(e) => onFiltersChange({ ...filters, department: e.target.value })}
          >
            <option value="">All Departments</option>
            {DEPARTMENT_OPTIONS.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </label>

        {/* Seniority Filter */}
        <label>
          Seniority:
          <select
            value={filters.seniorityLevel}
            onChange={(e) => onFiltersChange({ ...filters, seniorityLevel: e.target.value })}
          >
            <option value="">All Levels</option>
            <option value="junior">Junior (0-3 yrs)</option>
            <option value="mid">Mid (3-5 yrs)</option>
            <option value="senior">Senior (5-10 yrs)</option>
            <option value="staff">Staff+ (10+ yrs)</option>
          </select>
        </label>

        {/* Skills Filter */}
        <label>
          Has Skills:
          <MultiSelect
            options={availableSkills}
            selected={filters.skills}
            onChange={(skills) => onFiltersChange({ ...filters, skills })}
            placeholder="Select skills..."
          />
        </label>

        <button onClick={onClearFilters} className="clear-filters-btn">
          Clear Filters
        </button>
      </div>

      <div className="filter-stats">
        Showing <strong>{filteredCandidates.length}</strong> of <strong>{candidates.length}</strong> candidates
        {filters.department || filters.seniorityLevel || filters.skills.length > 0 ? (
          <span className="filter-active-indicator">
            {' '}(filters active)
          </span>
        ) : null}
      </div>
    </div>
  );
}

function getFilteredCandidates(candidates, filters) {
  let filtered = [...candidates];

  // Department filter
  if (filters.department) {
    filtered = filtered.filter(c =>
      c.active_experience_department === filters.department
    );
  }

  // Seniority filter
  if (filters.seniorityLevel) {
    filtered = filtered.filter(c => {
      const years = calculateExperienceYears(c.experience || []);
      if (filters.seniorityLevel === 'junior') return years < 3;
      if (filters.seniorityLevel === 'mid') return years >= 3 && years < 5;
      if (filters.seniorityLevel === 'senior') return years >= 5 && years < 10;
      if (filters.seniorityLevel === 'staff') return years >= 10;
      return true;
    });
  }

  // Skills filter (AND logic - must have all selected skills)
  if (filters.skills.length > 0) {
    filtered = filtered.filter(c => {
      const candidateSkills = (c.skills || []).map(s => s.toLowerCase());
      return filters.skills.every(skill =>
        candidateSkills.some(cs => cs.includes(skill.toLowerCase()))
      );
    });
  }

  return filtered;
}

function calculateExperienceYears(experience) {
  if (!experience || experience.length === 0) return 0;

  // Calculate total years from all experience entries
  const totalMonths = experience.reduce((sum, exp) => {
    const start = new Date(exp.date_from);
    const end = exp.date_to ? new Date(exp.date_to) : new Date();
    const months = (end.getFullYear() - start.getFullYear()) * 12 +
                   (end.getMonth() - start.getMonth());
    return sum + Math.max(0, months);
  }, 0);

  return Math.round(totalMonths / 12);
}

function extractUniqueSkills(candidates) {
  const skillsSet = new Set();
  candidates.forEach(c => {
    if (c.skills) {
      c.skills.forEach(skill => skillsSet.add(skill));
    }
  });
  return Array.from(skillsSet).sort();
}
```

### Backend: Modified Query Builder

```python
# backend/jd_analyzer/api/domain_search.py

def build_experience_based_query(
    jd_requirements: Dict,
    search_config: Dict,  # NEW parameter
    companies: List[Dict],
    page: int = 1
) -> Dict:
    """
    Build Elasticsearch DSL query for employee search with filters.

    Args:
        jd_requirements: Job requirements dict (role, location, seniority, skills, department)
        search_config: Search configuration (require_role, require_location, search_strategy)
        companies: List of company dicts with coresignal_id
        page: Page number for pagination

    Returns:
        Elasticsearch DSL query dict
    """

    # Extract filters from JD requirements
    role_title = jd_requirements.get('role_title', '')
    location = jd_requirements.get('location', '')
    seniority_level = jd_requirements.get('seniority_level', '')
    technical_skills = jd_requirements.get('technical_skills', [])
    department = jd_requirements.get('department', [])

    # Extract search config
    require_role = search_config.get('require_role', False)
    require_location = search_config.get('require_location', False)
    search_strategy = search_config.get('search_strategy', 'balanced')

    # Apply strategy overrides
    if search_strategy == 'precise':
        require_role = True
        require_location = True
    elif search_strategy == 'broad':
        require_role = False
        require_location = False
    # 'balanced' uses provided require_* flags

    # Build base query
    query = {
        "query": {
            "bool": {
                "must": [],
                "should": [],
                "filter": [],
                "minimum_should_match": 0
            }
        },
        "from": (page - 1) * 20,
        "size": 20
    }

    # REQUIRED: Company filter (always in "must")
    company_ids = [c.get('coresignal_id') for c in companies if c.get('coresignal_id')]
    company_names = [c.get('name') for c in companies]

    company_filter = {
        "nested": {
            "path": "experience",
            "query": {
                "bool": {
                    "should": []
                }
            }
        }
    }

    if company_ids:
        company_filter["nested"]["query"]["bool"]["should"].append({
            "terms": {"experience.company_id": company_ids}
        })

    if company_names:
        for name in company_names:
            company_filter["nested"]["query"]["bool"]["should"].append({
                "match_phrase": {"experience.company_name": name}
            })

    company_filter["nested"]["query"]["bool"]["minimum_should_match"] = 1
    query["query"]["bool"]["must"].append(company_filter)

    # Role filter (required or boost based on config)
    if role_title:
        role_keywords = extract_precise_role_keywords(role_title, technical_skills)
        role_query = {
            "nested": {
                "path": "experience",
                "query": {
                    "query_string": {
                        "query": role_keywords,
                        "default_field": "experience.title",
                        "default_operator": "OR"
                    }
                }
            }
        }

        if require_role:
            query["query"]["bool"]["must"].append(role_query)
        else:
            query["query"]["bool"]["should"].append(role_query)

    # Location filter (required or boost based on config)
    if location:
        location_query = {"term": {"location": location}}

        if require_location:
            query["query"]["bool"]["must"].append(location_query)
        else:
            query["query"]["bool"]["should"].append(location_query)

    # Seniority filter (NEW - always applied if specified)
    if seniority_level:
        seniority_query = build_seniority_filter(seniority_level)
        if seniority_query:
            query["query"]["bool"]["filter"].append(seniority_query)

    # Department filter (NEW - always applied if specified)
    if department and len(department) > 0:
        department_query = {
            "terms": {"active_experience_department": department}
        }
        query["query"]["bool"]["filter"].append(department_query)

    return query


def build_seniority_filter(seniority_level: str) -> Dict:
    """
    Build seniority filter query.

    Uses combination of:
    - Title keywords ("Senior", "Staff", "Principal")
    - Years of experience (calculated field)
    - Management level field (for managers/directors)
    """
    if seniority_level == "junior":
        return {
            "bool": {
                "should": [
                    {"match": {"active_experience_title": "junior associate"}},
                    {"range": {"experience_years": {"lt": 3}}}
                ],
                "minimum_should_match": 1
            }
        }

    elif seniority_level == "mid":
        return {
            "bool": {
                "must": [
                    {"range": {"experience_years": {"gte": 3, "lte": 5}}}
                ],
                "must_not": [
                    {"match": {"active_experience_title": "senior staff principal"}}
                ]
            }
        }

    elif seniority_level == "senior":
        return {
            "bool": {
                "should": [
                    {"match": {"active_experience_title": "senior"}},
                    {"range": {"experience_years": {"gte": 5, "lte": 10}}}
                ],
                "minimum_should_match": 1,
                "must_not": [
                    {"match": {"active_experience_title": "staff principal"}}
                ]
            }
        }

    elif seniority_level == "staff":
        return {
            "bool": {
                "should": [
                    {"match": {"active_experience_title": "staff principal"}},
                    {"range": {"experience_years": {"gte": 10}}}
                ],
                "minimum_should_match": 1
            }
        }

    elif seniority_level == "manager":
        return {"term": {"active_experience_management_level": "Manager"}}

    elif seniority_level == "director":
        return {"terms": {"active_experience_management_level": ["Director", "C-level"]}}

    elif seniority_level == "c-level":
        return {"term": {"active_experience_management_level": "C-level"}}

    else:
        return {}  # No seniority filter


def extract_precise_role_keywords(role_title: str, technical_skills: List[str]) -> str:
    """
    Extract precise role keywords for query_string query.

    Args:
        role_title: Job role title (e.g., "Senior ML Engineer")
        technical_skills: List of technical skills (e.g., ["Python", "PyTorch"])

    Returns:
        Query string with OR'd keywords
    """
    keywords = []

    # Add exact role title as phrase
    keywords.append(f'"{role_title.lower()}"')

    # Add role variations
    if "ml engineer" in role_title.lower():
        keywords.extend([
            '"machine learning engineer"',
            '"ai engineer"',
            '"ml scientist"'
        ])
    elif "data scientist" in role_title.lower():
        keywords.extend([
            '"data science"',
            '"ml scientist"',
            '"research scientist"'
        ])
    elif "software engineer" in role_title.lower():
        keywords.extend([
            '"backend engineer"',
            '"full stack engineer"',
            '"platform engineer"'
        ])

    # Join with OR
    return ' OR '.join(keywords)
```

---

## Testing Plan

### Unit Tests

**File:** `backend/tests/test_iterative_people_search.py`

```python
def test_build_query_with_all_filters():
    """Test query builder with all filters enabled."""
    jd_requirements = {
        'role_title': 'Senior ML Engineer',
        'location': 'San Francisco Bay Area',
        'seniority_level': 'senior',
        'department': ['Engineering and Technical']
    }

    search_config = {
        'require_role': True,
        'require_location': True,
        'search_strategy': 'precise'
    }

    companies = [
        {'name': 'Deepgram', 'coresignal_id': 3829471}
    ]

    query = build_experience_based_query(jd_requirements, search_config, companies)

    # Check company filter in "must"
    assert any('experience.company_id' in str(clause) for clause in query['query']['bool']['must'])

    # Check role filter in "must" (because require_role=True)
    assert len([c for c in query['query']['bool']['must'] if 'experience.title' in str(c)]) > 0

    # Check location filter in "must" (because require_location=True)
    assert any('location' in str(clause) for clause in query['query']['bool']['must'])

    # Check seniority filter in "filter"
    assert len(query['query']['bool']['filter']) > 0
    assert 'senior' in str(query['query']['bool']['filter'][0]).lower()

    # Check department filter in "filter"
    assert any('active_experience_department' in str(clause)
               for clause in query['query']['bool']['filter'])

def test_build_query_balanced_strategy():
    """Test query builder with balanced strategy (default)."""
    jd_requirements = {
        'role_title': 'ML Engineer',
        'location': 'Remote',
        'seniority_level': ''  # No seniority filter
    }

    search_config = {
        'search_strategy': 'balanced'
    }

    companies = [{'name': 'Test Co', 'coresignal_id': 123}]

    query = build_experience_based_query(jd_requirements, search_config, companies)

    # Role should be in "must" (balanced requires role)
    assert any('experience.title' in str(clause) for clause in query['query']['bool']['must'])

    # Location should be in "should" (optional boost)
    assert any('location' in str(clause) for clause in query['query']['bool']['should'])

    # No seniority filter
    assert len(query['query']['bool']['filter']) == 0

def test_build_query_broad_strategy():
    """Test query builder with broad discovery strategy."""
    jd_requirements = {
        'role_title': 'Engineer',
        'location': 'United States'
    }

    search_config = {
        'search_strategy': 'broad'
    }

    companies = [{'name': 'Test Co', 'coresignal_id': 123}]

    query = build_experience_based_query(jd_requirements, search_config, companies)

    # Only company filter should be in "must"
    assert len(query['query']['bool']['must']) == 1

    # Role and location should be in "should" (optional)
    assert len(query['query']['bool']['should']) == 2

def test_seniority_filter_senior():
    """Test senior seniority filter."""
    filter_query = build_seniority_filter('senior')

    # Should check for "senior" in title OR 5-10 years experience
    assert 'should' in filter_query['bool']
    assert len(filter_query['bool']['should']) == 2
    assert filter_query['bool']['minimum_should_match'] == 1

def test_seniority_filter_staff():
    """Test staff+ seniority filter."""
    filter_query = build_seniority_filter('staff')

    # Should check for "staff" or "principal" in title OR 10+ years
    assert 'should' in filter_query['bool']
    assert any('staff principal' in str(clause).lower()
               for clause in filter_query['bool']['should'])

def test_client_side_filtering():
    """Test client-side post-search filtering."""
    candidates = [
        {
            'name': 'John Doe',
            'active_experience_department': 'Engineering and Technical',
            'experience': [
                {'date_from': '2015-01-01', 'date_to': '2020-01-01'},  # 5 years
                {'date_from': '2020-01-01', 'date_to': None}  # 5 years to now
            ],
            'skills': ['Python', 'PyTorch', 'ML']
        },
        {
            'name': 'Jane Smith',
            'active_experience_department': 'Sales',
            'experience': [
                {'date_from': '2020-01-01', 'date_to': None}  # 5 years
            ],
            'skills': ['Salesforce', 'Negotiation']
        }
    ]

    # Filter: Engineering only
    filters = {'department': 'Engineering and Technical', 'seniorityLevel': '', 'skills': []}
    filtered = getFilteredCandidates(candidates, filters)
    assert len(filtered) == 1
    assert filtered[0]['name'] == 'John Doe'

    # Filter: Skills = Python
    filters = {'department': '', 'seniorityLevel': '', 'skills': ['Python']}
    filtered = getFilteredCandidates(candidates, filters)
    assert len(filtered) == 1
    assert filtered[0]['name'] == 'John Doe'

    # Filter: Senior level (5-10 years)
    filters = {'department': '', 'seniorityLevel': 'senior', 'skills': []}
    filtered = getFilteredCandidates(candidates, filters)
    assert len(filtered) == 1  # Only John with 10 years total
```

### Integration Tests

```python
def test_end_to_end_people_search_with_filters():
    """Test complete flow from filter UI to results."""
    # Step 1: User configures filters
    search_request = {
        'jd_requirements': {
            'role_title': 'Senior ML Engineer',
            'location': 'San Francisco Bay Area',
            'seniority_level': 'senior',
            'department': ['Engineering and Technical']
        },
        'search_config': {
            'require_role': True,
            'require_location': False,
            'search_strategy': 'balanced'
        },
        'mentioned_companies': [
            {'name': 'Deepgram', 'coresignal_id': 3829471}
        ],
        'max_previews': 100
    }

    # Step 2: Make API call
    response = client.post('/api/jd/domain-company-preview-search', json=search_request)

    assert response.status_code == 200
    data = response.get_json()

    # Step 3: Verify results
    assert 'stage2_previews' in data
    candidates = data['stage2_previews']

    # All candidates should match filters
    for candidate in candidates:
        # Should have engineering department (filter was applied)
        assert candidate.get('active_experience_department') == 'Engineering and Technical'

        # Should have relevant role (filter was required)
        assert 'engineer' in candidate.get('job_title', '').lower() or \
               'engineer' in candidate.get('active_experience_title', '').lower()
```

---

## Success Metrics

### Primary Metrics

**1. Filter Adoption Rate**
- **Formula:** `(searches with custom filters / total searches) × 100%`
- **Target:** 60%+ of searches customize at least one filter
- **Measurement:** Track filter changes from default values

**2. Refinement Usage Rate**
- **Formula:** `(searches using post-search filters / total searches) × 100%`
- **Target:** 40%+ use post-search refinement
- **Measurement:** Track client-side filter interactions

**3. Candidate Relevance Score**
- **Formula:** User feedback on candidate quality (1-5 stars)
- **Target:** 4.0+ average rating
- **Measurement:** Post-search survey

**4. API Credit Efficiency**
- **Formula:** `relevant_candidates / total_candidates_fetched`
- **Target:** 70%+ relevance rate (vs. 30-40% currently)
- **Measurement:** Compare fetch count to filtered results

### Secondary Metrics

**5. Time to Find Right Candidates**
- **Formula:** Time from "Search for People" click to "Add to List" action
- **Target:** 50% reduction (3 min → 1.5 min)
- **Measurement:** Frontend timing analytics

**6. Searches Per Session**
- **Formula:** Average number of people searches per company research session
- **Target:** 1.5-2.0 (down from 3-4 with current trial-and-error)
- **Measurement:** Session analytics

---

## Rollout Plan

### Phase 1: Pre-Search Filters (Week 1-2)
- Implement filter preview UI
- Modify backend query builder
- Add seniority and department filtering
- Deploy to staging for testing

### Phase 2: Post-Search Refinement (Week 3)
- Add refinement filter UI above results
- Implement client-side filtering logic
- Add filter stats display
- Deploy to production (100%)

### Phase 3: Saved Presets (Week 4+)
- Add preset management UI
- Implement save/load/delete functionality
- Add quick-apply buttons
- Optional: Team sharing

---

## Appendix

### A. CoreSignal Department Full List

```
"C-Suite"
"Engineering and Technical"
"Data Science"
"Product Management"
"Operations"
"Marketing"
"Sales"
"Customer Service"
"Finance & Accounting"
"Human Resources"
"Information Technology"
"Research and Development"
"Design"
"Business Development"
"Consulting"
"Legal"
"Quality Assurance"
"Supply Chain"
"Manufacturing"
"Education and Training"
"Healthcare"
"Other"
```

### B. Code Locations Reference

**Frontend:**
- Button rendering: `frontend/src/App.js:4219-4259`
- Handler: `handleStartDomainSearch()` at line 2110
- State variables: Lines 165-168

**Backend:**
- Endpoint: `backend/jd_analyzer/api/domain_search.py:2021-2257`
- Query builder: `build_experience_based_query()` lines 489-638
- Role extraction: `extract_precise_role_keywords()` lines 644-743

**API Reference:**
- Field taxonomy: `backend/coresignal_api_taxonomy.py`
- Field docs: `backend/jd_analyzer/docs/CORESIGNAL_FIELD_REFERENCE.md`

---

**Status:** Ready for implementation ✅
**Estimated Effort:** 3-4 days for Phases 1-2
**Expected Value:** 70%+ candidate relevance (vs. 30-40% currently)

**Questions?** See implementation code examples above or contact engineering team.
