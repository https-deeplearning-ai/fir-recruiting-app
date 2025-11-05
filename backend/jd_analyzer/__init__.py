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

from jd_analyzer.core.jd_parser import JDParser
from jd_analyzer.core.weight_generator import WeightGenerator
from jd_analyzer.core.shortlist_analyzer import ShortlistAnalyzer
from jd_analyzer.query.query_builder import JDToQueryBuilder
from jd_analyzer.query.llm_query_generator import MultiLLMQueryGenerator
from jd_analyzer.core.models import JDRequirements, ExperienceYears, LLMQueryResult, LLMComparisonResult
from jd_analyzer.utils.coresignal_taxonomies import (
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
