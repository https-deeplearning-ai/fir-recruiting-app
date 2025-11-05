# JD Analyzer Pipeline Debugging Guide

## Overview

This guide documents the comprehensive logging system added to the JD Analyzer to debug the complete pipeline:

**JD Text → Parsed Requirements → LLM Query Generation → Elasticsearch DSL → CoreSignal API → Candidates**

## Quick Start

### Enable Debug Logging

```bash
# Set environment variable
export JD_DEBUG=1

# Start backend
cd backend
python3 app.py

# Logs appear in:
# 1. Console (colored output)
# 2. backend/logs/debug.log (plain text)
```

### Disable Logging

```bash
unset JD_DEBUG
# or
export JD_DEBUG=0
```

## What Was Added

### 1. Debug Logger Utility (`backend/jd_analyzer/debug_logger.py`)

**Features:**
- **Colored console output** with distinct sections
- **Structured logging** with consistent format
- **JSON pretty-printing** with truncation
- **Automatic log file** (`backend/logs/debug.log`)
- **Zero overhead** when disabled (check happens once at import)

**Log Sections:**
- `[JD_PARSE]` - Job description parsing
- `[LLM_PROMPT]` - LLM prompts and inputs
- `[LLM_RESPONSE]` - LLM responses and parsed queries
- `[QUERY_BUILD]` - Query construction
- `[CORESIGNAL_API]` - CoreSignal API requests/responses
- `[ERROR]` - Errors with full context and tracebacks

### 2. Logging Points Added

#### JD Parser (`jd_parser.py`) - 4 Points

**Point 1 - Before Claude API Call (Line 114):**
```python
debug_log.jd_parse("Parsing JD text", jd_text=jd_text)
```
Logs: JD text preview (500 chars), total length

**Point 2 - After Claude Response (Line 128):**
```python
debug_log.llm_response("Claude Sonnet 4.5", response=response_text)
```
Logs: Full raw response from Claude

**Point 3 - After JSON Parsing (Line 147):**
```python
debug_log.jd_parse("Parse successful", requirements=parsed_data, success=True)
```
Logs: Parsed requirements summary (role, seniority, skills count, experience)

**Point 4 - Error Handlers (Lines 154, 160):**
```python
debug_log.error("Pydantic validation error", exception=e, context={...})
```
Logs: Full exception + traceback

#### LLM Query Generator (`llm_query_generator.py`) - 12 Points

**Claude Method (4 points):**
1. **Line 123** - Before API call: Model, temperature, prompt preview, requirements
2. **Line 146** - After API call: Raw response (before markdown stripping)
3. **Line 158** - After JSON parse: Parsed query structure with complexity analysis
4. **Line 172** - Error handler: Exception, context, raw data

**GPT Method (4 points):**
5. **Line 208** - Before API call
6. **Line 234** - After API call
7. **Line 246** - After JSON parse
8. **Line 260** - Error handler

**Gemini Method (4 points):**
9. **Line 296** - Before API call
10. **Line 323** - After API call
11. **Line 335** - After JSON parse
12. **Line 349** - Error handler

#### API Endpoints (`api_endpoints.py`) - 3 Critical Points

**Claude Endpoint `/api/jd/generate-query-claude`:**

**Line 679 - Before CoreSignal API:**
```python
debug_log.coresignal_api(
    f"Searching CoreSignal with {model} query",
    query=query,
    page=1
)
```
Logs: Pretty-printed Elasticsearch DSL query

**Line 694 - CoreSignal Error:**
```python
debug_log.coresignal_api(
    "CoreSignal API error",
    success=False,
    error_status=response.status_code,
    error_body=response.text
)
```
Logs: HTTP status, full error response

**Line 722 - CoreSignal Success:**
```python
debug_log.coresignal_api(
    "CoreSignal search successful",
    success=True,
    total_found=len(all_profiles),
    profiles_count=len(preview_profiles),
    first_profile=first_profile
)
```
Logs: Result count, first profile details (name, title, experience)

