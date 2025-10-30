"""
Pydantic Models for JD Analyzer

Type-safe data models for job description requirements and LLM responses.
Prevents "'list' object has no attribute 'get'" errors by enforcing structure.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ExperienceYears(BaseModel):
    """Experience years requirement with min/preferred values."""
    minimum: int = Field(default=0, ge=0, description="Minimum years of experience required")
    preferred: Optional[int] = Field(default=None, ge=0, description="Preferred years of experience")

    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow additional fields from LLM responses


class JDRequirements(BaseModel):
    """
    Structured job description requirements.

    Parsed from raw JD text by JDParser. Ensures all fields have safe defaults.
    """
    role_title: str = Field(default="Not specified", description="Job title")
    seniority_level: str = Field(default="Not specified", description="Seniority: junior/mid/senior/staff/principal/etc")
    must_have: List[str] = Field(default_factory=list, description="Required qualifications (hard filters)")
    nice_to_have: List[str] = Field(default_factory=list, description="Preferred qualifications (soft preferences)")
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills (languages, frameworks, tools)")
    domain_expertise: List[str] = Field(default_factory=list, description="Industry/domain knowledge required")
    experience_years: ExperienceYears = Field(default_factory=ExperienceYears, description="Years of experience")
    location: str = Field(default="Not specified", description="Location requirement or 'Remote'")
    company_stage: Optional[str] = Field(default=None, description="Company stage: startup/growth/enterprise/etc")
    implicit_criteria: Dict[str, Any] = Field(default_factory=dict, description="Inferred requirements from context")

    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow additional fields from LLM responses

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JDRequirements":
        """
        Create JDRequirements from dict with validation.

        Handles common parsing issues:
        - experience_years as dict, list, or int
        - Missing fields (uses defaults)
        - Extra fields (ignored)

        Args:
            data: Dictionary from JD parser or API

        Returns:
            Validated JDRequirements instance

        Raises:
            ValidationError: If data is severely malformed
        """
        # Handle experience_years special cases
        if "experience_years" in data:
            exp_years = data["experience_years"]

            # Case 1: Already a dict (ideal)
            if isinstance(exp_years, dict):
                pass  # Use as-is

            # Case 2: Integer (just minimum)
            elif isinstance(exp_years, int):
                data["experience_years"] = {"minimum": exp_years}

            # Case 3: List [min, preferred]
            elif isinstance(exp_years, list) and len(exp_years) > 0:
                data["experience_years"] = {
                    "minimum": exp_years[0] if len(exp_years) > 0 else 0,
                    "preferred": exp_years[1] if len(exp_years) > 1 else None
                }

            # Case 4: Invalid/empty - use default
            else:
                data["experience_years"] = {}

        return cls(**data)


class LLMQueryResult(BaseModel):
    """Result from a single LLM query generation."""
    model: str = Field(description="LLM model name/display name")
    query: Optional[Dict[str, Any]] = Field(default=None, description="Generated CoreSignal Elasticsearch DSL query")
    reasoning: Optional[str] = Field(default=None, description="Explanation of query generation strategy")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")

    class Config:
        """Pydantic config."""
        extra = "allow"


class LLMComparisonResult(BaseModel):
    """Result from comparing multiple LLM query generations."""
    success: bool = Field(description="Whether comparison completed successfully")
    comparisons: List[LLMQueryResult] = Field(description="Results from each LLM")
    error: Optional[str] = Field(default=None, description="Overall error if comparison failed")

    class Config:
        """Pydantic config."""
        extra = "allow"
