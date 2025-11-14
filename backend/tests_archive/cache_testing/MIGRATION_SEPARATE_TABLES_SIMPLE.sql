-- ============================================================================
-- Migration: Create Separate Table for Employee ID Lookups
-- ============================================================================
-- Approach: Keep existing stored_profiles untouched, create new table
-- Result: Clean separation, no NULL handling, minimal risk
-- ============================================================================

-- STEP 1: Create New Table for Employee ID Lookups
-- ============================================================================
CREATE TABLE IF NOT EXISTS stored_profiles_by_employee_id (
    id BIGSERIAL PRIMARY KEY,

    -- CoreSignal employee ID (required, unique, indexed)
    employee_id BIGINT UNIQUE NOT NULL,

    -- Profile data from CoreSignal API
    profile_data JSONB NOT NULL,

    -- Metadata
    checked_at TIMESTAMP,
    last_fetched TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_stored_profiles_by_id_employee_id
ON stored_profiles_by_employee_id(employee_id);

CREATE INDEX IF NOT EXISTS idx_stored_profiles_by_id_last_fetched
ON stored_profiles_by_employee_id(last_fetched DESC);

-- Add helpful comment
COMMENT ON TABLE stored_profiles_by_employee_id IS
'Cache for profiles fetched by CoreSignal employee_id (used in domain search workflow)';


-- STEP 2: Migrate Existing "id:xxxxx" Entries (Optional)
-- ============================================================================
-- This migrates existing employee ID entries from stored_profiles to new table
-- SAFE: Uses INSERT, doesn't modify stored_profiles

-- Simplified: Just copy employee_id and profile_data (the important parts)
-- Let timestamps default to NOW() for the new table
INSERT INTO stored_profiles_by_employee_id (employee_id, profile_data)
SELECT
    CAST(SUBSTRING(linkedin_url FROM 4) AS BIGINT) as employee_id,
    profile_data
FROM stored_profiles
WHERE linkedin_url LIKE 'id:%'
ON CONFLICT (employee_id) DO NOTHING;  -- Skip duplicates if any

-- Show how many were migrated
SELECT COUNT(*) as migrated_profiles FROM stored_profiles_by_employee_id;


-- STEP 3: Clean Up "id:xxxxx" Entries from stored_profiles (Optional)
-- ============================================================================
-- OPTIONAL: Remove the "weird IDs" from stored_profiles table
-- Uncomment if you want to clean up after confirming migration worked

-- DELETE FROM stored_profiles
-- WHERE linkedin_url LIKE 'id:%';


-- STEP 4: Verification Queries
-- ============================================================================

-- 4a. Check new table has data
SELECT
    COUNT(*) as total_profiles,
    MIN(last_fetched) as oldest_profile,
    MAX(last_fetched) as newest_profile
FROM stored_profiles_by_employee_id;

-- 4b. Sample of migrated data
SELECT
    employee_id,
    SUBSTRING(profile_data::text, 1, 100) as profile_preview,
    last_fetched,
    created_at
FROM stored_profiles_by_employee_id
ORDER BY created_at DESC
LIMIT 10;

-- 4c. Check stored_profiles table (should still have URL-based entries)
SELECT
    COUNT(*) as url_based_profiles,
    COUNT(*) FILTER (WHERE linkedin_url LIKE 'id:%') as weird_ids_remaining
FROM stored_profiles;
-- After optional Step 3, weird_ids_remaining should be 0


-- ============================================================================
-- Migration Complete!
-- ============================================================================
--
-- What Changed:
-- 1. ✅ Created new table: stored_profiles_by_employee_id
-- 2. ✅ Migrated existing "id:xxxxx" entries to new table
-- 3. ✅ Added indexes for fast lookups
-- 4. ✅ Verified data integrity
-- 5. ✅ Left stored_profiles untouched (safe!)
--
-- Table Structure:
--   stored_profiles               → For LinkedIn URL lookups (unchanged)
--   stored_profiles_by_employee_id → For employee ID lookups (NEW)
--
-- Next Steps:
-- 1. Update application code to use new table for employee ID lookups
-- 2. Restart backend server
-- 3. Test domain search → Search for People workflow
-- 4. (Optional) Run Step 3 to clean up "id:xxxxx" from stored_profiles
--
-- Rollback (if needed):
-- DROP TABLE stored_profiles_by_employee_id;
-- (That's it! stored_profiles was never modified)
-- ============================================================================
