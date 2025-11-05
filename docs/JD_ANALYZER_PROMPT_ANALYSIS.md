# JD Analyzer Prompt Flow Analysis

**Purpose:** Document and review all prompts used to derive weighted requirements from job descriptions.

---

## Overview: Two-Stage Pipeline

The JD Analyzer uses a **two-stage AI pipeline** to convert raw job descriptions into weighted assessment criteria:

1. **Stage 1 (JD Parser):** Extract structured requirements from raw JD text
2. **Stage 2 (Weight Generator):** Convert requirements into weighted assessment criteria

Both stages use **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) for consistency and quality.

---

## Stage 1: JD Parser

**File:** `backend/jd_analyzer/jd_parser.py:62-110`

**Model:** Claude Sonnet 4.5
**Temperature:** 0.2 (deterministic, low creativity)
**Max Tokens:** 4000

### System Prompt

```
You are an expert at analyzing job descriptions and extracting structured requirements.

Your task is to parse the job description and extract:

1. **Must-Have Requirements** - Hard requirements that are explicitly stated as required
2. **Nice-to-Have Requirements** - Soft preferences listed as "nice to have", "preferred", "bonus"
3. **Technical Skills** - Specific technologies, frameworks, languages mentioned
4. **Domain Expertise** - Industry knowledge, domain-specific experience required
5. **Experience Level** - Years of experience or seniority level
6. **Location** - Geographic requirements or remote work policy
7. **Company Stage** - Startup, growth, enterprise, etc.
8. **Implicit Criteria** - Unstated requirements you can infer from context

Return a JSON object with this structure:

{
  "role_title": "exact title from JD",
  "seniority_level": "junior | mid | senior | staff | principal | director | vp | c-suite",
  "must_have": [
    "requirement 1",
    "requirement 2"
  ],
  "nice_to_have": [
    "preference 1",
    "preference 2"
  ],
  "technical_skills": [
    "skill 1",
    "skill 2"
  ],
  "domain_expertise": [
    "domain 1",
    "domain 2"
  ],
  "experience_years": {
    "minimum": 5,
    "preferred": 10
  },
  "location": "location string or 'Remote' or 'United States'",
  "company_stage": "startup | growth | enterprise",
  "implicit_criteria": {
    "leadership_required": true,
    "founder_experience_valued": true,
    "network_in_industry": "AI/ML",
    "company_building_experience": true
  }
}

Be specific and extract as much detail as possible.
```

### User Prompt

```
[RAW JOB DESCRIPTION TEXT]
```

### Stage 1 Output Example

```json
{
  "role_title": "Founder-in-Residence/CEO (Realtime Voice-Developer Tools)",
  "seniority_level": "c-suite",
  "must_have": [
    "0→1 Technical Product Leadership",
    "AI/ML Literacy (LLM fine-tuning, RAG, guardrails)",
    "GTM Excellence (developer-first products, bottoms-up adoption)",
    "Leadership Skills (attract world-class team, drive results)",
    "Stakeholder Management (Fortune 500 + OSS community)"
  ],
  "nice_to_have": [
    "Voice / Real-Time Media Savvy (WebRTC, STT/TTS, streaming ML inference)",
    "Scaled telephony/conversational-AI startup (Series A to exit)",
    "Deep network in AI voice ecosystem (OpenAI, Deepgram, AssemblyAI)",
    "OSS maintainer or contributor to WebRTC/voice repos",
    "Previous fundraising experience"
  ],
  "technical_skills": [
    "LLM fine-tuning",
    "RAG",
    "Guardrails",
    "WebRTC",
    "STT/TTS",
    "Streaming ML inference",
    "Sub-400ms latency optimization"
  ],
  "domain_expertise": [
    "Voice AI",
    "Real-time Communication",
    "Conversational AI",
    "Developer Tools",
    "AI Infrastructure"
  ],
  "experience_years": {
    "minimum": 5,
    "preferred": 10
  },
  "location": "United States, Remote",
  "company_stage": "startup",
  "implicit_criteria": {
    "leadership_required": true,
    "founder_experience_valued": true,
    "network_in_industry": "Voice AI / Real-time ML",
    "company_building_experience": true,
    "fundraising_ability": true
  }
}
```

---

## Stage 2: Weight Generator

**File:** `backend/jd_analyzer/weight_generator.py:60-109`

**Model:** Claude Sonnet 4.5
**Temperature:** 0.3 (slightly more creative for rubric design)
**Max Tokens:** 3000

### System Prompt

