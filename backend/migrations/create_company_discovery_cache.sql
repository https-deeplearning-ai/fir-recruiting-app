-- Company Discovery Cache Table
-- Caches competitor discovery results to avoid redundant API calls across different JD searches
-- TTL: 7 days

CREATE TABLE IF NOT EXISTS company_discovery_cache (
    id BIGSERIAL PRIMARY KEY,
    seed_company TEXT NOT NULL,
    discovered_companies JSONB NOT NULL,
    search_queries JSONB NOT NULL,  -- Store the 3 queries used for debugging
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),

    -- Ensure one cache entry per seed company (case-insensitive)
    CONSTRAINT unique_seed_company UNIQUE(seed_company)
);

-- Index for fast lookups by seed company
CREATE INDEX IF NOT EXISTS idx_company_discovery_seed ON company_discovery_cache(seed_company);

-- Index for cleanup queries (find expired entries)
CREATE INDEX IF NOT EXISTS idx_company_discovery_expiry ON company_discovery_cache(expires_at);

-- Comments for documentation
COMMENT ON TABLE company_discovery_cache IS 'Caches competitor discovery results to reduce Claude API calls. TTL: 7 days.';
COMMENT ON COLUMN company_discovery_cache.seed_company IS 'The seed company name used to find competitors (stored lowercase for case-insensitive lookup)';
COMMENT ON COLUMN company_discovery_cache.discovered_companies IS 'Array of discovered company objects with metadata';
COMMENT ON COLUMN company_discovery_cache.search_queries IS 'The 3 search queries used (for debugging and cache validation)';
COMMENT ON COLUMN company_discovery_cache.expires_at IS 'Expiration timestamp - entries older than this are stale and should be refreshed';
