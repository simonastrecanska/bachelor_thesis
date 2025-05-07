-- Initialize Swift Testing Database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Schema
CREATE SCHEMA IF NOT EXISTS swift_testing;

-- Create Role for application access
CREATE ROLE swift_user WITH LOGIN PASSWORD 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON SCHEMA swift_testing TO swift_user;

-- Create Tables
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES message_templates(id),
    content TEXT NOT NULL,
    parsed_content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_valid BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS variator_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_tag VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    parameters JSONB,
    results JSONB,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO swift_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO swift_user;

-- Index for better performance
CREATE INDEX IF NOT EXISTS idx_template_type ON message_templates (template_type);
CREATE INDEX IF NOT EXISTS idx_variator_field_tag ON variator_data (field_tag);
CREATE INDEX IF NOT EXISTS idx_message_template_id ON messages (template_id);

-- Insert sample data for diagnostics
INSERT INTO parameters (test_name, description) 
VALUES ('Database Initialization', 'Initial setup from Docker container')
ON CONFLICT DO NOTHING; 