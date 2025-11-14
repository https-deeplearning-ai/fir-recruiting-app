-- Company ID Cache Table
-- Purpose: Cache company_name → coresignal_id mappings to save on search API credits
-- Estimated savings: 90%+ of search credits (most companies repeat across sessions)

CREATE TABLE IF NOT EXISTS company_id_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company identifiers
    company_name TEXT NOT NULL,
    company_name_normalized TEXT NOT NULL, -- Lowercase, no spaces/punctuation for matching
    coresignal_id BIGINT NOT NULL,

    -- Lookup metadata
    lookup_tier TEXT NOT NULL CHECK (lookup_tier IN ('website', 'name_exact', 'fuzzy', 'company_clean')),
    website TEXT, -- If available

    -- Additional metadata for validation
    metadata JSONB DEFAULT '{}', -- Store industry, employee_count, description for verification

    -- Usage tracking
    hit_count INTEGER DEFAULT 0, -- How many times this cache entry was used
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_company_name_normalized ON company_id_cache(company_name_normalized);
CREATE INDEX IF NOT EXISTS idx_company_name ON company_id_cache(company_name);
CREATE INDEX IF NOT EXISTS idx_coresignal_id ON company_id_cache(coresignal_id);
CREATE INDEX IF NOT EXISTS idx_website ON company_id_cache(website) WHERE website IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_last_accessed ON company_id_cache(last_accessed_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_company_id_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_company_id_cache_timestamp
    BEFORE UPDATE ON company_id_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_company_id_cache_updated_at();

-- Unique constraint: One mapping per normalized name
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_name_normalized_unique
    ON company_id_cache(company_name_normalized);

-- Comments
COMMENT ON TABLE company_id_cache IS 'Cache for company name to CoreSignal ID mappings to reduce API search credits';
COMMENT ON COLUMN company_id_cache.company_name IS 'Original company name as discovered';
COMMENT ON COLUMN company_id_cache.company_name_normalized IS 'Normalized name for matching (lowercase, no punctuation)';
COMMENT ON COLUMN company_id_cache.coresignal_id IS 'CoreSignal company ID from search API';
COMMENT ON COLUMN company_id_cache.lookup_tier IS 'How the ID was found: website, name_exact, fuzzy, company_clean';
COMMENT ON COLUMN company_id_cache.hit_count IS 'Number of times this cache entry was used (tracks savings)';
COMMENT ON COLUMN company_id_cache.metadata IS 'Additional company data for validation (industry, size, etc.)';
