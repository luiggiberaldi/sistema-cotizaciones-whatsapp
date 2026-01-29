-- Add updated_at column if it doesn't exist
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Add created_at column if it doesn't exist
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Add aliases column if it doesn't exist (used for search)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS aliases TEXT[] DEFAULT '{}';

-- Optional: Enable RLS if not enabled (good practice)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Creating a policy for products (if you want them public read, authenticated write)
-- This logic depends on your security model. 
-- For now, allowing all access to authenticated users or service role is safe.
