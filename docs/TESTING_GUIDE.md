# LinkedIn Profile AI Assessor - Testing Guide

Complete end-to-end testing guide for the Chrome extension integration and LinkedIn Recruiter export workflow.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Testing Phase 1: Extension Bookmarking](#testing-phase-1-extension-bookmarking)
4. [Testing Phase 2: Batch Assessment](#testing-phase-2-batch-assessment)
5. [Testing Phase 3: LinkedIn Recruiter Export](#testing-phase-3-linkedin-recruiter-export)
6. [API Testing with curl](#api-testing-with-curl)
7. [Database Verification](#database-verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Keys
- [ ] Anthropic API key (for Claude AI assessments)
- [ ] CoreSignal API key (for profile data)
- [ ] Supabase project (database)
- [ ] LinkedIn Recruiter account (for CSV import testing)
- [ ] Chrome browser (latest version)

### Environment Setup
```bash
# Backend environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export CORESIGNAL_API_KEY="..."
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="eyJhbGc..."
```

---

## Local Development Setup

### Step 1: Start Backend Server

```bash
# Terminal 1: Backend
cd backend
python3 app.py
# Should see: "Running on http://127.0.0.1:5001"
```

### Step 2: Load Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. Verify extension loads without errors

### Step 3: Configure Extension Settings

1. Click extension icon in toolbar
2. Click "Settings" button
3. Configure:
   - **Backend API URL**: `http://localhost:5001`
   - **Your Name**: Your recruiter name (e.g., "Jon")
   - Save settings

### Step 4: Verify Connection

1. Open any LinkedIn profile page
2. Click extension icon
3. Should see list dropdown (may be empty)
4. Check browser console for any errors

---

## Testing Phase 1: Extension Bookmarking

### Test Case 1.1: Create a New List

**Objective:** Verify list creation from extension

**Steps:**
1. Navigate to any LinkedIn profile
2. Click extension icon
3. In list dropdown, click "Create New List"
4. Enter name: "Test Senior Engineers"
5. Click "Create"

**Expected Results:**
- ✅ Success message appears
- ✅ New list appears in dropdown
- ✅ List is selected automatically

**API Call Verification:**
```bash
# Check backend logs for:
POST /extension/create-list
Response: {"success": true, "list_id": "uuid"}
```

### Test Case 1.2: Add Profile to List

**Objective:** Verify profile bookmarking functionality

**Test Profiles:**
Use these public LinkedIn profiles for testing:
- https://www.linkedin.com/in/satyanadella/ (Satya Nadella)
- https://www.linkedin.com/in/jeffweiner08/ (Jeff Weiner)
- https://www.linkedin.com/in/sundarpichai/ (Sundar Pichai)

**Steps:**
1. Navigate to first test profile
2. Wait for page to fully load
3. Click extension icon
4. Select "Test Senior Engineers" list
5. Click "Add to List" button

**Expected Results:**
- ✅ Success badge appears on extension icon
- ✅ Message shows "Added to list!"
- ✅ Badge disappears after 3 seconds

**Data Verification:**
```bash
# Backend logs should show:
POST /extension/add-profile
{
  "list_id": "uuid",
  "linkedin_url": "https://www.linkedin.com/in/satyanadella",
  "name": "Satya Nadella",
  "headline": "Chairman and CEO at Microsoft",
  ...
}
Response: {"success": true, "profile_id": "uuid", "is_duplicate": false}
```

### Test Case 1.3: Duplicate Profile Detection

**Objective:** Verify duplicate handling

**Steps:**
1. Stay on same LinkedIn profile
2. Click "Add to List" again

**Expected Results:**
- ✅ Success message appears (profile updated)
- ✅ No error occurs
- ✅ Backend logs show `is_duplicate: true`

### Test Case 1.4: Add Multiple Profiles

**Objective:** Build a test list with multiple candidates

**Steps:**
1. Add 3-5 test profiles to "Test Senior Engineers" list
2. Use the test profiles listed above

**Expected Results:**
- ✅ All profiles added successfully
- ✅ No errors in console
- ✅ Extension badge shows success for each

---

## Testing Phase 2: Batch Assessment

### Preparation: Verify Database State

**Check Extension Profiles Table:**
```bash
# Using Supabase SQL Editor or API
curl -X GET "https://your-project.supabase.co/rest/v1/extension_profiles?select=*" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"

# Should show 3-5 profiles with:
# - assessed: false
# - assessment_id: null
# - assessment_score: null
# - status: 'pending'
```

### Test Case 2.1: Assess All Profiles via API

**Objective:** Trigger batch assessment for all profiles in list

**Get List ID:**
```bash
# Get all lists
curl -X GET "http://localhost:5001/extension/lists?recruiter_name=Jon"

# Response will include:
# {
#   "lists": [
#     {
#       "id": "uuid-of-test-list",
#       "name": "Test Senior Engineers",
#       "profile_count": 5,
#       "assessed_count": 0
#     }
#   ]
# }
```

**Trigger Assessment:**
```bash
# Replace {list_id} with actual UUID
curl -X POST "http://localhost:5001/lists/{list_id}/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "name": "Leadership Experience",
        "description": "C-level executive experience at major tech companies",
        "weight": 40
      },
      {
        "name": "Strategic Vision",
        "description": "Track record of driving company growth and innovation",
        "weight": 30
      }
    ],
    "job_description": "Seeking experienced technology executive for board position"
  }'
```

**Expected Results:**
- ✅ Request returns 200 OK
- ✅ Response shows progress: `{"total": 5, "assessed": 5, "failed": 0}`
- ✅ Average score calculated: `"avg_score": 88.3`
- ✅ Process completes in 2-3 minutes (depending on profile count)

**Monitor Backend Logs:**
```
Processing list assessment: list_id={uuid}, total_profiles=5
Fetching profile 1/5 from CoreSignal: https://www.linkedin.com/in/satyanadella
Generating AI assessment for: Satya Nadella
Linking assessment to profile: assessment_id={uuid}, score=92.5
...
Assessment complete: 5 assessed, 0 failed, avg_score=88.3
```

### Test Case 2.2: Verify Assessment Data

**Check Extension Profiles Table:**
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/extension_profiles?list_id=eq.{list_id}&select=*" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"

# All profiles should now have:
# - assessed: true
# - assessment_id: (valid UUID)
# - assessment_score: (float value 0-100)
# - status: 'assessed'
```

**Check Candidate Assessments Table:**
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/candidate_assessments?select=*&order=created_at.desc&limit=5" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"

# Should show 5 new assessments with:
# - profile_data: (full CoreSignal data)
# - assessment_data: (full Claude AI assessment)
# - weighted_score: (calculated score)
# - assessment_type: 'batch'
```

### Test Case 2.3: Get List Statistics

**Objective:** Verify list stats after assessment

```bash
curl -X GET "http://localhost:5001/extension/lists/{list_id}/stats"

# Expected response:
{
  "list_id": "uuid",
  "total_profiles": 5,
  "assessed_profiles": 5,
  "by_status": {
    "pending": 0,
    "assessed": 5,
    "exported": 0
  },
  "score_distribution": {
    "90-100": 3,
    "80-89": 2,
    "70-79": 0,
    "60-69": 0
  },
  "avg_score": 88.3,
  "top_profiles": [
    {
      "linkedin_url": "https://www.linkedin.com/in/satyanadella",
      "name": "Satya Nadella",
      "score": 92.5
    },
    ...
  ]
}
```

---

## Testing Phase 3: LinkedIn Recruiter Export

### Test Case 3.1: Export All Assessed Profiles

**Objective:** Generate CSV for LinkedIn Recruiter import

```bash
# Export all assessed profiles
curl -X GET "http://localhost:5001/lists/{list_id}/export-csv?recruiter_name=Jon" \
  -o test-export.csv

# Or with score filter (only top candidates)
curl -X GET "http://localhost:5001/lists/{list_id}/export-csv?min_score=85&recruiter_name=Jon" \
  -o test-export-top.csv
```

**Expected Results:**
- ✅ CSV file downloaded successfully
- ✅ Filename format: `test-senior-engineers-2024-10-24.csv`
- ✅ File size > 0 bytes

### Test Case 3.2: Verify CSV Format

**Open CSV in Text Editor:**
```csv
first_name,last_name,email,note,tags
Satya,Nadella,,"AI Score: 92/100. Strengths: Leadership Experience (9/10) Strategic Vision (10/10). LinkedIn: https://www.linkedin.com/in/satyanadella. Assessed: 2024-10-24","Test Senior Engineers,2024-10-24"
Jeff,Weiner,,"AI Score: 87/100. Strengths: Leadership Experience (8/10) Strategic Vision (9/10). LinkedIn: https://www.linkedin.com/in/jeffweiner08. Assessed: 2024-10-24","Test Senior Engineers,2024-10-24"
```

**Verification Checklist:**
- ✅ Headers: `first_name,last_name,email,note,tags`
- ✅ Names parsed correctly (first_name, last_name)
- ✅ Email field is empty (as expected)
- ✅ Note contains: Score, Strengths, LinkedIn URL, Date
- ✅ Tags contain: List name, Export date
- ✅ Quotes around note field (contains commas)

### Test Case 3.3: Verify Export Tracking

**Check Extension Profiles Table:**
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/extension_profiles?list_id=eq.{list_id}&select=exported_to_recruiter,exported_at" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"

# All exported profiles should have:
# - exported_to_recruiter: true
# - exported_at: (timestamp)
```

**Check Recruiter Exports Table:**
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/recruiter_exports?list_id=eq.{list_id}&select=*" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"

# Should show export record with:
# - candidate_count: 5 (or filtered count)
# - min_score_filter: 85 (if used)
# - csv_filename: "test-senior-engineers-2024-10-24.csv"
# - exported_by: "Jon"
# - exported_at: (timestamp)
```

### Test Case 3.4: Import into LinkedIn Recruiter

**⚠️ IMPORTANT:** This requires a LinkedIn Recruiter account and should be done carefully.

**Steps:**
1. Log into LinkedIn Recruiter: https://www.linkedin.com/talent/
2. Open or create a project
3. Click "Add candidates" button
4. Select "Import from file"
5. Choose the exported CSV file
6. Click "Import"

**Expected Results:**
- ✅ LinkedIn recognizes CSV format
- ✅ Candidates are matched by name
- ✅ Notes appear in candidate profiles
- ✅ Tags are applied to candidates

**Verification:**
- Check that AI scores appear in notes
- Verify LinkedIn URLs are clickable
- Confirm tags help organize candidates

---

## API Testing with curl

### Complete API Test Suite

```bash
# 1. Check authentication
curl http://localhost:5001/extension/auth

# 2. Create list
curl -X POST http://localhost:5001/extension/create-list \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test List",
    "description": "Created via API testing",
    "recruiter_name": "Jon"
  }'

# 3. Get all lists
curl "http://localhost:5001/extension/lists?recruiter_name=Jon"

# 4. Add profile (manual)
curl -X POST http://localhost:5001/extension/add-profile \
  -H "Content-Type: application/json" \
  -d '{
    "list_id": "your-list-uuid",
    "linkedin_url": "https://www.linkedin.com/in/satyanadella",
    "name": "Satya Nadella",
    "headline": "Chairman and CEO at Microsoft",
    "location": "Redmond, Washington, United States",
    "current_company": "Microsoft",
    "current_title": "Chairman and CEO",
    "added_by": "Jon"
  }'

# 5. Get profiles in list
curl "http://localhost:5001/extension/profiles/your-list-uuid"

# 6. Get list stats
curl "http://localhost:5001/extension/lists/your-list-uuid/stats"

# 7. Assess all profiles
curl -X POST "http://localhost:5001/lists/your-list-uuid/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {"name": "Leadership", "description": "C-level experience", "weight": 40},
      {"name": "Strategy", "description": "Vision and growth", "weight": 30}
    ]
  }'

# 8. Export to CSV
curl "http://localhost:5001/lists/your-list-uuid/export-csv?min_score=80" \
  -o export.csv

# 9. Update profile status
curl -X PUT "http://localhost:5001/extension/profiles/your-profile-uuid/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'

# 10. Update list details
curl -X PUT "http://localhost:5001/extension/lists/your-list-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated List Name",
    "description": "Updated description"
  }'

# 11. Delete list (archive)
curl -X DELETE "http://localhost:5001/extension/lists/your-list-uuid"
```

---

## Database Verification

### Direct SQL Queries (Supabase Dashboard)

**Check recruiter_lists table:**
```sql
SELECT
  id,
  list_name,
  recruiter_name,
  profile_count,
  assessed_count,
  created_at
FROM recruiter_lists
WHERE is_active = true
ORDER BY created_at DESC;
```

**Check extension_profiles table:**
```sql
SELECT
  id,
  linkedin_url,
  name,
  headline,
  assessed,
  assessment_score,
  status,
  exported_to_recruiter,
  added_at
FROM extension_profiles
WHERE list_id = 'your-list-uuid'
ORDER BY assessment_score DESC NULLS LAST;
```

**Check candidate_assessments table:**
```sql
SELECT
  id,
  linkedin_url,
  weighted_score,
  assessment_type,
  created_at
FROM candidate_assessments
WHERE assessment_type = 'batch'
ORDER BY created_at DESC
LIMIT 10;
```

**Check recruiter_exports table:**
```sql
SELECT
  id,
  list_id,
  exported_by,
  candidate_count,
  min_score_filter,
  csv_filename,
  exported_at
FROM recruiter_exports
ORDER BY exported_at DESC;
```

**Verify linking between tables:**
```sql
SELECT
  ep.name,
  ep.assessed,
  ep.assessment_score,
  ca.weighted_score,
  ca.created_at
FROM extension_profiles ep
LEFT JOIN candidate_assessments ca ON ep.assessment_id = ca.id
WHERE ep.list_id = 'your-list-uuid'
ORDER BY ep.assessment_score DESC NULLS LAST;
```

---

## Troubleshooting

### Issue: Extension won't load

**Symptoms:**
- Extension shows errors in `chrome://extensions/`
- Service worker fails to register

**Solutions:**
1. Check Chrome version (requires 88+)
2. Verify all files are present in `chrome-extension/` folder
3. Check `manifest.json` for syntax errors
4. Look for errors in service worker console
5. Try reloading the extension

### Issue: Can't add profiles to list

**Symptoms:**
- "Add to List" button doesn't work
- No success badge appears
- Console shows API errors

**Solutions:**
1. Verify backend is running: `curl http://localhost:5001/extension/auth`
2. Check extension settings: Backend URL should be `http://localhost:5001`
3. Verify you're on a LinkedIn profile page (not search results)
4. Check CORS settings in Flask backend
5. Look for errors in browser console and backend logs

### Issue: Assessment fails

**Symptoms:**
- POST /lists/{id}/assess returns errors
- Profiles remain unassessed
- Backend logs show API errors

**Solutions:**
1. Verify `ANTHROPIC_API_KEY` is set and valid
2. Verify `CORESIGNAL_API_KEY` is set and valid
3. Check API credit balances (both services)
4. Verify LinkedIn URLs are valid and profiles are public
5. Check backend logs for specific error messages
6. Try assessing a single profile first to isolate issue

### Issue: CSV export is empty or malformed

**Symptoms:**
- CSV file is 0 bytes
- CSV has incorrect format
- Missing data in CSV fields

**Solutions:**
1. Verify profiles are assessed: `assessed=true` in database
2. Check that assessment data exists in `candidate_assessments` table
3. Verify foreign key links: `assessment_id` is not null
4. Try exporting without `min_score` filter first
5. Check backend logs for export errors
6. Verify list_id is correct

### Issue: LinkedIn Recruiter won't import CSV

**Symptoms:**
- LinkedIn rejects CSV file
- Import fails silently
- Candidates don't appear in project

**Solutions:**
1. Verify CSV format matches LinkedIn's requirements
2. Check that CSV has correct headers: `first_name,last_name,email,note,tags`
3. Ensure note field is properly quoted (contains commas)
4. Verify file encoding is UTF-8
5. Try importing a smaller CSV first (1-2 candidates)
6. Check LinkedIn Recruiter documentation for format changes

### Issue: Database connection errors

**Symptoms:**
- Backend logs show Supabase errors
- 401 Unauthorized responses
- Connection timeouts

**Solutions:**
1. Verify `SUPABASE_URL` is correct
2. Verify `SUPABASE_KEY` is correct (use anon/service key, not JWT)
3. Check Supabase project is active (not paused)
4. Verify RLS policies allow anon role access
5. Check network connectivity to Supabase
6. Review Supabase logs for errors

---

## Performance Testing

### Benchmark: Batch Assessment Speed

**Test:** Assess 50 profiles

**Expected Performance:**
- Render deployment: ~2-3 minutes (50 concurrent workers)
- Heroku deployment: ~5-7 minutes (15 concurrent workers)
- Local development: ~3-5 minutes (default 50 workers)

**Measurement:**
```bash
time curl -X POST "http://localhost:5001/lists/{list_id}/assess" \
  -H "Content-Type: application/json" \
  -d '{"requirements": [...]}'
```

### Benchmark: CSV Export Speed

**Test:** Export 50 assessed profiles

**Expected Performance:**
- Should complete in < 10 seconds
- Includes database queries + CSV generation + profile marking

**Measurement:**
```bash
time curl -X GET "http://localhost:5001/lists/{list_id}/export-csv" \
  -o export.csv
```

---

## Test Data Cleanup

### Clean up test data after testing:

```bash
# Delete test lists (will cascade to extension_profiles)
curl -X DELETE "http://localhost:5001/extension/lists/{list_id}"

# Or via Supabase SQL:
DELETE FROM recruiter_lists WHERE list_name LIKE 'Test%';
DELETE FROM extension_profiles WHERE list_id IS NULL;
DELETE FROM candidate_assessments WHERE assessment_type = 'batch' AND linkedin_url LIKE '%test%';
DELETE FROM recruiter_exports WHERE exported_by = 'Jon' AND notes LIKE '%test%';
```

---

## Next Steps

After completing all tests:

1. ✅ Verify all endpoints work as expected
2. ✅ Confirm data flows correctly through all three stages
3. ✅ Test CSV imports into LinkedIn Recruiter successfully
4. ✅ Document any issues or edge cases discovered
5. ✅ Commit all working code to repository
6. 🚀 Deploy to production (Render)

---

**Last Updated:** October 24, 2024
**Version:** 1.0.0
