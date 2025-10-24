-- Migration: Add Assessment Tracking Fields to extension_profiles
-- Date: 2024-10-24
-- Description: Adds fields to track assessment status and LinkedIn Recruiter exports

-- Add assessment tracking fields to extension_profiles
ALTER TABLE extension_profiles
ADD COLUMN IF NOT EXISTS assessed BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS assessment_id UUID REFERENCES candidate_assessments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS assessment_score FLOAT,
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS exported_to_recruiter BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS exported_at TIMESTAMP WITH TIME ZONE;

-- Add index for filtering by assessment status
CREATE INDEX IF NOT EXISTS idx_extension_profiles_assessed ON extension_profiles(assessed, assessment_score DESC);

-- Add index for filtering by status
CREATE INDEX IF NOT EXISTS idx_extension_profiles_status ON extension_profiles(status, added_at DESC);

-- Add index for exported profiles
CREATE INDEX IF NOT EXISTS idx_extension_profiles_exported ON extension_profiles(exported_to_recruiter, exported_at DESC);

-- Create recruiter_exports table for tracking exports
CREATE TABLE IF NOT EXISTS recruiter_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_id UUID REFERENCES recruiter_lists(id) ON DELETE CASCADE,
  job_template_id UUID REFERENCES job_templates(id) ON DELETE SET NULL,
  exported_by VARCHAR(255),
  candidate_count INTEGER DEFAULT 0,
  min_score_filter FLOAT,
  csv_filename VARCHAR(255),
  exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_recruiter_exports_list ON recruiter_exports(list_id, exported_at DESC);
CREATE INDEX IF NOT EXISTS idx_recruiter_exports_by ON recruiter_exports(exported_by, exported_at DESC);

-- Update the list counts function to include assessed count
CREATE OR REPLACE FUNCTION update_list_counts(list_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE recruiter_lists
    SET
        profile_count = (SELECT COUNT(*) FROM extension_profiles WHERE list_id = list_uuid),
        assessed_count = (SELECT COUNT(*) FROM extension_profiles WHERE list_id = list_uuid AND assessed = true)
    WHERE id = list_uuid;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE recruiter_exports IS 'Tracks CSV exports to LinkedIn Recruiter';
COMMENT ON COLUMN extension_profiles.assessed IS 'Whether full AI assessment has been run';
COMMENT ON COLUMN extension_profiles.assessment_id IS 'Links to full assessment in candidate_assessments table';
COMMENT ON COLUMN extension_profiles.assessment_score IS 'Cached score for quick filtering';
COMMENT ON COLUMN extension_profiles.status IS 'Pipeline status: pending, assessed, exported, contacted, rejected';
COMMENT ON COLUMN extension_profiles.exported_to_recruiter IS 'Whether exported to LinkedIn Recruiter';
COMMENT ON COLUMN extension_profiles.exported_at IS 'When exported to LinkedIn Recruiter';