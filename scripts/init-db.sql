-- Database initialization script for RAILPULSE AI (Railway Intelligence Platform)
-- This runs on first container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (will be created by Alembic migrations)
-- This script ensures the database is ready for the application

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE railway_intelligence TO railway;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO railway;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO railway;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO railway;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO railway;