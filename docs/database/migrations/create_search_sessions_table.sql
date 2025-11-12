-- Create search_sessions table for company batching and progressive loading
-- This table stores search session state to enable resumable searches

CREATE TABLE IF NOT EXISTS search_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    search_query JSONB NOT NULL,  -- Original CoreSignal query parameters
    company_batches JSONB NOT NULL,  -- Array of company batch configurations [[batch1], [batch2], ...]
    discovered_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- All employee IDs discovered
    profiles_fetched INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- Employee IDs that have been fetched
    total_discovered INTEGER DEFAULT 0,  -- Count of unique employee IDs found
    batch_index INTEGER DEFAULT 0,  -- Current batch being processed (0-indexed)
    employee_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- NEW: All employee IDs from search (up to 1000)
    profiles_offset INTEGER DEFAULT 0,  -- NEW: Current pagination offset for profile collection
    total_employee_ids INTEGER DEFAULT 0,  -- NEW: Total count of employee IDs for progress tracking
    is_active BOOLEAN DEFAULT TRUE,  -- Session active status (soft delete)
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Track last usage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_search_session_created ON search_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_session_updated ON search_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_session_active ON search_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_search_session_last_accessed ON search_sessions(last_accessed DESC);

-- Add comments for documentation
COMMENT ON TABLE search_sessions IS 'Stores search session state for progressive loading with company batching';
COMMENT ON COLUMN search_sessions.session_id IS 'Unique identifier for the search session (format: search_timestamp_uuid)';
COMMENT ON COLUMN search_sessions.search_query IS 'Original CoreSignal query parameters as JSON';
COMMENT ON COLUMN search_sessions.company_batches IS 'Array of company batches, each batch contains 5 companies';
COMMENT ON COLUMN search_sessions.discovered_ids IS 'All unique employee IDs found across all batches';
COMMENT ON COLUMN search_sessions.profiles_fetched IS 'Employee IDs whose full profiles have been fetched';
COMMENT ON COLUMN search_sessions.batch_index IS 'Current batch index (0-based), increments as batches are processed';
COMMENT ON COLUMN search_sessions.employee_ids IS 'All employee IDs from search endpoint (up to 1000), used for pagination';
COMMENT ON COLUMN search_sessions.profiles_offset IS 'Current offset for profile pagination (0, 20, 40, etc.)';
COMMENT ON COLUMN search_sessions.total_employee_ids IS 'Total count of employee IDs for progress tracking';
COMMENT ON COLUMN search_sessions.is_active IS 'Soft delete flag - FALSE means session is cleared but preserved';
COMMENT ON COLUMN search_sessions.last_accessed IS 'Updated on every session access for activity tracking';

-- Enable Row Level Security (optional, but recommended)
ALTER TABLE search_sessions ENABLE ROW LEVEL SECURITY;

-- Create policy for anonymous access (adjust based on your auth setup)
CREATE POLICY "Enable all operations for anonymous users" ON search_sessions
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_search_sessions_updated_at
    BEFORE UPDATE ON search_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();