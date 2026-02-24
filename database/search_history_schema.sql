-- Create search_history table for tracking user search queries
-- Used for autocomplete suggestions and search analytics
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, query)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_searched_at ON search_history(searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);

-- Enable Row Level Security
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own search history
CREATE POLICY "Users can view their own search history"
    ON search_history
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own search history
CREATE POLICY "Users can insert their own search history"
    ON search_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own search history (for upsert/timestamp updates)
CREATE POLICY "Users can update their own search history"
    ON search_history
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete their own search history
CREATE POLICY "Users can delete their own search history"
    ON search_history
    FOR DELETE
    USING (auth.uid() = user_id);