```
You are an expert at designing candidate assessment rubrics.

Given the parsed job description requirements, create {num_requirements} weighted assessment criteria.

Requirements:
1. Each criterion should be specific, measurable, and directly tied to job success
2. Weights must sum to 100%
3. Order criteria by importance (highest weight first)
4. Include clear scoring guidance (what makes a 10 vs a 5 vs a 1)
5. Focus on the most critical success factors, not every listed requirement

The remaining percentage will auto-calculate as "General Fit" to reach 100%.

Return JSON array:
[
  {
    "requirement": "Brief requirement name (4-6 words)",
    "weight": 35,
    "description": "Detailed description of what this requirement means and why it matters",
    "scoring_criteria": "How to score 1-10: 10 = [best case], 5 = [acceptable], 1 = [insufficient]"
  },
  ...
]

Ensure weights sum to at most 95% (leaving 5%+ for General Fit).
```

### User Prompt

```
Job Requirements to Convert to Weighted Criteria:

**Role:** Founder-in-Residence/CEO (Realtime Voice-Developer Tools)
**Seniority:** c-suite

**Must-Have Requirements:**
[
  "0→1 Technical Product Leadership",
  "AI/ML Literacy (LLM fine-tuning, RAG, guardrails)",
  "GTM Excellence (developer-first products, bottoms-up adoption)",
  "Leadership Skills (attract world-class team, drive results)",
  "Stakeholder Management (Fortune 500 + OSS community)"
]

**Nice-to-Have Requirements:**
[
  "Voice / Real-Time Media Savvy (WebRTC, STT/TTS, streaming ML inference)",
  "Scaled telephony/conversational-AI startup (Series A to exit)",
  "Deep network in AI voice ecosystem (OpenAI, Deepgram, AssemblyAI)",
  "OSS maintainer or contributor to WebRTC/voice repos",
  "Previous fundraising experience"
]

**Technical Skills:**
[
  "LLM fine-tuning",
  "RAG",
  "Guardrails",
  "WebRTC",
  "STT/TTS",
  "Streaming ML inference",
  "Sub-400ms latency optimization"
]

**Domain Expertise:**
[
  "Voice AI",
  "Real-time Communication",
  "Conversational AI",
  "Developer Tools",
  "AI Infrastructure"
]

**Experience Level:**
{
  "minimum": 5,
  "preferred": 10
}

**Implicit Criteria:**
{
  "leadership_required": true,
  "founder_experience_valued": true,
  "network_in_industry": "Voice AI / Real-time ML",
  "company_building_experience": true,
  "fundraising_ability": true
}

Generate 5 weighted assessment criteria that best predict success in this role.
```

### Stage 2 Output Example

```json
[
  {
    "requirement": "Voice AI / Real-time Systems Expertise",
    "weight": 35,
    "description": "Deep experience building voice AI, speech recognition, or real-time audio/video systems with sub-400ms latency requirements. Includes working knowledge of WebRTC, STT/TTS pipelines, and streaming ML inference.",
    "scoring_criteria": "10 = Built production voice AI systems at scale with proven <400ms latency; 5 = Worked with voice AI APIs or real-time systems; 1 = No voice/real-time experience"
  },
  {
    "requirement": "AI/ML Infrastructure & LLMs",
    "weight": 25,
    "description": "Strong technical background in ML infrastructure, LLM fine-tuning, RAG systems, and guardrails. Can discuss latency budgets, cost trade-offs, and agentic workflows with engineers.",
    "scoring_criteria": "10 = Architected ML systems serving millions with LLM fine-tuning; 5 = Deployed LLMs in production; 1 = Only academic ML experience"
  },
  {
    "requirement": "0→1 Product Leadership",
    "weight": 20,
    "description": "Proven track record taking products from concept to launch as founder, early employee, or within larger company. Can build bottoms-up adoption loops and close enterprise logos.",
    "scoring_criteria": "10 = Founded/co-founded successful companies or led 0→1 products; 5 = Early employee in startup; 1 = Joined mature products only"
  },
  {
    "requirement": "Developer Tools / Platform GTM",
    "weight": 10,
    "description": "Experience building and shipping developer-first products with community-led distribution. Understands SDK adoption, developer evangelism, and open-source dynamics.",
    "scoring_criteria": "10 = Scaled widely-adopted dev tools (100k+ users); 5 = Shipped developer-facing products; 1 = No dev tools experience"
  },
  {
    "requirement": "Fundraising & Network in Voice AI",
    "weight": 10,
    "description": "Previous fundraising experience (pre-seed to Series A) and deep network in AI voice ecosystem (OpenAI, Deepgram, AssemblyAI, LiveKit, etc.). Can attract investors and early customers.",
    "scoring_criteria": "10 = Raised Series A+ with strong voice AI network; 5 = Involved in fundraising or knows ecosystem; 1 = No fundraising or network"
  }
]
```

