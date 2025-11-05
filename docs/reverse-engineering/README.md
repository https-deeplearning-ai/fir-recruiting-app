# Reverse-Engineering Case Study: Voice AI Role

This folder contains the complete analysis of reverse-engineering recruiter search criteria from a real job description and candidate shortlist.

## Overview

**Objective:** Discover what recruiters *actually* value (implicit criteria) versus what they *state* in job descriptions (explicit requirements).

**Method:** Analyze 68-candidate shortlist for a "Founder-in-Residence/CEO (Voice AI)" role at AI Fund to uncover hidden hiring patterns.

**Key Finding:** 5 major gaps between JD and reality reveal the true hiring criteria.

---

## Files in This Folder

### 1. [REVERSE_ENGINEERING_REPORT.md](REVERSE_ENGINEERING_REPORT.md)
**15-page comprehensive report** (11,500 words) documenting:
- Pattern analysis of 68 candidates
- JD vs reality comparison
- 3-tier CoreSignal search query generation
- Post-search ranking model
- Key insights for recruiters

**Key Sections:**
- Executive Summary
- Dataset Overview
- Pattern Analysis (location, seniority, company types)
- JD vs Reality (5 hidden criteria)
- CoreSignal Search Query Design (Tier 1, 2, 3)
- Post-Search Ranking Model (scoring weights)
- Validation Strategy
- Recommendations

### 2. [vocal_bridge_fir_job_description.md](vocal_bridge_fir_job_description.md)
**Formatted job description** from AI Fund for the Voice AI role:
- Role: Founder-in-Residence/CEO (Realtime Voice-Developer Tools)
- Must-have: 0→1 product leadership, AI/ML literacy, GTM excellence
- Nice-to-have: Voice/real-time media savvy, AI voice ecosystem network
- Location (stated): "United States, Remote"

### 3. [candidate_shortlist.csv](candidate_shortlist.csv)
**68 candidates** hand-picked by recruiters:
- Columns: First Name, Last Name, Location, Current Title, Current Company, Profile URL, email, date of email, date of inmail, interview date
- Interview conversion: 14/68 (20.6%)
- Outreach period: August 21 - September 25, 2024

### 4. [reverse_engineer_results.json](reverse_engineer_results.json)
**Raw analysis data** in structured JSON format:
- Pattern analysis (locations, seniority, companies, keywords)
- 3-tier search queries (Tier 1: strict, Tier 2: relaxed, Tier 3: optimized)
- Expected coverage for each tier

### 5. [reverse_engineer_search.py](reverse_engineer_search.py)
**Python script** for automated reverse-engineering:
- Input: JD text + CSV of candidate URLs
- Output: Optimized CoreSignal search query + coverage analysis
- Reusable for future JD + shortlist pairs

---

## Key Findings Summary

### 5 Hidden Criteria Discovered

**1. Bay Area Bias (69%)**
- JD States: "United States, Remote"
- Reality: 69% in San Francisco Bay Area
- Insight: Strong implicit geographic preference

**2. Domain > Seniority**
- JD Lists: "Nice to have - Voice AI experience"
- Reality: 19% from Voice AI companies (Otter.ai, Deepgram, ElevenLabs)
- Insight: Voice AI is actually a HARD requirement

**3. Company Pedigree Matters**
- JD States: (No explicit company requirements)
- Reality: 37% from Big Tech (15%) + AI Infrastructure (22%)
- Insight: Unstated company quality bar

**4. Seniority Flexible**
- JD Emphasizes: "Founder/CEO"
- Reality: 50% C-Suite, 21% Senior IC
- Insight: Open to Staff Engineers and Research Scientists

**5. Network Effects**
- Top companies: Otter.ai (6), Meta (5), Sierra (5)
- Insight: Referral-driven sourcing from talent clusters

---

## Pattern Analysis Highlights

### Location Distribution
| Location | Count | % |
|----------|-------|---|
| San Francisco Bay Area | 47 | 69.1% |
| New York | 6 | 8.8% |
| Greater Seattle Area | 5 | 7.4% |
| Other | 10 | 14.7% |

### Seniority Distribution
| Level | Count | % |
|-------|-------|---|
| C-Suite (CEO, CTO, Founder) | 34 | 50.0% |
| Senior IC (Staff, Principal) | 14 | 20.6% |
| Mid-Level | 12 | 17.6% |
| VP/Director | 3 | 4.4% |

### Company Types
| Type | Count | % | Examples |
|------|-------|---|----------|
| Voice AI Specialist | 13 | 19.1% | Otter.ai, Deepgram, PlayAI |
| AI Infrastructure | 15 | 22.1% | Together AI, Anyscale, Pinecone |
| Big Tech / FAANG | 10 | 14.7% | Meta, Google, Amazon |
| Conversational AI | 8 | 11.8% | Sierra, LangChain |

