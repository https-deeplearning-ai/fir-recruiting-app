-- Create cached_searches table for domain search result caching
-- This table stores search results to avoid duplicate API calls and save credits

CREATE TABLE IF NOT EXISTS cached_searches (
    id SERIAL PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,  -- MD5 hash of normalized search parameters
    stage1_companies JSONB NOT NULL,  -- Company discovery results from Stage 1
    stage2_previews JSONB NOT NULL,  -- Preview search results from Stage 2
    session_id TEXT,  -- Optional reference to search_sessions table
    search_params JSONB,  -- Original search parameters (jd_requirements, endpoint) for debugging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Cache creation timestamp
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- Track when cache was last used
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_cached_searches_cache_key ON cached_searches(cache_key);
CREATE INDEX IF NOT EXISTS idx_cached_searches_created_at ON cached_searches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cached_searches_last_accessed ON cached_searches(last_accessed DESC);

-- Add comments for documentation
COMMENT ON TABLE cached_searches IS 'Caches domain search results to avoid duplicate CoreSignal API calls and save credits';
COMMENT ON COLUMN cached_searches.cache_key IS 'MD5 hash of normalized search parameters (target_domain, mentioned_companies, endpoint)';
COMMENT ON COLUMN cached_searches.stage1_companies IS 'JSON array of discovered companies from Stage 1 (company discovery)';
COMMENT ON COLUMN cached_searches.stage2_previews IS 'JSON array of candidate previews from Stage 2 (CoreSignal search)';
COMMENT ON COLUMN cached_searches.session_id IS 'Optional reference to search session that created this cache entry';
COMMENT ON COLUMN cached_searches.search_params IS 'Original search parameters for debugging and cache verification';
COMMENT ON COLUMN cached_searches.created_at IS 'When the cache entry was created';
COMMENT ON COLUMN cached_searches.last_accessed IS 'When the cache was last accessed (updated on cache hit)';

-- Enable Row Level Security (optional, but recommended)
ALTER TABLE cached_searches ENABLE ROW LEVEL SECURITY;

-- Create policy for anonymous access (adjust based on your auth setup)
CREATE POLICY "Enable all operations for anonymous users" ON cached_searches
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Function to automatically update last_accessed timestamp on cache hit
CREATE OR REPLACE FUNCTION update_cached_searches_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update last_accessed on UPDATE
CREATE TRIGGER update_cached_searches_last_accessed_trigger
    BEFORE UPDATE ON cached_searches
    FOR EACH ROW
    EXECUTE FUNCTION update_cached_searches_last_accessed();

-- Cache Freshness Policy:
-- - Default freshness: 7 days (configurable in get_cached_search_results)
-- - Recommendation: Set up a cron job to delete entries older than 30 days
-- Example cleanup query (run periodically):
-- DELETE FROM cached_searches WHERE created_at < NOW() - INTERVAL '30 days';
