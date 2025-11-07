-- Company Intelligence Cache Schema
-- For storing enriched company data with 30-day freshness

CREATE TABLE IF NOT EXISTS company_intelligence_cache (
    company_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL,
    enriched_data JSONB NOT NULL,      -- Full company_base data from CoreSignal
    employee_samples JSONB,             -- Sample employee profiles
    websearch_research JSONB,           -- Claude Agent SDK WebSearch findings
    validation_metadata JSONB,          -- Validation details and confidence scores
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_company_cache_name ON company_intelligence_cache(company_name);
CREATE INDEX IF NOT EXISTS idx_company_cache_updated ON company_intelligence_cache(last_updated);

-- Cached competitors for Tavily search results (7-day freshness)
CREATE TABLE IF NOT EXISTS cached_competitors (
    seed_company_name TEXT PRIMARY KEY,
    discovered_companies JSONB NOT NULL,  -- Array of discovered competitor companies
    search_queries JSONB NOT NULL,        -- Queries used for discovery
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_cached_competitors_updated ON cached_competitors(last_updated);

-- Company research sessions for progressive evaluation
CREATE TABLE IF NOT EXISTS company_research_sessions (
    jd_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,                 -- running, completed, failed
    search_config JSONB NOT NULL,         -- Original search configuration
    discovered_companies JSONB,           -- All discovered companies
    screened_companies JSONB,             -- Companies after initial screening
    evaluated_companies JSONB,            -- Deep researched companies
    employees_found JSONB,                -- Employee profiles by company
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for session lookups
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON company_research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_updated ON company_research_sessions(last_updated);