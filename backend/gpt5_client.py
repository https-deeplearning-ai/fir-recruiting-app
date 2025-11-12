import os
import json
from typing import List, Dict, Any, Optional
import asyncio
import openai
import httpx


class GPT5Client:
    """
    OpenAI GPT-5 client with automatic model detection and fallback.

    Note: As of October 2025, GPT-5 family includes:
    - gpt-5: Full model with automatic reasoning routing
    - gpt-5-mini: Fast, efficient for screening
    - gpt-5-nano: Ultra-fast for simple tasks
    - gpt-5-pro: Enhanced reasoning for complex analysis

    If GPT-5 is not available, falls back to GPT-4o or GPT-4 Turbo.
    """

    def __init__(self):
        """Initialize and detect available models."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.async_client = None
        self.available_models = []
        self.models_detected = False
        self.init_error = None

        if not self.api_key:
            self.init_error = "OPENAI_API_KEY environment variable not set"
            print(f"Warning: {self.init_error}")
            print("Company research will fallback to Claude Haiku 4.5")
            return

        try:
            # Use custom httpx client to bypass Render's proxy environment variables
            # Render sets HTTP_PROXY/HTTPS_PROXY which break OpenAI SDK connections
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
                trust_env=False  # Ignore HTTP_PROXY, HTTPS_PROXY, ALL_PROXY, NO_PROXY
            )

            async_http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                trust_env=False
            )

            self.client = openai.OpenAI(
                api_key=self.api_key,
                http_client=http_client
            )
            self.async_client = openai.AsyncOpenAI(
                api_key=self.api_key,
                http_client=async_http_client
            )
            print("✓ OpenAI client initialized successfully (trust_env=False)")

        except Exception as e:
            self.init_error = str(e)
            print(f"Warning: Could not initialize OpenAI client: {e}")
            print("Company research will fallback to Claude Haiku 4.5")
            import traceback
            traceback.print_exc()
            self.client = None
            self.async_client = None

    async def detect_available_models(self):
        """Test which GPT-5 models are available."""
        if self.models_detected:
            return

        test_models = [
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5-pro",
            "gpt-4o",  # Fallback
            "gpt-4-turbo",  # Fallback
            "gpt-4"  # Final fallback
        ]

        for model in test_models:
            try:
                # Try a minimal completion
                await self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                self.available_models.append(model)
                print(f"✓ Model available: {model}")
            except Exception as e:
                print(f"✗ Model unavailable: {model}")
                continue

        self.models_detected = True
        print(f"Available models: {self.available_models}")

    def get_screening_model(self) -> str:
        """Get best available model for batch screening."""
        preferences = ["gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4-turbo", "gpt-4"]

        for model in preferences:
            if model in self.available_models:
                return model

        # Default fallback if detection hasn't run yet
        return "gpt-4o"

    def get_research_model(self) -> str:
        """Get best available model for deep research."""
        preferences = ["gpt-5", "gpt-5-pro", "gpt-4o", "gpt-4-turbo", "gpt-4"]

        for model in preferences:
            if model in self.available_models:
                return model

        # Default fallback if detection hasn't run yet
        return "gpt-4o"

    async def batch_screen(
        self,
        companies: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[float]:
        """
        Batch screening with optimal model.
        Returns relevance scores for each company.
        """
        if not self.async_client:
            error_msg = "OpenAI client not initialized"
            if self.init_error:
                error_msg += f": {self.init_error}"
            else:
                error_msg += " - check OPENAI_API_KEY environment variable"
            raise ValueError(error_msg)

        # Ensure models are detected
        if not self.models_detected:
            await self.detect_available_models()

        model = self.get_screening_model()

        prompt = self._build_screening_prompt(companies, context)

        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # Parse scores from response
            result = json.loads(response.choices[0].message.content)

            return result.get("scores", [5.0] * len(companies))
        except Exception as e:
            print(f"Batch screening error: {e}")
            # Return default scores on error
            return [5.0] * len(companies)

    async def deep_research(
        self,
        company_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep research with best available model.
        Returns comprehensive analysis.
        """
        if not self.async_client:
            error_msg = "OpenAI client not initialized"
            if self.init_error:
                error_msg += f": {self.init_error}"
            else:
                error_msg += " - check OPENAI_API_KEY environment variable"
            raise ValueError(error_msg)

        # Ensure models are detected
        if not self.models_detected:
            await self.detect_available_models()

        model = self.get_research_model()

        # For GPT-5, we can use the verbosity parameter
        is_gpt5 = model.startswith("gpt-5")

        prompt = self._build_research_prompt(company_data, context)

        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        # Add GPT-5 specific parameters if available
        if is_gpt5:
            # Note: verbosity parameter may not be available yet
            # Will be silently ignored if not supported
            kwargs["extra_body"] = {"verbosity": "high"}

        try:
            response = await self.async_client.chat.completions.create(**kwargs)

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Deep research error: {e}")
            # Return fallback structure
            return {
                "relevance_score": 5.0,
                "category": "talent_pool",
                "reasoning": f"Error during analysis: {str(e)[:100]}",
                "talent_assessment": {},
                "poaching_strategy": {},
                "specific_targets": []
            }

    def _build_screening_prompt(
        self,
        companies: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for batch screening with enriched company data."""
        return f"""You are evaluating companies for recruiting candidates.

Job Context:
- Role: {context.get('title', 'Unknown')}
- Target Domain: {context.get('target_domain', 'Unknown')}
- Company Stage: {context.get('company_stage', 'Unknown')}
- Key Skills: {', '.join(context.get('key_skills', []))}
- Industries: {', '.join(context.get('industries', []))}

Rate each company's relevance (1-10) for sourcing candidates.

SCORING CRITERIA:
- Industry alignment: Does company industry match job requirements?
- Description fit: Does what the company does align with job domain?
- Company stage/culture fit: Is this the right size and stage?
- Tech stack/domain overlap: Likely to have candidates with relevant skills?

Use ALL available fields to make informed decisions. Companies with more context should get more accurate scores.

Companies to evaluate (with all available data):
{json.dumps([{
    'name': c.get('name'),
    'description': c.get('description', 'N/A'),
    'industry': c.get('industry', 'N/A'),
    'employee_count': c.get('employee_count', 'N/A'),
    'size_range': c.get('size_range', 'N/A'),
    'employee_count_hint': c.get('employee_count_hint', 'N/A'),
    'founded': c.get('founded', 'N/A'),
    'location': c.get('location', 'N/A'),
    'website': c.get('website', 'N/A')
} for c in companies], indent=2)}

Return JSON with scores array (one score per company, in same order):
{{"scores": [7.5, 8.2, 5.1, ...]}}

IMPORTANT: Base scores on ACTUAL company data (description, industry), not just name guessing.
"""

    def _build_research_prompt(
        self,
        company_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for competitive intelligence analysis."""
        return f"""Perform competitive similarity analysis for market intelligence.

TARGET DOMAIN/MARKET:
{json.dumps(context, indent=2)}

CANDIDATE COMPANY:
{json.dumps(company_data, indent=2)}

SCORING RUBRIC (1-10):
• 9-10: DIRECT COMPETITOR - Same product category, same target market, clear competitive overlap
• 7-8: ADJACENT PLAYER - Related product with overlapping use cases, could pivot to compete
• 5-6: SAME CATEGORY - Broad category match but different specific focus
• 3-4: TANGENTIAL - Uses similar tech but different application or market
• 1-2: NOT RELEVANT - Different industry entirely, no competitive overlap

Provide comprehensive analysis as JSON:

{{
  "relevance_score": 8.5,
  "category": "direct_competitor|adjacent_company|same_category|tangential",
  "reasoning": "Detailed explanation of competitive overlap, focusing on:
   - Product/service similarity
   - Target market overlap
   - Competitive positioning
   - Technology stack alignment",

  "competitive_positioning": {{
    "market_overlap": "high|medium|low",
    "product_similarity": "Detailed comparison of products/services",
    "differentiation": "Key differences in positioning and strategy",
    "competitive_advantages": ["List their key strengths"],
    "competitive_weaknesses": ["List potential vulnerabilities"]
  }},

  "market_intelligence": {{
    "target_customers": "Description of customer segments they serve",
    "unique_value_prop": "What makes them different from others",
    "stage_maturity": "early|growth|mature",
    "market_position": "leader|challenger|niche_player",
    "pricing_strategy": "Description if known"
  }},

  "strategic_insights": {{
    "partnership_potential": "Could they be a partner vs competitor?",
    "acquisition_target": "Are they potential M&A target?",
    "technology_moat": "Description of technical advantages"
  }}
}}

IMPORTANT: This is competitive intelligence, NOT recruiting. Do not include hiring/talent/poaching fields.

Return complete JSON response."""
