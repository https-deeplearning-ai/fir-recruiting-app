-- ============================================
-- Company Research Agent - Database Schema
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- ============================================

-- TABLE: target_companies
-- Purpose: Store discovered companies from research
CREATE TABLE IF NOT EXISTS target_companies (
    id SERIAL PRIMARY KEY,
    jd_id TEXT NOT NULL,                    -- Links to JD session
    company_id INTEGER,                      -- CoreSignal company ID
    company_name TEXT NOT NULL,
    company_domain TEXT,                     -- Company website

    -- Scoring & Categorization
    relevance_score NUMERIC(4,2),           -- 1-10 rating
    relevance_reasoning TEXT,                -- Why relevant
    category TEXT CHECK (category IN (
        'direct_competitor',
        'adjacent_company',
        'similar_stage',
        'talent_pool'
    )),

    -- Discovery metadata
    discovered_via TEXT,                     -- How we found it
    discovery_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Company data
    company_data JSONB,                      -- Full CoreSignal data
    employee_count INTEGER,
    funding_stage TEXT,
    industry TEXT,
    headquarters_location TEXT,

    -- AI Analysis
    gpt5_analysis JSONB,                     -- Deep research results
    ai_model_used TEXT,                      -- Which model scored it

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT target_companies_jd_company_unique
        UNIQUE (jd_id, company_id)
);

-- Indexes for performance
CREATE INDEX idx_target_companies_jd_id
    ON target_companies(jd_id);
CREATE INDEX idx_target_companies_score
    ON target_companies(jd_id, relevance_score DESC);
CREATE INDEX idx_target_companies_category
    ON target_companies(category);
CREATE INDEX idx_target_companies_created
    ON target_companies(created_at DESC);

-- TABLE: company_research_sessions
-- Purpose: Track research progress and metadata
CREATE TABLE IF NOT EXISTS company_research_sessions (
    jd_id TEXT PRIMARY KEY,
    jd_title TEXT,
    jd_company TEXT,
    jd_requirements JSONB,                   -- Extracted requirements

    -- Configuration
    search_config JSONB,                     -- Research parameters
    max_companies INTEGER DEFAULT 100,
    min_relevance_score NUMERIC(4,2) DEFAULT 5.0,

    -- Progress tracking
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),
    progress_percentage INTEGER DEFAULT 0,

    -- Metrics
    total_discovered INTEGER DEFAULT 0,
    total_evaluated INTEGER DEFAULT 0,
    total_selected INTEGER DEFAULT 0,

    -- API usage
    api_calls_made INTEGER DEFAULT 0,
    coresignal_credits_used INTEGER DEFAULT 0,
    gpt5_tokens_used INTEGER DEFAULT 0,
    tavily_searches_made INTEGER DEFAULT 0,

    -- Error handling
    error_message TEXT,
    error_details JSONB,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- User tracking
    initiated_by TEXT DEFAULT 'user'
);

-- Indexes
CREATE INDEX idx_research_sessions_status
    ON company_research_sessions(status);
CREATE INDEX idx_research_sessions_created
    ON company_research_sessions(created_at DESC);

-- RLS Policies (for Supabase)
ALTER TABLE target_companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_research_sessions ENABLE ROW LEVEL SECURITY;

-- Allow anon access (single-user tool)
CREATE POLICY "Allow anon access to target_companies"
    ON target_companies FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon access to research_sessions"
    ON company_research_sessions FOR ALL TO anon
    USING (true) WITH CHECK (true);

-- Auto-update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_target_companies_updated_at
    BEFORE UPDATE ON target_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- TABLE: company_discovery_cache
-- Purpose: Cache competitor discovery results to reduce API calls
CREATE TABLE IF NOT EXISTS company_discovery_cache (
    id BIGSERIAL PRIMARY KEY,
    seed_company TEXT NOT NULL,                  -- The company we searched competitors for (lowercase)
    discovered_companies JSONB NOT NULL,         -- Array of discovered competitor companies
    search_queries JSONB NOT NULL,               -- The 3 queries used (for debugging)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),

    -- Constraints
    UNIQUE(seed_company)
);

-- Indexes for performance
CREATE INDEX idx_company_discovery_seed
    ON company_discovery_cache(seed_company);
CREATE INDEX idx_company_discovery_expiry
    ON company_discovery_cache(expires_at);

-- RLS Policy
ALTER TABLE company_discovery_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anon access to company_discovery_cache"
    ON company_discovery_cache FOR ALL TO anon
    USING (true) WITH CHECK (true);

-- ============================================
-- Verification Query
-- ============================================
-- Run this to verify tables were created successfully:
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('target_companies', 'company_research_sessions', 'company_discovery_cache');
