# CoreSignal Employee Search API - Complete Reference

**Source:** CoreSignal Multi-source Employee API Documentation
**Date:** 2025-10-29
**Purpose:** Reference for JD Analyzer → CoreSignal search integration

## API Endpoint

```
POST https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl
```

**Headers Required:**
- `accept: application/json`
- `apikey: {API_KEY}`
- `Content-Type: application/json`

## Query Structure: Elasticsearch DSL

```json
{
  "query": {
    "bool": {
      "must": [/* Required conditions */],
      "should": [/* Optional conditions */],
      "minimum_should_match": 1
    }
  },
  "sort": ["_score"]
}
```

## Complete Searchable Fields List

### **CRITICAL FIELDS FOR JD MATCHING**

| Category | Field Name | Type | Query Type | JD Mapping |
|----------|------------|------|------------|------------|
| **Current Role** | `headline` | String | wildcard | Role title + skills keyword search |
| **Current Role** | `active_experience_title` | String | wildcard | Direct job title match |
| **Current Role** | `active_experience_department` | String (enumerated) | term | Department from JD |
| **Current Role** | `active_experience_management_level` | String (enumerated) | term | Seniority level |
| **Working Status** | `is_working` | Number (0/1) | match | Always 1 (currently employed) |
| **Skills** | `inferred_skills` | Array[String] | term | Technical skills from JD |
| **Location** | `location_country` | String | term | Country-level filter |
| **Location** | `location_city` | String | term | City match |
| **Location** | `location_state` | String | term | State match |
| **Location** | `location_full` | String | wildcard | Flexible location search |
| **Experience** | `total_experience_duration_months` | Number | range (gte) | Minimum experience years * 12 |
| **Education** | `education_degrees` | Array[String] | term | Degree requirements |
| **Education** | `last_graduation_date` | String (date) | range | Graduation recency |
| **Decision Maker** | `is_decision_maker` | Number (0/1) | term | Leadership filter |

### **NESTED FIELDS (Experience History)**

Search through `experience` array for past roles:

```json
{
  "nested": {
    "path": "experience",
    "query": {
      "bool": {
        "must": [
          {"term": {"experience.company_industry": "Software Development"}},
          {"wildcard": {"experience.position_title": "*engineer*"}},
          {"match": {"experience.department": "Engineering"}}
        ]
      }
    }
  }
}
```

**Experience Fields:**
- `experience.position_title` (String) - Past job titles
- `experience.department` (String) - Department
- `experience.management_level` (String) - Seniority
- `experience.company_name` (String) - Employer
- `experience.company_industry` (String) - Industry
- `experience.description` (String) - Role description
- `experience.duration_months` (Number) - Role duration
- `experience.date_from_year`, `date_to_year` (Number) - Time range

### **COMPANY/FIRMOGRAPHIC FILTERS**

Filter by current employer characteristics:

| Field | Type | Use Case |
|-------|------|----------|
| `company_name` | String | Target specific companies |
| `company_industry` | String | Industry filter |
| `company_size_range` | String | Company stage proxy |
| `company_employees_count` | Number | Company size |
| `company_founded_year` | String (date) | Startup filter (>2015) |
| `company_hq_city`, `company_hq_country` | String | Company location |
| `company_is_b2b` | Number (0/1) | B2B vs B2C |

## ENUMERATED VALUES (Exact Match Required)

### Management Levels
```
"C-Level"
"Intern"
"Senior"
"Specialist"
"Manager"
"Mid-Level"
```

### Departments (Standardized Categories)
```
"C-Suite"
"Marketing"
"Finance & Accounting"
"Engineering and Technical"
"Data Science"
"Sales"
"Operations"
"Human Resources"
"Product Management"
...
```

### Email Status
```
"verified"
"matched_email"
"matched_pattern"
"guessed_common_pattern"
```

## JD PARSER → CORESIGNAL FIELD MAPPING

