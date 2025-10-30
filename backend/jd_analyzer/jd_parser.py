"""
Job Description Parser

Extracts structured requirements from raw JD text using Claude AI.
"""

import os
import json
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from pydantic import ValidationError
from .models import JDRequirements
from .debug_logger import debug_log

class JDParser:
    """
    Parses job descriptions to extract structured requirements.

    Extracts:
    - Must-have requirements (hard filters)
    - Nice-to-have requirements (soft preferences)
    - Technical skills
    - Experience level
    - Location preferences
    - Domain expertise
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize JD Parser with Anthropic client.

        Args:
            anthropic_api_key: Optional API key, defaults to env var
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def parse(self, jd_text: str) -> JDRequirements:
        """
        Parse job description and extract structured requirements.

        Args:
            jd_text: Raw job description text

        Returns:
            JDRequirements Pydantic model with validated fields:
            - role_title: Job title
            - seniority_level: junior/mid/senior/staff/principal/etc
            - must_have: Required qualifications
            - nice_to_have: Preferred qualifications
            - technical_skills: Technologies, frameworks, languages
            - domain_expertise: Industry/domain knowledge
            - experience_years: ExperienceYears model with minimum/preferred
            - location: Location requirement or 'Remote'
            - company_stage: startup/growth/enterprise
            - implicit_criteria: Inferred requirements from context
        """

        system_prompt = """You are an expert at analyzing job descriptions and extracting structured requirements.

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

Be specific and extract as much detail as possible."""

        # LOG POINT 1: Before Claude API call
        debug_log.jd_parse("Parsing JD text", jd_text=jd_text)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": jd_text}]
            )

            response_text = response.content[0].text

            # LOG POINT 2: After Claude response
            debug_log.llm_response("Claude Sonnet 4.5", response=response_text)

            # Parse JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            # Parse to dict first, then validate with Pydantic
            parsed_data = json.loads(json_str)

            # LOG POINT 3: After JSON parsing
            jd_requirements = JDRequirements.from_dict(parsed_data)
            debug_log.jd_parse("Parse successful", requirements=parsed_data, success=True)

            # Use JDRequirements.from_dict() to handle edge cases
            return jd_requirements

        except ValidationError as e:
            # LOG POINT 4a: Validation error
            debug_log.error("Pydantic validation error", exception=e,
                          context={"model": self.model, "step": "validation"})
            print(f"Pydantic validation error parsing JD: {e}")
            return self._get_empty_structure()
        except Exception as e:
            # LOG POINT 4b: General error
            debug_log.error("Error parsing JD", exception=e,
                          context={"model": self.model, "step": "parsing"},
                          raw_data=response_text if 'response_text' in locals() else None)
            print(f"Error parsing JD: {e}")
            return self._get_empty_structure()

    def _get_empty_structure(self) -> JDRequirements:
        """Return empty Pydantic model for error cases"""
        return JDRequirements(
            role_title="",
            seniority_level="unknown",
            must_have=[],
            nice_to_have=[],
            technical_skills=[],
            domain_expertise=[],
            experience_years={"minimum": 0, "preferred": 0},
            location="",
            company_stage="unknown",
            implicit_criteria={}
        )

    def extract_keywords(self, jd_text: str) -> List[str]:
        """
        Extract key terms and keywords from JD for search queries.

        Args:
            jd_text: Raw job description text

        Returns:
            List of keywords ranked by importance
        """
        system_prompt = """Extract the top 20 most important keywords from this job description for candidate search.

Focus on:
- Technical skills (e.g., "Python", "React", "Machine Learning")
- Domain expertise (e.g., "Voice AI", "Real-time systems", "LLMs")
- Role-specific terms (e.g., "Founder", "CTO", "Staff Engineer")
- Industry terms (e.g., "SaaS", "Enterprise", "Developer tools")

Return as a JSON array ranked by importance:
["keyword1", "keyword2", ...]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": jd_text}]
            )

            response_text = response.content[0].text

            # Parse JSON array
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
