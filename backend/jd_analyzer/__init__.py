"""
JD Analyzer Module

Extracts weighted requirements from job descriptions to help configure
candidate assessment criteria.

This module provides:
- JD requirement extraction (must-have, nice-to-have, implicit criteria)
- Automatic weight generation for assessment rubrics
- CoreSignal search query generation from JD text
- Shortlist reverse-engineering (discover implicit criteria from existing candidates)
"""

from .jd_parser import JDParser
from .weight_generator import WeightGenerator
from .shortlist_analyzer import ShortlistAnalyzer
from .query_builder import JDToQueryBuilder
from .llm_query_generator import MultiLLMQueryGenerator
from .models import JDRequirements, ExperienceYears, LLMQueryResult, LLMComparisonResult
from .coresignal_taxonomies import (
    normalize_seniority,
    expand_location,
    infer_department
)

__all__ = [
    'JDParser',
    'WeightGenerator',
    'ShortlistAnalyzer',
    'JDToQueryBuilder',
    'MultiLLMQueryGenerator',
    'JDRequirements',
    'ExperienceYears',
    'LLMQueryResult',
    'LLMComparisonResult',
    'normalize_seniority',
    'expand_location',
    'infer_department'
]
