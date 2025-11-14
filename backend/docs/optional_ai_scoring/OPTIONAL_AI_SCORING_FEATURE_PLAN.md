# Optional AI Scoring Feature Plan

**Feature:** Skip Claude Haiku AI Scoring for Faster Company Research
**Feature Request ID:** #2
**Status:** Planning Phase
**Last Updated:** November 12, 2025
**Owner:** Engineering Team

---

## Executive Summary

### Problem Statement

The company research pipeline currently performs **mandatory Claude Haiku AI scoring** on all ~100 discovered companies, which:

- **Takes 90-150+ seconds** (more than half of total pipeline time)
- **Costs ~$150 per search** (81% of total pipeline cost)
- **Blocks users from seeing results** until all scoring completes
- **May not always be necessary** when users want quick discovery without AI evaluation

**Current Pipeline Performance:**
```
Phase 1: Discovery            30-45s    $20     (Required)
Phase 2: AI Scoring          90-150s   $150     ← TARGET TO MAKE OPTIONAL
Phase 3: Employee Sampling    30-40s    $15     (Required)
Phase 4: Sort & Return         <1s      $0      (Required)
───────────────────────────────────────────────
TOTAL:                      150-235s   $185
```

### Solution

Add a **UI checkbox** in the company research form that allows users to:
1. **Enable AI Scoring** (default): Full Claude Haiku evaluation with relevance scores 1-10
2. **Skip AI Scoring**: Fast discovery with default 5.0 scores, no AI evaluation

**With AI Scoring Skipped:**
```
Phase 1: Discovery            30-45s    $20
Phase 2: AI Scoring          SKIPPED   SKIPPED  ← 64% time savings, 81% cost savings
Phase 3: Employee Sampling    30-40s    $15
Phase 4: Sort & Return         <1s      $0
───────────────────────────────────────────────
TOTAL:                       60-85s     $35
```

### Business Value

**Speed Benefits:**
- ⚡ **64% faster results** (60-85s vs 150-235s)
- 🚀 **Quick discovery mode** for exploratory searches
- 👁️ **See companies sooner** without waiting for AI scoring

**Cost Benefits:**
- 💰 **81% cost reduction** ($35 vs $185 per search)
- 📊 **Budget-friendly option** for high-volume users
- 🎯 **Pay for value** - only use AI when needed

**User Experience Benefits:**
- ✅ **User control** - choose speed vs depth
- 🔄 **Iterative workflow** - quick discovery first, AI scoring later (future feature)
- 🎨 **Transparent trade-offs** - clear explanation of what's skipped

### Use Cases

**When to Skip AI Scoring:**
1. **Exploratory searches** - "What companies exist in this space?"
2. **Budget-conscious users** - Want to save API credits
3. **Time-sensitive searches** - Need results quickly
4. **Familiar domains** - User can manually assess relevance
5. **Large-scale research** - Discovering 100+ companies, will filter manually

**When to Enable AI Scoring:**
1. **Decision-making searches** - Need AI-validated relevance scores
2. **Unfamiliar domains** - Want AI assistance with company evaluation
3. **Client deliverables** - Need scored rankings for reports
4. **Quality over speed** - Willing to wait for better results

---

## Current State Analysis

### Existing Pipeline Architecture

**Main Flow:** `research_companies_for_jd()` in `company_research_service.py:117-290`

```
User Input (JD + Domain)
    ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 1: DISCOVERY (30-45s, $20)                       │
│ ──────────────────────────────────────────────────      │
│ • discover_companies() - lines 153-163                  │
│ • Tavily API searches (seed expansion + web)            │
│ • CoreSignal ID lookup (4-tier hybrid)                  │
│ • Result: ~100 unique companies with IDs                │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 2: AI SCORING (90-150s, $150) ← MAKE OPTIONAL    │
│ ──────────────────────────────────────────────────      │
│ • screen_companies_with_haiku() - lines 165-183         │
│ • Method implementation: lines 675-782                  │
│ • Claude Haiku 4.5 with web_search tool                │
│ • Process: ONE company at a time (not batched)          │
│ • Rate limit: 1.5s delay between companies              │
│ • Output: relevance_score (1-10), screening_reasoning   │
│ • Status: scored_by = 'claude_haiku_with_websearch'     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 3: EMPLOYEE SAMPLING (30-40s, $15)               │
│ ──────────────────────────────────────────────────────  │
│ • _add_sample_employees_to_companies() - lines 185-200  │
│ • CoreSignal employee search (3-5 per company)          │
│ • Result: Proof of talent pool                          │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 4: SORT & RETURN (<1s, $0)                       │
│ ──────────────────────────────────────────────────────  │
│ • Sort by relevance_score DESC                          │
│ • Return enriched company objects                       │
└─────────────────────────────────────────────────────────┘
    ↓
Frontend Display (Company Cards)
```

### Phase 2 Deep Dive: Claude Haiku Screening

**Method:** `screen_companies_with_haiku()` - lines 675-782

