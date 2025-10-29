# Evidence & Technical Decisions

This folder contains evidence, test results, and analysis that informed technical decisions for the LinkedIn Profile AI Assessor.

---

## Folder Structure

### 📁 [multi_source_api_evaluation/](multi_source_api_evaluation/)

**Purpose:** Evidence for why we DON'T use CoreSignal's `/employee/multi-source` API

**Key Findings:**
- ❌ Multi-source API provides **incomplete data** (missing critical fields)
- ❌ **Slower** than current two-step approach (search → collect)
- ❌ **Less reliable** company enrichment
- ✅ Current flow (search by URL → collect full profile) is superior

**Files:**
- `MULTI_SOURCE_EVALUATION.md` - Full evaluation report with test results
- `README.md` - Test methodology and setup
- `test_multi_source_employee.py` - Test script comparing APIs
- `compare_api_responses.py` - Field-by-field comparison tool
- `results/` - Raw JSON responses from 4 CEO profiles
- `comparisons/` - Side-by-side API comparison
- `evidence/` - Detailed field analysis

**Conclusion:** We use the **two-step approach** (search → collect) instead of multi-source API.

---

## Related Documentation

- [Technical Decisions](../technical-decisions/) - Architecture decisions with rationale
- [Reverse-Engineering](../reverse-engineering/) - JD + shortlist analysis case study
- [SUPABASE_SCHEMA.sql](../SUPABASE_SCHEMA.sql) - Database schema

---

## Adding New Evidence

When making technical decisions that require evidence:

1. Create a new folder under `docs/evidence/[decision-name]/`
2. Include:
   - `README.md` - Overview and methodology
   - `EVALUATION.md` - Detailed findings
   - Test scripts
   - Raw data / results
   - Analysis files
3. Update this README with a link and summary
4. Reference from main `CLAUDE.md` if it affects architecture

**Example:**
```
docs/evidence/
├── multi_source_api_evaluation/  ← This folder
├── rate_limiting_tests/           ← Future: API rate limit analysis
└── llm_model_comparison/          ← Future: Claude vs GPT-4 for assessments
```

---

## Key Takeaway

**Evidence-based decisions over assumptions.**

This folder documents the "why" behind technical choices, making it easier to:
- Onboard new developers
- Revisit decisions when requirements change
- Justify architecture to stakeholders
- Avoid repeating past mistakes
