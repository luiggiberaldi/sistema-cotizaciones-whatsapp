-- Create customers table
CREATE TABLE IF NOT EXISTS consumers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE consumers ENABLE ROW LEVEL SECURITY;

-- Policy (Open for service role, similar to others for now)
CREATE POLICY "Enable read/write for all" ON consumers
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Add customer_id to quotes
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES consumers(id);

-- Index for phone lookups
CREATE INDEX IF NOT EXISTS idx_consumers_phone ON consumers(phone);
