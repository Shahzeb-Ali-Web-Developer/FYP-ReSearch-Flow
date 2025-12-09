-- Add institutions column to research_papers table if it doesn't exist
-- This column stores institution names as a JSON array

-- Check if column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'research_papers' 
        AND column_name = 'institutions'
    ) THEN
        ALTER TABLE research_papers 
        ADD COLUMN institutions JSONB DEFAULT '[]'::jsonb;
        
        -- Create index for better query performance
        CREATE INDEX IF NOT EXISTS idx_research_papers_institutions 
        ON research_papers USING GIN (institutions);
        
        RAISE NOTICE 'Column institutions added successfully';
    ELSE
        RAISE NOTICE 'Column institutions already exists';
    END IF;
END $$;

