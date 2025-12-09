-- Create saved_articles table for user bookmarks and notes
CREATE TABLE IF NOT EXISTS saved_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, paper_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_saved_articles_user_id ON saved_articles(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_articles_paper_id ON saved_articles(paper_id);

-- Enable Row Level Security
ALTER TABLE saved_articles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own saved articles
CREATE POLICY "Users can view their own saved articles"
    ON saved_articles
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own saved articles
CREATE POLICY "Users can insert their own saved articles"
    ON saved_articles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own saved articles
CREATE POLICY "Users can update their own saved articles"
    ON saved_articles
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete their own saved articles
CREATE POLICY "Users can delete their own saved articles"
    ON saved_articles
    FOR DELETE
    USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_saved_articles_updated_at
    BEFORE UPDATE ON saved_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

