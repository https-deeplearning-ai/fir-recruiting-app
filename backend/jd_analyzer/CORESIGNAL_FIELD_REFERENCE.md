# CoreSignal employee_multi_source API - Complete Field Reference

**Purpose:** Reference documentation for LLM query generation and developer use
**Last Updated:** 2025-10-30
**API Endpoint:** `https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview`

---

## QUICK REFERENCE: Field Priority Order

Based on JD Analyzer requirements, fields should be used in this priority order:

1. **COMPANY & INDUSTRY** (Most Important) - Target companies and verticals
2. **LOCATION** - Geographic constraints
3. **ROLE & TITLE** - Functional match
4. **FUNDING** - Growth stage signals
5. **MANAGEMENT LEVEL** - Seniority matching
6. **SKILLS & EXPERIENCE** - Technical requirements

---

## PRIORITY 1: COMPANY & INDUSTRY FIELDS

### Core Company Fields
| Field | Type | Query | Coverage | Use Case |
|-------|------|-------|----------|----------|
| `company_name` | String | wildcard | 100% | **PRIMARY**: Target specific companies or patterns (e.g., "*google*", "*startup*") |
| `company_industry` | String | term | 96% | **PRIMARY**: Industry vertical exact match |
| `company_type` | String | term | 96% | Organization structure (Public Company, Privately Held, Non-Profit) |
| `company_size_range` | String | term | 96% | Employee count buckets |
| `company_employees_count` | Integer | range | Variable | Exact headcount for precise sizing |
| `company_founded_year` | String (YYYY) | range | 74% | **Startup proxy**: founded > 2020 = recent startup |
| `company_is_b2b` | Integer (0/1) | term | Available | B2B vs B2C distinction |

### Funding & Growth Fields
| Field | Type | Query | Coverage | Use Case |
|-------|------|-------|----------|----------|
| `company_last_funding_round_date` | String (date) | range | 63% | Recent funding signal (date only, no amount) |
| `company_employees_count_change_yearly_percentage` | Number (double) | range | Variable | **Growth signal**: >20% = high growth |
| `company_last_funding_round_amount_raised` | Integer (long) | ❌ **BROKEN** | 0% | **NEVER USE** - Always NULL |

### Company Contact/Social Fields
| Field | Type | Query | Coverage | Notes |
|-------|------|-------|----------|-------|
| `company_website` | String | term | 93% | Company domain |
| `company_linkedin_url` | String | term | 93% | LinkedIn company page |
| `company_followers_count` | Integer | range | Variable | LinkedIn followers (influence proxy) |
| `company_facebook_url` | Array[String] | term | Variable | Facebook presence |
| `company_twitter_url` | Array[String] | term | Variable | Twitter/X presence |

### Company HQ Location Fields
| Field | Type | Query | Coverage | Notes |
|-------|------|-------|----------|-------|
| `company_hq_country` | String | term | 96% | HQ country |
| `company_hq_city` | String | term | Variable | HQ city |
| `company_hq_state` | String | term | Variable | HQ state |
| `company_hq_full_address` | String | wildcard | 96% | Full address string |
| `company_hq_regions` | Array[String] | term | 96% | Geographic regions (e.g., ["Americas", "Northern America"]) |

**Example Query - Company Priority:**
```json
{
  "bool": {
    "should": [
      {"wildcard": {"company_name": "*google*"}},
      {"wildcard": {"company_name": "*meta*"}},
      {"wildcard": {"company_name": "*amazon*"}},
      {"term": {"company_industry": "Software Development"}},
      {"range": {"company_founded_year": {"gte": "2020"}}},
      {"range": {"company_employees_count": {"gte": 10, "lte": 500}}}
    ],
    "minimum_should_match": 2
  }
}
```

---

## PRIORITY 2: LOCATION FIELDS

| Field | Type | Query | Coverage | Use Case |
|-------|------|-------|----------|----------|
| `location_full` | String | wildcard | 100% | **PREFERRED**: Flexible location search (e.g., "*san francisco*", "*bay area*", "*remote*") |
| `location_country` | String | term | 100% | Country exact match (e.g., "United States") |
| `location_city` | String | term | Variable | City exact match (e.g., "San Francisco") |
| `location_state` | String | term | Variable | State exact match (e.g., "California") |
| `location_regions` | Array[String] | term | Variable | Geographic regions (e.g., ["Americas"]) |

**Location Mapping Strategy:**
- "Bay Area" → `location_full: "*san francisco*" OR "*bay area*" OR "*palo alto*" OR "*mountain view*"`
- "Remote" → `location_full: "*remote*"`
- "US Only" → `location_country: "United States"`