### Title Keywords
- AI: 29.4%
- ML: 5.9%
- LLM: 2.9%
- Voice: 1.5% (but 19% work at Voice AI companies!)

---

## CoreSignal Search Queries

### Tier 1: Strict JD Interpretation (30-40% coverage)
```json
{
  "must_have_location": "United States",
  "must_have_role_titles": ["Founder", "CEO", "CTO", "Chief"],
  "must_have_skills_in_headline": ["AI", "Voice", "ML"],
  "must_have_experience_years": 10
}
```

### Tier 2: Shortlist-Informed (60-80% coverage)
```json
{
  "must_have_location": "San Francisco Bay Area",
  "must_have_role_titles": ["AI", "ML", "Voice", "CTO", "Founder", "Staff", "Senior"],
  "must_have_skills_in_headline": ["AI", "Voice", "Speech", "LLM"],
  "must_have_experience_years": 5
}
```

### Tier 3: Optimized Multi-Location (80-90% coverage)
```json
{
  "must_have_locations": ["Bay Area", "Seattle", "NYC", "Boston", "Remote"],
  "must_have_role_titles": ["Voice", "Speech", "AI", "ML", "CTO", "Founder", "Staff"],
  "nice_to_have_companies": ["Meta", "Anthropic", "Otter.ai", "Deepgram", ...],
  "must_have_experience_years": 5
}
```

---

## Post-Search Ranking Model

**Scoring Weights (0-100 points):**
- Voice AI Experience: 30 points
- Company Pedigree: 25 points
- Leadership Level: 20 points
- AI/ML Depth: 15 points
- Location: 10 points

**Filtering Strategy:**
- Score 75-100: Shortlist quality (top 50)
- Score 60-75: Backup pool (next 100)
- Below 60: Likely false positives

---

## Validation Strategy

### Phase 1: Test Queries Against CoreSignal
1. Run Tier 1, 2, 3 queries
2. Measure coverage (% of 68 candidates found)
3. Identify missed candidates

### Phase 2: Analyze Gaps
4. Fetch full profiles for missed candidates
5. Understand why they weren't matched
6. Iterate on query parameters

### Phase 3: Post-Search Filtering
7. Apply scoring model to all results
8. Validate shortlist candidates score 75+
9. Use top non-shortlist candidates as recommendations

---

## Key Lessons for Recruiters

**1. Search by Company, Not Title**
- Only 1.5% have "Voice" in title, but 19% work at Voice AI companies
- Company is a stronger signal than job title keywords

**2. Geography Matters (Even When Unstated)**
- Even "Remote" roles show strong location clustering
- Consider: Is this intentional or unconscious bias?

**3. Seniority is Negotiable, Domain Isn't**
- Flexible on C-Suite vs Senior IC (50% vs 21%)
- But ALL candidates have AI/ML + Voice AI background

**4. Network Effects Drive Sourcing**
- 6 from Otter.ai, 5 from Meta, 5 from Sierra
- Best candidates know each other (referral-driven)

**5. "Nice to Have" Often Means "Required"**
- Voice AI listed as "nice to have" but appears critical
- Watch for this JD vs reality gap

---

## Usage: How to Run This Analysis

### 1. With Your Own Data

```bash
cd backend
python3 reverse_engineer_search.py \
  --csv "your_candidates.csv" \
  --jd "your_job_description.md"
```

### 2. Using the JD Analyzer Module

```python
from jd_analyzer import JDParser, ShortlistAnalyzer

# Parse JD
parser = JDParser()
requirements = parser.parse(jd_text)

# Analyze shortlist
analyzer = ShortlistAnalyzer("candidates.csv")
analyzer.load_candidates()
gaps = analyzer.compare_to_jd(requirements)
```

---

## Future Enhancements

- [ ] Machine learning model: JD + shortlist → predicted search query
- [ ] Auto-generate CoreSignal queries from JD text
- [ ] A/B test different query variations
- [ ] Track coverage + false positive rates over time
- [ ] Talent network mapping (graph analysis of connections)

---

## Related Files

- [../jd_analyzer/](../../backend/jd_analyzer/) - Modular JD analysis system
- [CLAUDE.md](../../CLAUDE.md) - Project architecture
- [SUPABASE_SCHEMA.sql](../SUPABASE_SCHEMA.sql) - Database schema

---

## Questions?

This case study demonstrates how to discover implicit hiring criteria by reverse-engineering recruiter decisions. The methodology is generalizable to any role where you have:
1. A job description
2. A shortlist of candidates selected by recruiters

The gap between what's stated and what's selected reveals the true requirements.
