"""
LLM Model Configurations

Centralized configuration for all LLM models used in query generation.
This ensures correct model names, parameters, and capabilities.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM model API calls."""
    model_name: str
    display_name: str
    provider: str  # "anthropic", "openai", "google"
    supports_temperature: bool
    supports_system_prompt: bool
    max_tokens: int
    reasoning: str
    fallback_model: Optional[str] = None


# Model configurations (updated with actual available models as of Jan 2025)
LLM_CONFIGS = {
    "claude": LLMConfig(
        model_name="claude-haiku-4-5",  # Claude Haiku 4.5 - latest, fastest, cheapest
        display_name="Claude Haiku 4.5",
        provider="anthropic",
        supports_temperature=True,
        supports_system_prompt=True,
        max_tokens=4096,
        reasoning="Claude Haiku 4.5: Sonnet 4-level performance at 1/3 cost, 2x faster. Best for structured tasks.",
        fallback_model="claude-sonnet-4-5-20250929"  # FIXED: Fallback to Sonnet 4.5 instead of old 3.5
    ),
    "openai": LLMConfig(
        model_name="gpt-4o",  # Latest GPT-4o (May 2024, still current)
        display_name="GPT-4o",
        provider="openai",
        supports_temperature=True,
        supports_system_prompt=True,
        max_tokens=4096,
        reasoning="GPT-4o: OpenAI's flagship multimodal model, fast and accurate",
        fallback_model="gpt-4-turbo"
    ),
    "google": LLMConfig(
        model_name="gemini-2.5-flash",  # Gemini 2.5 Flash (stable, Jan 2025)
        display_name="Gemini 2.5 Flash",
        provider="google",
        supports_temperature=True,
        supports_system_prompt=False,  # Gemini combines system+user in single prompt
        max_tokens=8192,
        reasoning="Gemini 2.5 Flash: Google's most efficient model with state-of-the-art performance",
        fallback_model="gemini-2.0-flash-exp"
    )
}


def get_config(provider: str) -> LLMConfig:
    """
    Get LLM configuration by provider name.

    Args:
        provider: One of "claude", "openai", "google"

    Returns:
        LLMConfig for the specified provider

    Raises:
        ValueError: If provider is not recognized
    """
    if provider not in LLM_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(LLM_CONFIGS.keys())}")
    return LLM_CONFIGS[provider]
