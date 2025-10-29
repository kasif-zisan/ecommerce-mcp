-- Drop database if exists (BE CAREFUL - this deletes everything!)
DROP DATABASE IF EXISTS products;

-- Create new database
CREATE DATABASE products
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Add comment to database
COMMENT ON DATABASE products IS 'E-commerce historical inventory database for MCP demo project';

-- Connect to the new database
\c products

-- Drop table if exists (for clean slate)
DROP TABLE IF EXISTS products CASCADE;

-- Create products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    rating DECIMAL(3, 2) NOT NULL CHECK (rating >= 0 AND rating <= 5),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    last_updated DATE NOT NULL DEFAULT '2024-04-27',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_price ON products(price);
CREATE INDEX idx_rating ON products(rating);
CREATE INDEX idx_stock ON products(stock);

-- Composite indexes for common query patterns
CREATE INDEX idx_category_price ON products(category, price);
CREATE INDEX idx_category_rating ON products(category, rating);
CREATE INDEX idx_category_stock ON products(category, stock);
CREATE INDEX idx_stock_rating ON products(stock, rating);

-- Success message
SELECT 'Database and schema created successfully!' AS status;