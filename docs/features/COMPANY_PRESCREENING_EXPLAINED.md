# 🏢 Company Pre-Screening: Detailed Explanation

## 📋 What You Asked About

You noticed that **"initial evaluation of the top 25"** companies doesn't happen in your current pipeline. Let me explain what this is, why it's missing, and how to add it.

---

## 🎯 Two Different Workflows

Your codebase supports TWO different approaches to company research:

### Workflow A: **Domain Search** (What You're Using Now)
```
1. Discover 40-50 companies (Stage 1)
   ↓
2. Search employees at ALL companies immediately (Stage 2)
   ↓
3. User reviews 85-1,500 candidate profiles
   ↓
4. Optional: AI evaluates candidates (Stage 4)
```

**Key Point:** Companies are **NOT** evaluated. All discovered companies go straight to employee search.

---

### Workflow B: **Company Research** (The One with Top 25 Evaluation)
```
1. Discover 40-50 companies (Stage 1)
   ↓
2. **AI screens all 40-50 companies** (GPT-5-mini batch screening)
   ↓
3. **AI deep-evaluates top 25 companies** (Claude Haiku 4.5 or GPT-5)
   ↓
4. User selects best companies from top 25
   ↓
5. Search employees at SELECTED companies only (Stage 2)
```

**Key Point:** Companies are **evaluated BEFORE** employee search. Only the best companies get employee searches.

---

## 🔍 Current State Analysis

### What Your Code Does Now:

Looking at `/api/jd/domain-company-preview-search`:

```python
# Stage 1: Discover companies
companies = await stage1_discover_companies(jd_requirements, session_logger)
# Result: 40-50 companies

# NO EVALUATION STEP HERE ❌

# Stage 2: Search employees immediately
stage2_results = await stage2_preview_search(
    companies,  # ALL 40-50 companies used
    jd_requirements,
    endpoint,
    max_previews,
    session_logger
)
# Result: 85-1,500 candidate profiles
```

**What's Missing:**
- No company screening between Stage 1 and Stage 2
- No relevance scoring for companies
- No filtering of low-quality companies
- Employee search happens at ALL discovered companies

---

## 📊 Why Company Pre-Screening Matters

### Problem Without Pre-Screening:

1. **Wasted API Credits**
   - Searching employees at 40-50 companies
   - Many companies may be irrelevant
   - Example: If only 10 companies are truly relevant, you're wasting 75% of searches

2. **Noisy Results**
   - Candidate pool includes profiles from less relevant companies
   - Harder to find best candidates
   - Example: Finding ML engineers at "generic tech companies" vs "voice AI specialists"

3. **No Transparency**
   - User doesn't know WHY these companies were selected
   - Can't verify if discovery found the right companies
   - Hard to trust the results

### Benefits With Pre-Screening:

1. **Targeted Employee Search**
   - Only search top 10-25 most relevant companies
   - Save 50-75% of API credits
   - Higher quality candidate pool

2. **Company Insights**
   - Know exactly why each company is relevant
   - See company scores/rankings
   - Understand domain fit, funding stage, growth signals

3. **User Control**
   - Review company list before employee search
   - Manually adjust selections
   - Add companies that were missed
   - Remove false positives

---

## 🛠️ How Company Pre-Screening Works

### Step 1: Batch Screening (Fast & Cheap)

**Model:** GPT-5-mini (fast, $0.15/1M tokens)
**Batch Size:** 20 companies at a time
**Speed:** ~5 seconds per batch
**Purpose:** Quick relevance check

**What It Does:**
```python
# Input: 40-50 discovered companies
# Output: Each company gets:
{
  "company_name": "Deepgram",
  "initial_score": 8.5,  # 0-10 scale
  "relevance": "high",  # high/medium/low
  "reasoning": "Voice AI specialist, Series B funded, 150+ employees"
}
```