**Total Custom Weight:** 100%
**General Fit (auto-calculated):** 0%

---

## Quality Control: Weight Normalization

**File:** `backend/jd_analyzer/weight_generator.py:136-142`

If the AI generates weights that sum to >100%, the system automatically normalizes them to 95%:

```python
total_weight = sum(req.get('weight', 0) for req in weighted_reqs)
if total_weight > 100:
    # Normalize to 95% to leave room for General Fit
    scale_factor = 95.0 / total_weight
    for req in weighted_reqs:
        req['weight'] = round(req['weight'] * scale_factor)
```

**Example Normalization:**
- Input: [40%, 35%, 30%, 15%, 10%] = 130%
- Normalized: [29%, 25%, 22%, 11%, 7%] = 94%
- General Fit: 6%

---

## Prompt Analysis & Recommendations

### ✅ What Works Well

**1. Two-Stage Pipeline**
- Separates extraction from weighting (single responsibility principle)
- Allows caching of Stage 1 output for different weight configurations
- Easier to debug (can inspect intermediate output)

**2. Structured JSON Output**
- Forces consistent format
- Prevents hallucination (schema validation)
- Easy to parse and validate

**3. Temperature Settings**
- 0.2 for parsing (deterministic, factual)
- 0.3 for weighting (slightly more creative for rubric design)

**4. Explicit Constraints**
- "Weights must sum to 100%"
- "Order by importance"
- "Ensure weights sum to at most 95%"
- Prevents edge cases

**5. Rich Context for Stage 2**
- Passes ALL extracted data (must-have, nice-to-have, technical, domain, implicit)
- Allows AI to make informed prioritization decisions
- Considers implicit criteria (unstated but inferred)

### ⚠️ Potential Issues

**1. Weight Distribution Consistency**
- AI might generate same weights for different JDs (e.g., always 35%, 25%, 20%, 10%, 10%)
- **Mitigation:** Prompt says "order by importance" but could be more explicit

**2. Generic Requirement Names**
- Risk of vague criteria like "Technical Skills" instead of specific "Voice AI Expertise"
- **Mitigation:** Prompt says "4-6 words" and "specific, measurable"

**3. No Validation of Scoring Criteria Quality**
- AI-generated scoring guidance might be unclear or inconsistent
- **Mitigation:** Could add examples of good vs bad scoring criteria

**4. Implicit Criteria May Be Ignored**
- Stage 2 receives implicit criteria but might not weight them heavily
- **Example:** Voice AI listed as "nice to have" but actually critical (as discovered in reverse-engineering)

**5. No Feedback Loop**
- System can't learn from which requirements actually predict hiring success
- **Future Enhancement:** Track assessment outcomes to refine weighting

---

## Prompt Improvements (Optional)

### Enhancement 1: Add Weight Distribution Guidance

**Current:**
```
Weights must sum to 100%
Order criteria by importance (highest weight first)
```

**Improved:**
```
Weights must sum to 100%
Order criteria by importance (highest weight first)

Weight distribution guidelines:
- Top priority (critical blocker): 30-40%
- High priority (important differentiator): 20-30%
- Medium priority (valuable but not critical): 10-20%
- Low priority (nice to have): 5-10%

Avoid equal weights - prioritize ruthlessly.
```

### Enhancement 2: Add Scoring Criteria Examples

**Current:**
```
"scoring_criteria": "How to score 1-10: 10 = [best case], 5 = [acceptable], 1 = [insufficient]"
```

**Improved:**
```
"scoring_criteria": "How to score 1-10 with specific examples:
  10 = [best case with measurable outcome]
  7-9 = [strong but not exceptional]
  5-6 = [meets minimum requirements]
  3-4 = [below expectations but salvageable]
  1-2 = [clearly insufficient]

Example: '10 = Founded voice AI startup with 1M+ users; 7 = Senior engineer at Deepgram; 5 = Built voice features; 1 = No voice experience'"
```

### Enhancement 3: Elevate Implicit Criteria

**Current:**
```
**Implicit Criteria:**
{
  "leadership_required": true,
  "founder_experience_valued": true,
  ...
}
```

**Improved:**
```
**Implicit Criteria (IMPORTANT - often more predictive than stated requirements):**
{
  "leadership_required": true,
  "founder_experience_valued": true,
  ...
}

Note: "Nice to have" items in JDs often signal hard requirements that recruiters don't want to state explicitly. Consider weighting implicit criteria heavily.
```