## Example Output

### Successful Flow

```
================================================================================
JD Analyzer Debug Session - 2025-10-30T15:30:00
================================================================================

[JD_PARSE] Parsing JD text
  JD Text (2,847 chars):
  We are seeking an experienced Senior Software Engineer with deep expertise in Python...

[LLM_RESPONSE] ✓ Claude Sonnet 4.5 responded
  Raw Response (1,234 chars):
  {"role_title": "Senior Software Engineer", "seniority_level": "Senior", ...}

[JD_PARSE] ✓ Parse successful
  Parsed Requirements:
    Role: Senior Software Engineer | Seniority: Senior
    Experience: 5-10 years | Skills: 12 | Must-have: 8

[LLM_PROMPT] Claude Haiku 4.5 generating query
  Model: Claude Haiku 4.5 | Temp: 0 | Max Tokens: 4096
  Requirements (abbreviated):
    {
      "role_title": "Senior Software Engineer",
      "seniority_level": "Senior",
      "technical_skills_count": 12,
      ...
    }

[LLM_RESPONSE] ✓ Claude Haiku 4.5 responded
  Raw Response (987 chars):
  ```json
  {
    "query": {
      "bool": {
        "must": [...]
      }
    }
  }
  ```

[LLM_RESPONSE] ✓ Claude Haiku 4.5 responded
  Parsed Query:
    Complexity: 3 must clauses, 2 should clauses
    {
      "query": {
        "bool": {
          "must": [
            {"match": {"is_working": 1}},
            {"wildcard": {"active_experience_title": "*senior*engineer*"}},
            {"range": {"total_experience_duration_months": {"gte": 60}}}
          ]
        }
      }
    }

[CORESIGNAL_API] Searching CoreSignal with Claude Haiku 4.5 query
  Page: 1
  Query:
    {
      "query": {
        "bool": {
          "must": [...]
        }
      }
    }

[CORESIGNAL_API] ✓ CoreSignal search successful
  Results: 47 candidates found
  Profiles in response: 20
  First Profile: John Doe | Senior Software Engineer at Google | 10.0 years exp

```

### Error Scenario: No Results

```
[CORESIGNAL_API] ✓ CoreSignal search successful
  Results: 0 candidates found
  Profiles in response: 0
```

**Analysis:** Query is likely too restrictive. Check:
1. Number of `must` clauses (too many = overly restrictive)
2. Field values match CoreSignal taxonomy
3. Wildcards are correctly formatted (`*keyword*`)

### Error Scenario: LLM JSON Parsing Failure

```
[LLM_RESPONSE] ✓ Claude Haiku 4.5 responded
  Raw Response (234 chars):
  I apologize, but I cannot generate a query for this JD because...

[ERROR] Claude Haiku 4.5 query generation failed
  Exception: JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  Context:
    {"model": "claude-haiku-4-5-20251015"}
  Raw Data (234 chars):
    I apologize, but I cannot generate...
  Traceback:
    File "llm_query_generator.py", line 155, in generate_with_claude
      query = json.loads(query_text)
```

**Analysis:** LLM returned text instead of JSON. Possible causes:
1. Prompt confusion (check system prompt clarity)
2. Safety refusal (LLM thinks request is inappropriate)
3. Model temperature too high (should be 0)

### Error Scenario: CoreSignal API Error

```
[CORESIGNAL_API] POST /search/es_dsl?page=1
  Query: {...}

[CORESIGNAL_API] ✗ CoreSignal API error
  HTTP Status: 400
  Error Response:
    {"error": "Invalid query syntax: field 'active_experience_titl' does not exist"}
```

**Analysis:** Query has typo in field name. Common issues:
1. Typo in field name (`active_experience_titl` vs `active_experience_title`)
2. Wrong data type (string vs array)
3. Invalid enum value for management_level or department

## Common Issues & Debugging

### Issue 1: "No candidates found" (0 results)