| JD Parser Field | CoreSignal Field(s) | Query Strategy |
|----------------|---------------------|----------------|
| `role_title` | `active_experience_title`, `headline` | Wildcard OR on both |
| `seniority_level` | `active_experience_management_level` | Map to CoreSignal taxonomy |
| `technical_skills` | `inferred_skills`, `headline` | term on skills array, wildcard on headline |
| `domain_expertise` | `experience.company_industry` (nested) | Multiple industry terms |
| `experience_years.minimum` | `total_experience_duration_months` | range gte (years * 12) |
| `location` | `location_city`, `location_state`, `location_full` | Flexible with wildcards |
| `must_have` | Multiple fields | Parse into specific filters |
| `education` requirements | `education_degrees`, `education.degree` | term match or nested |
| `company_stage` | `company_founded_year`, `company_employees_count` | Proxy filters (not direct) |

## EXAMPLE QUERIES

### Example 1: Senior AI Engineer in San Francisco

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"is_working": 1}},
        {
          "bool": {
            "should": [
              {"wildcard": {"active_experience_title": "*engineer*"}},
              {"wildcard": {"headline": "*engineer*"}}
            ],
            "minimum_should_match": 1
          }
        },
        {
          "bool": {
            "should": [
              {"term": {"inferred_skills": "AI"}},
              {"term": {"inferred_skills": "Machine Learning"}},
              {"wildcard": {"headline": "*ai*"}},
              {"wildcard": {"headline": "*machine learning*"}}
            ],
            "minimum_should_match": 1
          }
        },
        {"term": {"active_experience_management_level": "Senior"}},
        {
          "bool": {
            "should": [
              {"wildcard": {"location_full": "*san francisco*"}},
              {"wildcard": {"location_full": "*bay area*"}},
              {"term": {"location_city": "San Francisco"}}
            ],
            "minimum_should_match": 1
          }
        }
      ]
    }
  },
  "sort": ["_score"]
}
```

### Example 2: C-Level with Startup Experience

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"is_working": 1}},
        {"term": {"active_experience_management_level": "C-Level"}},
        {"range": {"total_experience_duration_months": {"gte": 120}}},
        {
          "nested": {
            "path": "experience",
            "query": {
              "bool": {
                "must": [
                  {"range": {"experience.company_employees_count": {"lte": 500}}}
                ]
              }
            }
          }
        }
      ]
    }
  }
}
```

## KEY LIMITATIONS

1. **No fuzzy matching** on enumerated fields (management_level, department)
2. **Nested queries are expensive** - use sparingly
3. **Wildcard queries are slow** - combine with more specific filters
4. **Company stage** - not directly filterable, must use proxy fields
5. **Skills array** may be incomplete - use headline as fallback
6. **Industry taxonomy** - must match exact CoreSignal values

## QUERY OPTIMIZATION STRATEGIES

1. **Always include** `is_working: 1` as first filter
2. **Use term queries** for exact matches (faster than wildcards)
3. **Limit nested queries** to essential filters only
4. **Combine filters** with AND logic to narrow results early
5. **Use should + minimum_should_match** for OR logic within categories
6. **Wildcard placement**: `*keyword*` for substring, `keyword*` for prefix (faster)

## MISSING FROM CURRENT IMPLEMENTATION

### Fields Not Yet Used:
- `is_decision_maker` - Leadership filter
- `education` fields - Degree/university requirements
- `company_is_b2b` - B2B vs B2C filter
- `company_founded_year` - Startup stage proxy
- `certifications` - Professional credentials
- `languages` - Language requirements
- `projected_total_salary_median` - Compensation level

### Taxonomies Needed:
- Complete list of valid `active_experience_department` values
- Complete list of valid `company_industry` values
- Location region mappings beyond hardcoded metros

## NEXT STEPS FOR IMPLEMENTATION

1. **Define VALID_INPUT_VALUES** with complete taxonomies
2. **Add education filtering** logic
3. **Implement department search** (currently extracted but unused)
4. **Add company stage proxy** filters (founded_year, employee_count)
5. **Optimize query builder** with field-specific strategies
6. **Test query performance** with different field combinations
