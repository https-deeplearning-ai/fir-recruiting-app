"""
JD to CoreSignal Query Builder

Converts parsed JD requirements into Elasticsearch DSL queries for CoreSignal API.
Uses structured field mapping instead of blind AI conversion.
"""

from typing import Dict, List, Any, Optional
from jd_analyzer.utils.coresignal_taxonomies import (
    normalize_seniority,
    expand_location,
    infer_department,
    COMMON_SKILLS
)

class JDToQueryBuilder:
    """
    Builds CoreSignal Elasticsearch DSL queries from parsed JD requirements.

    Uses field-specific handlers to map JD Parser output to CoreSignal API parameters.
    """

    def __init__(self):
        """Initialize query builder."""
        pass

    def build_query(self, jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert JD requirements to CoreSignal Elasticsearch DSL query.

        Args:
            jd_requirements: Output from JDParser.parse()

        Returns:
            Elasticsearch DSL query dict ready for CoreSignal API
        """
        must_filters = []
        should_filters = []

        # CRITICAL: Always filter for currently employed candidates
        must_filters.append({"match": {"is_working": 1}})

        # 1. Role Title
        role_filters = self._handle_role_title(jd_requirements.get('role_title'))
        if role_filters:
            must_filters.append(role_filters)

        # 2. Seniority Level
        seniority_filter = self._handle_seniority(jd_requirements.get('seniority_level'))
        if seniority_filter:
            must_filters.append(seniority_filter)

        # 3. Technical Skills
        skills_filters = self._handle_skills(jd_requirements.get('technical_skills', []))
        if skills_filters:
            must_filters.append(skills_filters)

        # 4. Location
        location_filters = self._handle_location(jd_requirements.get('location'))
        if location_filters:
            must_filters.append(location_filters)

        # 5. Experience Years
        experience_filter = self._handle_experience_years(
            jd_requirements.get('experience_years', {})
        )
        if experience_filter:
            must_filters.append(experience_filter)

        # 6. Domain Expertise (nested query on past experience)
        domain_filters = self._handle_domain_expertise(
            jd_requirements.get('domain_expertise', [])
        )
        if domain_filters:
            should_filters.append(domain_filters)

        # 7. Must-Have Requirements (parse and route)
        must_have_filters = self._handle_must_have(
            jd_requirements.get('must_have', [])
        )
        if must_have_filters:
            must_filters.extend(must_have_filters)

        # Build final query
        query = {
            "query": {
                "bool": {
                    "must": must_filters
                }
            },
            "sort": ["_score"]
        }

        # Add should filters if any
        if should_filters:
            query["query"]["bool"]["should"] = should_filters
            query["query"]["bool"]["minimum_should_match"] = 1

        return query

    def _handle_role_title(self, role_title: Optional[str]) -> Optional[Dict]:
        """
        Map role title to active_experience_title and headline.

        Strategy: Wildcard search on both fields with OR logic.
        """
        if not role_title:
            return None

        title_lower = role_title.lower()

        return {
            "bool": {
                "should": [
                    {"wildcard": {"active_experience_title": f"*{title_lower}*"}},
                    {"wildcard": {"headline": f"*{title_lower}*"}}
                ],
                "minimum_should_match": 1
            }
        }

    def _handle_seniority(self, seniority_level: Optional[str]) -> Optional[Dict]:
        """
        Map seniority level to active_experience_management_level.

        Strategy: Exact term match using CoreSignal taxonomy.
        """
        if not seniority_level:
            return None

        normalized = normalize_seniority(seniority_level)
        if not normalized:
            return None

        return {"term": {"active_experience_management_level": normalized}}

    def _handle_skills(self, technical_skills: List[str]) -> Optional[Dict]:
        """
        Map technical skills to inferred_skills array and headline.

        Strategy: Term queries on skills array + wildcard on headline.
        """
        if not technical_skills:
            return None

        skill_filters = []

        for skill in technical_skills:
            skill_lower = skill.lower()

            # Term query on inferred_skills array
            skill_filters.append({"term": {"inferred_skills": skill}})

            # Fallback: wildcard on headline
            skill_filters.append({"wildcard": {"headline": f"*{skill_lower}*"}})

        return {
            "bool": {
                "should": skill_filters,
                "minimum_should_match": 1  # Match at least one skill
            }
        }

    def _handle_location(self, location: Optional[str]) -> Optional[Dict]:
        """
        Map location to location_full with smart expansion.

        Strategy: Expand common locations (Bay Area, NYC) to multiple wildcards.
        """
        if not location:
            return None

        expansions = expand_location(location)
        if not expansions:
            return None

        location_filters = []

        for pattern in expansions:
            location_filters.append({"wildcard": {"location_full": pattern}})

        # Also try exact match on city
        location_filters.append({"term": {"location_city": location}})

        return {
            "bool": {
                "should": location_filters,
                "minimum_should_match": 1
            }
        }

    def _handle_experience_years(self, experience_years: Dict[str, int]) -> Optional[Dict]:
        """
        Map experience years to total_experience_duration_months.

        Strategy: Range query (gte) on total duration.
        """
        minimum = experience_years.get('minimum')
        if not minimum:
            return None

        # Convert years to months
        months = minimum * 12

        return {"range": {"total_experience_duration_months": {"gte": months}}}

    def _handle_domain_expertise(self, domain_expertise: List[str]) -> Optional[Dict]:
        """
        Map domain expertise to nested query on experience.company_industry.

        Strategy: Nested query on past experience to find industry matches.
        """
        if not domain_expertise:
            return None

        industry_filters = []

        for domain in domain_expertise:
            industry_filters.append({
                "term": {"experience.company_industry": domain}
            })

        return {
            "nested": {
                "path": "experience",
                "query": {
                    "bool": {
                        "should": industry_filters,
                        "minimum_should_match": 1
                    }
                }
            }
        }

    def _handle_must_have(self, must_have: List[str]) -> List[Dict]:
        """
        Parse must-have requirements and route to appropriate handlers.

        Strategy: Extract keywords and map to specific fields.
        """
        filters = []

        for requirement in must_have:
            req_lower = requirement.lower()

            # Check for education keywords
            if any(keyword in req_lower for keyword in ["degree", "bachelor", "master", "phd", "education"]):
                # Add education filter (term query on education_degrees array)
                filters.append({
                    "bool": {
                        "should": [
                            {"wildcard": {"education_degrees": "*bachelor*"}},
                            {"wildcard": {"education_degrees": "*master*"}},
                            {"wildcard": {"education_degrees": "*phd*"}}
                        ],
                        "minimum_should_match": 1
                    }
                })

            # Check for startup/company stage keywords
            if any(keyword in req_lower for keyword in ["startup", "early stage", "series a", "series b"]):
                # Add nested query for small company experience
                filters.append({
                    "nested": {
                        "path": "experience",
                        "query": {
                            "range": {"experience.company_employees_count": {"lte": 500}}
                        }
                    }
                })

            # Check for leadership keywords
            if any(keyword in req_lower for keyword in ["leadership", "management", "team lead", "decision maker"]):
                filters.append({"term": {"is_decision_maker": 1}})

        return filters

    def explain_query(self, query: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of the query.

        Args:
            query: Elasticsearch DSL query

        Returns:
            Markdown-formatted explanation
        """
        explanation = "## CoreSignal Search Query Breakdown\n\n"

        must_filters = query.get("query", {}).get("bool", {}).get("must", [])

        explanation += "**Required Filters (AND logic):**\n\n"
        for i, filter_obj in enumerate(must_filters, 1):
            explanation += f"{i}. {self._explain_filter(filter_obj)}\n"

        should_filters = query.get("query", {}).get("bool", {}).get("should", [])
        if should_filters:
            explanation += "\n**Optional Filters (OR logic):**\n\n"
            for i, filter_obj in enumerate(should_filters, 1):
                explanation += f"{i}. {self._explain_filter(filter_obj)}\n"

        return explanation

    def _explain_filter(self, filter_obj: Dict) -> str:
        """Explain a single filter object."""
        if "match" in filter_obj:
            field = list(filter_obj["match"].keys())[0]
            value = filter_obj["match"][field]
            return f"Match `{field}` = {value}"

        elif "term" in filter_obj:
            field = list(filter_obj["term"].keys())[0]
            value = filter_obj["term"][field]
            return f"Exact match on `{field}`: '{value}'"

        elif "wildcard" in filter_obj:
            field = list(filter_obj["wildcard"].keys())[0]
            value = filter_obj["wildcard"][field]
            return f"Wildcard search on `{field}`: '{value}'"

        elif "range" in filter_obj:
            field = list(filter_obj["range"].keys())[0]
            conditions = filter_obj["range"][field]
            return f"Range on `{field}`: {conditions}"

        elif "bool" in filter_obj:
            should_count = len(filter_obj["bool"].get("should", []))
            must_count = len(filter_obj["bool"].get("must", []))
            return f"Complex boolean: {must_count} required, {should_count} optional"

        elif "nested" in filter_obj:
            path = filter_obj["nested"]["path"]
            return f"Nested query on `{path}` (past experience)"

        else:
            return "Custom filter"