**How It Works:**
```python
async def screen_companies_with_haiku(
    self,
    companies: List[Dict],
    jd_context: Dict,
    jd_id: str
) -> List[Dict]:
    """
    Screen companies using Claude Haiku 4.5 with web search.

    For EACH company:
    1. Build prompt with JD context + company name
    2. Call Anthropic API with web_search tool enabled
    3. Claude researches company online in real-time
    4. Returns relevance score (1-10) + reasoning (2-3 sentences)
    5. Wait 1.5s (rate limit protection)

    Cost: ~$1.50 per company × 100 companies = $150
    Time: 100 companies × 1.5s = 150+ seconds minimum
    """

    for company in companies:
        # Build screening prompt
        prompt = f"""
        JD Context: {jd_context}
        Company: {company['name']}

        Research this company and evaluate relevance (1-10).
        Use web search to find latest information.
        """

        # Call Anthropic API with web_search tool
        response = await anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            tools=[{"type": "web_search_20250305"}],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract score and reasoning
        company['relevance_score'] = extract_score(response)
        company['screening_reasoning'] = extract_reasoning(response)
        company['scored_by'] = 'claude_haiku_with_websearch'

        # Rate limit protection
        await asyncio.sleep(1.5)
```

**Why It's Expensive:**
1. **Sequential processing** - One company at a time (not batched)
2. **Web search enabled** - Each call uses real-time web search tool
3. **100 companies** - Full discovered list gets scored
4. **API costs** - Claude Haiku + web search = ~$1.50 per company
5. **Rate limiting** - 1.5s delay between calls to avoid 429 errors

**What It Provides:**
- `relevance_score`: 1-10 numeric score (used for sorting)
- `screening_reasoning`: 2-3 sentence explanation
- `scored_by`: Attribution ('claude_haiku_with_websearch')

**What Happens If Skipped:**
- Companies still returned (name, domain, CoreSignal ID, employees)
- No relevance score → assign default 5.0
- No AI reasoning → show "AI scoring was skipped"
- Manual review required (user filters/sorts manually)

---

## Technical Architecture

### System Overview with Optional Scoring

```
┌──────────────────────────────────────────────────────────┐
│ FRONTEND: Company Research Form                         │
│ ──────────────────────────────────────────────────────── │
│                                                           │
│  Job Description Input:                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Paste job description here...                    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ☑ Enable AI scoring with Claude Haiku           │ ←──┼─── NEW CHECKBOX
│  │   (~2-3 min slower, relevance scores 1-10)       │    │
│  │                                                   │    │
│  │ Cost: $185 | Time: ~3 min                        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  [ Start Company Research ]                              │
│                                                           │
└──────────────────────────────────────────────────────────┘
            ↓
            POST /research-companies
            {
              "jd_text": "...",
              "skip_ai_scoring": true/false  ← NEW PARAMETER
            }
            ↓
┌──────────────────────────────────────────────────────────┐
│ BACKEND: research_companies_for_jd()                     │
│ ──────────────────────────────────────────────────────── │
│                                                           │
│  Phase 1: Discovery                                      │
│  • discover_companies() → 100 companies                  │
│                                                           │
│  Phase 2: AI Scoring (CONDITIONAL)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ if config.get('skip_ai_scoring', False):         │ ←──┼─── SKIP LOGIC
│  │     # Assign default scores (instant)            │    │
│  │     for company in companies:                    │    │
│  │         company['relevance_score'] = 5.0         │    │
│  │         company['screening_reasoning'] = '...'   │    │
│  │         company['scored_by'] = 'default_no_ai'   │    │
│  │ else:                                             │    │
│  │     # Full Claude Haiku screening                │    │
│  │     await screen_companies_with_haiku(...)       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  Phase 3: Employee Sampling                              │
│  • _add_sample_employees_to_companies() → 3-5 each       │
│                                                           │
│  Phase 4: Sort & Return                                  │
│  • Sort by relevance_score (all 5.0 if skipped)         │
│                                                           │
└──────────────────────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────────────┐
│ FRONTEND: Company Results Display                       │
│ ──────────────────────────────────────────────────────── │
│                                                           │
│  ⚠️ AI scoring was skipped for faster results            │ ←──┼─── BANNER (if skipped)
│     Companies show default scores (5.0)                   │    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🏢 Deepgram                                      │    │
│  │ Score: 5.0/10 (No AI scoring)                   │    │
│  │ Domain: deepgram.com                             │    │
│  │ Sample Employees: John Doe, Jane Smith...       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  [ Filter by relevance disabled when AI skipped ]       │    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Part 1: Backend Changes

#### 1.1 Add Request Parameter

**File:** `backend/app.py`
**Location:** Line 2991 - `/research-companies` endpoint

**Current Code (lines 3022-3026):**
```python
@app.route('/research-companies', methods=['POST'])
def research_companies():
    data = request.get_json()
    jd_text = data.get('jd_text')
    jd_id = data.get('jd_id')

    config = {
        'use_cache': data.get('use_cache', True),
        'max_companies': data.get('max_companies', 100)
    }
```

**New Code:**
```python
@app.route('/research-companies', methods=['POST'])
def research_companies():
    data = request.get_json()
    jd_text = data.get('jd_text')
    jd_id = data.get('jd_id')
    skip_ai_scoring = data.get('skip_ai_scoring', False)  # ✅ NEW

    config = {
        'use_cache': data.get('use_cache', True),
        'max_companies': data.get('max_companies', 100),
        'skip_ai_scoring': skip_ai_scoring  # ✅ NEW
    }
```

#### 1.2 Add Skip Logic to Service Method

**File:** `backend/company_research_service.py`
**Location:** Lines 165-183 - AI scoring phase

**Current Code:**
```python
# Phase 2: Claude Haiku Screening with Web Search
print(f"\n{'='*80}")
print(f"[SCREENING] Starting Claude Haiku screening with web search...")
print(f"[SCREENING] Processing {len(discovered)} companies")
print(f"{'='*80}\n")

await self.screen_companies_with_haiku(
    companies=discovered,
    jd_context=jd_context,
    jd_id=jd_id
)

