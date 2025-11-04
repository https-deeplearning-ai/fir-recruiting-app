"""
JD Data Validation Agent

Uses GPT-4o with Chain-of-Thought (CoT) prompting and few-shot examples
to validate that JD data was correctly transformed from parse → research payload.

Prevents bugs like:
- Losing mentioned companies during transformation
- Domain being replaced with default values
- Role title becoming "Engineering Role" instead of actual title
"""

import os
from typing import Dict, Any, List
from gpt5_client import GPT5Client


class JDValidationAgent:
    """
    Validates JD data transformations using GPT-4o with CoT reasoning.

    Uses Chain-of-Thought prompting with few-shot examples to ensure
    data integrity between JD parsing and company research payload.
    """

    def __init__(self):
        """Initialize validation agent with GPT-4o client"""
        self.client = GPT5Client()  # Uses GPT-4o (gpt-4o model)

    def validate_transformation(
        self,
        jd_text: str,
        parsed_requirements: Dict[str, Any],
        research_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that JD data was correctly transformed.

        Args:
            jd_text: Original job description text
            parsed_requirements: Output from /api/jd/parse
            research_payload: Input to /research-companies

        Returns:
            {
                "valid": True/False,
                "reasoning": "Step-by-step CoT analysis",
                "issues": ["issue1", "issue2"],
                "recommendation": "How to fix"
            }
        """
        prompt = self._build_cot_prompt(jd_text, parsed_requirements, research_payload)

        # Use GPT-4o with low temperature for deterministic validation
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )

        # Parse GPT-4o response
        result = self._parse_validation_response(response)

        return result

    def _build_cot_prompt(
        self,
        jd_text: str,
        parsed_requirements: Dict[str, Any],
        research_payload: Dict[str, Any]
    ) -> str:
        """
        Build Chain-of-Thought prompt with few-shot examples.

        Returns:
            Prompt string with CoT instructions + 3 examples + actual validation task
        """

        # Truncate JD text to first 500 chars for prompt efficiency
        jd_snippet = jd_text[:500] + "..." if len(jd_text) > 500 else jd_text

        prompt = f"""You are a data validation agent. Your job is to validate if job description (JD) data was correctly transformed for company research.

Use this step-by-step Chain-of-Thought reasoning process:

**Step 1: Extract key signals from the original JD text**
- What companies are mentioned?
- What domain/industry is it?
- What role title is it?

**Step 2: Check if parsed requirements captured these signals**
- Are mentioned companies in parsed.mentioned_companies?
- Is domain in parsed.target_domain?
- Is role title in parsed.role_title?

**Step 3: Check if research payload preserved the parsed data**
- Are parsed companies in payload.target_companies.mentioned_companies?
- Is parsed domain in payload.requirements.domain?
- Is role title in payload.title (not "Engineering Role" default)?

**Step 4: Identify any data loss**
- What was mentioned in JD but missing in payload?
- What defaults were used instead of real data?

**Step 5: Final verdict**
- PASS: All critical info preserved
- FAIL: Data loss detected (list what was lost)

---

# FEW-SHOT EXAMPLES

## Example 1: PASS (All data preserved)

JD: "Senior Voice AI Engineer... companies like Deepgram, AssemblyAI"

Parsed:
{{
  "mentioned_companies": ["Deepgram", "AssemblyAI"],
  "target_domain": "voice ai",
  "role_title": "Senior Voice AI Engineer"
}}

Payload:
{{
  "title": "Senior Voice AI Engineer",
  "target_companies": {{
    "mentioned_companies": ["Deepgram", "AssemblyAI"]
  }},
  "requirements": {{
    "domain": "voice ai"
  }}
}}

**Step 1**: JD mentions Deepgram, AssemblyAI; domain is voice ai; title is "Senior Voice AI Engineer"
**Step 2**: Parsed has companies ["Deepgram", "AssemblyAI"], domain "voice ai", title "Senior Voice AI Engineer" ✓
**Step 3**: Payload has companies ["Deepgram", "AssemblyAI"], domain "voice ai", title "Senior Voice AI Engineer" ✓
**Step 4**: No data loss detected
**Step 5**: PASS - All critical info preserved

---

## Example 2: FAIL (Companies lost, domain replaced)

JD: "Senior Voice AI Engineer... companies like Deepgram, AssemblyAI"

Parsed:
{{
  "mentioned_companies": ["Deepgram", "AssemblyAI"],
  "target_domain": "voice ai",
  "role_title": "Senior Voice AI Engineer"
}}

Payload:
{{
  "title": "Engineering Role",
  "target_companies": {{
    "mentioned_companies": []
  }},
  "requirements": {{
    "domain": "technology"
  }}
}}

**Step 1**: JD mentions Deepgram, AssemblyAI; domain is voice ai; title is "Senior Voice AI Engineer"
**Step 2**: Parsed has companies ["Deepgram", "AssemblyAI"], domain "voice ai", title "Senior Voice AI Engineer" ✓
**Step 3**: Payload has NO companies [], domain "technology" (default), title "Engineering Role" (default) ✗
**Step 4**: Data loss detected:
  - Companies: Lost ["Deepgram", "AssemblyAI"] → became []
  - Domain: Lost "voice ai" → became "technology" (default)
  - Title: Lost "Senior Voice AI Engineer" → became "Engineering Role" (default)
**Step 5**: FAIL - Critical data loss: companies, domain, and title were replaced with defaults

---

## Example 3: PASS (No companies mentioned - domain discovery mode)

JD: "CEO with voice AI experience" (no companies mentioned)

Parsed:
{{
  "mentioned_companies": [],
  "target_domain": "voice ai",
  "role_title": "CEO"
}}

Payload:
{{
  "title": "CEO",
  "target_companies": {{
    "mentioned_companies": []
  }},
  "requirements": {{
    "domain": "voice ai"
  }}
}}

**Step 1**: JD mentions NO companies; domain is voice ai; title is "CEO"
**Step 2**: Parsed has no companies [], domain "voice ai", title "CEO" ✓
**Step 3**: Payload has no companies [], domain "voice ai", title "CEO" ✓
**Step 4**: No data loss - empty companies list is correct (domain discovery will find companies via web search)
**Step 5**: PASS - Domain preserved for discovery; title correct; no companies to preserve

---

# YOUR VALIDATION TASK

Now validate this actual data transformation:

**JD Text (snippet):**
{jd_snippet}

**Parsed Requirements:**
{self._format_json(parsed_requirements)}

**Research Payload:**
{self._format_json(research_payload)}

Follow the 5-step Chain-of-Thought process above. Then respond in this exact format:

STEP 1: [Your analysis of JD text]
STEP 2: [Your analysis of parsed requirements]
STEP 3: [Your analysis of research payload]
STEP 4: [Data loss check - list any issues]
STEP 5: [Final verdict - PASS or FAIL]

VERDICT: PASS or FAIL
ISSUES: [List of issues if any, or "None"]
RECOMMENDATION: [How to fix if FAIL, or "No action needed" if PASS]
"""

        return prompt

    def _parse_validation_response(self, gpt_response: str) -> Dict[str, Any]:
        """
        Parse GPT-4o's CoT response into structured validation result.

        Args:
            gpt_response: Raw GPT-4o response text

        Returns:
            Structured validation result
        """
        # Extract verdict
        valid = "PASS" in gpt_response.upper() and "FAIL" not in gpt_response.upper()

        # Extract issues (lines starting with "- " after "ISSUES:")
        issues = []
        if "ISSUES:" in gpt_response:
            issues_section = gpt_response.split("ISSUES:")[1].split("RECOMMENDATION:")[0]
            issues = [
                line.strip("- ").strip()
                for line in issues_section.split("\n")
                if line.strip().startswith("-") and line.strip() != "- None"
            ]

        # Extract recommendation
        recommendation = "No action needed"
        if "RECOMMENDATION:" in gpt_response:
            rec_section = gpt_response.split("RECOMMENDATION:")[1].strip()
            recommendation = rec_section.split("\n")[0].strip()

        return {
            "valid": valid,
            "reasoning": gpt_response,  # Full CoT reasoning
            "issues": issues,
            "recommendation": recommendation
        }

    def _format_json(self, data: Dict[str, Any]) -> str:
        """
        Format dict as pretty JSON for prompt.

        Args:
            data: Dictionary to format

        Returns:
            Pretty-printed JSON string
        """
        import json
        return json.dumps(data, indent=2)
