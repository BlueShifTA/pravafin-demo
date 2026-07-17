-- Dev database initialization
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Create basic audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Audit table
CREATE TABLE IF NOT EXISTS audit.logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id TEXT,
    old_values JSONB,
    new_values JSONB,
    user_id TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_table_time ON audit.logs(table_name, timestamp DESC);

-- Grant permissions
GRANT USAGE ON SCHEMA audit TO devuser;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA audit TO devuser;