**Prompt Example:**
```
You are a recruiting research analyst. Evaluate these 20 companies for relevance to this job:

**Target Domain:** Voice AI
**Role:** Senior ML Engineer
**Key Requirements:** Speech recognition, real-time processing, Python

**Companies to Evaluate:**
1. Deepgram - Voice AI platform, speech recognition
2. Generic Software Inc - Enterprise software solutions
3. Krisp - AI-powered noise cancellation
...

For each company, provide:
- initial_score (0-10)
- relevance (high/medium/low)
- brief reasoning (one sentence)
```

**Result:**
- 40-50 companies → 40-50 scored companies
- Sorted by initial_score
- Takes ~10-15 seconds for 50 companies

---

### Step 2: Deep Evaluation (Top 25 Only)

**Model:** Claude Haiku 4.5 or GPT-5 (more capable)
**Batch Size:** 1 company at a time
**Speed:** ~2-3 seconds per company
**Purpose:** Detailed analysis for top candidates

**What It Does:**
```python
# Input: Top 25 companies from batch screening
# Output: Each company gets detailed evaluation:
{
  "company_name": "Deepgram",
  "overall_fit_score": 9.2,  # 0-10 scale
  "domain_fit": 9.5,
  "company_stage_fit": 8.0,
  "growth_signals": 9.0,
  "strengths": [
    "Leading voice AI platform",
    "Strong ML/NLP team",
    "Series B funded ($72M)",
    "Fast growth (3x in 2 years)"
  ],
  "concerns": [
    "Competitive hiring market",
    "Heavy focus on enterprise (less startup vibe)"
  ],
  "recommendation": "high_priority",  # high_priority/medium_priority/low_priority
  "estimated_employees": 150
}
```

**Prompt Example:**
```
You are a senior recruiting analyst. Perform deep evaluation of this company for a job opening.

**Company:**
Name: Deepgram
Website: https://deepgram.com
Description: End-to-end deep learning platform for speech recognition
LinkedIn: https://linkedin.com/company/deepgram
Employees: ~150

**Target Job Context:**
Role: Senior ML Engineer
Domain: Voice AI
Seniority: Senior
Must-Have: Speech recognition, real-time systems, Python, PyTorch
Nice-to-Have: Voice AI experience, startup background

**Evaluate:**
1. Domain Fit (0-10): How well does this company match the target domain?
2. Company Stage Fit (0-10): Is this the right stage (Series B preferred)?
3. Growth Signals (0-10): Is the company growing rapidly?
4. Overall Fit (0-10): Overall recommendation score

Provide detailed reasoning for each score.
```

**Result:**
- Top 25 companies → 25 deeply evaluated companies
- Rich metadata for each
- Takes ~50-75 seconds for 25 companies

---

### Step 3: User Selection

**UI Shows:**
```
┌─────────────────────────────────────────────┐
│ 🏢 Discovered 47 Companies                  │
│                                             │
│ TOP 25 EVALUATED (click to select):        │
│                                             │
│ ✅ 1. Deepgram              Score: 9.2/10  │
│    Voice AI platform • Series B • $72M     │
│    💡 "Leading voice AI specialist"        │
│    [View Details] [Select]                 │
│                                             │
│ ✅ 2. Krisp                  Score: 8.8/10  │
│    AI noise cancellation • Series A • $14M │
│    💡 "Strong audio ML team"               │
│    [View Details] [Select]                 │
│                                             │
│ ☐  3. AssemblyAI             Score: 8.5/10  │
│    Speech-to-text API • Series A • $28M    │
│    💡 "Fast-growing API platform"          │
│    [View Details] [Select]                 │
│                                             │
│ [Show Remaining 22 Companies ▼]            │
│                                             │
│ REMAINING 22 COMPANIES (not evaluated):    │
│ • Generic Tech Corp                        │
│ • Software Solutions Inc                   │
│ ... (click "Evaluate More" to score)       │
│                                             │
│ [Search Employees at 2 Selected Companies] │
└─────────────────────────────────────────────┘
```

