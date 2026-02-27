-- Create validation_results table
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL UNIQUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    input_types TEXT[],
    image_valid BOOLEAN,
    text_valid BOOLEAN,
    voice_valid BOOLEAN,
    overall_confidence REAL,
    routing VARCHAR(50),
    action VARCHAR(50),
    raw_results JSONB
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_request_id ON validation_results (request_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON validation_results (timestamp);
CREATE INDEX IF NOT EXISTS idx_routing ON validation_results (routing);
