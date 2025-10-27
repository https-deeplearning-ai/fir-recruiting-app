-- Migration: Add Enhancement Tables for LinkedIn Profile AI Assessor
-- Date: 2024-10-24
-- Description: Adds tables for Chrome extension, job templates, and company discovery features

-- =========================================
-- 1. RECRUITER LISTS
-- =========================================
-- Table for organizing candidates into lists
CREATE TABLE IF NOT EXISTS recruiter_lists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recruiter_name VARCHAR(255) NOT NULL,
  list_name VARCHAR(255) NOT NULL,
  description TEXT,
  job_template_id UUID, -- Will reference job_templates when created
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  profile_count INTEGER DEFAULT 0,
  assessed_count INTEGER DEFAULT 0,

  -- Indexes for performance
  CONSTRAINT unique_list_name_per_recruiter UNIQUE(recruiter_name, list_name)
);

CREATE INDEX idx_recruiter_lists_recruiter ON recruiter_lists(recruiter_name);
CREATE INDEX idx_recruiter_lists_active ON recruiter_lists(is_active, created_at DESC);

-- =========================================
-- 2. EXTENSION PROFILES
-- =========================================
-- Quick-add profiles from Chrome extension
CREATE TABLE IF NOT EXISTS extension_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  linkedin_url VARCHAR(500) UNIQUE NOT NULL,
  shorthand VARCHAR(255), -- e.g., "john-smith-123"
  name VARCHAR(255),
  headline TEXT,
  current_company VARCHAR(255),
  current_title VARCHAR(255),
  location VARCHAR(255),
  profile_picture_url TEXT,
  list_id UUID REFERENCES recruiter_lists(id) ON DELETE SET NULL,
  needs_full_fetch BOOLEAN DEFAULT true,
  last_fetched_at TIMESTAMP WITH TIME ZONE,
  added_via VARCHAR(50) DEFAULT 'extension',
  added_by VARCHAR(255),
  added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT,
  tags TEXT[],

  -- Quick assessment fields
  quick_score INTEGER,
  quick_assessed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_extension_profiles_list ON extension_profiles(list_id);
CREATE INDEX idx_extension_profiles_linkedin ON extension_profiles(linkedin_url);
CREATE INDEX idx_extension_profiles_needs_fetch ON extension_profiles(needs_full_fetch, last_fetched_at);

-- =========================================
-- 3. JOB TEMPLATES
-- =========================================
-- Store job descriptions and requirements
CREATE TABLE IF NOT EXISTS job_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  department VARCHAR(100),
  level VARCHAR(50), -- junior, mid, senior, staff, principal
  company_name VARCHAR(255),
  location VARCHAR(255),
  employment_type VARCHAR(50), -- full-time, part-time, contract

  -- Job details
  description TEXT,
  responsibilities TEXT,
  qualifications TEXT,

  -- AI-extracted fields (JSONB for flexibility)
  requirements JSONB, -- {required: [], preferred: [], nice_to_have: []}
  weighted_criteria JSONB, -- {criterion: weight_percentage}
  skills_required TEXT[],
  skills_preferred TEXT[],

  -- Experience requirements
  years_experience_min INTEGER,
  years_experience_max INTEGER,
  education_level VARCHAR(100),

  -- Additional context
  company_context TEXT,
  team_size INTEGER,
  reports_to VARCHAR(255),

  -- Metadata
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  is_public BOOLEAN DEFAULT false, -- Can be shared across recruiters

  -- Version control
  version INTEGER DEFAULT 1,
  parent_template_id UUID REFERENCES job_templates(id) ON DELETE SET NULL,

  -- Usage tracking
  times_used INTEGER DEFAULT 0,
  last_used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_job_templates_active ON job_templates(is_active, created_at DESC);
CREATE INDEX idx_job_templates_creator ON job_templates(created_by);
CREATE INDEX idx_job_templates_public ON job_templates(is_public, is_active);