print(f"\n[SCREENING] ✓ Screening complete")
print(f"[SCREENING] Screened {len(discovered)} companies with relevance scores\n")
```

**New Code:**
```python
# Phase 2: Claude Haiku Screening with Web Search (CONDITIONAL)
skip_ai_scoring = config.get('skip_ai_scoring', False)

if skip_ai_scoring:
    # ✅ SKIP AI SCORING - Assign default scores
    print(f"\n{'='*80}")
    print(f"[SCREENING] ⚡ AI scoring SKIPPED by user")
    print(f"[SCREENING] Assigning default scores to {len(discovered)} companies")
    print(f"{'='*80}\n")

    for company in discovered:
        company['relevance_score'] = 5.0
        company['screening_score'] = 5.0
        company['scored_by'] = 'default_no_ai'
        company['screening_reasoning'] = (
            'AI scoring was skipped for faster results. '
            'This company has not been evaluated by Claude Haiku.'
        )

    print(f"\n[SCREENING] ✓ Default scores assigned")
    print(f"[SCREENING] {len(discovered)} companies ready for display\n")

else:
    # ✅ FULL AI SCORING - Claude Haiku with web search
    print(f"\n{'='*80}")
    print(f"[SCREENING] Starting Claude Haiku screening with web search...")
    print(f"[SCREENING] Processing {len(discovered)} companies")
    print(f"{'='*80}\n")

    await self.screen_companies_with_haiku(
        companies=discovered,
        jd_context=jd_context,
        jd_id=jd_id
    )

    print(f"\n[SCREENING] ✓ Screening complete")
    print(f"[SCREENING] Screened {len(discovered)} companies with relevance scores\n")
```

#### 1.3 Update Response Metadata

**File:** `backend/company_research_service.py`
**Location:** Lines 270-290 - Return response

**Add metadata about AI scoring:**
```python
return {
    'discovered_companies': discovered,
    'screened_companies': discovered,  # Same after Phase 2
    'metadata': {
        'total_discovered': len(discovered),
        'total_screened': len(discovered),
        'ai_scoring_enabled': not skip_ai_scoring,  # ✅ NEW
        'scored_by': discovered[0].get('scored_by') if discovered else None,  # ✅ NEW
        'pipeline_phases': {
            'discovery': True,
            'ai_scoring': not skip_ai_scoring,  # ✅ NEW
            'employee_sampling': True
        }
    }
}
```

---

### Part 2: Frontend Changes

#### 2.1 Add Checkbox State

**File:** `frontend/src/App.js`
**Location:** Around line 100 (with other state variables)

**Add new state:**
```javascript
// Company research settings
const [skipAiScoring, setSkipAiScoring] = useState(false);
```

#### 2.2 Add Checkbox to UI Form

**File:** `frontend/src/App.js`
**Location:** Around line 3556-3567 (JD input section)

**Current UI Structure:**
```javascript
<div className="jd-input-section">
  <h3>Step 1: Enter Job Requirements</h3>
  <textarea
    value={jdText}
    onChange={(e) => setJdText(e.target.value)}
    placeholder="Paste job description..."
  />
  <button onClick={handleStartCompanyResearch}>
    Start Company Research
  </button>
</div>
```

**New UI Structure:**
```javascript
<div className="jd-input-section">
  <h3>Step 1: Enter Job Requirements</h3>
  <textarea
    value={jdText}
    onChange={(e) => setJdText(e.target.value)}
    placeholder="Paste job description..."
  />

  {/* ✅ NEW: AI Scoring Options */}
  <div className="research-options">
    <label className="checkbox-option">
      <input
        type="checkbox"
        checked={skipAiScoring}
        onChange={(e) => setSkipAiScoring(e.target.checked)}
      />
      <span className="checkbox-label">
        <strong>⚡ Skip AI scoring</strong> for faster, cheaper results
      </span>
    </label>

    <div className="option-details">
      {skipAiScoring ? (
        <div className="option-info skip">
          <span className="time-badge">⏱️ ~1 min</span>
          <span className="cost-badge">💰 $35</span>
          <span className="warning-text">
            ⚠️ Companies will show default scores (5.0) without AI evaluation
          </span>
        </div>
      ) : (
        <div className="option-info full">
          <span className="time-badge">⏱️ ~3 min</span>
          <span className="cost-badge">💰 $185</span>
          <span className="info-text">
            ✓ Claude Haiku will score each company's relevance (1-10)
          </span>
        </div>
      )}
    </div>
  </div>

  <button onClick={handleStartCompanyResearch}>
    Start Company Research
  </button>
