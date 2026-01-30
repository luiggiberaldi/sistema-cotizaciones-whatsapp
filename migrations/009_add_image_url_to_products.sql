-- Add image_url column to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Policy to allow public read access to product images (if using storage)
-- NOTE: Bucket 'product-images' must be created manually or via API if not exists.
