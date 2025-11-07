"""
Weight Generator

Automatically generates weighted requirements for candidate assessment
based on job description analysis.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from anthropic import Anthropic

class WeightGenerator:
    """
    Generates weighted assessment criteria from job requirements.

    Converts JD requirements into a 5-requirement rubric with percentage weights
    that sum to 100% for use in candidate assessment.
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Weight Generator with Anthropic client.

        Args:
            anthropic_api_key: Optional API key, defaults to env var
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Note: Sonnet uses dated version, unlike Haiku

    def generate_weighted_requirements(
        self,
        jd_requirements: Dict[str, Any],
        num_requirements: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate weighted requirements for assessment.

        Args:
            jd_requirements: Parsed JD requirements from JDParser
            num_requirements: Number of custom requirements (1-5)

        Returns:
            List of weighted requirements:
            [
                {
                    "requirement": "Voice AI / Real-time Systems Expertise",
                    "weight": 35,
                    "description": "Deep experience with...",
                    "scoring_criteria": "1-10 scale based on..."
                },
                ...
            ]
        """

        system_prompt = f"""You are an expert at designing candidate assessment rubrics.

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
  {{
    "requirement": "Brief requirement name (4-6 words)",
    "weight": 35,
    "description": "Detailed description of what this requirement means and why it matters",
    "scoring_criteria": "How to score 1-10: 10 = [best case], 5 = [acceptable], 1 = [insufficient]"
  }},
  ...
]

Ensure weights sum to at most 95% (leaving 5%+ for General Fit)."""

        user_prompt = f"""Job Requirements to Convert to Weighted Criteria:

**Role:** {jd_requirements.get('role_title', 'Unknown')}
**Seniority:** {jd_requirements.get('seniority_level', 'Unknown')}

**Must-Have Requirements:**
{json.dumps(jd_requirements.get('must_have', []), indent=2)}

**Nice-to-Have Requirements:**
{json.dumps(jd_requirements.get('nice_to_have', []), indent=2)}

**Technical Skills:**
{json.dumps(jd_requirements.get('technical_skills', []), indent=2)}

**Domain Expertise:**
{json.dumps(jd_requirements.get('domain_expertise', []), indent=2)}

**Experience Level:**
{json.dumps(jd_requirements.get('experience_years', {}), indent=2)}

**Implicit Criteria:**
{json.dumps(jd_requirements.get('implicit_criteria', {}), indent=2)}

Generate {num_requirements} weighted assessment criteria that best predict success in this role."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text

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

            weighted_reqs = json.loads(json_str)

            # Validate weights sum
            total_weight = sum(req.get('weight', 0) for req in weighted_reqs)
            if total_weight > 100:
                # Normalize to 95%
                scale_factor = 95.0 / total_weight
                for req in weighted_reqs:
                    req['weight'] = round(req['weight'] * scale_factor)

            return weighted_reqs

        except Exception as e:
            import traceback
            print(f"❌ Error generating weights: {e}")
            print(f"❌ Full traceback:")
            traceback.print_exc()
            print(f"❌ Returning default weights as fallback")
            return self._get_default_weights(num_requirements)

    def _get_default_weights(self, num_requirements: int) -> List[Dict[str, Any]]:
        """Return default weights if generation fails"""
        base_weight = 90 // num_requirements

        defaults = []
        for i in range(num_requirements):
            defaults.append({
                "requirement": f"Requirement {i+1}",
                "weight": base_weight,
                "description": "Custom requirement (please edit)",
                "scoring_criteria": "Score 1-10 based on candidate qualifications"
            })

        return defaults

    def adjust_weights(
        self,
        requirements: List[Dict[str, Any]],
        adjustments: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Adjust weights for specific requirements.

        Args:
            requirements: Current weighted requirements
            adjustments: Dict of {requirement_name: new_weight}

        Returns:
            Updated requirements with adjusted weights
        """
        # Create a copy
        updated = [req.copy() for req in requirements]

        # Apply adjustments
        for req in updated:
            if req['requirement'] in adjustments:
                req['weight'] = adjustments[req['requirement']]

        # Validate total doesn't exceed 95%
        total_weight = sum(req['weight'] for req in updated)
        if total_weight > 95:
            raise ValueError(f"Total weight ({total_weight}%) exceeds 95%. Reduce weights to leave room for General Fit.")

        return updated

    def explain_weights(self, requirements: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable explanation of weight allocation.

        Args:
            requirements: Weighted requirements

        Returns:
            Markdown-formatted explanation
        """
        total_custom = sum(req['weight'] for req in requirements)
        general_fit = 100 - total_custom

        explanation = "## Assessment Criteria Weights\n\n"

        for i, req in enumerate(requirements, 1):
            explanation += f"**{i}. {req['requirement']} ({req['weight']}%)**\n"
            explanation += f"- {req['description']}\n"
            explanation += f"- Scoring: {req['scoring_criteria']}\n\n"

        explanation += f"**General Fit ({general_fit}%)**\n"
        explanation += "- Overall alignment with role responsibilities\n"
        explanation += "- Cultural fit and communication skills\n"
        explanation += "- Career trajectory and growth potential\n\n"

        explanation += f"**Total: 100%**\n"

        return explanation