</div>
```

#### 2.3 Update API Call

**File:** `frontend/src/App.js`
**Location:** Line 3633-3644 (handleStartCompanyResearch function)

**Current Code:**
```javascript
const handleStartCompanyResearch = async () => {
  setResearchInProgress(true);

  const response = await fetch('/research-companies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jd_text: jdText,
      jd_id: activeJD?.id
    })
  });

  // ...
};
```

**New Code:**
```javascript
const handleStartCompanyResearch = async () => {
  setResearchInProgress(true);

  // ✅ Update notification based on settings
  const notificationText = skipAiScoring
    ? 'Starting company research (AI scoring disabled for faster results)...'
    : 'Starting company research with full AI scoring...';

  // Show notification (if you have notification system)
  // showNotification(notificationText);

  const response = await fetch('/research-companies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jd_text: jdText,
      jd_id: activeJD?.id,
      skip_ai_scoring: skipAiScoring  // ✅ NEW
    })
  });

  // ...
};
```

#### 2.4 Add Banner to Results Display

**File:** `frontend/src/App.js`
**Location:** Around line 4055 (company results rendering)

**Add banner if AI scoring was skipped:**
```javascript
{companyResearchResults.length > 0 && (
  <div className="company-results-section">
    <h3>Company Research Results</h3>

    {/* ✅ NEW: Warning banner if AI scoring was skipped */}
    {researchMetadata?.ai_scoring_enabled === false && (
      <div className="info-banner warning">
        <span className="banner-icon">⚠️</span>
        <div className="banner-content">
          <strong>AI scoring was skipped</strong>
          <p>
            Companies show default scores (5.0) for faster results.
            You can manually review companies or re-run with AI scoring enabled.
          </p>
        </div>
      </div>
    )}

    {/* Existing company cards... */}
    {companyResearchResults.map(company => (
      <CompanyCard key={company.id} company={company} />
    ))}
  </div>
)}
```

#### 2.5 Update Score Display in Company Cards

**File:** `frontend/src/App.js`
**Location:** Around line 4373-4640 (company card rendering)

**Update score display to show attribution:**
```javascript
<div className="company-score">
  <span className="score-value">{company.relevance_score}/10</span>

  {/* ✅ NEW: Show scoring method */}
  {company.scored_by === 'default_no_ai' ? (
    <span className="score-badge default">Default (No AI)</span>
  ) : (
    <span className="score-badge ai">AI Scored</span>
  )}
</div>
```

#### 2.6 Disable Relevance Filter When Skipped

**File:** `frontend/src/App.js`
**Location:** Company filter pills section

**Disable relevance filter if all scores are 5.0:**
```javascript
const allScoresDefault = companyResearchResults.every(
  c => c.relevance_score === 5.0 && c.scored_by === 'default_no_ai'
);

// ...

<button
  className={`filter-pill ${activeFilter === 'high-relevance' ? 'active' : ''}`}
  onClick={() => setActiveFilter('high-relevance')}
  disabled={allScoresDefault}  // ✅ NEW
  title={allScoresDefault ? 'AI scoring was skipped - filter unavailable' : ''}
>
  High Relevance (8+)
  {allScoresDefault && <span className="disabled-badge">N/A</span>}
</button>
```

---

### Part 3: CSS Styling

**File:** `frontend/src/App.css`
**Location:** End of file

**Add styles for new UI elements:**
```css
/* Research Options Section */
.research-options {
  margin: 20px 0;
  padding: 16px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

.checkbox-option {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
}

.checkbox-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin-right: 10px;
  cursor: pointer;
}

.checkbox-label {
  color: #212529;
}

.checkbox-label strong {
  color: #0066cc;
}

.option-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #dee2e6;
}

.option-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.time-badge,
.cost-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.time-badge {
  background: #e3f2fd;
  color: #1976d2;
}

.cost-badge {
  background: #fff3e0;
  color: #f57c00;
}

.warning-text {
  color: #f57c00;
  font-size: 13px;
}

.info-text {
  color: #28a745;
  font-size: 13px;
}

/* Info Banner */
.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  margin-bottom: 20px;
  border-radius: 8px;
  border-left: 4px solid;
}

.info-banner.warning {
  background: #fff3cd;
  border-left-color: #ffc107;
}

.banner-icon {
  font-size: 24px;
  line-height: 1;
}

.banner-content {
  flex: 1;
}

.banner-content strong {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  color: #856404;
}

.banner-content p {
  margin: 0;
  font-size: 13px;
  color: #856404;
  line-height: 1.5;
}

/* Score Badges */
.score-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-left: 8px;
}

.score-badge.default {
  background: #e0e0e0;
  color: #616161;
}

.score-badge.ai {
  background: #e3f2fd;
  color: #1976d2;
}