### Enhancement 4: Add Domain-Specific Context

**Current:**
```
Generate 5 weighted assessment criteria that best predict success in this role.
```

**Improved:**
```
Generate 5 weighted assessment criteria that best predict success in this role.

Context: These criteria will be used to score candidates on a 1-10 scale. The weighted average determines hiring decisions. Prioritize criteria that:
1. Differentiate top 10% candidates from top 30%
2. Are observable from resume/LinkedIn profile
3. Predict actual job performance (not just "looks good on paper")

Consider: What makes someone GREAT at this role vs merely qualified?
```

---

## Testing Strategy

### Test Case 1: Generic Software Engineer JD

**Input:** Standard SWE JD with Python, React, 5+ years

**Expected Output:**
- Technical Skills (35-40%)
- Problem Solving (20-25%)
- Experience Level (15-20%)
- Communication (10-15%)
- Domain Knowledge (5-10%)

### Test Case 2: Founder/CEO JD (Voice AI)

**Input:** AI Fund Voice AI CEO JD (from reverse-engineering case study)

**Expected Output:**
- Voice AI Domain Expertise (30-40%)
- Leadership/Founder Experience (20-30%)
- AI/ML Infrastructure (15-25%)
- GTM/Product Skills (10-15%)
- Fundraising/Network (5-10%)

### Test Case 3: Entry-Level Role

**Input:** Junior Product Manager, 0-2 years experience

**Expected Output:**
- Analytical Skills (25-35%)
- Communication (20-30%)
- Learning Agility (20-25%)
- Technical Aptitude (10-15%)
- Team Collaboration (10-15%)

### Test Case 4: Highly Specialized Role

**Input:** Staff ML Engineer (NLP), 8+ years, PhD preferred

**Expected Output:**
- NLP Expertise (40-50%)
- ML Infrastructure (25-30%)
- Research Publication Record (10-15%)
- Mentorship/Leadership (5-10%)
- Cross-functional Collaboration (5-10%)

---

## Validation Metrics

**How to measure if weights are "good":**

1. **Coverage:** Do the 5 requirements cover all must-have items from JD? (Target: 90%+)
2. **Differentiation:** Do weights vary meaningfully? (Avoid 20%, 20%, 20%, 20%, 20%)
3. **Relevance:** Do requirements match role type? (E.g., leadership weighted high for CEO roles)
4. **Clarity:** Are scoring criteria actionable? (Can recruiter assign scores 1-10?)
5. **User Acceptance:** Do recruiters edit <20% of auto-generated requirements?

---

## API Endpoint: `/api/jd/full-analysis`

**Current Implementation (Frontend):**

```javascript
const response = await fetch('http://localhost:5001/api/jd/full-analysis', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jd_text: jdText,
    num_requirements: 5
  })
});

const data = await response.json();
// data.success = true
// data.requirements = Stage 1 output
// data.weighted_requirements = Stage 2 output
// data.keywords = Extracted keywords
// data.general_fit_weight = 100 - sum(weights)
```

**Response Structure:**

```json
{
  "success": true,
  "requirements": {
    "role_title": "...",
    "seniority_level": "...",
    "must_have": [...],
    "nice_to_have": [...],
    ...
  },
  "weighted_requirements": [
    {
      "requirement": "Voice AI Expertise",
      "weight": 35,
      "description": "...",
      "scoring_criteria": "..."
    },
    ...
  ],
  "keywords": ["Voice AI", "LLM", "WebRTC", ...],
  "general_fit_weight": 0
}
```

---

## Conclusion

**The current prompt pipeline effectively:**
- ✅ Extracts structured requirements from unstructured JD text
- ✅ Generates weighted assessment criteria with scoring rubrics
- ✅ Handles edge cases (weight normalization, JSON parsing)
- ✅ Uses appropriate AI models and temperature settings

**Areas for improvement:**
- ⚠️ Weight distribution could be more varied/realistic
- ⚠️ Implicit criteria might not be weighted heavily enough
- ⚠️ No feedback loop to learn from hiring outcomes
- ⚠️ Scoring criteria examples could be more specific

**Recommendation:**
The current implementation is production-ready. Consider implementing the **Enhanced Prompts** (Enhancements 1-4 above) in a future iteration after gathering user feedback on weight quality and relevance.

**Next Step:**
Test with diverse JDs (technical, non-technical, entry-level, executive) to validate weight distribution patterns and identify systematic biases.
