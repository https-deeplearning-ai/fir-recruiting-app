"""
Multi-LLM Query Generator

Compares query generation across different LLMs (Claude, GPT-4, Gemini) to find
the best CoreSignal search query for a given JD.
"""

import os
import time
from typing import Dict, List, Any, Optional
import anthropic
from anthropic import RateLimitError
import openai
import json
from jd_analyzer.query.llm_configs import get_config
from jd_analyzer.utils.debug_logger import debug_log

# Optional Gemini import (not required for basic JD parsing)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

class MultiLLMQueryGenerator:
    """
    Generates CoreSignal queries using multiple LLMs and compares results.
    """

    def __init__(self):
        """Initialize LLM clients and load configs."""
        # Store initialization errors for better debugging
        self.anthropic_init_error = None
        self.openai_init_error = None

        try:
            # Anthropic client works fine on Render
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        except Exception as e:
            self.anthropic_init_error = str(e)
            print(f"Warning: Failed to initialize Anthropic client: {e}")
            import traceback
            traceback.print_exc()
            self.anthropic_client = None

        try:
            # Initialize OpenAI client - use custom httpx client to bypass proxy issues
            # Render's proxy environment variables cause OpenAI SDK to fail
            import httpx

            # Create httpx client with explicit proxy settings (none/disabled)
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
                proxies={}  # Empty dict explicitly disables proxies
            )

            self.openai_client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                http_client=http_client
            )
            print("✓ OpenAI client initialized successfully with custom httpx client")

        except Exception as e:
            self.openai_init_error = str(e)
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            import traceback
            traceback.print_exc()
            self.openai_client = None

        # Gemini uses per-request client initialization (new google-genai SDK)
        # No global configuration needed

        # Load model configurations
        self.claude_config = get_config("claude")
        self.openai_config = get_config("openai")
        self.google_config = get_config("google")

        # Query generation prompt template
        self.system_prompt = """You are an expert at translating job requirements into CoreSignal Elasticsearch DSL queries.

REFERENCE: See backend/jd_analyzer/CORESIGNAL_FIELD_REFERENCE.md for complete field documentation.

## CHAIN-OF-THOUGHT REASONING (REQUIRED)

Before generating the JSON query, think through your approach using these steps:

<thinking>
Step 1: Analyze JD requirements
- Extract: role, domain, seniority, mentioned_companies, implicit_criteria, company_stage
- Classify: Is this niche (CEO, Voice AI, specific domain) or broad (Junior Engineer, generic skills)?

Step 2: Determine field priority (use priority order below)
- Priority 1 (Company/Industry): If JD mentions specific companies → CRITICAL, use nested queries
- Priority 2 (Location): How flexible? Remote vs specific city? Include location wildcards
- Priority 3 (Role/Title): Exact match needed or variations acceptable?
- Priority 4 (Skills): Technical vs soft skills, use inferred_skills field
- Priority 5 (Seniority): NEVER in MUST, always SHOULD (only 1-2% of profiles have this)

Step 3: Select query strategy (UPDATED THRESHOLDS - LOWERED for CEO/executive/niche roles)
- Niche domain + senior/CEO role → "exploit" strategy (precision over recall)
  → Use minimum_should_match: 20% of total SHOULD clauses (was 40%, then 25%, now 20% for ultra-niche)
  → Expected: 30-150 high-quality candidates
  → NOTE: CEO/founder roles are <1% of profiles - use LOW thresholds!
- Broad domain + junior role → "explore" strategy (recall over precision)
  → Use minimum_should_match: 12% of total SHOULD clauses (was 20%, then 15%, now 12%)
  → Expected: 300-800 candidates
- Balanced → 15% match rate (was 30%, then 20%, now 15%)

Step 4: Build MUST clauses (KEEP MINIMAL OR EMPTY - prefer SHOULD clauses)
- **STRONGLY RECOMMENDED: Keep MUST array empty [] for maximum flexibility**
- ADD to MUST only if explicitly stated in JD AND field has >80% coverage:
  - Location country (if absolutely required): {"term": {"location_country": "United States"}}
  - **DO NOT add experience duration to MUST - see PRIORITY 6 warning above**
- NEVER add to MUST: is_deleted, connections_count, seniority, company_name, inferred_skills, is_working
- TIP: Empty MUST array is OK - rely on SHOULD clauses with minimum_should_match for filtering
- ⚠️ DATA TYPES: Use integers for numeric fields (company_founded_year: 2015 not "2015")

Step 5: Build SHOULD clauses (priority order, NO boost parameters allowed)
⚠️ CRITICAL WILDCARDING RULES:
- Use ONLY single-word wildcards in title/headline fields: "*engineer*" ✓, "*software engineer*" ✗ (returns 0)
- For multi-word roles, create SEPARATE single-word clauses:
  - "Software Engineer" → {"wildcard": {"active_experience_title": "*software*"}} AND {"wildcard": {"active_experience_title": "*engineer*"}}
  - "Machine Learning" → {"wildcard": {"headline": "*machine*"}} AND {"wildcard": {"headline": "*learning*"}}
- Exception: location_full CAN use multi-word: "*san francisco*" works, "*united states*" works
- Do NOT add "boost" parameters (API doesn't support scoring)

1. Role/Title - HIGHEST PRIORITY (single-word wildcards only)
   Examples:
   - "CEO" → {"wildcard": {"active_experience_title": "*ceo*"}}
   - "Software Engineer" → {"wildcard": {"active_experience_title": "*software*"}}, {"wildcard": {"active_experience_title": "*engineer*"}}
   - "Senior Developer" → {"wildcard": {"active_experience_title": "*senior*"}}, {"wildcard": {"active_experience_title": "*developer*"}}

2. Headline keywords - HIGH PRIORITY (single words only)
   Examples:
   - {"wildcard": {"headline": "*python*"}}, {"wildcard": {"headline": "*ai*"}}
   - Break phrases: "Machine Learning" → {"wildcard": {"headline": "*machine*"}}, {"wildcard": {"headline": "*learning*"}}

3. Skills - HIGH PRIORITY (use inferred_skills with COMMON terms ONLY)
   ⚠️ CRITICAL: inferred_skills contains ONLY common, broad skills - NOT cutting-edge acronyms!

   ✓ WORKS in inferred_skills (common skills):
   - {"term": {"inferred_skills": "Python"}}
   - {"term": {"inferred_skills": "JavaScript"}}
   - {"term": {"inferred_skills": "Machine Learning"}}
   - {"term": {"inferred_skills": "AI"}}
   - {"term": {"inferred_skills": "AWS"}}
   - {"term": {"inferred_skills": "React"}}

   ✗ DOESN'T WORK in inferred_skills (returns 0 results - use headline instead):
   - {"term": {"inferred_skills": "LLM"}} → Use {"wildcard": {"headline": "*llm*"}}
   - {"term": {"inferred_skills": "RAG"}} → Use {"wildcard": {"headline": "*rag*"}}
   - {"term": {"inferred_skills": "WebRTC"}} → Use {"wildcard": {"headline": "*webrtc*"}}
   - {"term": {"inferred_skills": "STT"}} → Use {"wildcard": {"headline": "*speech*"}}
   - {"term": {"inferred_skills": "TTS"}} → Use {"wildcard": {"headline": "*text*"}}

   Rule: If skill is an ACRONYM or very NEW/NICHE → use headline wildcard, NOT inferred_skills

4. Company/Industry - MEDIUM PRIORITY
   - {"term": {"company_industry": "Software Development"}}
   - If mentioned_companies exist: Add nested queries (see Step 3 for nested query format)

5. Location - MEDIUM PRIORITY (multi-word wildcards OK here)
   Examples:
   - {"wildcard": {"location_full": "*united states*"}} (works!)
   - {"wildcard": {"location_full": "*san francisco*"}} (works!)
   - {"wildcard": {"location_full": "*remote*"}}

6. Seniority - LOW PRIORITY (SHOULD ONLY, NEVER MUST)
   - {"term": {"active_experience_management_level": "Senior"}} (low coverage, use sparingly)

Step 6: Calculate minimum_should_match
- Count total SHOULD clauses generated
- Apply strategy percentage (AGGRESSIVELY LOWERED for CEO/executive/niche roles):
  - exploit: total * 0.20 → round to integer (was 0.40, then 0.25, now 0.20 for ultra-niche CEO roles)
  - balanced: total * 0.15 → round to integer (was 0.30, then 0.20, now 0.15)
  - explore: total * 0.12 → round to integer (was 0.20, then 0.15, now 0.12)
- Show calculation: "24 clauses * 0.20 = 4.8 → minimum_should_match: 5" (Voice AI CEO example)
- CRITICAL: CEO/founder/executive roles are <1% of all profiles - MUST use low thresholds (15-20%)
- Niche technical skills (LLM, Voice AI, WebRTC) further reduce pool - compensate with lower match requirements

Step 7: Validation checks
- ✓ No is_working filter (excludes job seekers)
- ✓ No is_deleted or connections_count in MUST (too restrictive)
- ✓ No "boost" parameters in SHOULD clauses (API doesn't support scoring)
- ✓ Seniority in SHOULD only (C-Level in MUST fails 99% of profiles)
- ✓ Nested query for past experience (if mentioned_companies exists)
- ✓ Location wildcards for flexibility (always include remote option)
- ✓ Expected result range based on strategy (e.g., "20-50 candidates for CEO role with exploit")
</thinking>

Then return the JSON query.

This structured thinking helps debug query failures and ensures consistent quality.

## FIELD PRIORITY ORDER (How to Build Queries)

### PRIORITY 1: COMPANY & INDUSTRY (Most Important - Search Company Experience First!)
- `company_name` (String, wildcard) - Target specific companies: "*google*", "*meta*", "*startup*"
- `company_industry` (String, term) - Industry: "Software Development", "Financial Services"
- `company_type` (String, term) - "Public Company", "Privately Held", "Non-Profit"
- `company_employees_count` (Integer, range) - Exact headcount for sizing
- `company_founded_year` (String YYYY, range) - Startup proxy: >= "2020" = recent
- `company_is_b2b` (Integer 0/1, term) - B2B vs B2C

**CRITICAL - Past Company Experience (Use Nested Queries):**
```json
{
  "nested": {
    "path": "experience",
    "query": {
      "bool": {
        "should": [
          {"wildcard": {"experience.company_name": "*google*"}},
          {"term": {"experience.company_industry": "Software Development"}}
        ],
        "minimum_should_match": 1
      }
    }
  }
}
```
This finds people who EVER worked at target companies (not just currently)!

### PRIORITY 2: LOCATION (Geographic Constraints)
- `location_full` (String, wildcard) - Flexible: "*san francisco*", "*bay area*", "*remote*"
- `location_country` (String, term) - Exact: "United States"
- `location_city` (String, term) - Exact: "San Francisco"
- `location_state` (String, term) - Exact: "California"

### PRIORITY 3: ROLE & TITLE (Functional Match)
- `active_experience_title` (String, wildcard) - Current title: "*engineer*", "*senior*"
- `active_experience_department` (String enum, term) - "Engineering and Technical", "Data Science"
- `headline` (String, wildcard) - Profile headline for keywords

### PRIORITY 4: FUNDING (Growth Stage Signal)
- `company_founded_year` (String, range) - Proxy for stage (>= "2020" = startup)
- `company_last_funding_round_date` (String date, range) - Funding recency (63% coverage)
⚠️ NEVER USE: `company_last_funding_round_amount_raised` (always NULL)

### PRIORITY 5: MANAGEMENT LEVEL (Seniority) - ⚠️ USE IN SHOULD ONLY!
- `active_experience_management_level` (String enum) - "Senior", "Manager", "C-Level"
- `is_decision_maker` (Integer 0/1) - Leadership flag

**WARNING:** "Senior" appears in only 2% of profiles! Never use in MUST clauses.

### PRIORITY 6: SKILLS & EXPERIENCE (Technical Requirements)
- `inferred_skills` (Array[String], term) - ✅ CONFIRMED WORKING: {"term": {"inferred_skills": "Python"}}
- `education_degrees` (Array[String], wildcard) - Degree requirements: "*bachelor*"

⚠️ **CRITICAL: NEVER USE total_experience_duration_months in queries (MUST or SHOULD)**
- Field: `total_experience_duration_months` (Integer, range)
- Coverage: <50% of profiles, especially executives/CEOs
- **WRONG:** `{"range": {"total_experience_duration_months": {"gte": 60}}}`
- **CORRECT:** Omit entirely - use title wildcards (*senior*, *lead*, *principal*) + headline keywords
- **Translation Guide:**
  - JD says "10+ years" → Use `{"wildcard": {"active_experience_title": "*senior*"}}` or `{"wildcard": {"active_experience_title": "*principal*"}}`
  - JD says "5+ years" → Use `{"wildcard": {"active_experience_title": "*mid*"}}` or specific role titles
  - **NEVER filter by duration - it excludes too many valid candidates**

## CRITICAL QUERY CONSTRUCTION RULES

1. **NO is_working filter** - Include both employed AND job-seeking candidates
   - Don't filter by employment status
   - Use nested queries to find people with past relevant experience

2. **MUST clause rules (UPDATED) - ⚠️ EXTREMELY IMPORTANT**:
   - **DEFAULT: KEEP MUST ARRAY EMPTY OR MINIMAL** - Use SHOULD clauses with minimum_should_match instead!
   - ADD to MUST ONLY if ALL of these conditions are met:
     a) Field is explicitly stated in JD (not inferred)
     b) Field has very high coverage (>80% of profiles)
     c) Field is stable/standardized (not variable)

   - ✅ SAFE for MUST (if explicitly stated):
     - Location country ONLY: `{"term": {"location_country": "United States"}}`
     - THAT'S IT - Keep MUST minimal or empty!

   - ❌ NEVER add to MUST (ALWAYS use SHOULD instead):
     - `total_experience_duration_months` - **FICKLE FIELD** with low/unreliable coverage
       - Why: Not populated for many profiles, especially executives/CEOs
       - CORRECT: Use in SHOULD as optional bonus (if experience matters)
       - WRONG: Add to MUST (will exclude 50%+ of valid candidates)
     - `inferred_skills` - **CRITICAL:** Even if "Python" is in must_have, use SHOULD not MUST!
       - Why: Coverage varies, "Python" in must_have means "prioritize Python" not "exclude non-Python"
       - CORRECT: Add to SHOULD with higher weight via minimum_should_match
       - WRONG: Add to MUST (will exclude 70%+ of valid candidates)
     - `active_experience_title` - Spelling variations, use SHOULD with wildcards
     - `active_experience_management_level` - Only 1-2% coverage, use SHOULD
     - `company_name` / `company_industry` - Too restrictive, use SHOULD or nested
     - `is_deleted` - Causes issues with some profiles
     - `connections_count` - Too restrictive
     - `is_working` - Excludes active job seekers

   - ⚠️ IMPORTANT: company_founded_year must be INTEGER not STRING: `{"gte": 2015}` not `{"gte": "2015"}`

   **Example of WRONG vs CORRECT:**
   ❌ WRONG (will return 0-5 results):
   ```json
   "must": [
     {"term": {"location_country": "United States"}},
     {"term": {"inferred_skills": "Python"}},  // Too restrictive!
     {"wildcard": {"active_experience_title": "*engineer*"}}  // Too restrictive!
   ]
   ```

   ✅ CORRECT (will return 20-100 results):
   ```json
   "must": [
     {"term": {"location_country": "United States"}}  // Only location
   ],
   "should": [
     {"term": {"inferred_skills": "Python"}},  // Skills in SHOULD
     {"wildcard": {"active_experience_title": "*engineer*"}},  // Titles in SHOULD
     {"wildcard": {"headline": "*python*"}}
   ],
   "minimum_should_match": 2  // Requires 2 out of 3 SHOULD clauses
   ```

3. **NESTED QUERY FOR MENTIONED COMPANIES (CRITICAL)**:
   If JD includes "mentioned_companies" field, ALWAYS add high-priority nested query:
   ```json
   {
     "nested": {
       "path": "experience",
       "query": {
         "bool": {
           "should": [
             {"wildcard": {"experience.company_name": "*otter*"}},
             {"wildcard": {"experience.company_name": "*deepgram*"}},
             {"wildcard": {"experience.company_name": "*assemblyai*"}},
             {"term": {"experience.company_industry": "Software Development"}}
           ],
           "minimum_should_match": 1
         }
       },
       "boost": 3.0
     }
   }
   ```
   This finds people who EVER worked at target companies (competitive intelligence).
   Also use competitor_context keywords in headline/skills searches.

4. **Build queries by priority:**
   - Start with company/industry (Priority 1) - Most specific
   - Add location if specified (Priority 2)
   - Layer in role/title (Priority 3)
   - Add funding/stage if mentioned (Priority 4)
   - Add seniority in SHOULD only (Priority 5)
   - Add skills as SHOULD clauses (Priority 6)

5. **Permissiveness target (dynamic based on role specificity):**
   - Niche roles (CEO, specialized domain): 15-20 SHOULD clauses, minimum_should_match: 9-12 (60%)
   - Broad roles (Junior Engineer): 10-15 SHOULD clauses, minimum_should_match: 3-4 (25%)
   - Expected: Niche = 20-50 candidates, Broad = 80-150 candidates

## COMPLETE EXAMPLE QUERY (All Priorities)

**JD:** "Senior Python Engineer with 5+ years at Series A startup in SF"

```json
{
  "query": {
    "bool": {
      "must": [],
      "should": [
        // Priority 1: Company & Industry (5 clauses)
        {"range": {"company_founded_year": {"gte": "2018", "lte": "2023"}}},
        {"range": {"company_employees_count": {"gte": 10, "lte": 500}}},
        {"term": {"company_industry": "Software Development"}},
        {"nested": {
          "path": "experience",
          "query": {
            "bool": {
              "should": [
                {"range": {"experience.company_employees_count": {"lte": 500}}},
                {"term": {"experience.company_industry": "Software Development"}},
                {"wildcard": {"experience.company_name": "*startup*"}}
              ],
              "minimum_should_match": 1
            }
          }
        }},

        // Priority 2: Location (3 clauses)
        {"wildcard": {"location_full": "*san francisco*"}},
        {"wildcard": {"location_full": "*bay area*"}},
        {"term": {"location_country": "United States"}},

        // Priority 3: Role & Title (3 clauses)
        {"wildcard": {"active_experience_title": "*engineer*"}},
        {"wildcard": {"active_experience_title": "*senior*"}},
        {"term": {"active_experience_department": "Engineering and Technical"}},

        // Priority 5: Seniority (2 clauses - SHOULD only!)
        {"term": {"active_experience_management_level": "Senior"}},
        {"wildcard": {"active_experience_title": "*lead*"}},

        // Priority 6: Skills & Experience (4 clauses)
        {"term": {"inferred_skills": "Python"}},
        {"wildcard": {"headline": "*python*"}},
        {"wildcard": {"headline": "*backend*"}},
        {"range": {"total_experience_duration_months": {"gte": 60}}}
      ],
      "minimum_should_match": 3
    }
  }
}
```

**CRITICAL:**
- Do NOT include `"sort"`, `"from"`, or `"size"` parameters (the API handles pagination automatically)
- Do NOT use `"boost"` parameters in should clauses (multi-source API does not support scoring)
- Do NOT use multi-word wildcards like `"*software engineer*"` (returns 0 results - use separate single-word wildcards instead)

**TESTED WORKING PATTERNS (use these as templates):**

✓ **Simple role search** (returns 1000 results):
```json
{
  "query": {
    "bool": {
      "should": [
        {"wildcard": {"active_experience_title": "*engineer*"}},
        {"wildcard": {"active_experience_title": "*senior*"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

✓ **Role + Location** (returns 1000 results):
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"location_country": "United States"}}
      ],
      "should": [
        {"wildcard": {"active_experience_title": "*engineer*"}},
        {"term": {"inferred_skills": "Python"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

✓ **Comprehensive search** (returns 164+ results):
```json
{
  "query": {
    "bool": {
      "should": [
        {"wildcard": {"active_experience_title": "*engineer*"}},
        {"wildcard": {"active_experience_title": "*senior*"}},
        {"wildcard": {"headline": "*python*"}},
        {"wildcard": {"headline": "*ai*"}},
        {"term": {"inferred_skills": "Python"}},
        {"wildcard": {"location_full": "*united states*"}},
        {"wildcard": {"location_full": "*remote*"}},
        {"term": {"company_industry": "Software Development"}}
      ],
      "minimum_should_match": 3
    }
  }
}
```

✗ **WRONG - Multi-word wildcard** (returns 0 results):
```json
{"wildcard": {"active_experience_title": "*software engineer*"}}
```

✓ **CEO/Founder in niche domain (Voice AI)** (returns 50-150 results with new thresholds):
{
  "query": {
    "bool": {
      "must": [],  // EMPTY MUST - maximum flexibility for CEO roles
      "should": [
        // Title variations (6 clauses)
        {"wildcard": {"active_experience_title": "*ceo*"}},
        {"wildcard": {"active_experience_title": "*founder*"}},
        {"wildcard": {"active_experience_title": "*chief*"}},
        {"wildcard": {"active_experience_title": "*executive*"}},
        {"wildcard": {"active_experience_title": "*president*"}},
        {"wildcard": {"active_experience_title": "*co-founder*"}},

        // Headline wildcards for NICHE SKILLS (8 clauses) - NOT inferred_skills!
        {"wildcard": {"headline": "*llm*"}},
        {"wildcard": {"headline": "*voice*"}},
        {"wildcard": {"headline": "*speech*"}},
        {"wildcard": {"headline": "*conversational*"}},
        {"wildcard": {"headline": "*webrtc*"}},
        {"wildcard": {"headline": "*real-time*"}},
        {"wildcard": {"headline": "*ai*"}},
        {"wildcard": {"headline": "*machine learning*"}},

        // Common skills in inferred_skills (3 clauses)
        {"term": {"inferred_skills": "Python"}},
        {"term": {"inferred_skills": "Machine Learning"}},
        {"term": {"inferred_skills": "AI"}},

        // Location (2 clauses) - keep flexible for CEO roles
        {"wildcard": {"location_full": "*united states*"}},
        {"wildcard": {"location_full": "*remote*"}},

        // Companies - Big Tech + Voice AI specialists (1 nested clause = counts as 1)
        {"nested": {
          "path": "experience",
          "query": {
            "bool": {
              "should": [
                {"wildcard": {"experience.company_name": "*google*"}},
                {"wildcard": {"experience.company_name": "*meta*"}},
                {"wildcard": {"experience.company_name": "*openai*"}},
                {"wildcard": {"experience.company_name": "*deepgram*"}},
                {"wildcard": {"experience.company_name": "*assemblyai*"}},
                {"wildcard": {"experience.company_name": "*twilio*"}},
                {"wildcard": {"experience.company_name": "*discord*"}},
                {"wildcard": {"experience.company_name": "*livekit*"}}
              ],
              "minimum_should_match": 1
            }
          }
        }}
      ],
      "minimum_should_match": 4
    }
  }
}

**This CEO query (20 SHOULD clauses, min 4 = 20% match rate):**
- ✅ Uses headline wildcards for niche acronyms (LLM, WebRTC) instead of inferred_skills
- ✅ EMPTY MUST array for maximum flexibility
- ✅ NO total_experience_duration_months (field is unreliable for executives)
- ✅ Lower threshold: 4/20 clauses = 20% (exploit strategy for CEO/niche)
- ✅ Nested company query counts as 1 SHOULD clause (not 8 separate)
- ✅ Combines C-Level titles with domain expertise
- ✅ Nested query includes Big Tech + Voice AI companies
- ✅ Expected result: 40-80 CEO candidates with Voice AI background

**This query:**
- ✅ Finds people at Series A startups (founded 2018-2023, 10-500 employees)
- ✅ Includes people who PREVIOUSLY worked at startups (nested query)
- ✅ Finds people in SF Bay Area (multiple location variations)
- ✅ Matches engineering roles with Python skills
- ✅ Requires only 3 out of 17 criteria (very permissive 18% match rate)
- ✅ NO is_working filter (includes job seekers)
- ✅ Expected result: 50-200 relevant candidates

## ENUM VALUES REFERENCE

**active_experience_department:**
"C-Suite", "Engineering and Technical", "Data Science", "Product Management", "Marketing", "Sales", "Finance & Accounting", "Operations", "Human Resources"

**active_experience_management_level:**
"C-Level", "Senior", "Manager", "Mid-Level", "Specialist", "Intern"
(Distribution: Specialist 74%, Manager 14%, Senior 2%, C-Level 1%)

Generate a CoreSignal Elasticsearch DSL query for the following JD requirements.

**IMPORTANT OUTPUT FORMAT:**
1. First, include your chain-of-thought reasoning inside <thinking></thinking> tags
2. Then, provide the JSON query

Example response format:
<thinking>
Step 1: Analyze JD requirements...
Step 2: Determine field priority...
...
</thinking>

{
  "query": { ... }
}
"""

    def _clean_json_response(self, query_text: str) -> str:
        """
        Clean LLM response to extract valid JSON.

        - Strips markdown code blocks
        - Removes JavaScript-style comments (// ...)
        - Fixes trailing commas
        """
        import re

        # Extract JSON from markdown code blocks if present
        if query_text.startswith("```"):
            query_text = query_text.split("```")[1]
            if query_text.startswith("json"):
                query_text = query_text[4:]
            query_text = query_text.strip()

        # Strip JavaScript-style comments (// ...) that some LLMs include
        lines = query_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove inline comments
            if '//' in line:
                line = line.split('//')[0]
            cleaned_lines.append(line)
        query_text = '\n'.join(cleaned_lines)

        # Fix trailing commas before closing brackets/braces (common GPT error)
        query_text = re.sub(r',(\s*[}\]])', r'\1', query_text)

        # Remove multiline comments /* ... */
        query_text = re.sub(r'/\*.*?\*/', '', query_text, flags=re.DOTALL)

        return query_text.strip()

    def _extract_thinking_and_query(self, response_text: str) -> Dict[str, Any]:
        """
        Extract chain-of-thought thinking and JSON query from LLM response.

        Args:
            response_text: Raw LLM response that may contain <thinking> tags

        Returns:
            {
                "thinking": "...",  # CoT reasoning (or None if not present)
                "query_text": "..."  # JSON query string (cleaned)
            }
        """
        thinking = None
        query_text = response_text

        # Check if response contains <thinking> tags
        if "<thinking>" in response_text and "</thinking>" in response_text:
            # Extract thinking content
            thinking_start = response_text.find("<thinking>") + len("<thinking>")
            thinking_end = response_text.find("</thinking>")
            thinking = response_text[thinking_start:thinking_end].strip()

            # Extract query JSON (everything after </thinking>)
            query_text = response_text[thinking_end + len("</thinking>"):].strip()

        return {
            "thinking": thinking,
            "query_text": query_text
        }

    def _build_user_prompt(self, jd_requirements: Dict[str, Any]) -> str:
        """
        Build user prompt from JD requirements.

        This method consolidates the user prompt generation that was previously
        duplicated across Claude, GPT, and Gemini methods.

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            Formatted user prompt string
        """
        implicit_criteria = jd_requirements.get('implicit_criteria', {})
        experience_years = jd_requirements.get('experience_years', {})

        return f"""Generate a CoreSignal Elasticsearch DSL query for these JD requirements:

**Role & Seniority:**
- Title: {jd_requirements.get('role_title', 'Not specified')}
- Level: {jd_requirements.get('seniority_level', 'Not specified')}
- Company Stage: {jd_requirements.get('company_stage', 'Not specified')}

**Must-Have Requirements (CRITICAL - High Priority):**
{chr(10).join('- ' + req for req in jd_requirements.get('must_have', [])) if jd_requirements.get('must_have') else '- None specified'}

**Nice-to-Have (BONUS POINTS - Medium Priority):**
{chr(10).join('- ' + req for req in jd_requirements.get('nice_to_have', [])) if jd_requirements.get('nice_to_have') else '- None specified'}

**Implicit Preferences (discovered from JD text):**
- Leadership Required: {implicit_criteria.get('leadership_required', False)}
- Founder Experience Valued: {implicit_criteria.get('founder_experience_valued', False)}
- Company Building Experience: {implicit_criteria.get('company_building_experience', False)}
- Fundraising Ability: {implicit_criteria.get('fundraising_ability', False)}
- Network in Industry: {implicit_criteria.get('network_in_industry', 'Not specified')}
- Technical Credibility: {implicit_criteria.get('technical_credibility', False)}
- Execution Speed: {implicit_criteria.get('execution_speed', False)}

**Domain Context:**
- Target Domain: {jd_requirements.get('target_domain', 'Not specified')}
- Domain Expertise: {', '.join(jd_requirements.get('domain_expertise', []))}
- Competitor Context: {jd_requirements.get('competitor_context', 'Not specified')}

**Mentioned Companies (USE IN NESTED QUERIES FOR PAST EXPERIENCE):**
{', '.join(jd_requirements.get('mentioned_companies', [])) if jd_requirements.get('mentioned_companies') else 'None mentioned'}

**Technical Skills:**
{', '.join(jd_requirements.get('technical_skills', [])) if jd_requirements.get('technical_skills') else 'None specified'}

**Location & Experience:**
- Location: {jd_requirements.get('location', 'Not specified')}
- Min Experience: {experience_years.get('minimum', 'Not specified')} years
- Preferred Experience: {experience_years.get('preferred', 'Not specified')} years

**IMPORTANT:** Follow the <thinking> steps in the system prompt. Generate nested queries for mentioned_companies. Use dynamic minimum_should_match based on role specificity.

Return the JSON query."""

    def generate_with_claude(self, jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate query using Claude (configured model).

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            {"query": {...}, "reasoning": "...", "model": "..."}
        """
        try:
            if self.anthropic_client is None:
                error_msg = "Anthropic client not initialized."
                if self.anthropic_init_error:
                    error_msg += f" Initialization error: {self.anthropic_init_error}"
                else:
                    error_msg += " Check ANTHROPIC_API_KEY environment variable."
                return {
                    "error": error_msg,
                    "model": self.claude_config.display_name
                }

            # Build user prompt from shared method
            user_prompt = self._build_user_prompt(jd_requirements)

            # LOG POINT 1: Before Claude API call
            debug_log.llm_prompt(
                model=self.claude_config.display_name,
                prompt=user_prompt,
                requirements=jd_requirements,
                temperature=0,
                max_tokens=self.claude_config.max_tokens
            )

            # Retry logic for rate limits (exponential backoff)
            max_retries = 3
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    # Use config for model parameters
                    response = self.anthropic_client.messages.create(
                        model=self.claude_config.model_name,
                        max_tokens=self.claude_config.max_tokens,
                        temperature=0 if self.claude_config.supports_temperature else None,
                        system=self.system_prompt,
                        messages=[{
                            "role": "user",
                            "content": user_prompt
                        }]
                    )
                    break  # Success, exit retry loop

                except RateLimitError as e:
                    retry_count += 1
                    last_error = e
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                        debug_log.error(
                            f"{self.claude_config.display_name} rate limit - retry {retry_count}/{max_retries} after {wait_time}s",
                            exception=e,
                            context={"retry_count": retry_count, "wait_time": wait_time}
                        )
                        time.sleep(wait_time)
                    else:
                        # Max retries exceeded, raise the error
                        raise

            if last_error and retry_count >= max_retries:
                # Should not reach here, but just in case
                raise last_error

            response_text = response.content[0].text.strip()

            # LOG POINT 2: After Claude response (raw, before markdown stripping)
            debug_log.llm_response(self.claude_config.display_name, response=response_text)

            # Extract thinking and query
            extracted = self._extract_thinking_and_query(response_text)
            thinking = extracted["thinking"]
            query_text = extracted["query_text"]

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 3: After JSON parsing
            debug_log.llm_response(
                self.claude_config.display_name,
                parsed_query=query,
                thinking=thinking,
                success=True
            )

            return {
                "query": query,
                "thinking": thinking,  # NEW: Chain-of-thought reasoning
                "reasoning": self.claude_config.reasoning,
                "model": self.claude_config.display_name
            }

        except Exception as e:
            # LOG POINT 4: Error handler
            debug_log.error(
                f"{self.claude_config.display_name} query generation failed",
                exception=e,
                context={"model": self.claude_config.model_name},
                raw_data=query_text if 'query_text' in locals() else None
            )
            return {
                "error": str(e),
                "model": self.claude_config.display_name
            }

    def generate_with_gpt5(self, jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate query using OpenAI (configured model).

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            {"query": {...}, "reasoning": "...", "model": "..."}
        """
        try:
            if self.openai_client is None:
                error_msg = "OpenAI client not initialized."
                if self.openai_init_error:
                    error_msg += f" Initialization error: {self.openai_init_error}"
                else:
                    error_msg += " Check OPENAI_API_KEY environment variable."
                return {
                    "error": error_msg,
                    "model": self.openai_config.display_name
                }

            # Build user prompt from shared method
            user_prompt = self._build_user_prompt(jd_requirements)

            # LOG POINT 5: Before GPT API call
            debug_log.llm_prompt(
                model=self.openai_config.display_name,
                prompt=user_prompt,
                requirements=jd_requirements,
                temperature=0,
                max_tokens=self.openai_config.max_tokens
            )

            # Build API call with config
            api_params = {
                "model": self.openai_config.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }

            # Only add temperature if supported
            if self.openai_config.supports_temperature:
                api_params["temperature"] = 0

            # Retry logic for rate limits (exponential backoff)
            max_retries = 3
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    response = self.openai_client.chat.completions.create(**api_params)
                    break  # Success, exit retry loop

                except openai.RateLimitError as e:
                    retry_count += 1
                    last_error = e
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                        debug_log.error(
                            f"{self.openai_config.display_name} rate limit - retry {retry_count}/{max_retries} after {wait_time}s",
                            exception=e,
                            context={"retry_count": retry_count, "wait_time": wait_time}
                        )
                        time.sleep(wait_time)
                    else:
                        # Max retries exceeded, raise the error
                        raise

            if last_error and retry_count >= max_retries:
                # Should not reach here, but just in case
                raise last_error

            response_text = response.choices[0].message.content.strip()

            # LOG POINT 6: After GPT response
            debug_log.llm_response(self.openai_config.display_name, response=response_text)

            # Extract thinking and query
            extracted = self._extract_thinking_and_query(response_text)
            thinking = extracted["thinking"]
            query_text = extracted["query_text"]

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 7: After JSON parsing
            debug_log.llm_response(
                self.openai_config.display_name,
                parsed_query=query,
                thinking=thinking,
                success=True
            )

            return {
                "query": query,
                "thinking": thinking,  # NEW: Chain-of-thought reasoning
                "reasoning": self.openai_config.reasoning,
                "model": self.openai_config.display_name
            }

        except Exception as e:
            # LOG POINT 8: Error handler
            debug_log.error(
                f"{self.openai_config.display_name} query generation failed",
                exception=e,
                context={"model": self.openai_config.model_name},
                raw_data=query_text if 'query_text' in locals() else None
            )
            return {
                "error": str(e),
                "model": self.openai_config.display_name
            }

    def generate_with_gemini(self, jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate query using Google Gemini (configured model).

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            {"query": {...}, "reasoning": "...", "model": "..."}
        """
        try:
            # Build user prompt from shared method
            user_prompt = self._build_user_prompt(jd_requirements)

            # LOG POINT 9: Before Gemini API call
            debug_log.llm_prompt(
                model=self.google_config.display_name,
                prompt=user_prompt,
                requirements=jd_requirements,
                temperature=0,
                max_tokens=self.google_config.max_tokens
            )

            # Initialize client with new google-genai SDK
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Gemini doesn't support separate system prompts, combine them
            combined_prompt = f"{self.system_prompt}\n\n{user_prompt}"

            # Retry logic for rate limits (exponential backoff)
            max_retries = 3
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    # Generate content using new SDK
                    response = client.models.generate_content(
                        model=self.google_config.model_name,
                        contents=combined_prompt,
                        config={
                            "temperature": 0 if self.google_config.supports_temperature else None
                        }
                    )
                    break  # Success, exit retry loop

                except Exception as e:
                    # Check if it's a rate limit error (429 or similar)
                    error_msg = str(e).lower()
                    if "rate" in error_msg or "429" in error_msg or "quota" in error_msg:
                        retry_count += 1
                        last_error = e
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                            debug_log.error(
                                f"{self.google_config.display_name} rate limit - retry {retry_count}/{max_retries} after {wait_time}s",
                                exception=e,
                                context={"retry_count": retry_count, "wait_time": wait_time}
                            )
                            time.sleep(wait_time)
                        else:
                            # Max retries exceeded, raise the error
                            raise
                    else:
                        # Not a rate limit error, raise immediately
                        raise

            if last_error and retry_count >= max_retries:
                # Should not reach here, but just in case
                raise last_error

            response_text = response.text.strip()

            # LOG POINT 10: After Gemini response
            debug_log.llm_response(self.google_config.display_name, response=response_text)

            # Extract thinking and query
            extracted = self._extract_thinking_and_query(response_text)
            thinking = extracted["thinking"]
            query_text = extracted["query_text"]

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 11: After JSON parsing
            debug_log.llm_response(
                self.google_config.display_name,
                parsed_query=query,
                thinking=thinking,
                success=True
            )

            return {
                "query": query,
                "thinking": thinking,  # NEW: Chain-of-thought reasoning
                "reasoning": self.google_config.reasoning,
                "model": self.google_config.display_name
            }

        except Exception as e:
            # LOG POINT 12: Error handler
            debug_log.error(
                f"{self.google_config.display_name} query generation failed",
                exception=e,
                context={"model": self.google_config.model_name},
                raw_data=query_text if 'query_text' in locals() else None
            )
            return {
                "error": str(e),
                "model": self.google_config.display_name
            }

    def compare_all(self, jd_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate queries using all three LLMs and return comparison.

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            List of query results with model info
        """
        results = []

        # Generate with Claude
        claude_result = self.generate_with_claude(jd_requirements)
        results.append(claude_result)

        # Generate with GPT-5
        gpt5_result = self.generate_with_gpt5(jd_requirements)
        results.append(gpt5_result)

        # Generate with Gemini
        gemini_result = self.generate_with_gemini(jd_requirements)
        results.append(gemini_result)

        return results

    def format_query_for_display(self, query: Dict[str, Any]) -> str:
        """
        Format query JSON for readable display.

        Args:
            query: Elasticsearch DSL query

        Returns:
            Pretty-printed JSON string
        """
        return json.dumps(query, indent=2)