/* Disabled Filter Pill */
.filter-pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.disabled-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  font-size: 10px;
}
```

---

## UI Mockups (ASCII)

### Before: Company Research Form (Current)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research                                          ┃
┃  ────────────────────────────────────────────────────      ┃
┃                                                             ┃
┃  Step 1: Enter Job Requirements                            ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ We're looking for an ML Engineer with experience   │  ┃
┃  │ in voice AI and real-time systems...               │  ┃
┃  │                                                     │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  [ Start Company Research ]                                ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### After: Company Research Form (With Checkbox)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research                                          ┃
┃  ────────────────────────────────────────────────────      ┃
┃                                                             ┃
┃  Step 1: Enter Job Requirements                            ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ We're looking for an ML Engineer with experience   │  ┃
┃  │ in voice AI and real-time systems...               │  ┃
┃  │                                                     │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ ☐ ⚡ Skip AI scoring for faster, cheaper results   │  ┃ ← NEW
┃  │                                                     │  ┃
┃  │ ─────────────────────────────────────────────────  │  ┃
┃  │ ⏱️ ~3 min  💰 $185                                  │  ┃
┃  │ ✓ Claude Haiku will score each company (1-10)      │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  [ Start Company Research ]                                ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### After: Company Research Form (Checkbox CHECKED)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research                                          ┃
┃  ────────────────────────────────────────────────────      ┃
┃                                                             ┃
┃  Step 1: Enter Job Requirements                            ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ We're looking for an ML Engineer with experience   │  ┃
┃  │ in voice AI and real-time systems...               │  ┃
┃  │                                                     │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ ☑ ⚡ Skip AI scoring for faster, cheaper results   │  ┃ ← CHECKED
┃  │                                                     │  ┃
┃  │ ─────────────────────────────────────────────────  │  ┃
┃  │ ⏱️ ~1 min  💰 $35                                   │  ┃ ← UPDATED
┃  │ ⚠️ Companies will show default scores (5.0)        │  ┃ ← WARNING
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  [ Start Company Research ]                                ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Results Display (AI Scoring Skipped)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research Results                                  ┃
┃  ────────────────────────────────────────────────────      ┃
┃                                                             ┃
┃  ┌───────────────────────────────────────────────────┐    ┃
┃  │ ⚠️  AI scoring was skipped                         │    ┃ ← BANNER
┃  │                                                    │    ┃
┃  │  Companies show default scores (5.0) for faster   │    ┃
┃  │  results. You can manually review companies or    │    ┃
┃  │  re-run with AI scoring enabled.                  │    ┃
┃  └───────────────────────────────────────────────────┘    ┃
┃                                                             ┃
┃  Filters: [ All ] [ High Relevance (8+) N/A ]  ← DISABLED ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ 🏢 Deepgram                                         │  ┃
┃  │ Score: 5.0/10 [Default (No AI)]  ← BADGE           │  ┃
┃  │ Domain: deepgram.com                                │  ┃
┃  │ Sample Employees: John Doe, Jane Smith...          │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ 🏢 AssemblyAI                                       │  ┃
┃  │ Score: 5.0/10 [Default (No AI)]                    │  ┃
┃  │ Domain: assemblyai.com                              │  ┃
┃  │ Sample Employees: Alice Johnson, Bob Lee...        │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ... 98 more companies ...                                 ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Results Display (AI Scoring Enabled)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Company Research Results                                  ┃
┃  ────────────────────────────────────────────────────      ┃
┃                                                             ┃
┃  Filters: [ All ] [ High Relevance (8+) ]  ← ENABLED      ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ 🏢 Deepgram                                         │  ┃
┃  │ Score: 9.2/10 [AI Scored]  ← BADGE                  │  ┃
┃  │ Domain: deepgram.com                                │  ┃
┃  │ 💡 Leading voice AI platform with real-time...     │  ┃
┃  │ Sample Employees: John Doe, Jane Smith...          │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ┌─────────────────────────────────────────────────────┐  ┃
┃  │ 🏢 AssemblyAI                                       │  ┃
┃  │ Score: 8.8/10 [AI Scored]                          │  ┃
┃  │ Domain: assemblyai.com                              │  ┃
┃  │ 💡 Speech-to-text API with strong ML team...       │  ┃
┃  │ Sample Employees: Alice Johnson, Bob Lee...        │  ┃
┃  └─────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┃  ... 98 more companies ...                                 ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Testing Plan

### Unit Tests

**Test File:** `backend/tests/test_optional_ai_scoring.py`

```python
import pytest
from company_research_service import CompanyResearchService

def test_ai_scoring_enabled():
    """Test full pipeline with AI scoring enabled."""
    service = CompanyResearchService()

    config = {'skip_ai_scoring': False}
    jd_context = {'domain': 'voice ai', 'role_title': 'ML Engineer'}

    result = await service.research_companies_for_jd(
        jd_text="ML Engineer for voice AI",
        jd_context=jd_context,
        config=config
    )

    # All companies should have AI scores
    assert all(c['scored_by'] == 'claude_haiku_with_websearch'
               for c in result['discovered_companies'])

    # Scores should vary (not all 5.0)
    scores = [c['relevance_score'] for c in result['discovered_companies']]
    assert len(set(scores)) > 1

    # Should have reasoning
    assert all(len(c['screening_reasoning']) > 50
               for c in result['discovered_companies'])

def test_ai_scoring_skipped():
    """Test pipeline with AI scoring skipped."""
    service = CompanyResearchService()

    config = {'skip_ai_scoring': True}
    jd_context = {'domain': 'voice ai', 'role_title': 'ML Engineer'}

    result = await service.research_companies_for_jd(
        jd_text="ML Engineer for voice AI",
        jd_context=jd_context,
        config=config
    )

    # All companies should have default scores
    assert all(c['relevance_score'] == 5.0
               for c in result['discovered_companies'])

    # All should be marked as no AI
    assert all(c['scored_by'] == 'default_no_ai'
               for c in result['discovered_companies'])

    # Should have skip message
    assert all('skipped' in c['screening_reasoning'].lower()
               for c in result['discovered_companies'])

def test_timing_difference():
    """Test that skipping AI scoring is significantly faster."""
    service = CompanyResearchService()

    # Measure with AI scoring
    start = time.time()
    result_with_ai = await service.research_companies_for_jd(
        jd_text="Test",
        jd_context={'domain': 'test'},
        config={'skip_ai_scoring': False}
    )
    time_with_ai = time.time() - start

    # Measure without AI scoring
    start = time.time()
    result_no_ai = await service.research_companies_for_jd(
        jd_text="Test",
        jd_context={'domain': 'test'},
        config={'skip_ai_scoring': True}
    )
    time_no_ai = time.time() - start

    # Should be at least 50% faster
    assert time_no_ai < time_with_ai * 0.5

def test_metadata_reflects_skip():
    """Test that response metadata correctly indicates skip status."""
    service = CompanyResearchService()

    result = await service.research_companies_for_jd(
        jd_text="Test",
        jd_context={'domain': 'test'},
        config={'skip_ai_scoring': True}
    )

    assert result['metadata']['ai_scoring_enabled'] == False
    assert result['metadata']['pipeline_phases']['ai_scoring'] == False
    assert result['metadata']['scored_by'] == 'default_no_ai'
