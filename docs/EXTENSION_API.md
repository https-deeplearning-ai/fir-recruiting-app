# Chrome Extension API Documentation

This document describes the API endpoints used by the LinkedIn Profile AI Assessor Chrome extension.

## Table of Contents

1. [Authentication](#authentication)
2. [List Management](#list-management)
3. [Profile Management](#profile-management)
4. [Assessment Operations](#assessment-operations)
5. [Export Operations](#export-operations)

---

## Authentication

### Check Authentication
**Endpoint:** `GET /extension/auth`

Simple endpoint to verify API connectivity and authentication.

**Response:**
```json
{
  "authenticated": true,
  "message": "Extension API ready"
}
```

---

## List Management

### Get All Lists
**Endpoint:** `GET /extension/lists`

Get all recruiter lists for a specific recruiter.

**Query Parameters:**
- `recruiter_name` (required): Name of the recruiter

**Response:**
```json
{
  "lists": [
    {
      "id": "uuid",
      "name": "Senior Backend Engineers",
      "description": "Candidates for backend role",
      "recruiter_name": "Jon",
      "profile_count": 15,
      "assessed_count": 8,
      "created_at": "2024-10-24T10:00:00Z",
      "updated_at": "2024-10-24T15:30:00Z"
    }
  ]
}
```

### Create New List
**Endpoint:** `POST /extension/create-list`

Create a new recruiter list.

**Request Body:**
```json
{
  "name": "Senior Frontend Engineers",
  "description": "React/TypeScript experts",
  "recruiter_name": "Jon",
  "job_template_id": "uuid (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "list_id": "uuid",
  "message": "List created successfully"
}
```

### Update List
**Endpoint:** `PUT /extension/lists/<list_id>`

Update an existing list's details.

**Request Body:**
```json
{
  "name": "Updated List Name (optional)",
  "description": "Updated description (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "List updated successfully"
}
```

### Delete List
**Endpoint:** `DELETE /extension/lists/<list_id>`

Archive a list (soft delete).

**Response:**
```json
{
  "success": true,
  "message": "List archived successfully"
}
```

### Get List Statistics
**Endpoint:** `GET /extension/lists/<list_id>/stats`

Get detailed statistics for a specific list.

**Response:**
```json
{
  "list_id": "uuid",
  "total_profiles": 20,
  "assessed_profiles": 15,
  "by_status": {
    "pending": 5,
    "assessed": 12,
    "exported": 3
  },
  "score_distribution": {
    "90-100": 2,
    "80-89": 5,
    "70-79": 6,
    "60-69": 2
  },
  "avg_score": 78.5,
  "top_profiles": [
    {
      "linkedin_url": "https://www.linkedin.com/in/johndoe",
      "name": "John Doe",
      "score": 92.5
    }
  ]
}
```

---

## Profile Management

### Add Profile to List
**Endpoint:** `POST /extension/add-profile`

Quick-add a profile to a list from the Chrome extension.

**Request Body:**
```json
{
  "list_id": "uuid",
  "linkedin_url": "https://www.linkedin.com/in/johndoe",
  "name": "John Doe",
  "headline": "Senior Software Engineer at Tech Corp",
  "location": "San Francisco, CA",
  "current_company": "Tech Corp",
  "current_title": "Senior Software Engineer",
  "profile_data": {
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "added_by": "Jon"
}
```

**Response:**
```json
{
  "success": true,
  "profile_id": "uuid",
  "message": "Profile added to list",
  "is_duplicate": false
}
```

**Notes:**
- If profile already exists in list, it will be updated with new data
- Returns `is_duplicate: true` if profile was already in the list

### Get Profiles in List
**Endpoint:** `GET /extension/profiles/<list_id>`

Get all profiles in a specific list with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (pending, assessed, exported)
- `assessed` (optional): Filter by assessment status (true/false)
- `min_score` (optional): Minimum assessment score

**Response:**
```json
{
  "profiles": [
    {
      "id": "uuid",
      "linkedin_url": "https://www.linkedin.com/in/johndoe",
      "name": "John Doe",
      "headline": "Senior Software Engineer",
      "location": "San Francisco, CA",
      "current_company": "Tech Corp",
      "current_title": "Senior Software Engineer",
      "assessed": true,
      "assessment_score": 87.5,
      "status": "assessed",
      "added_at": "2024-10-24T10:00:00Z",
      "exported_to_recruiter": false
    }
  ]
}
```

### Update Profile Status
**Endpoint:** `PUT /extension/profiles/<profile_id>/status`

Update a profile's status in the pipeline.

**Request Body:**
```json
{
  "status": "contacted"
}
```

**Valid Statuses:**
- `pending`: Not yet assessed
- `assessed`: Assessment completed
- `exported`: Exported to LinkedIn Recruiter
- `contacted`: Recruiter has reached out
- `rejected`: Not a good fit

**Response:**
```json
{
  "success": true,
  "message": "Profile status updated"
}
```

---

## Assessment Operations

### Assess All Profiles in List
**Endpoint:** `POST /lists/<list_id>/assess`

**⭐ NEW ENDPOINT** - Triggers batch AI assessment for all unassessed profiles in a list.

**Request Body:**
```json
{
  "requirements": [
    {
      "name": "Backend Experience",
      "description": "5+ years Python/Flask",
      "weight": 30
    },
    {
      "name": "System Design",
      "description": "Scalable architecture experience",
      "weight": 25
    }
  ],
  "job_description": "Optional job description text"
}
```

**Process Flow:**
1. Fetches all unassessed profiles from the list (`assessed=false`)
2. Formats profiles as candidates array with LinkedIn URLs
3. Calls existing `/batch-assess-profiles` endpoint internally
4. Uses CoreSignal API to fetch full profile data
5. Uses Claude AI to generate weighted assessments
6. Links assessment results back to `extension_profiles` table
7. Updates `assessed=true`, `assessment_id`, and `assessment_score`

**Response:**
```json
{
  "success": true,
  "total_profiles": 20,
  "assessed": 18,
  "failed": 2,
  "avg_score": 78.5,
  "results": [
    {
      "url": "https://www.linkedin.com/in/johndoe",
      "name": "John Doe",
      "score": 87.5,
      "assessment_id": "uuid"
    }
  ],
  "errors": [
    {
      "url": "https://www.linkedin.com/in/error",
      "error": "Profile not found"
    }
  ]
}
```

**Performance:**
- Uses high-concurrency batch processing (50 workers on Render, 15 on Heroku)
- Processes 100 profiles in ~2-3 minutes (depending on infrastructure)
- Automatic timeout protection per profile (60s Render, 25s Heroku)

**Notes:**
- Only processes profiles where `assessed=false`
- Reuses existing batch assessment infrastructure for reliability
- Stores full assessment data in `candidate_assessments` table
- Links back to `extension_profiles` via `assessment_id` foreign key

---

## Export Operations

### Export List to LinkedIn Recruiter CSV
**Endpoint:** `GET /lists/<list_id>/export-csv`

**⭐ NEW ENDPOINT** - Exports assessed profiles as CSV for LinkedIn Recruiter import.

**Query Parameters:**
- `min_score` (optional): Minimum score filter (e.g., 75 to export only top candidates)
- `recruiter_name` (optional): Name of recruiter for tracking
- `notes` (optional): Additional notes about this export

**Response:**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="list-name-2024-10-24.csv"`

**CSV Format:**
```csv
first_name,last_name,email,note,tags
John,Doe,,AI Score: 87/100. Strengths: Backend (9/10) System Design (8/10). LinkedIn: https://www.linkedin.com/in/johndoe. Assessed: 2024-10-24,"Senior Backend Engineers,2024-10-24"
```

**CSV Columns:**
- `first_name`: Parsed from profile name
- `last_name`: Parsed from profile name
- `email`: Empty (not publicly available on LinkedIn)
- `note`: Rich text with AI score, strengths, LinkedIn URL, assessment date
- `tags`: List name and export date (comma-separated)

**Process Flow:**
1. Fetches assessed profiles from list (with optional score filter)
2. Queries full assessment data from `candidate_assessments` table
3. Extracts requirement scores and analysis from assessment JSON
4. Formats note field with score, top strengths, LinkedIn URL
5. Marks all exported profiles with `exported_to_recruiter=true` and timestamp
6. Records export in `recruiter_exports` table for tracking
7. Returns CSV file as download

**LinkedIn Recruiter Import:**
After downloading the CSV, recruiters can import it into LinkedIn Recruiter:
1. Open LinkedIn Recruiter project
2. Click "Add candidates" → "Import from file"
3. Select the downloaded CSV file
4. LinkedIn will match candidates by name and create project entries
5. Notes and tags will be preserved in the project

**Tracking:**
The export is recorded in `recruiter_exports` table:
```sql
INSERT INTO recruiter_exports (
  list_id,
  exported_by,
  candidate_count,
  min_score_filter,
  csv_filename,
  notes
) VALUES (...)
```

**Notes:**
- Only exports profiles where `assessed=true`
- Can filter by minimum score to export only top candidates
- Marks profiles as exported to prevent duplicate exports
- Export history is tracked for audit purposes
- CSV format matches LinkedIn Recruiter's import specification

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message describing what went wrong",
  "details": "Optional additional details for debugging"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

**CoreSignal API Limits:**
- Profile fetches: Rate limited by CoreSignal (typically 100 requests/minute)
- Company data: Rate limited by CoreSignal

**Batch Assessment Limits:**
- Render deployment: 50 concurrent workers, 60s timeout per profile
- Heroku deployment: 15 concurrent workers, 25s timeout per profile
- Configured in `config.py` based on `RENDER` environment variable

**Best Practices:**
- For lists with 100+ profiles, assessment may take 3-5 minutes
- Consider breaking very large lists into smaller batches
- Monitor backend logs for rate limit warnings

---

## Complete Workflow Example

### 1. Extension User Bookmarks Profile
```javascript
// User clicks "Add to List" in Chrome extension
const response = await fetch('http://localhost:5001/extension/add-profile', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    list_id: 'uuid',
    linkedin_url: 'https://www.linkedin.com/in/johndoe',
    name: 'John Doe',
    headline: 'Senior Software Engineer',
    location: 'San Francisco, CA',
    // ... other profile data extracted from DOM
    added_by: 'Jon'
  })
});
```

### 2. Recruiter Assesses All Profiles in Web App
```javascript
// User clicks "Assess All" button in React frontend
const response = await fetch(`http://localhost:5001/lists/${listId}/assess`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    requirements: [
      { name: 'Backend Experience', description: '5+ years Python/Flask', weight: 30 },
      { name: 'System Design', description: 'Scalable systems', weight: 25 }
    ]
  })
});

