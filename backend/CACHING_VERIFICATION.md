# Caching System Verification

**Date:** 2025-11-06
**Status:** ✅ PROPERLY IMPLEMENTED

## Overview

The application has a **3-tier caching system** to minimize API credit usage:

1. **Supabase Database Storage** (persistent, long-term)
2. **Session Memory Cache** (temporary, per server restart)
3. **Fresh API Calls** (only when needed)

---

## Profile Caching (Single Profile View)

### Storage Location
- **Table:** `stored_profiles` (Supabase)
- **Function:** `get_stored_profile()` / `save_stored_profile()`
- **File:** `backend/app.py` lines 204-341

### Caching Logic

**1. Check Supabase Database First**
```python
# app.py lines 1222-1243
if not force_refresh:
    stored_result = get_stored_profile(linkedin_url)
    if stored_result:
        # Use cached profile - SAVES 1 Collect API credit!
        profile_data = stored_result['profile_data']
```

**2. Fetch Fresh if Not Cached**
```python
# app.py lines 1246-1262
result = coresignal_service.fetch_linkedin_profile(linkedin_url)
profile_data = result['profile_data']

# Save to Supabase for next time
save_stored_profile(linkedin_url, profile_data, checked_at)
```

### Freshness Rules
- **Storage TTL:** 90 days
- **Refresh Logic:** If profile is >90 days old, fetch fresh
- **Force Refresh:** User can request `force_refresh=true` to bypass cache

---

## Company Enrichment Caching

### Storage Location
- **Table:** `stored_companies` (Supabase)
- **Function:** `get_stored_company()` / `save_stored_company()`
- **File:** `backend/app.py` lines 343-437

### Multi-Level Caching

**Level 1: Supabase Database (Persistent)**
```python
# coresignal_service.py lines 320-337
if storage_functions:
    stored_result = storage_functions['get'](company_id, freshness_days=30)
    if stored_result:
        # Use cached company - SAVES 1 Collect credit!
        self.company_cache[company_id] = result  # Also add to session cache
        return result
```

**Level 2: Session Memory Cache**
```python
# coresignal_service.py lines 339-342
if company_id in self.company_cache:
    # Already fetched this session - instant return
    return self.company_cache[company_id]
```

**Level 3: Fresh API Call**
```python
# coresignal_service.py lines 344-390
response = requests.get(
    f"https://api.coresignal.com/cdapi/v2/company_base/collect/{company_id}",
    headers=get_headers,
    timeout=10
)

# Save to BOTH caches
storage_functions['save'](company_id, company_data)  # Supabase
self.company_cache[company_id] = result  # Session memory
```

### Freshness Rules
- **Storage TTL:** 30 days (customizable via `freshness_days` parameter)
- **Session Cache:** Lives until server restart
- **Min Year Filter:** Only enriches companies from 2015+ (saves credits on old jobs)

---

## How It Works in Single Profile View

### Step-by-Step Flow

**1. User Submits LinkedIn URL**
```
POST /fetch-profile
{
  "linkedin_url": "https://www.linkedin.com/in/john-doe",
  "enrich_companies": true
}
```

**2. Profile Fetch (with caching)**
```
Check Supabase `stored_profiles` table
  ↓ NOT FOUND
Fetch from CoreSignal API (1 Collect credit)
  ↓
Save to Supabase for next time
  ↓
Return profile_data
```

**3. Company Enrichment (with 3-tier caching)**

For each company in work experience (2015+):
```
Company ID: 12345
  ↓
Check Supabase `stored_companies` (freshness: 30 days)
  ↓ NOT FOUND
Check Session Cache (self.company_cache)
  ↓ NOT FOUND
Fetch from CoreSignal /company_base/collect (1 Collect credit)
  ↓
Save to Supabase (persistent)
  ↓
Save to Session Cache (temporary)
  ↓
Return enriched data
```

**4. Same Profile Fetched Again (within 90 days)**
```
Check Supabase `stored_profiles`
  ↓ FOUND! (age: 5 days)
Use cached profile (0 API credits)
  ↓
For each company:
  Check Supabase `stored_companies`
    ↓ FOUND! (age: 10 days)
  Use cached company (0 API credits)
    ↓
  Also add to Session Cache
    ↓
Return enriched profile (TOTAL: 0 API credits!)
```

---

## Cache Hit Scenarios

### Scenario 1: First Time View
- **Profile:** ❌ Not cached → Fetch (1 credit)
- **Companies (5 jobs):** ❌ Not cached → Fetch each (5 credits)
- **Total:** 6 API credits

### Scenario 2: Second View (Same Session)
- **Profile:** ✅ Cached in Supabase → Use cache (0 credits)
- **Companies:** ✅ Cached in Session Memory → Instant (0 credits)
- **Total:** 0 API credits

