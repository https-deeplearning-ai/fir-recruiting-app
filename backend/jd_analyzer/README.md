# JD Analyzer Module

Extract weighted assessment criteria from job descriptions to automatically configure candidate evaluation rubrics.

## Features

1. **JD Parsing** - Extract structured requirements (must-have, nice-to-have, technical skills, domain expertise)
2. **Weight Generation** - Automatically generate weighted assessment criteria (1-5 requirements with % weights)
3. **Keyword Extraction** - Extract search keywords for CoreSignal queries
4. **Shortlist Analysis** - Reverse-engineer implicit criteria from candidate shortlists

## Module Structure

```
jd_analyzer/
├── __init__.py              # Module exports
├── jd_parser.py             # JD text → structured requirements
├── weight_generator.py      # Requirements → weighted assessment criteria
├── shortlist_analyzer.py    # CSV shortlist → implicit criteria discovery
├── api_endpoints.py         # Flask API routes
└── README.md                # This file
```

## Usage

### 1. Parse Job Description

```python
from jd_analyzer import JDParser

parser = JDParser()
requirements = parser.parse(jd_text)

# Returns:
# {
#     "role_title": "Senior ML Engineer",
#     "seniority_level": "senior",
#     "must_have": ["5+ years ML", "Python", "LLMs"],
#     "nice_to_have": ["Voice AI experience"],
#     "technical_skills": ["Python", "PyTorch", "LLMs"],
#     "domain_expertise": ["NLP", "Voice AI"],
#     "experience_years": {"minimum": 5, "preferred": 8},
#     "location": "San Francisco Bay Area",
#     "implicit_criteria": {...}
# }
```

### 2. Generate Weighted Requirements

```python
from jd_analyzer import WeightGenerator

generator = WeightGenerator()
weighted_reqs = generator.generate_weighted_requirements(requirements, num_requirements=5)

# Returns:
# [
#     {
#         "requirement": "Voice AI / Real-time Systems Expertise",
#         "weight": 35,
#         "description": "Deep experience with voice AI, speech recognition, or real-time audio processing",
#         "scoring_criteria": "10 = Built production voice AI systems; 5 = Used voice APIs; 1 = No voice experience"
#     },
#     ...
# ]
```

### 3. Analyze Candidate Shortlist

```python
from jd_analyzer import ShortlistAnalyzer

analyzer = ShortlistAnalyzer("candidates.csv")
analyzer.load_candidates()
analysis = analyzer.analyze_patterns()

# Returns:
# {
#     "total_candidates": 68,
#     "location_distribution": {"San Francisco Bay Area": 47, "New York": 6, ...},
#     "seniority_distribution": {"c_suite": 34, "senior_ic": 14, ...},
#     "top_companies": [("Otter.ai", 6), ("Meta", 5), ...],
#     "implicit_criteria": {
#         "primary_location": "San Francisco Bay Area",
#         "location_preference_strength": "69.1%",
#         "seniority_flexibility": {...},
#         "referral_driven_sourcing": true
#     }
# }
```

### 4. Compare JD vs Reality

```python
# Discover gaps between stated JD requirements and actual shortlist
gaps = analyzer.compare_to_jd(requirements)

# Returns:
# {
#     "location_gap": {
#         "jd_states": "Remote, United States",
#         "reality": "69.1% in San Francisco Bay Area",
#         "insight": "Implicit geographic preference despite broader JD"
#     },
#     "seniority_gap": {...},
#     "nice_to_have_actually_required": {...}
# }
```

## API Endpoints

Add to your Flask app:

```python
from jd_analyzer.api_endpoints import register_jd_analyzer_routes

register_jd_analyzer_routes(app)
```

### Available Endpoints

**1. Parse JD**
```
POST /api/jd/parse
Body: {"jd_text": "..."}
```

**2. Generate Weights**
```
POST /api/jd/generate-weights
Body: {"jd_text": "...", "num_requirements": 5}
```

**3. Full Analysis**
```
POST /api/jd/full-analysis
Body: {"jd_text": "...", "num_requirements": 5}
Returns: Requirements + weighted criteria + keywords
```

