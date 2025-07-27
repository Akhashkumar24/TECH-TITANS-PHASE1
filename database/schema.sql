-- database/schema.sql
-- Database Schema for Job Matching System

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('job_seeker', 'admin')) NOT NULL,
    full_name VARCHAR(200),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    skills_required TEXT[],
    experience_level VARCHAR(50),
    salary_range VARCHAR(100),
    location VARCHAR(200),
    company_name VARCHAR(200),
    posted_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id INTEGER REFERENCES jobs(id),
    resume_path VARCHAR(500),
    resume_text TEXT,
    cover_letter TEXT,
    status VARCHAR(50) DEFAULT 'submitted',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Rankings table
CREATE TABLE IF NOT EXISTS rankings (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    application_id INTEGER REFERENCES applications(id),
    similarity_score DECIMAL(5,4),
    rank_position INTEGER,
    ranking_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, application_id)
);

-- Agent logs table for tracking agent communications
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50),
    action VARCHAR(100),
    job_id INTEGER REFERENCES jobs(id),
    application_id INTEGER REFERENCES applications(id),
    message TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_rankings_job_id ON rankings(job_id);
CREATE INDEX IF NOT EXISTS idx_rankings_similarity_score ON rankings(similarity_score DESC);