**Debug Steps:**
1. Check log for `[CORESIGNAL_API]` section
2. Look at query structure:
   ```
   Complexity: X must clauses, Y should clauses
   ```
3. **If must clauses > 4:** Query is likely too restrictive
4. **Check field values:** Do they match CoreSignal taxonomies?
5. **Test simpler query:** Remove optional filters one by one

**Fix:**
- Reduce `must` clauses, use `should` instead
- Verify enum values in `coresignal_taxonomies.py`
- Use broader wildcards (`*engineer*` vs `*senior*software*engineer*`)

### Issue 2: "JSON parsing error"

**Debug Steps:**
1. Check `[LLM_RESPONSE]` raw response
2. Look for:
   - Text instead of JSON
   - Malformed JSON (missing braces)
   - Markdown code blocks not stripped

**Fix:**
- Check prompt clarity in `llm_query_generator.py`
- Verify temperature is 0 (deterministic)
- Check model supports JSON mode

### Issue 3: "CoreSignal API 400 error"

**Debug Steps:**
1. Check error response body in logs
2. Common errors:
   - `field does not exist` → Typo in field name
   - `invalid value` → Wrong enum value
   - `syntax error` → Malformed Elasticsearch DSL

**Fix:**
- Cross-reference with CoreSignal API docs
- Check `coresignal_taxonomies.py` for correct enums
- Validate query structure matches examples

### Issue 4: "Wrong candidates returned"

**Debug Steps:**
1. Check parsed requirements in `[JD_PARSE]`
2. Compare to original JD text
3. Look at generated query in `[CORESIGNAL_API]`
4. Check first profile returned

**Fix:**
- Improve JD parsing prompt
- Add more specific skills to requirements
- Use nested queries for experience array
- Add location filters

## Performance Notes

**Logging Overhead:**
- **Disabled (JD_DEBUG=0):** Zero overhead (single check at import)
- **Enabled (JD_DEBUG=1):** ~5-10ms per log call (negligible)

**Log File Size:**
- ~50KB per JD analysis session
- Rotate logs manually or use logrotate

**Production Usage:**
- **NEVER** leave JD_DEBUG=1 in production
- Use only for local debugging or staging

## Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `backend/jd_analyzer/debug_logger.py` | 310 (NEW) | Debug logging utility |
| `backend/jd_analyzer/jd_parser.py` | +15 | 4 log points |
| `backend/jd_analyzer/llm_query_generator.py` | +48 | 12 log points (4 per model) |
| `backend/jd_analyzer/api_endpoints.py` | +31 | 3 critical CoreSignal API log points |
| `backend/logs/debug.log` | N/A (AUTO) | Log file output |

**Total:** ~404 lines added for complete pipeline visibility

## Next Steps

1. **Test with real JDs:**
   ```bash
   export JD_DEBUG=1
   cd backend && python3 app.py
   # Submit JD through frontend
   # Check console + backend/logs/debug.log
   ```

2. **Analyze failures:**
   - Find error in logs
   - Check raw LLM responses
   - Verify query structure
   - Test CoreSignal API directly if needed

3. **Optimize queries:**
   - Compare Claude vs GPT vs Gemini queries
   - Identify which generates best results
   - Update prompts if needed

4. **Production readiness:**
   - Ensure JD_DEBUG=0 in production
   - Add error monitoring
   - Set up alerts for common failures

## Related Documentation

- [JD Analyzer Integration Guide](JD_ANALYZER_INTEGRATION.md)
- [JD Analyzer Prompt Analysis](JD_ANALYZER_PROMPT_ANALYSIS.md)
- [CoreSignal API Documentation](https://coresignal.com/docs)

## Questions?

Check logs first, then:
1. Look for ERROR sections
2. Check raw LLM responses
3. Verify query structure
4. Test CoreSignal API directly

Most issues are either:
- LLM not generating valid JSON
- Query too restrictive (too many `must` clauses)
- Field name typos or wrong enum values