**Example Query - Location Priority:**
```json
{
  "bool": {
    "should": [
      {"wildcard": {"location_full": "*san francisco*"}},
      {"wildcard": {"location_full": "*bay area*"}},
      {"wildcard": {"location_full": "*silicon valley*"}},
      {"term": {"location_city": "San Francisco"}},
      {"term": {"location_state": "California"}},
      {"term": {"location_country": "United States"}}
    ],
    "minimum_should_match": 1
  }
}
```

---

## PRIORITY 3: ROLE & TITLE FIELDS

| Field | Type | Query | Coverage | Use Case |
|-------|------|-------|----------|----------|
| `active_experience_title` | String | wildcard | 100% | **PRIMARY**: Current job title (e.g., "*engineer*", "*senior*software*") |
| `active_experience_department` | String (enum) | term | Variable | Department classification |
| `headline` | String | wildcard | 100% | Profile headline for keyword matching (user-set, may be stale) |
| `generated_headline` | String | wildcard | Variable | Auto-generated headline (FRESH, auto-updates) |
| `active_experience_description` | String | wildcard | Variable | Current role description (rich for keywords) |

**Department Enum Values:**
```
"C-Suite"
"Engineering and Technical"
"Data Science"
"Product Management"
"Marketing"
"Sales"
"Finance & Accounting"
"Operations"
"Human Resources"
"Customer Service"
... (more available)
```

**Example Query - Role Priority:**
```json
{
  "bool": {
    "should": [
      {"wildcard": {"active_experience_title": "*engineer*"}},
      {"wildcard": {"active_experience_title": "*senior*"}},
      {"wildcard": {"active_experience_title": "*staff*"}},
      {"term": {"active_experience_department": "Engineering and Technical"}},
      {"wildcard": {"headline": "*software*engineer*"}},
      {"wildcard": {"headline": "*backend*"}}
    ],
    "minimum_should_match": 2
  }
}
```

---

## PRIORITY 4: FUNDING FIELDS

⚠️ **Limited Data Quality** - Use with caution

| Field | Type | Query | Coverage | Notes |
|-------|------|-------|----------|-------|
| `company_last_funding_round_date` | String (date) | range | 63% | Funding date (no amount available) |
| `company_founded_year` | String (YYYY) | range | 74% | **PREFERRED**: Use as stage proxy |
| `company_last_funding_round_amount_raised` | Integer (long) | ❌ **NEVER USE** | 0% | **ALWAYS NULL** - Broken field |

**Funding Stage Proxies:**
- **Early Stage Startup:** `founded_year: >= "2020"` AND `employees_count: <= 50`
- **Growth Stage:** `founded_year: >= "2018"` AND `employees_count: 50-500`
- **Mature:** `founded_year: < "2015"` OR `employees_count: > 500`

**Example Query - Funding Priority:**
```json
{
  "bool": {
    "should": [
      {"range": {"company_founded_year": {"gte": "2020", "lte": "2023"}}},
      {"range": {"company_employees_count": {"gte": 10, "lte": 500}}},
      {"exists": {"field": "company_last_funding_round_date"}}
    ],
    "minimum_should_match": 2
  }
}
```

---

## PRIORITY 5: MANAGEMENT LEVEL FIELDS

⚠️ **Rare Values** - "Senior" only appears in 2% of profiles

| Field | Type | Query | Coverage | Notes |
|-------|------|-------|----------|-------|
| `active_experience_management_level` | String (enum) | term | Variable | Seniority level - **USE IN SHOULD ONLY** |
| `is_decision_maker` | Integer (0/1) | term | Variable | Leadership flag based on title analysis |

**Management Level Enum Values & Distribution:**
```
"Specialist" - 74% (most common)
"Manager" - 14%
"Mid-Level" - ~5%
"Head" - 3%
"Senior" - 2% ⚠️ (very rare!)
"C-Level" - 1%
"Intern" - 2%
"Owner" - <1%
```

**⚠️ WARNING:** Never use `active_experience_management_level` in MUST clauses!
- Filtering for "Senior" eliminates 98% of candidates
- Use in SHOULD clauses only for preference scoring

**Example Query - Management Level (SHOULD only):**
```json
{
  "bool": {
    "should": [
      {"term": {"active_experience_management_level": "Senior"}},
      {"term": {"active_experience_management_level": "Manager"}},
      {"term": {"active_experience_management_level": "C-Level"}},
      {"term": {"is_decision_maker": 1}},
      {"wildcard": {"active_experience_title": "*senior*"}},
      {"wildcard": {"active_experience_title": "*lead*"}}
    ],
    "minimum_should_match": 1
  }
}
```

