-- Migration: Add source_tab column to recruiter_feedback table
-- Purpose: Track which tab/mode feedback was created in (single, batch, search, company_research)
-- Date: 2025-01-06

-- Add source_tab column with default value
ALTER TABLE recruiter_feedback
ADD COLUMN IF NOT EXISTS source_tab TEXT NOT NULL DEFAULT 'single'
CHECK (source_tab IN ('single', 'batch', 'search', 'company_research'));

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_source_tab
    ON recruiter_feedback(source_tab);

-- Add comment
COMMENT ON COLUMN recruiter_feedback.source_tab IS 'Tab/mode where feedback was created: single, batch, search, or company_research';

-- Verify migration
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'recruiter_feedback'
  AND column_name = 'source_tab';