-- =========================================
-- 4. JOB ASSESSMENTS
-- =========================================
-- Link assessments to specific job templates
CREATE TABLE IF NOT EXISTS job_assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_linkedin_url VARCHAR(500) NOT NULL,
  candidate_name VARCHAR(255),
  job_template_id UUID REFERENCES job_templates(id) ON DELETE CASCADE,

  -- Assessment results
  assessment_data JSONB, -- Full assessment JSON
  weighted_scores JSONB, -- Scores per requirement
  match_percentage FLOAT,
  overall_score FLOAT,

  -- Extracted insights
  strengths TEXT[],
  gaps TEXT[],
  recommendations TEXT,

  -- Metadata
  assessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  assessed_by VARCHAR(255),
  assessment_version VARCHAR(20) DEFAULT '1.0',

  -- Decision tracking
  decision VARCHAR(50), -- hired, rejected, interview, hold
  decision_by VARCHAR(255),
  decision_at TIMESTAMP WITH TIME ZONE,
  decision_notes TEXT,

  CONSTRAINT unique_assessment_per_job UNIQUE(candidate_linkedin_url, job_template_id)
);

CREATE INDEX idx_job_assessments_candidate ON job_assessments(candidate_linkedin_url);
CREATE INDEX idx_job_assessments_template ON job_assessments(job_template_id);
CREATE INDEX idx_job_assessments_score ON job_assessments(match_percentage DESC);
CREATE INDEX idx_job_assessments_decision ON job_assessments(decision, assessed_at DESC);

-- =========================================
-- 5. COMPANY DISCOVERY SESSIONS
-- =========================================
-- Track company-based talent discovery
CREATE TABLE IF NOT EXISTS discovery_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_name VARCHAR(255) NOT NULL,
  description TEXT,

  -- Discovery parameters
  seed_companies TEXT[], -- Target companies
  similar_companies JSONB, -- Found similar companies
  industry_filters TEXT[],
  location_filters TEXT[],
  role_filters TEXT[],
  seniority_filters TEXT[],

  -- Link to job template
  job_template_id UUID REFERENCES job_templates(id) ON DELETE SET NULL,

  -- Discovery settings
  filters JSONB, -- All filter criteria
  max_candidates INTEGER DEFAULT 100,

  -- Progress tracking
  status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
  discovered_count INTEGER DEFAULT 0,
  assessed_count INTEGER DEFAULT 0,
  qualified_count INTEGER DEFAULT 0,

  -- Metadata
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT
);

CREATE INDEX idx_discovery_sessions_status ON discovery_sessions(status, created_at DESC);
CREATE INDEX idx_discovery_sessions_creator ON discovery_sessions(created_by);

-- =========================================
-- 6. DISCOVERED CANDIDATES
-- =========================================
-- Candidates found through company discovery
CREATE TABLE IF NOT EXISTS discovered_candidates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  discovery_session_id UUID REFERENCES discovery_sessions(id) ON DELETE CASCADE,

  -- Candidate info
  linkedin_url VARCHAR(500) NOT NULL,
  name VARCHAR(255),
  headline TEXT,
  current_company VARCHAR(255),
  current_title VARCHAR(255),
  location VARCHAR(255),

  -- Discovery metadata
  source_company VARCHAR(255),
  discovery_method VARCHAR(50), -- direct, similar_company, competitor
  relevance_score FLOAT,

  -- Assessment link
  assessment_id UUID,
  match_score FLOAT,

  -- Pipeline tracking
  added_to_pipeline BOOLEAN DEFAULT false,
  pipeline_stage VARCHAR(50), -- sourced, contacted, interviewing, etc.

  -- Timestamps
  discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  assessed_at TIMESTAMP WITH TIME ZONE,
  contacted_at TIMESTAMP WITH TIME ZONE,

  CONSTRAINT unique_candidate_per_session UNIQUE(discovery_session_id, linkedin_url)
);

CREATE INDEX idx_discovered_candidates_session ON discovered_candidates(discovery_session_id);
CREATE INDEX idx_discovered_candidates_linkedin ON discovered_candidates(linkedin_url);
CREATE INDEX idx_discovered_candidates_score ON discovered_candidates(match_score DESC);
CREATE INDEX idx_discovered_candidates_pipeline ON discovered_candidates(added_to_pipeline, pipeline_stage);

-- =========================================
-- 7. AUTOMATION RULES
-- =========================================
-- Define automation workflows
CREATE TABLE IF NOT EXISTS automation_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_name VARCHAR(255) NOT NULL,
  description TEXT,

  -- Rule configuration
  trigger_type VARCHAR(50), -- schedule, threshold, event
  trigger_config JSONB, -- cron expression, threshold values, event names

  -- Conditions
  conditions JSONB, -- Array of conditions that must be met

  -- Actions
  action_type VARCHAR(50), -- email, assess, refresh, notify
  action_config JSONB, -- Email template, notification settings, etc.

  -- Scope
  applies_to VARCHAR(50), -- all, list, template, discovery
  scope_id UUID, -- ID of list, template, or discovery session

  -- Metadata
  created_by VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,

  -- Execution tracking
  last_triggered_at TIMESTAMP WITH TIME ZONE,
  times_triggered INTEGER DEFAULT 0,
  last_error TEXT
);