---

## PRIORITY 6: SKILLS & EXPERIENCE FIELDS

✅ **Confirmed Working** - Both `inferred_skills` and `total_experience_duration_months` exist!

| Field | Type | Query | Coverage | Use Case |
|-------|------|-------|----------|----------|
| `inferred_skills` | Array[String] | term | Variable | **CONFIRMED**: Technical skills (e.g., "Python", "React", "AWS") |
| `total_experience_duration_months` | Integer | range | Variable | **CONFIRMED**: Total career experience in months |
| `education_degrees` | Array[String] | wildcard | Variable | Degree requirements (e.g., "*Bachelor*", "*Computer Science*") |
| `last_graduation_date` | String (YYYY) | range | Variable | Graduation year (recency filter) |

**Example Query - Skills Priority:**
```json
{
  "bool": {
    "should": [
      {"term": {"inferred_skills": "Python"}},
      {"term": {"inferred_skills": "React"}},
      {"term": {"inferred_skills": "AWS"}},
      {"term": {"inferred_skills": "Machine Learning"}},
      {"wildcard": {"headline": "*python*"}},
      {"wildcard": {"headline": "*react*"}},
      {"range": {"total_experience_duration_months": {"gte": 60}}},
      {"wildcard": {"education_degrees": "*computer*science*"}}
    ],
    "minimum_should_match": 3
  }
}
```

---

## NESTED FIELDS: Past Experience Array

**Critical for finding candidates with relevant past experience!**

**Path:** `experience` (Array of Structs)

Use nested queries to search through **all past roles**, not just current job.

### Available Nested Fields
| Nested Field | Type | Use Case |
|--------------|------|----------|
| `experience.active_experience` | Integer (0/1) | Filter current (1) vs past (0) |
| `experience.position_title` | String | Past job titles |
| `experience.department` | String | Past departments |
| `experience.management_level` | String | Past seniority levels |
| `experience.company_id` | Integer | Past employer ID |
| `experience.company_name` | String | **Past employer name** |
| `experience.company_industry` | String | **Past industry experience** |
| `experience.company_employees_count` | Integer | Past company size |
| `experience.description` | String | Role description (rich for keywords) |
| `experience.duration_months` | Integer | Time in role |
| `experience.date_from_year` | Integer | Start year |
| `experience.date_to_year` | Integer | End year (null if current) |

**Example Nested Query - Past FAANG Experience:**
```json
{
  "nested": {
    "path": "experience",
    "query": {
      "bool": {
        "should": [
          {"wildcard": {"experience.company_name": "*google*"}},
          {"wildcard": {"experience.company_name": "*meta*"}},
          {"wildcard": {"experience.company_name": "*amazon*"}},
          {"wildcard": {"experience.company_name": "*apple*"}},
          {"wildcard": {"experience.company_name": "*microsoft*"}},
          {"wildcard": {"experience.position_title": "*engineer*"}},
          {"term": {"experience.company_industry": "Software Development"}}
        ],
        "minimum_should_match": 2
      }
    }
  }
}
```

**Why use nested queries?**
- Find people who EVER worked at target companies (not just currently)
- Find people who previously worked in target industries
- Find people with startup experience (even if now at large company)
- Include job seekers with relevant past roles

---

## COMPLETE QUERY TEMPLATE (All Priorities)

```json
{
  "query": {
    "bool": {
      "must": [],
      "should": [
        // Priority 1: Company & Industry
        {"term": {"company_industry": "Software Development"}},
        {"wildcard": {"company_name": "*startup*"}},
        {"range": {"company_founded_year": {"gte": "2020"}}},
        {"nested": {
          "path": "experience",
          "query": {
            "bool": {
              "should": [
                {"wildcard": {"experience.company_name": "*google*"}},
                {"term": {"experience.company_industry": "Software Development"}}
              ]
            }
          }
        }},

        // Priority 2: Location
        {"wildcard": {"location_full": "*san francisco*"}},
        {"wildcard": {"location_full": "*bay area*"}},
        {"term": {"location_country": "United States"}},

        // Priority 3: Role & Title
        {"wildcard": {"active_experience_title": "*engineer*"}},
        {"wildcard": {"active_experience_title": "*senior*"}},
        {"term": {"active_experience_department": "Engineering and Technical"}},

        // Priority 4: Funding (proxy via founded year)
        {"range": {"company_employees_count": {"gte": 10, "lte": 500}}},

        // Priority 5: Management Level (SHOULD only)
        {"term": {"active_experience_management_level": "Senior"}},
        {"wildcard": {"active_experience_title": "*lead*"}},

        // Priority 6: Skills & Experience
        {"term": {"inferred_skills": "Python"}},
        {"term": {"inferred_skills": "React"}},
        {"wildcard": {"headline": "*python*"}},
        {"range": {"total_experience_duration_months": {"gte": 60}}}
      ],
      "minimum_should_match": 3
    }
  },
  "sort": ["_score"]
}
```