**User Can:**
- ✅ Select/deselect companies for employee search
- 🔍 View detailed evaluation for each top 25 company
- ➕ Manually add companies that weren't in top 25
- 🔄 Click "Evaluate More" to score companies 26-50

---

## 💰 Cost & Time Analysis

### Without Pre-Screening (Current):
```
Stage 1: Discover 50 companies
  Tavily API: $0.10 (5 searches × $0.02)
  Time: ~5 seconds

Stage 2: Search employees at ALL 50 companies
  CoreSignal API: 50 searches × 100 previews = 5,000 preview fetches
  Time: ~60 seconds
  Cost: $0 (previews are free)

Stage 3: Collect full profiles (user selects 100)
  CoreSignal API: 100 profile collections × 1 credit = 100 credits
  Time: ~30 seconds
  Cost: $70 (assuming ~$0.70/credit)

TOTAL TIME: ~95 seconds
TOTAL COST: ~$70.10
RESULT: 100 profiles from potentially irrelevant companies
```

### With Pre-Screening:
```
Stage 1: Discover 50 companies
  Tavily API: $0.10
  Time: ~5 seconds

Stage 1.5: Company Screening (NEW)
  GPT-5-mini batch screening (50 companies):
    Cost: $0.05 (cheap!)
    Time: ~15 seconds

  Claude Haiku 4.5 deep eval (top 25):
    Cost: $0.50 (still cheap!)
    Time: ~50 seconds

  Sub-total: $0.55, ~65 seconds

Stage 2: Search employees at TOP 10 companies (user-selected)
  CoreSignal API: 10 searches × 100 previews = 1,000 preview fetches
  Time: ~15 seconds
  Cost: $0 (previews free)

Stage 3: Collect full profiles (user selects 100)
  CoreSignal API: 100 collections
  Time: ~30 seconds
  Cost: $70

TOTAL TIME: ~115 seconds (20 seconds more)
TOTAL COST: ~$70.65 (+$0.55 for screening)
RESULT: 100 profiles from HIGHLY RELEVANT companies
```

**Net Impact:**
- ⏱️ Time: +20 seconds (acceptable for better quality)
- 💰 Cost: +$0.55 (negligible - <1% increase)
- 🎯 Quality: **MUCH BETTER** (targeted companies only)
- 🔍 Transparency: User sees WHY companies were selected

---

## 🚀 How to Add Company Pre-Screening

### Option 1: Simple Version (10 lines of code)

Add basic screening between Stage 1 and Stage 2:

```python
# After Stage 1
companies = await stage1_discover_companies(jd_requirements, session_logger)
# Result: 50 companies

# NEW: Quick AI screening
from company_research_service import screen_companies_batch
screened = screen_companies_batch(companies, jd_requirements)
# Result: 50 companies with scores

# Sort and take top 10-25
top_companies = sorted(screened, key=lambda c: c['initial_score'], reverse=True)[:10]

# Proceed to Stage 2 with top companies only
stage2_results = await stage2_preview_search(
    top_companies,  # Only top 10 instead of all 50
    jd_requirements,
    endpoint,
    max_previews,
    session_logger
)
```

**Pro:** Simple, fast to implement
**Con:** User has no control, screening happens silently

---

### Option 2: Full Version with UI (Recommended)

Create a new 3-stage flow:

**Backend: New Endpoint**
```python
@domain_search_bp.route('/api/jd/domain-company-discover-and-screen', methods=['POST'])
def domain_company_discover_and_screen():
    """
    Stage 1 + 1.5: Discover companies and screen them.

    Returns companies with scores, does NOT search employees yet.
    """
    # Stage 1: Discover
    companies = await stage1_discover_companies(jd_requirements, session_logger)

    # Stage 1.5: Batch screening (all 50)
    screened = await screen_companies_batch(companies, jd_requirements)

    # Stage 1.5: Deep eval (top 25 only)
    top_25 = sorted(screened, key=lambda c: c['initial_score'], reverse=True)[:25]
    evaluated = await evaluate_companies_detailed(top_25, jd_requirements)

    # Return to user for selection
    return jsonify({
        "session_id": session_id,
        "discovered_companies": companies,  # All 50
        "screened_companies": screened,      # All 50 with scores
        "evaluated_companies": evaluated,    # Top 25 with detailed eval
        "recommended_companies": evaluated[:10]  # Top 10 for employee search
    })
```