```

### Integration Tests

**Test File:** `backend/tests/test_optional_scoring_integration.py`

```python
def test_api_endpoint_with_skip():
    """Test API endpoint with skip_ai_scoring parameter."""
    response = client.post('/research-companies', json={
        'jd_text': 'ML Engineer for voice AI',
        'skip_ai_scoring': True
    })

    assert response.status_code == 200
    data = response.get_json()

    # Check metadata
    assert data['metadata']['ai_scoring_enabled'] == False

    # Check all companies have default scores
    assert all(c['relevance_score'] == 5.0
               for c in data['discovered_companies'])

def test_api_endpoint_without_skip():
    """Test API endpoint with AI scoring (default behavior)."""
    response = client.post('/research-companies', json={
        'jd_text': 'ML Engineer for voice AI'
        # skip_ai_scoring not provided (defaults to False)
    })

    assert response.status_code == 200
    data = response.get_json()

    # Check metadata
    assert data['metadata']['ai_scoring_enabled'] == True

    # Check companies have AI scores
    assert all(c['scored_by'] == 'claude_haiku_with_websearch'
               for c in data['discovered_companies'])
```

### Frontend Tests

**Test File:** `frontend/src/__tests__/OptionalScoring.test.js`

```javascript
test('checkbox updates state', () => {
  render(<App />);

  const checkbox = screen.getByLabelText(/Skip AI scoring/i);

  // Initially unchecked
  expect(checkbox).not.toBeChecked();

  // Click checkbox
  fireEvent.click(checkbox);

  // Should be checked
  expect(checkbox).toBeChecked();
});

test('displays correct cost/time when checkbox checked', () => {
  render(<App />);

  const checkbox = screen.getByLabelText(/Skip AI scoring/i);

  // Initially shows full cost
  expect(screen.getByText(/~3 min/)).toBeInTheDocument();
  expect(screen.getByText(/\$185/)).toBeInTheDocument();

  // Click checkbox
  fireEvent.click(checkbox);

  // Should show reduced cost
  expect(screen.getByText(/~1 min/)).toBeInTheDocument();
  expect(screen.getByText(/\$35/)).toBeInTheDocument();
});

test('API call includes skip_ai_scoring parameter', async () => {
  const mockFetch = jest.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      discovered_companies: [],
      metadata: { ai_scoring_enabled: false }
    })
  }));

  global.fetch = mockFetch;

  render(<App />);

  // Check skip checkbox
  const checkbox = screen.getByLabelText(/Skip AI scoring/i);
  fireEvent.click(checkbox);

  // Start research
  const button = screen.getByText(/Start Company Research/);
  fireEvent.click(button);

  // Check API call
  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith(
      '/research-companies',
      expect.objectContaining({
        body: expect.stringContaining('"skip_ai_scoring":true')
      })
    );
  });
});

test('displays warning banner when AI scoring skipped', async () => {
  render(<App />);

  // Mock API response with skipped AI scoring
  mockApiResponse({
    discovered_companies: [{
      name: 'Test Company',
      relevance_score: 5.0,
      scored_by: 'default_no_ai'
    }],
    metadata: { ai_scoring_enabled: false }
  });

  // Trigger research with skip enabled
  // ...

  // Check for warning banner
  await waitFor(() => {
    expect(screen.getByText(/AI scoring was skipped/)).toBeInTheDocument();
  });
});