### Scenario 3: New Session, Within 30 Days
- **Profile:** ✅ Cached in Supabase (0 credits)
- **Companies:** ✅ Cached in Supabase (0 credits)
- **Total:** 0 API credits

### Scenario 4: After 90 Days (Profile Stale)
- **Profile:** ⚠️ Stale → Fetch fresh (1 credit)
- **Companies:** Check individual freshness
  - If <30 days: ✅ Cached (0 credits)
  - If >30 days: ❌ Fetch fresh (1 credit each)

---

## Verification Checklist

### ✅ Profile Caching Works
- [x] `get_stored_profile()` checks Supabase first (line 204)
- [x] `save_stored_profile()` saves after API fetch (line 314)
- [x] 90-day TTL implemented (line 209)
- [x] `force_refresh` parameter bypasses cache (line 1209)

### ✅ Company Caching Works
- [x] Supabase check first (coresignal_service.py line 321)
- [x] Session cache second (line 340)
- [x] Fresh API call last (line 349)
- [x] Saves to BOTH caches (lines 385, 388)
- [x] 30-day TTL (line 323)

### ✅ Storage Functions Passed Correctly
- [x] `storage_functions` dict created (app.py line 1270)
- [x] Contains `get` and `save` functions (line 1271-1272)
- [x] Passed to `enrich_profile_with_company_data()` (line 1274)

---

## Monitoring Cache Effectiveness

### Console Logs to Watch

**Profile Cache Hit:**
```
🔍 Checking if profile is stored in database...
✅ Using stored profile (saves 1 Collect credit!)
```

**Profile Cache Miss:**
```
📦 Fetching fresh profile from CoreSignal...
💾 Saving profile to storage for future use...
```

**Company Cache Hit (Supabase):**
```
🔍 Checking if company 12345 is stored in database...
✅ Using stored company 12345 - SAVED 1 Collect credit!
```

**Company Cache Hit (Session):**
```
💾 Company 12345 found in session cache
```

**Company Cache Miss:**
```
🏢 Fetching fresh company data from CoreSignal for ID: 12345
💾 Saving company 12345 to storage for future use...
```

---

## Database Schema

### `stored_profiles` Table
```sql
CREATE TABLE stored_profiles (
  id SERIAL PRIMARY KEY,
  linkedin_url TEXT UNIQUE NOT NULL,
  employee_id TEXT,
  profile_data JSONB NOT NULL,
  checked_at TIMESTAMP,
  last_fetched TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### `stored_companies` Table
```sql
CREATE TABLE stored_companies (
  id SERIAL PRIMARY KEY,
  company_id TEXT UNIQUE NOT NULL,
  company_data JSONB NOT NULL,
  last_fetched TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Performance Benefits

### Without Caching (Every Request)
- Profile fetch: 1 Collect credit
- 10 companies: 10 Collect credits
- **Total per view:** 11 credits

### With Caching (Second+ View)
- Profile: 0 credits (from Supabase)
- 10 companies: 0 credits (from Supabase or Session)
- **Total per view:** 0 credits

### Monthly Savings Example
- 100 profile views
- Without cache: 1,100 credits
- With cache (50% hit rate): 550 credits
- **Savings:** 50% reduction in API usage

---

## Troubleshooting

### Issue: Cache Not Being Used

**Check 1: Verify Supabase Connection**
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**Check 2: Check Console Logs**
Look for "Checking if profile is stored" or "Using stored profile"

**Check 3: Verify Data in Supabase**
```sql
SELECT linkedin_url, last_fetched,
       EXTRACT(DAY FROM (NOW() - last_fetched)) as age_days
FROM stored_profiles;
```

### Issue: Companies Always Fetching Fresh

**Check 1: Verify storage_functions Passed**
Look for log: "Checking if company X is stored in database"

**Check 2: Check Freshness**
```sql
SELECT company_id, last_fetched,
       EXTRACT(DAY FROM (NOW() - last_fetched)) as age_days
FROM stored_companies
WHERE EXTRACT(DAY FROM (NOW() - last_fetched)) > 30;
```

---

## Conclusion

✅ **Profile caching is properly implemented**
- Uses Supabase for persistent storage
- 90-day TTL with force refresh option
- Saves 1 API credit per cached profile

✅ **Company caching has 3 tiers**
- Supabase (persistent, 30-day TTL)
- Session memory (fast, temporary)
- Fresh API (only when needed)

✅ **Storage functions correctly passed**
- Single profile view: lines 1270-1277
- Batch processing: Would need verification

The caching system is working as designed and will significantly reduce API credit usage for repeat profile views.