**Frontend: Company Selection UI**
```javascript
// Step 1: Discover and screen companies
const response = await fetch('/api/jd/domain-company-discover-and-screen', {
  method: 'POST',
  body: JSON.stringify({jd_requirements})
});
const {evaluated_companies, recommended_companies} = await response.json();

// Step 2: User selects companies
<CompanySelectionUI
  companies={evaluated_companies}
  preselected={recommended_companies}
  onSelect={(selected) => {
    // User chose which companies to search
    searchEmployees(selected);
  }}
/>

// Step 3: Search employees at selected companies only
async function searchEmployees(selectedCompanies) {
  const response = await fetch('/api/jd/domain-company-preview-search', {
    method: 'POST',
    body: JSON.stringify({
      mentioned_companies: selectedCompanies,  // Only selected companies
      jd_requirements
    })
  });
  // ... show candidate results
}
```

**Pro:** Full transparency, user control, best quality
**Con:** More work (needs UI component, extra endpoint)

---

## 📊 Comparison: With vs Without Pre-Screening

| Aspect | Without Pre-Screening | With Pre-Screening |
|--------|----------------------|-------------------|
| **Companies Discovered** | 50 | 50 |
| **Companies Evaluated** | 0 (none) | 50 (batch) + 25 (deep) |
| **Companies Searched** | All 50 | Top 10 (user-selected) |
| **Candidate Quality** | Mixed (some irrelevant) | High (from best companies) |
| **User Transparency** | Low (black box) | High (see all scores) |
| **User Control** | None | Full (select companies) |
| **API Credit Usage** | Higher (50 searches) | Lower (10 searches) |
| **Time Cost** | ~95 seconds | ~115 seconds (+20s) |
| **Dollar Cost** | ~$70 | ~$70.55 (+$0.55) |

---

## 🎯 Recommendation

### For Your Use Case:

**Should you add company pre-screening?**

**YES if:**
- ✅ You want higher quality candidates (from best companies only)
- ✅ You want transparency (see WHY companies were selected)
- ✅ You want user control (manually adjust company selection)
- ✅ You're doing multiple searches (savings add up)

**NO if:**
- ❌ You trust the discovery to find perfect companies (risky assumption)
- ❌ You want the absolute fastest results (no 20-second delay)
- ❌ You want zero changes to current flow (it's working well enough)

### My Recommendation: **ADD IT**

**Why:**
1. **Quality > Speed**: 20 extra seconds is worth it for better candidates
2. **Transparency**: You'll know exactly why companies were selected
3. **Cost**: Only $0.55 extra per search (negligible)
4. **Flexibility**: Users can override AI selections if needed

### Implementation Priority:

**Phase 1 (Quick Win):**
- Add simple batch screening (Option 1)
- Auto-select top 10 companies
- No UI changes needed
- **Time: 30 minutes**

**Phase 2 (Full Experience):**
- Add company selection UI (Option 2)
- Show company scores and reasoning
- Let users manually adjust
- **Time: 2-3 hours**

---

## 💡 Next Steps

1. **Read this doc** to understand the trade-offs
2. **Decide:** Do you want company pre-screening?
3. **If yes:** Which version?
   - Simple (auto-select top 10)
   - Full (user selects from scored list)
4. **I'll implement** whichever you choose

**Question for you:**
Would you like me to implement Phase 1 (simple auto-select) now? It's 30 minutes of work and gives immediate quality improvement.