test('relevance filter disabled when all scores default', () => {
  render(<App />);

  // Mock companies with default scores
  setCompanies([
    { name: 'Company 1', relevance_score: 5.0, scored_by: 'default_no_ai' },
    { name: 'Company 2', relevance_score: 5.0, scored_by: 'default_no_ai' }
  ]);

  const relevanceFilter = screen.getByText(/High Relevance/);
  expect(relevanceFilter).toBeDisabled();
});
```

---

## Rollout Plan

### Phase 1: Development & Staging (Week 1)

**Goals:**
- Implement feature in staging environment
- Verify functionality with test searches
- Ensure no regressions

**Tasks:**
- [ ] Backend implementation (2-3 hours)
  - [ ] Add `skip_ai_scoring` parameter to endpoint
  - [ ] Add skip logic to service method
  - [ ] Update response metadata
- [ ] Frontend implementation (2-3 hours)
  - [ ] Add checkbox state and UI
  - [ ] Update API call
  - [ ] Add banner and badges
  - [ ] Add CSS styles
- [ ] Testing (3-4 hours)
  - [ ] Write unit tests
  - [ ] Write integration tests
  - [ ] Manual testing in staging
- [ ] Documentation (1 hour)
  - [ ] Update API documentation
  - [ ] Update user guide

**Success Criteria:**
- ✅ All tests pass
- ✅ Staging deployment successful
- ✅ Manual testing confirms 60-85s timing with skip
- ✅ Cost tracking confirms $35 vs $185

### Phase 2: Canary Rollout (Week 2)

**Goals:**
- Test with real production traffic (10%)
- Monitor for errors or issues
- Collect user feedback

**Tasks:**
- [ ] Deploy to production with feature flag (10% users)
- [ ] Monitor error rates and performance
- [ ] Track checkbox usage rate
- [ ] Collect user feedback (survey or interviews)

**Metrics to Monitor:**
- Error rate (should be unchanged)
- Average search time (should show bimodal distribution)
- Skip adoption rate (target: 30-40% of searches)
- User satisfaction (survey)

**Success Criteria:**
- ✅ No increase in error rate
- ✅ Timing matches expectations (60-85s vs 150-235s)
- ✅ Cost savings confirmed in API usage logs
- ✅ Positive user feedback

### Phase 3: Full Rollout (Week 3)

**Goals:**
- Enable for 100% of users
- Announce feature launch
- Monitor at scale

**Tasks:**
- [ ] Increase feature flag to 25% → 50% → 75% → 100%
- [ ] Send feature announcement email/notification
- [ ] Update help documentation
- [ ] Add analytics tracking for checkbox usage

**Success Criteria:**
- ✅ Feature available to all users
- ✅ Skip adoption rate 30-40%
- ✅ Overall cost savings 15-20% (30-40% adoption × 81% savings)
- ✅ No increase in support tickets

### Phase 4: Optimization (Week 4+)

**Goals:**
- Optimize user experience based on data
- Add related features
- Maximize value

**Tasks:**
- [ ] Analyze checkbox usage patterns
- [ ] Consider adding "preset" options (Fast/Balanced/Thorough)
- [ ] Add ability to re-score companies after fast search (future)
- [ ] Track long-term cost savings

**Future Enhancements:**
- [ ] **Re-score button:** Allow users to run AI scoring after fast search
- [ ] **Smart defaults:** Auto-suggest skip for familiar domains
- [ ] **Batch scoring:** Score only top 25 companies (compromise)
- [ ] **Progress bar:** Show AI scoring progress when enabled

---

## Success Metrics

### Primary Metrics

**1. Feature Adoption Rate**
- **Formula:** `(searches with skip / total searches) × 100%`
- **Target:** 30-40% adoption rate
- **Measurement:** Track `skip_ai_scoring` parameter in API logs

**2. Time Savings**
- **Formula:** `baseline_time - skip_time`
- **Target:** 64% reduction (150-235s → 60-85s)
- **Measurement:** Log search duration by skip status

**3. Cost Savings**
- **Formula:** `(skipped searches × $150) / total cost`
- **Target:** 15-20% overall cost reduction (with 30-40% adoption)
- **Measurement:** Track Anthropic API usage by search type

### Secondary Metrics

**4. User Satisfaction**
- **Formula:** Survey responses (1-5 scale)
- **Target:** 4.0+ average rating
- **Measurement:** In-app survey after search completion

**5. Error Rate**
- **Formula:** `(failed searches / total searches) × 100%`
- **Target:** No increase vs. baseline
- **Measurement:** Monitor API error logs

**6. Re-enable Rate**
- **Formula:** `(users who re-ran with AI / users who skipped) × 100%`
- **Target:** <10% (most users satisfied with skip)
- **Measurement:** Track repeat searches on same JD

### ROI Calculation

**Cost Savings Example:**
```
Assumptions:
- 100 domain searches per month
- 30% adoption rate for skip
- $150 saved per skipped search

Monthly Savings:
= 100 searches × 30% × $150
= 30 × $150
= $4,500/month

Annual Savings:
= $4,500 × 12
= $54,000/year
```

**Time Savings Example:**
```
Assumptions:
- 100 domain searches per month
- 30% adoption rate
- 90-120 seconds saved per skip

Monthly Time Savings:
= 100 × 30% × 105s (average)
= 3,150 seconds
= 52.5 minutes