**4. Analyze Shortlist**
```
POST /api/jd/analyze-shortlist
Form Data:
  - csv_file: CSV file (Profile URL, Current Title, Current Company, Location)
  - jd_text: Optional JD for gap analysis
```

**5. Extract Keywords**
```
POST /api/jd/extract-keywords
Body: {"jd_text": "..."}
```

## Frontend Integration

### Use Case: Auto-populate Assessment Criteria

**User Flow:**
1. User pastes job description into textarea
2. Click "Analyze JD" button
3. System calls `/api/jd/full-analysis`
4. Frontend displays suggested weighted requirements
5. User reviews and edits weights
6. Weights are used for candidate assessment

**React Example:**

```javascript
const analyzeJD = async (jdText) => {
  const response = await fetch('/api/jd/full-analysis', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      jd_text: jdText,
      num_requirements: 5
    })
  });

  const data = await response.json();

  if (data.success) {
    // Auto-populate assessment form
    setWeightedRequirements(data.weighted_requirements);
    setGeneralFitWeight(data.general_fit_weight);
  }
};
```

## CSV Format for Shortlist Analysis

Required columns (flexible naming):
- `Profile URL` or `linkedin_url` or `LinkedIn URL`
- `Current Title` or `title` or `Title`
- `Current Company` or `company` or `Company`
- `Location` or `location`

Example:
```csv
Profile URL,Current Title,Current Company,Location
https://linkedin.com/in/john-doe,CTO,Acme AI,San Francisco
https://linkedin.com/in/jane-smith,Staff ML Engineer,BigTech Co,Seattle
```

## Configuration

Set environment variable:
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

## Dependencies

- `anthropic` - Claude AI client for parsing and generation
- `csv` - CSV file parsing (Python stdlib)
- `collections.Counter` - Pattern counting (Python stdlib)

## Testing

```bash
# Test JD parsing
python3 -c "
from jd_analyzer import JDParser
parser = JDParser()
result = parser.parse('Senior ML Engineer with 5+ years experience...')
print(result)
"

# Test weight generation
python3 -c "
from jd_analyzer import JDParser, WeightGenerator
parser = JDParser()
generator = WeightGenerator()
reqs = parser.parse('Senior ML Engineer...')
weights = generator.generate_weighted_requirements(reqs, 3)
print(weights)
"
```

## Example Output

**Weighted Requirements for Voice AI Role:**

1. **Voice AI / Real-time Systems Expertise (35%)**
   - Description: Deep experience building voice AI, speech recognition, or real-time audio systems
   - Scoring: 10 = Built production voice AI; 5 = Used voice APIs; 1 = No experience

2. **AI/ML Infrastructure & LLMs (25%)**
   - Description: Strong background in ML infrastructure, LLM fine-tuning, and model deployment
   - Scoring: 10 = Scaled ML systems to millions of users; 5 = Deployed models in production; 1 = Academic only

3. **0→1 Product Leadership (20%)**
   - Description: Experience taking products from concept to launch as founder or early employee
   - Scoring: 10 = Founded/co-founded successful companies; 5 = Early employee; 1 = Joined mature products

4. **Developer Tools / Platform Engineering (10%)**
   - Description: Built developer-facing products, SDKs, or infrastructure tools
   - Scoring: 10 = Built widely-adopted dev tools; 5 = Contributed to dev platforms; 1 = No dev tools experience

5. **Fundraising & GTM Experience (10%)**
   - Description: Raised funding and executed go-to-market strategies
   - Scoring: 10 = Raised Series A+; 5 = Involved in fundraising; 1 = No fundraising experience

**General Fit: 0%** (auto-calculated)

Total: 100%

## Related Documentation

- [Reverse-Engineering Report](../../docs/reverse-engineering/REVERSE_ENGINEERING_REPORT.md) - Case study analyzing Voice AI role
- [CLAUDE.md](../../CLAUDE.md) - Project overview and architecture

## Future Enhancements

- [ ] Machine learning model trained on JD + shortlist → hiring outcomes
- [ ] Automatic CoreSignal query generation from parsed JD
- [ ] Integration with ATS systems (Lever, Greenhouse, Workable)
- [ ] A/B testing of different weight configurations
- [ ] Candidate-to-requirement similarity scoring
- [ ] Auto-suggest company filtering based on JD domain
