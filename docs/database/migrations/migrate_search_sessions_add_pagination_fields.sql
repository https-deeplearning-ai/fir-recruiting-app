-- Migration: Add pagination fields for search/collect pattern
-- Run this on existing databases to add the new fields
-- This enables progressive loading of up to 1000 candidates

-- Add new columns for employee ID pagination
ALTER TABLE search_sessions
ADD COLUMN IF NOT EXISTS employee_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
ADD COLUMN IF NOT EXISTS profiles_offset INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_employee_ids INTEGER DEFAULT 0;

-- Add comments for new fields
COMMENT ON COLUMN search_sessions.employee_ids IS 'All employee IDs from search endpoint (up to 1000), used for pagination';
COMMENT ON COLUMN search_sessions.profiles_offset IS 'Current offset for profile pagination (0, 20, 40, etc.)';
COMMENT ON COLUMN search_sessions.total_employee_ids IS 'Total count of employee IDs for progress tracking';

-- Verify migration
SELECT
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name = 'search_sessions'
AND column_name IN ('employee_ids', 'profiles_offset', 'total_employee_ids')
ORDER BY ordinal_position;