Annual Time Savings:
= 52.5 × 12
= 630 minutes (~10.5 hours)
```

---

## Risk Analysis

### Potential Risks

**Risk 1: Low Adoption Rate**
- **Risk:** Users don't check the box (< 10% adoption)
- **Impact:** Limited cost savings, feature underutilized
- **Mitigation:**
  - Make checkbox prominent and benefits clear
  - Add cost/time savings directly in UI
  - Consider making skip the DEFAULT for power users

**Risk 2: Poor User Experience Without AI Scores**
- **Risk:** Users frustrated by lack of relevance filtering
- **Impact:** Complaints, support tickets, feature abandonment
- **Mitigation:**
  - Clear warning banner about trade-offs
  - Add manual sorting/filtering options
  - Consider hybrid approach (score top 25 only)

**Risk 3: Confusion About What's Skipped**
- **Risk:** Users don't understand what "AI scoring" means
- **Impact:** Wrong usage, unexpected results
- **Mitigation:**
  - Clear, non-technical language ("Fast mode")
  - Tooltip explaining what's skipped
  - Show example results in help docs

**Risk 4: Regression in Quality Perception**
- **Risk:** Users perceive fast results as "lower quality"
- **Impact:** Brand perception damage
- **Mitigation:**
  - Frame as "exploratory mode" not "cheap mode"
  - Emphasize user control and choice
  - Show employee samples to prove quality

---

## Future Enhancements

### Short-term (Next 3 months)

**1. Re-score Companies Button**
- Allow users to run AI scoring after fast search
- Score only selected companies (not all 100)
- Use case: Fast discovery, then deep dive on interesting companies

**2. Preset Options**
- Replace checkbox with radio buttons:
  - 🚀 **Fast:** Skip AI scoring (~1 min, $35)
  - ⚖️ **Balanced:** Score top 25 only (~2 min, $75)
  - 🎯 **Thorough:** Full AI scoring (~3 min, $185)

**3. Smart Defaults**
- Remember user preference per session
- Auto-suggest skip for repeat searches
- Detect familiar domains and recommend fast mode

### Medium-term (Next 6 months)

**4. Batch Scoring**
- Instead of all-or-nothing, score in batches of 25
- Progressive disclosure: See first 25, load more if needed
- Balance speed and quality

**5. Caching of AI Scores**
- Cache company relevance scores by JD context
- If similar JD searched before, reuse scores
- Could reduce scoring from 100 companies to ~20-30 new ones

**6. Progress Visualization**
- When AI scoring enabled, show live progress:
  - "Scoring company 15/100... (Deepgram: 9.2/10)"
- Helps users understand time investment

### Long-term (Next year)

**7. Hybrid Approach**
- Fast discovery (Phase 1) completes in 30-45s
- Show companies immediately with "Score these companies?" button
- User decides after seeing list

**8. Tiered Scoring**
- **Tier 1:** Quick Haiku scoring (no web search, 10-20s total)
- **Tier 2:** Full Haiku + web search (current, 90-150s)
- **Tier 3:** Sonnet deep research (300-500s)

**9. AI Scoring as Background Job**
- Return companies immediately (no scores)
- Run AI scoring in background
- Update UI as scores arrive (real-time)

---

## Appendix

### A. Code References

**Backend Files:**
- `backend/app.py` - Line 2991 (API endpoint)
- `backend/company_research_service.py` - Lines 165-183 (skip logic integration)
- `backend/company_research_service.py` - Lines 675-782 (screening method)

**Frontend Files:**
- `frontend/src/App.js` - Line 100 (state variable)
- `frontend/src/App.js` - Line 3556-3567 (checkbox UI)
- `frontend/src/App.js` - Line 3633-3644 (API call)
- `frontend/src/App.js` - Line 4055 (results banner)
- `frontend/src/App.css` - End of file (styles)

**Test Files (to be created):**
- `backend/tests/test_optional_ai_scoring.py`
- `backend/tests/test_optional_scoring_integration.py`
- `frontend/src/__tests__/OptionalScoring.test.js`

### B. Related Features

**Existing Features:**
- Progressive evaluation (evaluate more companies on demand)
- Company discovery cache (7-day TTL)
- Employee sampling (3-5 per company)

**Complementary Features:**
- Company ID cache (Feature Request #1) - Saves lookup credits
- Optional AI scoring (Feature Request #2) - Saves scoring credits
- **Combined savings:** Up to 90% cost reduction with both features

### C. Performance Benchmarks

**Current Pipeline (Full AI Scoring):**
```
Phase 1: Discovery           30-45s    $20
Phase 2: AI Scoring         90-150s   $150
Phase 3: Employee Sampling   30-40s    $15
Phase 4: Sort & Return        <1s      $0
────────────────────────────────────────
TOTAL:                     150-235s   $185
```

**With Skip Enabled:**
```
Phase 1: Discovery           30-45s    $20
Phase 2: AI Scoring         SKIPPED   SKIPPED
Phase 3: Employee Sampling   30-40s    $15
Phase 4: Sort & Return        <1s      $0
────────────────────────────────────────
TOTAL:                      60-85s     $35
Savings:                    90-150s   $150 (81%)
```

**Detailed Timing Breakdown (AI Scoring Phase):**
```
For 100 companies with AI scoring:
- API call per company: ~800-900ms
- Rate limit delay: 1500ms
- Total per company: ~2300-2400ms
- Total for 100: 230-240 seconds

With skip:
- Default score assignment: <1ms per company
- Total for 100: <100ms (negligible)
```

### D. Decision Framework

**When to Recommend Skip:**

✅ **SKIP if:**
- User is exploring a new domain (broad discovery)
- Budget is limited (cost-sensitive)
- Time is critical (need results ASAP)
- User is familiar with domain (can self-assess)
- Planning to manually review all companies anyway

❌ **DON'T SKIP if:**
- User needs AI-validated rankings for client reports
- Unfamiliar domain requiring expert assessment
- Results will be used for decision-making without review
- User wants AI reasoning to understand relevance
- Sorting by relevance score is critical to workflow

---

## Implementation Checklist

### Backend Implementation
- [ ] Add `skip_ai_scoring` parameter to `/research-companies` endpoint
- [ ] Add skip logic to `research_companies_for_jd()` method
- [ ] Assign default scores (5.0) when skipped
- [ ] Update response metadata with skip status
- [ ] Add logging for skip detection
- [ ] Write unit tests for skip logic
- [ ] Write integration tests for API endpoint

### Frontend Implementation
- [ ] Add `skipAiScoring` state variable
- [ ] Create checkbox UI with label
- [ ] Add conditional cost/time display
- [ ] Update API call to include parameter
- [ ] Add warning banner to results
- [ ] Add score badges (Default vs AI)
- [ ] Disable relevance filter when all scores 5.0
- [ ] Add CSS styles for new elements
- [ ] Write React component tests

### Documentation
- [ ] Update API documentation with new parameter
- [ ] Add feature explanation to user guide
- [ ] Update inline code comments
- [ ] Add troubleshooting section
- [ ] Create feature announcement draft

### Testing
- [ ] Manual testing in local environment
- [ ] Deploy to staging environment
- [ ] Run automated test suite
- [ ] Performance testing (verify timing)
- [ ] Cost tracking (verify API usage)

### Deployment
- [ ] Deploy to staging (100%)
- [ ] Deploy to production (10% canary)
- [ ] Deploy to production (25%)
- [ ] Deploy to production (50%)
- [ ] Deploy to production (100%)

### Monitoring
- [ ] Set up analytics for checkbox usage
- [ ] Set up error monitoring
- [ ] Set up cost tracking
- [ ] Create usage dashboard
- [ ] Set up alerts for anomalies

---

**Status:** Ready for implementation ✅
**Estimated Effort:** 1-2 days for core feature + testing
**Expected ROI:** $4,500/month savings (30% adoption rate)

**Questions?** See implementation code blocks above or contact engineering team.