CREATE INDEX idx_automation_rules_active ON automation_rules(is_active, trigger_type);
CREATE INDEX idx_automation_rules_scope ON automation_rules(applies_to, scope_id);

-- =========================================
-- 8. ACTIVITY LOG
-- =========================================
-- Track all extension and automation activities
CREATE TABLE IF NOT EXISTS activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_type VARCHAR(50) NOT NULL, -- profile_added, assessment_run, email_sent, etc.
  activity_data JSONB,

  -- Related entities
  user_name VARCHAR(255),
  linkedin_url VARCHAR(500),
  list_id UUID REFERENCES recruiter_lists(id) ON DELETE SET NULL,
  template_id UUID REFERENCES job_templates(id) ON DELETE SET NULL,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ip_address INET,
  user_agent TEXT,
  source VARCHAR(50) -- extension, web, api, automation
);

CREATE INDEX idx_activity_log_type ON activity_log(activity_type, created_at DESC);
CREATE INDEX idx_activity_log_user ON activity_log(user_name, created_at DESC);
CREATE INDEX idx_activity_log_linkedin ON activity_log(linkedin_url);

-- =========================================
-- 9. UPDATE TRIGGERS
-- =========================================
-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers to tables with updated_at columns
CREATE TRIGGER update_recruiter_lists_updated_at BEFORE UPDATE ON recruiter_lists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_templates_updated_at BEFORE UPDATE ON job_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automation_rules_updated_at BEFORE UPDATE ON automation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================
-- 10. HELPER FUNCTIONS
-- =========================================
-- Function to update list counts
CREATE OR REPLACE FUNCTION update_list_counts(list_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE recruiter_lists
    SET
        profile_count = (SELECT COUNT(*) FROM extension_profiles WHERE list_id = list_uuid),
        assessed_count = (SELECT COUNT(*) FROM extension_profiles WHERE list_id = list_uuid AND quick_score IS NOT NULL)
    WHERE id = list_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to increment template usage
CREATE OR REPLACE FUNCTION increment_template_usage(template_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE job_templates
    SET
        times_used = times_used + 1,
        last_used_at = NOW()
    WHERE id = template_uuid;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- 11. SAMPLE DATA (Optional)
-- =========================================
-- Uncomment to add sample templates

/*
INSERT INTO job_templates (
    title, department, level, description,
    requirements, weighted_criteria,
    skills_required, years_experience_min,
    created_by, is_public
) VALUES
(
    'Senior Full Stack Engineer',
    'Engineering',
    'senior',
    'We are looking for a Senior Full Stack Engineer to join our growing team.',
    '{"required": ["5+ years experience", "React expertise", "Node.js proficiency"], "preferred": ["AWS experience", "Team leadership"]}',
    '{"Technical Skills": 40, "Experience": 30, "Leadership": 20, "Culture Fit": 10}',
    ARRAY['React', 'Node.js', 'PostgreSQL', 'AWS'],
    5,
    'Default',
    true
),
(
    'Product Manager',
    'Product',
    'mid',
    'Seeking an experienced Product Manager to drive product strategy.',
    '{"required": ["3+ years PM experience", "Data-driven mindset", "Stakeholder management"], "preferred": ["Technical background", "B2B SaaS experience"]}',
    '{"Product Experience": 35, "Technical Understanding": 25, "Communication": 25, "Strategic Thinking": 15}',
    ARRAY['Product Strategy', 'Data Analysis', 'Agile', 'User Research'],
    3,
    'Default',
    true
);
*/

-- =========================================
-- 12. PERMISSIONS
-- =========================================
-- Grant permissions for Supabase anon role
GRANT ALL ON recruiter_lists TO anon;
GRANT ALL ON extension_profiles TO anon;
GRANT ALL ON job_templates TO anon;
GRANT ALL ON job_assessments TO anon;
GRANT ALL ON discovery_sessions TO anon;
GRANT ALL ON discovered_candidates TO anon;
GRANT ALL ON automation_rules TO anon;
GRANT ALL ON activity_log TO anon;

-- =========================================
-- END OF MIGRATION
-- =========================================