// Response shows progress and results
const { total_profiles, assessed, avg_score } = await response.json();
```

### 3. Recruiter Exports to LinkedIn Recruiter
```javascript
// User clicks "Export to LinkedIn Recruiter" with score filter
window.location.href = `http://localhost:5001/lists/${listId}/export-csv?min_score=75&recruiter_name=Jon`;

// Browser downloads CSV file: "senior-backend-engineers-2024-10-24.csv"
```

### 4. Import into LinkedIn Recruiter (Manual)
- Open LinkedIn Recruiter project
- Click "Add candidates" → "Import from file"
- Select downloaded CSV
- LinkedIn matches candidates and imports with notes/tags

---

## Database Schema

### extension_profiles Table
```sql
CREATE TABLE extension_profiles (
  id UUID PRIMARY KEY,
  list_id UUID REFERENCES recruiter_lists(id),
  linkedin_url TEXT UNIQUE,
  name VARCHAR(255),
  headline TEXT,
  location VARCHAR(255),
  current_company VARCHAR(255),
  current_title VARCHAR(255),
  profile_data JSONB,

  -- Assessment tracking (NEW)
  assessed BOOLEAN DEFAULT false,
  assessment_id UUID REFERENCES candidate_assessments(id),
  assessment_score FLOAT,
  status VARCHAR(50) DEFAULT 'pending',

  -- Export tracking (NEW)
  exported_to_recruiter BOOLEAN DEFAULT false,
  exported_at TIMESTAMP WITH TIME ZONE,

  added_by VARCHAR(255),
  added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### recruiter_exports Table (NEW)
```sql
CREATE TABLE recruiter_exports (
  id UUID PRIMARY KEY,
  list_id UUID REFERENCES recruiter_lists(id),
  job_template_id UUID REFERENCES job_templates(id),
  exported_by VARCHAR(255),
  candidate_count INTEGER,
  min_score_filter FLOAT,
  csv_filename VARCHAR(255),
  exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT
);
```

---

**Last Updated:** October 24, 2024
**Version:** 1.0.0
