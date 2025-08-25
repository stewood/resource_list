-- Database initialization script for Resource Directory development environment
-- This script runs when the PostgreSQL container starts for the first time

-- Create the development database if it doesn't exist
-- (PostgreSQL creates the database automatically based on POSTGRES_DB environment variable)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE resource_directory_dev TO postgres;

-- Enable required extensions for Django
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Resource Directory development database initialized successfully';
END $$;
