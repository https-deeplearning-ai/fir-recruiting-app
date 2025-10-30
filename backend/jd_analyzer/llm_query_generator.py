"""
Multi-LLM Query Generator

Compares query generation across different LLMs (Claude, GPT-4, Gemini) to find
the best CoreSignal search query for a given JD.
"""

import os
from typing import Dict, List, Any, Optional
import anthropic
import openai
import google.generativeai as genai
import json
from .llm_configs import get_config
from .debug_logger import debug_log

class MultiLLMQueryGenerator:
    """
    Generates CoreSignal queries using multiple LLMs and compares results.
    """

    def __init__(self):
        """Initialize LLM clients and load configs."""
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        openai.api_key = os.getenv("OPENAI_API_KEY")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        # Load model configurations
        self.claude_config = get_config("claude")
        self.openai_config = get_config("openai")
        self.google_config = get_config("google")

        # Query generation prompt template
        self.system_prompt = """You are an expert at translating job requirements into CoreSignal Elasticsearch DSL queries.

REFERENCE: See backend/jd_analyzer/CORESIGNAL_FIELD_REFERENCE.md for complete field documentation.

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
- `total_experience_duration_months` (Integer, range) - ✅ CONFIRMED WORKING: {"range": {"total_experience_duration_months": {"gte": 60}}}
- `education_degrees` (Array[String], wildcard) - Degree requirements: "*bachelor*"

## CRITICAL QUERY CONSTRUCTION RULES

1. **NO is_working filter** - Include both employed AND job-seeking candidates
   - Don't filter by employment status
   - Use nested queries to find people with past relevant experience

2. **Empty MUST array (usually)** - Use SHOULD clauses with minimum_should_match
   - Better to get 100 candidates than 0
   - Prefer: `"must": []`
   - Only use MUST for absolute requirements (rare)

3. **Build queries by priority:**
   - Start with company/industry (Priority 1) - Most specific
   - Add location if specified (Priority 2)
   - Layer in role/title (Priority 3)
   - Add funding/stage if mentioned (Priority 4)
   - Add seniority in SHOULD only (Priority 5)
   - Add skills as SHOULD clauses (Priority 6)

4. **Always include nested query** for past company experience
   - People change jobs - past experience is valuable
   - "Worked at Google" = "Works at Google" for our purposes

5. **Permissiveness target:**
   - 10-15 SHOULD clauses total
   - minimum_should_match: 3 (need 3 out of 15 = 20% match rate)
   - Expect 50-200 candidate results

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

**CRITICAL:** Do NOT include `"sort"` or `"from"` or `"size"` parameters. The API handles pagination automatically.

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

Generate a CoreSignal Elasticsearch DSL query for the following JD requirements. Follow the priority order. Return ONLY the JSON query, no explanation."""

    def _clean_json_response(self, query_text: str) -> str:
        """
        Clean LLM response to extract valid JSON.

        - Strips markdown code blocks
        - Removes JavaScript-style comments (// ...)
        """
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

        return query_text.strip()

    def generate_with_claude(self, jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate query using Claude (configured model).

        Args:
            jd_requirements: Parsed JD requirements from JDParser (dict)

        Returns:
            {"query": {...}, "reasoning": "...", "model": "..."}
        """
        try:
            # Build user prompt with safe .get() access
            user_prompt = f"""Generate a CoreSignal Elasticsearch DSL query for these JD requirements:

**Role Title:** {jd_requirements.get('role_title', 'Not specified')}
**Seniority Level:** {jd_requirements.get('seniority_level', 'Not specified')}
**Technical Skills:** {', '.join(jd_requirements.get('technical_skills', []))}
**Location:** {jd_requirements.get('location', 'Not specified')}
**Experience Years:** {jd_requirements.get('experience_years', {}).get('minimum', 'Not specified')} years minimum
**Domain Expertise:** {', '.join(jd_requirements.get('domain_expertise', []))}
**Must-Have Requirements:** {', '.join(jd_requirements.get('must_have', []))}

Return ONLY the JSON query."""

            # LOG POINT 1: Before Claude API call
            debug_log.llm_prompt(
                model=self.claude_config.display_name,
                prompt=user_prompt,
                requirements=jd_requirements,
                temperature=0,
                max_tokens=self.claude_config.max_tokens
            )

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

            query_text = response.content[0].text.strip()

            # LOG POINT 2: After Claude response (raw, before markdown stripping)
            debug_log.llm_response(self.claude_config.display_name, response=query_text)

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 3: After JSON parsing
            debug_log.llm_response(
                self.claude_config.display_name,
                parsed_query=query,
                success=True
            )

            return {
                "query": query,
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
            # Build user prompt with safe .get() access
            user_prompt = f"""Generate a CoreSignal Elasticsearch DSL query for these JD requirements:

**Role Title:** {jd_requirements.get('role_title', 'Not specified')}
**Seniority Level:** {jd_requirements.get('seniority_level', 'Not specified')}
**Technical Skills:** {', '.join(jd_requirements.get('technical_skills', []))}
**Location:** {jd_requirements.get('location', 'Not specified')}
**Experience Years:** {jd_requirements.get('experience_years', {}).get('minimum', 'Not specified')} years minimum
**Domain Expertise:** {', '.join(jd_requirements.get('domain_expertise', []))}
**Must-Have Requirements:** {', '.join(jd_requirements.get('must_have', []))}

Return ONLY the JSON query."""

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

            response = openai.chat.completions.create(**api_params)

            query_text = response.choices[0].message.content.strip()

            # LOG POINT 6: After GPT response
            debug_log.llm_response(self.openai_config.display_name, response=query_text)

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 7: After JSON parsing
            debug_log.llm_response(
                self.openai_config.display_name,
                parsed_query=query,
                success=True
            )

            return {
                "query": query,
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
            # Build user prompt with safe .get() access
            user_prompt = f"""Generate a CoreSignal Elasticsearch DSL query for these JD requirements:

**Role Title:** {jd_requirements.get('role_title', 'Not specified')}
**Seniority Level:** {jd_requirements.get('seniority_level', 'Not specified')}
**Technical Skills:** {', '.join(jd_requirements.get('technical_skills', []))}
**Location:** {jd_requirements.get('location', 'Not specified')}
**Experience Years:** {jd_requirements.get('experience_years', {}).get('minimum', 'Not specified')} years minimum
**Domain Expertise:** {', '.join(jd_requirements.get('domain_expertise', []))}
**Must-Have Requirements:** {', '.join(jd_requirements.get('must_have', []))}

Return ONLY the JSON query."""

            # LOG POINT 9: Before Gemini API call
            debug_log.llm_prompt(
                model=self.google_config.display_name,
                prompt=user_prompt,
                requirements=jd_requirements,
                temperature=0,
                max_tokens=self.google_config.max_tokens
            )

            # Use config for model
            model = genai.GenerativeModel(self.google_config.model_name)

            # Build generation config based on capabilities
            gen_config_params = {}
            if self.google_config.supports_temperature:
                gen_config_params["temperature"] = 0

            # Gemini doesn't support separate system prompts, combine them
            combined_prompt = f"{self.system_prompt}\n\n{user_prompt}"

            response = model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(**gen_config_params) if gen_config_params else None
            )

            query_text = response.text.strip()

            # LOG POINT 10: After Gemini response
            debug_log.llm_response(self.google_config.display_name, response=query_text)

            # Clean response and extract JSON
            query_text = self._clean_json_response(query_text)
            query = json.loads(query_text)

            # LOG POINT 11: After JSON parsing
            debug_log.llm_response(
                self.google_config.display_name,
                parsed_query=query,
                success=True
            )

            return {
                "query": query,
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
