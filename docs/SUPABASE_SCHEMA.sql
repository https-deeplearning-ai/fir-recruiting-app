-- ============================================
-- SUPABASE DATABASE SCHEMA
-- LinkedIn Profile AI Assessor - Recruiter Tool
-- ============================================
-- Instructions:
-- 1. Go to Supabase Dashboard → SQL Editor
-- 2. Copy this entire file
-- 3. Run it to create all tables
-- ============================================

-- ============================================
-- TABLE 1: stored_profiles
-- Purpose: Store profile data to avoid redundant API calls
-- Freshness Rules:
--   - If < 3 days old: Use stored data (save 1 Collect credit)
--   - If 3-90 days old: Use stored BUT mark for background refresh
--   - If > 90 days old: Force fresh pull from CoreSignal
-- ============================================
CREATE TABLE IF NOT EXISTS stored_profiles (
    linkedin_url TEXT PRIMARY KEY,
    profile_data JSONB NOT NULL,
    last_fetched TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checked_at TEXT,  -- CoreSignal's last update timestamp
    keep_in_database BOOLEAN DEFAULT true,  -- If false, can be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster freshness checks
CREATE INDEX IF NOT EXISTS idx_stored_profiles_last_fetched
    ON stored_profiles(last_fetched DESC);
CREATE INDEX IF NOT EXISTS idx_stored_profiles_keep_in_database
    ON stored_profiles(keep_in_database) WHERE keep_in_database = false;

COMMENT ON TABLE stored_profiles IS 'Stores LinkedIn profile data from CoreSignal API to avoid redundant API calls';
COMMENT ON COLUMN stored_profiles.linkedin_url IS 'LinkedIn profile URL (unique identifier)';
COMMENT ON COLUMN stored_profiles.profile_data IS 'Full CoreSignal profile JSON (work history, education, skills, etc.)';
COMMENT ON COLUMN stored_profiles.last_fetched IS 'When we last fetched/updated this data from CoreSignal';
COMMENT ON COLUMN stored_profiles.checked_at IS 'CoreSignal''s checked_at timestamp showing their last scrape';
COMMENT ON COLUMN stored_profiles.keep_in_database IS 'If true, keep forever; if false, can be cleaned up';

-- ============================================
-- TABLE 2: stored_companies
-- Purpose: Store company data to avoid redundant API calls
-- Freshness Rules:
--   - If < 30 days old: Use stored data (save 1 Collect credit)
--   - If > 30 days old: Force fresh pull from CoreSignal
-- ============================================
CREATE TABLE IF NOT EXISTS stored_companies (
    company_id INTEGER PRIMARY KEY,
    company_data JSONB NOT NULL,
    last_fetched TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    keep_in_database BOOLEAN DEFAULT true,  -- If false, can be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster freshness checks
CREATE INDEX IF NOT EXISTS idx_stored_companies_last_fetched
    ON stored_companies(last_fetched DESC);
CREATE INDEX IF NOT EXISTS idx_stored_companies_keep_in_database
    ON stored_companies(keep_in_database) WHERE keep_in_database = false;

COMMENT ON TABLE stored_companies IS 'Stores company data from CoreSignal API to avoid redundant API calls';
COMMENT ON COLUMN stored_companies.company_id IS 'CoreSignal company ID (unique identifier)';
COMMENT ON COLUMN stored_companies.company_data IS 'Full CoreSignal company JSON (funding, growth, employees, etc.)';
COMMENT ON COLUMN stored_companies.last_fetched IS 'When we last fetched/updated this data from CoreSignal';
COMMENT ON COLUMN stored_companies.keep_in_database IS 'If true, keep forever; if false, can be cleaned up';

-- ============================================
-- TABLE 3: candidate_assessments
-- Purpose: Store AI assessment results
-- Features: Weighted scoring, custom requirements
-- ============================================
CREATE TABLE IF NOT EXISTS candidate_assessments (
    id SERIAL PRIMARY KEY,
    linkedin_url TEXT NOT NULL,
    full_name TEXT,
    headline TEXT,
    profile_data JSONB,
    assessment_data JSONB NOT NULL,
    weighted_score NUMERIC(4,2),
    overall_score NUMERIC(4,2),
    assessment_type TEXT CHECK (assessment_type IN ('single', 'batch')),
    session_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_candidate_assessments_linkedin_url
    ON candidate_assessments(linkedin_url);
CREATE INDEX IF NOT EXISTS idx_candidate_assessments_weighted_score
    ON candidate_assessments(weighted_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_assessments_created_at
    ON candidate_assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_assessments_session_name
    ON candidate_assessments(session_name);

COMMENT ON TABLE candidate_assessments IS 'Stores AI assessment results for candidates';
COMMENT ON COLUMN candidate_assessments.linkedin_url IS 'LinkedIn URL of the assessed candidate';
COMMENT ON COLUMN candidate_assessments.profile_data IS 'Full CoreSignal profile JSON';
COMMENT ON COLUMN candidate_assessments.assessment_data IS 'Complete AI assessment JSON';
COMMENT ON COLUMN candidate_assessments.weighted_score IS 'Final weighted score (0-10)';
COMMENT ON COLUMN candidate_assessments.overall_score IS 'Overall score before weighting (0-10)';
COMMENT ON COLUMN candidate_assessments.assessment_type IS 'Type: single or batch assessment';
COMMENT ON COLUMN candidate_assessments.session_name IS 'Optional grouping identifier for batch assessments';

-- ============================================
-- TABLE 4: recruiter_feedback
-- Purpose: Store recruiter notes, likes, dislikes
-- Features: Multi-recruiter support, auto-save
-- ============================================
CREATE TABLE IF NOT EXISTS recruiter_feedback (
    id SERIAL PRIMARY KEY,
    candidate_linkedin_url TEXT NOT NULL,
    feedback_text TEXT,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('like', 'dislike', 'note')),
    recruiter_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_linkedin_url
    ON recruiter_feedback(candidate_linkedin_url);
CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_created_at
    ON recruiter_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_recruiter_name
    ON recruiter_feedback(recruiter_name);

COMMENT ON TABLE recruiter_feedback IS 'Stores recruiter feedback (Jon/Mary) for candidates';
COMMENT ON COLUMN recruiter_feedback.candidate_linkedin_url IS 'LinkedIn URL of the candidate';
COMMENT ON COLUMN recruiter_feedback.feedback_text IS 'The note/comment text (nullable for like/dislike only)';
COMMENT ON COLUMN recruiter_feedback.feedback_type IS 'Type: like, dislike, or note';
COMMENT ON COLUMN recruiter_feedback.recruiter_name IS 'Who gave the feedback (Jon or Mary)';

-- ============================================
-- TRIGGERS: Auto-update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_stored_profiles_updated_at ON stored_profiles;
CREATE TRIGGER update_stored_profiles_updated_at
    BEFORE UPDATE ON stored_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_stored_companies_updated_at ON stored_companies;
CREATE TRIGGER update_stored_companies_updated_at
    BEFORE UPDATE ON stored_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_candidate_assessments_updated_at ON candidate_assessments;
CREATE TRIGGER update_candidate_assessments_updated_at
    BEFORE UPDATE ON candidate_assessments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_recruiter_feedback_updated_at ON recruiter_feedback;
CREATE TRIGGER update_recruiter_feedback_updated_at
    BEFORE UPDATE ON recruiter_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS) - CRITICAL!
-- ============================================
-- IMPORTANT: RLS policies control data access
-- We're using ANON KEY for API calls, so policies must allow anon role
-- ============================================

ALTER TABLE stored_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE stored_companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE recruiter_feedback ENABLE ROW LEVEL SECURITY;

-- Allow ANON role (API key) to do everything
-- This is safe since this is a single-user recruiter tool
DROP POLICY IF EXISTS "Allow anon access to stored_profiles" ON stored_profiles;
CREATE POLICY "Allow anon access to stored_profiles"
    ON stored_profiles FOR ALL
    TO anon
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon access to stored_companies" ON stored_companies;
CREATE POLICY "Allow anon access to stored_companies"
    ON stored_companies FOR ALL
    TO anon
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon access to candidate_assessments" ON candidate_assessments;
CREATE POLICY "Allow anon access to candidate_assessments"
    ON candidate_assessments FOR ALL
    TO anon
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon access to recruiter_feedback" ON recruiter_feedback;
CREATE POLICY "Allow anon access to recruiter_feedback"
    ON recruiter_feedback FOR ALL
    TO anon
    USING (true) WITH CHECK (true);

-- ============================================
-- UTILITY: Cleanup old temporary data
-- Run this periodically to clean up profiles/companies
-- marked with keep_in_database = false
-- ============================================
CREATE OR REPLACE FUNCTION cleanup_temporary_data()
RETURNS void AS $$
BEGIN
    -- Delete profiles older than 90 days that are marked as temporary
    DELETE FROM stored_profiles
    WHERE keep_in_database = false
      AND last_fetched < NOW() - INTERVAL '90 days';

    -- Delete companies older than 6 months that are marked as temporary
    DELETE FROM stored_companies
    WHERE keep_in_database = false
      AND last_fetched < NOW() - INTERVAL '6 months';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_temporary_data IS 'Deletes old temporary data. Run periodically via cron job.';

-- ============================================
-- VERIFICATION QUERIES
-- Run these after creating tables to verify
-- ============================================
-- Check that all 4 tables were created
SELECT table_name,
       (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('stored_profiles', 'stored_companies', 'candidate_assessments', 'recruiter_feedback')
ORDER BY table_name;

-- Verify RLS policies are set correctly (should show policies for anon role)
SELECT schemaname, tablename, policyname, roles
FROM pg_policies
WHERE tablename IN ('stored_profiles', 'stored_companies', 'candidate_assessments', 'recruiter_feedback')
ORDER BY tablename, policyname;
