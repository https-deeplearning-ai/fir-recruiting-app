-- ============================================================================
-- UNIFIED PROFILE CACHE TABLE
-- ============================================================================
-- Purpose: Merge stored_profiles and stored_profiles_by_employee_id into ONE table
--          with BOTH lookup columns (linkedin_url AND employee_id)
--
-- Benefits:
--   - Eliminate duplication (~462 profiles currently in both tables)
--   - Simpler lookups (one table, two indexes)
--   - Better data model (one profile = one row)
--   - Save storage (~90MB, ~464 rows)
--
-- Date: 2025-11-12
-- ============================================================================

-- STEP 1: Create unified table with both lookup columns
CREATE TABLE IF NOT EXISTS stored_profiles_unified (
    id BIGSERIAL PRIMARY KEY,

    -- Lookup fields (at least one required)
    linkedin_url TEXT UNIQUE,           -- LinkedIn profile URL (nullable)
    employee_id BIGINT UNIQUE,          -- CoreSignal employee ID (nullable)

    -- Profile data
    profile_data JSONB NOT NULL,        -- Complete CoreSignal profile (59 fields)

    -- Metadata
    checked_at TIMESTAMP,               -- When CoreSignal last checked this profile
    last_fetched TIMESTAMP DEFAULT NOW(),  -- When we last fetched from cache
    created_at TIMESTAMP DEFAULT NOW(),    -- When row was created
    updated_at TIMESTAMP DEFAULT NOW(),    -- When row was last updated

    -- Constraint: At least one identifier must exist
    CONSTRAINT has_identifier CHECK (
        linkedin_url IS NOT NULL OR employee_id IS NOT NULL
    ),

    -- Constraint: If both exist, they must match the same profile
    -- (This is enforced by merge logic, not DB constraint)

    -- Note: UNIQUE constraints on nullable columns work in PostgreSQL
    -- NULL != NULL, so multiple NULLs are allowed
    CONSTRAINT linkedin_url_unique UNIQUE (linkedin_url),
    CONSTRAINT employee_id_unique UNIQUE (employee_id)
);

-- STEP 2: Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_stored_profiles_unified_linkedin_url
    ON stored_profiles_unified(linkedin_url)
    WHERE linkedin_url IS NOT NULL;  -- Partial index (more efficient)

CREATE INDEX IF NOT EXISTS idx_stored_profiles_unified_employee_id
    ON stored_profiles_unified(employee_id)
    WHERE employee_id IS NOT NULL;   -- Partial index (more efficient)

-- STEP 3: Create index on JSONB for common queries
CREATE INDEX IF NOT EXISTS idx_stored_profiles_unified_full_name
    ON stored_profiles_unified((profile_data->>'full_name'));

-- STEP 4: Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stored_profiles_unified_updated_at
    BEFORE UPDATE ON stored_profiles_unified
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
--
-- This SQL creates the table structure only.
-- Data migration is handled by Python script: migrate_to_unified_table.py
--
-- Migration logic:
--   1. Fetch all from stored_profiles_by_employee_id (464 rows)
--   2. Extract linkedin_url from profile_data
--   3. Check if linkedin_url already exists in stored_profiles
--   4. If match found: INSERT with BOTH linkedin_url AND employee_id
--   5. If no match: INSERT with employee_id ONLY
--   6. Fetch remaining from stored_profiles (not already inserted)
--   7. INSERT with linkedin_url ONLY
--
-- Expected result: ~510 rows total
--   - ~462 rows with BOTH identifiers (matched)
--   - ~48 rows with linkedin_url ONLY (no employee_id)
--   - ~2 rows with employee_id ONLY (no linkedin_url)
--
-- ============================================================================

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count rows by identifier type
-- (Run after migration completes)
/*
SELECT
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL AND employee_id IS NOT NULL) as both_identifiers,
    COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL AND employee_id IS NULL) as url_only,
    COUNT(*) FILTER (WHERE linkedin_url IS NULL AND employee_id IS NOT NULL) as id_only
FROM stored_profiles_unified;
*/

-- Test lookup by LinkedIn URL
/*
SELECT
    linkedin_url,
    employee_id,
    profile_data->>'full_name' as name,
    profile_data->>'headline' as headline
FROM stored_profiles_unified
WHERE linkedin_url = 'https://www.linkedin.com/in/hylkedijkstra'
LIMIT 1;
*/

-- Test lookup by employee ID
/*
SELECT
    linkedin_url,
    employee_id,
    profile_data->>'full_name' as name,
    profile_data->>'headline' as headline
FROM stored_profiles_unified
WHERE employee_id = 75261
LIMIT 1;
*/

-- ============================================================================
-- CLEANUP (After verification, 7+ days later)
-- ============================================================================

-- Rename old tables as backups
/*
ALTER TABLE stored_profiles RENAME TO stored_profiles_OLD_backup;
ALTER TABLE stored_profiles_by_employee_id RENAME TO stored_profiles_by_employee_id_OLD_backup;
*/

-- Rename unified table to primary name
/*
ALTER TABLE stored_profiles_unified RENAME TO stored_profiles;
*/

-- Drop backups after confirmed working (optional)
/*
DROP TABLE stored_profiles_OLD_backup;
DROP TABLE stored_profiles_by_employee_id_OLD_backup;
*/