**Permissiveness:** 3 out of ~20 criteria = 15% match rate (very wide net)

---

## KEY DESIGN DECISIONS

### 1. NO `is_working` Filter
**Decision:** Don't filter by employment status
**Rationale:**
- Includes people actively job hunting
- Includes people who previously worked at target companies
- Includes people between roles with valuable experience
- Dramatically expands candidate pool

### 2. Empty MUST Array
**Decision:** Use SHOULD clauses with `minimum_should_match` instead of MUST
**Rationale:**
- Avoids overly restrictive AND logic
- Allows flexibility in matching criteria
- Better than 0 results from too many MUSTs

### 3. Nested Queries for Past Experience
**Decision:** Always include nested queries for experience array
**Rationale:**
- People change jobs - past experience is highly valuable
- "Worked at Google" is just as valuable as "Works at Google"
- Catches job seekers with ideal backgrounds

### 4. Management Level in SHOULD Only
**Decision:** Never filter `active_experience_management_level` in MUST
**Rationale:**
- "Senior" appears in only 2% of profiles
- Title variations ("Staff", "Lead", "Principal") spread across levels
- Better to match on title keywords than enum values

---

## COMMON PITFALLS TO AVOID

❌ **Don't:** Filter `is_working: 1` (excludes job seekers)
✅ **Do:** Include both employed and available candidates

❌ **Don't:** Require `active_experience_management_level: "Senior"` in MUST
✅ **Do:** Use in SHOULD with title wildcards

❌ **Don't:** Use `company_last_funding_round_amount_raised` (always NULL)
✅ **Do:** Use `company_founded_year` as funding stage proxy

❌ **Don't:** Ignore past experience
✅ **Do:** Use nested queries on `experience` array

❌ **Don't:** Put location in MUST (too restrictive)
✅ **Do:** Use location wildcards in SHOULD with remote options

❌ **Don't:** Require exact skill matches in MUST
✅ **Do:** Use SHOULD with `minimum_should_match: 2-3` for flexibility

---

## TESTING & VALIDATION

**Test Query Quality:**
1. **Result Count:** Aim for 20-200 results per query
   - <20 results → Too restrictive (increase SHOULD clauses or lower minimum_should_match)
   - >200 results → Too permissive (increase minimum_should_match or add more MUST clauses)

2. **Result Relevance:** Check first 10 candidates
   - Do they match company/industry priorities?
   - Do they have relevant skills?
   - Are locations appropriate?

3. **Permissiveness Tuning:**
   - Start with `minimum_should_match: 3`
   - If 0 results → Lower to 2
   - If >500 results → Raise to 4-5

---

## REFERENCE: JD Parser → CoreSignal Mapping

| JD Field | CoreSignal Field(s) | Strategy |
|----------|---------------------|----------|
| `role_title` | `active_experience_title`, `headline` | Wildcard with multiple variations |
| `seniority_level` | `active_experience_management_level` (SHOULD), title wildcards | Never in MUST |
| `technical_skills` | `inferred_skills`, `headline` | Term queries + headline wildcards |
| `domain_expertise` | `company_industry`, `experience.company_industry` (nested) | Current + past industries |
| `experience_years.minimum` | `total_experience_duration_months` | Range query (years * 12) |
| `location` | `location_full`, `location_city`, `location_country` | Wildcards + exact matches |
| `company_stage` | `company_founded_year`, `company_employees_count` | Range proxies |
| `must_have` (education) | `education_degrees` | Wildcard array search |

---

## CHANGELOG

**2025-10-30:**
- Initial documentation created
- Confirmed `inferred_skills` and `total_experience_duration_months` exist and work
- Established priority order: Company > Location > Role > Funding > Seniority > Skills
- Documented decision to remove `is_working` filter
- Added nested query examples for past experience
- Documented field coverage stats from testing

---

## ADDITIONAL RESOURCES

- CoreSignal API Docs: https://docs.coresignal.com/
- Elasticsearch DSL Docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
- JD Analyzer Integration: See `/docs/JD_ANALYZER_INTEGRATION.md`
- Pipeline Debugging: See `/docs/JD_PIPELINE_DEBUGGING.md`
