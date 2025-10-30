"""
CoreSignal API Taxonomies

Official enumerated values and mappings for CoreSignal Multi-source Employee API.
Source: CoreSignal Data Dictionary (docs/evidence/)
"""

# Management Levels (exact match required)
MANAGEMENT_LEVELS = [
    "C-Level",
    "Intern",
    "Senior",
    "Specialist",
    "Manager",
    "Mid-Level"
]

# Departments (standardized categories)
DEPARTMENTS = [
    "C-Suite",
    "Marketing",
    "Finance & Accounting",
    "Engineering and Technical",
    "Data Science",
    "Sales",
    "Operations",
    "Human Resources",
    "Product Management"
]

# Email Status (for validation)
EMAIL_STATUS = [
    "verified",
    "matched_email",
    "matched_pattern",
    "guessed_common_pattern"
]

# Seniority Level Mapping (JD Parser → CoreSignal)
SENIORITY_MAPPING = {
    "c-level": "C-Level",
    "executive": "C-Level",
    "ceo": "C-Level",
    "cto": "C-Level",
    "cfo": "C-Level",
    "vp": "C-Level",
    "vice president": "C-Level",
    "senior": "Senior",
    "staff": "Senior",
    "principal": "Senior",
    "lead": "Senior",
    "manager": "Manager",
    "mid-level": "Mid-Level",
    "mid level": "Mid-Level",
    "junior": "Mid-Level",
    "intern": "Intern",
    "internship": "Intern"
}

# Location Expansions (for smart geographic search)
LOCATION_EXPANSIONS = {
    "san francisco": ["*san francisco*", "*bay area*", "*palo alto*", "*mountain view*", "*sunnyvale*", "*menlo park*", "*redwood city*", "*san mateo*", "*san jose*", "*los altos*", "*san carlos*", "*cupertino*", "*oakland*", "*berkeley*", "*fremont*"],
    "bay area": ["*san francisco*", "*bay area*", "*palo alto*", "*mountain view*", "*sunnyvale*", "*menlo park*", "*redwood city*", "*san mateo*", "*san jose*", "*los altos*", "*san carlos*", "*cupertino*", "*oakland*", "*berkeley*", "*fremont*"],
    "seattle": ["*seattle*", "*bellevue*", "*redmond*", "*kirkland*"],
    "new york": ["*new york*", "*manhattan*", "*brooklyn*", "*nyc*"],
    "nyc": ["*new york*", "*manhattan*", "*brooklyn*", "*nyc*"],
    "boston": ["*boston*", "*cambridge*", "*somerville*"],
    "austin": ["*austin*", "*texas*"],
    "los angeles": ["*los angeles*", "*la*", "*santa monica*", "*pasadena*"],
    "chicago": ["*chicago*", "*illinois*"],
    "denver": ["*denver*", "*colorado*"],
    "miami": ["*miami*", "*florida*"],
    "remote": ["*remote*", "*united states*"]
}

# Department Keywords (for parsing JD text → department)
DEPARTMENT_KEYWORDS = {
    "Engineering and Technical": ["engineer", "engineering", "software", "developer", "technical", "infrastructure", "platform", "backend", "frontend", "full stack", "devops", "sre"],
    "Data Science": ["data", "ml", "machine learning", "ai", "artificial intelligence", "analytics", "data scientist", "research scientist"],
    "Product Management": ["product", "product manager", "pm", "product lead"],
    "Sales": ["sales", "account executive", "business development", "bd"],
    "Marketing": ["marketing", "growth", "content", "seo", "brand"],
    "Finance & Accounting": ["finance", "accounting", "financial", "controller", "fp&a"],
    "Operations": ["operations", "ops", "logistics", "supply chain"],
    "Human Resources": ["hr", "human resources", "recruiting", "recruiter", "talent"],
    "C-Suite": ["ceo", "cto", "cfo", "chief", "founder", "co-founder", "head of"]
}

# Common Technical Skills (for validation)
COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust", "Ruby",
    "React", "Node.js", "Django", "Flask", "Spring", "Rails",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "AI",
    "PyTorch", "TensorFlow", "scikit-learn",
    "Data Analysis", "Data Engineering", "ETL", "Spark", "Hadoop",
    "Product Management", "Agile", "Scrum",
    "Git", "CI/CD", "DevOps"
]

def normalize_seniority(jd_seniority: str) -> str:
    """
    Convert JD Parser seniority level to CoreSignal management_level.

    Args:
        jd_seniority: Seniority from JD Parser (e.g., "senior", "executive")

    Returns:
        CoreSignal management_level value or None if no match
    """
    if not jd_seniority:
        return None

    normalized = jd_seniority.lower().strip()
    return SENIORITY_MAPPING.get(normalized)

def expand_location(location: str) -> list:
    """
    Expand location to wildcard patterns for CoreSignal search.

    Args:
        location: Location string (e.g., "San Francisco", "Bay Area")

    Returns:
        List of wildcard patterns for location_full field
    """
    if not location:
        return []

    normalized = location.lower().strip()

    # Check for exact expansions
    for key, expansions in LOCATION_EXPANSIONS.items():
        if key in normalized:
            return expansions

    # Fallback: wrap location in wildcards
    return [f"*{location}*"]

def infer_department(role_title: str) -> str:
    """
    Infer CoreSignal department from role title.

    Args:
        role_title: Job title (e.g., "Senior ML Engineer")

    Returns:
        CoreSignal department value or None
    """
    if not role_title:
        return None

    normalized = role_title.lower().strip()

    # Check each department's keywords
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                return department

    return None
