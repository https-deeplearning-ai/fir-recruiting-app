-- ============================================================================
-- Migration: Normalize stored_profiles Table
-- ============================================================================
-- Problem: linkedin_url column contains BOTH LinkedIn URLs AND employee IDs
--          Example: "id:12345678" is stored in linkedin_url column (WEIRD!)
--
-- Solution: Add separate employee_id column, migrate data, add constraints
-- ============================================================================

-- STEP 1: Backup Current Data
-- ============================================================================
CREATE TABLE IF NOT EXISTS stored_profiles_backup_20251112 AS
SELECT * FROM stored_profiles;

-- Verify backup
SELECT COUNT(*) as total_rows_backed_up FROM stored_profiles_backup_20251112;


-- STEP 2: Remove NOT NULL Constraint from linkedin_url
-- ============================================================================
-- This is required because employee_id-only entries will have NULL linkedin_url
ALTER TABLE stored_profiles
ALTER COLUMN linkedin_url DROP NOT NULL;

-- Verify constraint was dropped
SELECT
    column_name,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'stored_profiles'
  AND column_name = 'linkedin_url';
-- Expected: is_nullable = 'YES'


-- STEP 3: Add employee_id Column
-- ============================================================================
ALTER TABLE stored_profiles
ADD COLUMN IF NOT EXISTS employee_id BIGINT;


-- STEP 4: Migrate "id:xxxxx" Entries to employee_id Column
-- ============================================================================

-- 4a. Extract employee_id from "id:xxxxx" format
UPDATE stored_profiles
SET employee_id = CAST(SUBSTRING(linkedin_url FROM 4) AS BIGINT)
WHERE linkedin_url LIKE 'id:%';

-- Verify migration (show sample of migrated rows)
SELECT
    linkedin_url as old_linkedin_url_field,
    employee_id as new_employee_id_field,
    created_at
FROM stored_profiles
WHERE employee_id IS NOT NULL
LIMIT 10;

-- 4b. Clear linkedin_url for employee_id-only entries (NOW ALLOWED because NOT NULL was dropped)
UPDATE stored_profiles
SET linkedin_url = NULL
WHERE linkedin_url LIKE 'id:%';


-- STEP 5: Extract LinkedIn URL from profile_data (if available)
-- ============================================================================
-- For employee_id entries that have a LinkedIn URL in their profile_data,
-- populate the linkedin_url column

UPDATE stored_profiles
SET linkedin_url = profile_data->>'url'
WHERE employee_id IS NOT NULL
  AND linkedin_url IS NULL
  AND profile_data->>'url' IS NOT NULL
  AND profile_data->>'url' LIKE 'https://www.linkedin.com/in/%';

-- Alternative: Try professional_network field
UPDATE stored_profiles
SET linkedin_url = (profile_data->'websites_professional_network'->>0)
WHERE employee_id IS NOT NULL
  AND linkedin_url IS NULL
  AND profile_data->'websites_professional_network'->>0 IS NOT NULL
  AND profile_data->'websites_professional_network'->>0 LIKE 'https://www.linkedin.com/in/%';


-- STEP 6: Add Constraints and Indexes
-- ============================================================================

-- 6a. Create UNIQUE index on employee_id (allows NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_stored_profiles_employee_id_unique
ON stored_profiles(employee_id)
WHERE employee_id IS NOT NULL;

-- 6b. Ensure linkedin_url remains UNIQUE (allows NULL)
-- This index should already exist, but let's verify it
DROP INDEX IF EXISTS idx_stored_profiles_linkedin_url_unique;
CREATE UNIQUE INDEX idx_stored_profiles_linkedin_url_unique
ON stored_profiles(linkedin_url)
WHERE linkedin_url IS NOT NULL;

-- 6c. Add CHECK constraint (must have at least one identifier)
ALTER TABLE stored_profiles
DROP CONSTRAINT IF EXISTS check_has_identifier;

ALTER TABLE stored_profiles
ADD CONSTRAINT check_has_identifier
CHECK (employee_id IS NOT NULL OR linkedin_url IS NOT NULL);

-- 6d. Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_stored_profiles_employee_id
ON stored_profiles(employee_id);

CREATE INDEX IF NOT EXISTS idx_stored_profiles_linkedin_url
ON stored_profiles(linkedin_url);

CREATE INDEX IF NOT EXISTS idx_stored_profiles_last_fetched
ON stored_profiles(last_fetched DESC);


-- STEP 7: Verification Queries
-- ============================================================================

-- 7a. Count rows by identifier type
SELECT
    COUNT(*) FILTER (WHERE employee_id IS NOT NULL AND linkedin_url IS NOT NULL) as both_identifiers,
    COUNT(*) FILTER (WHERE employee_id IS NOT NULL AND linkedin_url IS NULL) as employee_id_only,
    COUNT(*) FILTER (WHERE employee_id IS NULL AND linkedin_url IS NOT NULL) as linkedin_url_only,
    COUNT(*) as total_rows
FROM stored_profiles;

-- 7b. Verify no "id:" entries remain in linkedin_url
SELECT COUNT(*) as weird_ids_remaining
FROM stored_profiles
WHERE linkedin_url LIKE 'id:%';
-- Expected: 0 (should be zero after migration)

-- 7c. Check for duplicates (same person stored twice)
SELECT
    employee_id,
    linkedin_url,
    COUNT(*) as duplicate_count
FROM stored_profiles
WHERE employee_id IS NOT NULL
GROUP BY employee_id, linkedin_url
HAVING COUNT(*) > 1;
-- Expected: 0 rows (no duplicates)

-- 7d. Sample of migrated data
SELECT
    id,
    employee_id,
    linkedin_url,
    SUBSTRING(profile_data::text, 1, 100) as profile_data_preview,
    last_fetched,
    created_at
FROM stored_profiles
ORDER BY created_at DESC
LIMIT 20;


-- STEP 8: Clean Up Old Entries (Optional - Uncomment if needed)
-- ============================================================================
-- WARNING: Only run this if you want to remove old cached profiles

-- Delete profiles older than 6 months (180 days)
-- DELETE FROM stored_profiles
-- WHERE last_fetched < NOW() - INTERVAL '180 days';

-- Verify deletion count before running:
-- SELECT COUNT(*) as profiles_to_delete
-- FROM stored_profiles
-- WHERE last_fetched < NOW() - INTERVAL '180 days';


-- ============================================================================
-- Migration Complete!
-- ============================================================================
--
-- What Changed:
-- 1. ✅ Created backup table
-- 2. ✅ Removed NOT NULL constraint from linkedin_url
-- 3. ✅ Added employee_id column (BIGINT, UNIQUE, indexed)
-- 4. ✅ Migrated "id:xxxxx" entries to employee_id column
-- 5. ✅ Cleared linkedin_url for employee_id-only entries (now allowed!)
-- 6. ✅ Extracted LinkedIn URLs from profile_data where available
-- 7. ✅ Added constraints (UNIQUE, CHECK, indexes)
-- 8. ✅ Verified data integrity
--
-- Next Steps:
-- 1. Run verification queries (Step 7) to confirm success
-- 2. Update application code (supabase_storage.py, app.py) - ALREADY DONE!
-- 3. Restart backend server
-- 4. Test with a few profile lookups
-- 5. Remove backup table after confirming everything works (1 week)
--
-- Rollback (if needed):
-- DROP TABLE stored_profiles;
-- ALTER TABLE stored_profiles_backup_20251112 RENAME TO stored_profiles;
-- git checkout backend/utils/supabase_storage.py backend/app.py
-- ============================================================================
